"""EKS Stack - Amazon EKS cluster with managed node group and add-ons."""

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_eks as eks,
    aws_iam as iam,
    lambda_layer_kubectl_v31 as kubectl_v31,
    CfnOutput,
)
from constructs import Construct


class EksStack(Stack):
    """Creates EKS cluster with managed node group for AtScale and application workloads."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        sg_eks_nodes: ec2.SecurityGroup,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_name = self.node.try_get_context("project_name")
        cluster_name = self.node.try_get_context("eks_cluster_name")
        eks_version_str = self.node.try_get_context("eks_version")

        # Map version string to CDK KubernetesVersion
        k8s_version = eks.KubernetesVersion.of(eks_version_str)

        # EKS Cluster master role
        cluster_admin_role = iam.Role(
            self,
            "ClusterAdminRole",
            role_name=f"{project_name}-eks-admin",
            assumed_by=iam.AccountRootPrincipal(),
        )

        # EKS Cluster
        self.cluster = eks.Cluster(
            self,
            "EksCluster",
            cluster_name=cluster_name,
            version=k8s_version,
            kubectl_layer=kubectl_v31.KubectlV31Layer(self, "KubectlLayer"),
            vpc=vpc,
            vpc_subnets=[
                ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
            ],
            default_capacity=0,
            masters_role=cluster_admin_role,
            endpoint_access=eks.EndpointAccess.PUBLIC_AND_PRIVATE,
            cluster_logging=[
                eks.ClusterLoggingTypes.API,
                eks.ClusterLoggingTypes.AUDIT,
                eks.ClusterLoggingTypes.AUTHENTICATOR,
            ],
        )

        # Managed Node Group
        self.cluster.add_nodegroup_capacity(
            "WorkerNodes",
            nodegroup_name=f"{project_name}-workers",
            instance_types=[ec2.InstanceType("m5.2xlarge")],
            min_size=2,
            max_size=4,
            desired_size=2,
            disk_size=100,
            ami_type=eks.NodegroupAmiType.AL2023_X86_64_STANDARD,
            subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )

        # Add EBS CSI Driver add-on (for AtScale persistent volumes)
        eks.CfnAddon(
            self,
            "EbsCsiDriver",
            addon_name="aws-ebs-csi-driver",
            cluster_name=self.cluster.cluster_name,
            resolve_conflicts="OVERWRITE",
        )

        # Create namespace for AtScale
        self.cluster.add_manifest(
            "AtScaleNamespace",
            {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {"name": "atscale"},
            },
        )

        # Create namespace for application
        self.cluster.add_manifest(
            "AppNamespace",
            {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {"name": "c360-app"},
            },
        )

        # AWS Load Balancer Controller (via Helm)
        lb_controller_sa = self.cluster.add_service_account(
            "LbControllerSa",
            name="aws-load-balancer-controller",
            namespace="kube-system",
        )

        lb_controller_policy_statements = [
            iam.PolicyStatement(
                actions=[
                    "ec2:Describe*",
                    "elasticloadbalancing:*",
                    "iam:CreateServiceLinkedRole",
                    "cognito-idp:DescribeUserPoolClient",
                    "acm:ListCertificates",
                    "acm:DescribeCertificate",
                    "waf-regional:*",
                    "wafv2:*",
                    "shield:*",
                    "tag:GetResources",
                    "tag:TagResources",
                ],
                resources=["*"],
            )
        ]

        for stmt in lb_controller_policy_statements:
            lb_controller_sa.add_to_principal_policy(stmt)

        self.cluster.add_helm_chart(
            "LbController",
            chart="aws-load-balancer-controller",
            repository="https://aws.github.io/eks-charts",
            namespace="kube-system",
            release="aws-load-balancer-controller",
            values={
                "clusterName": self.cluster.cluster_name,
                "serviceAccount": {
                    "create": False,
                    "name": "aws-load-balancer-controller",
                },
                "region": self.region,
                "vpcId": vpc.vpc_id,
            },
        )

        # Outputs
        CfnOutput(self, "ClusterName", value=self.cluster.cluster_name)
        CfnOutput(
            self,
            "ClusterEndpoint",
            value=self.cluster.cluster_endpoint,
        )
        CfnOutput(
            self,
            "ClusterOidcProviderArn",
            value=self.cluster.open_id_connect_provider.open_id_connect_provider_arn,
        )
        CfnOutput(
            self,
            "KubectlCommand",
            value=f"aws eks update-kubeconfig --name {cluster_name} --region {self.region}",
        )
