"""Storage Stack - S3 bucket for data staging and AtScale aggregates."""

from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_s3 as s3,
    CfnOutput,
)
from constructs import Construct


class StorageStack(Stack):
    """Creates S3 bucket for CSV staging and AtScale aggregate storage."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_name = self.node.try_get_context("project_name")
        account = self.node.try_get_context("aws_account")
        region = self.node.try_get_context("aws_region")

        bucket_name = f"{self.node.try_get_context('s3_bucket_prefix')}-{account}-{region}"

        # S3 Bucket for data staging and aggregates
        self.bucket = s3.Bucket(
            self,
            "DataBucket",
            bucket_name=bucket_name,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="delete-staging-after-7-days",
                    prefix="staging/",
                    expiration=Duration.days(7),
                    enabled=True,
                ),
            ],
        )

        # Outputs
        CfnOutput(self, "BucketName", value=self.bucket.bucket_name)
        CfnOutput(self, "BucketArn", value=self.bucket.bucket_arn)
