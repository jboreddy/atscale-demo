"""IAM Stack - Roles and policies for cross-service access."""

from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_s3 as s3,
    aws_eks as eks,
    CfnOutput,
)
from constructs import Construct


class IamStack(Stack):
    """Creates IAM roles for Redshift COPY, AtScale (IRSA), and Bedrock access."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        bucket: s3.Bucket,
        cluster: eks.Cluster,
        aurora_secret_arn: str,
        redshift_secret_arn: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_name = self.node.try_get_context("project_name")

        # ─────────────────────────────────────────────
        # Redshift COPY Role (for loading data from S3)
        # ─────────────────────────────────────────────
        self.redshift_copy_role = iam.Role(
            self,
            "RedshiftCopyRole",
            role_name=f"{project_name}-redshift-s3-access",
            assumed_by=iam.ServicePrincipal("redshift.amazonaws.com"),
            description="Allows Redshift to COPY data from S3 staging bucket",
        )

        bucket.grant_read(self.redshift_copy_role, "staging/*")
        bucket.grant_read(self.redshift_copy_role, "csv/*")

        # ─────────────────────────────────────────────
        # AtScale Service Account (IRSA on EKS)
        # ─────────────────────────────────────────────
        self.atscale_sa = cluster.add_service_account(
            "AtScaleServiceAccount",
            name="atscale-service",
            namespace="atscale",
        )

        # AtScale needs S3 access for aggregate storage
        bucket.grant_read_write(self.atscale_sa, "aggregates/*")

        # AtScale needs access to DB secrets
        self.atscale_sa.add_to_principal_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[aurora_secret_arn, redshift_secret_arn],
            )
        )

        # ─────────────────────────────────────────────
        # Bedrock Access (IRSA for Agent/App pod)
        # ─────────────────────────────────────────────
        self.bedrock_sa = cluster.add_service_account(
            "BedrockServiceAccount",
            name="bedrock-agent",
            namespace="c360-app",
        )

        self.bedrock_sa.add_to_principal_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=[
                    f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-sonnet-4-6-v1:0",
                    f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.*",
                ],
            )
        )

        # App also needs secrets access for AtScale credentials
        self.bedrock_sa.add_to_principal_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[
                    aurora_secret_arn,
                    redshift_secret_arn,
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:c360/atscale/*",
                ],
            )
        )

        # ─────────────────────────────────────────────
        # Outputs
        # ─────────────────────────────────────────────
        CfnOutput(
            self,
            "RedshiftCopyRoleArn",
            value=self.redshift_copy_role.role_arn,
        )
        CfnOutput(
            self,
            "AtScaleServiceAccountArn",
            value=self.atscale_sa.role.role_arn,
        )
        CfnOutput(
            self,
            "BedrockServiceAccountArn",
            value=self.bedrock_sa.role.role_arn,
        )
