#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.adapter.aws.cloudformation-template
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.delivery-chain
#   disciplines: [security, sre]
#   kind: script
#   purpose: Normalize provider CloudFormation template bodies for exact source comparison while rejecting ambiguous mappings.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.kanbien-core-platform.execute-runtime-change-set
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/deploy-candidate/deploy.py
#   - id: deploy.adapter.platform-shell-release-control
#     path: scripts/04.deploy/reconcile-platform-shell-staging/release_control.py
"""AWS syntax normalization only; deployment qualification remains target-owned."""
import json
import yaml


class Loader(yaml.SafeLoader):
    pass


def mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str) or key in result:
            raise ValueError("cloudformation-template-mapping-invalid")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


def intrinsic(loader, tag, node):
    value = loader.construct_scalar(node) if isinstance(node, yaml.ScalarNode) else loader.construct_sequence(node) if isinstance(node, yaml.SequenceNode) else mapping(loader, node)
    if tag == "GetAtt" and isinstance(value, str):
        value = value.split(".", 1)
    return {tag if tag == "Ref" else "Fn::" + tag: value}


Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
Loader.add_multi_constructor("!", intrinsic)


def template(raw):
    try:
        value = yaml.load(raw, Loader=Loader) if isinstance(raw, str) else raw
        if not isinstance(value, dict) or not value:
            raise ValueError("cloudformation-template-body-invalid")
        # Reject recursive aliases, non-JSON values and non-finite numbers.
        json.dumps(value, sort_keys=True, allow_nan=False)
        return value
    except (yaml.YAMLError, TypeError, ValueError, RecursionError) as error:
        raise ValueError("cloudformation-template-body-invalid") from error


def templates_equal(left, right):
    # JSON canonicalization preserves scalar types (Python considers True == 1).
    return json.dumps(template(left), sort_keys=True, allow_nan=False) == json.dumps(template(right), sort_keys=True, allow_nan=False)
