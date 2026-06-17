"""Resolve Markpact artifact-index to a runnable OCI image on this node."""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import yaml


def is_url(source: str) -> bool:
    return source.startswith(("http://", "https://"))


def _auth_opener(for_url: str) -> urllib.request.OpenerDirector:
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return urllib.request.build_opener(_GitHubHeaderAuth(token))

    user = os.environ.get("URISYS_REGISTRY_USER")
    password = os.environ.get("URISYS_REGISTRY_PASSWORD")
    if not user or password is None:
        return urllib.request.build_opener()
    parsed = urllib.parse.urlparse(for_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    manager.add_password(None, origin, user, password)
    return urllib.request.build_opener(urllib.request.HTTPBasicAuthHandler(manager))


class _GitHubHeaderAuth(urllib.request.BaseHandler):
    handler_order = 480

    def __init__(self, token: str) -> None:
        self.token = token

    def https_request(self, req):  # noqa: ANN001
        req.add_header("Authorization", f"Bearer {self.token}")
        return req

    http_request = https_request


def fetch_json(url: str, *, timeout: int = 60) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with _auth_opener(url).open(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_text(url: str, *, timeout: int = 60) -> str:
    req = urllib.request.Request(url, headers={"Accept": "text/plain, text/markdown, */*"})
    with _auth_opener(url).open(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def _contract_yaml_block(contract_text: str) -> str:
    """Extract the ```yaml markpact:contract fenced block from a contract.markpact.md."""
    lines = contract_text.splitlines()
    inside = False
    body: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not inside:
            if stripped.startswith("```") and "markpact:contract" in stripped:
                inside = True
            continue
        if stripped.startswith("```"):
            break
        body.append(line)
    return "\n".join(body)


def parse_contract_spec(contract_text: str) -> dict[str, Any]:
    """Return {scheme, patterns} from a UriContract markpact. Patterns are every
    declared query + command pattern — exactly the URIs to forward to the worker."""
    block = _contract_yaml_block(contract_text)
    if not block.strip():
        raise ValueError("contract has no markpact:contract block")
    data = yaml.safe_load(block) or {}
    scheme = str(data.get("scheme") or "").strip()
    patterns: list[str] = []
    for item in (data.get("queries") or []) + (data.get("commands") or []):
        pattern = str((item or {}).get("pattern") or "").strip()
        if pattern:
            patterns.append(pattern)
    if not scheme:
        raise ValueError("contract declares no scheme")
    if not patterns:
        raise ValueError("contract declares no query/command patterns")
    return {"scheme": scheme, "patterns": patterns}


def contract_url_from_release(release: dict[str, Any]) -> str:
    """Locate the contract source URL declared by a release payload."""
    direct = release.get("contract_url") or release.get("contract_source")
    if direct:
        return str(direct)
    contract = release.get("contract")
    if isinstance(contract, dict):
        url = contract.get("url") or contract.get("contract_url")
        if url:
            return str(url)
    return ""


def contract_spec_from_release(release: dict[str, Any]) -> dict[str, Any]:
    """Fetch and parse the contract referenced by a release into {scheme, patterns}."""
    url = contract_url_from_release(release)
    if not url:
        raise ValueError("release has no contract_url to derive scheme/patterns from")
    return parse_contract_spec(fetch_text(url))


def load_node_profile(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return data.get("node") or data


def load_artifact_index(source: str | Path) -> dict[str, Any]:
    source_str = str(source)
    if is_url(source_str):
        data = fetch_json(source_str)
        if not isinstance(data, dict):
            raise ValueError("artifact-index must be a JSON object")
        return data
    return json.loads(Path(source_str).read_text(encoding="utf-8"))


def release_api_url(catalog_url: str, contract_id: str, version: str) -> str:
    base = catalog_url.rstrip("/")
    cid = urllib.parse.quote(contract_id, safe="")
    ver = urllib.parse.quote(version, safe="")
    return f"{base}/api/contracts/{cid}/releases/{ver}"


def fetch_release(catalog_url: str, contract_id: str, version: str) -> dict[str, Any]:
    data = fetch_json(release_api_url(catalog_url, contract_id, version))
    if not isinstance(data, dict):
        raise ValueError("release response must be a JSON object")
    if not data.get("ok"):
        raise ValueError(str(data.get("error") or "release fetch failed"))
    release = data.get("release")
    if not isinstance(release, dict):
        raise ValueError("release payload missing")
    return release


def select_artifact(index: dict[str, Any], node_profile: dict[str, Any]) -> dict[str, Any]:
    platform = str(node_profile.get("platform") or "linux/amd64")
    capabilities = set(node_profile.get("capabilities") or [])
    runtimes = set(node_profile.get("runtimes") or [])

    candidates = list(index.get("artifacts") or [])
    if not candidates:
        raise ValueError("artifact-index has no artifacts")

    for art in candidates:
        if art.get("platform") and art["platform"] != platform:
            continue
        if runtimes and art.get("runtime") not in runtimes:
            continue
        art_caps = set(art.get("capabilities") or [])
        if capabilities and art_caps and not capabilities.intersection(art_caps):
            continue
        return art

    return candidates[0]


def docker_pull(ref: str) -> None:
    proc = subprocess.run(["docker", "pull", ref], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"docker pull failed: {ref}")


def docker_run_worker(
    ref: str,
    *,
    container: str = "urisys-stepper-worker",
    host_port: int = 8791,
    container_port: int = 8790,
) -> None:
    subprocess.run(["docker", "rm", "-f", container], capture_output=True, text=True)
    proc = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            container,
            "-p",
            f"{host_port}:{container_port}",
            ref,
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "docker run failed")


def wait_health(port: int = 8791, attempts: int = 30, container: str = "urisys-stepper-worker") -> None:
    url = f"http://127.0.0.1:{port}/health"
    last = ""
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError, ConnectionResetError, OSError) as exc:
            last = str(exc)
        time.sleep(1)
    logs = subprocess.run(["docker", "logs", "--tail", "50", container], capture_output=True, text=True)
    raise RuntimeError(f"worker health timeout on {url}: {last}\n{logs.stdout}\n{logs.stderr}")


def resolve_and_run(
    index_source: str | Path,
    profile_path: str | Path,
    *,
    container: str = "urisys-stepper-worker",
    port: int = 8791,
) -> dict[str, Any]:
    index = load_artifact_index(index_source)
    profile = load_node_profile(profile_path)
    art = select_artifact(index, profile)
    ref = str(art.get("ref") or art.get("tag") or "")
    if not ref:
        raise ValueError("selected artifact has no ref or tag")

    docker_pull(ref)
    docker_run_worker(ref, container=container, host_port=port, container_port=8790)
    wait_health(port=port, container=container)

    return {
        "ok": True,
        "platform": profile.get("platform"),
        "artifact": art,
        "ref": ref,
        "container": container,
        "port": port,
        "index_source": str(index_source),
    }


def run_release(
    release: dict[str, Any],
    profile_path: str | Path,
    *,
    container: str = "urisys-stepper-worker",
    port: int = 8791,
) -> dict[str, Any]:
    """Pull and run the worker for an already-fetched release. Split out from
    resolve_from_release so the hot-load glue can verify the exact release it
    runs without re-fetching it from the catalog."""
    index_url = str(release.get("artifact_index_url") or "")
    if not index_url:
        raise ValueError("release has no artifact_index_url")

    index = load_artifact_index(index_url)
    profile = load_node_profile(profile_path)
    art = select_artifact(index, profile)
    ref = str(art.get("ref") or art.get("tag") or "")
    if not ref:
        raise ValueError("selected artifact has no ref or tag")

    container_port = int(art.get("port") or art.get("container_port") or 8790)

    docker_pull(ref)
    docker_run_worker(ref, container=container, host_port=port, container_port=container_port)
    wait_health(port=port, container=container)

    return {
        "ok": True,
        "contract_id": release.get("contract_id"),
        "version": release.get("version"),
        "release": release,
        "artifact_index_url": index_url,
        "platform": profile.get("platform"),
        "artifact": art,
        "ref": ref,
        "container": container,
        "port": port,
        "container_port": container_port,
    }


def resolve_from_release(
    catalog_url: str,
    contract_id: str,
    version: str,
    profile_path: str | Path,
    *,
    container: str = "urisys-stepper-worker",
    port: int = 8791,
) -> dict[str, Any]:
    release = fetch_release(catalog_url, contract_id, version)
    return run_release(release, profile_path, container=container, port=port)
