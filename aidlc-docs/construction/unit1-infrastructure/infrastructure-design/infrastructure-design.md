# Infrastructure Design - Unit 1: Infrastructure

## Overview

This document maps the logical components identified in Application Design to concrete AWS services deployed via AWS CDK (Python) in account **652341767951** (us-east-1).

---

## AWS Service Mapping

| Logical Component | AWS Service | Configuration |
|-------------------|-------------|---------------|
| Network | Amazon VPC | 10.1.0.0/16, 2 AZs, public + private subnets |
| Container Platform | Amazon EKS | K8s 1.36, managed nodes m5.2xlarge |
| Operational Database | Aurora PostgreSQL | 16.13, db.r6g.large, single-AZ |
| Analytics Database | Redshift Serverless | 8 RPU, customer360 namespace |
| Object Storage | Amazon S3 | Standard tier, SSE-S3 encryption |
| Model Inference | Amazon Bedrock | Claude Sonnet 4.6 |
| Secrets | AWS Secrets Manager | DB credentials, AtScale tokens |
| DNS/Ingress | AWS ALB | Via ALB Ingress Controller on EKS |
| Container Registry | Amazon ECR | For custom images (if needed) |
| Logging | CloudWatch Logs | EKS Container Insights |

---

## CDK Stack Architecture

```
C360InfraApp (CDK App)
│
├── NetworkingStack
│   ├── VPC (10.1.0.0/16)
│   ├── Public Subnet A (10.1.1.0/24) - us-east-1a
│   ├── Public Subnet B (10.1.2.0/24) - us-east-1b
│   ├── Private Subnet A (10.1.10.0/24) - us-east-1a
│   ├── Private Subnet B (10.1.11.0/24) - us-east-1b
│   ├── Internet Gateway
│   ├── NAT Gateway (1x, in Public Subnet A)
│   ├── Security Groups:
│   │   ├── sg-eks-nodes (self-referencing + ALB ingress)
│   │   ├── sg-aurora (5432 from sg-eks-nodes)
│   │   ├── sg-redshift (5439 from sg-eks-nodes)
│   │   ├── sg-alb (80/443 from 0.0.0.0/0)
│   │   └── sg-streamlit (8501 from sg-alb)
│   └── Exports: vpc_id, subnet_ids, sg_ids
│
├── StorageStack (depends on: NetworkingStack)
│   ├── S3 Bucket: c360-poc-data-652341767951-us-east-1
│   │   ├── Encryption: SSE-S3
│   │   ├── Lifecycle: Delete staging/* after 7 days
│   │   └── Block public access: enabled
│   └── Exports: bucket_name, bucket_arn
│
├── DatabaseStack (depends on: NetworkingStack)
│   ├── Aurora PostgreSQL Cluster
│   │   ├── Engine: Aurora PostgreSQL 16.13
│   │   ├── Instance: db.r6g.large (1 writer, 0 readers for POC)
│   │   ├── Database name: customer360_db
│   │   ├── Master username: postgres
│   │   ├── Master password: Generated → Secrets Manager
│   │   ├── Subnet group: Private subnets
│   │   ├── Security group: sg-aurora
│   │   ├── Encryption at rest: AWS KMS (default key)
│   │   ├── Backup retention: 1 day
│   │   └── Deletion protection: disabled (POC)
│   │
│   ├── Redshift Serverless
│   │   ├── Namespace: c360-atscale-ns
│   │   ├── Workgroup: c360-atscale-wg
│   │   ├── Base capacity: 8 RPU
│   │   ├── Database: analytics_db
│   │   ├── Admin user: admin
│   │   ├── Admin password: Generated → Secrets Manager
│   │   ├── Subnet group: Private subnets
│   │   ├── Security group: sg-redshift
│   │   └── Encryption: AWS KMS (default key)
│   │
│   └── Exports: aurora_endpoint, aurora_secret_arn, redshift_endpoint, redshift_secret_arn
│
├── EksStack (depends on: NetworkingStack, StorageStack)
│   ├── EKS Cluster
│   │   ├── Name: c360-poc-cluster
│   │   ├── Version: 1.36
│   │   ├── VPC: from NetworkingStack
│   │   ├── Subnets: Private
│   │   ├── Endpoint access: Public + Private
│   │   └── Logging: API, Audit, Authenticator
│   │
│   ├── Managed Node Group
│   │   ├── Instance type: m5.2xlarge
│   │   ├── Min/Max/Desired: 2/4/2
│   │   ├── Disk size: 100 GB (gp3)
│   │   ├── AMI: Amazon Linux 2023 (AL2023)
│   │   └── Subnets: Private
│   │
│   ├── Add-ons:
│   │   ├── CoreDNS
│   │   ├── kube-proxy
│   │   ├── VPC CNI
│   │   ├── EBS CSI Driver (for AtScale persistent volumes)
│   │   └── AWS Load Balancer Controller (for ALB ingress)
│   │
│   └── Exports: cluster_name, cluster_endpoint, oidc_provider_arn
│
└── IamStack (depends on: all other stacks)
    ├── EKS Node Role
    │   ├── AmazonEKSWorkerNodePolicy
    │   ├── AmazonEKS_CNI_Policy
    │   ├── AmazonEC2ContainerRegistryReadOnly
    │   └── AmazonSSMManagedInstanceCore
    │
    ├── RedshiftCopyRole
    │   ├── Trust: redshift.amazonaws.com
    │   └── Policy: s3:GetObject, s3:ListBucket on staging bucket
    │
    ├── AtScaleServiceRole (EKS Pod Identity / IRSA)
    │   ├── Trust: EKS OIDC provider
    │   └── Policy: s3:* on aggregate bucket prefix
    │
    ├── BedrockAccessRole (for Streamlit/Agent pod)
    │   ├── Trust: EKS OIDC provider
    │   └── Policy: bedrock:InvokeModel (claude-sonnet-4-6)
    │
    ├── Secrets Manager Access
    │   └── Policy: secretsmanager:GetSecretValue on DB secrets
    │
    └── Exports: role_arns
```

