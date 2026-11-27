#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.adapter.aws.lambda-runtime-configuration
#   version: 1
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.delivery-chain
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind managed image qualification to the selected Lambda configuration and its complete declarative resource closure.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.scheduling.immutable-publication
#     path: scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/publication.py
import importlib.util
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[6]
OWNER = ROOT / "scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py"
spec = importlib.util.spec_from_file_location("lambda_cloudformation_template", OWNER)
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)

def package_projection(path, selector):
    """The template is one configuration unit; include it whole to retain transitive IAM/network references."""
    if not isinstance(selector, str) or not re.fullmatch(r"(?:core-server-persistence|entity-smoke)\.(?:dispatch|worker)", selector):
        raise ValueError("package-lambda-selector-invalid")
    scope, purpose = selector.split(".")
    try:
        document = parser.template(Path(path).read_text())
        resource = document["Resources"]["DispatchFunction" if purpose == "dispatch" else "WorkerFunction"]
        properties = resource["Properties"]
        variables = properties["Environment"]["Variables"]
        if resource["Type"] != "AWS::Lambda::Function" or properties["PackageType"] != "Image": raise ValueError()
        if properties["Architectures"] != ["x86_64"] or properties["Timeout"] != 60 or properties["MemorySize"] != 512: raise ValueError()
        if "ImageConfig" in properties or variables.get("NODE_ENV") != "production": raise ValueError()
        if any(not isinstance(key, str) or key.startswith(("PERSISTENCE_LOCAL_QUALIFICATION_", "AWS_ACCESS_KEY", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "NODE_OPTIONS")) for key in variables): raise ValueError()
        if properties["Code"] != {"ImageUri": {"Ref": "DispatchImageUri" if purpose == "dispatch" else "WorkerImageUri"}}: raise ValueError()
        if scope not in document["Mappings"]["Scopes"]: raise ValueError()
    except (OSError, KeyError, TypeError, AttributeError, ValueError):
        raise ValueError("package-lambda-configuration-invalid") from None
    return {"schema": "deploy/lambda-package-configuration/v1", "scope": scope, "purpose": purpose, "template": document}
