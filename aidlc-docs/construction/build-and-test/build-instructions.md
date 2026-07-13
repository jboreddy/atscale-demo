# Build Instructions

## Prerequisites

Before deploying, ensure you have:

- [ ] AWS CLI v2 configured (account 652341767951, us-east-1)
- [ ] CDK CLI installed: `npm install -g aws-cdk`
- [ ] Python 3.11+ installed
- [ ] Docker running
- [ ] kubectl installed
- [ ] Helm 3.x installed
- [ ] Amazon Bedrock model access enabled (Claude Sonnet in us-east-1)
- [ ] AtScale trial license key obtained (from AtScale sales)

## Deployment Sequence

```
Step 1: CDK Infrastructure (20-30 min)
    ↓
Step 2: Data Loading (5-10 min)
    ↓
Step 3: AtScale Deployment (10-15 min)
    ↓
Step 4: AtScale Configuration (5-10 min)
    ↓
Step 5: Application Deployment (5 min)
    ↓
Step 6: Verification (5 min)
```

**Total estimated time: 50-80 minutes**

---

## Step 1: Deploy Infrastructure (CDK)

```bash
cd infrastructure/

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap aws://652341767951/us-east-1

# Synthesize (dry-run, validates templates)
cdk synth

# Deploy all stacks
cdk deploy --all --require-approval never

# Wait for completion (~20-30 min, EKS takes longest)
```

### Capture Outputs

After deployment completes, capture the stack outputs:

```bash
# Get Aurora endpoint
export AURORA_HOST=$(aws cloudformation describe-stacks \
  --stack-name c360-poc-database \
  --query 'Stacks[0].Outputs[?OutputKey==`AuroraEndpoint`].OutputValue' \
  --output text)

# Get Aurora secret
export AURORA_SECRET_ARN=$(aws cloudformation describe-stacks \
  --stack-name c360-poc-database \
  --query 'Stacks[0].Outputs[?OutputKey==`AuroraSecretArn`].OutputValue' \
  --output text)

# Get Redshift workgroup endpoint
export REDSHIFT_HOST=$(aws redshift-serverless get-workgroup \
  --workgroup-name c360-atscale-wg \
  --query 'workgroup.endpoint.address' \
  --output text)

# Get Redshift secret
export REDSHIFT_SECRET_ARN=$(aws cloudformation describe-stacks \
  --stack-name c360-poc-database \
  --query 'Stacks[0].Outputs[?OutputKey==`RedshiftSecretArn`].OutputValue' \
  --output text)

# Get S3 bucket
export S3_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name c360-poc-storage \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
  --output text)

# Get Redshift COPY role
export REDSHIFT_COPY_ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name c360-poc-iam \
  --query 'Stacks[0].Outputs[?OutputKey==`RedshiftCopyRoleArn`].OutputValue' \
  --output text)

# Get passwords from Secrets Manager
export AURORA_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id c360/aurora/master \
  --query 'SecretString' --output text | python3 -c "import sys,json;print(json.load(sys.stdin)['password'])")

export REDSHIFT_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id c360/redshift/admin \
  --query 'SecretString' --output text | python3 -c "import sys,json;print(json.load(sys.stdin)['password'])")

# Configure kubectl
aws eks update-kubeconfig --name c360-poc-cluster --region us-east-1

# Verify
echo "Aurora: $AURORA_HOST"
echo "Redshift: $REDSHIFT_HOST"
echo "S3: $S3_BUCKET"
kubectl get nodes
```

---

## Step 2: Load Data

```bash
cd data/

# Install dependencies
pip install -r requirements.txt

# Set environment variables (from Step 1 outputs)
export AURORA_HOST="<from-step-1>"
export AURORA_PORT=5432
export AURORA_DATABASE=customer360_db
export AURORA_USERNAME=postgres
export AURORA_PASSWORD="<from-step-1>"

export REDSHIFT_HOST="<from-step-1>"
export REDSHIFT_PORT=5439
export REDSHIFT_DATABASE=analytics_db
export REDSHIFT_USERNAME=admin
export REDSHIFT_PASSWORD="<from-step-1>"

export S3_BUCKET="<from-step-1>"
export REDSHIFT_COPY_ROLE_ARN="<from-step-1>"

# Run full data pipeline
cd scripts/
python load_all.py
```

