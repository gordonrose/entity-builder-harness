"""Source-only tests for the exact selected journal, evidence and controller boundary."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.selected-control-plane
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: test
#   purpose: Reject changed selected control resources, retention/recovery policy and broadened IAM before AWS creation.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [read-only]
from copy import deepcopy
import sys
import unittest
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORY))
import selected_control_plane as subject


class SelectedControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.config = subject.configuration()
        self.template = subject.template(config=self.config)

    def reject(self, code, callback, *args):
        with self.assertRaises(subject.ControlPlaneFailure) as found:
            callback(*args)
        self.assertEqual(code, found.exception.code)

    def test_compiles_exact_four_resource_policy_without_authority(self):
        result = subject.compile_control_plane(self.config, self.template)
        self.assertEqual(("selected-control-plane-result/v1", "selected-staging-control-plane", "compiled"),
                         (result["schema"], result["scope"], result["verdict"]))
        self.assertEqual(["ReleaseControlControllerRole", "ReleaseControlEvidenceBucket",
                          "ReleaseControlEvidenceBucketPolicy", "ReleaseControlJournalTable"], result["resources"])
        self.assertFalse(result["authorized"])
        self.assertEqual(("blocked", "blocked"), (result["release_eligibility"], result["operation_authorization"]))
        self.assertNotEqual(result["configuration_digest"], result["template_digest"])

    def test_changed_policy_values_or_extra_fields_fail(self):
        cases = (
            ("selected-control-plane-configuration-invalid", lambda value: value["evidence"].update(minimum_retention_days=89)),
            ("selected-control-plane-configuration-invalid", lambda value: value["recovery"].update(point_in_time_recovery_days=34)),
            ("selected-control-plane-configuration-invalid", lambda value: value["lease"].update(seconds=61)),
            ("selected-control-plane-configuration-invalid", lambda value: value["cost"].update(monthly_ceiling_usd=6)),
            ("selected-control-plane-configuration-invalid", lambda value: value.update(secret_reference="unsafe")),
        )
        for code, change in cases:
            with self.subTest(code=code):
                value = deepcopy(self.config)
                change(value)
                self.reject(code, subject.configuration, value)

    def test_extra_resource_ttl_or_missing_protection_fails(self):
        changed = deepcopy(self.template)
        changed["Resources"]["Unexpected"] = {"Type": "AWS::SQS::Queue"}
        self.reject("selected-control-plane-resource-set-invalid", subject.template, changed, self.config)
        changed = deepcopy(self.template)
        changed["Resources"]["ReleaseControlJournalTable"]["Properties"]["TimeToLiveSpecification"] = {"Enabled": True, "AttributeName": "expiry"}
        self.reject("selected-control-plane-journal-invalid", subject.template, changed, self.config)
        changed = deepcopy(self.template)
        del changed["Resources"]["ReleaseControlEvidenceBucket"]["Properties"]["VersioningConfiguration"]
        self.reject("selected-control-plane-evidence-invalid", subject.template, changed, self.config)

    def test_broadened_iam_or_unbound_bucket_policy_fails(self):
        changed = deepcopy(self.template)
        statement = changed["Resources"]["ReleaseControlControllerRole"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"]
        next(row for row in statement if row["Sid"] == "OperateOnlySelectedJournal")["Action"].append("dynamodb:DeleteItem")
        self.reject("selected-control-plane-iam-broadened", subject.template, changed, self.config)
        changed = deepcopy(self.template)
        statement = changed["Resources"]["ReleaseControlControllerRole"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"]
        next(row for row in statement if row["Sid"] == "OperateOnlySelectedEvidenceObjects")["Resource"] = "*"
        self.reject("selected-control-plane-iam-resource-invalid", subject.template, changed, self.config)
        changed = deepcopy(self.template)
        policy = changed["Resources"]["ReleaseControlEvidenceBucketPolicy"]["Properties"]["PolicyDocument"]["Statement"]
        next(row for row in policy if row["Sid"] == "DenyEvidenceOverwriteWithoutConditionalCreate")["Condition"] = {}
        self.reject("selected-control-plane-bucket-policy-invalid", subject.template, changed, self.config)

    def test_trust_cannot_be_moved_to_an_unprotected_ref(self):
        changed = deepcopy(self.template)
        trust = changed["Resources"]["ReleaseControlControllerRole"]["Properties"]["AssumeRolePolicyDocument"]["Statement"][0]
        trust["Condition"]["StringEquals"]["token.actions.githubusercontent.com:ref"] = "refs/heads/feature"
        self.reject("selected-control-plane-trust-invalid", subject.template, changed, self.config)

    def test_result_never_grants_execution_authority(self):
        self.reject("selected-control-plane-authority-unavailable", subject.require_execution_authority,
                    subject.compile_control_plane(self.config, self.template))


if __name__ == "__main__":
    unittest.main()
