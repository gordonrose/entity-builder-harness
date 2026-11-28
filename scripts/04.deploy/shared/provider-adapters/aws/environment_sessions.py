#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.aws.environment-sessions
#   version: 6
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.environment-lifecycle
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind checked temporary instance operations to durable admission and the existing single-submission change-set engine.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.test.aws.environment-sessions
#     path: scripts/04.deploy/shared/provider-adapters/aws/environment-sessions-test.py
"""Connected source/API boundary, not a live provider factory or cleanup claim.

The caller must qualify the supplied provider, remote-store guard and preflight
through the normal custody/realization/approval workflow.
Preflight receives the exact captured source plan, operation and reservation;
it must verify fresh source, effective permissions, armed independent expiry,
ownership, protected exclusions and exact approved changes, raising to deny.
Returning None is the validator protocol, not evidence manufactured here.
Activation additionally requires observed completion of original creation and
database preparation, readiness of captured dependencies, preservation of all
unowned deployed parameters, and exact declared count-only changes. A source
plan or successful reservation proves none of those live prerequisites.
Discard preparation likewise uses the captured source projection; its tuple
closure checks do not authenticate template contents or prove live ownership.
Fresh discard and deletion submissions observe the sealed record and recapture
the complete source plan at the observed clock, including after expiry. That
comparison does not qualify this controller or establish provider ownership.
Initialization acquires authenticated packages and validates grouped network
choices. Creation resolves declared outputs only through original CREATE intent
and observed provider lineage. Immutable base and per-operation inputs share the
versioned session record; recovery never repeats acquisition or resolution.

This increment supports CREATE, captured activation UPDATE, sealed captured
prepare-discard UPDATE change sets and reserved exact-stack deletion. Original
custody and prior operations are concretely checked before fresh deletion;
qualified preflight still owns protected exclusions and exact approved removals.
Final physical absence, successor sessions and workload command integration are
deliberately absent. Retained operations only observe.
The plan's explicit stack/template rows bind dependency instances too;
membership in independent template and stack sets cannot establish a pairing.
"""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re


def _module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


RECORDS = _module("environment_session_records", "session_records.py")
SESSION_CLI = _module("environment_session_cli", "session_cli.py")
RESERVATIONS = RECORDS.RESERVATIONS
CHANGE_SETS = _module("environment_session_change_sets", "change_sets.py")
CF = _module("environment_session_template", "cloudformation-template.py")
FOUNDATION = _module("environment_session_foundation", "foundation-checks.py")
ACQUISITION_PATH = Path(__file__).parent / "../../../lifecycle/40-package/package-custody-receipt/acquire.py"
PARAMETER_CODES = frozenset({"cloudformation-parameter-values-invalid", "cloudformation-parameter-declaration-invalid",
    "cloudformation-number-parameter-invalid", "cloudformation-string-parameter-invalid",
    "cloudformation-parameter-type-unsupported", "cloudformation-aws-parameter-invalid",
    "cloudformation-template-body-invalid", "cloudformation-template-mapping-invalid"})
FOUNDATION_CODES = frozenset("foundation-" + reason for reason in (
    "network-choice-context-invalid", "network-choices-invalid", "network-cidr-invalid", "network-cidr-not-private",
    "network-cidr-size-invalid", "network-subnet-containment-invalid", "network-subnet-overlap", "network-zone-selection-invalid", "network-zone-observation-invalid",
    "network-zone-selection-mismatch", "network-zone-region-mismatch", "network-zone-not-available",
    "network-zone-type-unsupported", "network-zone-ambiguous", "s3-prefix-observation-invalid", "s3-prefix-missing",
    "s3-prefix-ambiguous", "stack-observation-invalid", "stack-not-ready", "outputs-invalid", "outputs-ambiguous", "outputs-missing"))


class SessionOperationFailure(Exception):
    def __init__(self, condition):
        self.code = "environment-session-operation-" + condition
        super().__init__(self.code)


def _require(condition, reason):
    if not condition:
        raise SessionOperationFailure(reason)


def _digest(value):
    return hashlib.sha256(RESERVATIONS.canonical(value)).hexdigest()


def _template_matches(observed, expected):
    try:
        return CF.templates_equal(observed, expected)
    except ValueError:
        return False


class _Reservations(RESERVATIONS.ImmutableReservationStore):
    schema = "deploy/environment-session-operation/v1"
    operation_prefix = "es-"
    failure = SessionOperationFailure

    def __init__(self, storage, request):
        self.expected = deepcopy(request)
        super().__init__(None, storage=storage)

    def path_for(self, phase, request):
        kind = request.get("kind") if isinstance(request, dict) else None
        _require(request == self.expected and (kind == "delete" and phase == "delete"
                 or kind in ("creation", "activation", "prepare-discard") and phase in ("prepare", "execute")), "request-mismatch")
        return request["stack"] + ":" + phase

    def validate_time(self, value):
        try:
            RECORDS.checked_time(value)
        except RECORDS.SessionRecordFailure:
            raise SessionOperationFailure("reservation-time-invalid") from None


def publication_bindings(plan):
    try:
        result = {}
        for _, rows in plan["publication_selections"]:
            facts = dict(rows)
            pipeline = facts["pipeline"]
            _require(pipeline not in result or result[pipeline] == facts, "publication-bindings-invalid")
            result[pipeline] = facts
        return result
    except (KeyError, TypeError, ValueError):
        raise SessionOperationFailure("publication-bindings-invalid") from None

def checked_session_inputs(plan, **inputs):
    _require(set(inputs) == {"choices", "publications"}, "initialization-inputs-invalid")
    choices, selections = deepcopy(inputs["choices"]), deepcopy(inputs["publications"])
    try:
        contracts = {dict(row)["contract"] for _, _, row in plan["execution_parameters"] if dict(row)["kind"] == "choice"}
    except (KeyError, TypeError, ValueError):
        raise SessionOperationFailure("execution-bindings-invalid") from None
    _require(isinstance(choices, dict) and set(choices) == contracts == {"private-network/v1"}
             and isinstance(choices["private-network/v1"], dict)
             and set(choices["private-network/v1"]) == {"vpc_cidr", "subnet_one_cidr", "subnet_two_cidr", "availability_zone_one", "availability_zone_two"}
             and all(isinstance(value, str) for value in choices["private-network/v1"].values()), "choices-invalid")
    publications = publication_bindings(plan)
    _require(isinstance(selections, dict) and set(selections) == set(publications)
             and all(isinstance(row, dict) and set(row) == {"run_id", "source_revision"}
                     and type(row["run_id"]) is int and 0 < row["run_id"] < 10 ** 20
                     and isinstance(row["source_revision"], str) and re.fullmatch(r"[a-f0-9]{40}", row["source_revision"])
                     for row in selections.values()), "publications-invalid")
    return choices, selections, publications


