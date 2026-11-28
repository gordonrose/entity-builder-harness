#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.aws.session-cli
#   version: 3
#   status: active
#   created_on: "2026-11-27"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.provider-outcomes
#   disciplines: [security, sre]
#   kind: script
#   purpose: Transport closed temporary-session AWS calls through existing invocation mechanics without granting authority or retrying.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.library.aws.environment-sessions
#     path: scripts/04.deploy/shared/provider-adapters/aws/environment_sessions.py
#   - id: deploy.test.aws.environment-sessions
#     path: scripts/04.deploy/shared/provider-adapters/aws/environment-sessions-test.py
"""Closed session transport, not permission, expiry or ownership qualification.

Callers retain admission, evidence interpretation and reservation ownership.
Automatic CLI pagination completes observations within one process deadline;
that deadline does not bound buffered response bytes or the number of pages.
"""
import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile


_SPEC = importlib.util.spec_from_file_location("aws_session_transport_cli", Path(__file__).with_name("cli.py"))
CLI = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(CLI)

# Supported serialized requests are bounded independently of template size:
# escaping and parameters can make a valid 51200-byte template exceed this cap.
MAX_INPUT_BYTES = 131072
CLI_FAILURE_CODES = frozenset({
    "aws-access-denied", "aws-credentials-expired", "aws-command-timeout",
    "aws-command-unavailable", "aws-response-invalid", "aws-parameter-invalid",
    "aws-command-failed", "aws-resource-missing",
})
FAILURE_CODES = CLI_FAILURE_CODES | frozenset({
    "session-provider-context-invalid", "session-provider-operation-unsupported",
    "session-provider-arguments-invalid", "session-provider-input-too-large",
    "session-provider-input-unavailable",
})
_ARGUMENTS = {
    ("ec2", "describe-regions"): {"AllRegions": bool},
    ("backup", "list-backup-plans"): {"IncludeDeleted": bool},
    ("sts", "get-caller-identity"): {},
    ("sts", "assume-role"): {"RoleArn": str, "RoleSessionName": str, "DurationSeconds": int},
    ("codebuild", "batch-get-projects"): {"names": list},
    ("codebuild", "batch-get-builds"): {"ids": list},
    ("codebuild", "list-builds-for-project"): {"projectName": str, "sortOrder": str},
    ("s3api", "get-bucket-versioning"): {"Bucket": str, "ExpectedBucketOwner": str},
    ("s3api", "get-bucket-encryption"): {"Bucket": str, "ExpectedBucketOwner": str},
    ("s3api", "get-public-access-block"): {"Bucket": str, "ExpectedBucketOwner": str},
    ("s3api", "get-bucket-ownership-controls"): {"Bucket": str, "ExpectedBucketOwner": str},
    ("s3api", "get-bucket-policy"): {"Bucket": str, "ExpectedBucketOwner": str},
    ("stepfunctions", "start-execution"): {"stateMachineArn": str, "name": str, "input": str},
    ("stepfunctions", "describe-execution"): {"executionArn": str},
    ("stepfunctions", "describe-state-machine"): {"stateMachineArn": str},
    ("stepfunctions", "stop-execution"): {"executionArn": str, "error": str, "cause": str},
    ("cloudformation", "create-change-set"): {
        "StackName": str, "ChangeSetName": str, "ChangeSetType": str,
        "TemplateBody": str, "Parameters": list, "Capabilities": list,
        "ClientToken": str, "Description": str, "RoleARN": str,
    },
    ("cloudformation", "execute-change-set"): {
        "StackName": str, "ChangeSetName": str, "ClientRequestToken": str, "DisableRollback": bool,
    },
    ("cloudformation", "delete-stack"): {"StackName": str, "ClientRequestToken": str, "RoleARN": str},
    ("cloudformation", "describe-change-set"): {"StackName": str, "ChangeSetName": str},
    ("cloudformation", "describe-stack-events"): {"StackName": str},
    ("cloudformation", "validate-template"): {"TemplateBody": str},
    ("iam", "simulate-principal-policy"): {"PolicySourceArn": str, "ActionNames": list, "ResourceArns": list},
    ("cloudformation", "describe-stacks"): {"StackName": str},
    ("cloudformation", "get-template"): {"StackName": str, "TemplateStage": str},
    ("cloudformation", "list-stack-resources"): {"StackName": str},
    ("ec2", "describe-availability-zones"): {"ZoneNames": list},
    ("ec2", "describe-managed-prefix-lists"): {"Filters": list},
    ("ec2", "describe-vpcs"): {"VpcIds": list},
    ("ec2", "describe-subnets"): {"SubnetIds": list},
    ("ec2", "describe-route-tables"): {"RouteTableIds": list},
    ("ec2", "describe-vpc-endpoints"): {"VpcEndpointIds": list},
    ("ec2", "describe-security-groups"): {"GroupIds": list},
    ("rds", "describe-db-instances"): {"DBInstanceIdentifier": str},
    ("rds", "describe-db-subnet-groups"): {"DBSubnetGroupName": str},
    ("rds", "describe-db-snapshots"): {"SnapshotType": str, "IncludePublic": bool, "IncludeShared": bool},
    ("rds", "describe-db-instance-automated-backups"): {},
    ("route53", "get-hosted-zone"): {"Id": str},
    ("iam", "get-role"): {"RoleName": str},
    ("iam", "tag-role"): {"RoleName": str, "Tags": list},
    ("iam", "list-role-policies"): {"RoleName": str},
    ("iam", "list-attached-role-policies"): {"RoleName": str},
    ("iam", "get-role-policy"): {"RoleName": str, "PolicyName": str},
    ("iam", "get-policy"): {"PolicyArn": str},
    ("iam", "get-policy-version"): {"PolicyArn": str, "VersionId": str},
    ("secretsmanager", "describe-secret"): {"SecretId": str},
    ("ecs", "describe-clusters"): {"clusters": list},
    ("ecs", "describe-task-definition"): {"taskDefinition": str},
    ("ecs", "describe-services"): {"cluster": str, "services": list},
    ("servicediscovery", "get-namespace"): {"Id": str},
    ("servicediscovery", "get-service"): {"Id": str},
    ("logs", "describe-log-groups"): {"logGroupIdentifiers": list},
    ("ecr", "describe-repositories"): {"repositoryNames": list},
    ("ecr", "batch-get-image"): {
        "repositoryName": str, "imageIds": list, "acceptedMediaTypes": list,
    },
    ("ecr", "describe-image-scan-findings"): {
        "repositoryName": str, "imageId": dict, "maxResults": int,
    },
}
_EMPTY = frozenset({("cloudformation", "execute-change-set"), ("cloudformation", "delete-stack"), ("iam", "tag-role")})