---

## Network Topology

```
┌──────────────────────────────────────────────────────────────────────┐
│                     VPC: 10.1.0.0/16                                  │
│                                                                        │
│  ┌─── us-east-1a ────────────────┐  ┌─── us-east-1b ────────────────┐│
│  │                                │  │                                ││
│  │  Public: 10.1.1.0/24          │  │  Public: 10.1.2.0/24          ││
│  │  ┌────────────────────────┐   │  │  ┌────────────────────────┐   ││
│  │  │ NAT Gateway            │   │  │  │ (available for HA)     │   ││
│  │  │ ALB                    │   │  │  │                        │   ││
│  │  └────────────────────────┘   │  │  └────────────────────────┘   ││
│  │                                │  │                                ││
│  │  Private: 10.1.10.0/24        │  │  Private: 10.1.11.0/24        ││
│  │  ┌────────────────────────┐   │  │  ┌────────────────────────┐   ││
│  │  │ EKS Node 1            │   │  │  │ EKS Node 2            │   ││
│  │  │  - AtScale Engine     │   │  │  │  - AtScale Design Ctr  │   ││
│  │  │  - Streamlit Pod      │   │  │  │  - (overflow capacity) │   ││
│  │  │                        │   │  │  │                        │   ││
│  │  │ Aurora Writer          │   │  │  │                        │   ││
│  │  │ Redshift Serverless    │   │  │  │                        │   ││
│  │  └────────────────────────┘   │  │  └────────────────────────┘   ││
│  └────────────────────────────────┘  └────────────────────────────────┘│
│                                                                        │
│  ┌──── Internet Gateway ─────┐                                        │
│  └────────────────────────────┘                                        │
└──────────────────────────────────────────────────────────────────────────┘

External:
  ├── Amazon Bedrock (us-east-1, via AWS SDK/HTTPS)
  ├── GitHub (for C360 CSV download)
  └── User Browser (via ALB)
```

---

## Security Group Rules

| Security Group | Direction | Port | Source/Dest | Purpose |
|---------------|-----------|------|-------------|---------|
| **sg-alb** | Inbound | 80, 443 | 0.0.0.0/0 | Public HTTP/HTTPS |
| **sg-eks-nodes** | Inbound | 443 | sg-alb | ALB health checks |
| **sg-eks-nodes** | Inbound | All | sg-eks-nodes (self) | Pod-to-pod |
| **sg-eks-nodes** | Inbound | 8501 | sg-alb | Streamlit via ALB |
| **sg-eks-nodes** | Inbound | 10500 | sg-alb | AtScale Design Center |
| **sg-aurora** | Inbound | 5432 | sg-eks-nodes | AtScale/Agent → Aurora |
| **sg-redshift** | Inbound | 5439 | sg-eks-nodes | AtScale → Redshift |
| All | Outbound | All | 0.0.0.0/0 | Internet via NAT (Bedrock, GitHub) |

---

## Secrets Manager Layout

| Secret Name | Contents | Used By |
|-------------|----------|---------|
| `c360/aurora/master` | host, port, username, password, dbname | Data loader, AtScale |
| `c360/redshift/admin` | host, port, username, password, dbname | Data loader, AtScale |
| `c360/atscale/admin` | username, password, endpoint | Agent |

---

## Cost Optimization Notes (POC)

1. **Single NAT Gateway** — saves ~$45/mo vs. HA (2x NAT)
2. **Redshift Serverless** — scales to zero when idle
3. **EKS nodes 2x m5.2xlarge** — sufficient for AtScale + Streamlit
4. **Aurora single-AZ** — no reader, no Multi-AZ (saves ~$180/mo)
5. **Spot instances** — consider for EKS nodes (70% savings, acceptable for POC)
6. **Shutdown capability** — CDK makes destroy/redeploy easy

---

## Deployment Prerequisites

Before running `cdk deploy`:
1. AWS CLI configured with admin credentials for account 652341767951
2. CDK bootstrapped: `cdk bootstrap aws://652341767951/us-east-1`
3. Python 3.11+ with `aws-cdk-lib` installed
4. Docker running (for CDK asset bundling)
5. Bedrock model access enabled for Claude Sonnet in us-east-1
