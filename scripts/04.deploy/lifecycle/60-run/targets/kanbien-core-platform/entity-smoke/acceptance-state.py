#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.acceptance-state.implementation
#   version: 1
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Validate exact retained feature candidate/current custody through the existing release-succession owner without provider queries or current-health claims.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.entity-smoke.acceptance-state
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-state.sh
import argparse
import importlib.util
import json
from pathlib import Path
import re
import tempfile


spec = importlib.util.spec_from_file_location("entity_smoke_acceptance_state_collector", Path(__file__).with_name("acceptance-route.py"))
K = importlib.util.module_from_spec(spec); spec.loader.exec_module(K)
S, A = K.S, K.A
SOURCE_ROOT = K.C.ROOT
EVIDENCE_PATH = K.EVIDENCE_ROOT.relative_to(SOURCE_ROOT)


class StateFailure(K.CollectionFailure): pass


def require(value, code):
    if not value: raise StateFailure(code)


def bounded(path, limit):
    K.C.RESOURCE.CONTROL.no_symlinks(path)
    try:
        with path.open("rb") as stream: raw = stream.read(limit + 1)
    except OSError: raise StateFailure("acceptance-state-record-unavailable") from None
    require(len(raw) <= limit, "acceptance-state-record-too-large")
    return raw


class State:
    def __init__(self, root=SOURCE_ROOT, *, rehearsal=False):
        root = root.absolute()
        K.C.RESOURCE.CONTROL.no_symlinks(root)
        temporary = Path(tempfile.gettempdir()).resolve()
        if rehearsal:
            require(root != temporary and root.is_relative_to(temporary) and not root.is_relative_to(SOURCE_ROOT)
                    and not SOURCE_ROOT.is_relative_to(root), "acceptance-state-rehearsal-root-invalid")
        else: require(root == SOURCE_ROOT, "acceptance-state-root-invalid")
        self.base, self.root, self.evidence_class = root, root / EVIDENCE_PATH, "simulated" if rehearsal else "live"
        S.REPOSITORY_ROOT, S.EVIDENCE_CLASS = root, self.evidence_class

    def candidate(self, path, *, current_contracts=True):
        K.C.RESOURCE.CONTROL.no_symlinks(path.absolute())
        path = S.under(self.root, path.absolute(), S.CANDIDATE_DIRECTORY)
        raw = bounded(path, 65536)
        try: record = K.C.yaml.safe_load(raw)
        except (ValueError, UnicodeError, K.C.yaml.YAMLError): raise StateFailure("acceptance-state-candidate-invalid") from None
        require(isinstance(record, dict) and set(record) == {"schema", "target", "scope", "status", "evidence_class", "release", "proof", "proof_set"}, "acceptance-state-candidate-invalid")
        proofs = record.get("proof_set")
        require(isinstance(proofs, dict) and set(proofs) == {"entity-smoke-complete-proof"}, "acceptance-state-proof-set-incomplete")
        entry = proofs["entity-smoke-complete-proof"]
        require(isinstance(entry, dict) and set(entry) == {"path", "sha256"} and isinstance(entry["path"], str)
                and re.fullmatch(r"proof-receipts/entity-smoke-[a-f0-9]{64}\.json", entry["path"]), "acceptance-state-proof-reference-invalid")
        K.C.RESOURCE.CONTROL.no_symlinks(self.root / entry["path"])
        proof_path = S.retained_evidence_file(self.root, self.root / entry["path"])
        proof_bytes = bounded(proof_path, K.MAX_PACKET_BYTES)
        require(S.sha256_bytes(proof_bytes) == entry["sha256"], "acceptance-state-proof-hash-mismatch")
        try: packet = json.loads(proof_bytes)
        except (ValueError, UnicodeError, RecursionError): raise StateFailure("acceptance-state-proof-invalid") from None
        K.validate_packet(packet, evidence_class=self.evidence_class)
        require(proof_bytes == S.canonical(packet) + b"\n" and proof_path.name == "entity-smoke-" + A.digest(packet)[7:] + ".json", "acceptance-state-proof-reference-invalid")
        target, scope, image, identity = S.candidate_identity(record, self.root, current_contracts=current_contracts)
        binding = packet["binding"]
        require((target, scope) == (K.TARGET, K.SCOPE) and image == binding["image_digest"] and identity["source_revision"] == binding["source_revision"]
                and path.name == S.release_id(identity) + ".yml" and record["proof"]["accepted_at"] == packet["runtime"]["observed_at"], "acceptance-state-candidate-binding-mismatch")
        require(identity["configuration_contract"] == {"path": str((K.C.CONTRACT.parent / "declaration-contract.yml").relative_to(SOURCE_ROOT)), "sha256": binding["configuration_contract_sha256"]}
                and identity["permission_contract"] == {"path": str(K.C.DEPLOY.SOURCE.relative_to(SOURCE_ROOT)), "sha256": binding["permission_contract_sha256"]}, "acceptance-state-contract-binding-mismatch")
        return {"record": record, "packet": packet, "identity": identity, "path": path, "sha256": S.sha256_bytes(raw)}

    def current(self, *, allow_missing=False):
        K.C.RESOURCE.CONTROL.no_symlinks(self.root / S.CURRENT)
        state = S.current(self.root)
        if state is None:
            require(allow_missing, "acceptance-state-current-required")
            policy = S.recovery_policy(self.root, self.base / K.C.CONTRACT.parent.relative_to(SOURCE_ROOT) / "declaration-contract.yml")
            require(policy["accepted_release_id"] == "none", "acceptance-state-current-required")
            return None
        require((state["target"], state["scope"]) == (K.TARGET, K.SCOPE), "acceptance-state-current-binding-mismatch")
        K.C.RESOURCE.CONTROL.no_symlinks(self.root / state["record"]["path"])
        history_path = S.under(self.root, self.root / state["record"]["path"], S.HISTORY_DIRECTORY)
        bounded(history_path, 65536)
        history, _ = S.document(history_path)
        require(history["evidence"]["kind"] == "verified-release-candidate", "acceptance-state-feature-candidate-required")
        result = self.candidate(self.root / history["evidence"]["path"], current_contracts=False)
        require(S.release_id(result["identity"]) == state["release_id"], "acceptance-state-current-binding-mismatch")
        return {"reference": state, **result}


