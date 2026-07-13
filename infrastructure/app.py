#!/usr/bin/env python3
"""CDK App - Customer 360 Semantic Layer POC Infrastructure."""

import aws_cdk as cdk

from stacks.networking_stack import NetworkingStack
from stacks.storage_stack import StorageStack
from stacks.database_stack import DatabaseStack
from stacks.eks_stack import EksStack
from stacks.iam_stack import IamStack


app = cdk.App()

# Environment configuration
env = cdk.Environment(
    account=app.node.try_get_context("aws_account"),
    region=app.node.try_get_context("aws_region"),
)

project_name = app.node.try_get_context("project_name")

# ─────────────────────────────────────────────
# Stack 1: Networking (no dependencies)
# ─────────────────────────────────────────────
networking = NetworkingStack(
    app,
    f"{project_name}-networking",
    env=env,
    description="VPC, subnets, NAT gateway, and security groups",
)

# ─────────────────────────────────────────────
# Stack 2: Storage (depends on networking for tags)
# ─────────────────────────────────────────────
storage = StorageStack(
    app,
    f"{project_name}-storage",
    env=env,
    description="S3 bucket for data staging and AtScale aggregates",
)

# ─────────────────────────────────────────────
# Stack 3: Database (depends on networking)
# ─────────────────────────────────────────────
database = DatabaseStack(
    app,
    f"{project_name}-database",
    env=env,
    vpc=networking.vpc,
    sg_aurora=networking.sg_aurora,
    sg_redshift=networking.sg_redshift,
    description="Aurora PostgreSQL and Redshift Serverless",
)
database.add_dependency(networking)

# ─────────────────────────────────────────────
# Stack 4: EKS (depends on networking)
# ─────────────────────────────────────────────
eks_stack = EksStack(
    app,
    f"{project_name}-eks",
    env=env,
    vpc=networking.vpc,
    sg_eks_nodes=networking.sg_eks_nodes,
    description="EKS cluster with managed node group and add-ons",
)
eks_stack.add_dependency(networking)

# ─────────────────────────────────────────────
# Stack 5: IAM (depends on storage, database, EKS)
# ─────────────────────────────────────────────
iam_stack = IamStack(
    app,
    f"{project_name}-iam",
    env=env,
    bucket=storage.bucket,
    cluster=eks_stack.cluster,
    aurora_secret_arn=database.aurora_secret.secret_arn,
    redshift_secret_arn=database.redshift_secret.secret_arn,
    description="IAM roles for Redshift COPY, AtScale, and Bedrock access",
)
iam_stack.add_dependency(storage)
iam_stack.add_dependency(database)
iam_stack.add_dependency(eks_stack)

app.synth()
