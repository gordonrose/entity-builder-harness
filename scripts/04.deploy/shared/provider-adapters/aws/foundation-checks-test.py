#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.aws.foundation-checks
#   version: 4
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise foundation choices and observations, complete input validation, bounded source projection and the owned private-network template without AWS.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: repo.check-selection.catalog
#     path: scripts/repo/check-selection/checks.yml
import copy
import importlib.util
import json
from pathlib import Path
import re
import unittest
from unittest.mock import Mock, patch

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
    def proposed_network(self):
        choices = {"vpc_cidr": "10.71.0.0/16", "subnet_one_cidr": "10.71.1.0/24", "subnet_two_cidr": "10.71.2.0/24",
                   "availability_zone_one": "eu-west-1a", "availability_zone_two": "eu-west-1b"}
        zones = {"AvailabilityZones": [{"ZoneName": "eu-west-1" + letter, "ZoneId": "euw1-az" + str(index),
                    "RegionName": "eu-west-1", "State": "available", "ZoneType": "availability-zone"}
                    for index, letter in enumerate(("a", "b"), 1)]}
        return choices, zones

    def test_network_choices_check_real_zones_and_return_only_copied_choices(self):
        choices, zones = self.proposed_network()
        original = copy.deepcopy(choices)
        provider = Mock(return_value=zones)
        observed = M.private_network_choices(provider, choices, "eu-west-1")
        self.assertEqual(observed, original)
        provider.assert_called_once_with("ec2", "describe-availability-zones", ZoneNames=["eu-west-1a", "eu-west-1b"])
        observed["vpc_cidr"] = "changed"
        self.assertEqual(choices, original)
        for vpc, one, two in (("172.16.0.0/16", "172.16.0.0/28", "172.16.0.16/28"),
                              ("192.168.0.0/16", "192.168.0.0/17", "192.168.128.0/17")):
            selected = {**choices, "vpc_cidr": vpc, "subnet_one_cidr": one, "subnet_two_cidr": two}
            self.assertEqual(M.private_network_choices(provider, selected, "eu-west-1"), selected)

    def test_network_choice_rejections_precede_provider_calls_and_exclude_values(self):
        choices, _ = self.proposed_network()
        cases = [(None, "choices-invalid"), ([], "choices-invalid"), ({}, "choices-invalid"),
                 ({**choices, "private-canary": "value"}, "choices-invalid"),
                 ({**choices, "vpc_cidr": None}, "choices-invalid")]
        for value, reason in (("private-canary", "cidr-invalid"), ("10.71.0.1/16", "cidr-invalid"),
                              ("10.71.0.0/255.255.0.0", "cidr-invalid"), ("::/64", "cidr-invalid"),
                              ("127.0.0.0/16", "cidr-not-private"), ("100.64.0.0/16", "cidr-not-private"),
                              ("172.15.0.0/16", "cidr-not-private"), ("10.0.0.0/8", "cidr-size-invalid"),
                              ("10.71.0.0/29", "cidr-size-invalid")):
            cases.append(({**choices, "vpc_cidr": value}, reason))
        for changes, reason in (({"subnet_one_cidr": "10.72.0.0/24"}, "subnet-containment-invalid"),
                                ({"subnet_one_cidr": choices["vpc_cidr"]}, "subnet-containment-invalid"),
                                ({"subnet_two_cidr": choices["subnet_one_cidr"]}, "subnet-overlap"),
                                ({"subnet_two_cidr": "10.71.1.0/25"}, "subnet-overlap"),
                                ({"availability_zone_two": "eu-west-1a"}, "zone-selection-invalid"),
                                ({"availability_zone_one": "us-west-2a"}, "zone-selection-invalid"),
                                ({"availability_zone_one": "eu-west-1-dub-1a"}, "zone-selection-invalid")):
            cases.append(({**choices, **changes}, reason))
        provider = Mock(side_effect=AssertionError("unchecked choice reached provider"))
        for selected, reason in cases:
            with self.subTest(reason=reason), self.assertRaises(M.FoundationFailure) as failure:
                M.private_network_choices(provider, selected, "eu-west-1")
            self.assertEqual(str(failure.exception), "foundation-network-" + reason)
            self.assertNotIn("private-canary", str(failure.exception))
        for region in (None, "", "private-canary", "eu-west-1a"):
            with self.assertRaisesRegex(M.FoundationFailure, "^foundation-network-choice-context-invalid$"):
                M.private_network_choices(provider, choices, region)
        provider.assert_not_called()

    def test_network_zone_observation_rejections_and_provider_failure_identity(self):
        choices, zones = self.proposed_network()
        cases = [(None, "observation-invalid"), ({}, "observation-invalid"),
                 ({"AvailabilityZones": []}, "selection-mismatch"),
                 ({"AvailabilityZones": [None]}, "observation-invalid")]
        for field, value, reason in (("ZoneName", "eu-west-1c", "selection-mismatch"),
                                    ("ZoneName", None, "observation-invalid"),
                                    ("RegionName", "us-west-2", "region-mismatch"),
                                    ("State", "unavailable", "not-available"),
                                    ("ZoneType", "local-zone", "type-unsupported"),
                                    ("ZoneId", "private-canary", "ambiguous"),
                                    ("ZoneId", "euw1-az2", "ambiguous")):
            observed = copy.deepcopy(zones); observed["AvailabilityZones"][0][field] = value
            cases.append((observed, reason))
        observed = copy.deepcopy(zones); observed["AvailabilityZones"].append(observed["AvailabilityZones"][0])
        cases.append((observed, "selection-mismatch"))
        for observed, reason in cases:
            provider = Mock(return_value=observed)
            with self.subTest(reason=reason), self.assertRaises(M.FoundationFailure) as failure:
                M.private_network_choices(provider, choices, "eu-west-1")
            self.assertEqual(str(failure.exception), "foundation-network-zone-" + reason)
            provider.assert_called_once()
        cause = RuntimeError("private-canary")
        provider = Mock(side_effect=cause)
        with self.assertRaises(RuntimeError) as failure: M.private_network_choices(provider, choices, "eu-west-1")
        self.assertIs(failure.exception, cause)
        provider.assert_called_once()

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


class CloudFormationStringProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("string_projection", Path(__file__).with_name("cloudformation-template.py"))
        cls.cf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.cf)

    def source(self):
        return {"Parameters": {"Prefix": {"Type": "String", "Default": "production", "MinLength": 1,
                    "MaxLength": 21, "AllowedPattern": "^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$"},
                "Secret": {"Type": "String", "NoEcho": True}},
                "Resources": {"Example": {"Type": "AWS::Example::Resource", "Properties": {
                    "Name": {"Ref": "Prefix"}, "Url": {"Fn::Sub": "http://service.${Prefix}.internal"},
                    "Arn": {"Fn::Sub": "arn:${AWS::Partition}:example:${AWS::Region}:${Resource.Arn}:${Prefix}"},
                    "Escaped": {"Fn::Sub": "${Prefix}-${!Prefix}"}, "Secret": {"Ref": "Secret"},
                    "Other": {"Fn::Sub": ["${Local}", {"Local": {"Ref": "Resource"}}]},
                    "EscapedMap": {"Fn::Sub": ["${!Prefix}", {}]},
                    "Dynamic": {"Fn::Sub": "{{resolve:ssm:unselected-reference}}"},
                    "Join": {"Fn::Join": ["-", [{"Ref": "Prefix"}, {"Ref": "Resource"}]]},
                    "Unchanged": {"Fn::Sub": "literal-${AWS::Region}-${!Prefix}"}}}}}

    def test_selected_defaults_and_overrides_preserve_symbolic_source_and_copy(self):
        original = self.source(); before = copy.deepcopy(original)
        for override, expected in ((None, "production"), ({"Prefix": "temporary-one"}, "temporary-one")):
            result = self.cf.project_string_parameters(original, ["Prefix"], override)
            props = result["Resources"]["Example"]["Properties"]
            self.assertEqual(props["Name"], expected)
            self.assertEqual(props["Url"], "http://service." + expected + ".internal")
            self.assertEqual(props["Arn"], {"Fn::Sub": "arn:${AWS::Partition}:example:${AWS::Region}:${Resource.Arn}:" + expected})
            self.assertEqual(props["Escaped"], {"Fn::Sub": expected + "-${!Prefix}"})
            self.assertEqual(props["Join"], {"Fn::Join": ["-", [expected, {"Ref": "Resource"}]]})
            for key in ("Secret", "Other", "EscapedMap", "Dynamic", "Unchanged"):
                self.assertEqual(props[key], before["Resources"]["Example"]["Properties"][key])
            props["Other"]["Fn::Sub"][1]["Local"]["Ref"] = "changed"
            result["Parameters"]["Prefix"]["Default"] = "changed"
            self.assertTrue(self.cf.templates_equal(original, before))
        self.assertEqual(self.cf.project_string_parameters(json.dumps(original), ("Prefix",)),
                         self.cf.project_string_parameters(original, ["Prefix"]))

    def test_valid_explicit_string_and_constraint_boundaries(self):
        source = self.source(); declaration = source["Parameters"]["Prefix"]
        for value in ("a", "a" * 21):
            self.assertEqual(self.cf.project_string_parameters(source, ["Prefix"], {"Prefix": value})
                             ["Resources"]["Example"]["Properties"]["Name"], value)
        declaration.update(AllowedValues=["production", "staging"], NoEcho=False,
                           Description="Public identity", ConstraintDescription="An admitted identity")
        self.assertEqual(self.cf.project_string_parameters(source, ["Prefix"], {"Prefix": "staging"})
                         ["Resources"]["Example"]["Properties"]["Name"], "staging")
        del declaration["Default"]
        self.cf.project_string_parameters(source, ["Prefix"], {"Prefix": "staging"})
        source["Parameters"]["Suffix"] = {"Type": "String", "Default": "private"}
        source["Outputs"] = {"Name": {"Value": {"Fn::Sub": "${Prefix}-${Suffix}"}}}
        result = self.cf.project_string_parameters(source, ["Prefix", "Suffix"], {"Prefix": "staging"})
        self.assertEqual(result["Outputs"]["Name"]["Value"], "staging-private")

    def complete_parameters(self):
        declarations = {"Label": {"Type": "String", "Default": "old", "AllowedPattern": "[a-z]+", "MinLength": 1, "MaxLength": 8},
                        "Count": {"Type": "Number", "Default": 1, "MinValue": 0, "MaxValue": 2, "AllowedValues": [0, 1, 2]},
                        "Vpc": {"Type": "AWS::EC2::VPC::Id"}, "Group": {"Type": "AWS::EC2::SecurityGroup::Id"},
                        "Subnets": {"Type": "List<AWS::EC2::Subnet::Id>"},
                        "Zone": {"Type": "AWS::EC2::AvailabilityZone::Name"}}
        values = {"Label": "new", "Count": 0, "Vpc": "vpc-0123456789abcdef0", "Group": "sg-01234567",
                  "Subnets": "subnet-01234567,subnet-0123456789abcdef0", "Zone": "eu-west-1a"}
        return {"Parameters": declarations, "Resources": {"Kept": {"Properties": {"Value": {"Ref": "Vpc"}}}}}, values

    def test_complete_values_reuse_constraints_without_projecting_and_serialize_numbers(self):
        source, values = self.complete_parameters()
        original, supplied = copy.deepcopy(source), copy.deepcopy(values)
        for raw in (source, json.dumps(source)):
            for count in (0, "0", 1, "1"):
                chosen = {**values, "Count": count}
                result = self.cf.validate_parameter_values(raw, chosen)
                self.assertEqual(result, {**values, "Count": str(count)})
                self.assertTrue(all(type(value) is str for value in result.values()))
                result["Label"] = "changed-copy"
                self.assertEqual(chosen["Label"], supplied["Label"])
        self.assertEqual(source, original)
        self.assertEqual(values, supplied)
        # A shared constraint counterexample must reach both actual consumers.
        failure = ValueError("fixture-shared-constraint")
        with patch.object(self.cf, "_parameter_values", side_effect=failure) as shared:
            for consumer in (lambda: self.cf.validate_parameter_values(source, values),
                             lambda: self.cf.project_parameters(source, ("Label",), {"Label": "new"})):
                with self.assertRaises(ValueError) as caught: consumer()
                self.assertIs(caught.exception, failure)
            self.assertEqual(shared.call_count, 2)

    def test_complete_values_reject_missing_extra_secret_dynamic_and_invalid_constraints(self):
        source, values = self.complete_parameters()
        for malformed in ("Parameters: [private-canary", {"Parameters": float("nan")}):
            with self.assertRaisesRegex(ValueError, "^cloudformation-template-body-invalid$") as caught:
                self.cf.validate_parameter_values(malformed, values)
            self.assertIsNone(caught.exception.__cause__)
            self.assertTrue(caught.exception.__suppress_context__)
        for chosen in (None, [], {}, {key: value for key, value in values.items() if key != "Label"},
                       {**values, "Extra": "private-canary"}):
            with self.assertRaisesRegex(ValueError, "^cloudformation-parameter-values-invalid$"):
                self.cf.validate_parameter_values(source, chosen)
        changes = [("Label", "private-canary", "string"), ("Label", "${value}", "string"),
                   ("Label", "{{resolve:ssm:private-canary}}", "string"), ("Label", None, "string"),
                   ("Count", True, "number"), ("Count", 1.0, "number"), ("Count", "01", "number"),
                   ("Count", "-0", "number"), ("Count", "1.0", "number"), ("Count", "1e0", "number"),
                   ("Count", "private-canary", "number"), ("Count", 3, "number")]
        for name, value, kind in changes:
            with self.subTest(name=name, value_type=type(value).__name__), self.assertRaisesRegex(ValueError, "^cloudformation-" + kind + "-parameter-invalid$"):
                self.cf.validate_parameter_values(source, {**values, name: value})
        for name, change, kind in (("Label", {"NoEcho": True}, "string"),
                                   ("Label", {"Default": "private-canary"}, "string"),
                                   ("Label", {"AllowedPattern": "["}, "string"),
                                   ("Label", {"MinLength": True}, "string"),
                                   ("Label", {"UnknownConstraint": "private-canary"}, "string"),
                                   ("Count", {"Default": "1"}, "number"),
                                   ("Count", {"MaxValue": False}, "number"),
                                   ("Count", {"AllowedValues": [True]}, "number"),
                                   ("Count", {"NoEcho": True}, "number")):
            changed = copy.deepcopy(source); changed["Parameters"][name].update(change)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "^cloudformation-" + kind + "-parameter-invalid$"):
                self.cf.validate_parameter_values(changed, values)

    def test_complete_aws_values_reject_wrong_types_noncanonical_lists_and_unsupported_declarations(self):
        source, values = self.complete_parameters()
        changes = [("Vpc", "vpc-private-canary"), ("Vpc", "sg-01234567"), ("Vpc", []),
                   ("Group", "sg-0123456789"), ("Zone", "eu-west-1-dub-1a"), ("Zone", "${Zone}"),
                   ("Subnets", ["subnet-01234567"]), ("Subnets", ""), ("Subnets", "subnet-01234567,"),
                   ("Subnets", "subnet-01234567, subnet-89abcdef"),
                   ("Subnets", "subnet-01234567,subnet-01234567")]
        for name, value in changes:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "^cloudformation-aws-parameter-invalid$"):
                self.cf.validate_parameter_values(source, {**values, name: value})
        for change in ({"NoEcho": True}, {"AllowedValues": [values["Vpc"]]}, {"Default": "vpc-private-canary"}):
            changed = copy.deepcopy(source); changed["Parameters"]["Vpc"].update(change)
            with self.assertRaisesRegex(ValueError, "^cloudformation-aws-parameter-invalid$"):
                self.cf.validate_parameter_values(changed, values)
        for kind in (None, [], "CommaDelimitedList", "List<Number>", "AWS::SSM::Parameter::Value<String>"):
            changed = copy.deepcopy(source); changed["Parameters"]["Vpc"]["Type"] = kind
            with self.assertRaisesRegex(ValueError, "^cloudformation-parameter-type-unsupported$"):
                self.cf.validate_parameter_values(changed, values)

    def test_selection_and_declarations_fail_with_value_free_reasons(self):
        source = self.source()
        for names, overrides in (([], None), ("Prefix", None), (["Prefix", "Prefix"], None),
                                 (["Missing"], None), ([1], None), ([[]], None),
                                 (["Prefix"], []), (["Prefix"], {"Unknown": "private-canary"})):
            with self.subTest(names=names), self.assertRaisesRegex(ValueError, "^cloudformation-parameter-selection-invalid$"):
                self.cf.project_string_parameters(source, names, overrides)
        changes = [{"Type": "Number"}, {"NoEcho": True}, {"NoEcho": "false"}, {"Unexpected": 1},
                   {"Description": 1}, {"ConstraintDescription": []}, {"AllowedPattern": "[private-canary"},
                   {"AllowedPattern": "a{9999999999999999999999}"},
                   {"AllowedPattern": "(" * 1000 + "a" + ")" * 1000},
                   {"AllowedPattern": None}, {"MinLength": True}, {"MinLength": -1}, {"MaxLength": "21"},
                   {"MaxLength": None}, {"MinLength": 22}, {"AllowedValues": []}, {"AllowedValues": [1]},
                   {"AllowedValues": None}, {"AllowedValues": ["different"]}, {"Default": None},
                   {"Default": ""}, {"Default": "a" * 22}, {"Default": "two--hyphens"},
                   {"Default": "{{resolve:secretsmanager:private-canary}}"}, {"Default": "${private-canary}"}]
        for change in changes:
            changed = copy.deepcopy(source); changed["Parameters"]["Prefix"].update(change)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "^cloudformation-string-parameter-invalid$"):
                self.cf.project_string_parameters(changed, ["Prefix"], {"Prefix": "production"})
        for declaration in (None, [], {"Type": "String"}):
            changed = copy.deepcopy(source); changed["Parameters"]["Prefix"] = declaration
            with self.assertRaisesRegex(ValueError, "^cloudformation-string-parameter-invalid$"):
                self.cf.project_string_parameters(changed, ["Prefix"])
        for value in (None, 1, "", "a" * 22, "UPPER", "two--hyphens"):
            with self.assertRaisesRegex(ValueError, "^cloudformation-string-parameter-invalid$"):
                self.cf.project_string_parameters(source, ["Prefix"], {"Prefix": value})

    def test_unsupported_substitutions_dynamic_values_and_injection_are_rejected(self):
        expressions = [
            {"Ref": "Prefix", "Other": True}, {"Fn::Sub": "${Prefix}", "Other": True},
            {"Fn::Sub": ["${Prefix}", {"Prefix": "local-shadow"}]},
            {"Fn::Sub": ["${Local}", {"Local": {"Ref": "Prefix"}}]},
            {"Fn::Sub": {"Unexpected": "${Prefix}"}},
            {"Fn::Sub": "{{resolve:secretsmanager:${Prefix}}}"},
        ]
        for expression in expressions:
            source = self.source(); source["Outputs"] = {"Value": expression}
            with self.subTest(expression=expression), self.assertRaisesRegex(ValueError, "^cloudformation-parameter-substitution-unsupported$"):
                self.cf.project_string_parameters(source, ["Prefix"])
        for value, expression in (("$", "${Prefix}{AWS::Region}"), ("{", "$${Prefix}AWS::Region}"),
                                  ("resolve:private-canary", "{{${Prefix}}}")):
            source = {"Parameters": {"Prefix": {"Type": "String", "Default": value}},
                      "Outputs": {"Value": {"Fn::Sub": expression}}}
            with self.assertRaisesRegex(ValueError, "^cloudformation-parameter-substitution-unsupported$"):
                self.cf.project_string_parameters(source, ["Prefix"])
        for value in ("${private-canary}", "{{resolve:ssm:private-canary}}"):
            source = {"Parameters": {"Prefix": {"Type": "String", "Default": "safe"}}}
            with self.assertRaisesRegex(ValueError, "^cloudformation-string-parameter-invalid$"):
                self.cf.project_string_parameters(source, ["Prefix"], {"Prefix": value})


    def test_integer_parameters_and_selected_equality_guards_are_bounded(self):
        source = {'Parameters': {'Count': {'Type': 'Number', 'Default': 1, 'AllowedValues': [0, 1]},
                                 'Enabled': {'Type': 'String', 'Default': 'true', 'AllowedValues': ['true', 'false']}},
                  'Conditions': {'Selected': {'Fn::Equals': [{'Ref': 'Enabled'}, 'true']}, 'Other': {'Fn::Equals': [{'Ref': 'Provider'}, 'value']}},
                  'Resources': {'Optional': {'Type': 'AWS::Example::Resource', 'Condition': 'Selected'},
                                'Kept': {'Type': 'AWS::Example::Resource', 'Properties': {'Count': {'Ref': 'Count'}, 'Label': {'Fn::Sub': 'count-${Count}'}}}},
                  'Outputs': {'OptionalArn': {'Condition': 'Selected', 'Value': {'Fn::GetAtt': ['Optional', 'Arn']}}}}
        original = copy.deepcopy(source)
        production = self.cf.project_parameters(source, ['Count', 'Enabled'], condition_names=['Selected'])
        temporary = self.cf.project_parameters(source, ['Count', 'Enabled'], {'Count': 0, 'Enabled': 'false'}, condition_names=['Selected'])
        self.assertNotIn('Condition', production['Resources']['Optional'])
        self.assertIn('OptionalArn', production['Outputs'])
        self.assertNotIn('Optional', temporary['Resources'])
        self.assertNotIn('OptionalArn', temporary['Outputs'])
        self.assertEqual(temporary['Resources']['Kept']['Properties'], {'Count': 0, 'Label': 'count-0'})
        self.assertIs(type(temporary['Resources']['Kept']['Properties']['Count']), int)
        self.assertEqual(temporary['Conditions'], {'Other': source['Conditions']['Other']})
        self.assertEqual(source, original)
        with self.assertRaisesRegex(ValueError, '^cloudformation-string-parameter-invalid$'):
            self.cf.project_string_parameters(source, ['Count'])
        for value in (True, 0.0, '0', None, -1, 2):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, '^cloudformation-number-parameter-invalid$'):
                self.cf.project_parameters(source, ['Count'], {'Count': value})
        for change in ({'Default': True}, {'AllowedValues': [False, True]}, {'AllowedValues': []}, {'MinValue': '0'},
                       {'MaxValue': False}, {'MinValue': 2}, {'MaxValue': 0}, {'NoEcho': True}, {'Unknown': 1}):
            changed = copy.deepcopy(source); changed['Parameters']['Count'].update(change)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, '^cloudformation-number-parameter-invalid$'):
                self.cf.project_parameters(changed, ['Count'])

    def test_selected_guards_reject_unresolved_forms_and_surviving_references(self):
        base = {'Parameters': {'Enabled': {'Type': 'String', 'Default': 'false'}},
                'Conditions': {'Selected': {'Fn::Equals': [{'Ref': 'Enabled'}, 'true']}},
                'Resources': {'Removed': {'Type': 'AWS::Example::Resource', 'Condition': 'Selected'},
                              'Kept': {'Type': 'AWS::Example::Resource'}}}
        def project(source, guards=('Selected',)):
            return self.cf.project_parameters(source, ['Enabled'], condition_names=guards)
        for guards in ('Selected', ['Missing'], ['Selected', 'Selected'], [[]]):
            with self.assertRaisesRegex(ValueError, '^cloudformation-condition-selection-invalid$'): project(base, guards)
        for expression in ({'Fn::If': ['Other', True, False]}, {'Fn::Equals': [{'Ref': 'Provider'}, 'true']},
                           {'Fn::Equals': [True, 1]}, {'Fn::Equals': ['${Provider}', 'true']}, {'Fn::Equals': ['true', 'true'], 'Extra': 1}):
            source = copy.deepcopy(base); source['Conditions']['Selected'] = expression
            with self.assertRaisesRegex(ValueError, '^cloudformation-condition-unsupported$'): project(source)
        for value in ({'Ref': 'Removed'}, {'Fn::GetAtt': ['Removed', 'Arn']}, {'Fn::GetAtt': 'Removed.Arn'},
                      {'Fn::Sub': '${Removed}'}, {'Fn::Sub': 'arn:${Removed.Arn}'}, {'DependsOn': 'Removed'}, {'DependsOn': ['Removed']}):
            source = copy.deepcopy(base); source['Resources']['Kept']['Properties'] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, '^cloudformation-removed-resource-reference$'): project(source)
        for value in ({'Fn::If': ['Selected', 'yes']}, {'Fn::If': ['Selected', 'yes', 'no', 'extra']},
                      {'Fn::If': ['Selected', 'yes', 'no'], 'Extra': True},
                      {'Fn::If': [{'Unexpected': 'Selected'}, 'yes', 'no']},
                      {'Fn::If': {'Malformed': 'Selected'}}, {'Condition': 'Selected'}, {'Condition': {'Malformed': 'Selected'}}):
            source = copy.deepcopy(base); source['Outputs'] = {'StillPresent': {'Value': value}}
            with self.assertRaisesRegex(ValueError, '^cloudformation-condition-unsupported$'): project(source)
        source = copy.deepcopy(base); source['Resources']['Kept']['Condition'] = None
        with self.assertRaisesRegex(ValueError, '^cloudformation-condition-unsupported$'): project(source)

    def test_selected_if_branches_preserve_unknown_conditions_and_check_surviving_lineage(self):
        source = self.omission_source()
        source["Resources"]["Kept"]["Properties"]["Decision"] = {
            "Fn::If": ["Selected", [{"Ref": "OptionalInput"}, {"Ref": "Removed"}], ["kept"]]}
        original = copy.deepcopy(source)
        result = self.omit(source)
        self.assertEqual(result["Resources"]["Kept"]["Properties"]["Decision"], ["kept"])
        self.assertEqual(result["Resources"]["Kept"]["Properties"]["Symbolic"],
                         original["Resources"]["Kept"]["Properties"]["Symbolic"])
        self.assertEqual(source, original)
        ordinary = self.cf.project_parameters(source, ("Enabled",))
        self.assertEqual(ordinary["Resources"]["Kept"]["Properties"]["Decision"],
                         original["Resources"]["Kept"]["Properties"]["Decision"])
        enabled = self.cf.project_parameters(source, ("Enabled",), {"Enabled": "true"}, condition_names=("Selected",))
        self.assertEqual(enabled["Resources"]["Kept"]["Properties"]["Decision"],
                         [{"Ref": "OptionalInput"}, {"Ref": "Removed"}])
        with self.assertRaisesRegex(ValueError, "^cloudformation-parameter-still-mentioned$"):
            self.cf.project_parameters(source, ("Enabled",), {"Enabled": "true"},
                                       condition_names=("Selected",), omit_if_unused=("OptionalInput",))
        for reference in ({"Ref": "Removed"}, {"Fn::Sub": "${Removed.Arn}"}):
            source["Resources"]["Kept"]["Properties"]["Decision"]["Fn::If"][2] = reference
            with self.assertRaisesRegex(ValueError, "^cloudformation-removed-resource-reference$"):
                self.omit(source)
        # A malformed selected expression in a discarded arm is still rejected.
        source["Resources"]["Kept"]["Properties"]["Decision"] = {
            "Fn::If": ["Selected", {"Fn::If": ["Selected", "missing-arm"]}, "kept"]}
        with self.assertRaisesRegex(ValueError, "^cloudformation-condition-unsupported$"):
            self.omit(source)

    def omission_source(self, name="OptionalInput"):
        return {"Parameters": {"Enabled": {"Type": "String", "Default": "false"},
                    name: {"Type": "String", "Description": name + " is explicitly selected"},
                    "UnselectedInput": {"Type": "String"}, "Defaulted": {"Type": "String", "Default": "preserved"}},
                "Conditions": {"Selected": {"Fn::Equals": [{"Ref": "Enabled"}, "true"]},
                               "Other": {"Fn::Not": [{"Fn::Equals": [{"Ref": "AWS::Region"}, "elsewhere"]}]}},
                "Resources": {"Removed": {"Type": "AWS::Example::Resource", "Condition": "Selected",
                                          "Properties": {"Input": {"Ref": name}}},
                              "Kept": {"Type": "AWS::Example::Resource", "Properties": {
                                  "Symbolic": {"Fn::If": ["Other", {"Fn::GetAtt": ["External", "Arn"]},
                                      {"Fn::Join": ["-", [{"Ref": "UnselectedInput"}, {"Fn::Sub": ["${Local}-${AWS::Region}", {"Local": "literal"}]}]]}]}}}},
                "Outputs": {"RemovedOutput": {"Condition": "Selected", "Value": {"Fn::Sub": "${" + name + "}"}}}}

    def omit(self, source, names=("OptionalInput",)):
        return self.cf.project_parameters(source, ("Enabled",), condition_names=("Selected",), omit_if_unused=names)

    def test_explicit_unused_omission_copies_renamed_source_and_preserves_everything_else(self):
        for name in ("OptionalInput", "RenamedIdentity"):
            source = self.omission_source(name); original = copy.deepcopy(source)
            ordinary = self.cf.project_parameters(source, ("Enabled",), condition_names=("Selected",))
            expected = copy.deepcopy(ordinary); del expected["Parameters"][name]
            for raw in (source, json.dumps(source)):
                result = self.omit(raw, (name,))
                self.assertTrue(self.cf.templates_equal(result, expected))
                self.assertEqual(set(result["Parameters"]), {"Enabled", "UnselectedInput", "Defaulted"})
                self.assertEqual(result["Conditions"], {"Other": source["Conditions"]["Other"]})
                result["Resources"]["Kept"]["Properties"]["Symbolic"]["Fn::If"][0] = "changed"
                self.assertTrue(self.cf.templates_equal(source, original))
            self.assertIn(name, ordinary["Parameters"])
            self.assertIn(name, self.cf.project_string_parameters(source, ("Enabled",))["Parameters"])
            self.assertEqual(self.omit(source, ()), ordinary)
            self.assertEqual(self.omit(source, []), ordinary)

    def test_omission_selection_rejects_duplicate_missing_and_control_collisions(self):
        source = self.omission_source()
        for names in (None, "OptionalInput", {}, (None,), ([],), ("private-canary-invalid",),
                      ("Missing",), ("OptionalInput", "OptionalInput"), ("Enabled",)):
            with self.subTest(names=names), self.assertRaisesRegex(ValueError, "^cloudformation-parameter-omission-selection-invalid$"):
                self.omit(source, names)
        for declaration in (None, []):
            changed = copy.deepcopy(source); changed["Parameters"]["OptionalInput"] = declaration
            with self.assertRaisesRegex(ValueError, "^cloudformation-parameter-omission-selection-invalid$"):
                self.omit(changed)
        # A projected declaration without a default still cannot also be omitted.
        source["Parameters"]["Enabled"].pop("Default")
        with self.assertRaisesRegex(ValueError, "^cloudformation-parameter-omission-selection-invalid$"):
            self.cf.project_parameters(source, ("Enabled",), {"Enabled": "false"}, omit_if_unused=("Enabled",))

    def test_unused_defaulted_noecho_omission_never_retains_or_resolves_secret_values(self):
        source = self.omission_source()
        source["Parameters"]["OptionalInput"].update(Default="", NoEcho=True)
        original = copy.deepcopy(source)
        ordinary = self.cf.project_parameters(source, ("Enabled",), condition_names=("Selected",))
        self.assertEqual(ordinary["Parameters"]["OptionalInput"], original["Parameters"]["OptionalInput"])
        result = self.omit(source)
        self.assertNotIn("OptionalInput", result["Parameters"])
        self.assertEqual(result["Parameters"]["Defaulted"], original["Parameters"]["Defaulted"])
        self.assertNotIn("Defaulted", self.omit(source, ("OptionalInput", "Defaulted"))["Parameters"])
        source["Resources"]["Kept"]["Properties"]["StillNeeded"] = {"Ref": "OptionalInput"}
        with self.assertRaisesRegex(ValueError, "^cloudformation-parameter-still-mentioned$"):
            self.omit(source)
        self.assertEqual(source["Parameters"], original["Parameters"])

    def test_omission_rejects_surviving_nested_references_substitutions_and_plain_mentions(self):
        expressions = [{"Ref": "OptionalInput"}, {"Fn::Sub": "${OptionalInput}"},
                       {"Fn::Sub": "${!OptionalInput}"},
                       {"Fn::Sub": ["${Local}", {"Local": {"Ref": "OptionalInput"}}]},
                       {"Fn::Sub": ["${OptionalInput}", {"OptionalInput": "local-shadow"}]},
                       {"Fn::Sub": ["literal", {"OptionalInput": "unused-map-entry"}]},
                       {"Fn::GetAtt": ["External", "OptionalInput"]},
                       {"Fn::Join": ["-", ["literal", {"Ref": "OptionalInput"}]]},
                       ["nested", ({"NestedOptionalInputKey": "literal"},)],
                       "prefix-OptionalInput-suffix", "${!OptionalInput}"]
        for expression in expressions:
            source = self.omission_source(); source["Resources"]["Kept"]["Properties"]["Mention"] = expression
            original = copy.deepcopy(source)
            with self.subTest(expression=expression), self.assertRaisesRegex(ValueError, "^cloudformation-parameter-still-mentioned$"):
                self.omit(source)
            self.assertEqual(source, original)

    def test_omission_inspects_metadata_keys_other_parameters_conditions_and_outputs(self):
        changes = [lambda d: d.update(Description="OptionalInput is still described"),
                   lambda d: d.update(Metadata={"Nested": {"OptionalInputMetadata": "literal"}}),
                   lambda d: d["Parameters"]["UnselectedInput"].update(Description="OptionalInput"),
                   lambda d: d["Parameters"].update(PrefixedOptionalInput={"Type": "String"}),
                   lambda d: d["Conditions"].update(Mention={"Fn::Equals": ["OptionalInput", "literal"]}),
                   lambda d: d["Outputs"].update(Mention={"Value": "OptionalInput"}),
                   lambda d: d["Outputs"].update(OptionalInputKey={"Value": "literal"})]
        for change in changes:
            source = self.omission_source(); change(source)
            with self.assertRaisesRegex(ValueError, "^cloudformation-parameter-still-mentioned$"):
                self.omit(source)

    def test_omission_validates_all_candidates_before_deleting_any_declaration(self):
        source = self.omission_source()
        source["Parameters"]["SecondInput"] = {"Type": "String", "Description": "OptionalInput"}
        original = copy.deepcopy(source)
        for names in (("OptionalInput", "SecondInput"), ("SecondInput", "OptionalInput")):
            with self.assertRaisesRegex(ValueError, "^cloudformation-parameter-still-mentioned$"):
                self.omit(source, names)
            self.assertEqual(source, original)
        source["Parameters"]["SecondInput"].pop("Description")
        result = self.omit(source, ("OptionalInput", "SecondInput"))
        self.assertEqual(set(result["Parameters"]), {"Enabled", "UnselectedInput", "Defaulted"})

    def test_omission_rejects_original_macros_and_unknown_intrinsics_even_in_removed_resources(self):
        expressions = [{"Transform": "private-canary"}, {"Fn::Transform": {"Name": "private-canary"}},
                       {"Fn::ForEach": ["Item", [], {}]}, {"Fn::ForEach::Loop": ["Item", [], {}]},
                       {"Fn::ImportValue": "private-canary"}, {"Fn::UnknownFuture": "private-canary"},
                       {"Fn::FindInMap": ["Map", "Key", "Value"]}, {"Fn::Select": [0, ["literal"]]}]
        for expression in expressions:
            for section in ("top", "removed", "kept"):
                source = self.omission_source()
                if section == "top": source.update(expression)
                else: source["Resources"]["Removed" if section == "removed" else "Kept"]["Properties"]["Hidden"] = expression
                with self.subTest(expression=expression, section=section), self.assertRaisesRegex(ValueError, "^cloudformation-parameter-omission-unsupported$"):
                    self.omit(source)
                self.cf.project_parameters(source, ("Enabled",), condition_names=("Selected",))
        for tag in ("!Transform", "!ForEach", "!ForEach::Loop", "!UnknownFuture"):
            raw = "Parameters:\n  Enabled: {Type: String, Default: 'false'}\n  OptionalInput: {Type: String}\nMetadata: " + tag + " private-canary\n"
            with self.assertRaisesRegex(ValueError, "^cloudformation-parameter-omission-unsupported$"):
                self.cf.project_parameters(raw, ("Enabled",), omit_if_unused=("OptionalInput",))

    def test_omission_rejects_dynamic_and_malformed_refs_and_subs_before_removing_guards(self):
        expressions = ["{{resolve:ssm:private-canary}}", {"Ref": {"Fn::Sub": "${Other}"}},
                       {"Ref": ["Other"]}, {"Ref": "${Other}"}, {"Ref": "Other", "Extra": True},
                       {"Ref": "private-canary"}, {"Ref": ""}, {"Fn::Sub": None}, {"Fn::Sub": {}},
                       {"Fn::Sub": ["literal"]}, {"Fn::Sub": ["literal", {}, "extra"]},
                       {"Fn::Sub": ["literal", []]}, {"Fn::Sub": [None, {}]},
                       {"Fn::Sub": ["literal", {"bad-key": "private-canary"}]},
                       *({"Fn::Sub": ["${Local}", {"Local": value}]} for value in
                         (None, True, 1, [], {}, {"Unknown": "private-canary"}, {"Fn::Equals": [1, 1]})),
                       {"Fn::Sub": "${Other", "Extra": True}, {"Fn::Sub": "${}"},
                       {"Fn::Sub": "${bad-key}"}, {"Fn::Sub": "${Nested${Other}}"},
                       {"Fn::Sub": "{{resolve:secretsmanager:private-canary}}"}]
        for expression in expressions:
            source = self.omission_source(); source["Resources"]["Removed"]["Properties"]["Hidden"] = expression
            with self.subTest(expression=expression), self.assertRaisesRegex(ValueError, "^cloudformation-parameter-omission-unsupported$"):
                self.omit(source)
        source = self.omission_source(); source["Metadata"] = {"{{resolve:ssm:private-canary}}": "literal"}
        with self.assertRaisesRegex(ValueError, "^cloudformation-parameter-omission-unsupported$"):
            self.omit(source)

    def owned_secret_source(self):
        source = self.omission_source()
        source["Resources"]["OwnedSecret"] = {"Type": "AWS::SecretsManager::Secret",
                                               "Properties": {"GenerateSecretString": {"GenerateStringKey": "password"}}}
        source["Resources"]["Kept"]["Properties"]["Password"] = {
            "Fn::Sub": "{{resolve:secretsmanager:${OwnedSecret}:SecretString:password}}"}
        return source

    def test_omission_preserves_only_opaque_owned_secret_and_rejects_removed_secret(self):
        source = self.owned_secret_source(); original = copy.deepcopy(source)
        result = self.omit(source)
        self.assertEqual(result["Resources"]["Kept"]["Properties"]["Password"],
                         original["Resources"]["Kept"]["Properties"]["Password"])
        self.assertNotIn("OptionalInput", result["Parameters"])
        self.assertEqual(source, original)
        self.assertEqual(self.cf.project_parameters(source, ("Enabled",))["Resources"], original["Resources"])
        source["Resources"]["OwnedSecret"]["Condition"] = "Selected"
        with self.assertRaisesRegex(ValueError, "^cloudformation-removed-resource-reference$"):
            self.omit(source)

    def test_omission_rejects_external_constructed_misplaced_or_parameter_dependent_secrets(self):
        source = self.owned_secret_source()
        expression = source["Resources"]["Kept"]["Properties"]["Password"]["Fn::Sub"]
        malformed = [expression.replace("OwnedSecret", "UnknownSecret"),
                     expression.replace("${OwnedSecret}", "external-secret"),
                     expression.replace("secretsmanager:", "ssm:"),
                     expression.replace("password}}", "password:AWSCURRENT}}"),
                     expression.replace("password}}", "password::version}}"),
                     expression.replace("password", "${UnselectedInput}"),
                     expression.replace("password", "OptionalInput"), expression.replace("password", "Enabled"),
                     expression + "suffix", "prefix" + expression, expression[:-1]]
        for value in malformed:
            for location in ("Kept", "Removed"):
                changed = copy.deepcopy(source)
                changed["Resources"][location]["Properties"]["Password"] = {"Fn::Sub": value}
                with self.subTest(value=value, location=location), self.assertRaisesRegex(ValueError, "^cloudformation-parameter-omission-unsupported$"):
                    self.omit(changed)
        for change in (
                lambda d: d["Resources"]["OwnedSecret"].update(Type="AWS::Example::Resource"),
                lambda d: d.update(Metadata={"Password": {"Fn::Sub": expression}}),
                lambda d: d["Outputs"].update(Secret={"Value": {"Fn::Sub": expression}}),
                lambda d: d["Resources"]["Kept"]["Properties"].update(Password=expression),
                lambda d: d["Resources"]["Kept"]["Properties"].update(Password={"Fn::Sub": [expression, {}]}),
                lambda d: d["Resources"]["Kept"]["Properties"].update(Password={"Fn::Sub": ["${Local}", {"Local": {"Fn::Sub": expression}}]})):
            changed = copy.deepcopy(source); change(changed)
            with self.assertRaisesRegex(ValueError, "^cloudformation-parameter-omission-unsupported$"):
                self.omit(changed)


class PrivateNetworkTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("foundation_template", Path(__file__).with_name("cloudformation-template.py"))
        cls.cf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.cf)
        cls.path = Path(__file__).resolve().parents[5] / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/private-network.yml"

    def assert_private_graph(self, template):
        """Exact owned references reject shared adoption and added public paths."""
        ref = lambda name: {"Ref": name}
        tags = lambda suffix: [{"Key": "Name", "Value": {"Fn::Sub": "${ResourceNamePrefix}-" + suffix}}]
        expected = {"Vpc": {"Type": "AWS::EC2::VPC", "Properties": {
            "CidrBlock": ref("VpcCidr"), "EnableDnsSupport": True,
            "EnableDnsHostnames": True, "InstanceTenancy": "default", "Tags": tags("private")}}}
        for ordinal in ("One", "Two"):
            expected["PrivateSubnet" + ordinal] = {"Type": "AWS::EC2::Subnet", "Properties": {
                "VpcId": ref("Vpc"), "CidrBlock": ref("PrivateSubnet" + ordinal + "Cidr"),
                "AvailabilityZone": ref("AvailabilityZone" + ordinal), "MapPublicIpOnLaunch": False,
                "Tags": tags("private-" + ordinal.lower())}}
            expected["PrivateRouteTable" + ordinal] = {"Type": "AWS::EC2::RouteTable", "Properties": {
                "VpcId": ref("Vpc"), "Tags": tags("private-" + ordinal.lower())}}
            expected["PrivateSubnet" + ordinal + "RouteAssociation"] = {"Type": "AWS::EC2::SubnetRouteTableAssociation", "Properties": {
                "SubnetId": ref("PrivateSubnet" + ordinal), "RouteTableId": ref("PrivateRouteTable" + ordinal)}}
        expected["S3GatewayEndpoint"] = {"Type": "AWS::EC2::VPCEndpoint", "Properties": {
            "VpcId": ref("Vpc"), "VpcEndpointType": "Gateway", "ServiceName": {"Fn::Sub": "com.amazonaws.${AWS::Region}.s3"},
            "RouteTableIds": [ref("PrivateRouteTableOne"), ref("PrivateRouteTableTwo")],
            "PolicyDocument": {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": "*",
                "Action": "s3:GetObject", "Resource": {"Fn::Sub": "arn:${AWS::Partition}:s3:::prod-${AWS::Region}-starport-layer-bucket/*"}}]},
            "Tags": tags("image-layers")}}
        self.assertTrue(self.cf.templates_equal({"Resources": expected}, {"Resources": template["Resources"]}))
        self.assertEqual(template["Outputs"], {
            "VpcId": {"Value": ref("Vpc")}, "VpcCidr": {"Value": {"Fn::GetAtt": ["Vpc", "CidrBlock"]}},
            "PrivateSubnetIds": {"Value": {"Fn::Join": [",", [ref("PrivateSubnetOne"), ref("PrivateSubnetTwo")]]}},
            "PrivateRouteTableIds": {"Value": {"Fn::Join": [",", [ref("PrivateRouteTableOne"), ref("PrivateRouteTableTwo")]]}},
            "S3GatewayEndpointId": {"Value": ref("S3GatewayEndpoint")}})

    def test_owned_private_template_graph(self):
        self.assert_private_graph(self.cf.template(self.path.read_text()))

    def test_explicit_bounded_inputs_and_two_zone_rules(self):
        template = self.cf.template(self.path.read_text())
        self.assertEqual(set(template), {"AWSTemplateFormatVersion", "Description", "Metadata", "Parameters", "Rules", "Resources", "Outputs"})
        self.assertEqual(template["Metadata"], {"CreationControls": {}})
        parameters = template["Parameters"]
        self.assertEqual(set(parameters), {"ResourceNamePrefix", "VpcCidr", "PrivateSubnetOneCidr", "PrivateSubnetTwoCidr", "AvailabilityZoneOne", "AvailabilityZoneTwo"})
        self.assertTrue(all("Default" not in parameter for parameter in parameters.values()))
        prefix = parameters["ResourceNamePrefix"]
        self.assertEqual((prefix["MinLength"], prefix["MaxLength"], prefix["Type"]), (1, 40, "String"))
        for value in ("production", "temporary-a1", "a"):
            self.assertIsNotNone(re.fullmatch(prefix["AllowedPattern"], value))
        for value in ("", "-prefix", "prefix-", "Uppercase", "with.dot", "with/slash", "with space"):
            self.assertIsNone(re.fullmatch(prefix["AllowedPattern"], value))
        # Only lexical bounds are claimed here; source preflight must separately
        # prove canonical addresses, subnet containment, non-overlap and AZ availability.
        for name in ("VpcCidr", "PrivateSubnetOneCidr", "PrivateSubnetTwoCidr"):
            self.assertEqual(parameters[name]["Type"], "String")
            for value in ("10.72.0.0/16", "172.16.1.0/24", "192.168.2.0/28"):
                self.assertIsNotNone(re.fullmatch(parameters[name]["AllowedPattern"], value))
            for value in ("", "0.0.0.0/0", "8.8.8.0/24", "172.32.0.0/16", "10.0.0.0/15", "10.0.0.0/29", "::/64"):
                self.assertIsNone(re.fullmatch(parameters[name]["AllowedPattern"], value))
        for name in ("AvailabilityZoneOne", "AvailabilityZoneTwo"):
            self.assertEqual(parameters[name], {"Type": "AWS::EC2::AvailabilityZone::Name"})
        self.assertEqual(set(template["Rules"]), {"DistinctAvailabilityZones", "DistinctSubnetCidrs"})
        for rule, names in (("DistinctAvailabilityZones", ["AvailabilityZoneOne", "AvailabilityZoneTwo"]),
                            ("DistinctSubnetCidrs", ["PrivateSubnetOneCidr", "PrivateSubnetTwoCidr"])):
            assertions = template["Rules"][rule]["Assertions"]
            self.assertEqual(len(assertions), 1)
            self.assertEqual(assertions[0]["Assert"], {"Fn::Not": [{"Fn::Equals": [{"Ref": name} for name in names]}]})

    def test_assertions_reject_public_shared_or_overbroad_counterexamples(self):
        original = self.cf.template(self.path.read_text())
        counterexamples = [
            lambda d: d["Resources"]["PrivateSubnetOne"]["Properties"].update(MapPublicIpOnLaunch=True),
            lambda d: d["Resources"]["PrivateSubnetOne"]["Properties"].update(VpcId="vpc-existing"),
            lambda d: d["Resources"]["Vpc"]["Properties"].update(EnableDnsSupport=False),
            lambda d: d["Resources"].update(PublicGateway={"Type": "AWS::EC2::InternetGateway"}),
            lambda d: d["Resources"].update(NatGateway={"Type": "AWS::EC2::NatGateway"}),
            lambda d: d["Resources"]["PrivateSubnetTwoRouteAssociation"]["Properties"].update(RouteTableId={"Ref": "PrivateRouteTableOne"}),
            lambda d: d["Resources"]["S3GatewayEndpoint"]["Properties"].update(RouteTableIds=[{"Ref": "PrivateRouteTableOne"}]),
            lambda d: d["Resources"]["S3GatewayEndpoint"]["Properties"]["PolicyDocument"]["Statement"][0].update(Resource="*"),
            lambda d: d["Resources"]["S3GatewayEndpoint"]["Properties"]["PolicyDocument"]["Statement"][0].update(Action="s3:*"),
            lambda d: d["Outputs"]["VpcId"].update(Value="vpc-existing"),
        ]
        for index, change in enumerate(counterexamples):
            changed = copy.deepcopy(original); change(changed)
            with self.subTest(index=index), self.assertRaises(AssertionError):
                self.assert_private_graph(changed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
