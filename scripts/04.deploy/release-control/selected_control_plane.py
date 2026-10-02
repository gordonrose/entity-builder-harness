"""Validate the exact selected AWS store and controller source contract; no AWS calls."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.selected-control-plane
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Compile and reject drift in the approved four-resource selected release-control source boundary.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [read-only]
import hashlib
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[3]
CONFIGURATION = ROOT / "infra/04.deploy/03.product/targets/kanbien/staging/release-control/control-plane.v1.yml"
TEMPLATE = ROOT / "infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/release-control.yml"
SCHEMA = ROOT / "infra/04.deploy/contracts/release-control/v1/selected-control-plane.schema.yml"
RESOURCES = frozenset({"ReleaseControlJournalTable", "ReleaseControlEvidenceBucket",
                       "ReleaseControlEvidenceBucketPolicy", "ReleaseControlControllerRole"})
BLOCKED = {"authorized": False, "release_eligibility": "blocked", "operation_authorization": "blocked"}


class ControlPlaneFailure(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def fail(code):
    raise ControlPlaneFailure(code)


def canonical(value):
    try:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    except (TypeError, ValueError, RecursionError):
        fail("selected-control-plane-record-invalid")
    if len(raw) > 65536:
        fail("selected-control-plane-record-invalid")
    return raw


def digest(value):
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def load(path, code):
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        fail(code)
    if type(value) is not dict:
        fail(code)
    canonical(value)
    return value


def configuration(value=None):
    value = load(CONFIGURATION, "selected-control-plane-configuration-unreadable") if value is None else value
    schema = load(SCHEMA, "selected-control-plane-schema-unreadable")
    try:
        Draft202012Validator.check_schema(schema)
        if next(Draft202012Validator(schema).iter_errors(value), None):
            fail("selected-control-plane-configuration-invalid")
    except ControlPlaneFailure:
        raise
    except Exception:
        fail("selected-control-plane-schema-invalid")
    if value["authority"]["execution_minutes"] + value["authority"]["recovery_minutes"] != value["authority"]["window_minutes"]:
        fail("selected-control-plane-authority-budget-invalid")
    if value["lease"]["renew_every_seconds"] >= value["lease"]["minimum_effect_seconds"] or value["lease"]["minimum_effect_seconds"] >= value["lease"]["seconds"]:
        fail("selected-control-plane-lease-budget-invalid")
    return value


def _statements(policy):
    if type(policy) is not dict or policy.get("Version") != "2012-10-17":
        fail("selected-control-plane-policy-invalid")
    rows = policy.get("Statement")
    if type(rows) is not list or len({row.get("Sid") for row in rows if type(row) is dict}) != len(rows):
        fail("selected-control-plane-policy-invalid")
    return {row["Sid"]: row for row in rows if type(row) is dict and type(row.get("Sid")) is str}


def _exact_actions(statement, actions):
    value = statement.get("Action")
    actual = {value} if type(value) is str else set(value) if type(value) is list and all(type(x) is str for x in value) else set()
    if actual != set(actions):
        fail("selected-control-plane-iam-broadened")


def _resource(statement, expected):
    if statement.get("Resource") != expected:
        fail("selected-control-plane-iam-resource-invalid")


def template(value=None, config=None):
    config = configuration(config)
    value = load(TEMPLATE, "selected-control-plane-template-unreadable") if value is None else value
    resources = value.get("Resources")
    if type(resources) is not dict or set(resources) != RESOURCES:
        fail("selected-control-plane-resource-set-invalid")
    table = resources["ReleaseControlJournalTable"]
    if (table.get("Type") != "AWS::DynamoDB::Table" or table.get("DeletionPolicy") != "Retain"
            or table.get("UpdateReplacePolicy") != "Retain"):
        fail("selected-control-plane-journal-invalid")
    table_properties = table.get("Properties")
    expected_table = {
        "TableName": config["journal"]["table_name"], "BillingMode": "PAY_PER_REQUEST", "TableClass": "STANDARD",
        "AttributeDefinitions": [{"AttributeName": "pk", "AttributeType": "S"}, {"AttributeName": "sk", "AttributeType": "S"}],
        "KeySchema": [{"AttributeName": "pk", "KeyType": "HASH"}, {"AttributeName": "sk", "KeyType": "RANGE"}],
        "PointInTimeRecoverySpecification": {"PointInTimeRecoveryEnabled": True},
        "SSESpecification": {"SSEEnabled": True},
    }
    if type(table_properties) is not dict or any(table_properties.get(key) != part for key, part in expected_table.items()) or "TimeToLiveSpecification" in table_properties:
        fail("selected-control-plane-journal-invalid")
    bucket = resources["ReleaseControlEvidenceBucket"]
    bucket_properties = bucket.get("Properties") if type(bucket) is dict else None
    expected_bucket = {
        "BucketName": config["evidence"]["bucket_name"],
        "BucketEncryption": {"ServerSideEncryptionConfiguration": [{"ServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]},
        "VersioningConfiguration": {"Status": "Enabled"},
        "OwnershipControls": {"Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]},
        "PublicAccessBlockConfiguration": {"BlockPublicAcls": True, "BlockPublicPolicy": True,
                                           "IgnorePublicAcls": True, "RestrictPublicBuckets": True},
    }
    if (bucket.get("Type") != "AWS::S3::Bucket" or bucket.get("DeletionPolicy") != "Retain"
            or bucket.get("UpdateReplacePolicy") != "Retain" or type(bucket_properties) is not dict
            or any(bucket_properties.get(key) != part for key, part in expected_bucket.items())
            or "LifecycleConfiguration" in bucket_properties):
        fail("selected-control-plane-evidence-invalid")
    role = resources["ReleaseControlControllerRole"]
    properties = role.get("Properties") if type(role) is dict else None
    if role.get("Type") != "AWS::IAM::Role" or type(properties) is not dict or properties.get("RoleName") != config["executor"]["role_name"] or properties.get("MaxSessionDuration") != config["executor"]["max_session_seconds"]:
        fail("selected-control-plane-role-invalid")
    trust = _statements(properties.get("AssumeRolePolicyDocument"))
    if set(trust) != {"TrustedProtectedStagingWorkflow"}:
        fail("selected-control-plane-trust-invalid")
    trust_row = trust["TrustedProtectedStagingWorkflow"]
    if (trust_row.get("Effect") != "Allow" or trust_row.get("Action") != "sts:AssumeRoleWithWebIdentity"
            or trust_row.get("Principal") != {"Federated": "arn:aws:iam::337159794548:oidc-provider/token.actions.githubusercontent.com"}):
        fail("selected-control-plane-trust-invalid")
    conditions = trust_row.get("Condition")
    if conditions != {
        "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                         "token.actions.githubusercontent.com:repository": config["executor"]["github_repository"],
                         "token.actions.githubusercontent.com:ref": config["executor"]["github_ref"]},
        "StringLike": {"token.actions.githubusercontent.com:sub":
                       "repo:" + config["executor"]["github_repository"] + ":environment:" + config["executor"]["github_environment"]},
    }:
        fail("selected-control-plane-trust-invalid")
    policies = properties.get("Policies")
    if type(policies) is not list or len(policies) != 1 or policies[0].get("PolicyName") != "selected-release-control-store-only":
        fail("selected-control-plane-iam-invalid")
    statements = _statements(policies[0].get("PolicyDocument"))
    if set(statements) != {"VerifyControllerIdentity", "OperateOnlySelectedJournal", "OperateOnlySelectedEvidenceObjects", "ListOnlySelectedEvidencePrefix"}:
        fail("selected-control-plane-iam-invalid")
    _exact_actions(statements["VerifyControllerIdentity"], {"sts:GetCallerIdentity"})
    _resource(statements["VerifyControllerIdentity"], "*")
    _exact_actions(statements["OperateOnlySelectedJournal"], {"dynamodb:TransactGetItems", "dynamodb:TransactWriteItems"})
    _resource(statements["OperateOnlySelectedJournal"], {"Fn::GetAtt": ["ReleaseControlJournalTable", "Arn"]})
    _exact_actions(statements["OperateOnlySelectedEvidenceObjects"], {"s3:GetObject", "s3:GetObjectVersion", "s3:PutObject"})
    _resource(statements["OperateOnlySelectedEvidenceObjects"], {"Fn::Sub": "${ReleaseControlEvidenceBucket.Arn}/" + config["evidence"]["prefix"] + "*"})
    _exact_actions(statements["ListOnlySelectedEvidencePrefix"], {"s3:ListBucket"})
    _resource(statements["ListOnlySelectedEvidencePrefix"], {"Fn::GetAtt": ["ReleaseControlEvidenceBucket", "Arn"]})
    policy = resources["ReleaseControlEvidenceBucketPolicy"]
    if policy.get("Type") != "AWS::S3::BucketPolicy" or policy.get("Properties", {}).get("Bucket") != {"Ref": "ReleaseControlEvidenceBucket"}:
        fail("selected-control-plane-bucket-policy-invalid")
    bucket_statements = _statements(policy.get("Properties", {}).get("PolicyDocument"))
    if set(bucket_statements) != {"DenyInsecureTransport", "DenyEvidenceOverwriteWithoutConditionalCreate", "PermitOnlyControllerEvidenceObjects", "PermitOnlyControllerEvidenceList"}:
        fail("selected-control-plane-bucket-policy-invalid")
    conditional = bucket_statements["DenyEvidenceOverwriteWithoutConditionalCreate"]
    if (conditional.get("Effect") != "Deny" or conditional.get("Principal") != "*" or conditional.get("Action") != "s3:PutObject"
            or conditional.get("Condition") != {"Null": {"s3:if-none-match": "true"}}):
        fail("selected-control-plane-bucket-policy-invalid")
    return value


def compile_control_plane(config=None, source_template=None):
    config = configuration(config)
    source_template = template(source_template, config)
    result = {"schema": "selected-control-plane-result/v1", "scope": "selected-staging-control-plane",
              "verdict": "compiled", "configuration_digest": digest(config), "template_digest": digest(source_template),
              "resources": sorted(RESOURCES), **BLOCKED,
              "findings": [{"code": "selected-control-plane-creation-unapproved"}, {"code": "selected-control-plane-authority-unavailable"}]}
    result["result_digest"] = digest(result)
    return result


def require_execution_authority(result):
    if type(result) is not dict or result.get("schema") != "selected-control-plane-result/v1":
        fail("selected-control-plane-result-invalid")
    fail("selected-control-plane-authority-unavailable")
