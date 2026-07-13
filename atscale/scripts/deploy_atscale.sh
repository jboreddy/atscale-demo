#!/bin/bash
# Deploy AtScale on EKS using Helm
# Reference: https://github.com/AtScaleInc/atscale-k8s-blueprints

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HELM_DIR="${SCRIPT_DIR}/../helm"
NAMESPACE="atscale"
RELEASE_NAME="atscale"
CLUSTER_NAME="${EKS_CLUSTER_NAME:-c360-poc-cluster}"
REGION="${AWS_REGION:-us-east-1}"

echo "═══════════════════════════════════════════════════"
echo "AtScale Deployment on EKS"
echo "═══════════════════════════════════════════════════"

# Step 1: Configure kubectl
echo -e "\n📋 Step 1: Configure kubectl for EKS cluster..."
aws eks update-kubeconfig --name "${CLUSTER_NAME}" --region "${REGION}"
kubectl get nodes

# Step 2: Create namespace (if not exists)
echo -e "\n📋 Step 2: Ensure namespace '${NAMESPACE}' exists..."
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# Step 3: Add AtScale Helm repository
echo -e "\n📋 Step 3: Add AtScale Helm repository..."
# NOTE: Update this URL based on AtScale's actual Helm chart repository
# The atscale-k8s-blueprints repo may provide charts locally
helm repo add atscale https://charts.atscale.com 2>/dev/null || true
helm repo update

# Step 4: Install/Upgrade AtScale
echo -e "\n📋 Step 4: Deploy AtScale via Helm..."
ATSCALE_LICENSE_KEY="${ATSCALE_LICENSE_KEY:-}"

if [ -z "${ATSCALE_LICENSE_KEY}" ]; then
    echo "⚠️  WARNING: ATSCALE_LICENSE_KEY not set. AtScale will start in trial mode."
    echo "  Set it via: export ATSCALE_LICENSE_KEY='your-license-key'"
fi

helm upgrade --install "${RELEASE_NAME}" atscale/atscale \
    --namespace "${NAMESPACE}" \
    --values "${HELM_DIR}/values.yaml" \
    --set license.key="${ATSCALE_LICENSE_KEY}" \
    --timeout 10m \
    --wait

# Step 5: Wait for pods to be ready
echo -e "\n📋 Step 5: Waiting for AtScale pods to be ready..."
kubectl -n "${NAMESPACE}" wait --for=condition=ready pod --all --timeout=300s

# Step 6: Display status
echo -e "\n📋 Step 6: AtScale deployment status:"
kubectl -n "${NAMESPACE}" get pods
kubectl -n "${NAMESPACE}" get svc
kubectl -n "${NAMESPACE}" get ingress

# Step 7: Get access URL
echo -e "\n═══════════════════════════════════════════════════"
INGRESS_URL=$(kubectl -n "${NAMESPACE}" get ingress -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
echo "✅ AtScale deployed successfully!"
echo ""
echo "  Design Center URL: http://${INGRESS_URL}"
echo "  Query Endpoint:    http://${INGRESS_URL}:10502"
echo ""
echo "  Next steps:"
echo "  1. Access Design Center and configure data connections"
echo "  2. Import the Customer_360 semantic model"
echo "  3. Run: python scripts/configure_connections.py"
echo "═══════════════════════════════════════════════════"
