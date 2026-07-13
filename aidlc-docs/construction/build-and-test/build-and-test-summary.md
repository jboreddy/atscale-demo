# Build and Test Summary

## Overview

This document summarizes the deployment sequence and testing approach for the Customer 360 Semantic Layer POC.

## Deployment Sequence (6 Steps, ~60-80 min)

| Step | Action | Duration | Dependency |
|------|--------|----------|------------|
| 1 | `cdk deploy --all` (Infrastructure) | 20-30 min | None |
| 2 | `python load_all.py` (Data) | 5-10 min | Step 1 |
| 3 | `./deploy_atscale.sh` (AtScale on EKS) | 10-15 min | Step 1 |
| 4 | `python configure_connections.py` (AtScale config) | 5-10 min | Steps 2, 3 |
| 5 | `streamlit run app.py` (Application) | 2-5 min | Step 4 |
| 6 | Run Q1-Q13 tests | 5-10 min | Step 5 |

## Key Environment Variables

```bash
# Captured from CDK outputs (Step 1)
AURORA_HOST=<aurora-endpoint>
AURORA_PASSWORD=<from-secrets-manager>
REDSHIFT_HOST=<redshift-endpoint>
REDSHIFT_PASSWORD=<from-secrets-manager>
S3_BUCKET=c360-poc-data-652341767951-us-east-1
REDSHIFT_COPY_ROLE_ARN=<from-cdk-output>

# AtScale (Step 3)
ATSCALE_URL=<from-alb-ingress>
ATSCALE_USERNAME=admin
ATSCALE_PASSWORD=admin

# Application (Step 5)
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-6-v1:0
```

## Test Strategy

### Unit Tests (CDK)
```bash
cd infrastructure/
pytest tests/ -v
```

### Integration Tests (Q1-Q13)
- Run all 13 sample queries through the chat UI
- Compare results with direct SQL verification
- Pass criteria: All 13 return correct, non-empty results

### Smoke Test (Quick)
```bash
# Fastest validation — one query from each category
python agent/agent.py "List 5 customers and their state"        # Aurora only
python agent/agent.py "Top 5 products by units sold"            # Redshift only
python agent/agent.py "Top 5 spenders with their state"         # Federated
python agent/agent.py "How many big spenders per state?"        # Derived metric
```

## Cleanup (Teardown)

```bash
# Remove application
kubectl -n c360-app delete deployment,svc,ingress --all

# Remove AtScale
helm uninstall atscale -n atscale
kubectl delete namespace atscale

# Destroy all CDK stacks (~10 min)
cd infrastructure/
cdk destroy --all --force
```

## Documents

| Document | Purpose |
|----------|---------|
| [build-instructions.md](build-instructions.md) | Full step-by-step deployment guide |
| [integration-test-instructions.md](integration-test-instructions.md) | Test matrix with all 13 queries |

## Success Criteria

- [ ] Infrastructure deploys without errors
- [ ] Data loaded into both databases (verified by validate_data.py)
- [ ] AtScale running and Design Center accessible
- [ ] AtScale connections test successfully
- [ ] Semantic model published
- [ ] All 13 sample queries return correct results via chat UI
- [ ] End-to-end latency < 10 seconds per query
