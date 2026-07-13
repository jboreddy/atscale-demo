# Code Generation Plan — Unit 1: Infrastructure

## Unit Context
- **Unit**: Infrastructure (AWS CDK Python)
- **Purpose**: Provision all AWS resources for the C360 Semantic Layer POC
- **Output**: 5 CDK stacks deployable via `cdk deploy --all`
- **Target Account**: 652341767951 (us-east-1)
- **Dependencies**: None (first unit in build chain)

## Code Location
- **Root**: `/Users/jboreddy/jp-explore/Amazon/2026/Thought Leadership/Semantic Layer/AtScale/infrastructure/`
- **NOT in**: aidlc-docs/

---

## Code Generation Steps

### Step 1: Project Structure Setup
- [x] Create `infrastructure/` directory
- [x] Initialize CDK Python project (`cdk.json`, `app.py`, `requirements.txt`)
- [x] Create `stacks/` package with `__init__.py`
- [x] Create `.gitignore` for CDK (cdk.out/, .venv/, etc.)
- [x] Define CDK context variables (account, region, VPC CIDR, naming)

### Step 2: Networking Stack
- [x] Create `stacks/networking_stack.py`
- [x] VPC: 10.1.0.0/16 with 2 AZs
- [x] Public subnets: 10.1.1.0/24, 10.1.2.0/24 (with NAT Gateway, IGW)
- [x] Private subnets: 10.1.10.0/24, 10.1.11.0/24
- [x] NAT Gateway: 1x in us-east-1a
- [x] Security Groups: sg-eks-nodes, sg-aurora, sg-redshift, sg-alb, sg-streamlit
- [x] Export: VPC, subnets, security groups as stack outputs

### Step 3: Storage Stack
- [x] Create `stacks/storage_stack.py`
- [x] S3 bucket: `c360-poc-data-652341767951-us-east-1`
- [x] Encryption: SSE-S3
- [x] Lifecycle rule: Delete `staging/*` after 7 days
- [x] Block public access: enabled
- [x] Export: bucket name, bucket ARN

### Step 4: Database Stack
- [x] Create `stacks/database_stack.py`
- [x] Aurora PostgreSQL 16.13 cluster
- [x] Redshift Serverless (c360-atscale-ns / c360-atscale-wg)
- [x] Export: endpoints, secret ARNs

### Step 5: EKS Stack
- [x] Create `stacks/eks_stack.py`
- [x] EKS Cluster: c360-poc-cluster, version 1.36
- [x] Managed Node Group (m5.2xlarge, 2-4 nodes)
- [x] Add-ons: EBS CSI Driver, ALB Controller
- [x] OIDC provider for IRSA
- [x] Export: cluster name, endpoint, OIDC ARN

### Step 6: IAM Stack
- [x] Create `stacks/iam_stack.py`
- [x] RedshiftCopyRole
- [x] AtScaleServiceRole (IRSA)
- [x] BedrockAccessRole (IRSA)
- [x] SecretsAccessPolicy
- [x] Export: role ARNs

### Step 7: CDK App Entry Point
- [x] Create `app.py` wiring all stacks with correct dependency order

### Step 8: Configuration
- [x] Create `cdk.json` with context values
- [x] Create `requirements.txt` with CDK dependencies
- [x] Create `README.md` with deployment instructions

### Step 9: Unit Tests
- [x] Create `tests/test_stacks.py`
- [x] Test: Networking stack creates VPC
- [x] Test: Database stack creates Aurora cluster
- [x] Test: Database stack creates Redshift namespace
- [x] Test: Storage stack creates encrypted S3 bucket

### Step 10: Documentation
- [x] Create `infrastructure/README.md`

---

## Summary

| Metric | Value |
|--------|-------|
| Total Steps | 10 |
| Files to Create | ~12-15 Python files |
| CDK Stacks | 5 (Networking, Storage, Database, EKS, IAM) |
| Tests | 5+ assertion tests |
| Estimated Lines of Code | ~800-1200 |
