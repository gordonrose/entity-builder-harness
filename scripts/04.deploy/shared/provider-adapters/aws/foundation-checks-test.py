#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.aws.foundation-checks
#   version: 1
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-16"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise shared foundation and private-network checks with controlled provider observations.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: repo.check-selection.catalog
#     path: scripts/repo/check-selection/checks.yml
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import Mock

SPEC = importlib.util.spec_from_file_location("foundation_checks", Path(__file__).with_name("foundation-checks.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
OUTPUTS = {"VpcId": "vpc-test", "PrivateSubnetIds": "subnet-one,subnet-two",
           "ClusterArn": "cluster-test", "LogGroupName": "logs-test", "ServiceDiscoveryArn": "arn:service/srv-test"}
EXPECTED = {"cluster_arn": "cluster-test", "log_group": "logs-test"}


def stack():
    return {"Stacks": [{"StackStatus": "UPDATE_COMPLETE", "Outputs": [
        {"OutputKey": key, "OutputValue": value} for key, value in OUTPUTS.items()]}]}


def network():
    return [
        {"Vpcs": [{"VpcId": "vpc-test", "State": "available", "CidrBlock": "10.71.0.0/16"}]},
        {"Subnets": [{"SubnetId": name, "VpcId": "vpc-test", "State": "available", "MapPublicIpOnLaunch": False} for name in ("subnet-one", "subnet-two")]},
        {"Service": {"DnsConfig": {"NamespaceId": "ns-test"}}},
        {"Namespace": {"Id": "ns-test", "Name": "test.internal", "Type": "DNS_PRIVATE", "Properties": {"DnsProperties": {"HostedZoneId": "Z123"}}}},
        {"HostedZone": {"Config": {"PrivateZone": True}}, "VPCs": [{"VPCRegion": "eu-west-1", "VPCId": "vpc-test"}]},
    ]


class FoundationTests(unittest.TestCase):
    def test_budget_configuration_and_numeric_equivalence(self):
        expected = {'BudgetName':'fixture-monthly', 'BudgetType':'COST', 'TimeUnit':'MONTHLY',
                    'BudgetLimit':{'Amount':100, 'Unit':'USD'}, 'CostFilters':{'TagKeyValue':['user:Target$fixture']}}
        for amount in (100, 100.0, '100', '100.00', '1e2'):
            value = copy.deepcopy(expected); value['BudgetLimit']['Amount'] = amount
            M.budget(value, expected)
        for amount in (None, True, [], {}, '', 'private-canary', 'NaN', 'sNaN', 'Infinity', '-Infinity', 0, -1):
            value = copy.deepcopy(expected); value['BudgetLimit']['Amount'] = amount
            for observed, declared in ((value, expected), (value, value)):
                with self.subTest(amount=amount), self.assertRaises(M.FoundationFailure) as failure:
                    M.budget(observed, declared)
                self.assertEqual(failure.exception.code, 'foundation-budget-amount-invalid')
        cases = [
            (lambda d: d.update(BudgetName='other'), 'configuration-mismatch'),
            (lambda d: d.pop('BudgetName'), 'configuration-invalid'),
            (lambda d: d.update(BudgetType='USAGE'), 'configuration-invalid'),
            (lambda d: d.update(TimeUnit='ANNUALLY'), 'configuration-invalid'),
            (lambda d: d.update(BudgetLimit=None), 'configuration-invalid'),
            (lambda d: d['BudgetLimit'].update(Amount=101), 'configuration-mismatch'),
            (lambda d: d['BudgetLimit'].update(Unit='EUR'), 'configuration-mismatch'),
            (lambda d: d.update(CostFilters=None), 'configuration-invalid'),
            (lambda d: d['CostFilters'].update(Service=['another']), 'configuration-invalid'),
            (lambda d: d['CostFilters'].update(TagKeyValue=[]), 'configuration-invalid'),
            (lambda d: d['CostFilters'].update(TagKeyValue=['user:Target$other']), 'configuration-mismatch'),
        ]
        for change, reason in cases:
            value = copy.deepcopy(expected); change(value)
            with self.subTest(reason=reason), self.assertRaises(M.FoundationFailure) as failure: M.budget(value, expected)
            self.assertEqual(failure.exception.code, 'foundation-budget-' + reason)
        for value in (None, [], 'private-canary'):
            with self.assertRaises(M.FoundationFailure) as failure: M.budget(value, expected)
            self.assertEqual(str(failure.exception), 'foundation-budget-observation-invalid')

    def test_endpoint_policy_exactness_and_independent_safety(self):
        prefix = "arn:aws:ecr:eu-west-1:123456789012:repository/"
        repositories = [prefix + name for name in ("one", "two", "three", "four")]
        read = {"Effect": "Allow", "Principal": "*", "Action": ["ecr:BatchCheckLayerAvailability", "ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"], "Resource": repositories}
        token = {"Effect": "Allow", "Principal": "*", "Action": "ecr:GetAuthorizationToken", "Resource": "*"}
        expected = {"Version": "2012-10-17", "Statement": [read, token]}
        actual = copy.deepcopy(expected); actual["Statement"].reverse()
        actual["Statement"][1]["Resource"].reverse()
        M.endpoint_policy(json.dumps(actual), expected, "ecr.api", "123456789012", "eu-west-1", repositories[0])
        cases = [
            (lambda p: p["Statement"][0]["Resource"].pop(), "mismatch"),
            (lambda p: p["Statement"][0]["Resource"].append(prefix + "extra"), "mismatch"),
            (lambda p: p["Statement"][0].update(Resource=["*"]), "unsafe"),
            (lambda p: p["Statement"][0].update(Action="ecr:*"), "unsafe"),
            (lambda p: p["Statement"][0].update(Resource=[prefix.replace("123456789012", "999999999999") + "one"]), "unsafe"),
            (lambda p: p["Statement"][0].update(Condition={}), "invalid"),
            (lambda p: p["Statement"][0].update(Principal={"AWS": "*"}), "invalid"),
            (lambda p: p["Statement"][0].update(Resource=repositories[1:]), "required-resource-missing"),
        ]
        for mutate, reason in cases:
            changed = copy.deepcopy(expected); mutate(changed)
            # Reject unsafe matching source+observation as well as observed drift.
            for declared in ([expected] if reason == "mismatch" else [expected, changed]):
                with self.subTest(reason=reason):
                    with self.assertRaisesRegex(M.FoundationFailure, "^foundation-endpoint-policy-" + reason + "$"):
                        M.endpoint_policy(changed, declared, "ecr.api", "123456789012", "eu-west-1", repositories[0])
        secret = "arn:aws:secretsmanager:eu-west-1:123456789012:secret:selected-abc123"
        expected = {"Version": "2012-10-17", "Statement": [{**read, "Action": "secretsmanager:GetSecretValue", "Resource": [secret]}]}
        M.endpoint_policy(expected, expected, "secretsmanager", "123456789012", "eu-west-1", secret)
        for resource in ([secret, secret + "-extra"], ["*"], [secret + "-other"]):
            changed = copy.deepcopy(expected); changed["Statement"][0]["Resource"] = resource
            with self.assertRaises(M.FoundationFailure):
                M.endpoint_policy(changed, changed, "secretsmanager", "123456789012", "eu-west-1", secret)
        for malformed in ('{"Version":"2012-10-17","Version":"2012-10-17","Statement":[]}', "private-canary", None):
            with self.assertRaisesRegex(M.FoundationFailure, "^foundation-endpoint-policy-invalid$"):
                M.endpoint_policy(malformed, expected, "secretsmanager", "123456789012", "eu-west-1", secret)

    def test_endpoint_prerequisites_and_observation_rejections(self):
        services = {"com.amazonaws.eu-west-1." + name for name in ("ecr.api", "ecr.dkr", "logs")}
        rows = [{"ServiceName": name, "VpcId": "vpc-test", "State": "available", "VpcEndpointType": "Interface",
                 "PrivateDnsEnabled": True, "Groups": [{"GroupId": "sg-test"}], "PolicyDocument": "unchanged"} for name in sorted(services)]
        provider = Mock(return_value={"VpcEndpoints": rows})
        selected, group = M.private_endpoints(provider, "vpc-test", services)
        self.assertEqual((selected, group), (rows, "sg-test"))
        provider.assert_called_once_with("ec2", "describe-vpc-endpoints", Filters=[{"Name": "vpc-id", "Values": ["vpc-test"]}])
        secret = "com.amazonaws.eu-west-1.secretsmanager"
        with self.assertRaisesRegex(M.FoundationFailure, "^foundation-endpoint-missing$"):
            M.private_endpoints(provider, "vpc-test", services | {secret})
        rows.append({**rows[0], "ServiceName": secret})
        self.assertEqual(len(M.private_endpoints(provider, "vpc-test", services | {secret})[0]), 4)
        self.assertEqual(len(M.private_endpoints(provider, "vpc-test", services)[0]), 3)
        rows.pop()
        cases = [(None, "observation-invalid"), ({}, "observation-invalid"),
                 ({"VpcEndpoints": [None]}, "observation-invalid"),
                 ({"VpcEndpoints": [{"ServiceName": []}]}, "observation-invalid"),
                 ({"VpcEndpoints": []}, "missing"),
                 ({"VpcEndpoints": [*rows, {**rows[0], "State": "pending"}]}, "ambiguous")]
        for field, value, code in [
            ("VpcId", None, "observation-invalid"), ("VpcId", "private-canary", "vpc-mismatch"),
            ("State", [], "observation-invalid"), ("State", "pending", "not-available"),
            ("VpcEndpointType", "Gateway", "not-interface"),
            ("PrivateDnsEnabled", None, "observation-invalid"), ("PrivateDnsEnabled", False, "dns-not-private"),
            ("Groups", None, "group-invalid"), ("Groups", [], "group-invalid"), ("Groups", [None], "group-invalid"),
            ("Groups", [{"GroupId": ""}], "group-invalid"), ("Groups", [{"GroupId": []}], "group-invalid"),
            ("Groups", [{"GroupId": "sg-test"}] * 2, "group-invalid"),
            ("Groups", [{"GroupId": "sg-other"}], "group-mismatch")]:
            altered = copy.deepcopy(rows); altered[0][field] = value
            cases.append(({"VpcEndpoints": altered}, code))
        for document, code in cases:
            with self.subTest(code=code):
                provider = Mock(return_value=document)
                with self.assertRaisesRegex(M.FoundationFailure, "^foundation-endpoint-" + code + "$"):
                    M.private_endpoints(provider, "vpc-test", services)
                self.assertEqual(provider.call_count, 1)
        for selection in (None, [], "logs", ["logs", "logs"], [None], [""]):
            provider = Mock()
            with self.assertRaisesRegex(M.FoundationFailure, "^foundation-endpoint-selection-invalid$"):
                M.private_endpoints(provider, "vpc-test", selection)
            provider.assert_not_called()

    def test_prefix_selection_and_provider_failure_preservation(self):
        provider = Mock(return_value={"PrefixLists": [{"PrefixListId": "pl-test"}]})
        self.assertEqual(M.s3_prefix_list(provider, "eu-west-1"), "pl-test")
        provider.assert_called_once_with("ec2", "describe-managed-prefix-lists", Filters=[{"Name": "prefix-list-name", "Values": ["com.amazonaws.eu-west-1.s3"]}])
        for rows, code in [(None, "observation-invalid"), ([None], "observation-invalid"),
                           ([{"PrefixListId": ""}], "observation-invalid"), ([{"PrefixListId": []}], "observation-invalid"),
                           ([], "missing"), ([{"PrefixListId": "pl-test"}] * 2, "ambiguous"),
                           ([{"PrefixListId": "pl-test"}, {}], "observation-invalid")]:
            with self.subTest(code=code):
                provider = Mock(return_value={"PrefixLists": rows})
                with self.assertRaisesRegex(M.FoundationFailure, "^foundation-s3-prefix-" + code + "$"):
                    M.s3_prefix_list(provider, "eu-west-1")
                self.assertEqual(provider.call_count, 1)
        for function, arguments in [(M.private_endpoints, ("vpc-test", {"logs"})), (M.s3_prefix_list, ("eu-west-1",))]:
            failure = M.FoundationFailure("aws-access-denied"); provider = Mock(side_effect=failure)
            with self.assertRaises(M.FoundationFailure) as caught:
                function(provider, *arguments)
            self.assertIs(caught.exception, failure)
            self.assertEqual(provider.call_count, 1)

    def test_success_and_selected_provider_arguments(self):
        provider = Mock(side_effect=[stack(), *network()])
        outputs = M.foundation(provider("cloudformation", "describe-stacks", StackName="selected-stack"), M.NETWORK_OUTPUTS, EXPECTED)
        facts = M.private_network(provider, outputs, "test.internal", "eu-west-1")
        self.assertEqual(facts, {key: OUTPUTS[key] for key in ("VpcId", "PrivateSubnetIds", "ClusterArn", "LogGroupName")} | {"VpcCidr": "10.71.0.0/16", "NamespaceId": "ns-test"})
        self.assertEqual([call.args for call in provider.call_args_list], [
            ("cloudformation", "describe-stacks"), ("ec2", "describe-vpcs"), ("ec2", "describe-subnets"),
            ("servicediscovery", "get-service"), ("servicediscovery", "get-namespace"), ("route53", "get-hosted-zone")])
        self.assertEqual([call.kwargs for call in provider.call_args_list], [
            {"StackName": "selected-stack"}, {"VpcIds": ["vpc-test"]}, {"SubnetIds": ["subnet-one", "subnet-two"]},
            {"Id": "srv-test"}, {"Id": "ns-test"}, {"Id": "Z123"}])

    def test_stack_and_output_rejections(self):
        cases = [
            (None, "stack-observation-invalid"), ({"Stacks": []}, "stack-observation-invalid"),
            ({"Stacks": [None]}, "stack-observation-invalid"),
            ({"Stacks": [stack()["Stacks"][0], {}]}, "stack-observation-invalid"),
        ]
        for field, value, code in [
            ("StackStatus", None, "stack-observation-invalid"), ("StackStatus", [], "stack-observation-invalid"),
            ("StackStatus", "UPDATE_IN_PROGRESS", "stack-not-ready"),
            ("StackStatus", "UPDATE_ROLLBACK_COMPLETE", "stack-not-ready"),
            ("Outputs", None, "outputs-invalid"), ("Outputs", [None], "outputs-invalid"),
            ("Outputs", [], "outputs-missing"),
            ("Outputs", [{"OutputKey": [], "OutputValue": "private-canary"}], "outputs-invalid"),
            ("Outputs", [{"OutputKey": "VpcId", "OutputValue": ""}], "outputs-invalid"),
            ("Outputs", [{"OutputKey": "VpcId", "OutputValue": None}], "outputs-invalid")]:
            doc = stack(); doc["Stacks"][0][field] = value; cases.append((doc, code))
        doc = stack(); doc["Stacks"][0]["Outputs"].append(copy.deepcopy(doc["Stacks"][0]["Outputs"][0]))
        cases.append((doc, "outputs-ambiguous"))
        for doc, code in cases:
            with self.subTest(code=code):
                with self.assertRaisesRegex(M.FoundationFailure, "^foundation-" + code + "$"):
                    M.stack_outputs(doc, M.NETWORK_OUTPUTS)
        for key, code in [("cluster_arn", "cluster-mismatch"), ("log_group", "log-group-mismatch")]:
            provider = Mock(return_value=stack())
            with self.assertRaisesRegex(M.FoundationFailure, "^foundation-" + code + "$"):
                M.foundation(provider("cloudformation", "describe-stacks", StackName="selected"), M.NETWORK_OUTPUTS, {**EXPECTED, key: "private-canary"})
            self.assertEqual(provider.call_count, 1)

    def test_network_rejections_stop_at_failed_boundary(self):
        cases = [
            (0, lambda d: d.update(Vpcs=[]), "vpc-observation-invalid"),
            (0, lambda d: d["Vpcs"][0].pop("State"), "vpc-observation-invalid"),
            (0, lambda d: d["Vpcs"][0].update(VpcId="private-canary"), "vpc-mismatch"),
            (0, lambda d: d["Vpcs"][0].update(State="pending"), "vpc-not-available"),
            (0, lambda d: d["Vpcs"][0].update(CidrBlock=None), "vpc-cidr-invalid"),
            (0, lambda d: d["Vpcs"][0].update(CidrBlock="private-canary"), "vpc-cidr-invalid"),
            (1, lambda d: d.update(Subnets=None), "subnet-observation-invalid"),
            (1, lambda d: d.update(Subnets=[None]), "subnet-observation-invalid"),
            (1, lambda d: d["Subnets"].pop(), "subnet-selection-mismatch"),
            (1, lambda d: d["Subnets"][1].update(SubnetId="subnet-one"), "subnet-selection-mismatch"),
            (1, lambda d: d["Subnets"][0].update(VpcId="vpc-other"), "subnet-vpc-mismatch"),
            (1, lambda d: d["Subnets"][0].update(State="pending"), "subnet-not-available"),
            (1, lambda d: d["Subnets"][0].update(MapPublicIpOnLaunch=True), "subnet-not-private"),
            (1, lambda d: d["Subnets"][0].pop("MapPublicIpOnLaunch"), "subnet-observation-invalid"),
            (2, lambda d: d.update(Service=None), "namespace-reference-invalid"),
            (2, lambda d: d["Service"].update(DnsConfig=None), "namespace-reference-invalid"),
            (2, lambda d: d["Service"]["DnsConfig"].update(NamespaceId="private-canary"), "namespace-reference-invalid"),
            (3, lambda d: d.update(Namespace=None), "namespace-observation-invalid"),
            (3, lambda d: d["Namespace"].update(Id="ns-other"), "namespace-mismatch"),
            (3, lambda d: d["Namespace"].update(Name="other.internal"), "namespace-mismatch"),
            (3, lambda d: d["Namespace"].update(Type="DNS_PUBLIC"), "namespace-not-private"),
            (3, lambda d: d["Namespace"].update(Properties=None), "zone-reference-invalid"),
            (3, lambda d: d["Namespace"]["Properties"]["DnsProperties"].update(HostedZoneId="private-canary"), "zone-reference-invalid"),
            (4, lambda d: d.update(HostedZone=None), "zone-observation-invalid"),
            (4, lambda d: d["HostedZone"]["Config"].update(PrivateZone=False), "zone-not-private"),
            (4, lambda d: d.update(VPCs=[None]), "zone-vpcs-invalid"),
            (4, lambda d: d.update(VPCs=[]), "zone-vpc-mismatch"),
            (4, lambda d: d["VPCs"][0].update(VPCRegion="other-region"), "zone-vpc-mismatch"),
            (4, lambda d: d["VPCs"][0].update(VPCId="vpc-other"), "zone-vpc-mismatch"),
            (4, lambda d: d["VPCs"].append(copy.deepcopy(d["VPCs"][0])), "zone-vpc-mismatch"),
        ]
        for index, mutate, code in cases:
            with self.subTest(code=code, index=index):
                responses = network(); mutate(responses[index]); provider = Mock(side_effect=responses)
                with self.assertRaisesRegex(M.FoundationFailure, "^foundation-" + code + "$"):
                    M.private_network(provider, OUTPUTS, "test.internal", "eu-west-1")
                self.assertEqual(provider.call_count, index + 1)
        for value in ("subnet-one,subnet-one", "subnet-one,"):
            provider = Mock(side_effect=network())
            with self.assertRaisesRegex(M.FoundationFailure, "^foundation-subnet-selection-invalid$"):
                M.private_network(provider, {**OUTPUTS, "PrivateSubnetIds": value}, "test.internal", "eu-west-1")
            self.assertEqual(provider.call_count, 1)
        provider = Mock()
        with self.assertRaisesRegex(M.FoundationFailure, "^foundation-outputs-invalid$"):
            M.private_network(provider, {}, "test.internal", "eu-west-1")
        provider.assert_not_called()

    def test_provider_failure_identity_is_preserved_without_retry(self):
        for index in range(5):
            failure = M.FoundationFailure("aws-access-denied")
            provider = Mock(side_effect=[*network()[:index], failure])
            with self.assertRaises(M.FoundationFailure) as caught:
                M.private_network(provider, OUTPUTS, "test.internal", "eu-west-1")
            self.assertIs(caught.exception, failure)
            self.assertEqual(provider.call_count, index + 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
