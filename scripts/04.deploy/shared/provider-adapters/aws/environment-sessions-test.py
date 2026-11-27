#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.aws.environment-sessions
#   version: 1
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.environment-lifecycle
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove real session admission and shared change-set handoffs through disposable controlled S3 and CloudFormation subprocesses.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.aws.runtime-alignment
#     path: scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/runtime-alignment/smoke-test.sh
from copy import deepcopy
from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[5]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OWNER = load("tested_environment_sessions", Path(__file__).with_name("environment_sessions.py"))

# This is the only executable named aws on the child's PATH. No real provider
# process, network, credentials, installation or shell delegation is available.
FAKE = r'''
import json, os, pathlib, sys
args=sys.argv[1:]; service,operation=args[:2]
path=pathlib.Path(os.environ['SESSION_FIXTURE_STATE']); state=json.loads(path.read_text())
state['calls'].append([service,operation])
def option(name): return args[args.index(name)+1]
def finish(value=None,error=None):
 path.write_text(json.dumps(state))
 if error:
  print('An error occurred ('+error+') when calling the Fixture operation: private-canary',file=sys.stderr);sys.exit(1)
 print(json.dumps(value));sys.exit(0)
def lost():
 path.write_text(json.dumps(state));print('private-canary-lost-response');sys.exit(0)
def metadata(raw):
 return {'ContentLength':len(raw),'ContentRange':'bytes 0-'+str(len(raw)-1)+'/'+str(len(raw)),
         'ETag':'"etag-'+str(state['version'])+'"','VersionId':'version-'+str(state['version'])}
if service=='s3api':
 assert option('--expected-bucket-owner')==state['account']
 assert option('--profile')=='fixture' and option('--region')==state['region']
 assert os.environ['AWS_MAX_ATTEMPTS']=='1' and os.environ['AWS_PAGER']==''
 assert os.environ['AWS_IGNORE_CONFIGURED_ENDPOINT_URLS']=='true'
 fault=state.get('fault')
 if operation=='get-object':
  assert option('--range')=='bytes=0-65536'
  if fault in ('AccessDenied','ExpiredToken','NoSuchBucket','Unknown404'):finish(error=fault)
  if state['raw'] is None:finish(error='NoSuchKey')
  raw=state['raw'].encode(); meta=metadata(raw)
  if fault=='missing-version':meta.pop('VersionId')
  if fault=='null-version':meta['VersionId']='null'
  if fault=='missing-etag':meta.pop('ETag')
  if fault=='partial-range':meta['ContentRange']='bytes 0-'+str(len(raw)-1)+'/'+str(len(raw)+1)
  if fault=='wrong-length':meta['ContentLength']=0
  output=pathlib.Path(args[-1]);assert output.stat().st_mode&0o777==0o600
  assert output.parent.stat().st_mode&0o777==0o700
  output.write_bytes(raw[:65537]);finish(meta)
 if operation=='put-object':
  body=pathlib.Path(option('--body'));assert body.stat().st_mode&0o777==0o600
  assert body.parent.stat().st_mode&0o777==0o700
  raw=body.read_text();json.loads(raw)
  if '--if-none-match' in args:
   assert option('--if-none-match')=='*'
   if state['raw'] is not None:finish(error='PreconditionFailed')
  else:
   assert option('--if-match')=='"etag-'+str(state['version'])+'"'
  if fault=='conflict-seal':
   document=json.loads(state['raw']);document['state']='sealed';state['raw']=json.dumps(document)
   state['version']+=1;state['history'].append(state['raw']);state['fault']=None
   finish(error='PreconditionFailed')
  if fault in ('PreconditionFailed','ConditionalRequestConflict'):finish(error=fault)
  state['raw']=raw;state['version']+=1;state['history'].append(raw)
  if fault=='lost-put':state['fault']=None;lost()
  meta=metadata(raw.encode())
  if fault=='readback-version':meta['VersionId']='unconfirmed-version';state['fault']=None
  if fault=='missing-put-version':meta.pop('VersionId');state['fault']=None
  finish(meta)
 raise AssertionError(operation)
assert service=='cloudformation'
submitted=json.loads(option('--cli-input-json'));changes=state.setdefault('changes',{})
name=submitted.get('ChangeSetName')
if operation=='describe-change-set':
 if name not in changes:finish(error='ChangeSetNotFoundException')
 finish(changes[name])
if operation=='describe-stack-events':
 change=next((value for value in reversed(list(changes.values())) if value['StackId']==submitted['StackName']),{})
 finish({'StackEvents':[{'PhysicalResourceId':change.get('StackId'),
                         'ClientRequestToken':change.get('execution_token'),'ResourceStatus':'CREATE_COMPLETE'}]})
state['submissions'].append([operation,submitted])
if state.get('fault') in ('cf-AccessDenied','cf-ExpiredToken'):
 fault=state['fault'][3:];state['fault']=None;finish(error=fault)
if operation=='create-change-set':
 changes[name]={'ChangeSetName':name,'StackId':submitted['StackName'],'Description':submitted['Description'],
                'Status':'CREATE_COMPLETE','ExecutionStatus':'AVAILABLE'}
if operation=='execute-change-set':
 changes[name]['execution_token']=submitted['ClientRequestToken'];changes[name]['ExecutionStatus']='EXECUTE_COMPLETE'
if state.get('fault')=='lost-'+operation:state['fault']=None;lost()
assert operation in ('create-change-set','execute-change-set')
finish({'Id':'fixture-change-set'})
'''


class SessionHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preparation = load("tested_session_preparation", ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/preparation-inputs.py")
        document = {"schema": "deploy/environment-session-intent/v1", "target": "kanbien-core-platform",
                    "scope": "core-server-persistence", "session_id": "a" * 32, "starts_at": 1000, "expires_at": 8200,
                    "environment_lifecycle": {"mode": "temporary", "data_retention": "discard", "max_duration_seconds": 7200}}
        cls.session_document = deepcopy(document)
        cls.plan = cls.preparation.load_session_plan(ROOT, document["target"], document["scope"], document, 1000, 7200)
        document = {**document, "scope": "entity-smoke"}
        cls.entity_plan = cls.preparation.load_session_plan(ROOT, document["target"], document["scope"], document, 1000, 7200)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="environment-session-test-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.state_path = self.root / "state.json"
        source = self.plan["source_configuration"]
        self.write({"raw": None, "version": 0, "history": [], "calls": [], "submissions": [],
                    "account": source["account"], "region": source["region"], "fault": None})
        fake = self.root / "aws"
        fake.write_text("#!" + sys.executable + "\n" + FAKE)
        fake.chmod(0o700)
        self.environment = {"PATH": str(self.root), "SESSION_FIXTURE_STATE": str(self.state_path),
                            "PYTHONDONTWRITEBYTECODE": "1"}
        self.now = 1000
        self.guards, self.preflights, self.observations = [], [], []
        self.select_plan(self.plan)

    def select_plan(self, plan):
        self.plan = plan
        source = plan["source_configuration"]
        binding = self.plan["binding"]
        self.binding = {key: getattr(binding.intent, key) for key in ("target", "scope", "session_id", "starts_at", "expires_at")}
        self.binding["source_inputs_sha256"] = binding.source_inputs_sha256
        self.records = self.make_records()
        self.adapter = OWNER.SessionOperations(self.plan, self.records, provider=self.provider, preflight=self.preflight)
        self.stack = dict(self.plan["stack_names"])[binding.intent.scope]
        self.reference = source["template"]
        self.inputs = {"stack": self.stack, "template_reference": self.reference,
                       "parameters": [{"ParameterKey": key, "ParameterValue": value}
                                      for key, value in dict(self.plan["creation_parameters"])[self.reference]],
                       "observe": self.observe}
        self.active_inputs = {**self.inputs, "parameters": [{"ParameterKey": key, "ParameterValue": value}
                              for key, value in dict(self.plan["activation_parameters"])[self.reference]]}

    def source_variant(self, change):
        copied = self.root / "source"
        for reference in self.plan["references"]:
            destination = copied / reference
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / reference).read_bytes())
        target = self.session_document["target"]
        base = "infra/04.deploy/03.product/targets/" + target
        reference = base + "/00-target/target-profile.yml"
        profile = self.preparation.read_document(copied, reference)
        change(profile, copied / base)
        (copied / reference).write_text(json.dumps(profile))
        document = deepcopy(self.session_document)
        return self.preparation.load_session_plan(copied, target, document["scope"], document, 1000, 7200)

    def read(self):
        return json.loads(self.state_path.read_text())

    def write(self, state):
        self.state_path.write_text(json.dumps(state))

    def fault(self, value):
        state = self.read(); state["fault"] = value; self.write(state)

    def make_records(self, **overrides):
        values = {"bucket": "session-fixture", "key": "targets/fixture.json",
                  "account": self.plan["source_configuration"]["account"],
                  "region": self.plan["source_configuration"]["region"], "profile": "fixture",
                  "environment": self.environment, "binding": self.binding, "guard": self.guard, "clock": lambda: self.now}
        return OWNER.RECORDS.SessionRecords(**{**values, **overrides})

    def guard(self, action, binding):
        self.assertEqual(binding, self.binding)
        self.guards.append(action)

    def preflight(self, context):
        self.assertEqual(context["binding"], self.binding)
        self.assertEqual(context["source_plan"]["source_configuration"]["target"], "kanbien-core-platform")
        self.assertEqual(context["source_plan"]["execution_status"], "not-admitted")
        self.preflights.append(context)

    def provider(self, service, operation, **arguments):
        return OWNER.RECORDS.CLI.invoke_json(
            ["aws", service, operation, "--cli-input-json", json.dumps(arguments)],
            timeout=5, empty_body="reject", object_only=True, environment=self.environment)

    def observe(self, context):
        self.observations.append(context)
        request = context["request"]
        arguments = {"StackName": request["stack"], "ChangeSetName": request["change_set"]}
        try:
            change = self.provider("cloudformation", "describe-change-set", **arguments)
        except OWNER.RECORDS.CLI.CliFailure as failure:
            if failure.code == "aws-resource-missing":
                return {"status": "absence-unconfirmed", "operation_id": context["reservation"]["operation_id"]}
            raise
        prepared = context["preparation"] or context["reservation"]
        self.assertEqual(change["Description"], prepared["operation_id"])
        if context["action"].endswith("-execute"):
            events = self.provider("cloudformation", "describe-stack-events", StackName=request["stack"])
            self.assertEqual(len(OWNER.CHANGE_SETS.execution_events(events, context["reservation"]["operation_id"], request["stack"])), 1)
        return {"status": "fixture-observed", "operation_id": context["reservation"]["operation_id"]}

    def failed(self, callback, fragment):
        with self.assertRaises((OWNER.SessionOperationFailure, OWNER.RECORDS.SessionRecordFailure)) as raised:
            callback()
        self.assertIn(fragment, raised.exception.code)
        self.assertNotIn("canary", str(raised.exception))
        return raised.exception.code

    def test_connected_creation_uses_shared_tokens_and_resumed_observation(self):
        original = deepcopy(self.plan)
        self.adapter.initialize()
        prepared = self.adapter.prepare("creation", **self.inputs)
        executed = self.adapter.execute("creation", **self.inputs)
        self.assertEqual(self.adapter.prepare("creation", **self.inputs), prepared)
        self.assertEqual(self.adapter.execute("creation", **self.inputs), executed)
        submissions = self.read()["submissions"]
        self.assertEqual([row[0] for row in submissions], ["create-change-set", "execute-change-set"])
        self.assertEqual(submissions[0][1]["ClientToken"], prepared["operation_id"])
        self.assertEqual(submissions[0][1]["Description"], prepared["operation_id"])
        self.assertEqual(submissions[1][1]["ClientRequestToken"], executed["operation_id"])
        self.assertEqual(submissions[0][1]["ChangeSetType"], "CREATE")
        self.assertEqual(self.preflights[-1]["preparation"]["operation_id"], prepared["operation_id"])
        self.assertEqual(self.preflights[-1]["operation_arguments"], {key: value for key, value in submissions[0][1].items()
                                                                    if key not in {"ClientToken", "Description"}})
        self.assertEqual(len(json.loads(self.read()["raw"])["operations"]), 2)
        self.assertEqual(self.plan, original)

    def test_connected_prerequisite_creation_preserves_all_captured_output_bindings(self):
        self.adapter.initialize()
        stacks, pairs = dict(self.plan["stack_names"]), dict(self.plan["stack_templates"])
        prerequisites = {stacks[name] for name in self.plan["prerequisite_components"]}
        self.assertTrue(prerequisites)
        self.assertEqual(set(self.plan["stack_order"][:len(prerequisites)]), prerequisites)
        self.assertEqual(self.plan["stack_order"][len(prerequisites)], stacks["foundation"])
        sources = self.plan["stack_parameter_sources"]
        self.assertEqual({producer for _, _, producer, _ in sources}, prerequisites)
        for stack in self.plan["stack_order"]:
            reference = pairs[stack]
            inputs = {"stack": stack, "template_reference": reference, "observe": self.observe,
                      "parameters": [{"ParameterKey": key, "ParameterValue": value}
                                     for key, value in dict(self.plan["creation_parameters"])[reference]]}
            prepared = self.adapter.prepare("creation", **inputs)
            executed = self.adapter.execute("creation", **inputs)
            submitted, execution = self.read()["submissions"][-2:]
            self.assertEqual(submitted[1]["StackName"], stack)
            self.assertEqual(submitted[1]["ChangeSetType"], "CREATE")
            self.assertEqual(submitted[1]["TemplateBody"], dict(self.plan["projected_templates"])[reference])
            self.assertEqual(submitted[1]["Parameters"], inputs["parameters"])
            self.assertEqual(submitted[1]["ClientToken"], prepared["operation_id"])
            self.assertEqual(execution[1]["ClientRequestToken"], executed["operation_id"])
            self.assertEqual(self.preflights[-1]["source_plan"]["stack_parameter_sources"], sources)
            self.assertEqual(self.preflights[-1]["source_plan"]["stack_order"], self.plan["stack_order"])
        foundation_controls = dict(dict(self.plan["creation_parameters"])[pairs[stacks["foundation"]]])
        self.assertTrue(all(parameter not in foundation_controls for _, parameter, _, _ in sources))
        # The fixture submits captured controls only; it cannot prove live output resolution.
        for stack in prerequisites:
            self.assertNotIn(pairs[stack], dict(self.plan["activation_templates"]))

    def test_actual_reader_absent_prerequisites_preserves_optional_adapter_support(self):
        def omit(profile, _):
            profile["provider"]["foundation"].pop("instance_prerequisites")
        plan = self.source_variant(omit)
        self.assertEqual(plan["prerequisite_components"], ())
        self.assertEqual(plan["stack_parameter_sources"], ())
        self.assertEqual(set(dict(plan["stack_names"])), {"foundation", *plan["binding"].scopes})
        self.select_plan(plan)
        self.adapter.initialize()
        self.adapter.prepare("creation", **self.inputs)
        self.assertEqual(self.read()["submissions"][0][1]["TemplateBody"], dict(plan["projected_templates"])[self.reference])

    def test_actual_reader_renamed_prerequisite_and_outputs_connect_without_name_branches(self):
        def rename(profile, base):
            declared = profile["provider"]["foundation"]["instance_prerequisites"]
            self.assertEqual(len(declared), 1)
            row = declared.pop(next(iter(declared)))
            row["stack"] = self.session_document["target"] + "-isolated-supplier"
            template_path = base / row["template"]
            template = self.preparation.CF.template(template_path.read_text())
            outputs = {}
            for parameter, output in row["foundation_parameters"].items():
                renamed = "Supplied" + output
                template["Outputs"][renamed] = template["Outputs"].pop(output)
                outputs[parameter] = renamed
            row["foundation_parameters"] = outputs
            declared["isolated-supplier"] = row
            template_path.write_text(json.dumps(template))
        plan = self.source_variant(rename)
        self.assertEqual(plan["prerequisite_components"], ("isolated-supplier",))
        supplier = dict(plan["stack_names"])["isolated-supplier"]
        self.assertTrue(supplier.endswith("-isolated-supplier"))
        self.assertTrue(all(producer == supplier and output.startswith("Supplied")
                            for _, _, producer, output in plan["stack_parameter_sources"]))
        self.assert_connected_discard(plan)

    def test_prerequisite_components_and_output_rows_fail_closed_before_remote_use(self):
        prerequisites, sources = self.plan["prerequisite_components"], self.plan["stack_parameter_sources"]
        consumer, parameter, producer, output = sources[0]
        variants = [("prerequisite_components", value) for value in
                    (list(prerequisites), prerequisites + prerequisites, ("",), (17,), ("foundation",), (self.binding["scope"],))]
        variants.extend(("stack_parameter_sources", value) for value in
                        ((), list(sources), sources + sources, (list(sources[0]), *sources[1:]),
                         ((consumer, parameter, producer), *sources[1:]),
                         ((consumer, parameter, producer, 17), *sources[1:]),
                         ((*sources[0][:3], ""), *sources[1:]),
                         ((self.stack, parameter, producer, output), *sources[1:]),
                         ((consumer, "private-canary", producer, output), *sources[1:]),
                         ((consumer, parameter, "private-canary", output), *sources[1:]),
                         ((consumer, parameter, consumer, output), *sources[1:]),
                         ((consumer, parameter, producer, "private-canary"), *sources[1:]),
                         (*sources, (consumer, parameter, producer, "AnotherOutput"))))
        for reserved in dict(dict(self.plan["creation_parameters"])[self.plan["source_configuration"]["foundation_template"]]):
            variants.append(("stack_parameter_sources", ((consumer, reserved, producer, output), *sources[1:])))
        for key, value in variants:
            with self.subTest(key=key):
                self.failed(lambda: OWNER.SessionOperations({**self.plan, key: value}, self.records,
                            provider=self.provider, preflight=self.preflight), "prerequisite-bindings-invalid")
        pairs = dict(self.plan["stack_templates"])
        for stack, section, name in ((consumer, "Parameters", parameter), (producer, "Outputs", output)):
            for value in (None, "private-canary", {"Description": "no-value"}, {"Value": None}):
                if section == "Parameters" and isinstance(value, dict):
                    continue  # Template schema validity remains with the captured-source reader.
                reference = pairs[stack]
                template = json.loads(dict(self.plan["projected_templates"])[reference])
                template[section][name] = value
                changed = tuple((key, OWNER.RESERVATIONS.canonical(template).decode() if key == reference else body)
                                for key, body in self.plan["projected_templates"])
                self.failed(lambda: OWNER.SessionOperations({**self.plan, "projected_templates": changed}, self.records,
                            provider=self.provider, preflight=self.preflight), "prerequisite-bindings-invalid")
        self.failed(lambda: OWNER.SessionOperations({**self.plan, "prerequisite_components": ("private-canary",)}, self.records,
                    provider=self.provider, preflight=self.preflight), "instance-stacks-invalid")
        for missing in ("prerequisite_components", "stack_parameter_sources"):
            plan = {key: value for key, value in self.plan.items() if key != missing}
            self.failed(lambda: OWNER.SessionOperations(plan, self.records,
                        provider=self.provider, preflight=self.preflight), "source-plan-invalid")
        self.assertEqual(self.read()["calls"], [])

    def assert_connected_activation(self, plan):
        self.select_plan(plan)
        self.adapter.initialize()
        created = self.adapter.prepare("creation", **self.inputs)
        self.adapter.execute("creation", **self.inputs)
        expected = deepcopy(json.loads(dict(plan["projected_templates"])[self.reference]))
        for row in expected["Metadata"]["CreationControls"].values():
            if row["kind"] == "desired-count":
                for name in row["resources"]:
                    self.assertEqual(expected["Resources"][name]["Properties"]["DesiredCount"], 0)
                    expected["Resources"][name]["Properties"]["DesiredCount"] = row["active"]
        captured = dict(plan["activation_templates"])[self.reference]
        self.assertEqual(json.loads(captured), expected)
        def checked_fixture(context):
            # Fixture-only validation of the handoff, not live readiness proof.
            self.preflight(context)
            self.assertEqual(context["operation_arguments"]["TemplateBody"], captured)
            self.assertEqual(context["operation_arguments"]["Parameters"], self.active_inputs["parameters"])
            self.assertEqual(OWNER._digest(context["operation_arguments"]), context["request"]["arguments_sha256"])
            context["operation_arguments"]["TemplateBody"] = "{}"
            context["operation_arguments"]["Parameters"].clear()
            context["source_plan"]["resource_name_prefix"] = "production"
        adapter = OWNER.SessionOperations(plan, self.records, provider=self.provider, preflight=checked_fixture)
        prepared = adapter.prepare("activation", **self.active_inputs)
        executed = adapter.execute("activation", **self.active_inputs)
        self.assertNotEqual(created["operation_id"], prepared["operation_id"])
        self.assertEqual(adapter.prepare("activation", **self.active_inputs), prepared)
        self.assertEqual(adapter.execute("activation", **self.active_inputs), executed)
        submissions = self.read()["submissions"]
        self.assertEqual([row[0] for row in submissions], ["create-change-set", "execute-change-set"] * 2)
        self.assertEqual(submissions[2][1]["ChangeSetType"], "UPDATE")
        self.assertEqual(submissions[2][1]["TemplateBody"], captured)
        self.assertEqual(submissions[2][1]["Parameters"], self.active_inputs["parameters"])
        self.assertEqual(submissions[2][1]["StackName"], self.stack)
        self.assertEqual(submissions[2][1]["ClientToken"], prepared["operation_id"])
        self.assertEqual(submissions[3][1]["ClientRequestToken"], executed["operation_id"])
        operations = json.loads(self.read()["raw"])["operations"]
        self.assertEqual(set(operations), {kind + ":" + self.stack + ":" + phase
                                         for kind in ("creation", "activation") for phase in ("prepare", "execute")})
        self.assertIn("reserve-activation", self.guards)
        self.assertEqual(self.preflights[-1]["preparation"]["operation_id"], prepared["operation_id"])

    def test_connected_persistence_activation_changes_only_declared_counts(self):
        self.assert_connected_activation(self.plan)

    def test_connected_entity_activation_preserves_zero_production_default(self):
        self.assert_connected_activation(self.entity_plan)
        template = json.loads(dict(self.entity_plan["activation_templates"])[self.reference])
        self.assertEqual(template["Parameters"]["ServerDesiredCount"]["Default"], 0)

    def test_entity_activation_rejects_stopped_and_arbitrary_service_counts(self):
        self.select_plan(self.entity_plan)
        for count in ("0", "2", "private-canary"):
            with self.subTest(count=count):
                parameters = deepcopy(self.active_inputs["parameters"])
                next(row for row in parameters if row["ParameterKey"] == "ServerDesiredCount")["ParameterValue"] = count
                self.failed(lambda: self.adapter.prepare("activation", **{**self.active_inputs, "parameters": parameters}),
                            "instance-controls-mismatch")
        self.assertEqual(self.read()["calls"], [])

    def test_activation_rejects_wrong_counts_and_foundation_before_remote_use(self):
        foundation = self.plan["source_configuration"]["foundation_template"]
        variants = [({"parameters": self.inputs["parameters"]}, "instance-controls-mismatch"),
                    ({"stack": dict(self.plan["stack_names"])["foundation"], "template_reference": foundation}, "activation-selection-invalid"),
                    ({"template_reference": foundation}, "template-stack-mismatch")]
        for key, replacement in (("ResourceNamePrefix", "production"), ("IncludeLegacyPasswordSecrets", "true")):
            parameters = deepcopy(self.active_inputs["parameters"])
            next(row for row in parameters if row["ParameterKey"] == key)["ParameterValue"] = replacement
            variants.append(({"parameters": parameters}, "instance-controls-mismatch"))
        for mutation, reason in variants:
            with self.subTest(reason=reason):
                self.failed(lambda: self.adapter.prepare("activation", **{**self.active_inputs, **mutation}), reason)
        self.assertEqual(self.read()["calls"], [])

    def test_activation_bindings_reject_missing_duplicate_unowned_and_changed_controls(self):
        templates = self.plan["activation_templates"]
        foundation = self.plan["source_configuration"]["foundation_template"]
        changed = dict(dict(self.plan["activation_parameters"])[self.reference])
        changed["ResourceNamePrefix"] = "production"
        variants = ({"activation_templates": ()}, {"activation_templates": templates + templates},
                    {"activation_templates": (*templates, (foundation, "{}"))},
                    {"activation_parameters": ((self.reference, tuple(changed.items())),)})
        for change in variants:
            with self.subTest(change=next(iter(change))):
                self.failed(lambda: OWNER.SessionOperations({**self.plan, **change}, self.records,
                            provider=self.provider, preflight=self.preflight), "activation-bindings-invalid")
        binding = replace(self.plan["binding"], source_inputs_sha256="f" * 64)
        self.failed(lambda: OWNER.SessionOperations({**self.plan, "binding": binding}, self.records,
                    provider=self.provider, preflight=self.preflight), "source-binding-mismatch")
        self.assertEqual(self.read()["calls"], [])

    def test_expired_or_sealed_activation_only_observes_retained_preparation(self):
        self.adapter.initialize()
        prepared = self.adapter.prepare("activation", **self.active_inputs)
        self.now = 8200
        self.assertEqual(self.adapter.prepare("activation", **self.active_inputs), prepared)
        self.failed(lambda: self.adapter.execute("activation", **self.active_inputs), "admission-closed")
        self.now = 1000
        self.adapter.seal()
        self.assertEqual(self.adapter.prepare("activation", **self.active_inputs), prepared)
        self.failed(lambda: self.adapter.execute("activation", **self.active_inputs), "admission-closed")
        self.assertEqual(len(self.read()["submissions"]), 1)
        self.assertEqual(len(json.loads(self.read()["raw"])["operations"]), 1)

    def test_activation_lost_responses_never_replay_even_after_expiry(self):
        self.adapter.initialize()
        for phase, operation in (("prepare", "create-change-set"), ("execute", "execute-change-set")):
            with self.subTest(phase=phase):
                self.fault("lost-" + operation)
                call = lambda: getattr(self.adapter, phase)("activation", **self.active_inputs)
                self.assertEqual(self.failed(call, "submission-uncertain"),
                                 "environment-session-operation-" + operation + "-submission-uncertain:aws-response-invalid")
                self.now = 8200
                self.assertEqual(call()["status"], "fixture-observed")
                self.now = 1000
        self.assertEqual([row[0] for row in self.read()["submissions"]], ["create-change-set", "execute-change-set"])

    def test_activation_unconfirmed_creation_or_readiness_never_submits(self):
        self.adapter.initialize()
        def unconfirmed(context):
            self.assertEqual(context["action"], "activation-prepare")
            self.assertEqual(context["operation_arguments"]["ChangeSetType"], "UPDATE")
            self.assertEqual(context["source_plan"]["stack_dependencies"], self.plan["stack_dependencies"])
            raise ValueError("private-canary-creation-or-readiness-unconfirmed")
        adapter = OWNER.SessionOperations(self.plan, self.records, provider=self.provider, preflight=unconfirmed)
        self.failed(lambda: adapter.prepare("activation", **self.active_inputs), "preflight-unconfirmed")
        self.assertEqual(self.adapter.prepare("activation", **self.active_inputs)["status"], "absence-unconfirmed")
        self.assertEqual(self.read()["submissions"], [])
        self.assertEqual(len(json.loads(self.read()["raw"])["operations"]), 1)

    def test_seal_preserves_creation_and_admits_cleanup_preparation_only(self):
        self.adapter.initialize()
        created = self.adapter.prepare("creation", **self.inputs)
        prior = json.loads(self.read()["raw"])["operations"]
        self.adapter.seal()
        self.assertEqual(self.adapter.prepare("creation", **self.inputs), created)
        self.failed(lambda: self.adapter.execute("creation", **self.inputs), "admission-closed")
        self.adapter.prepare("prepare-discard", **self.inputs)
        self.adapter.execute("prepare-discard", **self.inputs)
        document = json.loads(self.read()["raw"])
        self.assertEqual(document["state"], "sealed")
        self.assertTrue(all(document["operations"][key] == value for key, value in prior.items()))
        self.assertEqual(self.read()["submissions"][1][1]["ChangeSetType"], "UPDATE")
        self.assertEqual(len(self.read()["history"]), 5)
        self.assertFalse(hasattr(self.adapter, "delete"))
        self.assertFalse(hasattr(self.records, "complete"))

    def test_absent_admission_open_cleanup_and_missing_preparation_block(self):
        self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "record-unavailable")
        self.adapter.initialize()
        self.failed(lambda: self.adapter.prepare("prepare-discard", **self.inputs), "admission-open")
        self.failed(lambda: self.adapter.execute("creation", **self.inputs), "preparation-required")
        self.assertEqual(self.read()["submissions"], [])

    def test_expiry_blocks_new_work_but_preserves_retained_observation(self):
        self.adapter.initialize()
        prepared = self.adapter.prepare("creation", **self.inputs)
        self.now = 8200
        self.assertEqual(self.adapter.prepare("creation", **self.inputs), prepared)
        self.failed(lambda: self.adapter.execute("creation", **self.inputs), "admission-closed")
        self.adapter.seal()
        self.adapter.prepare("prepare-discard", **self.inputs)
        self.assertEqual(len(self.read()["submissions"]), 2)

    def test_guard_boolean_or_exception_is_not_evidence(self):
        for guard in (lambda *_: True, lambda *_: (_ for _ in ()).throw(ValueError("private-canary"))):
            with self.subTest(guard=guard):
                records = self.make_records(guard=guard)
                self.failed(records.initialize, "protection-unconfirmed")
        self.assertEqual(self.read()["calls"], [])

    def test_cross_stack_template_pair_is_rejected_before_remote_use(self):
        inputs = {**self.inputs, "template_reference": self.plan["source_configuration"]["foundation_template"]}
        self.failed(lambda: self.adapter.prepare("creation", **inputs), "template-stack-mismatch")
        self.assertEqual(self.read()["calls"], [])

    def assert_connected_discard(self, plan):
        self.select_plan(plan)
        original = deepcopy(plan)
        templates, controls = dict(plan["discard_templates"]), dict(plan["discard_parameters"])
        self.assertEqual(controls, dict(plan["creation_parameters"]))
        self.assertEqual(set(templates), set(dict(plan["projected_templates"])))
        databases = 0
        for reference, source in plan["projected_templates"]:
            expected = json.loads(source)
            for resource in expected["Resources"].values():
                if resource["Type"] == "AWS::RDS::DBInstance":
                    databases += 1
                    self.assertEqual(resource["DeletionPolicy"], "Snapshot")
                    self.assertEqual(resource["UpdateReplacePolicy"], "Snapshot")
                    self.assertIs(resource["Properties"]["DeletionProtection"], True)
                    self.assertNotIn("DeleteAutomatedBackups", resource["Properties"])
                    resource["DeletionPolicy"] = resource["UpdateReplacePolicy"] = "Delete"
                    resource["Properties"]["DeletionProtection"] = False
                    resource["Properties"]["DeleteAutomatedBackups"] = True
            self.assertEqual(json.loads(templates[reference]), expected)
        self.assertEqual(databases, 1)
        self.adapter.initialize()
        self.failed(lambda: self.adapter.prepare("prepare-discard", **self.inputs), "admission-open")
        self.adapter.seal()
        self.now = 8200
        def checked_fixture(context):
            # Exact captured source handoff, not physical ownership/deletion proof.
            self.preflight(context)
            reference = context["request"]["template_reference"]
            self.assertEqual(context["operation_arguments"]["TemplateBody"], templates[reference])
            self.assertEqual(context["operation_arguments"]["Parameters"],
                             [{"ParameterKey": key, "ParameterValue": value} for key, value in controls[reference]])
            self.assertEqual(OWNER._digest(context["operation_arguments"]), context["request"]["arguments_sha256"])
            context["operation_arguments"]["TemplateBody"] = "{}"
            context["operation_arguments"]["Parameters"].clear()
            context["source_plan"]["resource_name_prefix"] = "production"
        adapter = OWNER.SessionOperations(plan, self.records, provider=self.provider, preflight=checked_fixture)
        for stack, reference in plan["stack_templates"]:
            inputs = {"stack": stack, "template_reference": reference, "observe": self.observe,
                      "parameters": [{"ParameterKey": key, "ParameterValue": value} for key, value in controls[reference]]}
            prepared = adapter.prepare("prepare-discard", **inputs)
            executed = adapter.execute("prepare-discard", **inputs)
            before = self.read()
            self.assertEqual(adapter.prepare("prepare-discard", **inputs), prepared)
            self.assertEqual(adapter.execute("prepare-discard", **inputs), executed)
            self.assertEqual(self.read()["history"], before["history"])
            self.assertEqual(self.read()["submissions"], before["submissions"])
            submitted, executed_arguments = self.read()["submissions"][-2:]
            self.assertEqual(submitted[0], "create-change-set")
            self.assertEqual(executed_arguments[0], "execute-change-set")
            self.assertEqual(submitted[1]["ChangeSetType"], "UPDATE")
            self.assertEqual(submitted[1]["TemplateBody"], templates[reference])
            self.assertEqual(submitted[1]["Parameters"], inputs["parameters"])
            self.assertEqual(submitted[1]["StackName"], stack)
            self.assertEqual(submitted[1]["ClientToken"], prepared["operation_id"])
            self.assertEqual(executed_arguments[1]["ClientRequestToken"], executed["operation_id"])
        document = json.loads(self.read()["raw"])
        self.assertEqual(document["state"], "sealed")
        self.assertEqual(set(document["operations"]), {"prepare-discard:" + stack + ":" + phase
                         for stack, _ in plan["stack_templates"] for phase in ("prepare", "execute")})
        self.assertEqual(plan, original)

    def test_connected_persistence_discard_changes_only_four_declared_paths(self):
        self.assert_connected_discard(self.plan)

    def test_connected_entity_discard_includes_captured_dependency_and_foundation(self):
        self.assert_connected_discard(self.entity_plan)

    def test_discard_bindings_reject_incomplete_duplicate_unowned_and_mutable_maps(self):
        templates, parameters = self.plan["discard_templates"], self.plan["discard_parameters"]
        variants = []
        for key, rows in (("discard_templates", templates), ("discard_parameters", parameters)):
            variants.extend(({key: ()}, {key: rows[:-1]}, {key: rows + rows}, {key: list(rows)},
                             {key: (list(rows[0]), *rows[1:])},
                             {key: (*rows, ("private-canary", rows[0][1]))},
                             {key: ((17, rows[0][1]), *rows[1:])}))
        reference, rows = parameters[0]
        variants.extend(({"discard_templates": ((templates[0][0], {}), *templates[1:])},
                         {"discard_parameters": ((reference, list(rows)), *parameters[1:])},
                         {"discard_parameters": ((reference, rows + rows), *parameters[1:])}))
        for change in variants:
            with self.subTest(change=next(iter(change))):
                self.failed(lambda: OWNER.SessionOperations({**self.plan, **change}, self.records,
                            provider=self.provider, preflight=self.preflight), "discard-bindings-invalid")
        for missing in ("discard_templates", "discard_parameters"):
            plan = {key: value for key, value in self.plan.items() if key != missing}
            self.failed(lambda: OWNER.SessionOperations(plan, self.records,
                        provider=self.provider, preflight=self.preflight), "source-plan-invalid")
        self.assertEqual(self.read()["calls"], [])

    def test_discard_rejects_changed_controls_and_crossed_pair_before_remote_use(self):
        controls = dict(dict(self.plan["discard_parameters"])[self.reference])
        counts = json.loads(dict(self.plan["projected_templates"])[self.reference])["Metadata"]["CreationControls"]
        count = next(key for key, row in counts.items() if row["kind"] == "desired-count")
        for key, replacement in ((count, "1"), ("ResourceNamePrefix", "production"), ("IncludeLegacyPasswordSecrets", "true")):
            with self.subTest(key=key):
                changed = {**controls, key: replacement}
                parameters = tuple((reference, tuple(changed.items()) if reference == self.reference else rows)
                                   for reference, rows in self.plan["discard_parameters"])
                self.failed(lambda: OWNER.SessionOperations({**self.plan, "discard_parameters": parameters}, self.records,
                            provider=self.provider, preflight=self.preflight), "discard-bindings-invalid")
                inputs = {**self.inputs, "parameters": [{"ParameterKey": name, "ParameterValue": value} for name, value in changed.items()]}
                self.failed(lambda: self.adapter.prepare("prepare-discard", **inputs), "instance-controls-mismatch")
        self.failed(lambda: self.adapter.prepare("prepare-discard", **{**self.inputs,
                    "template_reference": self.plan["source_configuration"]["foundation_template"]}), "template-stack-mismatch")
        self.assertEqual(self.read()["calls"], [])

    def test_public_operation_inputs_reject_overrides_and_missing_keys_without_disclosure(self):
        for phase in ("prepare", "execute"):
            for kind in ("creation", "activation", "prepare-discard"):
                for key in ("cleanup_template", "TemplateBody", "RoleARN", "private-canary-key"):
                    with self.subTest(phase=phase, kind=kind, key=key):
                        self.assertEqual(self.failed(lambda: getattr(self.adapter, phase)(kind, **{**self.inputs, key: "private-canary"}),
                                         "operation-inputs-invalid"), "environment-session-operation-operation-inputs-invalid")
                for missing in self.inputs:
                    with self.subTest(phase=phase, kind=kind, missing=missing):
                        inputs = {key: value for key, value in self.inputs.items() if key != missing}
                        self.failed(lambda: getattr(self.adapter, phase)(kind, **inputs), "operation-inputs-invalid")
        self.assertEqual(self.read()["calls"], [])

    def test_discard_lost_responses_resume_observation_without_new_reservations(self):
        self.adapter.initialize(); self.adapter.seal()
        for phase, operation in (("prepare", "create-change-set"), ("execute", "execute-change-set")):
            with self.subTest(phase=phase):
                self.fault("lost-" + operation)
                self.assertEqual(self.failed(lambda: getattr(self.adapter, phase)("prepare-discard", **self.inputs), "submission-uncertain"),
                                 "environment-session-operation-" + operation + "-submission-uncertain:aws-response-invalid")
                self.now = 8200
                before = self.read()
                adapter = OWNER.SessionOperations(self.plan, self.make_records(), provider=self.provider, preflight=self.preflight)
                for _ in range(2):
                    self.assertEqual(getattr(adapter, phase)("prepare-discard", **self.inputs)["status"], "fixture-observed")
                self.assertEqual(self.read()["history"], before["history"])
                self.assertEqual(self.read()["submissions"], before["submissions"])
        self.assertEqual([row[0] for row in self.read()["submissions"]], ["create-change-set", "execute-change-set"])

    def test_gate_receives_a_copy_not_mutation_access_to_submission(self):
        self.adapter.initialize()
        def mutate(context):
            context["operation_arguments"]["StackName"] = "production"
            context["operation_arguments"]["TemplateBody"] = "{}"
            context["request"]["stack"] = "production"
            context["source_plan"]["resource_name_prefix"] = "production"
        adapter = OWNER.SessionOperations(self.plan, self.records, provider=self.provider, preflight=mutate)
        adapter.prepare("creation", **self.inputs)
        submitted = self.read()["submissions"][0][1]
        self.assertEqual(submitted["StackName"], self.stack)
        self.assertEqual(submitted["TemplateBody"], dict(self.plan["projected_templates"])[self.reference])

    def test_failed_exact_preflight_retains_intent_without_submission_or_retry(self):
        self.adapter.initialize()
        def deny(context):
            self.assertEqual(context["request"]["stack"], self.stack)
            self.assertEqual(context["request"]["source_plan_sha256"], context["source_plan_sha256"])
            return True
        adapter = OWNER.SessionOperations(self.plan, self.records, provider=self.provider, preflight=deny)
        self.failed(lambda: adapter.prepare("creation", **self.inputs), "preflight-unconfirmed")
        self.adapter.prepare("creation", **self.inputs)
        self.assertEqual(self.read()["submissions"], [])
        self.assertEqual(len(json.loads(self.read()["raw"])["operations"]), 1)

    def test_production_identity_parameter_and_template_overrides_are_rejected(self):
        mutations = [({"stack": self.plan["source_configuration"]["stack"]}, "instance-selection-invalid"),
                     ({"template_reference": "private-canary"}, "instance-selection-invalid"),
                     ({"parameters": []}, "instance-controls-mismatch"),
                     ({"parameters": [{"ParameterKey": "x", "ParameterValue": "a"}] * 2}, "parameters-invalid")]
        for mutation, reason in mutations:
            with self.subTest(reason=reason):
                self.failed(lambda: self.adapter.prepare("creation", **{**self.inputs, **mutation}), reason)
        self.assertEqual(self.read()["calls"], [])

    def test_checked_plan_and_remote_identity_must_match(self):
        for overrides in ({"account": "999999999999"}, {"region": "us-west-2"},
                          {"binding": {**self.binding, "session_id": "b" * 32}}):
            with self.subTest(overrides=overrides):
                self.failed(lambda: OWNER.SessionOperations(self.plan, self.make_records(**overrides),
                                                            provider=self.provider, preflight=self.preflight), "remote-binding-mismatch")
        plan = deepcopy(self.plan)
        plan["binding"] = replace(plan["binding"], intent=replace(plan["binding"].intent,
            lifecycle=replace(plan["binding"].intent.lifecycle, mode="persistent", data_retention="preserve")))
        self.failed(lambda: OWNER.SessionOperations(plan, self.records, provider=self.provider, preflight=self.preflight), "temporary-discard-required")
        self.assertEqual(self.read()["calls"], [])

    def test_foreign_prior_session_never_reopens_or_replaces_history(self):
        self.adapter.initialize()
        prior = self.read()
        records = self.make_records(binding={**self.binding, "session_id": "b" * 32}, guard=lambda *_: None)
        self.failed(records.initialize, "binding-mismatch")
        self.assertEqual(self.read()["raw"], prior["raw"])
        self.assertEqual(self.read()["history"], prior["history"])

    def test_concurrent_seal_wins_without_replayed_admission(self):
        self.adapter.initialize()
        self.fault("conflict-seal")
        self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "record-conflict")
        self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "admission-closed")
        self.assertEqual(self.read()["submissions"], [])
        self.assertEqual(json.loads(self.read()["raw"])["operations"], {})

    def test_lost_put_or_unconfirmed_readback_never_grants_fresh_submission(self):
        for fault in ("lost-put", "readback-version", "missing-put-version"):
            with self.subTest(fault=fault):
                state = self.read(); state.update(raw=None, version=0, history=[], calls=[], submissions=[], fault=None); self.write(state)
                self.adapter.initialize()
                self.fault(fault)
                code = self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "retention-unconfirmed")
                if fault == "lost-put":
                    self.assertEqual(code, "environment-session-operation-session-retention-unconfirmed:aws-response-invalid")
                self.adapter.prepare("creation", **self.inputs)
                self.assertEqual(self.read()["submissions"], [])
                self.assertEqual(sum(call == ["s3api", "put-object"] for call in self.read()["calls"]), 2)

    def test_cloudformation_lost_responses_resume_observation_without_resubmission(self):
        self.adapter.initialize()
        for phase, operation in (("prepare", "create-change-set"), ("execute", "execute-change-set")):
            with self.subTest(phase=phase):
                self.fault("lost-" + operation)
                call = lambda: getattr(self.adapter, phase)("creation", **self.inputs)
                code = self.failed(call, "submission-uncertain")
                self.assertEqual(code, "environment-session-operation-" + operation + "-submission-uncertain:aws-response-invalid")
                call()
        self.assertEqual([row[0] for row in self.read()["submissions"]], ["create-change-set", "execute-change-set"])

    def test_ambiguous_read_denial_or_absent_version_never_means_absence(self):
        self.adapter.initialize()
        for fault in ("AccessDenied", "ExpiredToken", "NoSuchBucket", "Unknown404", "missing-version", "null-version",
                      "missing-etag", "partial-range", "wrong-length"):
            with self.subTest(fault=fault):
                before = len(self.read()["history"])
                self.fault(fault)
                code = self.failed(self.records.initialize, "session-record-")
                if fault in {"AccessDenied", "ExpiredToken", "NoSuchBucket", "Unknown404"}:
                    reason = {"AccessDenied": "aws-access-denied", "ExpiredToken": "aws-credentials-expired"}.get(fault, "aws-command-failed")
                    self.assertEqual(code, "session-record-unavailable:" + reason)
                self.assertEqual(len(self.read()["history"]), before)
        self.assertEqual(self.read()["submissions"], [])

    def test_malformed_duplicate_oversized_and_foreign_records_fail_closed(self):
        self.adapter.initialize()
        valid = self.read()["raw"]
        for raw in ("{", valid[:-1] + ',"state":"open"}', "x" * 65537,
                    valid.replace(self.binding["session_id"], "b" * 32), valid.replace('"open"', '"completed"')):
            with self.subTest(length=len(raw)):
                state = self.read(); state["raw"] = raw; self.write(state)
                self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "session-")
        self.assertEqual(self.read()["submissions"], [])

    def test_changed_intent_and_tampered_retained_reservation_are_not_adopted(self):
        self.adapter.initialize()
        self.adapter.prepare("creation", **self.inputs)
        parameters = [*self.inputs["parameters"], {"ParameterKey": "Additional", "ParameterValue": "private-canary"}]
        self.failed(lambda: self.adapter.prepare("creation", **{**self.inputs, "parameters": parameters}), "reservation-mismatch")
        state = self.read(); document = json.loads(state["raw"])
        next(iter(document["operations"].values()))["operation_id"] = "private-canary"
        state["raw"] = json.dumps(document); self.write(state)
        self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "reservation-mismatch")
        self.assertEqual(len(self.read()["submissions"]), 1)

    def test_cleanup_still_requires_exact_owned_change_preflight(self):
        self.adapter.initialize(); self.adapter.seal()
        def unowned(context):
            self.assertEqual(context["action"], "prepare-discard-prepare")
            raise ValueError("private-canary-unowned")
        adapter = OWNER.SessionOperations(self.plan, self.records, provider=self.provider, preflight=unowned)
        self.failed(lambda: adapter.prepare("prepare-discard", **self.inputs), "preflight-unconfirmed")
        self.assertEqual(self.read()["submissions"], [])

    def test_local_reservation_behavior_is_unchanged(self):
        class Local(OWNER.RESERVATIONS.ImmutableReservationStore):
            schema, operation_prefix = "fixture/local/v1", "fixture-"
            def path_for(self, phase, request): return self.root / (phase + ".json")
            def validate_time(self, value): self.assert_time(value)
        local = Local(self.root / "local")
        local.assert_time = lambda value: self.assertIsInstance(value, str)
        first, fresh = local.reserve("prepare", {"intent": "one"})
        self.assertTrue(fresh)
        self.assertEqual(local.reserve("prepare", {"intent": "one"}), (first, False))
        self.assertEqual(local.read("prepare", {"intent": "one"}), first)
        self.assertEqual(stat.S_IMODE((self.root / "local/prepare.json").stat().st_mode), 0o600)
        with self.assertRaises(OWNER.RESERVATIONS.ReservationFailure):
            local.reserve("prepare", {"intent": "different"})
        self.assertEqual(self.read()["calls"], [])

    def test_invalid_clock_or_future_start_never_opens_admission(self):
        for now, reason in ((True, "clock-invalid"), (-1, "clock-invalid"), ("1000", "clock-invalid"),
                            (999, "admission-closed"), (8200, "admission-closed")):
            with self.subTest(now=now):
                self.now = now
                self.failed(self.adapter.initialize, reason)
                self.assertEqual(self.read()["history"], [])

    def test_both_conditional_conflicts_are_finite_without_automatic_retry(self):
        self.adapter.initialize()
        for fault in ("PreconditionFailed", "ConditionalRequestConflict"):
            with self.subTest(fault=fault):
                before = len(self.read()["calls"])
                self.fault(fault)
                self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "record-conflict")
                self.assertEqual(self.read()["calls"][before:], [["s3api", "get-object"], ["s3api", "put-object"]])
        self.assertEqual(self.read()["submissions"], [])

    def test_observer_failure_cannot_be_reported_as_success_or_resubmitted(self):
        self.adapter.initialize()
        def unknown(_): raise ValueError("private-canary")
        self.failed(lambda: self.adapter.prepare("creation", **{**self.inputs, "observe": unknown}), "observation-unavailable")
        self.adapter.prepare("creation", **self.inputs)
        self.assertEqual(len(self.read()["submissions"]), 1)

    def test_malformed_public_selections_have_finite_diagnostics(self):
        self.failed(lambda: self.adapter.prepare([], **self.inputs), "kind-unsupported")
        for key in ("stack", "template_reference"):
            self.failed(lambda: self.adapter.prepare("creation", **{**self.inputs, key: []}), "instance-selection-invalid")
        self.assertEqual(self.read()["calls"], [])

    def test_missing_duplicate_or_crossed_plan_pairs_are_rejected(self):
        pairs = self.plan["stack_templates"]
        variants = ((), pairs + (pairs[0],), ((pairs[0][0], pairs[1][1]), (pairs[1][0], pairs[0][1])))
        for pairs in variants:
            with self.subTest(pairs=pairs):
                plan = {**self.plan, "stack_templates": pairs}
                self.failed(lambda: OWNER.SessionOperations(plan, self.records, provider=self.provider, preflight=self.preflight), "template-bindings-invalid")
        self.assertEqual(self.read()["calls"], [])

    def test_typed_provider_denial_is_preserved_without_replaying_intent(self):
        self.adapter.initialize()
        self.fault("cf-AccessDenied")
        code = self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "submission-uncertain")
        self.assertEqual(code, "environment-session-operation-create-change-set-submission-uncertain:aws-access-denied")
        observed = self.adapter.prepare("creation", **self.inputs)
        self.assertEqual(observed["status"], "absence-unconfirmed")
        self.assertEqual(len(self.read()["submissions"]), 1)


if __name__ == "__main__":
    unittest.main()
