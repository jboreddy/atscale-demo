"""Networking Stack - VPC, Subnets, NAT Gateway, Security Groups."""

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    CfnOutput,
)
from constructs import Construct


class NetworkingStack(Stack):
    """Creates VPC with public/private subnets and security groups."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_name = self.node.try_get_context("project_name")
        vpc_cidr = self.node.try_get_context("vpc_cidr")

        # VPC with 2 AZs, public + private subnets
        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=f"{project_name}-vpc",
            ip_addresses=ec2.IpAddresses.cidr(vpc_cidr),
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )

        # Security Group: ALB (public-facing)
        self.sg_alb = ec2.SecurityGroup(
            self,
            "SgAlb",
            vpc=self.vpc,
            security_group_name=f"{project_name}-sg-alb",
            description="ALB - public HTTP/HTTPS access",
            allow_all_outbound=True,
        )
        self.sg_alb.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "HTTP from internet",
        )
        self.sg_alb.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(443),
            "HTTPS from internet",
        )

        # Security Group: EKS Nodes
        self.sg_eks_nodes = ec2.SecurityGroup(
            self,
            "SgEksNodes",
            vpc=self.vpc,
            security_group_name=f"{project_name}-sg-eks-nodes",
            description="EKS worker nodes",
            allow_all_outbound=True,
        )
        # Self-referencing rule for pod-to-pod communication
        self.sg_eks_nodes.add_ingress_rule(
            self.sg_eks_nodes,
            ec2.Port.all_traffic(),
            "Pod-to-pod communication",
        )
        # ALB to EKS nodes (health checks + traffic)
        self.sg_eks_nodes.add_ingress_rule(
            self.sg_alb,
            ec2.Port.tcp(443),
            "ALB health checks",
        )
        self.sg_eks_nodes.add_ingress_rule(
            self.sg_alb,
            ec2.Port.tcp(8501),
            "Streamlit via ALB",
        )
        self.sg_eks_nodes.add_ingress_rule(
            self.sg_alb,
            ec2.Port.tcp(10500),
            "AtScale Design Center via ALB",
        )

        # Security Group: Aurora PostgreSQL
        self.sg_aurora = ec2.SecurityGroup(
            self,
            "SgAurora",
            vpc=self.vpc,
            security_group_name=f"{project_name}-sg-aurora",
            description="Aurora PostgreSQL - access from EKS",
            allow_all_outbound=True,
        )
        self.sg_aurora.add_ingress_rule(
            self.sg_eks_nodes,
            ec2.Port.tcp(5432),
            "PostgreSQL from EKS nodes",
        )

        # Security Group: Redshift Serverless
        self.sg_redshift = ec2.SecurityGroup(
            self,
            "SgRedshift",
            vpc=self.vpc,
            security_group_name=f"{project_name}-sg-redshift",
            description="Redshift Serverless - access from EKS",
            allow_all_outbound=True,
        )
        self.sg_redshift.add_ingress_rule(
            self.sg_eks_nodes,
            ec2.Port.tcp(5439),
            "Redshift from EKS nodes",
        )

        # Outputs
        CfnOutput(self, "VpcId", value=self.vpc.vpc_id)
        CfnOutput(
            self,
            "PrivateSubnetIds",
            value=",".join(
                [s.subnet_id for s in self.vpc.private_subnets]
            ),
        )
        CfnOutput(
            self,
            "PublicSubnetIds",
            value=",".join(
                [s.subnet_id for s in self.vpc.public_subnets]
            ),
        )
