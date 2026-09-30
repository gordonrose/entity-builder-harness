"""Bounded local control-store conformance through the existing gate."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.control-store-cli
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Expose safe local control-store conformance without granting operation authority.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py
import argparse
import json
import sys

CODES = frozenset(('input-invalid', 'scratch-root-invalid', 'schema-invalid',
                   'source-invalid', 'source-changed', 'dependency-unavailable', 'conformance-failed'))

class InputFailure(Exception):
    pass

class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        raise InputFailure()


def failure(code):
    # Bootstrap errors must remain safe when a schema or dependency cannot load.
    if type(code) is not str or code not in CODES:
        code = 'conformance-failed'
    return {'schema': 'control-store-error/v1', 'scope': 'local-process-restart-conformance',
            'verdict': 'blocked', 'authorized': False, 'release_eligibility': 'blocked',
            'operation_authorization': 'blocked', 'qualification_verdict': 'blocked',
            'findings': [{'code': code}]}


def main(argv=None):
    result, status = failure('conformance-failed'), 1
    try:
        values = list(sys.argv[1:] if argv is None else argv)
        flags = [value.split('=', 1)[0] for value in values if value.startswith('--')]
        if len(flags) != len(set(flags)):
            raise InputFailure()
        parser = SafeParser(add_help=False, allow_abbrev=False)
        parser.add_argument('--control-store-conformance', action='store_true', required=True)
        parser.add_argument('--scratch-root', required=True)
        args = parser.parse_args(values)
    except Exception:
        result = failure('input-invalid')
    else:
        try:
            import operation_journal as contracts
            import control_store_conformance as runner
        except Exception:
            result = failure('dependency-unavailable')
        else:
            try:
                result = runner.conformance(args.scratch_root)
                contracts.validate('control-store-conformance', result)
                if contracts.digest({key: value for key, value in result.items()
                                     if key != 'result_digest'}) != result['result_digest']:
                    raise InputFailure()
                if any(result.get(key) != value for key, value in runner.bindings().items()):
                    raise InputFailure()
                status = 0
            except Exception as error:
                code = (error.code if type(error) is contracts.ControlFailure
                        and type(error.code) is str and error.code in CODES else 'conformance-failed')
                result = failure(code)
    print(json.dumps(result, sort_keys=True))
    return status


if __name__ == '__main__':
    raise SystemExit(main())
