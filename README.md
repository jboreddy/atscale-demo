# AtScale Semantic Layer for Agentic AI on AWS — Customer 360 POC

Build a semantic layer for agentic AI using **AtScale** (on Amazon EKS) and **AWS AI services** (Amazon Bedrock AgentCore, Strands Agents). This POC demonstrates natural language querying of Customer 360 data spanning **Aurora PostgreSQL** and **Amazon Redshift** through a unified semantic layer.

## Architecture

```
Streamlit Chat App (NL Interface)
        ↓
Strands Agent + Claude Sonnet (Amazon Bedrock)
        ↓
AtScale Semantic Layer (on Amazon EKS)
        ↓
┌───────────────────┬──────────────────────┐
│ Aurora PostgreSQL  │  Amazon Redshift     │
│ (Customer data)   │  (Product/Purchase)  │
└───────────────────┴──────────────────────┘
```

## Reference

Adapted from: [Build a semantic layer for agentic AI on AWS with Stardog and Amazon Bedrock AgentCore](https://aws.amazon.com/blogs/machine-learning/build-a-semantic-layer-for-agentic-ai-on-aws-with-stardog-and-amazon-bedrock-agentcore/)

## Key Components

| Component | Technology |
|-----------|-----------|
| Semantic Layer | AtScale (self-managed on EKS) |
| Agent Framework | Strands Agents |
| Foundation Model | Claude Sonnet 4.6 (Amazon Bedrock) |
| Chat UI | Streamlit |
| Operational DB | Aurora PostgreSQL |
| Analytics DB | Amazon Redshift Serverless |
| Container Orchestration | Amazon EKS |
| Infrastructure | AWS CDK / Terraform |

## Repository Structure

```
.
├── docs/                        # PRD, architecture docs, research
├── research-output/             # Research findings and analysis
├── infrastructure/              # IaC (CDK/Terraform) — TBD
├── data/                        # C360 CSV files + loading scripts — TBD
├── atscale/                     # Helm values and SML models — TBD
├── agent/                       # Strands Agent code — TBD
├── app/                         # Streamlit chat application — TBD
└── scripts/                     # Utility scripts — TBD
```

## Data Source

Customer 360 sample data from [Stardog C360 Knowledge Kit](https://github.com/stardog-union/knowledge-kits/tree/main/examples/c360/data):

| Database | Tables |
|----------|--------|
| **Aurora PostgreSQL** | customer, address, credit_card, rewards_account |
| **Amazon Redshift** | purchase, product, category, vendor |

## AWS Environment

| Parameter | Value |
|-----------|-------|
| Account | 652341767951 |
| Region | us-east-1 |
| VPC CIDR | 10.1.0.0/16 |

## Getting Started

> **Status:** POC in planning phase. See `research-output/PRD-AtScale-Customer360-SemanticLayer.md` for full requirements.

### Prerequisites

- AWS CLI v2 configured for account 652341767951
- kubectl, Helm 3.x
- Python 3.11+
- Docker
- AtScale trial license

## Documentation

- [PRD](research-output/PRD-AtScale-Customer360-SemanticLayer.md) — Full product requirements document
- [Implementation Guide](research-output/atscale-semantic-layer-implementation-guide.md) — Detailed technical guide
- [Executive Summary](research-output/executive-summary.md) — High-level findings
- [Quick Reference](research-output/atscale-quick-reference.md) — Commands, checklists, troubleshooting

## License

Internal use only.
