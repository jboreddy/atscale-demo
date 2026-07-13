# Application Design Summary

## Overview

The Customer 360 Semantic Layer POC is composed of **5 components** deployed sequentially on AWS account 652341767951 (us-east-1).

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          AWS Account 652341767951                     │
│                              us-east-1                                │
│                                                                       │
│  ┌────────────────── VPC (10.1.0.0/16) ─────────────────────────┐   │
│  │                                                                │   │
│  │  ┌─── Public Subnets ───┐    ┌─── Private Subnets ─────────┐ │   │
│  │  │                      │    │                              │ │   │
│  │  │  ALB (Streamlit)     │    │  EKS Cluster                │ │   │
│  │  │  NAT Gateway         │    │  ├── AtScale Engine Pod     │ │   │
│  │  │                      │    │  ├── AtScale Design Center  │ │   │
│  │  └──────────────────────┘    │  └── Streamlit Pod (or EC2) │ │   │
│  │                               │                              │ │   │
│  │                               │  Aurora PostgreSQL           │ │   │
│  │                               │  (customer360_db)            │ │   │
│  │                               │                              │ │   │
│  │                               │  Redshift Serverless         │ │   │
│  │                               │  (analytics_db)              │ │   │
│  │                               └──────────────────────────────┘ │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────────┐   ┌────────────────────────────────┐  │
│  │  Amazon Bedrock          │   │  S3 Bucket                     │  │
│  │  (Claude Sonnet 4.6)     │   │  (CSV staging + aggregates)    │  │
│  └──────────────────────────┘   └────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────┘
```

## Components

| # | Component | Technology | Purpose |
|---|-----------|-----------|---------|
| 1 | Infrastructure | AWS CDK (Python) | Provision all AWS resources |
| 2 | Data Layer | Python scripts | Download, load, validate C360 data |
| 3 | Semantic Layer | AtScale on EKS | Federated query layer with business context |
| 4 | AI Agent | Strands Agents + Bedrock | NL→SQL reasoning and tool invocation |
| 5 | Chat App | Streamlit | Web-based chat interface |

## Build Sequence

```
Unit 1: Infrastructure → Unit 2: Data → Unit 3: Semantic Layer → Unit 4: Application
```

Each unit depends on the previous unit being complete.

## Key Interfaces

| Interface | Protocol | From → To |
|-----------|----------|-----------|
| Chat UI | HTTP :8501 | Browser → Streamlit |
| LLM Invocation | HTTPS (Bedrock SDK) | Agent → Claude Sonnet |
| Semantic Query | REST API / JDBC | Agent Tool → AtScale |
| Customer Data | PostgreSQL :5432 | AtScale → Aurora |
| Analytics Data | PostgreSQL :5439 | AtScale → Redshift |
| Data Staging | S3 API | Data Loader → S3 → Redshift |

## Design Artifacts

- [Components](components.md) — Component definitions and responsibilities
- [Component Methods](component-methods.md) — Method signatures and interfaces
- [Services](services.md) — Service orchestration and communication patterns
- [Component Dependencies](component-dependency.md) — Dependency graph and data flows