class SessionProviderFailure(Exception):
    """A finite condition only; native stderr, arguments and causes stay private."""
    def __init__(self, code):
        self.code = code if type(code) is str and code in FAILURE_CODES else "aws-command-failed"
        super().__init__(self.code)


def _json_value(value, depth=0):
    if depth > 32:
        return False
    if type(value) is dict:
        return all(type(key) is str and _json_value(item, depth + 1) for key, item in value.items())
    if type(value) is list:
        return all(_json_value(item, depth + 1) for item in value)
    return value is None or type(value) in (str, bool, int, float)


def _encoded(arguments):
    try:
        if not _json_value(arguments):
            raise SessionProviderFailure("session-provider-arguments-invalid")
        raw = json.dumps(arguments, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, OverflowError, RecursionError, UnicodeError):
        raise SessionProviderFailure("session-provider-arguments-invalid") from None
    if len(raw) > MAX_INPUT_BYTES:
        raise SessionProviderFailure("session-provider-input-too-large")
    return raw


class SessionProvider:
    """One closed invocation per call; construction and import make no remote call."""
    def __init__(self, *, profile, region, environment):
        if not ((profile is None or type(profile) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.@+=,-]{0,127}", profile))
                and type(region) is str and re.fullmatch(r"[a-z]{2}(?:-[a-z]+)+-[0-9]+", region)
                and type(environment) is dict
                and all(type(key) is str and type(value) is str for key, value in environment.items())):
            raise SessionProviderFailure("session-provider-context-invalid")
        self._profile, self._region = profile, region
        self._environment = {**environment, "AWS_MAX_ATTEMPTS": "1", "AWS_PAGER": "",
                             "AWS_CLI_AUTO_PROMPT": "off", "AWS_IGNORE_CONFIGURED_ENDPOINT_URLS": "true"}
        if profile is None:
            self._environment.pop("AWS_PROFILE", None)
            self._environment.pop("AWS_DEFAULT_PROFILE", None)

    def observe_region(self, region, service, operation, **arguments):
        """Cross-region metadata only; no regional mutation escape."""
        if (service, operation) not in {("rds", "describe-db-snapshots"), ("rds", "describe-db-instance-automated-backups")}:
            raise SessionProviderFailure("session-provider-operation-unsupported")
        return SessionProvider(profile=self._profile, region=region, environment=self._environment)(service, operation, **arguments)

    def __call__(self, service, operation, **arguments):
        if type(service) is not str or type(operation) is not str or (service, operation) not in _ARGUMENTS:
            raise SessionProviderFailure("session-provider-operation-unsupported")
        selection = (service, operation)
        shape = _ARGUMENTS[selection]
        if selection == ("cloudformation", "get-template") and "ChangeSetName" in arguments:
            shape = {**shape, "ChangeSetName": str}
        if selection == ("ec2", "describe-route-tables") and "Filters" in arguments:
            shape = {"Filters": list}
        if selection == ("ecs", "describe-task-definition") and "include" in arguments:
            shape = {**shape, "include": list}
        if (set(arguments) != set(shape)
                or any(type(arguments[key]) is not expected for key, expected in shape.items())
                or any(not arguments[key] for key, expected in shape.items() if expected is str)):
            raise SessionProviderFailure("session-provider-arguments-invalid")
        if selection == ("cloudformation", "get-template") and arguments["TemplateStage"] != "Original":
            raise SessionProviderFailure("session-provider-arguments-invalid")
        if selection == ("iam", "tag-role") and not (len(arguments["Tags"]) == 1
                and type(arguments["Tags"][0]) is dict and set(arguments["Tags"][0]) == {"Key", "Value"}
                and arguments["Tags"][0]["Key"] == "kanbien:session-vpc-id"
                and type(arguments["Tags"][0]["Value"]) is str
                and re.fullmatch(r"vpc-[0-9a-f]{8}(?:[0-9a-f]{9})?", arguments["Tags"][0]["Value"])):
            raise SessionProviderFailure("session-provider-arguments-invalid")
        if selection in (("ec2", "describe-regions"), ("backup", "list-backup-plans")) and next(iter(arguments.values())) is not False:
            raise SessionProviderFailure("session-provider-arguments-invalid")
        if "RoleARN" in arguments and re.fullmatch(r"arn:aws:iam::[0-9]{12}:role/[A-Za-z0-9+=,.@_-]{1,64}", arguments["RoleARN"]) is None:
            raise SessionProviderFailure("session-provider-arguments-invalid")
        if selection == ("ecs", "describe-task-definition") and "include" in arguments and arguments["include"] != ["TAGS"]:
            raise SessionProviderFailure("session-provider-arguments-invalid")
        if selection == ("cloudformation", "execute-change-set") and arguments["DisableRollback"] is not True:
            raise SessionProviderFailure("session-provider-arguments-invalid")
        if selection == ("rds", "describe-db-snapshots") and (arguments["SnapshotType"] not in ("manual", "automated", "awsbackup")
                or arguments["IncludePublic"] is not False or arguments["IncludeShared"] is not False):
            raise SessionProviderFailure("session-provider-arguments-invalid")
        for key in ("VpcIds", "SubnetIds", "RouteTableIds", "VpcEndpointIds", "GroupIds", "clusters", "services", "logGroupIdentifiers"):
            if key in arguments and not (len(arguments[key]) == 1 and type(arguments[key][0]) is str and arguments[key][0]):
                raise SessionProviderFailure("session-provider-arguments-invalid")
        if selection == ("ec2", "describe-route-tables") and "Filters" in arguments:
            filters = arguments["Filters"]
            if not (len(filters) == 1 and type(filters[0]) is dict and set(filters[0]) == {"Name", "Values"}
                    and filters[0]["Name"] == "association.route-table-association-id"
                    and type(filters[0]["Values"]) is list and len(filters[0]["Values"]) == 1
                    and type(filters[0]["Values"][0]) is str and filters[0]["Values"][0]):
                raise SessionProviderFailure("session-provider-arguments-invalid")
        raw = _encoded(arguments)
        pagination = []
        if selection == ("ecr", "describe-image-scan-findings"):
            if arguments["maxResults"] != 1:
                raise SessionProviderFailure("session-provider-arguments-invalid")
            # Page size controls each service response, never the total result.
            raw = _encoded({key: value for key, value in arguments.items() if key != "maxResults"})
            pagination = ["--page-size", "1"]
        failure, response = None, None
        try:
            with tempfile.TemporaryDirectory(prefix="aws-session-request-") as directory:
                path = Path(directory) / "arguments.json"
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(raw)
                command = [
                    "aws", service, operation, "--cli-input-json", "file://" + str(path),
                    *pagination, *(["--profile", self._profile] if self._profile is not None else []), "--region", self._region,
                    "--output", "json", "--no-cli-pager", "--no-cli-auto-prompt",
                    "--cli-connect-timeout", "10", "--cli-read-timeout", "20",
                ]
                try:
                    response = CLI.invoke_json(
                        command, timeout=35, empty_body="empty-string" if selection in _EMPTY else "reject",
                        object_only=True, environment=self._environment,
                    )
                except CLI.CliFailure as problem:
                    code = problem.code if problem.code in CLI_FAILURE_CODES else "aws-command-failed"
                    failure = SessionProviderFailure(code)
        except (OSError, TypeError, ValueError, OverflowError, RecursionError, UnicodeError):
            # A failed temporary-file cleanup must not erase a known provider
            # failure; neither outcome authorizes the caller to replay a write.
            if failure is None:
                failure = SessionProviderFailure("session-provider-input-unavailable")
        if failure is not None:
            raise failure from None
        if (any(response.get(key) not in (None, "") for key in ("NextToken", "nextToken", "next_token", "Marker", "marker", "NextMarker"))
                or response.get("IsTruncated", False) is not False):
            raise SessionProviderFailure("aws-response-invalid")
        return response
