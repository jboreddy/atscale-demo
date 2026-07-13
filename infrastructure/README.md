# Infrastructure — AWS CDK (Python)

Provisions all AWS resources for the Customer 360 Semantic Layer POC.

## Stacks

| Stack | Resources |
|-------|-----------|
| **Networking** | VPC (10.1.0.0/16), 4 subnets (2 AZ), NAT, IGW, 5 security groups |
| **Storage** | S3 bucket (staging + aggregates) |
| **Database** | Aurora PostgreSQL 16.13 + Redshift Serverless (c360-atscale-ns) |
| **EKS** | Kubernetes 1.36 cluster, 2× m5.2xlarge nodes, EBS CSI, ALB Controller |
| **IAM** | Roles: Redshift COPY, AtScale IRSA, Bedrock IRSA |

## Prerequisites

1. **AWS CLI v2** configured with admin access to account `652341767951`
2. **Python 3.11+**
3. **Node.js 18+** (required by CDK)
4. **Docker** running (for CDK asset bundling)
5. **CDK CLI**: `npm install -g aws-cdk`

## Setup

```bash
cd infrastructure/

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap aws://652341767951/us-east-1
```

## Deploy

```bash
# Synthesize CloudFormation templates (dry-run)
cdk synth

# Deploy all stacks
cdk deploy --all --require-approval never

# Or deploy individually in order:
cdk deploy c360-poc-networking
cdk deploy c360-poc-storage
cdk deploy c360-poc-database
cdk deploy c360-poc-eks
cdk deploy c360-poc-iam
```

## Verify Deployment

```bash
# Check Aurora endpoint
aws rds describe-db-clusters --query 'DBClusters[?DBClusterIdentifier==`c360-poc-aurora`].Endpoint' --output text

# Check Redshift workgroup
aws redshift-serverless get-workgroup --workgroup-name c360-atscale-wg --query 'workgroup.endpoint.address' --output text

# Configure kubectl
aws eks update-kubeconfig --name c360-poc-cluster --region us-east-1

# Check EKS nodes
kubectl get nodes

# Check S3 bucket
aws s3 ls s3://c360-poc-data-652341767951-us-east-1/
```

## Destroy (Cleanup)

```bash
# Destroy all stacks (removes ALL resources)
cdk destroy --all

# Note: S3 bucket auto-deletes objects due to RemovalPolicy.DESTROY
```

## Stack Outputs

After deployment, key outputs include:

| Output | Use |
|--------|-----|
| `VpcId` | Reference for other resources |
| `AuroraEndpoint` | Connection string for data loading + AtScale |
| `AuroraSecretArn` | Retrieve credentials from Secrets Manager |
| `RedshiftWorkgroupName` | Connection for data loading + AtScale |
| `RedshiftSecretArn` | Retrieve credentials from Secrets Manager |
| `ClusterName` | kubectl configuration |
| `RedshiftCopyRoleArn` | Attach to Redshift for S3 COPY |
| `BucketName` | Upload CSVs for Redshift loading |

## Run Tests

```bash
pytest tests/ -v
```

## Cost Estimate

~$1,000-$1,200/month when running. Use `cdk destroy` when not in use.

## Troubleshooting

**CDK bootstrap fails:**
```bash
# Ensure your AWS credentials are for account 652341767951
aws sts get-caller-identity
```

**EKS cluster creation times out:**
- EKS takes 10-15 minutes to create. Be patient.
- Check CloudFormation console for detailed status.

**Redshift namespace conflict:**
- We use `c360-atscale-ns` to avoid conflict with existing `customer360-ns`.
- If still conflicts, update `redshift_namespace` in `cdk.json`.