class SessionOperations:
    """Use a captured source plan; its not-admitted status never becomes approval."""

    def __init__(self, plan, records, *, provider, preflight, source_root=None, approved_max_duration_seconds=None, qualified_facts=None):
        try:
            _require(isinstance(plan, dict) and plan.get("schema") == "deploy/aws-session-source-plan/v1"
                     and plan.get("execution_status") == "not-admitted", "source-plan-invalid")
            binding = asdict(plan["binding"])
            intent, policy = binding["intent"], binding["intent"]["lifecycle"]
            _require(policy["mode"] == "temporary" and policy["data_retention"] == "discard"
                     and policy["explicit"] is True, "temporary-discard-required")
            _require(type(intent["starts_at"]) is int and type(intent["expires_at"]) is int
                     and 0 <= intent["starts_at"] < intent["expires_at"], "lifetime-invalid")
            _require(isinstance(source_root, (str, Path)) and bool(str(source_root))
                     and type(approved_max_duration_seconds) is int
                     and approved_max_duration_seconds >= intent["expires_at"] - intent["starts_at"], "source-context-invalid")
            try:
                self._source_root = Path(source_root)
                _require(self._source_root.is_absolute(), "source-context-invalid")
            except (OSError, ValueError):
                raise SessionOperationFailure("source-context-invalid") from None
            self._approved_duration = approved_max_duration_seconds
            _require(isinstance(intent["session_id"], str) and re.fullmatch(r"[a-f0-9]{32}", intent["session_id"]) is not None,
                     "identity-invalid")
            # Upstream binds sorted captured source rows using this serialization.
            source_digest = hashlib.sha256(json.dumps(binding["source_inputs"], separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
            _require(source_digest == binding["source_inputs_sha256"], "source-binding-mismatch")
            source = plan["source_configuration"]
            _require(source["target"] == intent["target"] and source["scope"] == intent["scope"], "source-target-mismatch")
            prefix = "s-" + intent["session_id"][:19]
            _require(plan["resource_name_prefix"] == prefix and prefix != source["target"], "instance-prefix-invalid")
            try:
                self._roles = RECORDS.checked_execution_roles(plan.get("execution_roles"),
                    account=source["account"], session_id=intent["session_id"])
            except RECORDS.SessionRecordFailure:
                raise SessionOperationFailure("execution-roles-invalid") from None
            prerequisites = plan["prerequisite_components"]
            _require(isinstance(prerequisites, tuple) and all(isinstance(name, str) and bool(name) for name in prerequisites)
                     and len(set(prerequisites)) == len(prerequisites)
                     and not set(prerequisites).intersection({"foundation", *binding["scopes"]}), "prerequisite-bindings-invalid")
            stacks = dict(plan["stack_names"])
            _require(len(stacks) == len(plan["stack_names"]) and set(stacks) == {"foundation", *binding["scopes"], *prerequisites}
                     and len(set(stacks.values())) == len(stacks), "instance-stacks-invalid")
            _require(all(isinstance(name, str) and name.startswith(prefix + "-")
                         and re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{0,127}", name) is not None
                         and name not in {source["stack"], source["foundation_stack"]} for name in stacks.values()),
                     "production-identity-prohibited")
            self._plan = deepcopy({**plan, "binding": binding})
            self._plan_sha256 = _digest(self._plan)
            self._binding = {key: intent[key] for key in ("target", "scope", "session_id", "starts_at", "expires_at")}
            self._binding["source_inputs_sha256"] = source_digest
            _require(records.binding == self._binding and records.account == source["account"]
                     and records.region == source["region"], "remote-binding-mismatch")
            _require(callable(provider) and callable(preflight), "qualified-callbacks-required")
            self._templates = deepcopy(dict(plan["projected_templates"]))
            self._controls = deepcopy(dict(plan["creation_parameters"]))
            _require(len(self._templates) == len(plan["projected_templates"])
                     and len(self._controls) == len(plan["creation_parameters"])
                     and set(self._templates) == set(self._controls) and bool(self._templates), "template-bindings-invalid")
            self._stacks = frozenset(stacks.values())
            pairs = plan["stack_templates"]
            _require(isinstance(pairs, tuple) and all(isinstance(row, tuple) and len(row) == 2
                     and all(isinstance(value, str) for value in row) for row in pairs), "template-bindings-invalid")
            self._pairs = frozenset(pairs)
            _require(len(self._pairs) == len(pairs) == len(self._stacks) == len(self._templates)
                     and {stack for stack, _ in pairs} == self._stacks
                     and {reference for _, reference in pairs} == set(self._templates)
                     and (stacks["foundation"], source["foundation_template"]) in self._pairs
                     and (stacks[intent["scope"]], source["template"]) in self._pairs, "template-bindings-invalid")
            for field, width in (("execution_parameters", 3), ("execution_output_sources", 4),
                                 ("execution_source_values", 3), ("publication_selections", 2)):
                rows = plan[field]
                _require(isinstance(rows, tuple) and all(isinstance(row, tuple) and len(row) == width
                         and isinstance(row[0], str) and row[0] in self._stacks for row in rows), "execution-bindings-invalid")
                keys = [row[:1] if field == "publication_selections" else row[:2] for row in rows]
                _require(all(all(isinstance(value, str) for value in key) for key in keys)
                         and len(set(keys)) == len(keys), "execution-bindings-invalid")
                if field in {"execution_parameters", "publication_selections"}:
                    _require(all(isinstance(row[-1], tuple) and all(isinstance(item, tuple) and len(item) == 2
                                 and all(isinstance(value, str) for value in item) for item in row[-1])
                                 and len(dict(row[-1])) == len(row[-1]) for row in rows), "execution-bindings-invalid")
                    if field == "execution_parameters":
                        _require(all(dict(row[-1]).get("kind") in {"choice", "package", "source", "output", "provider", "omit-if-unused"}
                                     for row in rows), "execution-bindings-invalid")
                else:
                    _require(all(all(isinstance(value, str) for value in row) for row in rows), "execution-bindings-invalid")
            output_rows = plan["stack_parameter_sources"]
            _require(isinstance(output_rows, tuple) and all(isinstance(row, tuple) and len(row) == 4
                     and all(isinstance(value, str) and bool(value) for value in row) for row in output_rows),
                     "prerequisite-bindings-invalid")
            prerequisite_stacks = {stacks[name] for name in prerequisites}
            _require(len(set(output_rows)) == len(output_rows)
                     and len({(consumer, parameter) for consumer, parameter, _, _ in output_rows}) == len(output_rows)
                     and {producer for _, _, producer, _ in output_rows} == prerequisite_stacks,
                     "prerequisite-bindings-invalid")
            templates_by_stack = dict(pairs)
            foundation = json.loads(self._templates[source["foundation_template"]])
            for consumer, parameter, producer, output in output_rows:
                _require(consumer == stacks["foundation"] and isinstance(foundation["Parameters"].get(parameter), dict)
                         and parameter not in dict(self._controls[source["foundation_template"]]), "prerequisite-bindings-invalid")
                output_value = json.loads(self._templates[templates_by_stack[producer]]).get("Outputs", {}).get(output)
                _require(isinstance(output_value, dict) and output_value.get("Value") is not None, "prerequisite-bindings-invalid")
            self._activation_templates = deepcopy(dict(plan["activation_templates"]))
            self._activation_controls = deepcopy(dict(plan["activation_parameters"]))
            declared = {}
            for reference, template in self._templates.items():
                rows = json.loads(template)["Metadata"]["CreationControls"]
                counts = {key: str(row["active"]) for key, row in rows.items() if row["kind"] == "desired-count"}
                if counts:
                    declared[reference] = {**dict(self._controls[reference]), **counts}
            _require(len(self._activation_templates) == len(plan["activation_templates"])
                     and len(self._activation_controls) == len(plan["activation_parameters"])
                     and set(self._activation_templates) == set(self._activation_controls) == set(declared)
                     and source["foundation_template"] not in declared
                     and all(dict(self._activation_controls[key]) == values for key, values in declared.items()),
                     "activation-bindings-invalid")
            discard_templates, discard_parameters = plan["discard_templates"], plan["discard_parameters"]
            _require(all(isinstance(rows, tuple) and all(isinstance(row, tuple) and len(row) == 2
                         and isinstance(row[0], str) for row in rows)
                         for rows in (discard_templates, discard_parameters)), "discard-bindings-invalid")
            self._discard_templates = deepcopy(dict(discard_templates))
            self._discard_controls = deepcopy(dict(discard_parameters))
            _require(len(self._discard_templates) == len(discard_templates)
                     and len(self._discard_controls) == len(discard_parameters)
                     and set(self._discard_templates) == set(self._discard_controls) == set(self._templates)
                     and all(isinstance(template, str) for template in self._discard_templates.values())
                     and all(isinstance(rows, tuple) and rows == self._controls[reference]
                             and all(isinstance(row, tuple) and len(row) == 2
                                     and all(isinstance(value, str) for value in row) for row in rows)
                             and len(dict(rows)) == len(rows)
                             for reference, rows in self._discard_controls.items()), "discard-bindings-invalid")
            qualified_facts = {} if qualified_facts is None else qualified_facts
            _require(isinstance(qualified_facts, dict) and (not qualified_facts
                or set(qualified_facts) == {"qualified-session-control/v1"}
                and isinstance(qualified_facts["qualified-session-control/v1"], str)
                and RECORDS.SHA.fullmatch(qualified_facts["qualified-session-control/v1"])), "control-facts-invalid")
            self._qualified_facts = deepcopy(qualified_facts)
            self.records, self._provider, self._preflight = records, provider, preflight
            self._task_selections = self._task_rows()
            self.records.check_task_capacity(self._task_selections)
        except SessionOperationFailure:
            raise
        except (KeyError, TypeError, ValueError, AttributeError):
            raise SessionOperationFailure("source-plan-invalid") from None

    def _context(self, action, request=None, reservation=None, preparation=None, arguments=None):
        return deepcopy({"action": action, "source_plan": self._plan,
                         "source_plan_sha256": self._plan_sha256, "binding": self._binding,
                         "request": request, "reservation": reservation, "preparation": preparation,
                         "operation_arguments": arguments})

    def _admit(self, action, request=None, reservation=None, preparation=None, arguments=None):
        if action in {"prepare-discard-prepare", "prepare-discard-execute", "delete"}:
            self._revalidate_existing_source()
        try:
            result = self._preflight(self._context(action, request, reservation, preparation, arguments))
        except Exception:
            raise SessionOperationFailure("preflight-unconfirmed") from None
        _require(result is None, "preflight-unconfirmed")
        if action.startswith(("creation-", "activation-", "prepare-discard-")):
            self.records.check_input_admission(request["kind"])

    def _revalidate_existing_source(self):
        observed = self.records.observe_existing()
        document = observed["document"]
        _require(document["state"] in ("sealed", "deleting"), "admission-open")
        _require(document["binding"] == self._binding, "remote-binding-mismatch")
        try:
            preparation = _module("environment_session_preparation",
                                  "../../../lifecycle/00-target-alignment/provider-adapters/aws/preparation-inputs.py")
            _require(callable(preparation.revalidate_session_plan) and isinstance(preparation.InputFailure, type)
                     and issubclass(preparation.InputFailure, ValueError), "source-revalidator-unavailable")
        except SessionOperationFailure:
            raise
        except Exception:
            raise SessionOperationFailure("source-revalidator-unavailable") from None
        try:
            fresh = preparation.revalidate_session_plan(self._source_root, deepcopy(self._plan),
                                                       observed["observed_at"], self._approved_duration)
            fresh = {**fresh, "binding": asdict(fresh["binding"])}
            _require(fresh["binding"]["source_inputs_sha256"] == document["binding"]["source_inputs_sha256"]
                     and _digest(fresh) == self._plan_sha256, "source-plan-mismatch")
        except SessionOperationFailure:
            raise
        except preparation.InputFailure as failure:
            raise SessionOperationFailure("source-revalidation:" + failure.code) from None
        except Exception:
            raise SessionOperationFailure("source-revalidation-unconfirmed") from None

    def _checked_values(self, template, values):
        try:
            return CF.validate_parameter_values(template, values)
        except ValueError as failure:
            raise SessionOperationFailure(str(failure) if str(failure) in PARAMETER_CODES else "parameters-unconfirmed") from None
        except Exception:
            raise SessionOperationFailure("parameters-unconfirmed") from None

    def _foundation(self, method, *arguments):
        try:
            return method(*arguments)
        except FOUNDATION.FoundationFailure as failure:
            raise SessionOperationFailure(failure.code if failure.code in FOUNDATION_CODES else "foundation-unconfirmed") from None
        except (RECORDS.CLI.CliFailure, SESSION_CLI.SessionProviderFailure) as failure:
            codes = SESSION_CLI.FAILURE_CODES if isinstance(failure, SESSION_CLI.SessionProviderFailure) else RECORDS.CLI_FAILURE_CODES
            code = failure.code if failure.code in codes else "aws-command-failed"
            raise SessionOperationFailure("foundation-unconfirmed:" + code) from None
        except Exception:
            raise SessionOperationFailure("foundation-unconfirmed") from None

    def _publications(self):
        return publication_bindings(self._plan)

    def _base(self, document):
        base = document["base"]
        _require(isinstance(base.get("provider_facts"), dict)
            and all(base["provider_facts"].get(key) == value for key, value in self._qualified_facts.items()), "control-facts-mismatch")
        _require(base.get("execution_roles") == self._roles, "execution-roles-mismatch")
        _require(set(base) == {"source_plan_sha256", "choices", "publications", "packages", "provider_facts", "cleanup_shapes", "lifecycle_max_duration_seconds", "task_selections_sha256", "task_selection_count", "execution_roles"}
                 and base["source_plan_sha256"] == self._plan_sha256, "inputs-source-mismatch")
        _require(base["task_selections_sha256"] == _digest(self._task_selections)
                 and base["task_selection_count"] == len(self._task_selections), "task-selection-mismatch")
        _require(base["lifecycle_max_duration_seconds"] == self._plan["binding"]["intent"]["lifecycle"]["max_duration_seconds"], "inputs-source-mismatch")
        _require(base["cleanup_shapes"] == self._cleanup_shapes(), "inputs-cleanup-shape-mismatch")
        for stack, physical in document["physical_resources"].items():
            positions = {logical: position for position, (logical, _) in enumerate(self._resource_index(stack))}
            for key, rows in self._cleanup_bindings(stack).items():
                _require(all(physical[key][position] == "unknown" or RECORDS.SHA.fullmatch(physical["slots"][positions[logical]])
                             for position, (logical, _) in enumerate(rows)), "cleanup-binding-allocation-mismatch")
        _require(all(isinstance(base[key], dict) for key in ("choices", "publications", "packages", "provider_facts"))
                 and set(base["publications"]) == set(base["packages"]) == set(self._publications()), "inputs-publications-mismatch")
        return base

    def _task_rows(self):
        result = []
        stacks, references = dict(self._plan["stack_names"]), dict(self._plan["stack_templates"])
        components = self._plan["task_selections"]
        _require(isinstance(components, tuple) and len(dict(components)) == len(components)
                 and set(dict(components)) == set(self._plan["binding"]["scopes"]), "task-selection-invalid")
        for component, selected in components:
            _require(isinstance(selected, dict) and set(selected) == {"kind", "route", "proof_label", "steps", "sources"}
                     and selected["kind"] in {"ordered-commands/v1", "entity-smoke-baseline/v1"}
                     and isinstance(selected["steps"], (list, tuple)) and bool(selected["steps"]), "task-selection-invalid")
            stack = stacks[component]
            index = dict((name, position) for position, (name, _) in enumerate(self._resource_index(stack)))
            template = json.loads(self._templates[references[stack]])
            for row in selected["steps"]:
                ordered = selected["kind"] == "ordered-commands/v1"
                fields = {"id", "command", "phase", "workload", "proof", "task_definition"} if ordered else {
                    "proof", "workload", "workload_id", "task_definition_ref", "operation", "stage", "phase", "activation", "key", "label", "condition"}
                _require(isinstance(row, dict) and set(row) == fields, "task-selection-invalid")
                step, logical = row["id" if ordered else "key"], row["task_definition" if ordered else "task_definition_ref"]
                _require(isinstance(step, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", step)
                         and isinstance(logical, str) and template["Resources"].get(logical, {}).get("Type") == "AWS::ECS::TaskDefinition", "task-selection-invalid")
                result.append({"component": component, "step": step, "kind": selected["kind"], "stack": stack,
                               "definition_position": index[logical], "selection": deepcopy(row)})
        _require(len({(row["component"], row["step"]) for row in result}) == len(result), "task-selection-invalid")
        return result

    def task_storage(self, component, step, *, validate_record, validate_receipt, record_selection, key_for_record=None, before_submit=None):
        """Select storage only; native validators and qualified authority remain explicit."""
        _require(isinstance(component, str) and isinstance(step, str), "task-selection-invalid")
        matches = [index for index, row in enumerate(self._task_selections) if (row["component"], row["step"]) == (component, step)]
        _require(len(matches) == 1, "task-selection-invalid")
        self._base(self.records.observe_existing()["document"])
        _require(callable(validate_record) and callable(validate_receipt) and callable(record_selection)
                 and (before_submit is None or callable(before_submit)), "task-callbacks-invalid")
        return self.records.task_storage(self._task_selections, matches[0], validate_record=validate_record,
            validate_receipt=validate_receipt, record_selection=record_selection, key_for_record=key_for_record, before_submit=before_submit)

    def _cleanup_shapes(self):
        return {stack: {"template_reference": reference, "discard": reference in self._discard_templates,
                        "resource_count": len(self._resource_index(stack)),
                        "resources_sha256": _digest(dict(self._resource_index(stack))),
                        "bindings_sha256": _digest(self._cleanup_bindings(stack)),
                        **{key + "_count": len(rows) for key, rows in self._cleanup_bindings(stack).items()}}
                for stack, reference in self._pairs}

    def _cleanup_bindings(self, stack):
        resources = json.loads(self._templates[dict(self._pairs)[stack]])["Resources"]
        groups = {"relationships": ("AWS::EC2::SecurityGroupIngress", "AWS::EC2::SecurityGroupEgress", "AWS::ECS::Service"),
                  "databases": ("AWS::RDS::DBInstance",), "namespaces": ("AWS::ServiceDiscovery::PrivateDnsNamespace",)}
        return {key: tuple((logical, resources[logical]) for logical, kind in self._resource_index(stack) if kind in kinds)
                for key, kinds in groups.items()}

    def _resource_index(self, stack):
        reference = dict(self._pairs)[stack]
        return tuple(sorted((logical, resource["Type"]) for logical, resource in json.loads(self._templates[reference])["Resources"].items()))

    def _physical_projection(self, stack, stack_id, response, *, never_allocated=False):
        index = self._resource_index(stack)
        positions = {logical: (position, kind) for position, (logical, kind) in enumerate(index)}
        _require(isinstance(response, dict) and not response.get("NextToken")
                 and isinstance(response.get("StackResourceSummaries"), list), "custody-resources-incomplete")
        slots, raw, seen = ["unknown"] * len(index), {}, set()
        for row in response["StackResourceSummaries"]:
            logical = row.get("LogicalResourceId") if isinstance(row, dict) else None
            _require(isinstance(logical, str) and logical in positions and logical not in seen
                     and row.get("ResourceType") == positions[logical][1], "custody-resource-mismatch")
            seen.add(logical)
            physical_id = row.get("PhysicalResourceId")
            _require(physical_id is None or isinstance(physical_id, str), "physical-identity-invalid")
            if physical_id:
                _require(bool(physical_id.strip()), "physical-identity-invalid")
                position = positions[logical][0]
                slots[position], raw[position] = _digest(physical_id), physical_id
        if never_allocated:
            _require(not raw, "physical-allocation-contradiction")
            slots = ["never-allocated"] * len(index)
        return {"stack_id_sha256": _digest(stack_id), "slots": slots,
                **{key: ["unknown"] * len(rows) for key, rows in self._cleanup_bindings(stack).items()},
                "observation_sha256": _digest({"stack_id": stack_id, "resources": response}),
                "observed_at": datetime.now(timezone.utc).isoformat(timespec="microseconds")}, raw

    def initialize(self, **inputs):
        choices, selections, publications = checked_session_inputs(self._plan, **inputs)
        prior = self.records.observe_initialization()
        if prior is not None:
            base = self._base(prior)
            _require(base["choices"] == choices and base["publications"] == selections, "inputs-selection-mismatch")
            return deepcopy(prior)
        self._admit("initialize")
        region = self._plan["source_configuration"]["region"]
        checked = self._foundation(FOUNDATION.private_network_choices, self._provider, choices["private-network/v1"], region)
        facts = deepcopy(self._qualified_facts)
        if any(dict(row).get("contract") == "aws-regional-s3-prefix-list/v1" for _, _, row in self._plan["execution_parameters"]):
            facts["aws-regional-s3-prefix-list/v1"] = self._foundation(FOUNDATION.s3_prefix_list, self._provider, region)
        try:
            acquisition = _module("environment_session_acquisition", ACQUISITION_PATH)
            _require(callable(acquisition.acquire_custody) and isinstance(acquisition.AcquisitionFailure, type)
                     and issubclass(acquisition.AcquisitionFailure, Exception) and isinstance(acquisition.FAILURE_CODES, frozenset),
                     "acquisition-unavailable")
        except Exception:
            raise SessionOperationFailure("acquisition-unavailable") from None
        packages = {}
        for pipeline, publication in sorted(publications.items()):
            selection = selections[pipeline]
            try:
                acquired = acquisition.acquire_custody(publication=deepcopy(publication), run_id=selection["run_id"],
                    expected_source_revision=selection["source_revision"], aws_provider=self._provider)
                packages[pipeline] = {"receipt": acquired["receipt"], "evidence": dict(acquired["evidence"])}
            except acquisition.AcquisitionFailure as failure:
                code = failure.code if failure.code in getattr(acquisition, "FAILURE_CODES", ()) else "acquisition-unconfirmed"
                raise SessionOperationFailure(code) from None
            except Exception:
                raise SessionOperationFailure("acquisition-unconfirmed") from None
        base = {"source_plan_sha256": self._plan_sha256, "choices": {"private-network/v1": checked},
                "publications": selections, "packages": packages, "provider_facts": facts,
                "execution_roles": deepcopy(self._roles),
                "lifecycle_max_duration_seconds": self._plan["binding"]["intent"]["lifecycle"]["max_duration_seconds"],
                "cleanup_shapes": self._cleanup_shapes(), "task_selections_sha256": _digest(self._task_selections),
                "task_selection_count": len(self._task_selections)}
        return self.records.initialize(base)

    def seal(self):
        self._admit("seal")
        return self.records.seal()

    def _selection(self, kind, stack, template_reference):
        _require(isinstance(kind, str) and kind in {"creation", "activation", "prepare-discard"}, "kind-unsupported")
        _require(isinstance(stack, str) and stack in self._stacks and isinstance(template_reference, str)
                 and template_reference in self._templates, "instance-selection-invalid")
        _require((stack, template_reference) in self._pairs, "template-stack-mismatch")
        _require(kind != "activation" or template_reference in self._activation_templates, "activation-selection-invalid")

    def _phase_sources(self, kind):
        return ((self._activation_templates, self._activation_controls) if kind == "activation"
                else (self._discard_templates, self._discard_controls) if kind == "prepare-discard"
                else (self._templates, self._controls))

    def _delete_arguments(self, document, stack_id):
        return {"StackName": stack_id, "RoleARN": document["base"]["execution_roles"]["cleanup"]}

    def _operation(self, kind, stack, template_reference, document, resolved):
        self._selection(kind, stack, template_reference)
        templates, selections = self._phase_sources(kind)
        template = templates[template_reference]
        try:
            _require(isinstance(template, str) and len(template.encode()) <= 51200, "template-invalid")
            parsed = json.loads(template)
            _require(isinstance(parsed, dict) and RESERVATIONS.canonical(parsed).decode() == template, "template-invalid")
            entry = resolved["inputs"]
            _require(resolved["sha256"] == _digest(entry), "resolved-inputs-invalid")
            controls = dict(selections[template_reference])
            if kind == "creation":
                producers = sorted({row[2] for row in (*self._plan["stack_parameter_sources"], *self._plan["execution_output_sources"]) if row[0] == stack})
                _require(set(entry) == {"values", "producer_stacks"} and entry["producer_stacks"] == producers
                         and all(producer in document["creation_evidence"] for producer in producers), "resolved-inputs-invalid")
                values = self._checked_values(template, entry["values"])
                _require(values == entry["values"] and all(values.get(key) == value for key, value in controls.items()), "instance-controls-mismatch")
                parameters = [{"ParameterKey": key, "ParameterValue": value} for key, value in sorted(values.items())]
                stack_id = stack
            else:
                _require(set(entry) == {"observed_values_sha256"} and isinstance(entry["observed_values_sha256"], str)
                         and RECORDS.SHA.fullmatch(entry["observed_values_sha256"]) and stack in document["creation_evidence"], "resolved-inputs-invalid")
                original = document["resolved"]["creation:" + stack]["inputs"]["values"]
                self._checked_values(template, {**original, **controls})
                parameters = CHANGE_SETS.update_parameter_inputs(original, controls)
                stack_id = document["incarnations"][stack]
                _require(self._stack_id(stack, stack_id), "resolved-inputs-invalid")
            request = RECORDS.operation_request(document, kind, stack, "f" * 64, resolved_sha256=resolved["sha256"])
            _require(len(request["change_set"]) <= 128, "change-set-name-invalid")
            arguments = {"StackName": stack_id, "ChangeSetName": request["change_set"],
                         "ChangeSetType": "CREATE" if kind == "creation" else "UPDATE",
                         "RoleARN": document["base"]["execution_roles"]["cleanup" if kind == "prepare-discard" else "creation"],
                         "TemplateBody": template, "Parameters": deepcopy(parameters), "Capabilities": ["CAPABILITY_NAMED_IAM"]}
            request["arguments_sha256"] = _digest(arguments)
            return request, arguments
        except SessionOperationFailure:
            raise
        except (TypeError, ValueError, KeyError):
            raise SessionOperationFailure("operation-inputs-invalid") from None

    def _stack_id(self, stack, value):
        source = self._plan["source_configuration"]
        pattern = (r"arn:aws:cloudformation:" + re.escape(source["region"]) + ":" + re.escape(source["account"])
                   + ":stack/" + re.escape(stack) + r"/[A-Za-z0-9][A-Za-z0-9-]*")
        return isinstance(value, str) and len(value) <= 2048 and re.fullmatch(pattern, value) is not None

    def _owned_stack(self, stack, document, required):
        current, proof = self._successful_stack(stack, document)
        outputs = self._foundation(FOUNDATION.stack_outputs, {"Stacks": [current]}, required)
        return current, outputs, proof

    def runtime_view(self, **inputs):
        """Hand off checked current resources, never reusable mutation authority."""
        _require(set(inputs) == {"stack", "required_outputs"}, "operation-inputs-invalid")
        stack, required = inputs["stack"], inputs["required_outputs"]
        _require(isinstance(stack, str) and stack in self._stacks, "instance-selection-invalid")
        reference = dict(self._pairs)[stack]
        declared = json.loads(self._templates[reference]).get("Outputs", {})
        _require(isinstance(required, (list, tuple)) and all(isinstance(name, str) and name in declared for name in required)
                 and len(required) == len(set(required)), "runtime-output-selection-invalid")
        required = tuple(required)
        try:
            document = self.records.observe_existing()["document"]
            self._base(document)
            delete_key = "delete:" + stack + ":delete"
            _require(delete_key not in document["operations"]
                     or document["operation_outcomes"].get(delete_key, {}).get("status") == "not-submitted",
                     "runtime-phase-unready")
            current, outputs, proof = self._owned_stack(stack, document, required)
            _, stack_id, evidence, custody, outcomes, physical = proof
            executed = []
            for kind in ("creation", "activation", "prepare-discard"):
                preparation = outcomes.get(kind + ":" + stack + ":prepare")
                _require(preparation is None or preparation["status"] in ("CREATE_COMPLETE", "not-submitted"),
                         "runtime-phase-unready")
                execution = outcomes.get(kind + ":" + stack + ":execute")
                if execution is not None and execution["status"] != "not-submitted":
                    executed.append(kind)
            _require(bool(executed), "output-creation-required")
            phase = executed[-1]
            _require(outcomes[phase + ":" + stack + ":execute"]["status"] in ("CREATE_COMPLETE", "UPDATE_COMPLETE"),
                     "runtime-phase-unready")
            later = ("creation", "activation", "prepare-discard")[("creation", "activation", "prepare-discard").index(phase) + 1:]
            _require(not any(kind == "prepare-discard"
                             and outcomes.get(kind + ":" + stack + ":prepare", {}).get("status") in ("CREATE_COMPLETE", "FAILED")
                             for kind in later), "runtime-phase-unready")
            template = json.loads(self._phase_sources(phase)[0][reference])
            _require(set(required) <= template.get("Outputs", {}).keys(), "runtime-output-selection-invalid")
            parameters = self._checked_values(template, CHANGE_SETS.parameter_values(current.get("Parameters")))
            databases = self._cleanup_bindings(stack)["databases"]
            if databases:
                raw = self._cleanup_raw(stack, stack_id, physical)
                previous = document["physical_resources"].get(stack)
                for position, (logical, _) in enumerate(databases):
                    declared = template["Resources"][logical].get("Properties", {}).get("BackupRetentionPeriod")
                    _require(type(declared) is int and declared == 0, "runtime-database-retention-unconfirmed")
                    _require(logical in raw, "runtime-resources-unconfirmed")
                    known = previous["databases"][position] if previous else "unknown"
                    database = self._database_instance(raw[logical], known)
                    _require(database is not None, "cleanup-database-lineage-unconfirmed")
                    retention = database.get("BackupRetentionPeriod")
                    _require(type(retention) is int and retention == 0, "runtime-database-retention-unconfirmed")
                    pending = database.get("PendingModifiedValues", {})
                    _require(isinstance(pending, dict) and ("BackupRetentionPeriod" not in pending
                             or type(pending["BackupRetentionPeriod"]) is int and pending["BackupRetentionPeriod"] == 0),
                             "runtime-database-pending-retention-unconfirmed")
                    # Optional omission proves no replication absence. This
                    # current runtime gate never qualifies lifetime cleanup.
                    _require("DBInstanceAutomatedBackupsReplications" not in database
                             or isinstance(database["DBInstanceAutomatedBackupsReplications"], list)
                             and not database["DBInstanceAutomatedBackupsReplications"], "runtime-database-replication-unconfirmed")
                    physical["databases"][position] = _digest(database["DbiResourceId"])
                physical["observation_sha256"] = _digest({key: value for key, value in physical.items()
                                                          if key not in ("observation_sha256", "observed_at")})
            self._retain_inspection(stack, stack_id, custody, outcomes, evidence, physical)
            reconstructed = self.reconstruct_physical(stack=stack, stack_id=stack_id)
            resources = {}
            for row in reconstructed["resources"]:
                _require(row["allocation"] == "allocated" and isinstance(row["physical_id"], str)
                         and bool(row["physical_id"]), "runtime-resources-unconfirmed")
                resources[row["logical_id"]] = {"type": row["resource_type"], "physical_id": row["physical_id"]}
            _require({key: row["type"] for key, row in resources.items()}
                     == {key: row["Type"] for key, row in template["Resources"].items()}, "runtime-resources-unconfirmed")
            observed = self.records.observe_existing()
            latest = observed["document"]
            _require(latest["operations"] == document["operations"], "reconciliation-changed")
            _require(latest["incarnations"].get(stack) == stack_id and latest["creation_custody"].get(stack) == custody,
                     "custody-retained-mismatch")
            return deepcopy({"schema": "deploy/aws-session-runtime-view/v1", "binding": self.records.binding,
                             "source_plan_sha256": self._plan_sha256, "account": self.records.account,
                             "region": self.records.region, "component": next(component for component, name in self._plan["stack_names"] if name == stack),
                             "stack": stack, "stack_id": stack_id, "phase": phase, "template_reference": reference,
                             "template": template, "parameters": parameters, "resources": resources,
                             "outputs": {name: outputs[name] for name in required}, "custody": custody,
                             "observed_at": observed["observed_at"]})
        except (SessionOperationFailure, RECORDS.SessionRecordFailure):
            raise
        except SESSION_CLI.SessionProviderFailure as failure:
            raise SessionOperationFailure("runtime-observation-unavailable:" + failure.code) from None
        except Exception:
            raise SessionOperationFailure("runtime-observation-unavailable") from None

    def _successful_stack(self, stack, document):
        """Observe CREATE custody from complete provider responses, never pages.

        The qualified provider must aggregate observations within its own bounds;
        a continuation token here is incomplete evidence, not a pagination plan.
        """
        try:
            stack_id, custody, current, events, outcomes, physical = self._inspect_stack(stack, document)
            executed = document["operations"].get("creation:" + stack + ":execute")
            _require(executed is not None, "output-creation-required")
            _require(outcomes.get("creation:" + stack + ":execute", {}).get("status") == "CREATE_COMPLETE",
                     "output-creation-unconfirmed")
            prior = document["creation_evidence"].get(stack)
            roots = CHANGE_SETS.execution_events(events, executed["operation_id"], stack_id)
            successes = [row for row in roots if row.get("ResourceStatus") == "CREATE_COMPLETE" and row.get("ResourceType") == "AWS::CloudFormation::Stack"
                         and row.get("StackId") == stack_id and row.get("LogicalResourceId") == stack]
            _require(len(successes) == 1 and isinstance(successes[0].get("EventId"), str)
                     and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,255}", successes[0]["EventId"]), "output-creation-unconfirmed")
            event_digest = _digest(successes[0]["EventId"])
            proof = {key: custody[key] for key in ("creation_request_sha256", "change_set_id_sha256")}
            proof["creation_event_id_sha256"] = event_digest
            _require(prior is None or proof == prior, "output-retained-creation-mismatch")
            return current, (stack, stack_id, proof, custody, outcomes, physical)
        except SessionOperationFailure:
            raise
        except (RECORDS.CLI.CliFailure, SESSION_CLI.SessionProviderFailure) as failure:
            codes = SESSION_CLI.FAILURE_CODES if isinstance(failure, SESSION_CLI.SessionProviderFailure) else RECORDS.CLI_FAILURE_CODES
            code = failure.code if failure.code in codes else "aws-command-failed"
            raise SessionOperationFailure("output-observation-unavailable:" + code) from None
        except Exception:
            raise SessionOperationFailure("output-observation-unavailable") from None

    def _discard_stack(self, stack, document):
        current, proof = self._successful_stack(stack, document)
        if current.get("StackStatus") == "UPDATE_FAILED":
            outcomes = proof[4]
            _require(document["state"] == "sealed"
                     and outcomes.get("activation:" + stack + ":execute", {}).get("status") == "UPDATE_FAILED"
                     and not any(key.startswith("prepare-discard:" + stack + ":") for key in document["operations"]),
                     "discard-recovery-unconfirmed")
        else:
            self._foundation(FOUNDATION.stack_outputs, {"Stacks": [current]}, set())
        return current, proof

    def _change_identity(self, kind, stack, document, *, stack_id=None):
        """Authenticate available identity before interpreting mutable progress."""
        reference = dict(self._pairs)[stack]
        resolved = document["resolved"][kind + ":" + stack]
        request, arguments = self._operation(kind, stack, reference, document, resolved)
        prepared = document["operations"].get(kind + ":" + stack + ":prepare")
        _require(prepared is not None and prepared["request"] == request, "custody-reservation-mismatch")
        change = self._provider("cloudformation", "describe-change-set", StackName=stack_id or stack,
                                ChangeSetName=request["change_set"])
        source = self._plan["source_configuration"]
        prefix = "arn:aws:cloudformation:" + source["region"] + ":" + source["account"] + ":changeSet/" + request["change_set"] + "/"
        expected = {**document["resolved"]["creation:" + stack]["inputs"]["values"],
                    **dict(self._phase_sources(kind)[1][reference])}
        _require(isinstance(change, dict) and change.get("ChangeSetName") == request["change_set"]
                 and change.get("StackName") == stack and self._stack_id(stack, change.get("StackId"))
                 and (stack_id is None or change["StackId"] == stack_id)
                 and change.get("Description") == prepared["operation_id"]
                 and isinstance(change.get("ChangeSetId"), str) and len(change["ChangeSetId"]) <= 2048
                 and re.fullmatch(re.escape(prefix) + r"[A-Za-z0-9-]+", change["ChangeSetId"])
                 and change.get("Status") in ("CREATE_PENDING", "CREATE_IN_PROGRESS", "CREATE_COMPLETE", "FAILED",
                                              "DELETE_PENDING", "DELETE_IN_PROGRESS", "DELETE_COMPLETE", "DELETE_FAILED")
                 and change.get("ExecutionStatus") in ("AVAILABLE", "EXECUTE_IN_PROGRESS", "EXECUTE_COMPLETE", "EXECUTE_FAILED", "UNAVAILABLE", "OBSOLETE")
                 and ("Capabilities" not in change or change["Capabilities"] == ["CAPABILITY_NAMED_IAM"])
                 and change.get("IncludeNestedStacks", False) is False and change.get("ImportExistingResources", False) is False
                 and not change.get("RoleARN") and not change.get("NotificationARNs") and not change.get("NextToken")
                 and ("Parameters" not in change or CHANGE_SETS.parameter_values(change["Parameters"]) == expected), "output-creation-mismatch")
        _require("OnStackFailure" not in change, "operation-failure-policy-unconfirmed")
        return change, request, arguments, expected

    def _reviewed_change(self, kind, stack, document, *, stack_id=None, before_execute=False):
        change, request, arguments, expected = self._change_identity(kind, stack, document, stack_id=stack_id)
        _require(isinstance(change.get("Status"), str) and change["Status"] in RECORDS.TERMINAL_STATES["prepare"]
                 and change.get("Capabilities") == ["CAPABILITY_NAMED_IAM"]
                 and CHANGE_SETS.parameter_values(change.get("Parameters")) == expected, "output-creation-mismatch")
        if before_execute:
            _require(change.get("Status") == "CREATE_COMPLETE" and change.get("ExecutionStatus") == "AVAILABLE",
                     "operation-terminal-unconfirmed")
        else:
            execution_key = kind + ":" + stack + ":execute"
            _require(execution_key not in document["operations"]
                     or document["operation_outcomes"].get(execution_key, {}).get("status") == "not-submitted"
                     or change.get("ExecutionStatus") in ("EXECUTE_COMPLETE", "EXECUTE_FAILED"), "operation-terminal-unconfirmed")
        template = self._provider("cloudformation", "get-template", StackName=change["StackId"],
                                  ChangeSetName=change["ChangeSetId"], TemplateStage="Original")
        _require(isinstance(template, dict) and _template_matches(template.get("TemplateBody"), arguments["TemplateBody"]),
                 "custody-template-mismatch")
        resources = {key: row["Type"] for key, row in json.loads(arguments["TemplateBody"])["Resources"].items()}
        _require("AWS::CloudFormation::Stack" not in resources.values(), "custody-resource-mismatch")
        changes = change.get("Changes")
        _require(isinstance(changes, list), "custody-resource-mismatch")
        actual = {}
        for row in changes:
            item = row.get("ResourceChange") if isinstance(row, dict) else None
            _require(isinstance(item, dict) and isinstance(item.get("LogicalResourceId"), str) and item["LogicalResourceId"] in resources
                     and item["LogicalResourceId"] not in actual and item.get("ResourceType") == resources[item["LogicalResourceId"]]
                     and item.get("Action") == ("Add" if kind == "creation" else "Modify")
                     and item.get("Replacement", "False") == "False" and not item.get("ChangeSetId"), "custody-resource-mismatch")
            actual[item["LogicalResourceId"]] = item["ResourceType"]
        _require(kind != "creation" or actual == resources, "custody-resource-mismatch")
        return change, {"creation_request_sha256": _digest(request), "change_set_id_sha256": _digest(change["ChangeSetId"]),
                        "template_sha256": _digest(arguments["TemplateBody"]), "parameters_sha256": _digest(expected),
                        "resources_sha256": _digest(resources)}

    def _review_discard_execution(self, stack, document):
        """Review this first stop-only execution against retained, observed inputs."""
        reference, stack_id = dict(self._pairs)[stack], document["incarnations"][stack]
        change, _ = self._reviewed_change("prepare-discard", stack, document, stack_id=stack_id, before_execute=True)
        prior = []
        for kind in ("creation", "activation"):
            for phase in ("prepare", "execute"):
                key = kind + ":" + stack + ":" + phase
                if key in document["operations"]:
                    outcome = document["operation_outcomes"].get(key)
                    _require(outcome is not None, "operation-terminal-unconfirmed")
                    if phase == "execute" and outcome["status"] != "not-submitted":
                        prior.append((kind, key, outcome))
        _require(bool(prior), "output-creation-required")
        kind, key, outcome = prior[-1]
        response = self._provider("cloudformation", "describe-stacks", StackName=stack_id)
        rows = response.get("Stacks") if isinstance(response, dict) else None
        _require(isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict)
                 and not response.get("NextToken"), "output-stack-mismatch")
        current = rows[0]
        _require(current.get("StackId") == stack_id and current.get("StackName") == stack
                 and current.get("StackStatus") == outcome["status"], "operation-current-state-mismatch")
        events = self._provider("cloudformation", "describe-stack-events", StackName=stack_id)
        _require(isinstance(events, dict) and not events.get("NextToken") and isinstance(events.get("StackEvents"), list),
                 "output-events-incomplete")
        _require(self._event_outcome(key, document["operations"][key], stack_id, events) == outcome,
                 "operation-retained-mismatch")
        prepared = [phase for phase in ("creation", "activation")
                    if document["operation_outcomes"].get(phase + ":" + stack + ":prepare", {}).get("status") in ("CREATE_COMPLETE", "FAILED")]
        self._attached_role(current, document, [(phase, result) for phase, _, result in prior],
                            [*prepared, "prepare-discard"])
        values = CHANGE_SETS.parameter_values(current.get("Parameters"))
        _require(values is not None and _digest(values) == document["resolved"]["prepare-discard:" + stack]["inputs"]["observed_values_sha256"],
                 "deployed-inputs-drift")
        observed = self._provider("cloudformation", "get-template", StackName=stack_id, TemplateStage="Original")
        previous = self._phase_sources(kind)[0][reference]
        _require(isinstance(observed, dict) and _template_matches(observed.get("TemplateBody"), previous), "custody-template-mismatch")
        old = json.loads(previous)["Resources"]
        new = json.loads(self._discard_templates[reference])["Resources"]
        _require(set(old) == set(new), "discard-change-invalid")
        allowed = {}
        for logical, resource in new.items():
            earlier = old[logical]
            _require({key: value for key, value in earlier.items() if key != "Properties"}
                     == {key: value for key, value in resource.items() if key != "Properties"}, "discard-change-invalid")
            before, after = earlier.get("Properties", {}), resource.get("Properties", {})
            fields = {name for name in set(before) | set(after)
                      if name not in before or name not in after or before[name] != after[name]}
            if fields:
                allowed[logical] = fields
        actual = {}
        for row in change["Changes"]:
            resource = row["ResourceChange"]
            logical, details = resource["LogicalResourceId"], resource.get("Details")
            _require(logical in allowed and resource.get("Scope") == ["Properties"]
                     and isinstance(details, list) and len(details) == len(allowed[logical]), "discard-change-invalid")
            names = set()
            for detail in details:
                target = detail.get("Target") if isinstance(detail, dict) else None
                _require(isinstance(target, dict) and isinstance(target.get("Name"), str) and target["Name"] in allowed[logical]
                         and target["Name"] not in names
                         and target == {"Attribute": "Properties", "Name": target["Name"], "RequiresRecreation": "Never"}
                         and detail == {"Target": target, "Evaluation": "Static", "ChangeSource": "DirectModification"},
                         "discard-change-invalid")
                names.add(target["Name"])
            actual[logical] = names
        _require(actual == allowed, "discard-change-invalid")

    def _latest_event(self, key, reservation, stack_id, events):
        kind, stack, _ = key.split(":")
        _require(isinstance(events, dict) and not events.get("NextToken")
                 and isinstance(events.get("StackEvents"), list), "output-events-incomplete")
        roots = CHANGE_SETS.execution_events(events, reservation["operation_id"], stack_id)
        if not roots:
            return None
        checked = []
        for row in roots:
            _require(row.get("StackId") == stack_id and row.get("LogicalResourceId") == stack
                     and row.get("ResourceType") == "AWS::CloudFormation::Stack"
                     and isinstance(row.get("EventId"), str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,255}", row["EventId"]),
                     "operation-event-invalid")
            try:
                stamp = row["Timestamp"]
                _require(isinstance(stamp, str) and len(stamp) <= 32 and re.fullmatch(
                    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|\+00:00)", stamp),
                    "operation-event-invalid")
                instant = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                _require(datetime.fromisoformat(reservation["reserved_at"]) <= instant <= datetime.now(timezone.utc),
                         "operation-event-invalid")
            except (KeyError, ValueError, RECORDS.SessionRecordFailure):
                raise SessionOperationFailure("operation-event-invalid") from None
            checked.append((instant, row))
        checked.sort(key=lambda value: value[0])
        _require(len({row["EventId"] for _, row in checked}) == len(checked)
                 and (len(checked) == 1 or checked[-2][0] < checked[-1][0]), "operation-event-invalid")
        latest = checked[-1][1]
        _require(kind == "delete" or reservation["request"].get("disable_rollback") is True, "operation-failure-policy-unconfirmed")
        pending = {"creation": ("CREATE_IN_PROGRESS", "ROLLBACK_IN_PROGRESS"),
                   "activation": ("UPDATE_IN_PROGRESS", "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS", "UPDATE_ROLLBACK_IN_PROGRESS", "UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS"),
                   "prepare-discard": ("UPDATE_IN_PROGRESS", "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS", "UPDATE_ROLLBACK_IN_PROGRESS", "UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS"),
                   "delete": ("DELETE_IN_PROGRESS",)}
        _require(isinstance(latest.get("ResourceStatus"), str)
                 and (latest["ResourceStatus"] in RECORDS.TERMINAL_STATES[kind]
                      or latest["ResourceStatus"] in pending[kind]), "operation-event-invalid")
        return {"request_sha256": reservation["request_sha256"], "status": latest["ResourceStatus"],
                "evidence_sha256": _digest(latest), "observed_at": checked[-1][0].isoformat(timespec="microseconds")}

    def _event_outcome(self, key, reservation, stack_id, events):
        outcome = self._latest_event(key, reservation, stack_id, events)
        _require(outcome is not None and outcome["status"] in RECORDS.TERMINAL_STATES[key.split(":")[0]],
                 "operation-terminal-unconfirmed")
        return outcome

    def _creation_binding(self, stack, document):
        """Reconstruct immutable original inputs without requiring current status."""
        prepared = document["operations"].get("creation:" + stack + ":prepare")
        _require(prepared is not None, "output-creation-required")
        reference = dict(self._pairs)[stack]
        original_request, _ = self._operation("creation", stack, reference, document, document["resolved"]["creation:" + stack])
        _require(prepared["request"] == original_request, "custody-reservation-mismatch")
        original = document["resolved"]["creation:" + stack]["inputs"]["values"]
        resources = {key: row["Type"] for key, row in json.loads(self._templates[reference])["Resources"].items()}
        custody = document["creation_custody"].get(stack)
        if custody is not None:
            _require(custody["creation_request_sha256"] == prepared["request_sha256"]
                     and custody["template_sha256"] == _digest(self._templates[reference])
                     and custody["parameters_sha256"] == _digest(original)
                     and custody["resources_sha256"] == _digest(resources), "custody-retained-mismatch")
        return reference, original, custody

    def _inspect_stack(self, stack, document):
        """Concrete original custody plus every admitted operation, without writes."""
        reference, original, custody = self._creation_binding(stack, document)
        changes = {}
        if custody is None:
            change, custody = self._reviewed_change("creation", stack, document)
            changes["creation"] = change
            stack_id = change["StackId"]
        else:
            stack_id = document["incarnations"][stack]
        _require(document["incarnations"].get(stack, stack_id) == stack_id, "output-retained-creation-mismatch")
        response = self._provider("cloudformation", "describe-stacks", StackName=stack_id)
        _require(isinstance(response, dict) and not response.get("NextToken") and isinstance(response.get("Stacks"), list)
                 and len(response["Stacks"]) == 1 and isinstance(response["Stacks"][0], dict), "output-stack-mismatch")
        current = response["Stacks"][0]
        _require(current.get("StackId") == stack_id and current.get("StackName") == stack, "output-stack-mismatch")
        members = self._provider("cloudformation", "list-stack-resources", StackName=stack_id)
        physical, _ = self._physical_projection(stack, stack_id, members)
        events = self._provider("cloudformation", "describe-stack-events", StackName=stack_id)
        _require(isinstance(events, dict) and not events.get("NextToken") and isinstance(events.get("StackEvents"), list), "output-events-incomplete")
        outcomes = {}
        for kind in ("creation", "activation", "prepare-discard"):
            for phase in ("prepare", "execute"):
                key = kind + ":" + stack + ":" + phase
                reservation = document["operations"].get(key)
                if reservation is None:
                    continue
                expected_request, _ = self._operation(kind, stack, reference, document, document["resolved"][kind + ":" + stack])
                _require(reservation["request"] == expected_request, "custody-reservation-mismatch")
                prior = document["operation_outcomes"].get(key)
                if prior is not None:
                    if phase == "execute" and prior["status"] != "not-submitted":
                        _require(self._event_outcome(key, reservation, stack_id, events) == prior, "operation-retained-mismatch")
                    outcomes[key] = prior
                    continue
                if phase == "prepare":
                    change = changes.get(kind)
                    if change is None:
                        change, _ = self._reviewed_change(kind, stack, document, stack_id=stack_id)
                        changes[kind] = change
                    outcomes[key] = {"request_sha256": reservation["request_sha256"], "status": change["Status"],
                                     "evidence_sha256": _digest(change), "observed_at": reservation["reserved_at"]}
                else:
                    outcomes[key] = self._event_outcome(key, reservation, stack_id, events)
        for kind, change in changes.items():
            if change.get("ExecutionStatus") == "EXECUTE_FAILED":
                terminal = outcomes.get(kind + ":" + stack + ":execute", {}).get("status")
                _require(terminal in RECORDS.TERMINAL_STATES[kind]
                         and terminal not in ("CREATE_COMPLETE", "UPDATE_COMPLETE"), "operation-terminal-unconfirmed")
        executed = [(kind, outcomes[kind + ":" + stack + ":execute"]) for kind in
                    ("creation", "activation", "prepare-discard") if kind + ":" + stack + ":execute" in outcomes
                    and outcomes[kind + ":" + stack + ":execute"]["status"] != "not-submitted"]
        phases = ("creation", "activation", "prepare-discard")
        prepared = [kind for kind in phases
                    if outcomes.get(kind + ":" + stack + ":prepare", {}).get("status") in ("CREATE_COMPLETE", "FAILED")]
        self._attached_role(current, document, executed, prepared)
        if executed:
            kind, terminal = executed[-1]
            _require(current.get("StackStatus") == terminal["status"], "operation-current-state-mismatch")
            if terminal["status"] in ("CREATE_COMPLETE", "CREATE_FAILED", "UPDATE_COMPLETE", "UPDATE_FAILED"):
                template = self._provider("cloudformation", "get-template", StackName=stack_id, TemplateStage="Original")
                _require(isinstance(template, dict) and _template_matches(template.get("TemplateBody"), self._phase_sources(kind)[0][reference]), "custody-template-mismatch")
                expected = {**original, **dict(self._phase_sources(kind)[1][reference])}
                _require(CHANGE_SETS.parameter_values(current.get("Parameters")) == expected, "deployed-inputs-drift")
        else:
            _require(current.get("StackStatus") == "REVIEW_IN_PROGRESS", "operation-current-state-mismatch")
            if document["state"] in ("sealed", "deleting"):
                physical, _ = self._physical_projection(stack, stack_id, members, never_allocated=True)
        return stack_id, custody, current, events, outcomes, physical

    def _attached_role(self, current, document, executed, prepared):
        """Consume positively checked phase custody, never a reservation alone."""
        phases = ("creation", "activation", "prepare-discard")
        roles = document["base"]["execution_roles"]
        role_for = lambda kind: roles["cleanup" if kind == "prepare-discard" else "creation"]
        successful = executed and executed[-1][1]["status"] in ("CREATE_COMPLETE", "UPDATE_COMPLETE")
        later_prepared = executed and any(phases.index(kind) > phases.index(executed[-1][0])
                                         and role_for(kind) != role_for(executed[-1][0]) for kind in prepared)
        if successful and not later_prepared:
            _require(current.get("RoleARN") == role_for(executed[-1][0]), "execution-role-unconfirmed")
        else:
            # Preparation may attach its role without executing. Missing role
            # on failed/REVIEW roots cannot veto independently owned cleanup.
            _require(isinstance(current.get("RoleARN"), str) and current["RoleARN"] in {role_for(kind) for kind in prepared}
                     or "RoleARN" not in current and not successful, "execution-role-unconfirmed")

    def _retain_inspection(self, stack, stack_id, custody, outcomes, evidence=None, physical=None):
        self.records.retain_ownership(stack, stack_id, evidence, custody=custody, outcomes=outcomes, physical=physical)

    def _stopped(self, stack, stack_id, document, current):
        reference = dict(self._pairs)[stack]
        desired = {**document["resolved"]["creation:" + stack]["inputs"]["values"], **dict(self._discard_controls[reference])}
        template = self._provider("cloudformation", "get-template", StackName=stack_id, TemplateStage="Original")
        _require(isinstance(template, dict) and "TemplateBody" in template, "custody-template-mismatch")
        values = CHANGE_SETS.parameter_values(current.get("Parameters"))
        _require(values is not None and set(values) == set(desired), "deployed-inputs-drift")
        return _template_matches(template["TemplateBody"], self._discard_templates[reference]) and values == desired

    def _cleanup_readiness(self, stack, stack_id):
        document = self.records.observe_existing()["document"]
        _require(document["state"] in ("sealed", "deleting"), "admission-open")
        admitted = sorted({key.split(":")[1] for key in document["operations"] if key.startswith("creation:")
                           and document["operation_outcomes"].get(key, {}).get("status") != "not-submitted"})
        _require(stack in admitted, "output-creation-required")
        try:
            for owner in admitted:
                # Earlier exact delete intents are observation-only, not absence evidence.
                if owner != stack and "delete:" + owner + ":delete" in document["operations"]:
                    continue
                owned_id, custody, current, _, outcomes, physical = self._inspect_stack(owner, document)
                _require(owner != stack or owned_id == stack_id, "custody-stack-mismatch")
                if current["StackStatus"] != "REVIEW_IN_PROGRESS":
                    _require(self._stopped(owner, owned_id, document, current), "discard-required")
                    physical = self._capture_cleanup_bindings(owner, owned_id, document, physical)
                self._retain_inspection(owner, owned_id, custody, outcomes, physical=physical)
        except (SessionOperationFailure, RECORDS.SessionRecordFailure):
            raise
        except SESSION_CLI.SessionProviderFailure as failure:
            raise SessionOperationFailure("cleanup-observation-unavailable:" + failure.code) from None
        except Exception:
            raise SessionOperationFailure("cleanup-observation-unavailable") from None
        latest = self.records.observe_existing()["document"]
        _require(RECORDS.operations_sha256(latest) == RECORDS.operations_sha256(document), "reconciliation-changed")
        _require(stack in latest["physical_resources"] and latest["incarnations"][stack] == stack_id,
                 "physical-retention-required")
        return RECORDS.operations_sha256(latest), _digest(latest["physical_resources"][stack])

    def _resolve(self, kind, stack, reference, document):
        base = self._base(document)
        templates, selections = self._phase_sources(kind)
        controls = dict(selections[reference])
        proofs = []
        if kind == "creation":
            declarations = json.loads(templates[reference]).get("Parameters", {})
            values = {key: row["Default"] for key, row in declarations.items() if "Default" in row}
            values.update(controls)
            publications = dict(self._plan["publication_selections"])
            source_values = {(owner, key): value for owner, key, value in self._plan["execution_source_values"]}
            for owner, key, items in self._plan["execution_parameters"]:
                if owner != stack:
                    continue
                recipe = dict(items)
                if recipe["kind"] == "choice":
                    values[key] = base["choices"][recipe["contract"]][recipe["field"]]
                elif recipe["kind"] == "package":
                    pipeline = dict(publications[stack])["pipeline"]
                    values[key] = base["packages"][pipeline]["receipt"][recipe["field"]]
                elif recipe["kind"] == "source":
                    values[key] = source_values[(stack, key)]
                elif recipe["kind"] == "provider":
                    values[key] = base["provider_facts"][recipe["contract"]]
            rows = [row for row in (*self._plan["stack_parameter_sources"], *self._plan["execution_output_sources"]) if row[0] == stack]
            for producer in sorted({row[2] for row in rows}):
                selected = [row for row in rows if row[2] == producer]
                _, outputs, proof = self._owned_stack(producer, document, {row[3] for row in selected})
                proofs.append(proof)
                values.update({parameter: outputs[output] for _, parameter, _, output in selected})
            values = self._checked_values(templates[reference], values)
            inputs = {"values": values, "producer_stacks": sorted(row[0] for row in proofs)}
        else:
            if kind == "prepare-discard":
                current, proof = self._discard_stack(stack, document)
            else:
                current, _, proof = self._owned_stack(stack, document, set())
            original = document["resolved"]["creation:" + stack]["inputs"]["values"]
            deployed = CHANGE_SETS.parameter_values(current.get("Parameters"))
            _require(deployed is not None and set(deployed) == set(original)
                     and all(value == original[key] for key, value in deployed.items() if key not in controls), "deployed-inputs-drift")
            self._checked_values(templates[reference], deployed)
            self._checked_values(templates[reference], {**deployed, **controls})
            proofs = [proof]
            inputs = {"observed_values_sha256": _digest(deployed)}
        for owner, stack_id, proof, custody, outcomes, physical in proofs:
            self._retain_inspection(owner, stack_id, custody, outcomes, proof, physical)
        return inputs

    def _operation_observation(self, kind, stack, phase, *, admitting=None):
        """Observe only reconstructed retained intent; never grant replay authority."""
        key = kind + ":" + stack + ":" + phase
        document = self.records.observe_existing()["document"]
        self._base(document)
        reservation = document["operations"].get(key)
        result = {"operation": key, "status": "unreserved", "reason": "unreserved",
                  "request_sha256": None if reservation is None else reservation["request_sha256"], "provider_status": None}
        if reservation is None:
            return result
        if kind == "delete":
            stack_id = reservation["request"]["stack_id"]
            request = RECORDS.operation_request(document, kind, stack, _digest(self._delete_arguments(document, stack_id)), stack_id=stack_id)
        else:
            reference = dict(self._pairs)[stack]
            request, _ = self._operation(kind, stack, reference, document, document["resolved"][kind + ":" + stack])
        _require(_Reservations(self.records.storage(kind), request).read(phase, request) == reservation,
                 "custody-reservation-mismatch")
        prior = document["operation_outcomes"].get(key)
        if prior is not None and prior["status"] == "not-submitted":
            return {**result, "status": "not-submitted", "reason": "not-submitted"}
        try:
            if phase == "prepare":
                execution = document["operations"].get(kind + ":" + stack + ":execute")
                if prior is not None and execution is not None and execution != admitting:
                    return {**result, "status": "succeeded" if prior["status"] == "CREATE_COMPLETE" else "failed",
                            "reason": "execution-reserved", "provider_status": prior["status"]}
                change, _, _, _ = self._change_identity(kind, stack, document, stack_id=document["incarnations"].get(stack))
                status = change["Status"]
                if status in ("CREATE_PENDING", "CREATE_IN_PROGRESS"):
                    return {**result, "status": "pending", "reason": "preparation-pending", "provider_status": status}
                if status == "FAILED":
                    _require(prior is None or prior["status"] == status, "operation-retained-mismatch")
                    outcome = {"request_sha256": reservation["request_sha256"], "status": status,
                               "evidence_sha256": _digest(change), "observed_at": reservation["reserved_at"]}
                    self.records.retain_outcome(key, prior or outcome)
                    return {**result, "status": "failed", "reason": "preparation-failed", "provider_status": status}
                if status != "CREATE_COMPLETE" or change["ExecutionStatus"] != "AVAILABLE":
                    return {**result, "status": "unknown", "reason": "preparation-unavailable", "provider_status": status}
                change, custody = self._reviewed_change(kind, stack, document,
                    stack_id=document["incarnations"].get(stack), before_execute=True)
                _require(prior is None or prior["status"] == "CREATE_COMPLETE", "operation-retained-mismatch")
                if kind == "prepare-discard":
                    self._review_discard_execution(stack, document)
                outcome = {"request_sha256": reservation["request_sha256"], "status": "CREATE_COMPLETE",
                           "evidence_sha256": _digest(change), "observed_at": reservation["reserved_at"]}
                if kind == "creation":
                    self._retain_inspection(stack, change["StackId"], custody, {key: prior or outcome})
                else:
                    self.records.retain_outcome(key, prior or outcome)
                return {**result, "status": "ready", "reason": "ready", "provider_status": "CREATE_COMPLETE"}
            _, _, custody = self._creation_binding(stack, document)
            _require(custody is not None and stack in document["incarnations"], "custody-retained-mismatch")
            stack_id = document["incarnations"][stack]
            _require(kind != "delete" or request["stack_id"] == stack_id, "custody-stack-mismatch")
            events = self._provider("cloudformation", "describe-stack-events", StackName=stack_id)
            outcome = self._latest_event(key, reservation, stack_id, events)
            if outcome is None:
                return {**result, "status": "unknown", "reason": "operation-event-unconfirmed"}
            response = self._provider("cloudformation", "describe-stacks", StackName=stack_id)
            rows = response.get("Stacks") if isinstance(response, dict) else None
            _require(isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict)
                     and rows[0].get("StackId") == stack_id and rows[0].get("StackName") == stack
                     and not response.get("NextToken"), "output-stack-mismatch")
            if rows[0].get("StackStatus") != outcome["status"]:
                return {**result, "status": "unknown", "reason": "operation-current-state-mismatch"}
            if outcome["status"] not in RECORDS.TERMINAL_STATES[kind]:
                return {**result, "status": "pending", "reason": "operation-pending", "provider_status": outcome["status"]}
            if prior is not None:
                _require(prior == outcome, "operation-retained-mismatch")
            if kind == "delete":
                self.records.retain_outcome(key, outcome)
            else:
                owned_id, custody, _, _, outcomes, physical = self._inspect_stack(stack, document)
                _require(owned_id == stack_id and outcomes[key] == outcome, "operation-retained-mismatch")
                self._retain_inspection(stack, stack_id, custody, outcomes)
            succeeded = outcome["status"] in ("CREATE_COMPLETE", "UPDATE_COMPLETE", "DELETE_COMPLETE")
            return {**result, "status": "succeeded" if succeeded else "failed",
                    "reason": "operation-succeeded" if succeeded else "operation-failed", "provider_status": outcome["status"]}
        except (SessionOperationFailure, RECORDS.SessionRecordFailure):
            raise
        except SESSION_CLI.SessionProviderFailure as failure:
            return {**result, "status": "unknown", "reason": failure.code}
        except Exception:
            return {**result, "status": "unknown", "reason": "observation-unavailable"}

    def reconcile_operation(self, **inputs):
        _require(set(inputs) == {"kind", "stack", "phase"}, "operation-inputs-invalid")
        kind, stack, phase = (inputs[key] for key in ("kind", "stack", "phase"))
        _require(isinstance(kind, str) and kind in ("creation", "activation", "prepare-discard", "delete"), "kind-unsupported")
        _require(isinstance(stack, str) and stack in self._stacks, "instance-selection-invalid")
        _require(phase == "delete" if kind == "delete" else phase in ("prepare", "execute"), "operation-inputs-invalid")
        if kind != "delete":
            self._selection(kind, stack, dict(self._pairs)[stack])
        return self._operation_observation(kind, stack, phase)

    def _execution_ready(self, kind, stack, *, admitting=None):
        result = self._operation_observation(kind, stack, "prepare", admitting=admitting)
        _require(result["status"] == "ready", "execution-not-ready:" + result["reason"])

    def reconcile_stops(self, **inputs):
        _require(not inputs, "operation-inputs-invalid")
        document = self.records.observe_existing()["document"]
        self._base(document)
        _require(document["state"] in ("sealed", "deleting"), "admission-open")
        result = []
        for stack in reversed(self._plan["stack_order"]):
            row = {"stack": stack, "status": "not-started", "reason": "not-started"}
            if "creation:" + stack + ":prepare" not in document["operations"]:
                result.append(row)
                continue
            if (document["operation_outcomes"].get("creation:" + stack + ":prepare", {}).get("status") == "not-submitted"
                    and "creation:" + stack + ":execute" not in document["operations"]):
                result.append({**row, "reason": "creation-not-submitted"})
                continue
            if "delete:" + stack + ":delete" in document["operations"]:
                result.append({**row, "status": "delete-observation-only", "reason": "delete-reserved"})
                continue
            try:
                blocked = None
                for kind in ("creation", "activation", "prepare-discard"):
                    for phase in ("prepare", "execute"):
                        key = kind + ":" + stack + ":" + phase
                        if key not in document["operations"]:
                            continue
                        retained = document["operation_outcomes"].get(key)
                        if retained is not None:
                            continue
                        observation = self._operation_observation(kind, stack, phase)
                        if observation["status"] in ("pending", "unknown"):
                            blocked = {**row, "status": "pending" if observation["status"] == "pending" else "blocked",
                                       "reason": observation["reason"]}
                            break
                    if blocked:
                        break
                if blocked:
                    result.append(blocked)
                    continue
                document = self.records.observe_existing()["document"]
                stack_id, custody, current, _, outcomes, physical = self._inspect_stack(stack, document)
                status = ("never-allocated" if current["StackStatus"] == "REVIEW_IN_PROGRESS" else
                          "stopped" if self._stopped(stack, stack_id, document, current) else "stop-required")
                # A previously consumed stop label cannot authorize another stop.
                if status == "stop-required" and ("prepare-discard:" + stack + ":execute" in document["operations"]
                        or document["operation_outcomes"].get("prepare-discard:" + stack + ":prepare", {}).get("status") in ("FAILED", "not-submitted")):
                    status = "blocked"
                self._retain_inspection(stack, stack_id, custody, outcomes, physical=physical)
                result.append({**row, "status": status, "reason": "stop-attempt-retained" if status == "blocked" else status})
            except RECORDS.SessionRecordFailure:
                raise
            except SessionOperationFailure as failure:
                result.append({**row, "status": "blocked", "reason": failure.code})
            except SESSION_CLI.SessionProviderFailure as failure:
                result.append({**row, "status": "blocked", "reason": failure.code})
            except Exception:
                result.append({**row, "status": "blocked", "reason": "observation-unavailable"})
        return result

    def _run(self, phase, kind, *, stack, template_reference):
        self._selection(kind, stack, template_reference)
        document = self.records.observe_existing()["document"]
        self._base(document)
        resolved = document["resolved"].get(kind + ":" + stack)
        if resolved is None:
            _require(phase == "prepare", "preparation-required")
            self.records.check_input_admission(kind)
            try:
                inputs = self._resolve(kind, stack, template_reference, document)
            except (SessionOperationFailure, RECORDS.SessionRecordFailure):
                raise
            except Exception:
                raise SessionOperationFailure("input-resolution-unconfirmed") from None
            resolved = self.records.retain_inputs(kind, stack, document["base_sha256"], inputs)
            document = self.records.observe_existing()["document"]
        request, arguments = self._operation(kind, stack, template_reference, document, resolved)
        operation_arguments = deepcopy(arguments)
        store = _Reservations(self.records.storage(kind), request)
        preparation = None
        if phase == "execute":
            preparation = store.read("prepare", request)
            _require(preparation is not None, "preparation-required")
            if store.read("execute", request) is None:
                self._execution_ready(kind, stack)
            arguments = {"StackName": arguments["StackName"], "ChangeSetName": request["change_set"],
                         "DisableRollback": request["disable_rollback"]}
        return self._submit(phase, kind, request, arguments, operation_arguments, store, preparation)

    def _submit(self, phase, kind, request, arguments, operation_arguments, store, preparation=None,
                reconciled_operations_sha256=None):
        action = "delete" if kind == "delete" else kind + "-" + phase
        def observed(reservation):
            return self._operation_observation(kind, request["stack"], phase)

        def admitted(reservation):
            # This runs inside the existing engine, strictly before its provider call.
            try:
                self._admit(action, request, reservation, preparation, operation_arguments)
                if kind == "delete":
                    _require(self._cleanup_readiness(request["stack"], request["stack_id"]) == reconciled_operations_sha256,
                             "reconciliation-changed")
                elif phase == "execute":
                    self._execution_ready(kind, request["stack"], admitting=reservation)
            except Exception:
                self.records.retain_outcome(kind + ":" + request["stack"] + ":" + phase,
                    {"request_sha256": reservation["request_sha256"], "status": "not-submitted",
                     "evidence_sha256": _digest({"operation_id": reservation["operation_id"], "boundary": "pre-provider"}),
                     "observed_at": reservation["reserved_at"]})
                raise

        try:
            operation = {"prepare": CHANGE_SETS.prepare, "execute": CHANGE_SETS.execute, "delete": CHANGE_SETS.delete}[phase]
            return operation(self._provider, store, phase=phase, request=request, arguments=arguments,
                             precondition=admitted,
                             observe=observed, passthrough=(SessionOperationFailure,))
        except CHANGE_SETS.ChangeSetFailure as failure:
            reason = failure.code if failure.code in {"create-change-set-submission-uncertain", "execute-change-set-submission-uncertain",
                                                      "delete-stack-submission-uncertain"} else "submission-uncertain"
            cause = failure.__cause__
            if (isinstance(cause, RECORDS.CLI.CliFailure) and cause.code in RECORDS.CLI_FAILURE_CODES
                    or isinstance(cause, SESSION_CLI.SessionProviderFailure) and cause.code in SESSION_CLI.FAILURE_CODES):
                reason += ":" + cause.code
            raise SessionOperationFailure(reason) from None

    def prepare(self, kind, **inputs):
        _require(set(inputs) == {"stack", "template_reference"}, "operation-inputs-invalid")
        return self._run("prepare", kind, **inputs)

    def execute(self, kind, **inputs):
        _require(set(inputs) == {"stack", "template_reference"}, "operation-inputs-invalid")
        return self._run("execute", kind, **inputs)

    def delete(self, **inputs):
        """Reconcile original custody before one exact-ARN intent; not absence proof."""
        _require(set(inputs) == {"stack", "stack_id"}, "operation-inputs-invalid")
        stack, stack_id = (inputs[key] for key in ("stack", "stack_id"))
        _require(isinstance(stack, str) and stack in self._stacks, "instance-selection-invalid")
        _require(self._stack_id(stack, stack_id), "stack-identity-invalid")
        document = self.records.observe_existing()["document"]
        self._base(document)
        arguments = self._delete_arguments(document, stack_id)
        request = RECORDS.operation_request(document, "delete", stack, _digest(arguments), stack_id=stack_id)
        retained = _Reservations(self.records.storage("delete"), request).read("delete", request)
        reconciled = None
        if retained is None:
            self._revalidate_existing_source()
            reconciled = self._cleanup_readiness(stack, stack_id)
        store = _Reservations(self.records.storage("delete",
            reconciled_operations_sha256=None if reconciled is None else reconciled[0],
            physical_manifest_sha256=None if reconciled is None else reconciled[1]), request)
        return self._submit("delete", "delete", request, arguments, deepcopy(arguments), store,
                            reconciled_operations_sha256=reconciled)

    def retain_physical_observation(self, **inputs):
        """Retain late original-stack identities, never infer lost native lineage."""
        _require(set(inputs) == {"stack", "stack_id"}, "operation-inputs-invalid")
        stack, stack_id = inputs["stack"], inputs["stack_id"]
        _require(isinstance(stack, str) and stack in self._stacks, "instance-selection-invalid")
        _require(self._stack_id(stack, stack_id), "stack-identity-invalid")
        document = self.records.observe_existing()["document"]
        self._base(document)
        _require(document["state"] in ("sealed", "deleting"), "admission-open")
        _require(document["incarnations"].get(stack) == stack_id and stack in document["creation_custody"], "physical-retention-required")
        self._creation_binding(stack, document)
        try:
            response = self._provider("cloudformation", "list-stack-resources", StackName=stack_id)
            physical, _ = self._physical_projection(stack, stack_id, response)
            retained = self.records.retain_ownership(stack, stack_id, physical=physical)
            return deepcopy(retained["physical_resources"][stack])
        except (SessionOperationFailure, RECORDS.SessionRecordFailure):
            raise
        except SESSION_CLI.SessionProviderFailure as failure:
            raise SessionOperationFailure("physical-observation-unavailable:" + failure.code) from None
        except Exception:
            raise SessionOperationFailure("physical-observation-unavailable") from None

    def _cleanup_raw(self, stack, stack_id, physical):
        response = self._provider("cloudformation", "list-stack-resources", StackName=stack_id)
        observed, raw = self._physical_projection(stack, stack_id, response)
        _require(observed["slots"] == physical["slots"], "physical-identity-mismatch")
        return {logical: raw[position] for position, (logical, _) in enumerate(self._resource_index(stack)) if position in raw}

    def _binding_value(self, value, values, raw):
        if isinstance(value, dict):
            _require(set(value) == {"Ref"} and isinstance(value["Ref"], str), "cleanup-binding-unsupported")
            reference = value["Ref"]
            _require((reference in values) != (reference in raw), "cleanup-binding-unavailable")
            value = values[reference] if reference in values else raw[reference]
        _require(type(value) in (str, int) and value != "", "cleanup-binding-unsupported")
        return value

    def _relationship(self, resource, identity, values, raw, *, retained=None):
        properties, kind = resource.get("Properties", {}), resource["Type"]
        if kind == "AWS::ECS::Service":
            _require(isinstance(properties.get("Cluster"), dict), "cleanup-binding-unsupported")
            cluster = self._binding_value(properties["Cluster"], values, raw)
            context = re.escape(self.records.region + ":" + self.records.account)
            _require(isinstance(cluster, str) and re.fullmatch(r"arn:aws:ecs:" + context + r":cluster/[A-Za-z0-9_-]{1,255}", cluster)
                     and re.fullmatch(r"arn:aws:ecs:" + context + r":service/" + re.escape(cluster.split("/")[-1]) + r"/[A-Za-z0-9_-]+", identity), "cleanup-resource-identity-invalid")
            proof = _digest({"identity": identity, "cluster": cluster})
            _require(retained is None or retained == proof, "cleanup-relationship-unretained")
            if retained is not None:
                parent = self._observe_native_resource("AWS::ECS::Cluster", cluster)
                if parent in ("absent", "inactive"):
                    return proof, parent
            response = self._provider("ecs", "describe-services", cluster=cluster, services=[identity])
            rows, failures = response.get("services"), response.get("failures")
            _require(isinstance(rows, list) and isinstance(failures, list), "cleanup-resource-response-invalid")
            if not rows and retained is not None:
                _require(len(failures) == 1 and isinstance(failures[0], dict) and failures[0].get("arn") == identity
                         and failures[0].get("reason") == "MISSING" and set(failures[0]) <= {"arn", "reason", "detail"}
                         and ("detail" not in failures[0] or isinstance(failures[0]["detail"], str)), "cleanup-resource-response-invalid")
                return proof, "absent"
            _require(not failures and len(rows) == 1 and isinstance(rows[0], dict) and rows[0].get("serviceArn") == identity
                     and rows[0].get("clusterArn") == cluster and rows[0].get("status") in ("ACTIVE", "DRAINING", "INACTIVE"), "cleanup-resource-response-invalid")
            counts = [rows[0].get(key) for key in ("desiredCount", "runningCount", "pendingCount")]
            _require(all(type(count) is int and count >= 0 for count in counts)
                     and (rows[0]["status"] != "INACTIVE" or not any(counts)), "cleanup-resource-response-invalid")
            return proof, "inactive" if rows[0]["status"] == "INACTIVE" else "present"
        fields = {"GroupId", "IpProtocol", "FromPort", "ToPort", "CidrIp", "CidrIpv6", "SourceSecurityGroupId", "DestinationSecurityGroupId", "DestinationPrefixListId", "SourcePrefixListId", "Description"}
        _require(set(properties) <= fields and isinstance(properties.get("GroupId"), dict), "cleanup-binding-unsupported")
        checked = {key: self._binding_value(value, values, raw) for key, value in properties.items() if key != "Description"}
        group = checked.get("GroupId")
        _require(isinstance(group, str) and re.fullmatch(r"sg-(?:[a-f0-9]{8}|[a-f0-9]{17})", group), "cleanup-resource-identity-invalid")
        peers = [(key, checked[key]) for key in ("CidrIp", "CidrIpv6", "SourceSecurityGroupId", "DestinationSecurityGroupId", "DestinationPrefixListId", "SourcePrefixListId") if key in checked]
        _require(len(peers) == 1 and isinstance(checked.get("IpProtocol"), str)
                 and all(type(checked.get(key)) is int for key in ("FromPort", "ToPort")), "cleanup-binding-unsupported")
        proof = _digest({"identity": identity, "kind": kind, "properties": checked})
        _require(retained is None or retained == proof, "cleanup-relationship-unretained")
        try:
            response = self._provider("ec2", "describe-security-groups", GroupIds=[group])
        except SESSION_CLI.SessionProviderFailure as failure:
            if retained is not None and failure.code == "aws-resource-missing":
                return proof, "absent"
            raise
        rows = response.get("SecurityGroups")
        _require(isinstance(rows, list) and len(rows) <= 1 and all(isinstance(row, dict) and row.get("GroupId") == group for row in rows), "cleanup-resource-response-invalid")
        if not rows:
            _require(retained is not None, "cleanup-relationship-unconfirmed")
            return proof, "absent"
        permissions = rows[0].get("IpPermissionsEgress" if kind.endswith("Egress") else "IpPermissions")
        _require(isinstance(permissions, list) and all(isinstance(row, dict) for row in permissions), "cleanup-resource-response-invalid")
        key, peer = peers[0]
        collection, field = ("IpRanges", "CidrIp") if key == "CidrIp" else ("Ipv6Ranges", "CidrIpv6") if key == "CidrIpv6" else ("PrefixListIds", "PrefixListId") if "PrefixList" in key else ("UserIdGroupPairs", "GroupId")
        matches = 0
        for row in permissions:
            _require(isinstance(row.get("IpProtocol"), str), "cleanup-resource-response-invalid")
            for name, target in (("IpRanges", "CidrIp"), ("Ipv6Ranges", "CidrIpv6"), ("PrefixListIds", "PrefixListId"), ("UserIdGroupPairs", "GroupId")):
                members = row.get(name, [])
                _require(isinstance(members, list) and all(isinstance(member, dict) and isinstance(member.get(target), str) for member in members)
                         and len({member[target] for member in members}) == len(members), "cleanup-resource-response-invalid")
            if all(row.get(name) == checked[name] for name in ("IpProtocol", "FromPort", "ToPort")):
                matches += sum(member[field] == peer for member in row.get(collection, []))
        _require(matches <= 1 and (retained is not None or matches == 1), "cleanup-relationship-unconfirmed")
        return proof, "present" if matches else "absent"

    def _database_instance(self, identity, known):
        """Observe exact immutable lineage, independently of retention policy."""
        _require(isinstance(identity, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{0,62}", identity),
                 "cleanup-database-lineage-unconfirmed")
        response = self._provider("rds", "describe-db-instances", DBInstanceIdentifier=identity)
        databases = response.get("DBInstances") if isinstance(response, dict) else None
        _require(isinstance(databases, list) and len(databases) <= 1, "cleanup-database-lineage-unconfirmed")
        if not databases:
            return None
        database = databases[0]
        _require(isinstance(database, dict) and database.get("DBInstanceIdentifier") == identity
                 and database.get("DBInstanceArn") == "arn:aws:rds:" + self.records.region + ":" + self.records.account + ":db:" + identity,
                 "cleanup-database-lineage-unconfirmed")
        immutable = database.get("DbiResourceId")
        _require(isinstance(immutable, str) and re.fullmatch(r"db-[A-Z0-9]{1,64}", immutable), "cleanup-database-lineage-unconfirmed")
        _require(known == "unknown" or known == _digest(immutable), "cleanup-native-lineage-mismatch")
        return database

    def _capture_cleanup_bindings(self, stack, stack_id, document, physical):
        raw = self._cleanup_raw(stack, stack_id, physical)
        values = document["resolved"]["creation:" + stack]["inputs"]["values"]
        previous = document["physical_resources"].get(stack)
        for key, rows in self._cleanup_bindings(stack).items():
            for position, (logical, resource) in enumerate(rows):
                if logical not in raw:
                    continue  # Unknown allocation is never an artifact exemption.
                known = previous[key][position] if previous else "unknown"
                if known != "unknown" and key == "relationships":
                    physical[key][position] = known
                    continue
                identity = raw[logical]
                if key == "relationships":
                    try:
                        physical[key][position] = self._relationship(resource, identity, values, raw)[0]
                    except Exception:
                        # Missing correspondence cannot imply coverage, but does
                        # not veto independently proved exact-stack cleanup.
                        physical[key][position] = "unknown"
                elif key == "databases":
                    try:
                        database = self._database_instance(identity, known)
                    except SESSION_CLI.SessionProviderFailure as failure:
                        if known != "unknown" and failure.code == "aws-resource-missing":
                            physical[key][position] = known
                            continue
                        raise
                    if database is None and known != "unknown":
                        physical[key][position] = known
                        continue
                    _require(database is not None, "cleanup-database-lineage-unconfirmed")
                    physical[key][position] = _digest(database["DbiResourceId"])
                else:
                    try:
                        response = self._provider("servicediscovery", "get-namespace", Id=identity)
                    except SESSION_CLI.SessionProviderFailure as failure:
                        if known != "unknown" and failure.code == "aws-resource-missing":
                            physical[key][position] = known
                            continue
                        raise
                    namespace = response.get("Namespace")
                    reference = dict(self._pairs)[stack]
                    projected = CF.project_string_parameters(self._templates[reference], ("ResourceNamePrefix",), {"ResourceNamePrefix": values["ResourceNamePrefix"]})
                    name = projected["Resources"][logical]["Properties"]["Name"]
                    vpc = self._binding_value(resource["Properties"]["Vpc"], values, raw)
                    _require(isinstance(name, str) and isinstance(namespace, dict) and namespace.get("Id") == identity
                             and namespace.get("Name") == name and namespace.get("Type") == "DNS_PRIVATE", "cleanup-namespace-lineage-unconfirmed")
                    zone = namespace.get("Properties", {}).get("DnsProperties", {}).get("HostedZoneId")
                    _require(isinstance(zone, str) and re.fullmatch(r"[A-Z0-9]{1,32}", zone), "cleanup-namespace-lineage-unconfirmed")
                    _require(known == "unknown" or known == zone, "cleanup-native-lineage-mismatch")
                    self._hosted_zone(zone, name=name, vpc=vpc)
                    physical[key][position] = zone
        physical["observation_sha256"] = _digest({key: value for key, value in physical.items() if key not in ("observation_sha256", "observed_at")})
        return physical

    def _hosted_zone(self, identity, *, name=None, vpc=None):
        response = self._provider("route53", "get-hosted-zone", Id=identity)
        zone = response.get("HostedZone")
        _require(isinstance(zone, dict) and zone.get("Id") in (identity, "/hostedzone/" + identity)
                 and zone.get("Config", {}).get("PrivateZone") is True, "cleanup-resource-response-invalid")
        if name is not None:
            _require(zone.get("Name") == name.rstrip(".") + "." and response.get("VPCs") == [{"VPCId": vpc, "VPCRegion": self.records.region}], "cleanup-namespace-lineage-unconfirmed")
        return "present"

    def reconstruct_physical(self, **inputs):
        """Recover internal raw identities, never absence, from bounded CF lineage.

        AWS retains deleted-stack resource information for up to 90 days. Missing
        lineage is an error, not permission to invent identity or claim removal.
        This route does not require a deleted stack to have its old root status.
        """
        _require(set(inputs) == {"stack", "stack_id"}, "operation-inputs-invalid")
        stack, stack_id = inputs["stack"], inputs["stack_id"]
        _require(isinstance(stack, str) and stack in self._stacks, "instance-selection-invalid")
        _require(self._stack_id(stack, stack_id), "stack-identity-invalid")
        document = self.records.observe_existing()["document"]
        self._base(document)
        retained = document["physical_resources"].get(stack)
        _require(retained is not None and document["incarnations"].get(stack) == stack_id
                 and stack in document["creation_custody"], "physical-retention-required")
        self._creation_binding(stack, document)
        try:
            response = self._provider("cloudformation", "list-stack-resources", StackName=stack_id)
            physical, raw = self._physical_projection(stack, stack_id, response)
            resources = []
            for position, (logical, kind) in enumerate(self._resource_index(stack)):
                known, observed = retained["slots"][position], physical["slots"][position]
                if known == "unknown":
                    _require(observed == "unknown", "physical-observation-unretained")
                elif known == "never-allocated":
                    _require(observed == "unknown", "physical-allocation-contradiction")
                else:
                    _require(observed != "unknown", "physical-lineage-unavailable")
                    _require(observed == known, "physical-identity-mismatch")
                resources.append({"logical_id": logical, "resource_type": kind,
                                  "allocation": known if known in ("unknown", "never-allocated") else "allocated",
                                  "physical_id": raw.get(position)})
            return {"stack_id": stack_id, "resources": resources}
        except (SessionOperationFailure, RECORDS.SessionRecordFailure):
            raise
        except SESSION_CLI.SessionProviderFailure as failure:
            raise SessionOperationFailure("physical-observation-unavailable:" + failure.code) from None
        except Exception:
            raise SessionOperationFailure("physical-observation-unavailable") from None

    def _observe_native_resource(self, kind, identity):
        """Interpret exact native reads, not parent coverage or cleanup authority."""
        region, account = self.records.region, self.records.account
        ec2 = {
            "AWS::EC2::VPC": ("describe-vpcs", "VpcIds", "Vpcs", "VpcId", "vpc"),
            "AWS::EC2::Subnet": ("describe-subnets", "SubnetIds", "Subnets", "SubnetId", "subnet"),
            "AWS::EC2::RouteTable": ("describe-route-tables", "RouteTableIds", "RouteTables", "RouteTableId", "rtb"),
            "AWS::EC2::VPCEndpoint": ("describe-vpc-endpoints", "VpcEndpointIds", "VpcEndpoints", "VpcEndpointId", "vpce"),
            "AWS::EC2::SecurityGroup": ("describe-security-groups", "GroupIds", "SecurityGroups", "GroupId", "sg"),
        }
        native = {
            "AWS::RDS::DBInstance": ("rds", "describe-db-instances", "DBInstanceIdentifier", "DBInstances", "DBInstanceIdentifier", r"[A-Za-z][A-Za-z0-9-]{0,62}", True),
            "AWS::RDS::DBSubnetGroup": ("rds", "describe-db-subnet-groups", "DBSubnetGroupName", "DBSubnetGroups", "DBSubnetGroupName", r"[a-z0-9][a-z0-9._ -]{0,254}", True),
            "AWS::IAM::Role": ("iam", "get-role", "RoleName", "Role", "RoleName", r"[A-Za-z0-9+=,.@_-]{1,64}", False),
            "AWS::SecretsManager::Secret": ("secretsmanager", "describe-secret", "SecretId", None, "ARN",
                r"arn:aws:secretsmanager:" + re.escape(region + ":" + account) + r":secret:[A-Za-z0-9/_+=.@-]+-[A-Za-z0-9]{6}", False),
            "AWS::ServiceDiscovery::PrivateDnsNamespace": ("servicediscovery", "get-namespace", "Id", "Namespace", "Id", r"ns-[a-z0-9]+", False),
            "AWS::ServiceDiscovery::Service": ("servicediscovery", "get-service", "Id", "Service", "Id", r"srv-[a-z0-9]+", False),
            "AWS::Logs::LogGroup": ("logs", "describe-log-groups", "logGroupIdentifiers", "logGroups", "logGroupName", r"[.\-_/#A-Za-z0-9]{1,512}", True),
        }
        if kind in ec2:
            operation, argument, collection, field, prefix = ec2[kind]
            _require(re.fullmatch(prefix + r"-(?:[a-f0-9]{8}|[a-f0-9]{17})", identity) is not None, "cleanup-resource-identity-invalid")
            value = self._provider("ec2", operation, **{argument: [identity]})
            rows = value.get(collection) if isinstance(value, dict) else None
        elif kind in native:
            service, operation, argument, collection, field, pattern, multiple = native[kind]
            _require(re.fullmatch(pattern, identity) is not None, "cleanup-resource-identity-invalid")
            value = self._provider(service, operation, **{argument: [identity] if kind == "AWS::Logs::LogGroup" else identity})
            selected = value.get(collection) if isinstance(value, dict) and collection else value
            rows = selected if multiple else [selected]
        elif kind == "AWS::EC2::SubnetRouteTableAssociation":
            _require(re.fullmatch(r"rtbassoc-(?:[a-f0-9]{8}|[a-f0-9]{17})", identity) is not None, "cleanup-resource-identity-invalid")
            value = self._provider("ec2", "describe-route-tables",
                Filters=[{"Name": "association.route-table-association-id", "Values": [identity]}])
            tables = value.get("RouteTables") if isinstance(value, dict) else None
            _require(isinstance(tables, list) and len(tables) <= 1, "cleanup-resource-response-invalid")
            if not tables:
                return "absent"
            table = tables[0]
            _require(isinstance(table, dict) and isinstance(table.get("RouteTableId"), str)
                     and re.fullmatch(r"rtb-(?:[a-f0-9]{8}|[a-f0-9]{17})", table["RouteTableId"]), "cleanup-resource-response-invalid")
            associations = table.get("Associations")
            _require(isinstance(associations, list) and all(isinstance(row, dict)
                     and isinstance(row.get("RouteTableAssociationId"), str)
                     and row.get("RouteTableId") == table["RouteTableId"] for row in associations), "cleanup-resource-response-invalid")
            identifiers = [row["RouteTableAssociationId"] for row in associations]
            _require(len(set(identifiers)) == len(identifiers) and identifiers.count(identity) == 1, "cleanup-resource-response-invalid")
            return "present"
        elif kind == "AWS::ECS::Cluster":
            prefix = "arn:aws:ecs:" + region + ":" + account + ":cluster/"
            name = identity.removeprefix(prefix)
            _require(re.fullmatch(r"[A-Za-z0-9_-]{1,255}", name) is not None, "cleanup-resource-identity-invalid")
            arn = prefix + name
            value = self._provider("ecs", "describe-clusters", clusters=[arn])
            rows, failures = (value.get(key) for key in ("clusters", "failures")) if isinstance(value, dict) else (None, None)
            _require(isinstance(rows, list) and isinstance(failures, list), "cleanup-resource-response-invalid")
            if not rows:
                _require(len(failures) == 1 and isinstance(failures[0], dict)
                         and failures[0].get("arn") == arn and failures[0].get("reason") == "MISSING"
                         and set(failures[0]) <= {"arn", "reason", "detail"}
                         and ("detail" not in failures[0] or isinstance(failures[0]["detail"], str)), "cleanup-resource-response-invalid")
                return "absent"
            _require(not failures and len(rows) == 1 and isinstance(rows[0], dict)
                     and rows[0].get("clusterArn") == arn and rows[0].get("clusterName") == name
                     and rows[0].get("status") in ("ACTIVE", "PROVISIONING", "DEPROVISIONING", "FAILED", "INACTIVE"),
                     "cleanup-resource-response-invalid")
            counts = [rows[0][key] for key in ("runningTasksCount", "pendingTasksCount", "activeServicesCount", "registeredContainerInstancesCount") if key in rows[0]]
            _require(all(type(value) is int and value >= 0 for value in counts)
                     and (rows[0]["status"] != "INACTIVE" or all(value == 0 for value in counts)), "cleanup-resource-response-invalid")
            return "inactive" if rows[0]["status"] == "INACTIVE" else "present"
        elif kind == "AWS::ECS::TaskDefinition":
            _require(re.fullmatch(r"arn:aws:ecs:" + re.escape(region + ":" + account)
                     + r":task-definition/[A-Za-z0-9_-]{1,255}:[1-9][0-9]*", identity) is not None, "cleanup-resource-identity-invalid")
            value = self._provider("ecs", "describe-task-definition", taskDefinition=identity)
            definition = value.get("taskDefinition") if isinstance(value, dict) else None
            _require(isinstance(definition, dict) and definition.get("taskDefinitionArn") == identity
                     and definition.get("status") in ("ACTIVE", "INACTIVE", "DELETE_IN_PROGRESS"), "cleanup-resource-response-invalid")
            return "inactive" if definition["status"] == "INACTIVE" else "present"
        else:
            raise SessionOperationFailure("cleanup-resource-type-unsupported")
        _require(isinstance(rows, list) and len(rows) <= 1
                 and all(isinstance(row, dict) and row.get(field) == identity for row in rows), "cleanup-resource-response-invalid")
        # A scheduled secret deletion still returns the exact secret and is
        # present. Native database absence is not snapshot or backup absence.
        return "present" if rows else "absent"

    def _database_artifacts(self, lineage):
        _require(lineage != "unknown", "cleanup-database-lineage-unconfirmed")
        result = []
        for snapshot_type in ("manual", "automated", "awsbackup"):
            response = self._provider("rds", "describe-db-snapshots", SnapshotType=snapshot_type, IncludePublic=False, IncludeShared=False)
            rows = response.get("DBSnapshots")
            count = self._lineage_count(rows, lineage, "DBSnapshotArn", "snapshot")
            result.append({"kind": snapshot_type + "-snapshots", "status": "present" if count else "absent", "count": count})
        response = self._provider("rds", "describe-db-instance-automated-backups")
        rows = response.get("DBInstanceAutomatedBackups")
        count = self._lineage_count(rows, lineage, "DBInstanceAutomatedBackupsArn", "auto-backup")
        result.append({"kind": "automated-backups", "status": "present" if count else "absent", "count": count})
        if not isinstance(self._provider, SESSION_CLI.SessionProvider):
            # An unqualified callback cannot assert a global absence observation.
            result.append({"kind": "cross-region-backups", "status": "unknown"})
            return result
        regions = self._provider("ec2", "describe-regions", AllRegions=False).get("Regions")
        _require(isinstance(regions, list) and bool(regions)
            and all(isinstance(row, dict) and isinstance(row.get("RegionName"), str)
                and re.fullmatch(r"[a-z]{2}(?:-[a-z]+)+-[0-9]+", row["RegionName"])
                and row.get("OptInStatus") in ("opt-in-not-required", "opted-in") for row in regions)
            and len({row["RegionName"] for row in regions}) == len(regions)
            and self.records.region in {row["RegionName"] for row in regions}, "cleanup-regions-unconfirmed")
        count, inspected = 0, 0
        for region in sorted(row["RegionName"] for row in regions if row["RegionName"] != self.records.region):
            for snapshot_type in ("manual", "automated", "awsbackup"):
                response = self._provider.observe_region(region, "rds", "describe-db-snapshots",
                    SnapshotType=snapshot_type, IncludePublic=False, IncludeShared=False)
                count += self._lineage_count(response.get("DBSnapshots"), lineage, "DBSnapshotArn", "snapshot", region=region)
            response = self._provider.observe_region(region, "rds", "describe-db-instance-automated-backups")
            count += self._lineage_count(response.get("DBInstanceAutomatedBackups"), lineage, "DBInstanceAutomatedBackupsArn", "auto-backup", region=region)
            inspected += 1
        result.append({"kind": "cross-region-backups", "status": "present" if count else "absent", "count": count, "regions": inspected})
        return result

    def _lineage_count(self, rows, lineage, field, kind, *, region=None):
        _require(isinstance(rows, list), "cleanup-resource-response-invalid")
        seen, count = set(), 0
        prefix = "arn:aws:rds:" + (self.records.region if region is None else region) + ":" + self.records.account + ":" + kind + ":"
        for row in rows:
            _require(isinstance(row, dict), "cleanup-resource-response-invalid")
            identity, immutable = row.get(field), row.get("DbiResourceId")
            _require(isinstance(identity, str) and identity.startswith(prefix) and len(identity) > len(prefix)
                     and identity not in seen and isinstance(immutable, str) and re.fullmatch(r"db-[A-Z0-9]{1,64}", immutable), "cleanup-resource-response-invalid")
            seen.add(identity)
            count += _digest(immutable) == lineage
            if "DBInstanceAutomatedBackupsReplications" in row:
                replicas = row["DBInstanceAutomatedBackupsReplications"]
                _require(isinstance(replicas, list) and all(isinstance(item, dict) and isinstance(item.get("DBInstanceAutomatedBackupsArn"), str)
                         for item in replicas), "cleanup-resource-response-invalid")
        return count

    def complete_cleanup(self):
        """Observe the entire captured graph before retaining cleanup completion."""
        observed = self.records.observe_existing()
        document = observed["document"]
        self._base(document)
        _require(document["state"] in ("sealed", "deleting"), "admission-open")
        _require(document["functional_result"] is not None, "functional-result-required")
        self._admit("complete-cleanup")
        if document["cleanup_completion"] is not None:
            self.records._read_child(document["cleanup_completion"], max_bytes=RECORDS.CHILD_LIMIT)
            return {"status": "completed", "reference": deepcopy(document["cleanup_completion"]),
                    "evidence_reuse": "retained-cleanup"}
        stacks, remaining = {}, []
        for stack in self._plan["stack_order"]:
            preparation = "creation:" + stack + ":prepare"
            if preparation not in document["operations"]:
                stacks[stack] = {"status": "not-started"}
                continue
            if (document["operation_outcomes"].get(preparation, {}).get("status") == "not-submitted"
                    and "creation:" + stack + ":execute" not in document["operations"]):
                stacks[stack] = {"status": "not-submitted"}
                continue
            stack_id = document["incarnations"].get(stack)
            _require(stack_id is not None, "physical-retention-required")
            outcome = self.reconcile_operation(kind="delete", stack=stack, phase="delete")
            if outcome["status"] != "succeeded":
                stacks[stack] = {"status": outcome["status"]}
                remaining.append(outcome["status"])
                continue
            report = self.observe_resource_cleanup(stack=stack, stack_id=stack_id)
            resources = report["resources"]
            expected = dict(self._resource_index(stack))
            _require(isinstance(resources, list) and len(resources) == len(expected)
                     and {row["logical_id"]: row["resource_type"] for row in resources} == expected,
                     "cleanup-resource-set-mismatch")
            stacks[stack] = {"status": "removed", "resources": resources}
            for resource in resources:
                if not RECORDS.cleanup_terminal(resource):
                    remaining.append(resource["status"])
                for item in resource.get("artifacts", []):
                    if item["status"] not in ("absent", "never-allocated"):
                        remaining.append(item["status"])
        if remaining:
            return {"status": "unknown" if any(state in ("unknown", "unreserved", "blocked", "failed", "not-submitted")
                                                    for state in remaining) else "pending", "stacks": stacks}
        evidence = {"schema": "deploy/environment-session-cleanup/v1", "binding": self.records.binding,
                    "source_plan_sha256": self._plan_sha256, "stacks": stacks}
        reference = self.records.retain_cleanup_completion(evidence)
        return {"status": "completed", "reference": reference, "stacks": stacks}

    def observe_resource_cleanup(self, **inputs):
        """Read safe per-resource states; never write, delete or claim completion."""
        _require(set(inputs) == {"stack", "stack_id"}, "operation-inputs-invalid")
        stack, stack_id = inputs["stack"], inputs["stack_id"]
        _require(isinstance(stack, str) and stack in self._stacks, "instance-selection-invalid")
        _require(self._stack_id(stack, stack_id), "stack-identity-invalid")
        document = self.records.observe_existing()["document"]
        self._base(document)
        request = RECORDS.operation_request(document, "delete", stack, _digest(self._delete_arguments(document, stack_id)), stack_id=stack_id)
        reservation = _Reservations(self.records.storage("delete"), request).read("delete", request)
        _require(reservation is not None, "cleanup-delete-required")
        try:
            events = self._provider("cloudformation", "describe-stack-events", StackName=stack_id)
            outcome = self._event_outcome("delete:" + stack + ":delete", reservation, stack_id, events)
            _require(outcome["status"] == "DELETE_COMPLETE", "cleanup-delete-unconfirmed")
            response = self._provider("cloudformation", "describe-stacks", StackName=stack_id)
            current = response.get("Stacks") if isinstance(response, dict) else None
            _require(isinstance(current, list) and len(current) == 1 and isinstance(current[0], dict)
                     and current[0].get("StackId") == stack_id and current[0].get("StackName") == stack,
                     "cleanup-delete-observation-invalid")
            _require(current[0].get("StackStatus") == "DELETE_COMPLETE", "cleanup-delete-unconfirmed")
        except SessionOperationFailure:
            raise
        except SESSION_CLI.SessionProviderFailure as failure:
            raise SessionOperationFailure("cleanup-delete-observation-unavailable:" + failure.code) from None
        except Exception:
            raise SessionOperationFailure("cleanup-delete-observation-unavailable") from None
        retained = self.reconstruct_physical(stack=stack, stack_id=stack_id)
        manifest = document["physical_resources"][stack]
        bindings = self._cleanup_bindings(stack)
        positions = {key: {logical: position for position, (logical, _) in enumerate(rows)} for key, rows in bindings.items()}
        resources = {logical: resource for rows in bindings.values() for logical, resource in rows}
        raw = {row["logical_id"]: row["physical_id"] for row in retained["resources"] if row["allocation"] == "allocated"}
        values = document["resolved"]["creation:" + stack]["inputs"]["values"]
        result = []
        for row in retained["resources"]:
            observed = {"logical_id": row["logical_id"], "resource_type": row["resource_type"]}
            if row["allocation"] == "never-allocated":
                observed["status"] = "never-allocated"
            elif row["allocation"] == "unknown":
                observed.update(status="unknown", reason="environment-session-operation-physical-allocation-unknown")
            else:
                try:
                    if row["logical_id"] in positions["relationships"]:
                        known = manifest["relationships"][positions["relationships"][row["logical_id"]]]
                        _require(known != "unknown", "cleanup-relationship-unretained")
                        observed["status"] = self._relationship(resources[row["logical_id"]], row["physical_id"], values, raw, retained=known)[1]
                    else:
                        observed["status"] = self._observe_native_resource(row["resource_type"], row["physical_id"])
                except SessionOperationFailure as failure:
                    observed.update(status="unknown", reason=failure.code)
                except SESSION_CLI.SessionProviderFailure as failure:
                    if (failure.code == "aws-resource-missing"
                            and row["resource_type"] not in ("AWS::EC2::SubnetRouteTableAssociation", "AWS::ECS::Cluster", "AWS::ECS::TaskDefinition", "AWS::ECS::Service", "AWS::EC2::SecurityGroupIngress", "AWS::EC2::SecurityGroupEgress")):
                        observed["status"] = "absent"
                    else:
                        observed.update(status="unknown", reason="environment-session-operation-cleanup-resource-observation-unavailable:" + failure.code)
                except Exception:
                    observed.update(status="unknown", reason="environment-session-operation-cleanup-resource-observation-unavailable")
            for key, artifact in (("databases", "database-artifacts"), ("namespaces", "hosted-zone")):
                if row["logical_id"] not in positions[key]:
                    continue
                known = manifest[key][positions[key][row["logical_id"]]]
                if row["allocation"] == "never-allocated":
                    observed["artifacts"] = [{"kind": artifact, "status": "never-allocated"}]
                else:
                    try:
                        _require(known != "unknown", "cleanup-artifact-lineage-unconfirmed")
                        observed["artifacts"] = self._database_artifacts(known) if key == "databases" else [{"kind": artifact, "status": self._hosted_zone(known)}]
                    except SESSION_CLI.SessionProviderFailure as failure:
                        if key == "namespaces" and failure.code == "aws-resource-missing":
                            observed["artifacts"] = [{"kind": artifact, "status": "absent"}]
                        else:
                            observed["artifacts"] = [{"kind": artifact, "status": "unknown", "reason": "environment-session-operation-cleanup-resource-observation-unavailable:" + failure.code}]
                    except SessionOperationFailure as failure:
                        observed["artifacts"] = [{"kind": artifact, "status": "unknown", "reason": failure.code}]
                    except Exception:
                        observed["artifacts"] = [{"kind": artifact, "status": "unknown", "reason": "environment-session-operation-cleanup-resource-observation-unavailable"}]
            result.append(observed)
        return {"resources": result}
