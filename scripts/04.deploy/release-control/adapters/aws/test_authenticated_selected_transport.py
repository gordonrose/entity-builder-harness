"""Verify the selected AWS transport cannot widen or treat uncertainty as success."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.aws-authenticated-selected-transport
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [security, sre]
#   kind: test
#   purpose: Exercise the fixed authenticated store request boundary without an AWS call.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [read-only]
import base64
import hashlib
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parents[2] / "operational-realization-gate"))

import authenticated_selected_transport as transport

IDENTITY = {
    "Account": "337159794548",
    "Arn": "arn:aws:sts::337159794548:assumed-role/kanbien-staging-platform-shell-release-control-controller/source-test",
    "UserId": "source-test",
}
TABLE = "kanbien-staging-platform-shell-release-control"
BUCKET = "kanbien-staging-platform-shell-release-evidence-337159794548"
PREFIX = "kanbien/staging/operations/"


class AuthenticatedSelectedTransportTests(unittest.TestCase):
    def reject(self, callback, *args):
        with self.assertRaises(transport.TransportFailure) as found:
            callback(*args)
        self.assertIn(found.exception.code, {
            "selected-transport-request-invalid", "selected-transport-operation-invalid",
            "selected-transport-region-invalid", "selected-transport-identity-required",
            "selected-transport-outcome-unknown", "selected-transport-identity-invalid",
        })

    def test_identity_is_checked_before_only_the_fixed_store_request_set(self):
        calls = []

        def runner(request):
            calls.append(request)
            return IDENTITY if request["service"] == "sts" else {"Responses": []}

        value = transport.AuthenticatedSelectedTransport(_runner=runner)
        result = value(value._request("dynamodb", "TransactGetItems", {
            "TransactItems": [{"Get": {"TableName": TABLE}}, {"Get": {"TableName": TABLE}}]}))
        self.assertEqual({"Responses": []}, result)
        self.assertEqual(["sts", "dynamodb"], [row["service"] for row in calls])

    def test_bad_identity_and_runner_error_fail_closed(self):
        self.reject(transport.AuthenticatedSelectedTransport(
            _runner=lambda _: {**IDENTITY, "Account": "000000000000"}).verify_identity)
        value = transport.AuthenticatedSelectedTransport(
            _runner=lambda _: (_ for _ in ()).throw(OSError("offline")))
        self.reject(value.verify_identity)

    def test_rejects_every_non_selected_or_malformed_request_before_runner(self):
        calls = []
        value = transport.AuthenticatedSelectedTransport(_runner=lambda request: calls.append(request) or IDENTITY)
        bad = (
            {"service": "ecs", "operation": "RunTask", "region": "eu-west-1", "parameters": {}},
            {"service": "sts", "operation": "GetCallerIdentity", "region": "us-east-1", "parameters": {}},
            {"service": "dynamodb", "operation": "TransactWriteItems", "region": "eu-west-1",
             "parameters": {"TransactItems": [], "ClientRequestToken": "f" * 32}},
            {"service": "s3", "operation": "PutObject", "region": "eu-west-1", "parameters": {"Bucket": BUCKET}},
        )
        for request in bad:
            with self.subTest(request=request["operation"]):
                self.reject(value._invoke, request)
        self.assertEqual([], calls)

    def test_s3_write_shape_matches_immutable_store_and_maps_to_bounded_cli(self):
        body = b'{"proof":"fixture"}'
        checksum = base64.b64encode(hashlib.sha256(body).digest()).decode("ascii")
        request = {"service": "s3", "operation": "PutObject", "region": "eu-west-1", "parameters": {
            "Bucket": BUCKET, "Key": PREFIX + "a" * 32 + "/candidate-server/" + "b" * 64 + ".json",
            "ExpectedBucketOwner": "337159794548", "IfNoneMatch": "*", "Body": body,
            "ContentType": "application/json", "ServerSideEncryption": "AES256", "ChecksumSHA256": checksum}}
        value = transport.AuthenticatedSelectedTransport()
        value._identity_checked = True
        seen = []
        value._run = lambda command: seen.append(command) or {
            "VersionId": "version-1", "ChecksumSHA256": checksum, "ServerSideEncryption": "AES256"}
        result = value._invoke(request)
        self.assertEqual("version-1", result["VersionId"])
        self.assertIn("--if-none-match", seen[0])
        self.assertIn("--checksum-sha256", seen[0])
        self.assertIn("--server-side-encryption", seen[0])

    def test_dynamo_writes_are_fixed_to_four_selected_table_operations(self):
        request = {"service": "dynamodb", "operation": "TransactWriteItems", "region": "eu-west-1", "parameters": {
            "ClientRequestToken": "a" * 32, "TransactItems": [
                {"ConditionCheck": {"TableName": TABLE}}, {"Put": {"TableName": TABLE}},
                {"Put": {"TableName": TABLE}}, {"Put": {"TableName": TABLE}}]}}
        value = transport.AuthenticatedSelectedTransport(_runner=lambda _: {})
        value._identity_checked = True
        self.assertEqual({}, value._invoke(request))
        request["parameters"]["TransactItems"][0]["ConditionCheck"]["TableName"] = "other"
        self.reject(value._invoke, request)

    def test_authenticated_store_must_verify_the_dedicated_identity(self):
        instance = transport.authenticated_store(
            "a" * 32, _runner=lambda request: IDENTITY if request["service"] == "sts" else {})
        self.assertEqual("a" * 32, instance.generation)


if __name__ == "__main__":
    unittest.main()

