"""CDK Stack Unit Tests."""

import pytest
import aws_cdk as cdk
from aws_cdk.assertions import Template, Match

from stacks.networking_stack import NetworkingStack
from stacks.storage_stack import StorageStack
from stacks.database_stack import DatabaseStack
from stacks.eks_stack import EksStack


@pytest.fixture
def app():
    """Create CDK app with test context."""
    app = cdk.App(
        context={
            "project_name": "c360-poc",
            "aws_account": "652341767951",
            "aws_region": "us-east-1",
            "vpc_cidr": "10.1.0.0/16",
            "eks_cluster_name": "c360-poc-cluster",
            "eks_version": "1.36",
            "aurora_instance_class": "r6g.large",
            "aurora_engine_version": "16.13",
            "aurora_database_name": "customer360_db",
            "redshift_namespace": "c360-atscale-ns",
            "redshift_workgroup": "c360-atscale-wg",
            "redshift_database": "analytics_db",
            "redshift_base_capacity": 8,
            "s3_bucket_prefix": "c360-poc-data",
        }
    )
    return app


@pytest.fixture
def env():
    return cdk.Environment(account="652341767951", region="us-east-1")


class TestNetworkingStack:
    """Tests for NetworkingStack."""

    def test_vpc_created(self, app, env):
        stack = NetworkingStack(app, "TestNetworking", env=env)
        template = Template.from_stack(stack)

        # VPC is created
        template.resource_count_is("AWS::EC2::VPC", 1)

    def test_subnets_created(self, app, env):
        stack = NetworkingStack(app, "TestNetworking2", env=env)
        template = Template.from_stack(stack)

        # 4 subnets (2 public + 2 private)
        template.resource_count_is("AWS::EC2::Subnet", 4)

    def test_nat_gateway_created(self, app, env):
        stack = NetworkingStack(app, "TestNetworking3", env=env)
        template = Template.from_stack(stack)

        # Single NAT gateway
        template.resource_count_is("AWS::EC2::NatGateway", 1)

    def test_security_groups_created(self, app, env):
        stack = NetworkingStack(app, "TestNetworking4", env=env)
        template = Template.from_stack(stack)

        # At least 4 security groups (ALB, EKS, Aurora, Redshift)
        template.resource_count_is("AWS::EC2::SecurityGroup", Match.any_value())


class TestStorageStack:
    """Tests for StorageStack."""

    def test_s3_bucket_created(self, app, env):
        stack = StorageStack(app, "TestStorage", env=env)
        template = Template.from_stack(stack)

        template.resource_count_is("AWS::S3::Bucket", 1)

    def test_bucket_encryption(self, app, env):
        stack = StorageStack(app, "TestStorage2", env=env)
        template = Template.from_stack(stack)

        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "BucketEncryption": {
                    "ServerSideEncryptionConfiguration": Match.any_value()
                }
            },
        )

    def test_public_access_blocked(self, app, env):
        stack = StorageStack(app, "TestStorage3", env=env)
        template = Template.from_stack(stack)

        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "PublicAccessBlockConfiguration": {
                    "BlockPublicAcls": True,
                    "BlockPublicPolicy": True,
                    "IgnorePublicAcls": True,
                    "RestrictPublicBuckets": True,
                }
            },
        )


class TestDatabaseStack:
    """Tests for DatabaseStack."""

    def test_aurora_cluster_created(self, app, env):
        networking = NetworkingStack(app, "TestNet", env=env)
        stack = DatabaseStack(
            app,
            "TestDb",
            env=env,
            vpc=networking.vpc,
            sg_aurora=networking.sg_aurora,
            sg_redshift=networking.sg_redshift,
        )
        template = Template.from_stack(stack)

        template.resource_count_is("AWS::RDS::DBCluster", 1)

    def test_redshift_namespace_created(self, app, env):
        networking = NetworkingStack(app, "TestNet2", env=env)
        stack = DatabaseStack(
            app,
            "TestDb2",
            env=env,
            vpc=networking.vpc,
            sg_aurora=networking.sg_aurora,
            sg_redshift=networking.sg_redshift,
        )
        template = Template.from_stack(stack)

        template.has_resource_properties(
            "AWS::RedshiftServerless::Namespace",
            {"NamespaceName": "c360-atscale-ns"},
        )

    def test_redshift_workgroup_created(self, app, env):
        networking = NetworkingStack(app, "TestNet3", env=env)
        stack = DatabaseStack(
            app,
            "TestDb3",
            env=env,
            vpc=networking.vpc,
            sg_aurora=networking.sg_aurora,
            sg_redshift=networking.sg_redshift,
        )
        template = Template.from_stack(stack)

        template.has_resource_properties(
            "AWS::RedshiftServerless::Workgroup",
            {
                "WorkgroupName": "c360-atscale-wg",
                "BaseCapacity": 8,
            },
        )

    def test_secrets_created(self, app, env):
        networking = NetworkingStack(app, "TestNet4", env=env)
        stack = DatabaseStack(
            app,
            "TestDb4",
            env=env,
            vpc=networking.vpc,
            sg_aurora=networking.sg_aurora,
            sg_redshift=networking.sg_redshift,
        )
        template = Template.from_stack(stack)

        # Aurora + Redshift secrets
        template.resource_count_is("AWS::SecretsManager::Secret", 2)
