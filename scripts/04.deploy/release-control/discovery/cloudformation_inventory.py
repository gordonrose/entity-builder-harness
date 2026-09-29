#!/usr/bin/env python3
"""Collect bounded CloudFormation reference structure; never evaluate provider state."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.release-control-cloudformation-inventory
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Resolve safe source-bound CloudFormation symbols and references without executing templates.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.release-control-source-inventory
#     path: scripts/04.deploy/release-control/discovery/source_inventory.py

from __future__ import annotations

from pathlib import PurePosixPath
import re

# Reviewed declarative families only. Native executables, custom resources,
# nested stacks, macros and unknown types remain unsupported source boundaries.
DECLARATIVE_RESOURCE_TYPES = frozenset({
    "AWS::Budgets::Budget", "AWS::CertificateManager::Certificate", "AWS::CloudWatch::Alarm",
    "AWS::DynamoDB::Table", "AWS::EC2::SecurityGroup", "AWS::EC2::SecurityGroupEgress",
    "AWS::EC2::SecurityGroupIngress", "AWS::ECR::Repository", "AWS::ECS::Service",
    "AWS::ElasticLoadBalancingV2::ListenerCertificate", "AWS::ElasticLoadBalancingV2::ListenerRule",
    "AWS::ElasticLoadBalancingV2::TargetGroup", "AWS::IAM::OIDCProvider", "AWS::IAM::Role",
    "AWS::Logs::LogGroup", "AWS::RDS::DBInstance", "AWS::RDS::DBParameterGroup",
    "AWS::RDS::DBSubnetGroup", "AWS::RDS::EventSubscription", "AWS::Route53::RecordSet",
    "AWS::S3::Bucket", "AWS::S3::BucketPolicy", "AWS::SNS::Subscription", "AWS::SNS::Topic",
    "AWS::SNS::TopicPolicy", "AWS::SQS::Queue", "AWS::SQS::QueuePolicy", "AWS::SSM::Parameter",
    "AWS::SecretsManager::Secret", "AWS::SecretsManager::SecretTargetAttachment",
    "AWS::WAFv2::WebACL", "AWS::WAFv2::WebACLAssociation",
})
MAX_SYMBOLS = 10000
MAX_REFERENCES = 50000
MAX_GROUPS = 256

PSEUDO = frozenset({"AWS::AccountId", "AWS::NotificationARNs", "AWS::NoValue", "AWS::Partition",
                   "AWS::Region", "AWS::StackId", "AWS::StackName", "AWS::URLSuffix"})
SYMBOL = re.compile(r"[A-Za-z][A-Za-z0-9]*\Z")
SUB_NAME = re.compile(r"[A-Za-z0-9_.:]+\Z")
SECTIONS = {"Resources": "resource", "Parameters": "parameter", "Conditions": "condition",
            "Mappings": "mapping", "Outputs": "output"}
ROOT_FIELDS = set(SECTIONS) | {"AWSTemplateFormatVersion", "Description", "Metadata", "Rules", "Transform"}
RESOURCE_FIELDS = {"Type", "Properties", "Condition", "DependsOn", "DeletionPolicy", "UpdateReplacePolicy", "Metadata", "CreationPolicy", "UpdatePolicy"}


def collect(collector):
    """Use only documents already read through the collector's no-follow reader."""
    docs = collector.infrastructure_documents
    by_path = {source["path"]: (source, document) for source, document in docs.values()}
    manifests = [(source, doc) for source, doc in docs.values()
                 if isinstance(doc, dict) and doc.get("schema") == "deploy/cloudformation-composition/v1"]
    claimed = set()
    groups = []
    for source, doc in sorted(manifests, key=lambda item: item[0]["path"]):
        fragments = doc.get("fragments")
        if (set(doc) - {"schema", "description", "fragments"} or not isinstance(fragments, list)
                or not fragments or len(fragments) > 256
                or any(not isinstance(item, str) for item in fragments)
                or len(set(fragments)) != len(fragments)):
            collector.issue(source["id"], "infrastructure-composition-invalid")
            continue
        members = []
        valid = True
        for relative in fragments:
            path = PurePosixPath(relative)
            if (not relative or not re.fullmatch(r"[A-Za-z0-9_./-]+", relative)
                    or path.is_absolute() or any(part in {"", ".", ".."} for part in relative.split("/"))):
                collector.issue(source["id"], "infrastructure-fragment-path-invalid")
                valid = False
                continue
            target = (PurePosixPath(source["path"]).parent / path).as_posix()
            member = by_path.get(target)
            if member is None or not isinstance(member[1], dict):
                collector.issue(source["id"], "infrastructure-fragment-missing")
                valid = False
                continue
            if target in claimed:
                collector.issue(source["id"], "infrastructure-fragment-shared")
                valid = False
            claimed.add(target)
            members.append(member)
            allowed = {"Parameters", "Resources", "Outputs", "AWSTemplateFormatVersion", "Description"}
            if set(member[1]) - allowed:
                collector.issue(member[0]["id"], "infrastructure-fragment-shape-unsupported")
                valid = False
        if valid:
            # The source renderer requires every section, including Outputs.
            scalar_counts = {key: sum(key in doc for _, doc in members)
                             for key in ("AWSTemplateFormatVersion", "Description")}
            if (any(count != 1 for count in scalar_counts.values())
                    or any(not any(doc.get(key) for _, doc in members)
                           for key in ("Parameters", "Resources", "Outputs"))):
                collector.issue(source["id"], "infrastructure-composition-invalid")
            groups.append((source, members))
    for source, doc in sorted(docs.values(), key=lambda item: item[0]["path"]):
        if (source["path"] not in claimed and isinstance(doc, dict)
                and ("Resources" in doc or any(key in doc for key in SECTIONS if key != "Resources"))
                and doc.get("schema") != "deploy/cloudformation-composition/v1"):
            groups.append((source, [(source, doc)]))
    if len(groups) > MAX_GROUPS:
        for source, _ in groups:
            collector.issue(source["id"], "infrastructure-reference-limit-exceeded")
        return
    for source, members in groups:
        _Template(collector, source, members).run()


