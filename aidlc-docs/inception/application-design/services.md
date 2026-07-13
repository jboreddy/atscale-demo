# Application Design - Services

## Service Architecture

This POC uses a **monolithic deployment** pattern for the application layer (Agent + Streamlit in one process) with **managed services** for data and orchestration.

---

## Service 1: Infrastructure Provisioning Service

**Type:** CLI tool (CDK deploy)  
**Orchestration:** Sequential stack deployment with cross-stack references

```
CDK App
  ├── NetworkingStack (first - no dependencies)
  ├── StorageStack (depends on: Networking for VPC)
  ├── DatabaseStack (depends on: Networking for subnets/SGs)
  ├── EksStack (depends on: Networking for VPC/subnets)
  └── IamStack (depends on: Database ARNs, EKS ARN, S3 ARN)
```

**Deployment Order:** Networking → Storage → Database → EKS → IAM  
**Rollback:** `cdk destroy` removes all resources

---

## Service 2: Data Pipeline Service

**Type:** One-shot script (run once for POC)  
**Orchestration:** Sequential execution

```
data_loader.py
  1. download_csvs()           → Local CSV files
  2. upload_to_s3()            → CSVs in S3 bucket
  3. create_aurora_schema()    → DDL in Aurora
  4. create_redshift_schema()  → DDL in Redshift
  5. load_aurora_data()        → Customer data loaded
  6. load_redshift_data()      → Product/purchase data loaded
  7. validate_data()           → Integrity confirmed
```

**Dependencies:** Infrastructure must be deployed first  
**Idempotency:** DROP IF EXISTS + CREATE (safe to re-run)

---

## Service 3: Semantic Layer Service

**Type:** Long-running Kubernetes deployment (AtScale on EKS)  
**Orchestration:** Helm chart deployment

```
AtScale on EKS (namespace: atscale)
  ├── atscale-engine (StatefulSet, 1 replica for POC)
  ├── atscale-design-center (Deployment, 1 replica)
  ├── atscale-metadata-db (PostgreSQL, embedded or external)
  └── Ingress (ALB for Design Center access)
```

**Lifecycle:**
1. Deploy Helm chart
2. Wait for pods healthy
3. Configure data connections via REST API or UI
4. Create/import semantic model (SML or UI)
5. Publish model
6. Verify query endpoint responds

**Health Check:** `GET /api/health` → 200 OK

---

## Service 4: Agent + Chat Service

**Type:** Long-running web application (Streamlit)  
**Orchestration:** Single process (monolith for POC)

```
Streamlit Process
  ├── Streamlit UI Server (port 8501)
  ├── Strands Agent (in-process)
  │   ├── Claude Sonnet 4.6 (via Bedrock API)
  │   └── AtScale Tool (via REST/JDBC to AtScale)
  └── Session State (in-memory)
```

**Request Flow:**
```
User (Browser)
    │ HTTP (port 8501)
    ▼
Streamlit UI
    │ Function call (in-process)
    ▼
Strands Agent
    │ HTTPS (Bedrock API)
    ▼
Claude Sonnet 4.6 (Amazon Bedrock)
    │ Tool invocation
    ▼
AtScale Tool
    │ REST API / JDBC
    ▼
AtScale Semantic Layer (EKS)
    │ SQL pushdown
    ├──▶ Aurora (PostgreSQL wire protocol)
    └──▶ Redshift (PostgreSQL wire protocol)
```

**Deployment:** EC2 instance or EKS pod (single replica for POC)

---

## Service Interactions Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Browser                              │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTP :8501
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Streamlit + Strands Agent                           │
│              (EC2 or EKS pod)                                    │
└───────────┬──────────────────────────────────┬──────────────────┘
            │ HTTPS                            │ REST/JDBC
            ▼                                  ▼
┌─────────────────────┐          ┌─────────────────────────────────┐
│  Amazon Bedrock     │          │  AtScale (EKS)                   │
│  (Claude Sonnet)    │          │  - Query Engine                  │
│                     │          │  - Semantic Model                │
└─────────────────────┘          └────────┬──────────────┬─────────┘
                                          │              │
                                    JDBC  │              │ JDBC
                                          ▼              ▼
                                 ┌──────────┐    ┌──────────────┐
                                 │  Aurora   │    │  Redshift    │
                                 │  (RDS)    │    │  (Serverless)│
                                 └──────────┘    └──────────────┘
```

---

## Communication Patterns

| From | To | Protocol | Auth | Purpose |
|------|----|----------|------|---------|
| Browser | Streamlit | HTTP :8501 | None (POC) | Chat UI |
| Streamlit | Bedrock | HTTPS (AWS SDK) | IAM (instance role) | LLM invocation |
| Agent Tool | AtScale | REST API (HTTPS) | Basic Auth / Token | Query submission |
| AtScale | Aurora | PostgreSQL (JDBC :5432) | Username/Password | Customer data |
| AtScale | Redshift | PostgreSQL (JDBC :5439) | Username/Password | Product/purchase data |
| CDK | AWS APIs | HTTPS | IAM (CLI credentials) | Infrastructure provisioning |
| Data Loader | Aurora | PostgreSQL :5432 | Username/Password | Data loading |
| Data Loader | S3 | HTTPS (AWS SDK) | IAM | CSV staging |
| Redshift | S3 | HTTPS (internal) | IAM Role | COPY command |
