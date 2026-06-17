from __future__ import annotations

import argparse
import json
import os
import sys

from urisysnode.artifact_resolver import (
    fetch_release,
    load_artifact_index,
    load_node_profile,
    release_api_url,
    resolve_and_run,
    resolve_from_release,
    select_artifact,
)
from urisysnode.client import call_via_route_map, discover_mdns
from urisysnode.identity import enroll, load_identity, load_pairing
from urisysnode.router import load_route_map, rewrite_uri_for_slave
from urisysnode.runtime import Runtime, load_json
from urisysnode.serve import build_runtime, serve


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="urisys-node", description="urisys slave node — explicit local install")
    p.add_argument("--config", default=os.environ.get("URISYS_NODE_CONFIG", "config/node-profile.json"))
    p.add_argument("--events", default=os.environ.get("URISYS_NODE_EVENTS", "data/events.jsonl"))
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("serve", help="Start HTTP URI server (default :8790)")
    s.add_argument("--host", default=os.environ.get("URISYS_NODE_HOST", "0.0.0.0"))
    s.add_argument("--port", type=int, default=int(os.environ.get("URISYS_NODE_PORT", "8790")))

    e = sub.add_parser("enroll", help="Pair node with controller")
    e.add_argument("--controller", required=True)
    e.add_argument("--code", default=None)
    e.add_argument("--token", default=None)

    sub.add_parser("identity", help="Show node identity")
    sub.add_parser("pairing", help="Show pairing status")

    doc = sub.add_parser("doctor", help="Check urisys installation and environment")
    doc.add_argument("--min-version", default=os.environ.get("URISYS_MIN_VERSION", "0.1.25"))

    d = sub.add_parser("discover", help="Discover nodes on LAN (requires zeroconf)")
    d.add_argument("--timeout", type=float, default=2.0)

    nl = sub.add_parser("nodes", help="List known nodes from registry")
    nl.add_argument("--registry", default="config/nodes.registry.json")

    c = sub.add_parser("call", help="Call URI locally or via route map")
    c.add_argument("uri")
    c.add_argument("--payload", default="{}")
    c.add_argument("--approve", action="store_true")
    c.add_argument("--dry-run", action="store_true")
    c.add_argument("--allow-real", action="store_true")
    c.add_argument("--route-map", default=None)
    c.add_argument("--nodes-registry", default="config/nodes.registry.json")

    art = sub.add_parser("artifact", help="Resolve artifact-index and run OCI worker (lab/prototype)")
    art_sub = art.add_subparsers(dest="artifact_command", required=True)
    art_sel = art_sub.add_parser("select", help="Print selected artifact for node profile")
    art_sel.add_argument("--index", required=True, help="Local path or http(s) URL to artifact-index.json")
    art_sel.add_argument("--profile", required=True)
    art_run = art_sub.add_parser("resolve-run", help="Pull image from index and start worker container")
    art_run.add_argument("--index", required=True, help="Local path or http(s) URL to artifact-index.json")
    art_run.add_argument("--profile", required=True)
    art_run.add_argument("--port", type=int, default=int(os.environ.get("WORKER_PORT", "8791")))
    art_run.add_argument("--container", default=os.environ.get("WORKER_NAME", "urisys-stepper-worker"))
    art_rel = art_sub.add_parser("resolve-release", help="Fetch release from markpact.com catalog, then pull and run")
    art_rel.add_argument("--catalog", default=os.environ.get("MARKPACT_CATALOG_URL", "https://markpact.com"))
    art_rel.add_argument("--contract", required=True, help="Contract id, e.g. uristepper.contract")
    art_rel.add_argument("--version", required=True)
    art_rel.add_argument("--profile", required=True)
    art_rel.add_argument("--port", type=int, default=int(os.environ.get("WORKER_PORT", "8791")))
    art_rel.add_argument("--container", default=os.environ.get("WORKER_NAME", "urisys-stepper-worker"))
    art_fetch = art_sub.add_parser("fetch-release", help="Print release metadata from catalog API")
    art_fetch.add_argument("--catalog", default=os.environ.get("MARKPACT_CATALOG_URL", "https://markpact.com"))
    art_fetch.add_argument("--contract", required=True)
    art_fetch.add_argument("--version", required=True)

    args = p.parse_args(argv)

    if args.cmd == "serve":
        rt = build_runtime(args.config)
        serve(rt, args.host, args.port)
        return 0

    if args.cmd == "enroll":
        result = enroll(args.controller, code=args.code, token=args.token)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    if args.cmd == "identity":
        print(json.dumps(load_identity(), indent=2, ensure_ascii=False))
        return 0

    if args.cmd == "pairing":
        print(json.dumps(load_pairing(), indent=2, ensure_ascii=False))
        return 0

    if args.cmd == "doctor":
        from urisys.doctor import run_doctor

        report = run_doctor(min_version=args.min_version or None)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report.get("ok") else 1

    if args.cmd == "discover":
        nodes = discover_mdns(args.timeout)
        print(json.dumps(nodes, indent=2, ensure_ascii=False))
        return 0

    if args.cmd == "nodes":
        path = args.registry
        if not os.path.exists(path):
            print(json.dumps({"nodes": {}}, indent=2))
            return 0
        print(open(path, encoding="utf-8").read())
        return 0

    if args.cmd == "call":
        payload = json.loads(args.payload)
        context = {
            "approved": args.approve,
            "dry_run": args.dry_run,
            "allow_real": args.allow_real,
        }
        if args.route_map:
            result = call_via_route_map(
                args.uri,
                route_map_path=args.route_map,
                nodes_registry_path=args.nodes_registry,
                payload=payload,
                context=context,
            )
        else:
            rt = build_runtime(args.config)
            uri = args.uri
            identity = load_identity()
            uri = rewrite_uri_for_slave(uri, node_id=identity["node_id"], target_node="local")
            result = rt.call(uri, payload, context)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("ok") else 1

    if args.cmd == "artifact":
        if args.artifact_command == "select":
            art = select_artifact(load_artifact_index(args.index), load_node_profile(args.profile))
            print(json.dumps(art, indent=2, ensure_ascii=False))
            return 0
        if args.artifact_command == "fetch-release":
            release = fetch_release(args.catalog, args.contract, args.version)
            print(json.dumps({"ok": True, "release": release, "api": release_api_url(args.catalog, args.contract, args.version)}, indent=2, ensure_ascii=False))
            return 0
        if args.artifact_command == "resolve-run":
            result = resolve_and_run(
                args.index,
                args.profile,
                container=args.container,
                port=args.port,
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0
        if args.artifact_command == "resolve-release":
            result = resolve_from_release(
                args.catalog,
                args.contract,
                args.version,
                args.profile,
                container=args.container,
                port=args.port,
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
