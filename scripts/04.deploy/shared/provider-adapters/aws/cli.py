#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.aws.cli-invocation
#   version: 1
#   status: active
#   created_on: "2026-11-14"
#   updated_on: "2026-11-15"
#   layer: 04.deploy
#   domain: deployment.provider-outcomes
#   disciplines: [security, sre]
#   kind: script
#   purpose: Execute one caller-approved AWS CLI invocation and classify its response without granting authority or retrying.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network]
#   used_by:
#   - id: deploy.command.entity-smoke.infrastructure.implementation
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/script.py
#   - id: deploy.command.entity-smoke.target-alignment.implementation
#     path: scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/entity-smoke/script.py
"""Private invocation mechanics; callers own arguments, admission and retry policy."""
import importlib.util
import json
from pathlib import Path
import re
import subprocess

_SPEC = importlib.util.spec_from_file_location("aws_cli_response", Path(__file__).with_name("response.py"))
_RESPONSE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_RESPONSE)


class CliFailure(Exception):
    """Finite classification; original causes are only for existing caller chaining."""
    def __init__(self, code, phase, *, cause=None, transport_timeout=False):
        super().__init__(code)
        self.code, self.phase, self.cause = code, phase, cause
        self.transport_timeout = transport_timeout


def invoke_json(arguments, *, timeout, empty_body, object_only, environment=None,
                cwd=None, timeout_endpoint=None, classify_errors=True, check=None):
    """Exactly one process, with explicit caller response/environment policies.

    Empty-body policy is 'empty-string', 'whitespace', or 'reject'. None for
    environment/cwd/check preserves the omitted subprocess option. No default
    credential, endpoint, operation allowlist or retry capability is introduced.
    """
    if empty_body not in {"empty-string", "whitespace", "reject"}:
        raise ValueError("unsupported AWS CLI empty-body policy")
    options = {"capture_output": True, "text": True, "timeout": timeout}
    if environment is not None: options["env"] = environment
    if cwd is not None: options["cwd"] = cwd
    if check is not None: options["check"] = check
    try:
        result = subprocess.run(arguments, **options)
    except subprocess.TimeoutExpired as error:
        raise CliFailure("aws-command-timeout", "process", cause=error) from None
    except OSError as error:
        raise CliFailure("aws-command-unavailable", "process", cause=error) from None
    except UnicodeError as error:
        raise CliFailure("aws-response-invalid", "process", cause=error) from None
    if result.returncode:
        exact_timeout = timeout_endpoint is not None and re.fullmatch(
            r'aws: \[ERROR\]: (?:Connect|Read) timeout on endpoint URL: "' +
            re.escape(timeout_endpoint) + r'/?"', result.stderr.strip()) is not None
        code = _RESPONSE.classify_error(arguments[1], arguments[2], result.stderr) if classify_errors else "aws-command-failed"
        raise CliFailure(code, "service", transport_timeout=exact_timeout)
    output = result.stdout
    if empty_body == "empty-string": output = output or "{}"
    if empty_body == "whitespace" and not output.strip(): output = "{}"
    try:
        value = json.loads(output)
    except json.JSONDecodeError as error:
        raise CliFailure("aws-response-invalid", "response", cause=error) from None
    if object_only and not isinstance(value, dict):
        raise CliFailure("aws-response-invalid", "response")
    return value
