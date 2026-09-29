"""Existing-gate command surface for isolated artifact evidence verification."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.artifact-admission-cli
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify pinned artifact bundles and expose explicit public verifier acquisition without provider mutation.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

import json
import sys
import time

import artifact_admission as admission
import artifact_verifier as verifier
import release_compiler as release


def failure(code):
    """Bootstrap failure output cannot depend on the file/schema that just failed."""
    try:
        return admission.finish(admission.initial(int(time.time())), code)
    except Exception:
        return {'schema': 'artifact-admission-error/v1', 'scope': 'artifact-supply-chain',
                'authorized': False, 'release_eligibility': 'blocked',
                'operation_authorization': 'blocked', 'qualification_verdict': 'blocked',
                'verdict': 'blocked', 'findings': [{'code': 'schema-invalid'}]}


def main(argv=None):
    try:
        argv = list(sys.argv[1:] if argv is None else argv)
        options = [value.split('=', 1)[0] for value in argv if value.startswith('--')]
        if len(options) != len(set(options)):
            verifier.fail('input-invalid')
        parser = release.SafeParser(add_help=False, allow_abbrev=False)
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument('--artifact-admission', action='store_true')
        mode.add_argument('--artifact-verifier-acquire', action='store_true')
        mode.add_argument('--artifact-verifier-conformance', action='store_true')
        parser.add_argument('--verifier-cache', required=True)
        parser.add_argument('--policy')
        parser.add_argument('--artifact')
        parser.add_argument('--image-config')
        parser.add_argument('--provenance-bundle')
        parser.add_argument('--sbom-bundle')
        parser.add_argument('--scan-bundle')
        args = parser.parse_args(argv)
        inputs = [args.policy, args.artifact, args.image_config, args.provenance_bundle, args.sbom_bundle, args.scan_bundle]
        if args.artifact_admission:
            if not all(inputs):
                verifier.fail('input-invalid')
            policy = verifier.json_bytes(verifier.read_bytes(args.policy))
            artifact = verifier.read_bytes(args.artifact)
            bundles = {name: verifier.read_bytes(getattr(args, name + '_bundle'))
                       for name in ('provenance', 'sbom', 'scan')}
            result = admission.admit(policy, artifact, bundles, args.verifier_cache, verifier.read_bytes(args.image_config))
            status = 0 if result['verdict'] == 'verified' else 1
        else:
            if any(inputs):
                verifier.fail('input-invalid')
            if args.artifact_verifier_acquire:
                lock = verifier.acquire(args.verifier_cache)
                result = {'schema': 'artifact-verifier-acquisition/v1', 'authorized': False,
                          'verdict': 'acquired', 'binary_digest': lock['binary_digest'],
                          'trusted_root_digest': lock['trusted_root_digest']}
            else:
                from artifact_verifier_conformance import conformance
                result = conformance(args.verifier_cache)
            status = 0
    except (verifier.AdmissionFailure, release.ReleaseFailure) as error:
        code = error.code if isinstance(error, verifier.AdmissionFailure) else 'input-invalid'
        result, status = failure(code), 1
    except Exception:
        result, status = failure('input-invalid'), 1
    print(json.dumps(result, sort_keys=True))
    return status


if __name__ == '__main__':
    raise SystemExit(main())