def parse(arguments=None):
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.error = lambda _message: (_ for _ in ()).throw(StateFailure("acceptance-state-arguments-invalid"))
    parser.add_argument("--operation", required=True, choices=("validate-candidate", "validate-current", "current-release"))
    parser.add_argument("--candidate-record", type=Path)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--root", type=Path, default=SOURCE_ROOT)
    parser.add_argument("--rehearsal-root", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    args = parser.parse_args(arguments)
    require((args.operation == "validate-candidate") == (args.candidate_record is not None)
            and (args.record is None or args.operation == "validate-current"), "acceptance-state-arguments-invalid")
    return args


def main():
    try:
        args = parse()
        if args.validate_arguments:
            print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": []})); return 0
        owner = State(args.rehearsal_root or args.root, rehearsal=args.rehearsal_root is not None)
        if args.record is not None:
            require(args.record.absolute() == owner.root / S.CURRENT, "acceptance-state-current-reference-invalid")
        result = owner.candidate(args.candidate_record) if args.operation == "validate-candidate" else owner.current(allow_missing=args.operation == "current-release")
        release = "none" if result is None else S.release_id(result["identity"])
        print(json.dumps({"schema": "deploy/entity-smoke-acceptance-state-report/v1", "verdict": "validated", "target": K.TARGET, "scope": K.SCOPE,
            "release_id": release, "evidence_class": owner.evidence_class, "current_readiness": False, "findings": []})); return 0
    except Exception as failure:
        details = K.failure_details(failure)
        print(json.dumps({"schema": "deploy/entity-smoke-acceptance-state-report/v1", "verdict": "blocked", "target": K.TARGET, "scope": K.SCOPE,
            **details, "effect": "read-only-no-provider-query", "current_readiness": False}, sort_keys=True)); return 1


if __name__ == "__main__": raise SystemExit(main())
