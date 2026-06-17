from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import yaml

import urisysnode.artifact_resolver as artifact_resolver
from urisysnode.artifact_resolver import (
    fetch_release,
    load_artifact_index,
    load_node_profile,
    release_api_url,
    run_release,
    select_artifact,
)


def test_select_artifact_by_platform(tmp_path: Path) -> None:
    index = {
        "artifacts": [
            {"target": "linux-arm64", "platform": "linux/arm64", "ref": "img:arm"},
            {
                "target": "linux-amd64-mock",
                "platform": "linux/amd64",
                "ref": "img:amd64",
                "runtime": "docker",
                "capabilities": ["mock-stepper"],
            },
        ]
    }
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text(
        yaml.safe_dump({"node": {"platform": "linux/amd64", "runtimes": ["docker"], "capabilities": ["mock-stepper"]}}),
        encoding="utf-8",
    )
    art = select_artifact(index, load_node_profile(profile_path))
    assert art["ref"] == "img:amd64"


def test_load_artifact_index_from_file(tmp_path: Path) -> None:
    p = tmp_path / "index.json"
    p.write_text(json.dumps({"schema": "markpact.artifact-index.v1", "artifacts": []}), encoding="utf-8")
    assert load_artifact_index(p)["schema"] == "markpact.artifact-index.v1"


def test_load_artifact_index_from_url() -> None:
    payload = {"schema": "markpact.artifact-index.v1", "artifacts": [{"ref": "img:1"}]}
    with patch("urisysnode.artifact_resolver.fetch_json", return_value=payload):
        data = load_artifact_index("http://registry.example/releases/x/0.1.0/artifact-index.json")
    assert data["artifacts"][0]["ref"] == "img:1"


def test_fetch_release() -> None:
    release = {
        "contract_id": "uristepper.contract",
        "version": "0.1.0",
        "artifact_index_url": "https://raw.githubusercontent.com/org/repo/v0.1.0/releases/x/0.1.0/artifact-index.json",
    }
    with patch(
        "urisysnode.artifact_resolver.fetch_json",
        return_value={"ok": True, "release": release},
    ):
        out = fetch_release("https://markpact.com", "uristepper.contract", "0.1.0")
    assert out["artifact_index_url"].endswith("artifact-index.json")


def test_release_api_url() -> None:
    url = release_api_url("https://markpact.com", "stepper.axis-control", "0.1.0")
    assert "/api/contracts/stepper.axis-control/releases/0.1.0" in url


def test_run_release_honors_artifact_container_port(monkeypatch, tmp_path) -> None:
    # urikvm image listens on 8794, not the 8790 default — the artifact declares it.
    index = {"artifacts": [{"ref": "ghcr.io/x/urikvm@sha256:abc", "port": 8794}]}
    captured = {}

    monkeypatch.setattr(artifact_resolver, "load_artifact_index", lambda _u: index)
    monkeypatch.setattr(artifact_resolver, "load_node_profile", lambda _p: {})
    monkeypatch.setattr(artifact_resolver, "docker_pull", lambda ref: None)
    monkeypatch.setattr(artifact_resolver, "wait_health", lambda **k: None)

    def fake_run_worker(ref, *, container, host_port, container_port):
        captured.update(ref=ref, host_port=host_port, container_port=container_port)

    monkeypatch.setattr(artifact_resolver, "docker_run_worker", fake_run_worker)

    out = run_release(
        {"artifact_index_url": "https://x/index.json", "contract_id": "urikvm.contract"},
        tmp_path / "p.yaml", container="urisys-kvm-worker", port=8895,
    )
    assert captured["container_port"] == 8794
    assert captured["host_port"] == 8895
    assert out["container_port"] == 8794
