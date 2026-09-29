#!/usr/bin/env python3
"""Compatibility entry point; the operational realization gate owns compilation."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.command.release-control-compiler-compatibility
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Preserve the draft compiler path while delegating to the existing realization capability.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.readme.release-control-compatibility
#     path: scripts/04.deploy/release-control/README.md

import json
import sys
from pathlib import Path

def main():
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "operational-realization-gate"))
    try:
        from release_compiler import main as compile_main
    except ImportError:
        print(json.dumps({"schema": "release-control-result/v1", "scope": "release-definition",
                          "verdict": "failed", "authorized": False,
                          "findings": [{"code": "compiler-dependency-unavailable"}]}, sort_keys=True))
        return 1
    args = sys.argv[1:]
    if args and not args[0].startswith("-"):
        args.insert(0, "--release")
    return compile_main(args)

if __name__ == "__main__":
    raise SystemExit(main())
