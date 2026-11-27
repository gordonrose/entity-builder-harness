#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.aws.environment-sessions
#   version: 1
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-27"
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

The caller must qualify the supplied provider, remote-store guard, preflight and
observation callbacks through the normal custody/realization/approval workflow.
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
Prerequisite output rows describe source connections only. The qualified
preflight must resolve fresh owned outputs and reject caller replacements;
this adapter does not resolve outputs or validate network execution inputs.

This increment supports CREATE, captured activation UPDATE, and sealed captured
prepare-discard UPDATE change sets only. DeleteStack, final absence, successor
sessions and workload command integration are deliberately absent. Retained
operations only observe.
The plan's explicit stack/template rows bind dependency instances too;
membership in independent template and stack sets cannot establish a pairing.
"""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re


def _module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


RECORDS = _module("environment_session_records", "session_records.py")
RESERVATIONS = RECORDS.RESERVATIONS
CHANGE_SETS = _module("environment_session_change_sets", "change_sets.py")


class SessionOperationFailure(Exception):
    def __init__(self, condition):
        self.code = "environment-session-operation-" + condition
        super().__init__(self.code)


def _require(condition, reason):
    if not condition:
        raise SessionOperationFailure(reason)


def _digest(value):
    return hashlib.sha256(RESERVATIONS.canonical(value)).hexdigest()


class _Reservations(RESERVATIONS.ImmutableReservationStore):
    schema = "deploy/environment-session-operation/v1"
    operation_prefix = "es-"
    failure = SessionOperationFailure

    def __init__(self, storage, request):
        self.expected = deepcopy(request)
        super().__init__(None, storage=storage)

    def path_for(self, phase, request):
        _require(phase in {"prepare", "execute"} and request == self.expected, "request-mismatch")
        return request["stack"] + ":" + phase

    def validate_time(self, value):
        try:
            _require(isinstance(value, str) and datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None,
                     "reservation-time-invalid")
        except (TypeError, ValueError):
            raise SessionOperationFailure("reservation-time-invalid") from None


class SessionOperations:
    """Use a captured source plan; its not-admitted status never becomes approval."""

    def __init__(self, plan, records, *, provider, preflight):
        try:
            _require(isinstance(plan, dict) and plan.get("schema") == "deploy/aws-session-source-plan/v1"
                     and plan.get("execution_status") == "not-admitted", "source-plan-invalid")
            binding = asdict(plan["binding"])
            intent, policy = binding["intent"], binding["intent"]["lifecycle"]
            _require(policy["mode"] == "temporary" and policy["data_retention"] == "discard"
                     and policy["explicit"] is True, "temporary-discard-required")
            _require(type(intent["starts_at"]) is int and type(intent["expires_at"]) is int
                     and 0 <= intent["starts_at"] < intent["expires_at"], "lifetime-invalid")
            _require(isinstance(intent["session_id"], str) and re.fullmatch(r"[a-f0-9]{32}", intent["session_id"]) is not None,
                     "identity-invalid")
            # Upstream binds sorted captured source rows using this serialization.
            source_digest = hashlib.sha256(json.dumps(binding["source_inputs"], separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
            _require(source_digest == binding["source_inputs_sha256"], "source-binding-mismatch")
            source = plan["source_configuration"]
            _require(source["target"] == intent["target"] and source["scope"] == intent["scope"], "source-target-mismatch")
            prefix = "s-" + intent["session_id"][:19]
            _require(plan["resource_name_prefix"] == prefix and prefix != source["target"], "instance-prefix-invalid")
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
            self.records, self._provider, self._preflight = records, provider, preflight
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
        try:
            result = self._preflight(self._context(action, request, reservation, preparation, arguments))
        except Exception:
            raise SessionOperationFailure("preflight-unconfirmed") from None
        _require(result is None, "preflight-unconfirmed")

    def initialize(self):
        self._admit("initialize")
        return self.records.initialize()

    def seal(self):
        self._admit("seal")
        return self.records.seal()

    def _operation(self, kind, stack, template_reference, parameters):
        _require(isinstance(kind, str) and kind in {"creation", "activation", "prepare-discard"}, "kind-unsupported")
        _require(isinstance(stack, str) and stack in self._stacks and isinstance(template_reference, str)
                 and template_reference in self._templates, "instance-selection-invalid")
        _require((stack, template_reference) in self._pairs, "template-stack-mismatch")
        _require(kind != "activation" or template_reference in self._activation_templates, "activation-selection-invalid")
        templates, selections = ((self._activation_templates, self._activation_controls) if kind == "activation"
                                 else (self._discard_templates, self._discard_controls) if kind == "prepare-discard"
                                 else (self._templates, self._controls))
        template = templates[template_reference]
        try:
            _require(isinstance(template, str) and len(template.encode()) <= 51200, "template-invalid")
            parsed = json.loads(template)
            _require(isinstance(parsed, dict) and RESERVATIONS.canonical(parsed).decode() == template, "template-invalid")
            values = CHANGE_SETS.parameter_values(parameters)
            _require(values is not None and all(set(row) == {"ParameterKey", "ParameterValue"} for row in parameters), "parameters-invalid")
            controls = dict(selections[template_reference])
            _require(all(values.get(key) == value for key, value in controls.items()), "instance-controls-mismatch")
            name = stack + {"creation": "-session-create", "activation": "-session-activate", "prepare-discard": "-session-discard"}[kind]
            _require(len(name) <= 128, "change-set-name-invalid")
            arguments = {"StackName": stack, "ChangeSetName": name,
                         "ChangeSetType": "CREATE" if kind == "creation" else "UPDATE",
                         "TemplateBody": template, "Parameters": deepcopy(parameters), "Capabilities": ["CAPABILITY_NAMED_IAM"]}
            request = {"kind": kind, "stack": stack, "change_set": name,
                       "source_plan_sha256": self._plan_sha256, "arguments_sha256": _digest(arguments),
                       "template_reference": template_reference}
            return request, arguments
        except SessionOperationFailure:
            raise
        except (TypeError, ValueError, KeyError):
            raise SessionOperationFailure("operation-inputs-invalid") from None

    def _run(self, phase, kind, *, stack, template_reference, parameters, observe):
        _require(callable(observe), "observer-required")
        request, arguments = self._operation(kind, stack, template_reference, parameters)
        operation_arguments = deepcopy(arguments)
        store = _Reservations(self.records.storage(kind), request)
        preparation = None
        if phase == "execute":
            preparation = store.read("prepare", request)
            _require(preparation is not None, "preparation-required")
            arguments = {"StackName": stack, "ChangeSetName": request["change_set"]}

        def observed(reservation):
            try:
                value = observe(self._context(kind + "-" + phase, request, reservation, preparation, operation_arguments))
            except Exception:
                raise SessionOperationFailure("observation-unavailable") from None
            _require(isinstance(value, dict), "observation-unavailable")
            return value

        try:
            operation = CHANGE_SETS.prepare if phase == "prepare" else CHANGE_SETS.execute
            return operation(self._provider, store, phase=phase, request=request, arguments=arguments,
                             precondition=lambda reservation: self._admit(kind + "-" + phase, request, reservation, preparation, operation_arguments),
                             observe=observed, passthrough=(SessionOperationFailure,))
        except CHANGE_SETS.ChangeSetFailure as failure:
            reason = failure.code if failure.code in {"create-change-set-submission-uncertain", "execute-change-set-submission-uncertain"} else "submission-uncertain"
            cause = failure.__cause__
            if isinstance(cause, RECORDS.CLI.CliFailure) and cause.code in RECORDS.CLI_FAILURE_CODES:
                reason += ":" + cause.code
            raise SessionOperationFailure(reason) from None

    def prepare(self, kind, **inputs):
        _require(set(inputs) == {"stack", "template_reference", "parameters", "observe"}, "operation-inputs-invalid")
        return self._run("prepare", kind, **inputs)

    def execute(self, kind, **inputs):
        _require(set(inputs) == {"stack", "template_reference", "parameters", "observe"}, "operation-inputs-invalid")
        return self._run("execute", kind, **inputs)
