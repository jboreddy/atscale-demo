"""Database Stack - Aurora PostgreSQL and Redshift Serverless."""

from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_redshiftserverless as redshift,
    aws_secretsmanager as secretsmanager,
    CfnOutput,
)
from constructs import Construct


class DatabaseStack(Stack):
    """Creates Aurora PostgreSQL cluster and Redshift Serverless namespace/workgroup."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        sg_aurora: ec2.SecurityGroup,
        sg_redshift: ec2.SecurityGroup,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_name = self.node.try_get_context("project_name")
        aurora_db_name = self.node.try_get_context("aurora_database_name")
        redshift_ns_name = self.node.try_get_context("redshift_namespace")
        redshift_wg_name = self.node.try_get_context("redshift_workgroup")
        redshift_db_name = self.node.try_get_context("redshift_database")
        redshift_base_capacity = self.node.try_get_context("redshift_base_capacity")

        # ─────────────────────────────────────────────
        # Aurora PostgreSQL
        # ─────────────────────────────────────────────

        # Aurora credentials in Secrets Manager
        self.aurora_secret = secretsmanager.Secret(
            self,
            "AuroraSecret",
            secret_name=f"c360/aurora/master",
            description="Aurora PostgreSQL master credentials",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "postgres"}',
                generate_string_key="password",
                exclude_punctuation=True,
                password_length=30,
            ),
        )

        # Aurora subnet group
        aurora_subnet_group = rds.SubnetGroup(
            self,
            "AuroraSubnetGroup",
            description="Aurora PostgreSQL subnet group",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )

        # Aurora PostgreSQL Cluster
        self.aurora_cluster = rds.DatabaseCluster(
            self,
            "AuroraCluster",
            cluster_identifier=f"{project_name}-aurora",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_16_4,
            ),
            default_database_name=aurora_db_name,
            credentials=rds.Credentials.from_secret(self.aurora_secret),
            writer=rds.ClusterInstance.provisioned(
                "Writer",
                instance_type=ec2.InstanceType.of(
                    ec2.InstanceClass.R6G, ec2.InstanceSize.LARGE
                ),
            ),
            vpc=vpc,
            subnet_group=aurora_subnet_group,
            security_groups=[sg_aurora],
            storage_encrypted=True,
            backup=rds.BackupProps(retention=Duration.days(1)),
            deletion_protection=False,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ─────────────────────────────────────────────
        # Redshift Serverless
        # ─────────────────────────────────────────────

        # Redshift admin credentials
        self.redshift_secret = secretsmanager.Secret(
            self,
            "RedshiftSecret",
            secret_name="c360/redshift/admin",
            description="Redshift Serverless admin credentials",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "admin"}',
                generate_string_key="password",
                exclude_punctuation=True,
                password_length=30,
            ),
        )

        # Redshift Serverless Namespace
        self.redshift_namespace = redshift.CfnNamespace(
            self,
            "RedshiftNamespace",
            namespace_name=redshift_ns_name,
            admin_username="admin",
            admin_user_password=self.redshift_secret.secret_value_from_json(
                "password"
            ).unsafe_unwrap(),
            db_name=redshift_db_name,
        )

        # Redshift Serverless Workgroup
        private_subnet_ids = [s.subnet_id for s in vpc.private_subnets]

        self.redshift_workgroup = redshift.CfnWorkgroup(
            self,
            "RedshiftWorkgroup",
            workgroup_name=redshift_wg_name,
            namespace_name=redshift_ns_name,
            base_capacity=redshift_base_capacity,
            publicly_accessible=False,
            subnet_ids=private_subnet_ids,
            security_group_ids=[sg_redshift.security_group_id],
        )
        self.redshift_workgroup.add_dependency(self.redshift_namespace)

        # ─────────────────────────────────────────────
        # Outputs
        # ─────────────────────────────────────────────

        CfnOutput(
            self,
            "AuroraEndpoint",
            value=self.aurora_cluster.cluster_endpoint.hostname,
        )
        CfnOutput(
            self,
            "AuroraSecretArn",
            value=self.aurora_secret.secret_arn,
        )
        CfnOutput(
            self,
            "RedshiftNamespaceName",
            value=redshift_ns_name,
        )
        CfnOutput(
            self,
            "RedshiftWorkgroupName",
            value=redshift_wg_name,
        )
        CfnOutput(
            self,
            "RedshiftSecretArn",
            value=self.redshift_secret.secret_arn,
        )


# Need this import at top level for Duration
from aws_cdk import Duration