### Expected Output:
```
C360 DATA LOADING PIPELINE
============================================================

📥 STEP 1: Download CSV files from GitHub
  Downloading customer.csv... ✓ (XXX rows)
  Downloading address.csv... ✓ (XXX rows)
  ...

📤 STEP 2: Load data into Aurora PostgreSQL
  ✓ customer: XXX rows loaded
  ✓ address: XXX rows loaded
  ...

📤 STEP 3: Load data into Redshift Serverless
  ✓ category: XXX rows loaded
  ✓ product: XXX rows loaded
  ...

🔍 STEP 4: Validate data integrity
  ✓ All tables populated
  ✓ FK integrity verified

✅ DATA PIPELINE COMPLETE
```

---

## Step 3: Deploy AtScale on EKS

```bash
cd atscale/

# Set license key
export ATSCALE_LICENSE_KEY="<your-trial-license>"
export EKS_CLUSTER_NAME="c360-poc-cluster"

# Run deployment script
chmod +x scripts/deploy_atscale.sh
./scripts/deploy_atscale.sh
```

### Verify AtScale Pods

```bash
kubectl -n atscale get pods
# Expected: atscale-engine-0 (Running), atscale-design-center-xxx (Running)

kubectl -n atscale get svc
# Expected: services exposed

kubectl -n atscale get ingress
# Expected: ALB URL for Design Center
```

### Get AtScale URL

```bash
export ATSCALE_URL="http://$(kubectl -n atscale get ingress -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}')"
echo "AtScale Design Center: $ATSCALE_URL"
```

---

## Step 4: Configure AtScale

```bash
cd atscale/

# Set connection credentials
export ATSCALE_URL="<from-step-3>"
export ATSCALE_USERNAME="admin"
export ATSCALE_PASSWORD="admin"  # Default, change in production

export AURORA_HOST="<from-step-1>"
export AURORA_PASSWORD="<from-step-1>"
export REDSHIFT_HOST="<from-step-1>"
export REDSHIFT_PASSWORD="<from-step-1>"

# Run connection configuration
pip install requests
python scripts/configure_connections.py
```

### Import Semantic Model

**Option A: Via Design Center UI**
1. Open AtScale Design Center at `$ATSCALE_URL`
2. Log in (admin/admin)
3. Create new project → Import from SML
4. Upload files from `atscale/models/`
5. Publish model

**Option B: Via REST API (if SML import is supported)**
```bash
python scripts/deploy_model.py  # If available
```

### Verify Model

```bash
# Test query via AtScale REST API
curl -X POST "$ATSCALE_URL/api/1.0/query" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT state, COUNT(*) as cnt FROM customer_360 GROUP BY state LIMIT 5",
    "catalog": "customer_360"
  }'
```

---

## Step 5: Deploy Application

### Option A: Run Locally (Quickest for testing)

```bash
cd app/

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ATSCALE_URL="<from-step-3>"
export ATSCALE_USERNAME="admin"
export ATSCALE_PASSWORD="admin"
export AWS_REGION="us-east-1"
export BEDROCK_MODEL_ID="anthropic.claude-sonnet-4-6-v1:0"

# Run Streamlit
streamlit run app.py
```

Access at: http://localhost:8501

### Option B: Deploy to EKS

```bash
# Build Docker image
docker build -t c360-app:latest -f app/Dockerfile .

# Tag and push to ECR (create repo first)
aws ecr create-repository --repository-name c360-app 2>/dev/null
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 652341767951.dkr.ecr.us-east-1.amazonaws.com
docker tag c360-app:latest 652341767951.dkr.ecr.us-east-1.amazonaws.com/c360-app:latest
docker push 652341767951.dkr.ecr.us-east-1.amazonaws.com/c360-app:latest

# Deploy to EKS
kubectl -n c360-app apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: c360-chat
  namespace: c360-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: c360-chat
  template:
    metadata:
      labels:
        app: c360-chat
    spec:
      serviceAccountName: bedrock-agent
      containers:
      - name: chat
        image: 652341767951.dkr.ecr.us-east-1.amazonaws.com/c360-app:latest
        ports:
        - containerPort: 8501
        env:
        - name: ATSCALE_URL
          value: "http://atscale-engine.atscale.svc.cluster.local:10500"
        - name: AWS_REGION
          value: "us-east-1"
---
apiVersion: v1
kind: Service
metadata:
  name: c360-chat
  namespace: c360-app
spec:
  type: ClusterIP
  ports:
  - port: 8501
    targetPort: 8501
  selector:
    app: c360-chat
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: c360-chat
  namespace: c360-app
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: c360-chat
            port:
              number: 8501
EOF
```

### Get Application URL

```bash
export APP_URL="http://$(kubectl -n c360-app get ingress c360-chat -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')"
echo "Chat Application: $APP_URL"
```

---

## Step 6: Verification

Once deployed, verify end-to-end flow by testing sample queries in the chat UI.

See `integration-test-instructions.md` for the full test matrix.
