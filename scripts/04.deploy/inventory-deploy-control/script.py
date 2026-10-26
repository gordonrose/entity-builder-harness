#!/usr/bin/env python3
"""Generate the authoritative source delivery census without provider access."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
from delivery_inventory import report, markdown


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery', action='store_true', help='Compatibility alias; delivery coverage is now the default report.')
    parser.add_argument('--root', type=Path, help='Inspect a disposable repository fixture.')
    parser.add_argument('--json', action='store_true', help='Emit all discovered routes, chains, findings and hashed inputs as JSON.')
    parser.add_argument('--check', action='store_true', help='Exit nonzero for any unsupported, unregistered or incomplete delivery route.')
    arguments = parser.parse_args()
    try:
        root = arguments.root.resolve() if arguments.root else Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip())
        value = report(root)
    except (OSError, ValueError, TypeError, subprocess.SubprocessError) as exc:
        value = {'schema': 'deploy/delivery-coverage-report/v1', 'verdict': 'gap', 'findings': [{'code': 'delivery-inventory-input-invalid', 'path': '.', 'error': type(exc).__name__}]}
        print(json.dumps(value, sort_keys=True) if arguments.json else 'Delivery inventory could not read a valid source tree (' + type(exc).__name__ + ').', file=sys.stdout)
        return 1
    print(json.dumps(value, indent=2, sort_keys=True) if arguments.json else markdown(value))
    return 1 if arguments.check and value['findings'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
