"""Selected candidate start/stop intent has durable bounded local conformance only."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.candidate-lifecycle
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: test
#   purpose: Verify selected start/stop reservations, safe identity binding, restart recovery and expired-writer refusal.
#   portability: {class: internal, targets: [kanbien-staging]}
#   effects: [writes-files]
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

import candidate_lifecycle as candidate
import control_store_fixtures as fixtures
import operation_actions as actions
import operation_journal as journal
import selected_admission as admission
import selected_admission_cli as admission_cli

DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[2]
BLUEPRINT = ROOT / "infra/04.deploy/03.product/targets/kanbien/staging/operational-realization/target-release-blueprint.v1.yml"
REVISION = "a" * 40
IMAGE = "sha256:" + "b" * 64
TASK = "sha256:" + "e" * 64
IDENTITY = {"cluster_digest": "sha256:" + "c" * 64, "task_revision_digest": "sha256:" + "d" * 64,
            "image_digest": IMAGE}
SENTINEL = "RAW-TASK-HANDLE-MUST-NOT-ESCAPE"


class CandidateLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = admission_cli.load_compiler()
        blueprint = compiler.release.load_document(BLUEPRINT)
        baseline = compiler.compile_blueprint(ROOT, blueprint, REVISION, IMAGE, "candidate-lifecycle-baseline")
        proposed = compiler.compile_blueprint(ROOT, blueprint, REVISION, IMAGE, "candidate-lifecycle-proposed")
        cls.admission = admission.compile_admission(baseline, proposed)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.now = fixtures.NOW
        self.store = actions.OperationActionStore(self.tmp.name, _clock=lambda: self.now)
        self.addCleanup(self.store.close)
        self.attempt = candidate.make_attempt(self.admission, IDENTITY)
        self.intent = candidate.make_control_intent(self.attempt)
        self.store.prepare_attempt(self.intent, self.attempt)
        self.claim = self.store.claim(self.intent["operation_id"], fixtures.OWNER_A)

    def reject(self, code, callback, *args, **kwargs):
        with self.assertRaises(journal.ControlFailure) as found:
            callback(*args, **kwargs)
        self.assertEqual(code, found.exception.code)

    def snapshot(self):
        return self.store.read(self.intent["operation_id"])

    def history(self):
        return self.store.read_actions(self.intent["operation_id"])

    def advance(self, event, evidence=None):
        return self.store.advance(self.claim, self.snapshot()["revision"], event, evidence)

    def reserve(self, action):
        return self.store.reserve_action(self.claim, self.history()["revision"], action)

    def observe(self, ticket, state, **changes):
        value = candidate.observation(self.attempt, state, TASK, **IDENTITY)
        value.update(changes)
        return self.store.observe_action(self.claim, self.history()["revision"], ticket, value)

    def begin(self):
        self.advance("effect-intent")

    def test_start_and_stop_reservations_precede_each_safe_observation(self):
        self.reject("action-reconciliation-only", self.reserve, "start")
        self.begin()
        start = self.reserve("start")
        self.assertGreater(self.store.action_budget(self.claim, self.history()["revision"], start), 0)
        self.assertEqual(start["event_digest"], candidate.request_token(start))
        self.observe(start, "running")
        stop = self.reserve("stop")
        self.assertGreater(self.store.action_budget(self.claim, self.history()["revision"], stop), 0)
        self.assertEqual(stop["event_digest"], candidate.request_token(stop))
        self.observe(stop, "stopped")
        history = self.history()
        self.assertEqual(["attachment-bound", "reserved", "observed", "reserved", "observed"],
                         [row["event"] for row in history["records"]])
        self.assertEqual(["start", "stop"], [row["action"] for row in history["records"] if row["event"] == "reserved"])
        self.assertEqual(TASK, history["known_resource_id"])
        self.assertFalse(history["authorized"])
        self.assertNotIn(SENTINEL, repr(history))

    def test_wrong_task_cluster_revision_or_image_is_refused_without_a_second_request(self):
        self.begin()
        ticket = self.reserve("start")
        for field, value in (("task_id_digest", "sha256:" + "f" * 64),
                             ("cluster_digest", "sha256:" + "f" * 64),
                             ("task_revision_digest", "sha256:" + "f" * 64),
                             ("image_digest", "sha256:" + "f" * 64),
                             ("resource_id", SENTINEL)):
            with self.subTest(field=field):
                observation = candidate.observation(self.attempt, "running", TASK, **IDENTITY)
                observation[field] = value
                self.reject("candidate-lifecycle-record-invalid" if field == "resource_id"
                            else "candidate-lifecycle-observation-binding-invalid",
                            self.store.observe_action, self.claim, self.history()["revision"], ticket, observation)
        self.assertEqual(1, self.history()["counts"]["start"])
        self.assertEqual([], self.history()["observations"])
        self.assertNotIn(SENTINEL, repr(self.history()))

    def test_lost_start_response_survives_restart_and_cannot_be_reissued(self):
        self.begin()
        ticket = self.reserve("start")
        self.store.close()
        self.store = actions.OperationActionStore(self.tmp.name, _clock=lambda: self.now)
        self.addCleanup(self.store.close)
        self.now += 1001
        takeover = self.store.claim(self.intent["operation_id"], fixtures.OWNER_B)
        self.reject("claim-stale", self.store.action_budget, self.claim, self.history()["revision"], ticket)
        self.reject("action-budget-exhausted", self.store.reserve_action, takeover, self.history()["revision"], "start")
        self.assertEqual(("unknown", "reconcile"), (self.snapshot()["state"], self.snapshot()["mode"]))
        self.assertEqual([], self.history()["observations"])

    def test_expired_writer_is_fenced_and_unresolved_scope_cannot_reopen(self):
        self.begin()
        self.reserve("start")
        self.now += 1001
        takeover = self.store.claim(self.intent["operation_id"], fixtures.OWNER_B)
        self.reject("action-reconciliation-only", self.store.reserve_action, takeover, self.history()["revision"], "stop")
        conflicting = deepcopy(self.intent)
        conflicting["operation_id"] = "candidate-retry"
        conflicting["idempotency_key"] = journal.digest({"candidate_retry": 1})
        self.store.prepare(conflicting)
        self.reject("scope-unresolved", self.store.claim, conflicting["operation_id"], fixtures.OWNER_C)

    def test_verified_closed_scope_can_be_claimed_again_without_authorizing_the_attempt(self):
        self.begin()
        start = self.reserve("start")
        self.observe(start, "running")
        stop = self.reserve("stop")
        self.observe(stop, "stopped")
        self.advance("observed")
        self.advance("failed")
        proof = fixtures.evidence(self.intent, self.snapshot()["attempt"], "fixture-cleanup",
                                  now=self.now, resources=0, revision=self.snapshot()["revision"],
                                  fences=deepcopy(self.claim["fences"]))
        proof = self.store.put_evidence(self.claim, proof)
        self.advance("cleanup-verified", proof)
        self.advance("closed")
        self.assertEqual("closed", self.snapshot()["state"])
        retry = deepcopy(self.intent)
        retry["operation_id"] = "candidate-retry"
        retry["idempotency_key"] = journal.digest({"candidate_retry": 2})
        self.store.prepare(retry)
        claim = self.store.claim(retry["operation_id"], fixtures.OWNER_C)
        self.assertEqual("execute", claim["mode"])
        self.reject("candidate-lifecycle-authority-unavailable", candidate.require_execution_authority, self.attempt)


if __name__ == "__main__":
    unittest.main()
