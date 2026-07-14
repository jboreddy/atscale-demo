#!/bin/bash
# Deploy AtScale on EKS using Helm (OCI chart from Docker Hub)
# Reference: https://documentation.atscale.com/container/installation-guides/kubernetes/installing-atscale
# K8s Blueprints: https://github.com/AtScaleInc/atscale-k8s-blueprints

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HELM_DIR="${SCRIPT_DIR}/../helm"
NAMESPACE="atscale"
RELEASE_NAME="atscale"
CLUSTER_NAME="${EKS_CLUSTER_NAME:-c360-poc-cluster}"
REGION="${AWS_REGION:-us-east-1}"
ATSCALE_VERSION="${ATSCALE_VERSION:-2024.9.0}"

echo "═══════════════════════════════════════════════════"
echo "AtScale Deployment on EKS"
echo "  Cluster:   ${CLUSTER_NAME}"
echo "  Namespace: ${NAMESPACE}"
echo "  Version:   ${ATSCALE_VERSION}"
echo "  Chart:     oci://docker.io/atscaleinc/atscale"
echo "═══════════════════════════════════════════════════"

# Step 1: Configure kubectl
echo -e "\n📋 Step 1: Configure kubectl for EKS cluster..."
aws eks update-kubeconfig --name "${CLUSTER_NAME}" --region "${REGION}"
kubectl get nodes

# Step 2: Create namespace (if not exists)
echo -e "\n📋 Step 2: Ensure namespace '${NAMESPACE}' exists..."
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# Step 3: Generate self-signed TLS certificate (POC only)
echo -e "\n📋 Step 3: Generate self-signed TLS certificate..."
TLS_DIR="/tmp/atscale-tls"
mkdir -p "${TLS_DIR}"

if [ ! -f "${TLS_DIR}/tls.crt" ]; then
    openssl req -x509 -nodes -days 365 \
        -newkey rsa:2048 \
        -keyout "${TLS_DIR}/tls.key" \
        -out "${TLS_DIR}/tls.crt" \
        -subj "/CN=atscale.local/O=C360-POC" \
        2>/dev/null
    
    # Create Kubernetes TLS secret
    kubectl create secret tls atscale-tls \
        --cert="${TLS_DIR}/tls.crt" \
        --key="${TLS_DIR}/tls.key" \
        -n "${NAMESPACE}" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    echo "  ✓ Self-signed TLS certificate created"
else
    echo "  ℹ TLS certificate already exists"
fi

# Step 4: Install/Upgrade AtScale via OCI Helm chart
echo -e "\n📋 Step 4: Deploy AtScale via Helm (OCI chart)..."
echo "  Installing from: oci://docker.io/atscaleinc/atscale"
echo "  Version: ${ATSCALE_VERSION}"

helm upgrade --install "${RELEASE_NAME}" \
    oci://docker.io/atscaleinc/atscale \
    --version "${ATSCALE_VERSION}" \
    --namespace "${NAMESPACE}" \
    --values "${HELM_DIR}/values.yaml" \
    --timeout 15m \
    --wait

# Step 5: Wait for pods to be ready
echo -e "\n📋 Step 5: Waiting for AtScale pods to be ready..."
kubectl -n "${NAMESPACE}" wait --for=condition=ready pod --all --timeout=300s || true

# Step 6: Display status
echo -e "\n📋 Step 6: AtScale deployment status:"
kubectl -n "${NAMESPACE}" get pods
kubectl -n "${NAMESPACE}" get svc
kubectl -n "${NAMESPACE}" get ingress 2>/dev/null || echo "  (no ingress yet)"

# Step 7: Get access info
echo -e "\n═══════════════════════════════════════════════════"
PROXY_SVC=$(kubectl -n "${NAMESPACE}" get svc atscale-proxy -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
echo "✅ AtScale deployed successfully!"
echo ""
echo "  AtScale Proxy: https://${PROXY_SVC}"
echo ""
echo "  To get the service URL:"
echo "    kubectl get svc -n ${NAMESPACE} atscale-proxy"
echo ""
echo "  Next steps:"
echo "  1. Configure DNS or use port-forward:"
echo "     kubectl port-forward svc/atscale-proxy 10500:443 -n ${NAMESPACE}"
echo "  2. Access Design Center at https://localhost:10500"
echo "  3. Run: python scripts/configure_connections.py"
echo "═══════════════════════════════════════════════════"
