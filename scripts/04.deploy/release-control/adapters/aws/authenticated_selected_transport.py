"""Bounded authenticated AWS CLI transport for the selected store; no authority."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.aws-authenticated-selected-transport
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Convert only the selected store protocol to authenticated AWS CLI calls and preserve safe failure boundaries.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [network]
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

import selected_control_plane as control
import selected_store as store


MAX_BYTES = 65536
ROLE_ARN = re.compile(r"^arn:aws:sts::337159794548:assumed-role/kanbien-staging-platform-shell-release-control-controller/[A-Za-z0-9+=,.@_-]{2,64}$")


class TransportFailure(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def fail(code):
    raise TransportFailure(code)


class AuthenticatedSelectedTransport:
    """A fixed adapter. Construction grants nothing; each run first verifies identity."""

    def __init__(self, *, _runner=None):
        self.config = control.configuration()
        self._runner = _runner
        self._identity_checked = False

    def _request(self, service, operation, parameters):
        if (type(service) is not str or type(operation) is not str or type(parameters) is not dict
                or len(control.canonical(parameters)) > MAX_BYTES):
            fail("selected-transport-request-invalid")
        return {"service": service, "operation": operation, "region": self.config["region"], "parameters": parameters}

    def verify_identity(self):
        response = self._invoke(self._request("sts", "GetCallerIdentity", {}), identity=True)
        if (type(response) is not dict or set(response) != {"Account", "Arn", "UserId"}
                or response["Account"] != self.config["account_id"] or type(response["UserId"]) is not str
                or not ROLE_ARN.fullmatch(response["Arn"])):
            fail("selected-transport-identity-invalid")
        self._identity_checked = True

    def __call__(self, request):
        if not self._identity_checked:
            self.verify_identity()
        return self._invoke(request)

    def _invoke(self, request, *, identity=False):
        if type(request) is not dict or set(request) != {"service", "operation", "region", "parameters"}:
            fail("selected-transport-request-invalid")
        if request["region"] != self.config["region"]:
            fail("selected-transport-region-invalid")
        permitted = {("sts", "GetCallerIdentity"), ("dynamodb", "TransactGetItems"),
                     ("dynamodb", "TransactWriteItems"), ("s3", "PutObject"), ("s3", "GetObject")}
        if (request["service"], request["operation"]) not in permitted or (identity and request["operation"] != "GetCallerIdentity"):
            fail("selected-transport-operation-invalid")
        if not identity and not self._identity_checked:
            fail("selected-transport-identity-required")
        self._validate_parameters(request)
        if self._runner is not None:
            try:
                response = self._runner(request)
            except Exception:
                fail("selected-transport-outcome-unknown")
            if type(response) is not dict:
                fail("selected-transport-response-invalid")
            return response
        return self._aws_cli(request)

    def _validate_parameters(self, request):
        service, operation, parameters = request["service"], request["operation"], request["parameters"]
        if (service, operation) == ("sts", "GetCallerIdentity"):
            if parameters:
                fail("selected-transport-request-invalid")
            return
        if (service, operation) == ("dynamodb", "TransactGetItems"):
            rows = parameters.get("TransactItems")
            if (set(parameters) != {"TransactItems"} or type(rows) is not list or len(rows) != 2
                    or any(type(row) is not dict or set(row) != {"Get"} or type(row["Get"]) is not dict
                           or row["Get"].get("TableName") != self.config["journal"]["table_name"] for row in rows)):
                fail("selected-transport-request-invalid")
            return
        if (service, operation) == ("dynamodb", "TransactWriteItems"):
            rows, token = parameters.get("TransactItems"), parameters.get("ClientRequestToken")
            if (set(parameters) != {"TransactItems", "ClientRequestToken"} or type(rows) is not list or len(rows) != 4
                    or not re.fullmatch(r"[0-9a-f]{32}", token if type(token) is str else "")
                    or any(type(row) is not dict or len(row) != 1 or next(iter(row)) not in {"ConditionCheck", "Put"}
                           or type(next(iter(row.values()))) is not dict
                           or next(iter(row.values())).get("TableName") != self.config["journal"]["table_name"] for row in rows)):
                fail("selected-transport-request-invalid")
            return
        if (service, operation) == ("s3", "PutObject"):
            required = {"Bucket", "Key", "Body", "ContentType", "ServerSideEncryption", "ChecksumSHA256", "IfNoneMatch", "ExpectedBucketOwner"}
            body, checksum = parameters.get("Body"), parameters.get("ChecksumSHA256")
            if (set(parameters) != required or parameters["Bucket"] != self.config["evidence"]["bucket_name"]
                    or type(parameters["Key"]) is not str or not parameters["Key"].startswith(self.config["evidence"]["prefix"])
                    or parameters["ExpectedBucketOwner"] != self.config["account_id"] or parameters["ContentType"] != "application/json"
                    or parameters["ServerSideEncryption"] != "AES256" or parameters["IfNoneMatch"] != "*"
                    or type(body) is not bytes or len(body) > MAX_BYTES or type(checksum) is not str
                    or checksum != base64.b64encode(hashlib.sha256(body).digest()).decode("ascii")):
                fail("selected-transport-request-invalid")
            return
        if (service, operation) == ("s3", "GetObject"):
            required = {"Bucket", "Key", "ExpectedBucketOwner", "VersionId", "ChecksumMode"}
            if (set(parameters) != required or parameters["Bucket"] != self.config["evidence"]["bucket_name"]
                    or type(parameters["Key"]) is not str or not parameters["Key"].startswith(self.config["evidence"]["prefix"])
                    or parameters["ExpectedBucketOwner"] != self.config["account_id"] or parameters["ChecksumMode"] != "ENABLED"
                    or type(parameters["VersionId"]) is not str or not parameters["VersionId"]):
                fail("selected-transport-request-invalid")
            return
        fail("selected-transport-operation-invalid")

    def _run(self, command):
        environment = dict(os.environ)
        environment.update({"AWS_PAGER": "", "AWS_CLI_AUTO_PROMPT": "off", "AWS_MAX_ATTEMPTS": "1", "AWS_RETRY_MODE": "standard"})
        try:
            result = subprocess.run(["aws", *command, "--profile", "kanbien-dev", "--region", self.config["region"], "--output", "json"],
                                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    check=False, timeout=30, env=environment)
        except (OSError, subprocess.SubprocessError):
            fail("selected-transport-outcome-unknown")
        if result.returncode != 0 or len(result.stdout) > MAX_BYTES:
            fail("selected-transport-outcome-unknown")
        try:
            response = json.loads(result.stdout.decode("utf-8"), parse_constant=lambda _: fail("selected-transport-response-invalid"))
        except (UnicodeError, ValueError):
            fail("selected-transport-response-invalid")
        if type(response) is not dict:
            fail("selected-transport-response-invalid")
        return response

    def _aws_cli(self, request):
        service, operation, parameters = request["service"], request["operation"], request["parameters"]
        if (service, operation) == ("sts", "GetCallerIdentity"):
            if parameters:
                fail("selected-transport-request-invalid")
            return self._run(["sts", "get-caller-identity"])
        if (service, operation) == ("dynamodb", "TransactGetItems"):
            if set(parameters) != {"TransactItems"}:
                fail("selected-transport-request-invalid")
            return self._run(["dynamodb", "transact-get-items", "--transact-items", control.canonical(parameters["TransactItems"]).decode("ascii")])
        if (service, operation) == ("dynamodb", "TransactWriteItems"):
            if set(parameters) != {"TransactItems", "ClientRequestToken"} or not re.fullmatch(r"[0-9a-f]{32}", parameters["ClientRequestToken"]):
                fail("selected-transport-request-invalid")
            return self._run(["dynamodb", "transact-write-items", "--transact-items", control.canonical(parameters["TransactItems"]).decode("ascii"),
                              "--client-request-token", parameters["ClientRequestToken"]])
        if (service, operation) == ("s3", "PutObject"):
            with tempfile.TemporaryDirectory() as directory:
                body = Path(directory) / "body.json"
                body.write_bytes(parameters["Body"])
                return self._run(["s3api", "put-object", "--bucket", parameters["Bucket"], "--key", parameters["Key"],
                                  "--expected-bucket-owner", parameters["ExpectedBucketOwner"], "--body", str(body),
                                  "--content-type", parameters["ContentType"], "--server-side-encryption", "AES256",
                                  "--checksum-sha256", parameters["ChecksumSHA256"], "--if-none-match", "*"])
        if (service, operation) == ("s3", "GetObject"):
            required = {"Bucket", "Key", "ExpectedBucketOwner", "VersionId", "ChecksumMode"}
            if set(parameters) != required or parameters["Bucket"] != self.config["evidence"]["bucket_name"] or parameters["ExpectedBucketOwner"] != self.config["account_id"] or parameters["ChecksumMode"] != "ENABLED":
                fail("selected-transport-request-invalid")
            with tempfile.TemporaryDirectory() as directory:
                body = Path(directory) / "body.json"
                response = self._run(["s3api", "get-object", "--bucket", parameters["Bucket"], "--key", parameters["Key"],
                                      "--expected-bucket-owner", parameters["ExpectedBucketOwner"], "--version-id", parameters["VersionId"],
                                      "--checksum-mode", "ENABLED", str(body)])
                try:
                    payload = body.read_bytes()
                except OSError:
                    fail("selected-transport-response-invalid")
                if len(payload) > MAX_BYTES:
                    fail("selected-transport-response-invalid")
                return {**response, "Body": payload}
        fail("selected-transport-operation-invalid")


def authenticated_store(generation, *, _runner=None):
    """Verify the dedicated role before exposing the existing selected-store protocol."""
    transport = AuthenticatedSelectedTransport(_runner=_runner)
    transport.verify_identity()
    return store.SelectedStore(generation, _transport=transport)
