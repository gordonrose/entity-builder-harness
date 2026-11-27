#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.test.check-selection.repository-contracts
#   version: 36
#   status: active
#   created_on: "2026-10-29"
#   updated_on: "2026-11-27"
#   layer: 06.shared
#   domain: validation
#   disciplines: [agentic, security, sre]
#   kind: test
#   purpose: Prove actual repository verification ownership and executable catalog contracts.
#   portability: {class: source-only, targets: []}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: repo.test.check-selection.wrapper
#     path: scripts/repo/check-selection/smoke-test.sh
from __future__ import annotations
from test_support import *


class RepositoryContractTests(unittest.TestCase):
    def codes(self, report): return {item["code"] for item in report["findings"]}

    def test_scheduler_contract_inputs_and_foundation_effects_are_owned(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        checks = catalog['checks']
        contracts = 'infra/04.deploy/03.product/targets/kanbien-core-platform/40-package-custody/github-actions/'
        cases = [('.agentic/04.deploy/schemas/change-impact.v1.schema.yml', 'persistence-composition'),
                 (contracts + 'core-scheduling-package-custody.delivery-access.yml', 'managed-handler-image-contracts'),
                 (contracts + 'entity-smoke-scheduling-package-custody.delivery-access.yml', 'managed-handler-image-contracts'),
                 ('scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/acceptance-route-rehearsal', 'acceptance-route-regression')]
        for path, identity in cases:
            with self.subTest(path=path):
                inputs = checks[identity]['inputs']
                self.assertIn(path, inputs)
                self.assertTrue(any(identity in rule['checks'] and any(selection.below(path, ref)
                    for ref in rule['inputs']) for rule in catalog['repository_inputs']))
                with tempfile.TemporaryDirectory(prefix='scheduler-contract-input-') as directory:
                    root = Path(directory); source = root / path
                    source.parent.mkdir(parents=True); source.write_text('original')
                    before = selection.fingerprint(root, inputs)
                    source.write_text('changed')
                    self.assertNotEqual(before, selection.fingerprint(root, inputs))
                    omitted = [ref for ref in inputs if not selection.below(path, ref)]
                    before = selection.fingerprint(root, omitted)
                    source.write_text('changed-again')
                    self.assertEqual(before, selection.fingerprint(root, omitted))
        identity = 'foundation-access-update-contracts'
        self.assertEqual(checks[identity]['effects'], ['read-only', 'writes-files'])
        self.assertEqual(selection.validate_check(ROOT, identity, checks[identity]), [])
        wrong = {**checks[identity], 'effects': ['read-only']}
        self.assertIn('check-effects-mismatch', self.codes({'findings': selection.validate_check(ROOT, identity, wrong)}))

    def test_scheduler_proof_inputs_cover_native_and_provider_dependencies(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        checks = catalog['checks']
        shared = checks['scheduling-runtime-proof-contracts']['inputs']
        self.assertIs(shared, checks['scheduling-acceptance-contracts']['inputs'])
        self.assertIs(shared, checks['scheduling-provider-controls']['inputs'])
        core = 'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/'
        entity = 'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/'
        common = [
            'scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/script.py',
            'scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/admission.py',
            'scripts/04.deploy/lifecycle/60-run/release-succession/scheduling-proof.py',
            'scripts/04.deploy/shared/provider-adapters/aws/task_journal.py',
            'scripts/04.deploy/operational-realization-gate/script.py',
            'scripts/04.deploy/lifecycle/40-package/package-custody-receipt/github-artifact.py',
            'scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/lambda-runtime-configuration.py',
            'infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/scheduling.yml',
            'infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/10-workload-binding/scheduling-binding.yml',
            core + 'run-administration/script.py', core + 'proof-receipts.py',
            core + 'task-operations.py', core + 'rehearse-isolated-database-restore/script.py',
            core + 'observability-receipts.py', core + 'rehearse-observability-readiness/script.py',
            entity + 'acceptance-evaluation/implementation/acceptance-evidence.py',
            entity + 'task-execution/implementation/task-route.py',
            entity + 'task-execution/implementation/task-steps.py',
            'scripts/repo/check-selection/script.py',
            'scripts/repo/check-selection/check-inputs.mjs',
            'scripts/repo/workspace-build/declarations.mjs',
        ]
        for identity, references in [('scheduling-runtime-proof-contracts', common),
                                     ('scheduling-acceptance-contracts', common),
                                     ('scheduling-provider-controls', common)]:
            inputs = set(checks[identity]['inputs'])
            self.assertEqual(len(inputs), len(checks[identity]['inputs']))
            self.assertFalse(inputs & {'scripts', 'infra', 'platform', 'apps', '.agentic'})
            self.assertTrue(all((ROOT / item).exists() for item in inputs))
            self.assertEqual(selection.validate_check(ROOT, identity, checks[identity]), [])
            for reference in references:
                with self.subTest(check=identity, dependency=reference):
                    self.assertTrue(any(selection.below(reference, item) for item in inputs))
                    self.assertTrue(any(identity in rule['checks'] and any(
                        selection.below(reference, item) for item in rule['inputs'])
                        for rule in catalog['repository_inputs']))
            # The real fingerprint must change, not merely a matching filename
            # assertion; omitting the dependency demonstrates the stale result.
            for reference in (references[0], references[-1]):
                with tempfile.TemporaryDirectory(prefix='scheduler-proof-input-') as directory:
                    root = Path(directory)
                    source = root / reference
                    source.parent.mkdir(parents=True)
                    source.write_text('controlled original dependency')
                    before = selection.fingerprint(root, inputs)
                    source.write_text('controlled changed dependency')
                    self.assertNotEqual(before, selection.fingerprint(root, inputs))
                    omitted = {item for item in inputs if not selection.below(reference, item)}
                    before = selection.fingerprint(root, omitted)
                    source.write_text('controlled third dependency')
                    self.assertEqual(before, selection.fingerprint(root, omitted))

    def test_managed_payload_inputs_cover_actual_fixture_reads(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        check = checks['managed-handler-payload']
        source = """
import {readProgramBuildInputs} from './scripts/04.deploy/lifecycle/20-build/runnable-program-contract/build-inputs.mjs';
const files = new Set();
for (const programId of JSON.parse(process.argv[1])) {
  const selected = readProgramBuildInputs(process.cwd(), {programId});
  for (const path of [selected.runtimeEntry.source, ...selected.manifestPaths,
    ...selected.inputs.sourceFiles, ...Object.values(selected.inputs.packages)
      .flatMap(exports => Object.values(exports).filter(path => path.endsWith('.json')))]) files.add(path);
}
console.log(JSON.stringify([...files].sort()));
"""
        result = subprocess.run(['node', '--input-type=module', '-e', source,
                                 json.dumps(check['applicability']['program_ids'])],
                                cwd=ROOT, capture_output=True, text=True, check=True)
        consumed = json.loads(result.stdout)
        self.assertTrue(consumed)
        def missing(inputs):
            return [path for path in consumed
                    if not any(selection.below(path, ref) for ref in inputs)]
        self.assertEqual(missing(check['inputs']), [])
        selected = 'platform/adapters/aws/runtime/lambda/package.json'
        self.assertIn(selected, consumed)
        self.assertIn(selected, missing([ref for ref in check['inputs'] if ref != selected]))
        self.assertEqual(checks['scheduling-provider-controls']['feedback']['rationale'],
                         'Prove exact legacy queue routes, immutable releases and observe-only recovery with controlled provider responses.')

    def test_retained_staging_catalogue_is_explicitly_isolated(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        contexts, findings = selection.isolated_check_contexts(ROOT, catalog, catalog['checks'])
        self.assertFalse(findings, findings)
        self.assertIn('kanbien-staging', contexts)
        retained = [identity for identity in catalog['checks']
                    if identity == 'platform-shell-payload' or identity.startswith('shell-')]
        self.assertEqual(len(retained), 42)
        for identity in retained:
            with self.subTest(check=identity):
                self.assertEqual(catalog['checks'][identity].get('isolated_context'), 'kanbien-staging')
        rag = [identity for identity, check in catalog['checks'].items()
               if check['argv'][1].startswith('scripts/02.rag-rulebook/')
               or identity == 'rag-retirement-regression']
        self.assertEqual(len(rag), 15)
        self.assertIn('rag-rulebook', contexts)
        for identity in rag:
            with self.subTest(check=identity):
                self.assertEqual(catalog['checks'][identity].get('isolated_context'), 'rag-rulebook')

    def test_every_catalogue_check_declares_its_scheduling_boundary(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        for identity, check in checks.items():
            with self.subTest(check=identity):
                self.assertIn('boundary', check)
                self.assertIn(check['boundary'], selection.BOUNDARIES)

    def test_core_runtime_alone_receives_declared_changed_path_context(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        declared = {identity for identity, check in checks.items() if check.get('changed_path_context')}
        self.assertEqual(declared, {'core-runtime'})
        self.assertEqual(selection.validate_check(ROOT, 'core-runtime', checks['core-runtime']), [])

    def test_infrastructure_composition_partition(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        parent = checks['entity-smoke-composition']
        self.assertEqual(parent['members'], ['entity-smoke-infrastructure-route', 'entity-smoke-composition-suite'])
        wrapper = parent['argv'][1]
        source = (ROOT / wrapper).read_text()
        fixture = 'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/controls-and-readiness/tests/infrastructure-route-test.py'
        self.assertEqual(source.count(fixture), 1)
        self.assertIn('infrastructure) exec python3 -B ' + fixture + ' ;;', source)
        self.assertLess(source.index(fixture), source.index('entity_smoke_build='))
        self.assertEqual(parent['inputs'], [wrapper])
        for identity, unit in zip(parent['members'], ['infrastructure', 'suite']):
            child = checks[identity]
            self.assertEqual(child['argv'], ['bash', wrapper, '--unit', unit])
            self.assertEqual(selection.validate_check(ROOT, identity, child), [])
        self.assertEqual(selection.validate_check(ROOT, 'entity-smoke-composition', parent), [])
        self.assertEqual(checks['entity-smoke-infrastructure-route']['runtime']['tools'], ['bash', 'python3'])
        route_units = {
            'entity-smoke-composition-base': 'base',
            'entity-smoke-task-route': 'task-route',
            'entity-smoke-failure-route': 'failure-route',
            'entity-smoke-restart-route': 'restart-route',
            'entity-smoke-credential-route': 'credential-route',
        }
        for identity, unit in route_units.items():
            child = checks[identity]
            self.assertEqual(child['argv'], ['bash', wrapper, '--unit', unit])
            self.assertIn('base|suite)' if unit == 'base' else unit + ')', source)
            self.assertEqual(selection.validate_check(ROOT, identity, child), [])
        for identity in ['entity-smoke-composition', *parent['members'], *route_units]:
            self.assertEqual(selection.execution_policy.validate_feedback(identity, checks[identity]), [])
        self.assertFalse(parent['feedback']['development'])
        self.assertTrue(checks['entity-smoke-infrastructure-route']['feedback']['development'])
        self.assertFalse(checks['entity-smoke-composition-suite']['feedback']['development'])
        self.assertEqual(checks['entity-smoke-composition-suite']['cadence'], 'deferred')
        suite = checks['entity-smoke-composition-suite']
        acceptance = checks['entity-smoke-acceptance-controls']['argv'][1]
        self.assertEqual(source.count('bash ' + acceptance), 1)
        self.assertGreater(source.index('bash ' + acceptance), source.index('if [ "$2" = "base" ]'))
        for name in ['acceptance-control-test.py', 'acceptance-state-test.py', 'acceptance-route-test.py']:
            self.assertNotIn(name, source, 'Acceptance fixtures belong to their existing wrapper, not the composition base.')
        for identity in ['entity-smoke-composition-suite', 'entity-smoke-composition-base']:
            self.assertIn('TMPDIR', checks[identity]['runtime']['environment'])
        for reference in [
            fixture, acceptance,
            'scripts/repo/check-selection/execution_policy.py',
        ]:
            self.assertTrue(any(selection.below(reference, declared) for declared in suite['inputs']))
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                path = root / reference; path.parent.mkdir(parents=True); path.write_text('first')
                before = selection.fingerprint(root, set(suite['inputs']))
                path.write_text('changed')
                self.assertNotEqual(selection.fingerprint(root, set(suite['inputs'])), before)
        for arguments in [('--unit', 'unknown'), ('--unit', 'infrastructure', 'extra'), ('--unit',)]:
            result = subprocess.run(['bash', wrapper, *arguments], cwd=ROOT, capture_output=True)
            self.assertEqual(result.returncode, 2)

    def test_entity_smoke_route_selection_avoids_the_full_aggregate(self):
        """Direct route work must select its dependent route leaves, not the full suite."""
        catalog = ROOT / 'scripts/repo/check-selection/checks.yml'
        original_fingerprint = selection.fingerprint
        def planning_fingerprint(root, references, *, exclude=frozenset()):
            if references == {'scripts/repo/check-selection/checks.yml'}:
                return original_fingerprint(root, references, exclude=exclude)
            import hashlib
            return hashlib.sha256(json.dumps(sorted(set(references) - set(exclude))).encode()).hexdigest()
        path = 'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-execution/tests/task-route-test.py'
        args = argparse.Namespace(root=ROOT, catalog=catalog, paths=[path], staged=False,
            all=False, stage='local', boundary='integration', ci=False, changed_only=False,
            execute_local=False, evidence=None, json=True, development=True,
            checks=None, aggregate_members=None, record_preparation=False,
            require_preparation=False, task_paths=None, explain=False)
        # This is a catalogue-routing test, not another repository census. A
        # separate explicit planner probe below this test's boundary covers
        # real scope discovery; repeatedly rebuilding it here is no stronger.
        with patch.object(selection, 'fingerprint', side_effect=planning_fingerprint), \
             patch.object(selection, 'runtime_identity', return_value={'selection_fixture': 'no-execution'}), \
             patch.object(selection, 'repository_paths', return_value=[path]), \
             patch.object(selection, 'discover', return_value=([], [])):
            report = selection.plan(args)
        self.assertEqual(report['verdict'], 'planned', report.get('findings'))
        selected = {check['check_id'] for check in report['checks'] if check['status'] == 'pending'}
        self.assertTrue({'entity-smoke-task-route', 'entity-smoke-restart-route',
                         'entity-smoke-credential-route'} <= selected)
        self.assertFalse({'entity-smoke-composition', 'entity-smoke-composition-suite'} & selected)

    def test_described_aggregate_branches_preserve_exact_execution_gate(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        wrapper = ROOT / 'scripts/repo/diagnostic-coverage/verify.sh'
        source = wrapper.read_text()
        original_read = Path.read_text
        for identity in ('diagnostic-runtime-contracts', 'diagnostic-base-runtime'):
            with self.subTest(check=identity):
                check = catalog['checks'][identity]
                self.assertEqual(selection.validate_check(ROOT, identity, check), [])
                expected = 'exec bash scripts/repo/check-selection/script.sh --aggregate-members ' + identity + ' --execute-local --json'
                for extra in ('node undeclared-child.mjs; ', 'non_npm; '):
                    altered = source.replace(expected, extra + expected)
                    self.assertNotEqual(altered, source)
                    with patch.object(Path, 'read_text', new=lambda path, *args, **kwargs:
                                      altered if path == wrapper else original_read(path, *args, **kwargs)):
                        self.assertEqual(selection.validate_check(ROOT, identity, check),
                                         [{'code': 'verification-aggregate-wrapper-invalid', 'check_id': identity}])

    def test_declaration_helpers_are_executed_and_fingerprinted_by_existing_regressions(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        payload = (ROOT / 'scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/script.sh').read_text()
        for name in ('declarations', 'compile', 'script', 'project-selection', 'runtime-packages'):
            self.assertIn('scripts/repo/workspace-build/' + name + '-test.mjs', payload)
        self.assertNotIn('check-inputs-test.mjs', payload)
        identity = 'check-selection-workspace-inputs'
        check = catalog['checks'][identity]
        wrapper = 'scripts/repo/check-selection/smoke-test.sh'
        helper = 'scripts/repo/check-selection/check-inputs.mjs'
        test = 'scripts/repo/check-selection/check-inputs-test.mjs'
        self.assertEqual(check['argv'], ['bash', wrapper, '--unit', 'workspace-inputs'])
        self.assertEqual(check['owner'], selection.metadata(ROOT / wrapper)['id'])
        self.assertEqual(selection.metadata(ROOT / test)['kind'], 'script')
        self.assertEqual(check['inputs'], [wrapper, helper, test, *[
            'scripts/repo/workspace-build/' + name + '.mjs'
            for name in ('declarations', 'script', 'compile', 'project-selection')]])
        self.assertEqual([rule['inputs'] for rule in catalog['repository_inputs'] if identity in rule['checks']], [check['inputs']])
        self.assertEqual(check['runtime']['node_packages'], ['typescript'])
        self.assertFalse(selection.validate_check(ROOT, identity, check))
        self.assertIn('workspace-inputs) exec node --test ' + test + ' ;;', (ROOT / wrapper).read_text())
        self.assertIn("PROJECTOR = '" + helper + "'", (ROOT / 'scripts/repo/check-selection/workspace_context.py').read_text())
        module = (ROOT / 'scripts/repo/module-structure/smoke-test.sh').read_text()
        self.assertIn('scripts/repo/module-structure/dependencies-test.mjs', module)
        boundary = (ROOT / 'scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/smoke-test.sh').read_text()
        self.assertIn('runnable-program-contract/smoke-test.sh', boundary)
        program = (ROOT / 'scripts/04.deploy/lifecycle/20-build/runnable-program-contract/smoke-test.sh').read_text()
        self.assertIn('runnable-program-contract/build-inputs-test.mjs', program)
        self.assertIn('runnable-program-contract/build-validation-test.py', program)
        for rule in catalog['repository_inputs']:
            self.assertTrue(set(rule['checks']) <= set(catalog['checks']))
        for identity, source in [('check-selection-workspace-inputs', helper),
                                 ('check-selection-workspace-inputs', test),
                                 ('check-selection-workspace-inputs', 'scripts/repo/workspace-build/project-selection.mjs'),
                                 ('runtime-payload-assembly', 'scripts/repo/workspace-build/project-selection.mjs'),
                                 ('runtime-payload-assembly', 'scripts/repo/workspace-build/compile-test.mjs'),
                                 ('core-dependency-boundary', 'scripts/04.deploy/lifecycle/20-build/runnable-program-contract/build-validation-test.py'),
                                 ('runnable-program', 'scripts/repo/workspace-build/declarations.mjs')]:
            with self.subTest(check=identity), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                file = root / source; file.parent.mkdir(parents=True); file.write_text('first')
                inputs = set(catalog['checks'][identity]['inputs'])
                before = selection.fingerprint(root, inputs)
                file.write_text('second')
                self.assertNotEqual(selection.fingerprint(root, inputs), before)
                omitted = {path for path in inputs if not selection.below(source, path)}
                counterexample = selection.fingerprint(root, omitted)
                file.write_text('third')
                self.assertEqual(selection.fingerprint(root, omitted), counterexample)

    def test_shared_payload_assembly_selects_and_invalidates_both_consumers(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        cases = {
            'scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/assemble.mjs': {'bootstrap-payload-regression'},
            'scripts/04.deploy/lifecycle/40-package/prepare-runtime-dependencies/prepare.mjs': set(),
            'scripts/04.deploy/lifecycle/40-package/build-candidate-image/operations.sh': None,
        }
        for source, additional in cases.items():
            expected = {'persistence-payload-regression', 'entity-smoke-publication-contract', 'package-custody-regression', 'persistence-container', 'entity-smoke-container'} if additional is None else additional | {'runtime-payload-assembly', 'runtime-dependency-assembly',
                        'persistence-payload-regression', 'entity-smoke-composition',
                        'persistence-container', 'entity-smoke-container'}
            args = argparse.Namespace(root=ROOT, catalog=ROOT / 'scripts/repo/check-selection/checks.yml', paths=[source], staged=False,
                                      all=False, stage='local', execute_local=False, evidence=None, json=True)
            report = selection.plan(args)
            self.assertEqual(report['verdict'], 'planned', report.get('findings'))
            self.assertTrue(expected <= {check['check_id'] for check in report['checks']},
                            (source, expected - {check['check_id'] for check in report['checks']}))
            # Aggregate receipts bind child evidence; the child owns source
            # fingerprints while the parent's own input is only its wrapper.
            owners = {member for identity in expected - {'persistence-container', 'entity-smoke-container'}
                      for member in catalog['checks'][identity].get('members', [identity])}
            for identity in owners:
                with self.subTest(source=source, check=identity), tempfile.TemporaryDirectory(prefix='shared-package-input-') as directory:
                    root = Path(directory)
                    file = root / source
                    file.parent.mkdir(parents=True)
                    file.write_text('fixture v1')
                    inputs = set(catalog['checks'][identity]['inputs'])
                    before = selection.fingerprint(root, inputs)
                    file.write_text('fixture v2')
                    self.assertNotEqual(before, selection.fingerprint(root, inputs))
                    omitted = {item for item in inputs if not selection.below(source, item)}
                    missing_before = selection.fingerprint(root, omitted)
                    file.write_text('fixture v3')
                    self.assertEqual(missing_before, selection.fingerprint(root, omitted),
                                     'counterexample demonstrates why the shared input cannot be omitted')

    def test_shared_ecs_response_selects_and_invalidates_both_bindings(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        for source in ('scripts/04.deploy/shared/provider-adapters/aws/response.py',
                       'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/ecs-task-evidence.py'):
            args = argparse.Namespace(root=ROOT, catalog=ROOT / 'scripts/repo/check-selection/checks.yml', paths=[source], staged=False,
                                      all=False, stage='local', execute_local=False, evidence=None, json=True)
            report = selection.plan(args)
            self.assertEqual(report['verdict'], 'planned', report.get('findings'))
            expected = {'entity-smoke-composition', 'persistence-payload-regression'}
            if source.endswith('/response.py'):
                expected |= {'persistence-provider-regression', 'deployment-operation-diagnostics-regression'}
            selected = {check['check_id'] for check in report['checks']}
            self.assertTrue(expected <= selected)
            retained = {'shell-negative-authz-client-check', 'shell-postgresql-relational-smoke-check'}
            self.assertFalse(retained & selected, 'shared Core changes do not activate retained staging')
            owners = {member for identity in ('entity-smoke-composition', 'persistence-payload-regression')
                      for member in catalog['checks'][identity].get('members', [identity])}
            for identity in owners:
                with self.subTest(source=source, check=identity), tempfile.TemporaryDirectory(prefix='shared-ecs-input-') as directory:
                    root = Path(directory)
                    file = root / source
                    file.parent.mkdir(parents=True)
                    file.write_text('fixture v1')
                    inputs = set(catalog['checks'][identity]['inputs'])
                    before = selection.fingerprint(root, inputs)
                    file.write_text('fixture v2')
                    self.assertNotEqual(before, selection.fingerprint(root, inputs))
                    omitted = {item for item in inputs if not selection.below(source, item)}
                    missing_before = selection.fingerprint(root, omitted)
                    file.write_text('fixture v3')
                    self.assertEqual(missing_before, selection.fingerprint(root, omitted))

        # Retention includes an executable deliberate maintenance route.
        args.checks = sorted(retained)
        args.paths = []
        report = selection.plan(args)
        self.assertEqual(report['verdict'], 'planned', report.get('findings'))
        self.assertEqual({check['check_id'] for check in report['checks']}, retained)

    def test_shared_cli_boundary_invalidates_registered_callers(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        expected = {'diagnostic-catalog-readers', 'core-target-declaration-regression', 'bootstrap-target-controls-regression',
                    'restore-connection-diagnostics', 'entity-smoke-composition', 'persistence-composition',
                    'persistence-payload-regression', 'persistence-provider-regression', 'acceptance-route-regression',
                    'deployment-operation-diagnostics-regression'}
        for source in ('scripts/04.deploy/shared/provider-adapters/aws/cli.py',
                       'scripts/04.deploy/shared/provider-adapters/aws/response.py'):
            args = argparse.Namespace(root=ROOT, catalog=ROOT / 'scripts/repo/check-selection/checks.yml', paths=[source], staged=False,
                                      all=False, stage='local', execute_local=False, evidence=None, json=True)
            report = selection.plan(args)
            self.assertEqual(report['verdict'], 'planned', report.get('findings'))
            self.assertTrue(expected <= {check['check_id'] for check in report['checks']})
            owners = {member for identity in expected
                      for member in catalog['checks'][identity].get('members', [identity])}
            for identity in owners:
                with self.subTest(source=source, check=identity), tempfile.TemporaryDirectory(prefix='shared-cli-input-') as directory:
                    root = Path(directory)
                    file = root / source
                    file.parent.mkdir(parents=True)
                    file.write_text('fixture v1')
                    inputs = set(catalog['checks'][identity]['inputs'])
                    before = selection.fingerprint(root, inputs)
                    file.write_text('fixture v2')
                    self.assertNotEqual(before, selection.fingerprint(root, inputs))
                    omitted = {item for item in inputs if not selection.below(source, item)}
                    missing_before = selection.fingerprint(root, omitted)
                    file.write_text('fixture v3')
                    self.assertEqual(missing_before, selection.fingerprint(root, omitted))

    def test_shared_task_and_publication_owners_invalidate_actual_callers(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        # Plans still validate the real catalog and every selected input. This
        # fixture never changes repository sources: reuse their real digests
        # across plan cases, not across runs. Actual mutation/omission probes
        # below retain the unwrapped fingerprint implementation.
        actual_fingerprint, plan_hashes = selection.fingerprint, {}
        def plan_fingerprint(root, refs, *, exclude=frozenset()):
            if root != ROOT or refs == {'scripts/repo/check-selection/checks.yml'}:
                return actual_fingerprint(root, refs, exclude=exclude)
            key = (root, frozenset(refs), frozenset(exclude))
            if key not in plan_hashes:
                plan_hashes[key] = actual_fingerprint(root, refs, exclude=exclude)
            return plan_hashes[key]
        aws = 'scripts/04.deploy/shared/provider-adapters/aws/'
        baseline = {'diagnostic-catalog-readers', 'persistence-composition', 'persistence-provider-regression',
                    'acceptance-route-regression', 'deployment-operation-diagnostics-regression'}
        publication = {'entity-smoke-publication-contract', 'package-custody-regression'}
        cases = {
            aws + 'tasks.py': baseline | {'entity-smoke-composition', 'restore-connection-diagnostics', 'persistence-payload-regression', 'runtime-payload-assembly'},
            aws + 'task_journal.py': baseline,
            'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/task-operations.py': baseline,
            'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/replacement-operations.py': {'diagnostic-catalog-readers', 'persistence-provider-regression', 'acceptance-route-regression', 'deployment-operation-diagnostics-regression'},
            'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/snapshot-operations.py': {'diagnostic-catalog-readers', 'persistence-provider-regression', 'acceptance-route-regression', 'deployment-operation-diagnostics-regression'},
            'infra/04.deploy/03.product/entrypoints/shared/persistence/configuration-implementation.ts': {'diagnostic-catalog-readers', 'entity-smoke-composition', 'persistence-composition', 'persistence-payload-regression', 'package-custody-regression'},
            'infra/04.deploy/03.product/entrypoints/shared/persistence/configuration.ts': {'diagnostic-catalog-readers', 'entity-smoke-composition', 'persistence-composition', 'persistence-payload-regression', 'package-custody-regression'},
            'infra/04.deploy/03.product/entrypoints/shared/persistence/role-credential.ts': {'diagnostic-catalog-readers', 'entity-smoke-composition', 'persistence-composition', 'persistence-payload-regression', 'package-custody-regression'},
            'infra/04.deploy/03.product/entrypoints/shared/persistence/operation-diagnostics.ts': {'diagnostic-catalog-readers', 'entity-smoke-composition', 'persistence-composition', 'persistence-payload-regression', 'package-custody-regression'},
            aws + 'resource_reservation.py': baseline | {'entity-smoke-composition', 'runtime-payload-assembly'},
            aws + 'snapshots.py': baseline | {'entity-smoke-composition', 'runtime-payload-assembly'},
            aws + 'change_sets.py': {'entity-smoke-composition', 'persistence-provider-regression', 'acceptance-route-regression', 'runtime-payload-assembly'},
            'scripts/04.deploy/lifecycle/60-run/release-succession/script.py': {'release-succession-regression', 'entity-smoke-composition', 'acceptance-route-regression', 'runtime-payload-assembly'},
            aws + 'ecr_publication.py': publication,
            'scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody/publication.py': publication,
        }
        for source, expected in cases.items():
            args = argparse.Namespace(root=ROOT, catalog=ROOT / 'scripts/repo/check-selection/checks.yml', paths=[source], staged=False,
                                      all=False, stage='local', execute_local=False, evidence=None, json=True)
            with patch.object(selection, 'fingerprint', side_effect=plan_fingerprint):
                report = selection.plan(args)
            self.assertEqual(report['verdict'], 'planned', report.get('findings'))
            self.assertTrue(expected <= {check['check_id'] for check in report['checks']},
                            (source, expected - {check['check_id'] for check in report['checks']}))
            self.assertNotIn('platform-shell-payload', {check['check_id'] for check in report['checks']})
            # Its evidence still expires when shared inputs change; isolation
            # removes automatic scheduling, not the retained proof's inputs.
            retained = {'platform-shell-payload'} if source.startswith('infra/04.deploy/03.product/entrypoints/shared/persistence/') else set()
            owners = {member for identity in expected | retained
                      for member in catalog['checks'][identity].get('members', [identity])}
            for identity in owners:
                with self.subTest(source=source, check=identity), tempfile.TemporaryDirectory(prefix='shared-execution-input-') as directory:
                    root = Path(directory)
                    file = root / source; file.parent.mkdir(parents=True); file.write_text('fixture v1')
                    inputs = set(catalog['checks'][identity]['inputs'])
                    before = selection.fingerprint(root, inputs)
                    file.write_text('fixture v2')
                    self.assertNotEqual(before, selection.fingerprint(root, inputs))
                    omitted = {item for item in inputs if not selection.below(source, item)}
                    missing_before = selection.fingerprint(root, omitted)
                    file.write_text('fixture v3')
                    self.assertEqual(missing_before, selection.fingerprint(root, omitted))
        for identity in publication:
            inputs = catalog['checks'][identity]['inputs']
            for source in ('scripts/04.deploy/shared/deployment-operation-diagnostics.py', 'scripts/repo/diagnostic-coverage/runtime_contract.py',
                           'packages/core/contracts/diagnostics.v1.json', 'infra/04.deploy/03.product/entrypoints/contracts/kanbien-platform-delivery-diagnostics.v1.json'):
                self.assertTrue(any(selection.below(source, item) for item in inputs), (identity, source))

    def test_feature_catalog_inputs_invalidate_actual_fingerprints(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        for identity in ('diagnostic-catalog-readers', 'diagnostic-runtime-contracts'):
            with self.subTest(check=identity), tempfile.TemporaryDirectory(prefix='feature-catalog-inputs-') as directory:
                root = Path(directory)
                source = root / 'apps/entity-smoke/features/test-entity/contract/diagnostics.ts'
                export = root / 'apps/entity-smoke/contracts/diagnostics.v1.json'
                source.parent.mkdir(parents=True); source.write_text('fixture source v1\n')
                export.parent.mkdir(parents=True); export.write_text('{"fixture":1}\n')
                inputs = set(checks[identity]['inputs'])
                before = selection.fingerprint(root, inputs)
                source.write_text('fixture source v2\n')
                changed_source = selection.fingerprint(root, inputs)
                self.assertNotEqual(before, changed_source, 'consumed feature source must invalidate catalog proof')
                export.write_text('{"fixture":2}\n')
                changed_export = selection.fingerprint(root, inputs)
                self.assertNotEqual(changed_source, changed_export, 'feature export must invalidate catalog proof')
                (root / 'unrelated.txt').write_text('unrelated fixture input\n')
                self.assertEqual(changed_export, selection.fingerprint(root, inputs))
                omitted = inputs - {'apps/entity-smoke'}
                missing_before = selection.fingerprint(root, omitted)
                source.write_text('fixture source v3\n')
                self.assertEqual(missing_before, selection.fingerprint(root, omitted), 'counterexample reproduces omitted-root cache identity')
                self.assertIn('@kanbien/app-entity-smoke', checks[identity]['runtime']['node_packages'])

    def test_catalog_configuration_selects_its_reader_and_invalidates_consumed_inputs(self):
        config = 'scripts/repo/diagnostic-coverage/tsconfig.json'
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        inputs = set(catalog['checks']['diagnostic-catalog-readers']['inputs'])
        def selected(candidate):
            return {identity for rule in candidate['repository_inputs'] if config in rule['inputs'] for identity in rule['checks']}
        self.assertEqual(selected(catalog), {'diagnostic-catalog-readers'})
        stale = copy.deepcopy(catalog)
        for rule in stale['repository_inputs']:
            if config in rule['inputs']: rule['checks'] = ['diagnostic-runtime-contracts']
        self.assertNotIn('diagnostic-catalog-readers', selected(stale))
        self.assertTrue(any(selection.below(config, item) for item in inputs))
        project = json.loads((ROOT / config).read_text())
        for include in project['include']:
            prefix = (ROOT / config).parent.joinpath(include.split('*', 1)[0]).resolve().relative_to(ROOT).as_posix().rstrip('/')
            self.assertTrue(any(selection.below(prefix, item) for item in inputs), prefix)
        with tempfile.TemporaryDirectory(prefix='catalog-config-input-') as directory:
            root = Path(directory); source = root / config
            source.parent.mkdir(parents=True); source.write_text('first')
            before = selection.fingerprint(root, inputs); source.write_text('second')
            self.assertNotEqual(before, selection.fingerprint(root, inputs))
            omitted = {item for item in inputs if not selection.below(config, item)}
            before = selection.fingerprint(root, omitted); source.write_text('third')
            self.assertEqual(before, selection.fingerprint(root, omitted))

    def test_feedback_pilot_binds_real_owners_without_reclassifying_existing_gates(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        checks = catalog['checks']
        for identity, check in checks.items():
            self.assertEqual(selection.execution_policy.validate_feedback(identity, check), [], identity)
        feature = checks['entity-smoke-runtime']
        self.assertEqual(feature['argv'], ['bash', 'scripts/repo/diagnostic-coverage/verify.sh', '--unit', 'entity-smoke'])
        self.assertEqual(feature['boundary'], 'integration')
        self.assertEqual(feature['effects'], ['writes-files'])
        self.assertTrue(feature['feedback']['development'])
        self.assertIn('apps/entity-smoke', feature['inputs'])
        self.assertIn('packages/core', feature['inputs'])
        self.assertIn('platform/contracts', feature['inputs'])
        self.assertIn('packages/core/tests/test-infrastructure/helpers/runtime-runner-fixture.ts', feature['inputs'])
        scripts = json.loads((ROOT / 'package.json').read_text())['scripts']
        self.assertEqual(scripts['app:entity-smoke:check'], 'npm run app:entity-smoke:typecheck && npm run app:entity-smoke:test')
        self.assertIn('tsc -p apps/entity-smoke/tsconfig.check.json', scripts['app:entity-smoke:typecheck'])
        self.assertIn('node apps/entity-smoke/tests/run-runtime-tests.mjs', scripts['app:entity-smoke:test'])
        self.assertTrue(checks['dynamodb-persistence-runtime']['feedback']['development'])
        self.assertTrue(checks['postgresql-connection-diagnostics']['feedback']['development'])
        for identity in ('platform-server-runtime', 'kanbien-platform-runtime', 'platform-shell-payload',
                         'check-selection-mechanics', 'check-selection-promotion',
                         'check-selection-repository-contracts'):
            self.assertFalse(checks[identity]['feedback']['development'], identity)
            self.assertEqual(checks[identity]['boundary'], 'integration', identity)
        self.assertTrue(checks['diagnostic-runtime-contracts']['focused_prerequisites'])
        self.assertIn('platform-server-runtime', checks['diagnostic-runtime-contracts']['members'])
        self.assertIn('kanbien-platform-runtime', checks['diagnostic-runtime-contracts']['members'])
        self.assertNotIn('feedback', checks['core-runtime'])

    def test_migrated_runner_units_bind_shared_fixture_changes(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        fixture = 'packages/core/tests/test-infrastructure/helpers/runtime-runner-fixture.ts'
        identities = ('core-runtime', 'platform-contracts-runtime', 'platform-config-runtime',
                      'platform-health-runtime', 'platform-observability-runtime',
                      'platform-persistence-runtime', 'platform-runtime-runtime',
                      'platform-security-runtime', 'platform-testing-runtime',
                      'platform-workers-runtime', 'platform-server-runtime',
                      'platform-smoke-runtime', 'kanbien-platform-runtime',
                      'cloudwatch-observability-runtime', 'ecs-fargate-runtime',
                      'dynamodb-persistence-runtime', 'sqs-queue-runtime',
                      'security-cognito-diagnostics', 'security-shared-rate-limit-diagnostics',
                      'postgresql-connection-diagnostics')

        def assert_binding(candidate):
            for identity in identities:
                self.assertTrue(any(selection.below(fixture, item)
                                    for item in candidate['checks'][identity]['inputs']), identity)

        assert_binding(catalog)
        stale = copy.deepcopy(catalog)
        stale['checks']['platform-config-runtime']['inputs'].remove(fixture)
        with self.assertRaises(AssertionError):
            assert_binding(stale)

    def test_imported_diagnostic_fixtures_have_focused_registered_owners(self):
        import re
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        expected = {
            "chat-startup-regression": ("scripts/00.chat/startup/start-chat-session/smoke-test.sh", True),
            "chat-log-writers-regression": ("scripts/00.chat/session-log/update-chat-log/smoke-test.sh", False),
            "chat-log-maintenance-regression": ("scripts/00.chat/session-log/checkpoint-chat-session-log/smoke-test.sh", False),
            "chat-summary-regression": ("scripts/00.chat/reporting/generate-commit-log-summary/smoke-test.sh", True),
            "chat-upstream-portability-regression": ("scripts/00.chat/upstream/validate-llm-workbench-portability/script.sh", True),
            "harness-governed-runner-regression": ("scripts/01.harness/smoke-test-governed-script-runner.sh", False),
            "harness-command-drift-regression": ("scripts/01.harness/smoke-test-governed-script-command-drift.sh", False),
            "harness-process-drift-regression": ("scripts/01.harness/smoke-test-deterministic-process-drift.sh", False),
            "chat-bootstrap-audit-regression": ("scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/smoke-test.sh", False),
            "chat-migration-audit-regression": ("scripts/00.chat/migration/audit-chat-layer-migration/smoke-test.sh", False),
            "chat-upstream-ensure-regression": ("scripts/00.chat/upstream/ensure-llm-workbench-repo/smoke-test.sh", False),
            "chat-upstream-contract-regression": ("scripts/00.chat/upstream/check-llm-workbench-contract/smoke-test.sh", False),
            "chat-upstream-bootstrap-regression": ("scripts/00.chat/upstream/bootstrap-llm-workbench-repo/smoke-test.sh", True),
            "chat-integration-preparation-regression": ("scripts/00.chat/remote-promotion/prepare-clean-integration-worktree/smoke-test.sh", False),
            "chat-cleanup-regression": ("scripts/00.chat/git/cleanup-empty-chat-branches/smoke-test.sh", False),
            "chat-prerequisites-regression": ("scripts/00.chat/session-log/check-commit-prerequisites/smoke-test.sh", False),
            "chat-conflict-audit-regression": ("scripts/00.chat/main-refresh/verify-conflict-audit/smoke-test.sh", False),
            "chat-recovery-regression": ("scripts/00.chat/recovery/import-active-paths-to-chat-worktree/smoke-test.sh", False),
            "chat-session-reader-regression": ("scripts/00.chat/session-log/read-current-chat-log/smoke-test.sh", False),
            "chat-session-resolution-regression": ("scripts/00.chat/startup/resolve-current-chat-session/smoke-test.sh", True),
            "chat-worktree-paths-regression": ("scripts/00.chat/worktree/paths/smoke-test.sh", True),
            "chat-command-dispatch-regression": ("scripts/00.chat/command/dispatcher/smoke-test.sh", True),
            "chat-refresh-readiness-regression": ("scripts/00.chat/main-refresh/classify-refresh-readiness/smoke-test.sh", True),
            "chat-conflict-classification-regression": ("scripts/00.chat/main-refresh/classify-conflict/smoke-test.sh", False),
            "chat-log-deletion-regression": ("scripts/00.chat/session-log/check-commitlog-deletions/smoke-test.sh", False),
        }
        direct_owners = {
            'chat-summary-regression': (
                'chat.script.reporting.generate-commit-log-summary.smoke-test',
                'scripts/00.chat/reporting/generate-commit-log-summary/script.sh'),
            'chat-upstream-ensure-regression': (
                'chat.script.upstream.ensure-llm-workbench-repo.smoke-test',
                'scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh'),
            'chat-upstream-contract-regression': (
                'chat.script.upstream.check-llm-workbench-contract.smoke-test',
                'scripts/00.chat/upstream/check-llm-workbench-contract/script.sh'),
            'harness-process-drift-regression': (
                'harness.script.smoke-test-deterministic-process-drift',
                'scripts/01.harness/check-deterministic-process-drift.sh'),
            'chat-bootstrap-audit-regression': (
                'chat.script.bootstrap.diagnostic-smoke-test',
                'scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/script.sh'),
            'chat-migration-audit-regression': (
                'chat.script.migration.diagnostic-smoke-test',
                'scripts/00.chat/migration/audit-chat-layer-migration/script.sh'),
        }
        for identity, (fixture, uses_node) in expected.items():
            with self.subTest(identity=identity):
                check = catalog['checks'][identity]
                unit = identity.removesuffix('-regression')
                if identity in direct_owners:
                    self.assertEqual(check['argv'], ['bash', fixture])
                    self.assertEqual(check['owner'], direct_owners[identity][0])
                    self.assertEqual(check['effects'], ['writes-files'])
                else:
                    self.assertEqual(check['argv'], ['bash', 'scripts/repo/check-selection/smoke-test.sh', '--unit', unit])
                    self.assertEqual(check['owner'], 'repo.test.check-selection.wrapper')
                    self.assertEqual(check['effects'], ['read-only', 'writes-files'])
                wrapper = (ROOT / 'scripts/repo/check-selection/smoke-test.sh').read_text()
                self.assertEqual(wrapper.count(unit + ') exec bash ' + fixture + ' ;;'), 1)
                self.assertEqual(check['stage'], 'local')
                self.assertEqual(check['boundary'], 'integration')
                self.assertFalse(check['scope_inputs'])
                self.assertFalse(selection.validate_check(ROOT, identity, check))
                self.assertEqual('node' in check['runtime']['tools'], uses_node)
                inputs = check['inputs']
                self.assertEqual(len(inputs), len(set(inputs)))
                # Real copied source files, not merely the fixture itself, must invalidate proof.
                copied = re.findall(r'\$SOURCE_ROOT/(scripts/[^"\s$]+)"', (ROOT / fixture).read_text())
                sources = [fixture, *copied]
                if identity in direct_owners:
                    sources.append(direct_owners[identity][1])
                    self.assertFalse(any(selection.below('scripts/repo/check-selection/smoke-test.sh', ref)
                                         for ref in inputs))
                else:
                    sources.append('scripts/repo/check-selection/smoke-test.sh')
                for source in sources:
                    self.assertTrue(any(selection.below(source, ref) for ref in inputs), source)
                rules = [rule for rule in catalog['repository_inputs'] if identity in rule['checks']]
                self.assertEqual(len(rules), 1)
                self.assertEqual(set(rules[0]['inputs']), set(inputs))
                self.assertFalse(any(selection.below('platform/server/src/index.ts', ref) for ref in inputs))
                self.assertNotIn(identity, catalog['checks']['check-selection-regression']['members'])
        readiness = catalog['checks']['chat-refresh-readiness-regression']['inputs']
        merge = catalog['checks']['chat-local-merge-regression']['inputs']
        for source in ('scripts/00.chat/local-merge/list-active-chat-branches',
                       'scripts/00.chat/local-merge/report-chat-branch-overlaps',
                       'scripts/00.chat/reporting/report-chat-workspaces'):
            self.assertIn(source, merge)
        merge_rule = next(rule for rule in catalog['repository_inputs']
                          if rule['checks'] == ['chat-local-merge-regression'])
        self.assertEqual(set(merge_rule['inputs']), set(merge))
        for rule in catalog['repository_inputs']:
            for source in rule['inputs']:
                self.assertNotIn(' - scripts/', source, 'indented YAML list item became part of a path')
        for capability in ('classify-refresh-readiness', 'check-chat-is-current-with-main', 'show-main-update-status', 'rehearse-refresh-from-main'):
            self.assertIn('scripts/00.chat/main-refresh/' + capability, readiness)

    def test_configuration_requirements_have_one_harness_standard_owner(self):
        canonical = '.agentic/03.product/standards/config-runtime-settings.md'
        legacy = 'docs/03.product/rules/platform/concerns/config-runtime-settings.yml'
        manifest = yaml.safe_load((ROOT / '.agentic/01.harness/manifest.yml').read_text())
        pointer = yaml.safe_load((ROOT / legacy).read_text())
        workflow = (ROOT / '.agentic/03.product/workflows/platform-runtime-implementation.md').read_text()
        metadata = selection.metadata(ROOT / canonical)
        placement = (ROOT / '.agentic/01.harness/standards/document-artifact-placement.md').read_text()
        self.assertNotIn('| Structured ruleset | `docs/', placement)
        self.assertNotIn('| Rule pack | `docs/', placement)
        self.assertIn('`.agentic/<owner-layer>/standards/`', placement)

        def assert_owner(candidate):
            self.assertIn(canonical, candidate['current_known_artifacts']['standards'])
            self.assertNotIn(legacy, json.dumps(candidate['current_known_artifacts']))
            self.assertEqual(metadata['kind'], 'standard')
            self.assertEqual(metadata['id'], 'product.standard.config-runtime-settings')
            self.assertEqual(metadata['status'], 'active')
            self.assertIn('../standards/config-runtime-settings.md', workflow)
            self.assertEqual(pointer['canonical_document'], canonical)
            self.assertEqual(pointer['canonical_id'], metadata['id'])
            self.assertEqual(pointer['compatibility'], 'human-readable-pointer')
            self.assertEqual(pointer['status'], 'deprecated')
            self.assertNotIn('rules', pointer, 'the pointer must not retain a second requirements body')

        assert_owner(manifest)
        stale = copy.deepcopy(manifest)
        stale['current_known_artifacts']['standards'].remove(canonical)
        stale['current_known_artifacts']['concern_rulesets'].append(legacy)
        with self.assertRaises(AssertionError):
            assert_owner(stale)

    def test_configuration_standard_retains_diagnostic_selection_and_rejects_stale_binding(self):
        canonical = '.agentic/03.product/standards/config-runtime-settings.md'
        legacy = 'docs/03.product/rules/platform/concerns/config-runtime-settings.yml'
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        expected = {'diagnostic-adoption', 'diagnostic-runtime-contracts'}

        def assert_binding(candidate):
            rules = candidate['repository_inputs']
            self.assertTrue(any(canonical in rule['inputs'] and expected <= set(rule['checks'])
                                for rule in rules), 'canonical requirements must retain their diagnostic owners')
            self.assertFalse(any(legacy in rule['inputs'] for rule in rules),
                             'current selection must not treat the pointer as the requirements owner')
            selected = {identity for rule in rules
                        if any(selection.below(canonical, item) for item in rule['inputs'])
                        for identity in rule['checks']}
            self.assertTrue(expected <= selected)

        assert_binding(catalog)
        stale = copy.deepcopy(catalog)
        for rule in stale['repository_inputs']:
            rule['inputs'] = [legacy if item == canonical else item for item in rule['inputs']]
        with self.assertRaises(AssertionError):
            assert_binding(stale)

    def test_module_structure_is_a_retained_manual_scan_with_bounded_regression(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        checks = catalog['checks']
        for identity, command, owner, boundary, cadence in [
            ('module-index-structure', 'script.sh', 'repo.module-structure.command', 'commit', 'hygiene'),
            ('module-index-structure-regression', 'smoke-test.sh', 'repo.module-structure.regression', 'integration', 'candidate'),
        ]:
            check = checks[identity]
            self.assertEqual(check['argv'], ['bash', 'scripts/repo/module-structure/' + command])
            self.assertEqual(check['owner'], owner)
            self.assertEqual(check['boundary'], boundary)
            self.assertEqual(check.get('cadence', 'candidate'), cadence)
            self.assertEqual(check['effects'], ['read-only'] if boundary == 'commit' else ['read-only', 'writes-files'])
            self.assertEqual(check['stage'], 'local')
            self.assertFalse(selection.validate_check(ROOT, identity, check))
            self.assertIn('typescript', check['runtime']['node_packages'])
        rules = catalog['repository_inputs']

        # The complete source scan stays manually available with all of its
        # invalidators declared. The slower fixture command tests the checker
        # automatically only when its own inputs change.
        source_rule = checks['module-index-structure']
        regression_rule = checks['module-index-structure-regression']
        fixture_inputs = {
            'scripts/repo/module-structure/check.mjs',
            'scripts/repo/module-structure/smoke-test.mjs',
            'scripts/repo/module-structure/smoke-test.sh',
            'scripts/repo/module-structure/dependencies.mjs',
            'scripts/repo/workspace-build/declarations.mjs',
            'scripts/repo/module-structure/dependencies-test.mjs',
            'package.json',
            'package-lock.json',
        }
        self.assertEqual(set(regression_rule['inputs']), fixture_inputs)
        for root in ['packages', 'platform', 'apps', 'products', 'infra']:
            self.assertIn(root, source_rule['inputs'], 'real-source inspection must invalidate the commit command')
            self.assertNotIn(root, regression_rule['inputs'], 'fixture proof must not rerun for ordinary source changes')

        def selected(ref):
            return {identity for rule in rules if any(selection.below(ref, item) for item in rule['inputs'])
                    for identity in rule['checks']}

        for ref in ['packages/core/src/config/index.ts', 'packages/future/src/index.ts',
                    'platform/future/src/index.ts', 'apps/future/src/index.ts',
                    'products/future/src/index.ts', 'infra/04.deploy/future.ts', 'scripts/repo/module-structure/legacy.v1.json',
                    '.agentic/03.product/standards/public-module-structure.md']:
            self.assertTrue(any(selection.below(ref, item) for item in source_rule['inputs']), ref)
            self.assertNotIn('module-index-structure-regression', selected(ref), ref)
        for ref in fixture_inputs - {'package.json', 'package-lock.json'}:
            self.assertIn('module-index-structure-regression', selected(ref), ref)
            self.assertTrue(any(selection.below(ref, item) for item in source_rule['inputs']), ref)
        baseline = json.loads((ROOT / 'scripts/repo/module-structure/legacy.v1.json').read_text())
        self.assertNotIn('packages/core/src/config/index.ts', [row['path'] for row in baseline['legacy']])
        self.assertIn('module-structure/check.mjs', (ROOT / 'packages/core/tests/test-infrastructure/static-validation/core-boundaries.test.mjs').read_text())
        self.assertIn('scripts/repo/module-structure/check.mjs', checks['core-runtime']['inputs'])
        self.assertIn('scripts/repo/module-structure/dependencies.mjs', checks['core-runtime']['inputs'])
        self.assertTrue(any('scripts/repo/module-structure/check.mjs' in rule['inputs']
                            and 'core-runtime' in rule['checks'] for rule in rules))

    def test_workspace_dependency_inspection_uses_existing_gate_and_real_input_closure(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        real_source = 'module-index-structure'
        fixture_regression = 'module-index-structure-regression'
        fixture_references = ['scripts/repo/module-structure/dependencies.mjs',
                              'scripts/repo/workspace-build/declarations.mjs',
                              'scripts/repo/module-structure/dependencies-test.mjs']

        def selected(reference):
            return {identity for rule in catalog['repository_inputs']
                    if any(selection.below(reference, item) for item in rule['inputs'])
                    for identity in rule['checks']}

        for reference in fixture_references:
            self.assertIn(fixture_regression, selected(reference), reference)
            self.assertTrue(any(selection.below(reference, item) for item in catalog['checks'][real_source]['inputs']), reference)
        self.assertIn('core-runtime', selected('scripts/repo/module-structure/dependencies.mjs'))
        for reference in ['scripts/future/imported-test-tool.mjs', 'apps/future/package.json',
                          'apps/future/tests/fixture.ts', 'infra/future/probe.ts']:
            self.assertTrue(any(selection.below(reference, item) for item in catalog['checks'][real_source]['inputs']), reference)
            self.assertNotIn(fixture_regression, selected(reference), reference)

        for reference in fixture_references:
            selected = {identity for rule in catalog['repository_inputs']
                        if any(selection.below(reference, item) for item in rule['inputs'])
                        for identity in rule['checks']}
            for identity in {real_source, fixture_regression}:
                with tempfile.TemporaryDirectory(prefix='workspace-import-input-') as directory:
                    root = Path(directory)
                    source = root / reference
                    source.parent.mkdir(parents=True)
                    source.write_text('independent first source')
                    inputs = set(catalog['checks'][identity]['inputs'])
                    before = selection.fingerprint(root, inputs)
                    source.write_text('independent changed source')
                    self.assertNotEqual(before, selection.fingerprint(root, inputs), (reference, identity))
                    omitted = {item for item in inputs if not selection.below(reference, item)}
                    missing_before = selection.fingerprint(root, omitted)
                    source.write_text('independent third source')
                    self.assertEqual(missing_before, selection.fingerprint(root, omitted))
        implementation = (ROOT / 'scripts/repo/module-structure/check.mjs').read_text()
        self.assertIn('workspaces = inspectWorkspaceDependencies(root)', implementation)
        self.assertIn('...workspaces.findings', implementation)
        wrapper = (ROOT / 'scripts/repo/module-structure/smoke-test.sh').read_text()
        self.assertIn('node --test scripts/repo/module-structure/dependencies-test.mjs', wrapper)
        self.assertNotIn('workspace-dependency-registry', json.dumps(catalog))

    def test_configuration_access_uses_the_existing_gate_and_policy_inputs(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        policy = '.agentic/03.product/standards/config-runtime-settings.md'
        identity = 'module-index-structure'
        self.assertIn(policy, catalog['checks'][identity]['inputs'])
        self.assertTrue(any(policy in rule['inputs'] and identity in rule['checks']
                            for rule in catalog['repository_inputs']))
        self.assertNotIn(policy, catalog['checks']['module-index-structure-regression']['inputs'])
        implementation = (ROOT / 'scripts/repo/module-structure/check.mjs').read_text()
        self.assertIn('const access = inspectConfigurationAccess(sources)', implementation)
        self.assertIn('...access.findings', implementation)
        self.assertNotIn('configuration-access-registry', json.dumps(catalog))

    def test_artifact_migration_owns_complete_existing_command_and_exact_inputs(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        check = catalog['checks']['harness-artifact-migration-regression']
        self.assertEqual(check['argv'], ['bash', 'scripts/01.harness/smoke-test-artifact-path-migration.sh'])
        self.assertEqual(check['owner'], 'harness.script.smoke-test-artifact-path-migration')
        self.assertEqual(check['stage'], 'local')
        self.assertEqual(check['boundary'], 'integration')
        self.assertEqual(check['evidence_class'], 'local-runtime')
        self.assertEqual(check['effects'], ['read-only', 'writes-files'])
        self.assertFalse(check['scope_inputs'])
        self.assertEqual(check['inputs'], [
            'scripts/01.harness/check-artifact-path-migration.sh',
            'scripts/01.harness/plan-artifact-path-migration.sh',
            'scripts/01.harness/smoke-test-artifact-path-migration.sh'])
        self.assertEqual(check['runtime'], {'tools': ['bash', 'git'], 'node_packages': [],
            'environment': ['PATH', 'LANG', 'LC_ALL', 'TMPDIR']})
        self.assertFalse(selection.validate_check(ROOT, 'harness-artifact-migration-regression', check))
        self.assertNotIn('harness-artifact-migration-regression', catalog['checks']['check-selection-regression']['members'])
        driver = (ROOT / check['argv'][1]).read_text()
        for child in ('plan-artifact-path-migration.sh', 'check-artifact-path-migration.sh'):
            self.assertIn('bash "$SOURCE_ROOT/scripts/01.harness/' + child + '"', driver)
        reviews = json.loads((ROOT / 'scripts/repo/diagnostic-coverage/reviews.v1.json').read_text())['reviews']
        review = next(row for row in reviews if row['owner'] == 'harness-artifact-migration-diagnostics')
        self.assertEqual(review['checks'], ['harness-artifact-migration-regression'])
        self.assertEqual(review['tests'], ['scripts/01.harness/smoke-test-artifact-path-migration.sh'])
        self.assertEqual([source['path'] for source in review['sources']], check['inputs'][:2])

    def test_chat_export_and_metrics_own_exact_standalone_commands_inputs_and_runtime(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        checks = catalog['checks']
        common_environment = ['PATH', 'LANG', 'LC_ALL', 'NODE_OPTIONS', 'NODE_PATH', 'TMPDIR']
        metrics_environment = ['CHAT_COST_PROFILE', 'CHAT_COST_PRICING_FILE', 'CHAT_TRANSCRIPT_PROVIDER',
            'CHAT_TRANSCRIPT_PATH', 'CHAT_TRANSCRIPT_BYTES', 'CHAT_TRANSCRIPT_SOURCE', 'CHAT_TRANSCRIPT_METRICS_MODE',
            'TRANSCRIPT_PROVIDER', 'TRANSCRIPT_PATH', 'TRANSCRIPT_BYTES', 'TRANSCRIPT_SOURCE',
            'CODEX_SESSION_LOG_PATH', 'LLM_WORKBENCH_TRANSCRIPT_PROVIDER', 'ESTIMATED_CHAT_TOKENS',
            'ALLOW_MISSING_CHAT_TRANSCRIPT_METRICS']
        expected = {
            'chat-export-regression': ('chat-export', 'scripts/00.chat/export/smoke-test.sh', {
                'scripts/repo/check-selection/smoke-test.sh', 'scripts/00.chat/export/smoke-test.sh',
                'scripts/00.chat/export/create-worktree-bundle/script.js',
                'scripts/00.chat/export/worktree/script.sh', 'scripts/00.chat/export/worktree-diff/script.sh',
                'bin/llm-workbench.js', 'bin/llm-workbench-ownership.js', 'package.json'}, common_environment),
            'chat-commit-metrics-regression': ('chat-commit-metrics', 'scripts/00.chat/session-log/record-chat-commit/smoke-test.sh', {
                'scripts/repo/check-selection/smoke-test.sh',
                'scripts/00.chat/session-log/record-chat-commit/smoke-test.sh',
                'scripts/00.chat/session-log/record-chat-commit/script.sh',
                'scripts/00.chat/session-log/paths/lib.sh',
                'scripts/00.chat/transcript/discover-codex-session-log/script.sh',
                'scripts/00.chat/metrics/estimate-chat-cost/script.js',
                'scripts/00.chat/metrics/data/chat-pricing.json'}, common_environment + metrics_environment),
        }
        wrapper = (ROOT / 'scripts/repo/check-selection/smoke-test.sh').read_text()
        self.assertEqual(selection.LOCAL_EFFECTS, {'read-only', 'writes-files'})
        for identity, (unit, child, inputs, environment) in expected.items():
            with self.subTest(identity=identity):
                check = checks[identity]
                self.assertEqual(check['argv'], ['bash', 'scripts/repo/check-selection/smoke-test.sh', '--unit', unit])
                self.assertEqual(check['owner'], 'repo.test.check-selection.wrapper')
                self.assertEqual(check['stage'], 'local')
                self.assertEqual(check['boundary'], 'integration')
                self.assertEqual(check['evidence_class'], 'local-runtime')
                self.assertEqual(check['effects'], ['read-only', 'writes-files'])
                self.assertFalse(check['scope_inputs'])
                self.assertEqual(set(check['inputs']), inputs)
                self.assertEqual(len(check['inputs']), len(inputs))
                self.assertEqual(check['runtime'], {'tools': ['bash', 'node', 'git'], 'node_packages': [],
                    'environment': environment, 'config_inputs': ['.node-version', '.nvmrc']})
                self.assertFalse(selection.validate_check(ROOT, identity, check))
                self.assertNotIn(identity, checks['check-selection-regression']['members'])
                self.assertEqual(wrapper.count(unit + ') exec bash ' + child + ' ;;'), 1)
                rules = [rule for rule in catalog['repository_inputs'] if identity in rule['checks']]
                self.assertEqual(len(rules), 1)
                self.assertEqual(set(rules[0]['inputs']), inputs)
                self.assertFalse(any(selection.below('platform/server/src/index.ts', ref) for ref in inputs))

    def test_alignment_suites_have_separate_actual_local_commands_and_input_closures(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        alignment = 'scripts/04.deploy/lifecycle/00-target-alignment/'
        expected = {
            'aws-runtime-alignment-regression': (
                'provider-adapters/aws/runtime-alignment', 'deploy.test.aws.runtime-alignment',
                {alignment + 'provider-adapters/aws/runtime-alignment',
                 'scripts/04.deploy/shared/postgresql-version.py',
                 'scripts/04.deploy/shared/provider-adapters/aws/foundation-checks.py',
                 'scripts/04.deploy/shared/provider-adapters/aws/response.py'}),
            'provider-condition-evidence-regression': (
                'validate-provider-condition-evidence', 'deploy.test.validate-provider-condition-evidence',
                {alignment + 'validate-provider-condition-evidence'}),
            'core-target-declaration-regression': (
                'core-platform-target-declaration', 'deploy.test.core-platform-target-declaration',
                {alignment.rstrip('/'), 'scripts/04.deploy/lifecycle/60-run',
                 'scripts/04.deploy/shared/provider-adapters/aws/cli.py',
                 'scripts/04.deploy/shared/provider-adapters/aws/response.py',
                 'scripts/04.deploy/shared/provider-adapters/aws/tasks.py',
                 'scripts/04.deploy/lifecycle/40-package/package-custody-receipt',
                 'scripts/04.deploy/shared/deployment-operation-diagnostics.py',
                 'scripts/repo/diagnostic-coverage/runtime_contract.py',
                 'platform/persistence/contracts/diagnostics.v1.json',
                 'infra/04.deploy/03.product/targets/kanbien-core-platform',
                 'infra/04.deploy/03.product/image/core-server/image-contract.yml',
                 'infra/04.deploy/03.product/image/core-server-persistence-observability-collector',
                 '.github/workflows/publish-kanbien-core-platform-core-server.yml',
                 '.github/workflows/publish-kanbien-core-platform-core-server-persistence.yml',
                 '.github/workflows/publish-kanbien-core-platform-observability-collector.yml'}),
        }
        for identity, (directory, owner, inputs) in expected.items():
            with self.subTest(identity=identity):
                check = checks[identity]
                self.assertEqual(check['argv'], ['bash', alignment + directory + '/smoke-test.sh'])
                self.assertEqual(check['owner'], owner)
                self.assertEqual(check['stage'], 'local')
                self.assertEqual(check['evidence_class'], 'local-runtime')
                self.assertEqual(check['effects'], ['read-only', 'writes-files'])
                self.assertFalse(check['scope_inputs'])
                self.assertEqual(set(check['inputs']), inputs)
                self.assertEqual(check['runtime'], checks['target-alignment-regression']['runtime'])
                self.assertFalse(selection.validate_check(ROOT, identity, check))
                self.assertNotIn(identity, checks['target-alignment-regression'].get('members', []))
        # Ordinary runtime implementation edits do not own these fixture suites.
        for source in ('scripts/04.deploy/shared/postgresql-version.py',
                       'scripts/04.deploy/shared/provider-adapters/aws/foundation-checks.py'):
            with self.subTest(shared_input=source), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                file = root / source; file.parent.mkdir(parents=True); file.write_text('first')
                inputs = set(checks['aws-runtime-alignment-regression']['inputs'])
                before = selection.fingerprint(root, inputs)
                file.write_text('changed')
                self.assertNotEqual(before, selection.fingerprint(root, inputs))
                omitted = inputs - {source}
                without = selection.fingerprint(root, omitted)
                file.write_text('changed again')
                self.assertEqual(without, selection.fingerprint(root, omitted))
        for identity in expected:
            self.assertFalse(any(selection.below('platform/server/src/index.ts', path)
                                 for path in checks[identity]['inputs']))

    def test_deployment_diagnostic_fixture_binds_actual_controller_and_catalog_dependencies(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        check = checks['deployment-operation-diagnostics-regression']
        run = 'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/'
        required = {
            run + name for name in ('run-administration/script.py', 'run-migration/script.py',
                'proof-receipts.py', 'rehearse-runtime-credential-lifecycle/script.py',
                'rehearse-observability-readiness/script.py', 'rehearse-server-replacement/script.py')
        } | {
            run + 'deployment-diagnostics/binding.py',
            run + 'deployment-diagnostics/tests/binding-test.py',
            'packages/core/contracts', 'apps/platform-smoke/contracts',
            'infra/04.deploy/03.product/entrypoints/contracts',
            'scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-restoration-verifier-surface/script.py'
        } | {'platform/' + name + '/contracts' for name in (
            'config', 'contracts', 'health', 'observability', 'persistence', 'runtime', 'security', 'server', 'workers')}
        self.assertLessEqual(required, set(check['inputs']))
        self.assertNotIn('platform', check['inputs'])
        self.assertFalse(selection.validate_check(ROOT, 'deployment-operation-diagnostics-regression', check))
        self.assertIn('infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml',
                      checks['shell-release-evidence-regression']['inputs'])

    def test_disposable_postgresql_proof_binds_actual_composition_dependencies(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        check = checks['postgresql-disposable-diagnostics']
        self.assertEqual(check['stage'], 'package')
        self.assertEqual(check['argv'], ['bash', 'scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/postgresql-integration-check.sh'])
        self.assertEqual(set(check['inputs']), {
            'platform/adapters/aws/persistence/postgresql', 'platform/persistence', 'packages/core',
            'platform/adapters/aws/queue/sqs',
            'platform/contracts', 'platform/security', 'platform/observability', 'apps/platform-smoke',
            'platform/config', 'platform/health', 'platform/runtime', 'platform/server', 'platform/workers',
            'platform/testing', 'apps/entity-smoke',
            'infra/04.deploy/03.product/entrypoints/entity-smoke/postgresql.ts',
            'infra/04.deploy/03.product/entrypoints/entity-smoke/runtime.ts',
            'infra/04.deploy/03.product/entrypoints/entity-smoke/configuration.ts',
            'infra/04.deploy/03.product/entrypoints/entity-smoke/diagnostics.ts',
            'infra/04.deploy/03.product/entrypoints/entity-smoke/verification.ts',
            'infra/04.deploy/03.product/entrypoints/entity-smoke/proof-facts.ts',
            'infra/04.deploy/03.product/entrypoints/entity-smoke/administration.ts',
            'infra/04.deploy/03.product/entrypoints/entity-smoke/preflight.ts',
            'infra/04.deploy/03.product/entrypoints/shared/persistence/configuration.ts',
            'infra/04.deploy/03.product/entrypoints/shared/persistence/configuration-implementation.ts',
            'infra/04.deploy/03.product/entrypoints/shared/persistence/operation-diagnostics.ts',
            'infra/04.deploy/03.product/entrypoints/shared/persistence/scheduling-administration.ts',
            'infra/04.deploy/03.product/entrypoints/shared/persistence/role-credential.ts',
            'infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-administration.main.ts',
            'infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-runtime-credential.ts',
            'infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-iam-authentication.ts',
            'infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-postgresql.ts',
            'infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-scheduling.app.ts',
            'infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.app.ts',
            'infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-diagnostics.ts',
            'infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-persistence.ts',
            'infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-operation-diagnostics.ts',
            'infra/04.deploy/03.product/entrypoints/kanbien-platform-configuration-diagnostics.ts',
            'package.json', 'package-lock.json',
            'scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/postgresql-integration-check.sh'})
        self.assertEqual(check['effects'], ['network', 'writes-files'])
        self.assertEqual(check['owner'], 'deploy.test.postgresql-disposable-connection-diagnostics')
        self.assertFalse(selection.validate_check(ROOT, 'postgresql-disposable-diagnostics', check))
        local = checks['postgresql-connection-diagnostics']
        self.assertEqual(local['argv'], ['bash', 'scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/postgresql-diagnostics-check.sh'])
        self.assertEqual(set(local['inputs']), {
            'platform/adapters/aws/persistence/postgresql', 'platform/persistence', 'packages/core',
            'platform/contracts', 'platform/security', 'platform/observability',
            'package.json', 'package-lock.json',
            'scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/postgresql-diagnostics-check.sh'})
        self.assertEqual(local['stage'], 'local')
        self.assertFalse(selection.validate_check(ROOT, 'postgresql-connection-diagnostics', local))

    def test_harness_index_owns_actual_complete_command_and_input_closure(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        identity = 'harness-index-regression'
        check = checks[identity]
        self.assertEqual(check['argv'], ['bash', 'scripts/repo/check-selection/smoke-test.sh', '--unit', 'harness-index'])
        self.assertEqual(check['owner'], 'repo.test.check-selection.wrapper')
        self.assertEqual(check['stage'], 'local')
        self.assertEqual(check['evidence_class'], 'local-runtime')
        self.assertEqual(check['effects'], ['read-only', 'writes-files'])
        self.assertFalse(check['scope_inputs'])
        self.assertEqual(set(check['inputs']), {
            'scripts/repo/check-selection/smoke-test.sh',
            'scripts/01.harness/artifact-metadata/generate-index',
            'scripts/01.harness/artifact-metadata/header_discovery.py',
            'scripts/01.harness/artifact-metadata/backfill-v2-headers',
            'scripts/01.harness/artifact-metadata/check-headers/script.sh',
            'scripts/01.harness/check-artifact-metadata-headers.sh',
            '.agentic/01.harness/artifact-metadata/examples/markdown.v2.md',
            '.agentic/01.harness/artifact-metadata/examples/yaml.v2.yml',
            'docs/02.rag-rulebook/rules/README.md',
            'docs/02.rag-rulebook/rules/concerns/mcp-server-deployment-architecture.yml',
            'docs/03.product/rules/core/layers/packages-core.yml'})
        self.assertEqual(check['runtime'], {
            'tools': ['bash', 'python3', 'git'], 'node_packages': [],
            'environment': ['PATH', 'LANG', 'LC_ALL', 'PYTHONPATH', 'PYTHONHOME',
                            'PYTHONHASHSEED', 'PYTHONDONTWRITEBYTECODE', 'RAG_REPO_ROOT', 'RAG_SOURCE_COMMIT_SHA'],
            'config_inputs': ['.python-version', 'pyproject.toml', 'requirements.txt']})
        self.assertFalse(selection.validate_check(ROOT, identity, check))
        self.assertNotIn(identity, checks['check-selection-regression']['members'])
        wrapper = (ROOT / check['argv'][1]).read_text()
        self.assertEqual(wrapper.count('harness-index) exec bash scripts/01.harness/artifact-metadata/generate-index/smoke-test.sh ;;'), 1)
        driver = (ROOT / 'scripts/01.harness/artifact-metadata/generate-index/smoke-test.sh').read_text()
        self.assertEqual(driver.count('python3 -B "$repo_root/scripts/01.harness/artifact-metadata/backfill-v2-headers/diagnostic-test.py"'), 1)
        self.assertFalse(any(selection.below('platform/server/src/index.ts', ref) for ref in check['inputs']))

    def test_harness_validator_owns_actual_complete_command_and_input_closure(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        identity = 'harness-agent-validator-regression'
        check = checks[identity]
        self.assertEqual(check['argv'], ['bash', 'scripts/01.harness/agents/validate-harness-agents/diagnostic-test.sh'])
        self.assertEqual(check['owner'], 'harness.test.agents.validate-harness-agents.diagnostics')
        self.assertEqual(check['stage'], 'local')
        self.assertEqual(check['evidence_class'], 'local-runtime')
        self.assertEqual(check['effects'], ['read-only', 'writes-files'])
        self.assertFalse(check['scope_inputs'])
        self.assertEqual(set(check['inputs']), {
            'scripts/01.harness/agents/validate-harness-agents',
            'scripts/01.harness/metrics/compare-task-token-consumption',
            '.agentic/01.harness/agents',
            *('.agentic/01.harness/templates/' + name for name in [
                'agent-review-report.md', 'agent-scorecard.yml', 'agent-scorecard.schema.yml',
                'agent-scorecard.example.yml', 'examples/cfo-token-efficiency-scorecard.yml']),
            *('.agentic/01.harness/workflows/' + name for name in [
                'run-agent-review.md', 'run-review-board.md', 'implement-backend-architecture-guideline.md']),
            '.agentic/01.harness/standards/agent-contracts.md',
            '.agentic/01.harness/manifest.yml', '.agentic/01.harness/README.md'})
        self.assertEqual(check['runtime'], {
            'tools': ['bash', 'node', 'git'],
            'node_packages': [],
            'environment': ['PATH', 'LANG', 'LC_ALL', 'NODE_OPTIONS', 'NODE_PATH'],
            'config_inputs': ['.node-version', '.nvmrc']})
        self.assertFalse(selection.validate_check(ROOT, identity, check))
        wrapper = (ROOT / check['argv'][1]).read_text()
        self.assertEqual(wrapper.count('exec node '), 1)
        self.assertIn('/diagnostic-test.js', wrapper)
        driver = (ROOT / 'scripts/01.harness/agents/validate-harness-agents/diagnostic-test.js').read_text()
        self.assertIn("const wrapper = path.join(__dirname, 'script.sh');", driver)
        self.assertIn("spawnSync('bash', [wrapper, ...args]", driver)
        self.assertIn("run('existing complete internal fixtures')", driver)
        self.assertIn("run('restored complete internal fixtures')", driver)
        self.assertFalse(any(selection.below('platform/server/src/index.ts', ref) for ref in check['inputs']))

    def test_target_controls_and_budget_own_actual_complete_local_commands(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        base = 'scripts/04.deploy/lifecycle/'
        cases = {
            'bootstrap-target-controls-regression': (
                base + '50-deploy/targets/kanbien-core-platform/bootstrap-runtime',
                'deploy.test.kanbien-core-platform.target-controls',
                ['release-contract/smoke-test.sh', 'deployment-cli-regression.py',
                 'rehearse-accepted-workload-replacement/smoke-test.sh',
                 'rehearse-private-verifier-fault/smoke-test.sh',
                 'verify-delivery-role-access/smoke-test.py'],
                {base + '50-deploy/targets/kanbien-core-platform/bootstrap-runtime',
                 base + '60-run/targets/kanbien-core-platform/bootstrap-runtime',
                 base + '00-target-alignment',
                 *(base + '60-run/' + name for name in ['validate-active-workload-health-recovery',
                    'validate-health-failure-and-recovery-declaration', 'validate-persistence-diagnostic-mapping',
                    'validate-acceptance-route', 'promote-accepted-scope', 'release-succession']),
                 base + '40-package/package-custody-receipt',
                 'scripts/04.deploy/shared/provider-adapters/aws/cli.py',
                 'scripts/04.deploy/shared/provider-adapters/aws/response.py',
                 'scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py',
                 'scripts/04.deploy/shared/deployment-operation-diagnostics.py',
                 'scripts/repo/diagnostic-coverage/runtime_contract.py',
                 'platform/persistence/contracts/diagnostics.v1.json',
                 '.agentic/04.deploy/60-run/schemas', 'infra/04.deploy/03.product/image',
                 'infra/04.deploy/03.product/entrypoints', 'infra/04.deploy/03.product/targets/kanbien-core-platform'}),
            'foundation-budget-regression': (
                base + '50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget',
                'deploy.test.kanbien-core-platform.provision-target-budget',
                ['recovery-test.py', 'RecoveryCli.test_budget_lost_response_resumes_exact_operation'],
                {base + '50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget',
                 base + '00-target-alignment/declaration-coverage/script.py',
                 base + '00-target-alignment/provider-adapters/aws/preparation-inputs.py',
                 'scripts/04.deploy/shared/postgresql-version.py',
                 'scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py',
                 'scripts/04.deploy/shared/provider-adapters/aws/foundation-checks.py',
                 'infra/04.deploy/03.product/targets/kanbien-core-platform/10-foundation/budget-control.yml',
                 'scripts/04.deploy/shared/provider-adapters/aws/recovery-test.py',
                 'scripts/04.deploy/shared/provider-adapters/aws/response.py',
                 'scripts/04.deploy/legacy/kanbien-staging/shared/provider-adapters/aws/cognito-provisioning.py',
                 'infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/foundation.yml'}),
        }
        for identity, (directory, owner, fixtures, inputs) in cases.items():
            with self.subTest(identity=identity):
                check = checks[identity]
                self.assertEqual(check['argv'], ['bash', directory + '/smoke-test.sh'])
                self.assertEqual(check['owner'], owner)
                self.assertEqual(check['stage'], 'local')
                self.assertEqual(check['evidence_class'], 'local-runtime')
                self.assertEqual(check['effects'], ['read-only', 'writes-files'])
                self.assertFalse(check['scope_inputs'])
                self.assertEqual(set(check['inputs']), inputs)
                self.assertEqual(check['runtime'], checks['target-alignment-regression']['runtime'])
                self.assertFalse(selection.validate_check(ROOT, identity, check))
                wrapper = (ROOT / check['argv'][1]).read_text()
                for fixture in fixtures:
                    self.assertEqual(wrapper.count(fixture), 1, (identity, fixture))
        self.assertFalse(any(selection.below('platform/server/src/index.ts', ref)
                             for identity in cases for ref in checks[identity]['inputs']))

    def test_delivery_access_suite_and_package_fixture_dependencies_are_real_inputs(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        check = checks['delivery-access-contract-regression']
        base = 'scripts/04.deploy/lifecycle/40-package/'
        self.assertEqual(check['argv'], ['bash', base + 'validate-delivery-access-contract/smoke-test.sh'])
        self.assertEqual(check['owner'], 'deploy.test.validate-delivery-access-contract')
        self.assertEqual(check['stage'], 'local')
        self.assertEqual(check['evidence_class'], 'local-runtime')
        self.assertEqual(check['effects'], ['read-only', 'writes-files'])
        self.assertFalse(check['scope_inputs'])
        self.assertEqual(set(check['inputs']), {
            'scripts/04.deploy/shared/safe-command-diagnostics.sh',
            base + 'validate-delivery-access-contract', base + 'provider-adapters/aws/iam-policy-coverage',
            base + 'targets/kanbien-core-platform/core-server-package-custody/validate-delivery-access',
            base + 'targets/kanbien-core-platform/core-server-persistence-package-custody/validate-delivery-access'})
        self.assertFalse(selection.validate_check(ROOT, 'delivery-access-contract-regression', check))
        package = checks['package-custody-regression']
        wrapper = (ROOT / package['argv'][1]).read_text()
        for fixture in ['qualification-test.py', 'disposable-cleanup-test.py', 'ecr-scan-test.py']:
            self.assertIn(fixture, wrapper)
        # These are actually read/executed by existing fixtures, not a broad
        # platform dependency guessed from the directory's name.
        for path in [base + 'build-core-server-image/script.sh',
                     base + 'qualify-retained-persistence-rollback-image/script.sh',
                     'scripts/04.deploy/shared/safe-command-diagnostics.sh',
                     'scripts/04.deploy/shared/provider-adapters/docker/disposable-cleanup.py',
                     'scripts/04.deploy/shared/provider-adapters/aws/ecr-scan.py',
                     'scripts/04.deploy/legacy/kanbien-staging/verify-platform-shell-deployment-workflow/script.sh',
                     'platform/server/src/index.ts', 'packages/core/src/index.ts']:
            self.assertTrue(any(selection.below(path, ref) for ref in package['inputs']), path)
        self.assertTrue({'python3', 'node', 'typescript'} <= set(package['runtime']['tools']))
        self.assertIn('typescript', package['runtime']['node_packages'])
        # The payload fixture reads the actual Dockerfile COPY closure, so its
        # source identity must invalidate proof when an imported file is omitted.
        self.assertIn('infra/04.deploy/03.product/image/core-server-persistence/Dockerfile',
                      checks['persistence-payload-regression']['inputs'])

    def test_dynamodb_persistence_owns_complete_adapter_command_and_actual_inputs(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        check = checks['dynamodb-persistence-runtime']
        self.assertEqual(check['argv'], ['bash', 'scripts/repo/diagnostic-coverage/verify.sh', '--unit', 'dynamodb-persistence'])
        wrapper = (ROOT / 'scripts/repo/diagnostic-coverage/verify.sh').read_text()
        self.assertIn('  dynamodb-persistence) run_npm --ignore-scripts run platform:adapter:aws:persistence:dynamodb:check ;;', wrapper.splitlines())
        self.assertEqual(check['stage'], 'local')
        self.assertEqual(check['evidence_class'], 'local-runtime')
        self.assertFalse(check['scope_inputs'])
        self.assertEqual(check['effects'], ['writes-files'])
        self.assertEqual(set(check['inputs']), {'scripts/repo/diagnostic-coverage/verify.sh', 'packages/core', 'platform/persistence',
            'platform/adapters/aws/persistence/dynamodb', 'package.json', 'package-lock.json'})
        script = json.loads((ROOT / 'package.json').read_text())['scripts']['platform:adapter:aws:persistence:dynamodb:check']
        self.assertEqual(script.split(' && '), ['npm run platform:adapter:aws:persistence:dynamodb:' + name
            for name in ['typecheck', 'build', 'test', 'boundary']])
        self.assertFalse(selection.validate_check(ROOT, 'dynamodb-persistence-runtime', check))

    def test_ecs_runtime_uses_existing_complete_adapter_command_and_inputs(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        check = checks['ecs-fargate-runtime']
        self.assertEqual(check['argv'], ['bash', 'scripts/repo/diagnostic-coverage/verify.sh', '--unit', 'ecs-fargate'])
        self.assertEqual(check['stage'], 'local')
        self.assertEqual(check['evidence_class'], 'local-runtime')
        self.assertFalse(check['scope_inputs'])
        self.assertEqual(check['effects'], ['writes-files'])
        expected = {'packages/core', 'platform/contracts', 'platform/config', 'platform/health',
                    'platform/observability', 'platform/runtime', 'platform/security', 'platform/server',
                    'platform/testing', 'platform/adapters/aws/runtime/ecs-fargate', 'package.json', 'package-lock.json',
                    'scripts/repo/diagnostic-coverage/verify.sh'}
        self.assertEqual(set(check['inputs']), expected)
        script = json.loads((ROOT / 'package.json').read_text())['scripts']['platform:adapter:aws:runtime:ecs-fargate:check']
        self.assertEqual(script.split(' && '), ['npm run platform:adapter:aws:runtime:ecs-fargate:' + name
                         for name in ['typecheck', 'build', 'test', 'boundary']])
        self.assertFalse(selection.validate_check(ROOT, 'ecs-fargate-runtime', check))

    def test_sqs_queue_owns_complete_adapter_command_and_actual_inputs(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        check = checks['sqs-queue-runtime']
        self.assertEqual(check['argv'], ['bash', 'scripts/repo/diagnostic-coverage/verify.sh', '--unit', 'sqs-queue'])
        wrapper = (ROOT / 'scripts/repo/diagnostic-coverage/verify.sh').read_text()
        self.assertIn('  sqs-queue) run_npm --ignore-scripts run platform:adapter:aws:queue:sqs:check ;;', wrapper.splitlines())
        self.assertEqual(check['stage'], 'local')
        self.assertEqual(check['evidence_class'], 'local-runtime')
        self.assertFalse(check['scope_inputs'])
        self.assertEqual(check['effects'], ['writes-files'])
        self.assertEqual(set(check['inputs']), {'scripts/repo/diagnostic-coverage/verify.sh', 'packages/core',
            'platform/adapters/aws/queue/sqs', 'package.json', 'package-lock.json'})
        script = json.loads((ROOT / 'package.json').read_text())['scripts']['platform:adapter:aws:queue:sqs:check']
        self.assertEqual(script.split(' && '), ['npm run platform:adapter:aws:queue:sqs:' + name
            for name in ['typecheck', 'build', 'test', 'boundary']])
        self.assertFalse(selection.validate_check(ROOT, 'sqs-queue-runtime', check))

    def test_scheduling_proofs_are_local_owned_and_select_their_actual_sources(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        checks = catalog['checks']
        adapter, composition = checks['lambda-runtime'], checks['scheduling-composition']
        self.assertEqual(adapter['argv'], ['bash', 'scripts/repo/diagnostic-coverage/verify.sh', '--unit', 'lambda'])
        self.assertEqual(composition['argv'], ['bash', 'scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh', '--scheduling'])
        for identity, check in [('lambda-runtime', adapter), ('scheduling-composition', composition)]:
            self.assertEqual(check['effects'], ['writes-files'])
            self.assertEqual(check['stage'], 'local')
            self.assertFalse(selection.validate_check(ROOT, identity, check))
        context = selection.workspace_context.load(ROOT, {'lambda-runtime': adapter}, selection.coverage.safe_path)['checks']['lambda-runtime']
        self.assertTrue({'packages/core', 'platform/persistence', 'platform/adapters/aws/runtime/lambda'} <= set(context['references']))
        self.assertNotIn('platform/adapters/aws/runtime/ecs-fargate', context['references'])
        rules = [rule['inputs'] for rule in catalog['repository_inputs'] if 'scheduling-composition' in rule['checks']]
        self.assertEqual(rules, [composition['inputs']])
        cases = {'lambda-runtime': 'platform/adapters/aws/runtime/lambda/src/dispatch.ts',
                 'scheduling-composition': 'infra/04.deploy/03.product/entrypoints/shared/scheduling/composition.ts'}
        for identity, source in cases.items():
            self.assertTrue(any(selection.below(source, path) for path in checks[identity]['inputs']))
            stale = copy.deepcopy(checks[identity])
            stale['inputs'] = [path for path in stale['inputs'] if not selection.below(source, path)]
            self.assertFalse(any(selection.below(source, path) for path in stale['inputs']))

    def test_scheduler_preparation_binds_direct_real_consumers(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        entrypoints = 'infra/04.deploy/03.product/entrypoints/'
        templates = 'infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/'
        provider_dependencies = [
            'scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/lambda-runtime-configuration.py',
            'scripts/04.deploy/lifecycle/40-package/package-custody-receipt/validate.py',
            'scripts/04.deploy/lifecycle/40-package/package-custody-receipt/github-artifact.py',
            'scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/publication.py',
            'scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/qualification.py',
            'scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/smoke-test.py',
            'scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/script.py',
            'scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/admission.py',
            'scripts/04.deploy/operational-realization-gate/script.py',
        ]
        cases = {
            '.agentic/04.deploy/20-build/schemas/runnable-program-contract.v1.schema.yml': 'core-dependency-boundary',
            **{entrypoints + scope + '-scheduling-' + purpose + '.tsconfig.json': 'core-dependency-boundary'
               for scope in ('kanbien-core-server-persistence', 'kanbien-entity-smoke') for purpose in ('dispatch', 'worker')},
            **{entrypoints + 'contracts/' + name + '-diagnostics.v1.json': 'diagnostic-catalog-readers'
               for name in ('kanbien-core-server-acceptance', 'scheduling-target')},
            **{templates + name + '.yml': 'persistence-provider-regression' for name in ('scheduling', 'scheduling-network')},
            **{path: 'persistence-provider-regression' for path in provider_dependencies},
            'apps/entity-smoke/features/test-entity/domain/services/purge-expired-test-entities.ts': 'postgresql-disposable-diagnostics',
            'platform/testing/src/index.ts': 'postgresql-disposable-diagnostics',
            entrypoints + 'entity-smoke/postgresql.ts': 'postgresql-disposable-diagnostics',
            **{entrypoints + 'entity-smoke/' + name + '.ts': 'postgresql-disposable-diagnostics'
               for name in ('runtime', 'configuration', 'diagnostics', 'verification', 'proof-facts')},
            **{entrypoints + 'shared/persistence/' + name + '.ts': 'postgresql-disposable-diagnostics'
               for name in ('configuration', 'configuration-implementation', 'operation-diagnostics')},
            'platform/adapters/aws/queue/sqs/src/lambda-batch.ts': 'postgresql-disposable-diagnostics',
            entrypoints + 'kanbien-core-server-persistence-postgresql.ts': 'postgresql-disposable-diagnostics',
            entrypoints + 'kanbien-core-server-persistence-scheduling.app.ts': 'postgresql-disposable-diagnostics',
            entrypoints + 'kanbien-core-server-persistence-diagnostics.ts': 'postgresql-disposable-diagnostics',
        }
        for source, owner in cases.items():
            with self.subTest(source=source, owner=owner):
                self.assertTrue((ROOT / source).is_file())
                rules = [rule for rule in catalog['repository_inputs'] if owner in rule['checks']]
                self.assertTrue(any(selection.below(source, path) for rule in rules for path in rule['inputs']))
                inputs = catalog['checks'][owner]['inputs']
                self.assertTrue(any(selection.below(source, path) for path in inputs))
                # An incidental/full-graph consumer cannot replace either edge.
                removed = [path for path in inputs if not selection.below(source, path)]
                self.assertFalse(any(selection.below(source, path) for path in removed))
                if owner == 'persistence-provider-regression':
                    with tempfile.TemporaryDirectory(prefix='scheduler-provider-input-') as directory:
                        root = Path(directory); dependency = root / source
                        dependency.parent.mkdir(parents=True); dependency.write_text('original')
                        before = selection.fingerprint(root, inputs)
                        dependency.write_text('changed')
                        self.assertNotEqual(before, selection.fingerprint(root, inputs))
                        before = selection.fingerprint(root, removed)
                        dependency.write_text('changed-again')
                        self.assertEqual(before, selection.fingerprint(root, removed))
        self.assertEqual(catalog['checks']['postgresql-disposable-diagnostics']['stage'], 'package')
        self.assertEqual(catalog['checks']['persistence-provider-regression']['stage'], 'local')
        program = (ROOT / 'scripts/04.deploy/lifecycle/20-build/runnable-program-contract/build-inputs-test.mjs').read_text()
        self.assertIn('managed handler projects isolate each declared scheduling program', program)
        self.assertIn('JSON.parse(readFileSync(join(root, selected.project)', program)
        provider = (ROOT / catalog['checks']['persistence-provider-regression']['argv'][1]).read_text()
        helper_path = 'scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/smoke-test.py'
        self.assertIn(helper_path, provider)
        self.assertIn('scheduling_safety.check_templates()', provider)
        self.assertIn('Source safety only; the reusable scheduler owner retains these assertions.', provider)
        helper = (ROOT / helper_path).read_text()
        self.assertIn('def check_templates(', helper)
        self.assertIn('M.ROOT / binding["template"]', helper)
        self.assertIn('M.ROOT / binding["network_template"]', helper)

    def test_package_units_preserve_original_command_membership_and_audited_inputs(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        members = catalog['diagnostic-base-runtime']['members']
        expected = {'catalog', 'core', 'contracts', 'config', 'security', 'observability', 'health', 'persistence', 'runtime', 'testing', 'workers', 'smoke-app'}
        self.assertEqual({catalog[identity]['argv'][-1] for identity in members}, expected)
        self.assertEqual(len(members), len(expected))
        for identity in members:
            if identity == 'diagnostic-catalog-readers': continue
            check = catalog[identity]
            self.assertNotIn('scripts/04.deploy', check['inputs'])
            self.assertNotIn('platform', check['inputs'])
            self.assertTrue(any((ROOT / path / 'tests').is_dir() for path in check['inputs']))
            self.assertIn('typescript', check['runtime']['node_packages'])


    def test_real_aggregate_contracts_cover_child_inputs_and_runtime(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        for aggregate, children in {
            'diagnostic-runtime-contracts': ['diagnostic-base-runtime', 'platform-server-runtime', 'kanbien-platform-runtime'],
            'shell-package-source': ['platform-server-runtime', 'kanbien-platform-runtime', 'platform-shell-payload'],
        }.items():
            parent = checks[aggregate]
            self.assertEqual(parent['members'], children)
            for child in children:
                leaf = checks[child]
                self.assertFalse(selection.validate_check(ROOT, child, leaf))
                for field in ['tools', 'node_packages', 'environment']:
                    self.assertTrue(set(leaf['runtime'][field]) <= set(parent['runtime'][field]), (aggregate, child, field))
                for reference in leaf['runtime']['config_inputs']:
                    self.assertTrue(reference in parent['runtime']['config_inputs'] or reference in parent['inputs'])


    def test_bootstrap_payload_regression_is_a_local_owned_check(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        check = catalog['checks']['bootstrap-payload-regression']
        self.assertEqual(check['stage'], 'local')
        self.assertEqual(check['boundary'], 'integration')
        self.assertEqual(check['effects'], ['writes-files'])
        self.assertEqual(check['applicability']['program_id'], 'kanbien-core-server')
        self.assertEqual(check['argv'], ['bash', 'scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/payload-fixture-test.sh'])
        self.assertIn('scripts/04.deploy/lifecycle/40-package/build-core-server-image', check['inputs'])
        for path in [
            'scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs',
            'scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/runtime-contract.mjs',
            'scripts/04.deploy/legacy/kanbien-staging/build-platform-shell-image/prepare-runtime.mjs',
        ]:
            self.assertIn(path, check['inputs'])
        wrapper = (ROOT / check['argv'][1]).read_text()
        self.assertEqual(wrapper.count('python3 -B scripts/04.deploy/lifecycle/40-package/build-core-server-image/runtime-preparation-diagnostic-test.py'), 1)
        self.assertIn('platform', check['inputs'])
        self.assertIn('packages/core', check['inputs'])


    def test_every_registered_check_has_a_valid_execution_contract(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        errors = [error for key, check in catalog['checks'].items()
                  for error in selection.validate_check(ROOT, key, check)]
        self.assertEqual(errors, [])


    def test_existing_persistence_scope_has_coverage(self):
        catalog = selection.coverage.document(ROOT / 'scripts/repo/check-selection/checks.yml')
        report = selection.coverage.inspect(ROOT / 'infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml', ROOT, catalog)
        self.assertEqual(report['verdict'], 'covered', report)
        self.assertIn('persistence-composition', report['required_checks'])

    def test_candidate_preparation_selects_its_direct_persistence_proof(self):
        catalog = ROOT / 'scripts/repo/check-selection/checks.yml'
        args = argparse.Namespace(root=ROOT, catalog=catalog,
            paths=['scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.sh'],
            staged=False, all=False, stage='local', boundary='integration', ci=True,
            changed_only=True, execute_local=False, evidence=None, json=True)
        report = selection.plan(args)
        self.assertEqual(report['verdict'], 'planned', report.get('findings'))
        selected = {check['check_id'] for check in report['checks']}
        self.assertIn('persistence-provider-regression', selected)
        # Metadata links this command to its candidate workflow, whose declared
        # consumer checks include diagnostics. CI uses the same full consumer
        # analysis as other integration callers, not a direct-input exemption.
        self.assertIn('deployment-operation-diagnostics-regression', selected)

    def test_development_scope_selection_requires_a_direct_proof_input(self):
        """A scope trigger cannot turn every scope proof into editing feedback."""
        catalog = ROOT / 'scripts/repo/check-selection/checks.yml'
        original_fingerprint = selection.fingerprint
        def planning_fingerprint(root, references, *, exclude=frozenset()):
            if references == {'scripts/repo/check-selection/checks.yml'}:
                return original_fingerprint(root, references, exclude=exclude)
            import hashlib
            return hashlib.sha256(json.dumps(sorted(set(references) - set(exclude))).encode()).hexdigest()
        cases = [
            ('scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/entity-smoke-package-custody/publication.py',
             {'entity-smoke-publication-contract'},
             {'entity-smoke-runtime', 'entity-smoke-composition-suite', 'entity-smoke-acceptance-controls'}),
        ]
        with patch.object(selection, 'fingerprint', side_effect=planning_fingerprint), patch.object(selection, 'runtime_identity', return_value={'selection_fixture': 'no-execution'}):
            for path, required, forbidden in cases:
                with self.subTest(path=path):
                    args = argparse.Namespace(root=ROOT, catalog=catalog, paths=[path], staged=False,
                        all=False, stage='local', boundary='integration', ci=False, changed_only=False,
                        execute_local=False, evidence=None, json=True, development=True,
                        checks=None, aggregate_members=None, record_preparation=False,
                        require_preparation=False, task_paths=None, explain=False)
                    report = selection.plan(args)
                    self.assertEqual(report['verdict'], 'planned', report.get('findings'))
                    selected = {check['check_id'] for check in report['checks'] if check['status'] == 'pending'}
                    self.assertTrue(required <= selected, (path, required - selected))
                    self.assertFalse(forbidden & selected, (path, forbidden & selected))

    def test_development_scope_contract_change_retains_the_complete_scope_proof(self):
        """The direct-input rule must not weaken a changed scope declaration."""
        catalog = ROOT / 'scripts/repo/check-selection/checks.yml'
        original_fingerprint = selection.fingerprint
        def planning_fingerprint(root, references, *, exclude=frozenset()):
            if references == {'scripts/repo/check-selection/checks.yml'}:
                return original_fingerprint(root, references, exclude=exclude)
            import hashlib
            return hashlib.sha256(json.dumps(sorted(set(references) - set(exclude))).encode()).hexdigest()
        args = argparse.Namespace(root=ROOT, catalog=catalog,
            paths=['infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/00-declaration/declaration-contract.yml'],
            staged=False, all=False, stage='local', boundary='integration', ci=False,
            changed_only=False, execute_local=False, evidence=None, json=True,
            development=True, checks=None, aggregate_members=None,
            record_preparation=False, require_preparation=False, task_paths=None,
            explain=False)
        with patch.object(selection, 'fingerprint', side_effect=planning_fingerprint), patch.object(selection, 'runtime_identity', return_value={'selection_fixture': 'no-execution'}):
            report = selection.plan(args)
        self.assertEqual(report['verdict'], 'planned', report.get('findings'))
        observed = {check['check_id']: check for check in report['checks']}
        contract = yaml.safe_load((ROOT / args.paths[0]).read_text())
        required = {identity for requirement in contract['change_impact']['requirements']
                    for identity in requirement['local_proofs']}
        self.assertTrue(required <= set(observed), required - set(observed))
        selected = {identity for identity, check in observed.items() if check['status'] == 'pending'}
        self.assertTrue({'entity-smoke-runtime', 'entity-smoke-acceptance-controls',
                         'entity-smoke-publication-contract'} <= selected)
        # All declared obligations remain visible above. The retained full
        # composition parent does not expand into its children merely because
        # the scope declaration changed during an editing-feedback request.
        self.assertEqual(observed['entity-smoke-composition']['status'], 'deferred')
        self.assertNotIn('entity-smoke-composition-suite', selected)
        self.assertNotIn('entity-smoke-infrastructure-route', selected)


    def test_actual_diagnostic_paths_select_focused_checks(self):
        """Direct promotion routing must not require a repository-wide graph.

        These cases assert declared changed-path ownership.  Running the full
        planner here repeats an unrelated source census four times and makes
        the check a delivery bottleneck without increasing the assertion's
        strength.  Full-impact graph behaviour is covered by its own fixtures.
        """
        catalog = ROOT / 'scripts/repo/check-selection/checks.yml'
        for paths, expected in [
            (['platform/adapters/aws/persistence/dynamodb/src/transactions.ts'], {'dynamodb-persistence-runtime'}),
            (['platform/adapters/aws/queue/sqs/src/worker.ts'], {'sqs-queue-runtime'}),
            (['platform/adapters/aws/persistence/postgresql/src/errors.ts', 'platform/adapters/aws/persistence/postgresql/tests/integration/postgresql-diagnostics-runtime.test.ts'], {'postgresql-connection-diagnostics', 'postgresql-disposable-diagnostics', 'persistence-composition'}),
            (['scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.py', '.agentic/04.deploy/schemas/deployment-operation-diagnostic.v1.schema.yml'], {'restore-connection-diagnostics', 'deployment-operation-diagnostics-regression'}),
        ]:
            args = argparse.Namespace(root=ROOT, catalog=catalog, paths=paths, staged=False, all=False,
                                      stage='local', boundary='integration', ci=True, changed_only=True,
                                      execute_local=False, evidence=None, json=True)
            report = selection.plan(args)
            self.assertEqual(report['verdict'], 'planned', report.get('findings'))
            selected = {check['check_id'] for check in report['checks']}
            self.assertTrue(expected <= selected, (paths, selected))
            self.assertNotIn('platform-shell-payload', selected, paths)
            if 'postgresql-disposable-diagnostics' in expected:
                engine = next(check for check in report['checks'] if check['check_id'] == 'postgresql-disposable-diagnostics')
                self.assertEqual(engine['stage'], 'package'); self.assertEqual(engine['evidence_class'], 'ci')
                image = next(check for check in report['checks'] if check['check_id'] == 'persistence-container')
                self.assertEqual(image['evidence_class'], 'container-qualification')
                self.assertNotEqual(engine['argv'], image['argv'])
            if paths[0].startswith('scripts/04.deploy'):
                self.assertNotIn('postgresql-connection-diagnostics', selected, 'report-only changes reuse unaffected adapter evidence')


    def test_selection_does_not_probe_unrelated_acceptance_commands(self):
        catalog = ROOT / 'scripts/repo/check-selection/checks.yml'
        calls = []
        original = selection.coverage.inspect

        def inspect(contract, root, catalog, *, probe_commands=True):
            calls.append(probe_commands)
            return original(contract, root, catalog, probe_commands=probe_commands)

        args = argparse.Namespace(root=ROOT, catalog=catalog,
            paths=['scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.py'],
            staged=False, all=False, stage='local', execute_local=False,
            evidence=None, json=True)
        with patch.object(selection.coverage, 'inspect', side_effect=inspect):
            selection.plan(args)
        self.assertTrue(calls)
        self.assertEqual(set(calls), {False})


    def test_local_runner_and_commit_hook_declare_write_effects(self):
        for path in ('scripts/repo/check-selection/script.sh', 'scripts/repo/commit-gates/script.sh', 'scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh'):
            self.assertIn('writes-files', selection.metadata(ROOT / path)['effects'])
        result = subprocess.run(['bash', 'scripts/01.harness/run-governed-script.sh', 'scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh'], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('approval-sensitive script requires --approved-action', result.stderr)


    def test_real_persistence_cannot_borrow_bootstrap_proofs_or_omit_composition(self):
        path = ROOT / 'infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml'
        original = selection.coverage.document
        contract = copy.deepcopy(original(path))
        requirement = contract['change_impact']['requirements'][0]
        requirement.update(local_proofs=['scope-inventory', 'runnable-program'], package_proofs=['bootstrap-container'], target_proofs=['bootstrap-target-alignment'], run_proofs=['bootstrap-acceptance'])
        with patch.object(selection.coverage, 'document', side_effect=lambda candidate: contract if candidate == path else original(candidate)):
            report = selection.coverage.inspect(path, ROOT, original(ROOT / 'scripts/repo/check-selection/checks.yml'))
        self.assertIn('requirement-check-subject-mismatch', self.codes(report))
        self.assertIn('scope-program-local-proof-missing', self.codes(report))


    def test_workload_specific_startup_conditions(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        for context, expected in [(['platform/observability/src/configuration.ts'], {'persistence-composition'}), (['infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.ts'], set()), (['services/new-independent/src/main.ts'], set())]:
            graph, findings = selection.verification_dependencies(checks, ['diagnostic-base-runtime'], context)
            self.assertFalse(findings)
            self.assertEqual(graph['diagnostic-base-runtime'] & {'persistence-composition', 'platform-shell-payload'}, expected)
        # The staging aggregate retains its own payload prerequisite when
        # deliberately requested; shared diagnostics no longer inherit it.
        graph, findings = selection.verification_dependencies(checks, ['shell-package-source'],
            ['infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.ts'])
        self.assertFalse(findings)
        self.assertIn('platform-shell-payload', graph['shell-package-source'])
        for member in ('platform-server-runtime', 'kanbien-platform-runtime'):
            self.assertIn('platform-shell-payload', graph[member])



    def test_component_assignment_preserves_original_methods_without_duplicates(self):
        import ast
        import mechanics_test
        import repository_contracts_test
        folder = ROOT / 'scripts/repo/check-selection'
        def names(module):
            suite = unittest.defaultTestLoader.loadTestsFromModule(module)
            def flatten(items):
                for item in items:
                    if isinstance(item, unittest.TestSuite): yield from flatten(item)
                    else: yield item
            tests = list(flatten(suite))
            ids = [case.id() for case in tests]
            self.assertEqual(len(ids), len(set(ids)))
            return {case._testMethodName for case in tests}
        mechanics = names(mechanics_test)
        repository = names(repository_contracts_test)
        self.assertFalse(mechanics & repository)
        discovered = []
        for path in folder.glob('*.py'):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_'):
                    self.assertIn(path.name, {'mechanics_test.py', 'repository_contracts_test.py'}, (path, node.name))
                    discovered.append(node.name)
        self.assertEqual(len(discovered), len(set(discovered)), "Physical test definitions must not shadow each other.")
        self.assertEqual(set(discovered), mechanics | repository, 'New executable tests must belong to a loaded collection.')

    def test_runner_aggregate_retains_exact_components_and_owner_obligations(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        wrapper = 'scripts/repo/check-selection/smoke-test.sh'
        compatibility = 'scripts/repo/check-selection/smoke-test.py'
        command = 'scripts/repo/check-selection/script.sh'
        commit_gate = 'scripts/repo/commit-gates/script.sh'
        preparation = 'scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh'
        self.assertEqual(selection.metadata(ROOT / wrapper)['used_by'], [
            {'id': 'repo.check-selection.catalog', 'path': 'scripts/repo/check-selection/checks.yml'},
            {'id': 'repo.test.check-selection', 'path': compatibility},
        ])
        # Registration must not turn this test launcher into every selector
        # caller's implementation; preserve the real selector/commit chain.
        graph = selection.consumer_graph(ROOT, [wrapper, compatibility, command, commit_gate, preparation])
        wrapper_consumers = selection.closure([wrapper], graph)
        self.assertIn(compatibility, wrapper_consumers)
        self.assertNotIn(preparation, wrapper_consumers)
        self.assertIn(preparation, selection.closure([command], graph))
        expected = {'check-selection-workspace-inputs', 'check-selection-mechanics', 'check-selection-repository-contracts', 'harness-lifecycle-metadata-regression', 'harness-header-regression', 'chat-session-preparation-regression', 'chat-local-merge-regression', 'chat-main-refresh-regression'}
        parent = checks['check-selection-regression']
        self.assertEqual(set(parent['members']), expected)
        self.assertEqual(len(parent['members']), len(expected))
        self.assertEqual(parent['inputs'], ['scripts/repo/check-selection'])
        self.assertEqual(checks['check-selection-mechanics']['runtime']['node_packages'], [])
        self.assertEqual(checks['check-selection-mechanics']['cadence'], 'deferred')
        self.assertEqual(checks['check-selection-promotion']['inputs'], ['scripts/repo/check-selection'])
        self.assertNotIn('cadence', checks['check-selection-promotion'])
        self.assertTrue({'scripts/repo/diagnostic-coverage/script.py',
                         'scripts/repo/diagnostic-coverage/script.sh'} <= set(checks['check-selection-mechanics']['inputs']))
        for excluded in ['platform', 'packages/core', 'docs', '.agentic', 'scripts/04.deploy']:
            self.assertNotIn(excluded, checks['check-selection-mechanics']['inputs'])
        for member in expected:
            child = checks[member]
            self.assertFalse(selection.validate_check(ROOT, member, child))
            for field in ['tools', 'environment', 'node_packages']:
                self.assertTrue(set(child['runtime'].get(field, [])) <= set(parent['runtime'].get(field, [])), (member, field))

    def test_actual_runtime_and_runner_changes_select_independent_proof(self):
        # These are real repository paths, catalog, metadata and review rules.
        # No test command executes. Runtime probing is already separately proved;
        # a bounded identity avoids re-hashing installed SDKs in each pure plan.
        catalog = ROOT / 'scripts/repo/check-selection/checks.yml'
        owners = {'harness-lifecycle-metadata-regression', 'harness-header-regression', 'chat-session-preparation-regression', 'chat-local-merge-regression', 'chat-main-refresh-regression'}
        cases = [
            ('apps/entity-smoke/features/test-entity/domain/services/update-test-entity.ts', {'entity-smoke-runtime', 'kanbien-platform-runtime'}, {'check-selection-mechanics'}),
            ('platform/adapters/aws/persistence/dynamodb/src/index.ts', {'dynamodb-persistence-runtime'}, {'check-selection-mechanics'}),
            ('platform/adapters/aws/persistence/postgresql/src/index.ts', {'postgresql-connection-diagnostics', 'postgresql-disposable-diagnostics'}, {'check-selection-mechanics'}),
            ('platform/adapters/aws/runtime/ecs-fargate/src/index.ts', {'ecs-fargate-runtime', 'check-selection-repository-contracts'}, {'check-selection-mechanics', 'chat-export-regression', 'chat-commit-metrics-regression', *owners}),
            ('platform/server/src/configuration/runtime.ts', {'platform-server-runtime', 'check-selection-repository-contracts'}, {'check-selection-mechanics', 'check-selection-regression', 'chat-export-regression', 'chat-commit-metrics-regression', *owners}),
            ('scripts/repo/check-selection/script.py', {'check-selection-promotion', 'check-selection-mechanics', 'check-selection-repository-contracts'}, {'check-selection-regression'}),
            ('scripts/repo/check-selection/checks.yml', {'check-selection-promotion'}, {'check-selection-mechanics', 'check-selection-repository-contracts', 'check-selection-regression'}),
            ('scripts/repo/diagnostic-coverage/smoke-test.py', {'diagnostic-catalog-readers'},
             {'diagnostic-adoption', 'diagnostic-runtime-contracts', 'core-runtime', 'platform-server-runtime',
              'kanbien-platform-runtime', 'entity-smoke-composition', 'persistence-composition'}),
            ('scripts/repo/diagnostic-coverage/tsconfig.json', {'diagnostic-catalog-readers'},
             {'diagnostic-runtime-contracts', 'core-runtime', 'platform-server-runtime', 'kanbien-platform-runtime'}),
            ('infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/10-workload-binding/workload-binding.yml',
             {'check-selection-promotion', 'check-selection-repository-contracts'}, {'check-selection-mechanics'}),
            ('scripts/00.chat/main-refresh/rehearse-refresh-from-main/smoke-test.sh', {'chat-main-refresh-regression', 'check-selection-repository-contracts'}, {'check-selection-regression', 'check-selection-mechanics'}),
            ('bin/llm-workbench.js', {'chat-export-regression'}, {'chat-commit-metrics-regression', 'check-selection-regression', 'check-selection-mechanics'}),
            ('bin/llm-workbench-ownership.js', {'chat-export-regression'}, {'chat-commit-metrics-regression', 'check-selection-regression', 'check-selection-mechanics'}),
            ('scripts/00.chat/export/create-worktree-bundle/script.js', {'chat-export-regression', 'check-selection-repository-contracts'}, {'chat-commit-metrics-regression', 'check-selection-regression', 'check-selection-mechanics'}),
            ('scripts/00.chat/metrics/estimate-chat-cost/script.js', {'chat-commit-metrics-regression', 'check-selection-repository-contracts'}, {'chat-export-regression', 'check-selection-regression', 'check-selection-mechanics'}),
        ]
        # A valid future baseline contains this split catalog. Simulate only its
        # git-show bytes: selection logic, current wiring and dependencies remain
        # real. Current task impact against HEAD is intentionally broader.
        original_git = selection.git
        def git(root, *arguments):
            if arguments == ('show', 'HEAD:scripts/repo/check-selection/checks.yml'):
                return catalog.read_text()
            return original_git(root, *arguments)
        original_fingerprint = selection.fingerprint
        def planning_fingerprint(root, references, *, exclude=frozenset()):
            if references == {'scripts/repo/check-selection/checks.yml'}:
                return original_fingerprint(root, references, exclude=exclude)
            # This test proves selection, not source-byte freshness. Preserve the
            # real catalog race guard, but don't hash every selected SDK/runtime
            # payload five times. Execution/cache regressions remain unmocked.
            import hashlib
            return hashlib.sha256(json.dumps(sorted(set(references) - set(exclude))).encode()).hexdigest()
        original_inspect = selection.coverage.inspect
        inspections = {}
        def inspect(contract, root, current_catalog, **options):
            key = (str(contract), str(root), json.dumps(current_catalog, sort_keys=True), tuple(sorted(options.items())))
            if key not in inspections:
                inspections[key] = original_inspect(contract, root, current_catalog, **options)
            return copy.deepcopy(inspections[key])
        # The independent physical census has its own command/fixtures and is
        # checked once in the final candidate plan. Repeating it for every pure
        # routing example adds no consumer-selection assertion.
        with patch.object(selection, 'delivery_inventory_required', return_value=False), \
             patch.object(selection.coverage, 'inspect', side_effect=inspect), \
             patch.object(selection, 'git', side_effect=git), patch.object(selection, 'runtime_identity', return_value={'pure_plan_fixture': 'no-execution'}), patch.object(selection, 'fingerprint', side_effect=planning_fingerprint):
            for path, required, forbidden in cases:
                with self.subTest(path=path):
                    args = argparse.Namespace(root=ROOT, catalog=catalog, paths=[path], staged=False, all=False,
                                              stage='local', boundary='integration', ci=True, changed_only=True,
                                              execute_local=False, evidence=None, json=True)
                    report = selection.plan(args)
                    self.assertEqual(report['verdict'], 'planned', report['findings'])
                    selected = {item['check_id'] for item in report['checks']}
                    required_now = {item['check_id'] for item in report['execution_policy']['checks']
                                    if item['decision'] == 'required-now'}
                    retained = {identity for identity in required
                                if yaml.safe_load(catalog.read_text())['checks'][identity].get('cadence', 'candidate') != 'candidate'}
                    later = {identity for identity in required
                             if yaml.safe_load(catalog.read_text())['checks'][identity]['stage'] != 'local'}
                    self.assertTrue(required <= selected, (required - selected, selected))
                    self.assertTrue(required - retained - later <= required_now,
                                    (required - retained - later - required_now, required_now))
                    self.assertTrue(later <= set(report['execution_policy']['later_stage_check_ids']))
                    self.assertFalse((forbidden | {'platform-shell-payload'}) & required_now,
                                     (forbidden | {'platform-shell-payload'}) & required_now)

    def test_foreign_imports_preserve_fixture_and_facade_without_launching_suites(self):
        import sys
        code = '''
import importlib.util, subprocess, sys
def forbidden(*args, **kwargs):
    raise AssertionError('Import must not launch a suite or child command')
subprocess.call = subprocess.run = subprocess.Popen = forbidden
spec = importlib.util.spec_from_file_location('foreign_fixture_surface', sys.argv[2])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
if sys.argv[1] == 'facade':
    assert callable(module.SelectionTests)
    assert module.selection is module.SelectionTests.run_plan.__globals__['selection']
else:
    assert not any(name.startswith('test_') for name in vars(module.FixtureSupport))
    fixture = module.FixtureSupport()
    assert callable(fixture.setUp) and callable(fixture.run_plan)
    assert module.selection is fixture.run_plan.__globals__['selection']
print('Foreign ' + sys.argv[1] + ' import passed without executing suites.')
'''
        with tempfile.TemporaryDirectory(prefix='foreign-fixture-import-') as directory:
            for surface, filename in [('facade', 'smoke-test.py'), ('helper', 'test_support.py')]:
                with self.subTest(surface=surface):
                    # Separate processes prevent one surface's sys.path setup
                    # from concealing a broken standalone import of the other.
                    result = subprocess.run([sys.executable, '-I', '-B', '-c', code,
                        surface, str(ROOT / 'scripts/repo/check-selection' / filename)],
                        cwd=directory, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout.strip(), 'Foreign ' + surface + ' import passed without executing suites.')