class _Template:
    def __init__(self, collector, source, members):
        self.c = collector
        self.source = source
        self.members = members
        self.symbols = {}
        self.edges = {}
        self.owners = {}
        self.kinds = {}
        self.pseudos = {}
        self.reference_count = 0
        self.original_resource_issues = {row["id"]: row["issues"][:] for row in collector.observations.values()
                                         if row["kind"] == "resource"}

    def issue(self, source, code):
        self.c.issue(source["id"], code)

    def run(self):
        for source, doc in self.members:
            if set(doc) - ROOT_FIELDS:
                self.issue(source, "infrastructure-root-field-unsupported")
            if "Rules" in doc:
                self.issue(source, "infrastructure-rules-unsupported")
            if "Metadata" in doc:
                self.issue(source, "infrastructure-metadata-unsupported")
            # Unsupported root sections stay blocking but must not hide imports.
            root_owner = next(row["id"] for row in self.c.observations.values()
                              if row["kind"] == "source-file" and row["source_id"] == source["id"])
            for key, value in doc.items():
                if key not in SECTIONS:
                    self.walk(source, root_owner, [key], value)
            for section, kind in SECTIONS.items():
                values = doc.get(section, {})
                if not isinstance(values, dict):
                    self.issue(source, "infrastructure-symbol-shape-invalid")
                    continue
                for name, value in values.items():
                    if len(self.symbols) >= MAX_SYMBOLS:
                        self.issue(source, "infrastructure-reference-limit-exceeded")
                        return
                    if not SYMBOL.fullmatch(name) or not isinstance(value, dict):
                        self.issue(source, "infrastructure-symbol-shape-invalid")
                        continue
                    key = (kind, name)
                    if key in self.symbols or kind in {"resource", "parameter"} and any(
                            (other, name) in self.symbols for other in ("resource", "parameter")):
                        self.issue(source, "infrastructure-symbol-duplicate")
                        continue
                    if kind == "resource":
                        # Identical identity and detail to the original resource collector.
                        oid = self.c.observation(source, "resource", [section, name], value)
                        self.c.observations[oid]["issues"] = self.original_resource_issues.get(oid, [])
                    else:
                        oid = self.c.observation(source, "infrastructure-symbol", [section, name],
                                                 {"kind": kind, "definition": value})
                    if kind != "resource":
                        self.c.observations[oid]["symbol_kind"] = kind
                    self.symbols[key] = (oid, source, value)
                    self.owners[oid] = source
                    self.kinds[oid] = kind
                    self.edges[oid] = set()
        for (kind, name), (oid, source, value) in list(self.symbols.items()):
            if kind == "parameter":
                parameter_type = value.get("Type")
                if isinstance(parameter_type, str) and (parameter_type.startswith("AWS::") or parameter_type.startswith("List<AWS::")):
                    # AWS-specific input types bind existing provider objects;
                    # SSM value types additionally retrieve provider-side values.
                    self.external(source, oid, ["Parameters", name], value)
                elif not isinstance(parameter_type, str) or parameter_type not in {"String", "Number", "List<Number>", "CommaDelimitedList"}:
                    self.issue(source, "infrastructure-parameter-type-unsupported")
            if kind == "resource":
                if not isinstance(value, dict) or set(value) - RESOURCE_FIELDS:
                    self.issue(source, "infrastructure-resource-field-unsupported")
                if isinstance(value, dict):
                    for field in ("Metadata", "CreationPolicy", "UpdatePolicy"):
                        if field in value:
                            self.issue(source, "infrastructure-resource-behavior-unsupported")
                    if "Condition" in value:
                        self.reference(source, oid, ["Resources", name, "Condition"], value["Condition"], {"condition"}, "condition")
                    if "DependsOn" in value:
                        dependencies = value["DependsOn"]
                        dependencies = [dependencies] if isinstance(dependencies, str) else dependencies
                        if not isinstance(dependencies, list) or not dependencies or any(not isinstance(item, str) for item in dependencies):
                            self.issue(source, "infrastructure-reference-shape-invalid")
                        else:
                            for index, target in enumerate(dependencies):
                                self.reference(source, oid, ["Resources", name, "DependsOn", index], target, {"resource"}, "depends-on")
            if kind == "output" and isinstance(value, dict) and "Condition" in value:
                self.reference(source, oid, ["Outputs", name, "Condition"], value["Condition"], {"condition"}, "condition")
            self.walk(source, oid, [next(s for s, k in SECTIONS.items() if k == kind), name], value)
        self.check_cycles()

    def reference(self, source, owner, locator, name, kinds, relation):
        if not isinstance(name, str):
            self.issue(source, "infrastructure-reference-shape-invalid")
            return
        if name in PSEUDO and "parameter" in kinds:
            if name not in self.pseudos:
                self.pseudos[name] = self.c.observation(self.source, "infrastructure-symbol",
                    ["pseudo", name], {"kind": "pseudo-parameter", "name": name})
                self.c.observations[self.pseudos[name]]["symbol_kind"] = "pseudo-parameter"
            target = self.pseudos[name]
        else:
            candidates = [self.symbols[(kind, name)][0] for kind in kinds if (kind, name) in self.symbols]
            if len(candidates) != 1:
                self.issue(source, "infrastructure-reference-unknown")
                return
            target = candidates[0]
        if self.kinds.get(owner) == "condition" and self.kinds.get(target) == "resource":
            self.issue(source, "infrastructure-reference-context-invalid")
        if self.kinds.get(owner) in {"parameter", "mapping"}:
            self.issue(source, "infrastructure-reference-context-invalid")
        self.reference_count += 1
        if self.reference_count > MAX_REFERENCES:
            self.issue(source, "infrastructure-reference-limit-exceeded")
            return
        oid = self.c.observation(source, "infrastructure-reference", locator,
                                 {"relation": relation, "target": target}, owner)
        self.c.observations[oid]["target_id"] = target
        self.c.observations[oid]["reference_kind"] = relation
        self.edges.setdefault(owner, set()).add(target)

    def walk(self, source, owner, locator, value):
        if isinstance(value, list):
            for index, item in enumerate(value):
                self.walk(source, owner, locator + [index], item)
        elif isinstance(value, dict):
            if "$tag" in value:
                if set(value) != {"$tag", "value"}:
                    self.issue(source, "infrastructure-intrinsic-shape-invalid")
                    return
                self.intrinsic(source, owner, locator, value["$tag"], value["value"], value, "value")
            elif (any(key == "Ref" or key.startswith("Fn::") for key in value)
                  or set(value) == {"Condition"} and isinstance(value["Condition"], str)):
                if len(value) != 1:
                    self.issue(source, "infrastructure-intrinsic-shape-invalid")
                    return
                key, argument = next(iter(value.items()))
                self.intrinsic(source, owner, locator, key[4:] if key.startswith("Fn::") else key, argument, value, key)
            else:
                for key, item in value.items():
                    # Resource Condition and DependsOn are handled in their own contexts.
                    self.walk(source, owner, locator + [key], item)
        elif isinstance(value, str) and "{{resolve:" in value:
            # Resolution is a provider-side dependency, not a literal value proof.
            self.external(source, owner, locator, value)

    def external(self, source, owner, locator, value):
        issues = [] if self.kinds.get(owner) == "resource" else ["infrastructure-external-consumer-unresolved"]
        self.c.observation(source, "external-dependency", locator, value, owner, issues=issues)

    def intrinsic(self, source, owner, locator, name, argument, original, argument_key):
        argument_locator = locator + [argument_key]
        if name == "ImportValue":
            # Preserve the exact locator and original tagged/long-form subtree,
            # including invalid imports. Existing resource observations deduplicate.
            self.external(source, owner, locator, original)
        if name == "Ref":
            self.reference(source, owner, locator, argument, {"resource", "parameter"}, "ref")
            return
        if name == "GetAtt":
            parts = argument.split(".", 1) if isinstance(argument, str) else argument
            if (not isinstance(parts, list) or len(parts) != 2 or any(not isinstance(item, str) or not item for item in parts)):
                self.issue(source, "infrastructure-intrinsic-shape-invalid")
            else:
                self.reference(source, owner, locator, parts[0], {"resource"}, "get-att")
            return
        if name == "Condition":
            self.reference(source, owner, locator, argument, {"condition"}, "condition")
            return
        if name == "Sub":
            self.substitution(source, owner, locator, argument, argument_locator)
            return
        if name == "If":
            if not isinstance(argument, list) or len(argument) != 3 or not isinstance(argument[0], str):
                self.issue(source, "infrastructure-intrinsic-shape-invalid")
                return
            self.reference(source, owner, argument_locator + [0], argument[0], {"condition"}, "condition")
        elif name == "FindInMap":
            if not isinstance(argument, list) or len(argument) != 3 or not isinstance(argument[0], str):
                self.issue(source, "infrastructure-intrinsic-shape-invalid")
                return
            self.reference(source, owner, argument_locator + [0], argument[0], {"mapping"}, "mapping")
        elif name in {"Join", "Split", "Select", "Equals", "Not", "And", "Or", "Cidr"}:
            lengths = {"Join": (2, 2), "Split": (2, 2), "Select": (2, 2), "Equals": (2, 2),
                       "Not": (1, 1), "And": (2, 10), "Or": (2, 10), "Cidr": (3, 3)}
            minimum, maximum = lengths[name]
            valid = isinstance(argument, list) and minimum <= len(argument) <= maximum
            if valid and name in {"Join", "Split"}:
                valid = isinstance(argument[0], str)
            if valid and name == "Join":
                valid = isinstance(argument[1], (list, dict))
            if not valid:
                self.issue(source, "infrastructure-intrinsic-shape-invalid")
                return
        elif name in {"ImportValue", "Base64", "GetAZs"}:
            if not isinstance(argument, (str, dict)):
                self.issue(source, "infrastructure-intrinsic-shape-invalid")
                return
        else:
            self.issue(source, "infrastructure-intrinsic-unsupported")
            return
        self.walk(source, owner, argument_locator, argument)

    def substitution(self, source, owner, locator, value, argument_locator):
        variables = {}
        if isinstance(value, list) and len(value) == 2:
            text, variables = value
        else:
            text = value
        if (not isinstance(text, str) or not isinstance(variables, dict)
                or any(not SUB_NAME.fullmatch(key) for key in variables)):
            self.issue(source, "infrastructure-intrinsic-shape-invalid")
            return
        matches = list(re.finditer(r"\$\{([^}]+)\}", text))
        if "${" in re.sub(r"\$\{[^}]+\}", "", text):
            self.issue(source, "infrastructure-intrinsic-shape-invalid")
        for index, match in enumerate(matches):
            name = match.group(1)
            if name.startswith("!"):
                continue
            if not SUB_NAME.fullmatch(name):
                self.issue(source, "infrastructure-intrinsic-shape-invalid")
            elif name in variables:
                continue
            elif "." in name:
                self.reference(source, owner, locator + ["sub", index], name.split(".", 1)[0], {"resource"}, "sub")
            else:
                self.reference(source, owner, locator + ["sub", index], name, {"resource", "parameter"}, "sub")
        if "{{resolve:" in text:
            self.external(source, owner, argument_locator + ([0] if isinstance(value, list) else []), text)
        for name, value in variables.items():
            self.walk(source, owner, argument_locator + [1, name], value)

    def check_cycles(self):
        visiting, done = set(), set()
        def visit(node):
            if node in visiting:
                self.issue(self.owners.get(node, self.source), "infrastructure-reference-cycle")
                return
            if node in done:
                return
            visiting.add(node)
            for target in sorted(self.edges.get(node, ())):
                visit(target)
            visiting.remove(node)
            done.add(node)
        try:
            for node in sorted(self.edges):
                visit(node)
        except RecursionError:
            self.issue(self.source, "infrastructure-reference-limit-exceeded")
