#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.validation.package-qualification-binding
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.delivery-chain
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind local finished-image qualification to immutable image identity and relevant input hashes before publication.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.validation.package-qualification-workflow
#     path: scripts/04.deploy/lifecycle/40-package/package-custody-receipt/workflow_guard.py
"""Bind local qualification to the exact image ID and selected non-secret inputs."""
import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path


def image_id(reference):
    value = subprocess.run(["docker", "image", "inspect", reference, "--format", "{{.Id}}"], capture_output=True, text=True, check=True, timeout=30).stdout.strip()
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", value): raise ValueError("qualification-image-identity-invalid")
    return value


def configuration_fingerprint(adapter_name, source, selector):
    root=Path.cwd().resolve();adapter=(root/adapter_name).resolve()
    allowed=root/'scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters'
    if not adapter.is_relative_to(allowed) or adapter.suffix!='.py':raise ValueError('configuration-adapter-invalid')
    spec=importlib.util.spec_from_file_location('package_configuration_adapter',adapter);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    projection=module.package_projection(Path(source),selector)
    return {'adapter':adapter_name,'source':source,'selector':selector,'adapter_sha256':hashlib.sha256(adapter.read_bytes()).hexdigest(),'projection_sha256':hashlib.sha256(json.dumps(projection,sort_keys=True,separators=(',',':')).encode()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["record", "verify"])
    parser.add_argument("--image", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--input", action="append", default=[])
    parser.add_argument("--configuration-input", nargs=3, action="append", default=[], metavar=("ADAPTER", "SOURCE", "CONTAINERS"))
    args = parser.parse_args()
    identity = image_id(args.image)
    if args.operation == "record":
        if not args.input: raise ValueError("qualification-inputs-missing")
        inputs = {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in args.input}
        configurations=[configuration_fingerprint(*item) for item in args.configuration_input]
        receipt={"schema":"deploy/local-image-qualification/v1","image_id":identity,"inputs":inputs}
        if configurations:receipt['configuration_inputs']=configurations
        with args.receipt.open("x") as file:json.dump(receipt,file,sort_keys=True)
    else:
        data = json.loads(args.receipt.read_text())
        if data.get("schema") != "deploy/local-image-qualification/v1" or data.get("image_id") != identity: raise ValueError("qualification-image-mismatch")
        if not isinstance(data.get("inputs"), dict) or not data["inputs"]: raise ValueError("qualification-inputs-missing")
        if any(hashlib.sha256(Path(name).read_bytes()).hexdigest() != digest for name, digest in data["inputs"].items()): raise ValueError("qualification-inputs-changed")
        configurations=data.get('configuration_inputs',[])
        if not isinstance(configurations,list):raise ValueError('qualification-configuration-invalid')
        expected=[list(item) for item in args.configuration_input]
        actual=[[item.get('adapter'),item.get('source'),item.get('selector')] for item in configurations if isinstance(item,dict)]
        if expected and actual!=expected:raise ValueError('qualification-required-configuration-missing')
        for item in configurations:
            if not isinstance(item,dict) or set(item)!={'adapter','source','selector','adapter_sha256','projection_sha256'} or configuration_fingerprint(item['adapter'],item['source'],item['selector'])!=item:raise ValueError('qualification-configuration-changed')
        print(identity)
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except (OSError, ValueError, TypeError, KeyError, AttributeError, ImportError, subprocess.SubprocessError):
        print(json.dumps({"verdict": "failed", "code": "qualification-binding-invalid"}))
        raise SystemExit(1)
