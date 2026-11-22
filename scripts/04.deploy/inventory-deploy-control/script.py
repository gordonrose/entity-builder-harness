#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.compiler.inventory-deploy-control
#   version: 2
#   status: active
#   created_on: "2026-10-06"
#   updated_on: "2026-11-22"
#   layer: 04.deploy
#   domain: deployment.governance
#   disciplines: [architecture, sre]
#   kind: script
#   purpose: Emit read-only delivery coverage or deployment script topology observations from repository source.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.inventory-deploy-control.wrapper
#     path: scripts/04.deploy/inventory-deploy-control/script.sh
"""Generate the authoritative source delivery census without provider access."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
from delivery_inventory import report, markdown
from script_topology import markdown as topology_markdown
from script_topology import report as topology_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery', action='store_true', help='Compatibility alias; delivery coverage is now the default report.')
    parser.add_argument('--root', type=Path, help='Inspect a disposable repository fixture.')
    parser.add_argument('--json', action='store_true', help='Emit all discovered routes, chains, findings and hashed inputs as JSON.')
    parser.add_argument('--check', action='store_true', help='Exit nonzero for any unsupported, unregistered or incomplete delivery route.')
    parser.add_argument('--topology', action='store_true', help='Emit the read-only scripts ownership, placement and migration-disposition view.')
    arguments = parser.parse_args()
    if arguments.topology and arguments.check:
        parser.error('--topology is an observation and cannot be combined with --check')
    try:
        root = arguments.root.resolve() if arguments.root else Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip())
        value = topology_report(root) if arguments.topology else report(root)
    except (OSError, ValueError, TypeError, subprocess.SubprocessError) as exc:
        schema = 'deploy/script-topology-inventory/v1' if arguments.topology else 'deploy/delivery-coverage-report/v1'
        value = {'schema': schema, 'verdict': 'gap', 'findings': [{'code': 'inventory-input-invalid', 'path': '.', 'error': type(exc).__name__}]}
        label = 'Script topology inventory' if arguments.topology else 'Delivery inventory'
        print(json.dumps(value, sort_keys=True) if arguments.json else label + ' could not read a valid source tree (' + type(exc).__name__ + ').', file=sys.stdout)
        return 1
    print(json.dumps(value, indent=2, sort_keys=True) if arguments.json else (topology_markdown(value) if arguments.topology else markdown(value)))
    return 1 if arguments.check and value['findings'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
