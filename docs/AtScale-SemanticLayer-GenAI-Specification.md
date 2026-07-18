# Specification Document
# Building a Semantic Layer for Agentic AI on AWS with AtScale

**Version:** 1.0  
**Date:** July 2026  
**Purpose:** Prescriptive guidance for deploying AtScale as the semantic layer for GenAI-powered analytics on AWS  
**Audience:** Data engineers, solutions architects, AI/ML engineers, and enterprise architects

---

## 1. Executive Overview

### 1.1 Objective

This document provides a complete specification for building a **semantic layer for agentic AI** using AtScale deployed on AWS. The solution enables business users to query enterprise data through natural language, with an AI agent translating questions into governed, accurate analytical responses—without requiring users to understand SQL, schemas, or where data resides.

### 1.2 Business Problem

Enterprise data is fragmented across operational databases and analytics warehouses. Each system defines business concepts differently. AI agents (LLMs) can generate technically valid SQL, but without business context they produce:

- **Conflicting results** — two agents return different numbers for the same question
- **Wrong joins** — agents don't know which tables relate or how
- **No governance** — raw database access bypasses security policies
- **Unexplainable answers** — no provenance or audit trail

A **semantic layer** solves this by providing a single, governed, business-context-aware interface between AI agents and underlying data sources.

### 1.3 Solution Summary

AtScale provides the **universal semantic layer** that sits between AI agents and enterprise data, delivering:

- **Unified business definitions** — metrics, dimensions, hierarchies, and business rules defined once
- **Data federation** — query across multiple cloud data sources without ETL
- **Governance** — row/column-level security, role-based access, full audit trail
- **Performance** — intelligent query acceleration through aggregate management
- **AI-native integration** — Model Context Protocol (MCP) for agent connectivity

---

## 2. End-to-End Architecture

### 2.1 System Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Natural Language Chat Interface                      │
│                (Streamlit / Custom Web Application)                   │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ User question (natural language)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 AI Agent (Strands Agents Framework)                   │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Foundation Model: Claude Sonnet (Amazon Bedrock)               │ │
│  │  - Understands user intent                                      │ │
│  │  - Plans query strategy                                         │ │
│  │  - Generates semantic SQL                                       │ │
│  │  - Formats human-readable answers                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ Tool invocation (MCP / REST)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Amazon Bedrock AgentCore (Production Path)               │
│                                                                       │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────────────────┐  │
│  │   Gateway    │  │     Runtime      │  │      Identity         │  │
│  │  (JWT Auth)  │  │ (Agent Hosting)  │  │ (Credential Mgmt)    │  │
│  └─────────────┘  └──────────────────┘  └───────────────────────┘  │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ MCP Protocol
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              AtScale Semantic Layer (on Amazon EKS)                   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  MCP Server          │  Query Engine      │  Design Center    │   │
│  │  - NL → SQL          │  - Federation      │  - Visual Model   │   │
│  │  - Schema metadata   │  - Optimization    │  - SML (Git)      │   │
│  │  - Result formatting │  - Aggregates      │  - AI-Assisted    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Governance Layer                                             │   │
│  │  - Role-Based Access Control (RBAC)                           │   │
│  │  - Row-Level Security (RLS)                                   │   │
│  │  - Column Masking                                             │   │
│  │  - Full Query Audit Trail                                     │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────┬────────────────────┘
                     │                            │
          SQL pushdown                  SQL pushdown
                     │                            │
                     ▼                            ▼
┌──────────────────────────────┐  ┌────────────────────────────────────┐
│    Amazon Aurora PostgreSQL   │  │       Amazon Redshift Serverless   │
│                               │  │                                    │
│    Operational Data:          │  │    Analytical Data:                │
│    - Customer profiles        │  │    - Purchase transactions         │
│    - Addresses                │  │    - Product catalog               │
│    - Credit cards             │  │    - Categories                    │
│    - Rewards accounts         │  │    - Vendors                       │
└──────────────────────────────┘  └────────────────────────────────────┘
```

### 2.2 Request Flow (Detailed)

| Step | Component | Action |
|------|-----------|--------|
| 1 | User | Types natural language question in chat interface |
| 2 | Chat App | Sends question to AI Agent |
| 3 | Agent | Sends question + semantic model context to Foundation Model (Bedrock) |
| 4 | Foundation Model | Reasons about data needed, generates semantic SQL |
| 5 | Agent | Invokes AtScale tool via MCP protocol |
| 6 | AgentCore Gateway | Validates JWT, injects AtScale credentials |
| 7 | AtScale MCP Server | Receives query, validates against semantic model |
| 8 | AtScale Query Engine | Plans federated execution across data sources |
| 9 | AtScale | Pushes optimized SQL to Aurora and/or Redshift |
| 10 | Data Sources | Execute SQL, return results |
| 11 | AtScale | Joins results on shared dimension keys, applies security |
| 12 | Agent | Receives results, sends to FM for summarization |
| 13 | Foundation Model | Formats human-readable answer |
| 14 | Chat App | Displays answer, SQL used, and data sources cited |

### 2.3 Integration Protocol: Model Context Protocol (MCP)

AtScale's MCP Server exposes the semantic layer as AI-accessible tools:

| MCP Tool | Purpose | Input | Output |
|----------|---------|-------|--------|
| `atscale_ask` | Natural language query | Question string | Results + SQL + provenance |
| `atscale_query` | Direct semantic SQL | SQL string | Result set |
| `atscale_schema` | Model discovery | Model name (optional) | Dimensions, measures, metadata |

**Benefits of MCP integration:**
- Standard protocol — works with any MCP-compatible agent framework
- Credential isolation — tokens managed by AgentCore Identity, not in agent code
- Tool discovery — agents can introspect available semantic models
- Governed access — every query passes through AtScale's security layer

---

## 3. Use Case: Customer 360 Analytics

### 3.1 Business Scenario

A retail enterprise needs unified customer analytics across operational and analytical systems. Customer profiles and addresses live in an operational database. Purchase history, products, and vendor data live in an analytics warehouse. Business users need to ask cross-cutting questions without knowing where data resides or how systems connect.

### 3.2 Data Architecture

**Operational Data (Aurora PostgreSQL):**

| Table | Key Columns | Description |
|-------|-------------|-------------|
| `customer` | cid (PK), first_name, last_name, email, ssn, phone, location | Customer profiles |
| `address` | id (PK), street_number, street_name, state, zip, city | Customer addresses |
| `credit_card` | id (PK), cid (FK), card_num, card_type | Payment methods |
| `rewards_account` | id (PK), cid (FK), account_id, create_date | Loyalty program |

**Analytical Data (Amazon Redshift):**

| Table | Key Columns | Description |
|-------|-------------|-------------|
| `purchase` | id, pid, purchase_date, quantity, price, cid, card | Purchase transactions |
| `product` | id (PK), name, brand, price, dept | Product catalog |
| `category` | id (PK), dept_name, parent | Product categories |
| `vendor` | id (PK), vendor_name, industry | Suppliers |

**Cross-Source Identity:** The shared key `cid` (customer ID) links Aurora customer records with Redshift purchase transactions. AtScale resolves this join at the semantic layer without requiring ETL or data movement.

### 3.3 Semantic Model: Customer_360

#### Dimensions

| Dimension | Source | Key | Attributes |
|-----------|--------|-----|------------|
| Dim_Customer | Aurora | cid | first_name, last_name, full_name, email, phone |
| Dim_Address | Aurora | id | city, state, zip_code, street |
| Dim_Product | Redshift | id | product_name, brand, price |
| Dim_Category | Redshift | id | dept_name, parent_category |
| Dim_Vendor | Redshift | id | vendor_name, industry |
| Dim_Date | Generated | date_key | year, quarter, month, day |

#### Fact Table

| Fact | Source | Grain | Dimension Links |
|------|--------|-------|-----------------|
| Fact_Purchase | Redshift | One row per transaction | cid→Dim_Customer, pid→Dim_Product |

#### Measures

| Measure | Formula | Description |
|---------|---------|-------------|
| Total Revenue | `SUM(price × quantity)` | Total sales dollars |
| Order Count | `COUNT(id)` | Number of transactions |
| Units Sold | `SUM(quantity)` | Total items sold |
| Avg Order Value | `Total Revenue / Order Count` | Revenue per transaction |
| Customer Lifetime Value | `SUM(price × quantity) per customer` | Total spend per customer |
| Distinct Customers | `COUNT(DISTINCT cid)` | Unique customer count |

#### Derived Business Attributes

| Attribute | Logic | Description |
|-----------|-------|-------------|
| Big_Spender | `CLV > $10,000 → 'Yes'` | High-value customer indicator |
| Large_Order | `order_total > $500 → 'Yes'` | High-value order indicator |
| Spend_Tier | `CLV > $50K → 'Platinum'; > $10K → 'Gold'; else 'Standard'` | Customer segmentation |

### 3.4 Sample Queries

| Category | Question | Data Sources | Expected Behavior |
|----------|----------|-------------|-------------------|
| **Single-source (Aurora)** | "List 10 customers and their state" | Aurora only | Query customer + address |
| **Single-source (Redshift)** | "Top 10 products by units sold" | Redshift only | Aggregate purchases by product |
| **Federated** | "Top 10 spenders with their state" | Aurora + Redshift | Join on cid, aggregate spend |
| **Derived metrics** | "Big spenders per state" | Aurora + Redshift | Apply CLV threshold + group by state |
| **Time-series** | "Revenue trend by month" | Redshift | Group by date dimension |

---

## 4. AtScale Capabilities

### 4.1 Universal Semantic Layer

- **One model, many consumers** — BI tools (SQL/MDX/DAX), AI agents (MCP), data science (Python/REST)
- **No data movement** — queries pushed to source systems at runtime
- **Business logic centralization** — metrics defined once, consistent everywhere
- **Composable architecture** — SML (Semantic Modeling Language) enables Git-based version control

### 4.2 AI-Assisted Modeling Engine

AtScale's AI-powered modeling capabilities accelerate semantic model development:

**Semantic Discovery Engine:**
- Scans warehouse schemas, query history, and data lineage
- Infers candidate joins, hierarchies, and metric definitions
- Identifies patterns across teams and usage

**Model Recommendation System:**
- Suggests new dimensions, measures, and relationships
- Proposes optimizations based on actual query patterns
- Reduces time-to-insight from weeks to hours

**Governed Feedback Loop:**
- Human-in-the-loop review of AI suggestions
- Acceptance/rejection shapes future recommendations
- All changes versioned and auditable via SML

**Benefits for GenAI deployments:**
- Accelerates onboarding of new data domains
- Ensures consistent definitions as models evolve
- Reduces semantic drift across AI and BI consumers
- Enables rapid iteration as business requirements change

### 4.3 Query Acceleration

- **Automatic aggregate management** — monitors query patterns, creates/maintains summary tables
- **Multi-layer caching** — metadata, result, and aggregate caches
- **Intelligent pushdown** — maximizes work done at the source database
- **Performance monitoring** — built-in query analysis and optimization recommendations

### 4.4 MCP Server (AI Agent Integration)

- **Open protocol** — standard MCP implementation for any compatible agent
- **Semantic context delivery** — provides business definitions, not just raw schemas
- **Natural language translation** — converts questions to governed SQL
- **Result provenance** — traces every answer back to source data

### 4.5 Data Source Connectivity

| AWS Service | Connection Type | Use Case |
|-------------|----------------|----------|
| Amazon Redshift | JDBC (native connector) | Analytics warehouse, aggregate storage |
| Amazon Aurora (PostgreSQL/MySQL) | JDBC | Operational databases |
| Amazon Athena | JDBC | Data lake (S3) queries |
| Amazon Redshift Spectrum | Via Redshift | S3 external tables |

---

## 5. Security & Governance

### 5.1 Authentication Architecture

#### Single Sign-On (SSO)

AtScale supports enterprise SSO through Keycloak (bundled) with federation to:

| Identity Provider | Protocol | Use Case |
|-------------------|----------|----------|
| Amazon Cognito | OIDC / SAML 2.0 | AWS-native SSO |
| Okta | OIDC / SAML 2.0 | Enterprise identity |
| Azure Active Directory | OIDC / SAML 2.0 | Microsoft ecosystem |
| PingFederate | SAML 2.0 | Enterprise federation |
| Custom OIDC Provider | OIDC | Any standards-compliant IdP |

**Authentication flow:**
```
User → Chat App → AgentCore Gateway (JWT validation)
                         ↓
              Identity Provider (SSO)
                         ↓
              AtScale Keycloak (federation)
                         ↓
              User identity + roles resolved
                         ↓
              Security policies applied to queries
```

### 5.2 Authorization Model

#### Role-Based Access Control (RBAC)

| Role | Permissions | Data Access |
|------|-------------|-------------|
| Admin | Full model management | All data |
| Analyst | Query execution, model browsing | Per-policy filtered data |
| Marketing | Query execution | No PII, regional filter |
| HR/Compliance | Query execution | Full PII access |
| Data Engineer | Model design, connection management | All data |

#### Attribute-Based Access Control (ABAC)

Fine-grained access based on user attributes:

```yaml
# Example: Regional access based on user attribute
policy:
  name: "regional_access"
  condition: "user.region == data.state"
  effect: "filter rows to user's assigned region"

# Example: Department-based column access
policy:
  name: "pii_access"
  condition: "user.department IN ('HR', 'Compliance')"
  effect: "allow access to SSN, credit card columns"
  default: "mask/redact sensitive columns"
```

### 5.3 Row-Level Security (RLS)

```yaml
# Users see only data relevant to their scope
row_level_security:
  - dimension: "Dim_Address"
    filter: "[state] IN user.assigned_states"
    applies_to: ["regional_sales"]
    
  - dimension: "Dim_Customer"
    filter: "[spend_tier] = 'Platinum'"
    applies_to: ["vip_team"]
```

### 5.4 Column-Level Security (Masking)

| Column | Default View | Privileged View | Masking Rule |
|--------|-------------|-----------------|--------------|
| SSN | `XXX-XX-6789` | `123-45-6789` | Show last 4 only |
| Credit Card | `****-****-****-1234` | Full number | Show last 4 only |
| Email | `j***@company.com` | Full email | Partial redaction |
| Phone | Hidden | Visible | Full redaction |

### 5.5 End-to-End Traceability

Every query through AtScale is fully auditable:

```json
{
  "timestamp": "2026-07-16T10:34:56Z",
  "session_id": "sess-abc123",
  "user_identity": "jsmith@company.com",
  "user_role": "marketing_analyst",
  "authentication_method": "SSO/OIDC",
  "idp": "corporate-okta",
  "question": "Top 10 customers by revenue in California",
  "semantic_model": "Customer_360",
  "generated_sql": "SELECT full_name, total_revenue FROM ...",
  "data_sources_accessed": ["aurora_c360", "redshift_c360"],
  "tables_queried": ["customer", "address", "purchase"],
  "security_policies_applied": ["regional_access", "pii_masking"],
  "rows_returned": 10,
  "execution_time_ms": 850,
  "served_from": "aggregate",
  "agent_framework": "strands-agents",
  "model_invoked": "claude-sonnet-4.6",
  "request_source": "chat-application"
}
```

**Traceability chain:**
```
User Identity (SSO) → Agent Request → AgentCore Gateway (JWT) 
  → AtScale MCP → Query Engine → Data Source 
  → Results (filtered by policy) → Agent → User
```

**Compliance capabilities:**
- Complete query lineage (question → SQL → sources → results)
- User identity tied to every data access
- Security policy enforcement logged
- Retention policies for audit logs
- Export to SIEM/compliance systems

### 5.6 Data Protection

| Layer | Mechanism | Details |
|-------|-----------|---------|
| In Transit | TLS 1.2+ | All connections encrypted |
| At Rest | Source-dependent | AWS KMS encryption on Aurora/Redshift |
| Query Results | Never stored in AtScale | Query-time only, no data copies |
| Credentials | AWS Secrets Manager | Rotatable, never in code |
| Network | VPC isolation | Private subnets, security groups |

---

## 6. Deployment Architecture

### 6.1 AtScale on Amazon EKS

```
┌───────────────────────── Amazon EKS Cluster ─────────────────────────┐
│                                                                       │
│  Namespace: atscale                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  atscale-engine        — Core query processing                  │ │
│  │  atscale-sml-api       — Semantic model API                     │ │
│  │  atscale-sml-web       — Design Center (UI)                     │ │
│  │  atscale-mcp-server    — MCP endpoint for AI agents             │ │
│  │  atscale-keycloak      — Authentication / SSO                   │ │
│  │  atscale-db            — Metadata (PostgreSQL)                  │ │
│  │  atscale-redis         — Query cache                            │ │
│  │  atscale-ingress       — External access (NLB)                  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  Namespace: c360-app                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  chat-application      — Streamlit UI                           │ │
│  │  (uses IRSA for Bedrock access)                                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
```

### 6.2 Infrastructure Components

| Component | AWS Service | Purpose |
|-----------|-------------|---------|
| Container Orchestration | Amazon EKS | Host AtScale + application |
| Operational Database | Amazon Aurora PostgreSQL | Customer data |
| Analytics Warehouse | Amazon Redshift Serverless | Purchase/product data |
| AI/ML | Amazon Bedrock | Foundation model inference |
| Agent Runtime | Amazon Bedrock AgentCore | Managed agent hosting |
| Object Storage | Amazon S3 | Data staging, aggregate storage |
| Secrets | AWS Secrets Manager | Credential management |
| Identity | Amazon Cognito / External IdP | User authentication |
| Networking | VPC + NLB | Secure, isolated network |

### 6.3 Deployment Method

- **Helm chart:** `oci://docker.io/atscaleinc/atscale`
- **Infrastructure reference:** [AtScale K8s Blueprints](https://github.com/AtScaleInc/atscale-k8s-blueprints)
- **Model management:** SML files in Git (version controlled)
- **Configuration as Code:** Helm values + Terraform/CDK

---

## 7. Semantic Modeling with SML

### 7.1 Semantic Modeling Language (SML)

AtScale models are defined in **SML** (YAML-based), enabling:

- **Version control** — models stored in Git
- **CI/CD pipelines** — automated testing and deployment
- **Code review** — pull request workflows for model changes
- **Portability** — models independent of deployment environment

### 7.2 Model Structure (Customer 360 Example)

```yaml
# customer_360.yml
unique_name: customer_360
object_type: model
label: Customer 360
description: |
  Unified Customer 360 semantic model spanning operational and
  analytics data sources with shared customer dimension key.

dimensions:
  - unique_name: dim_customer
    label: Customer
    dataset: aurora_customer
    key_columns: [cid]
    attributes:
      - unique_name: full_name
        expression: "first_name || ' ' || last_name"
      - unique_name: email
      - unique_name: phone

  - unique_name: dim_product
    label: Product
    dataset: redshift_product
    key_columns: [id]
    attributes:
      - unique_name: product_name
        key_column: name
      - unique_name: brand
      - unique_name: product_price
        key_column: price

facts:
  - unique_name: fact_purchase
    dataset: redshift_purchase
    dimension_links:
      - dimension: dim_customer
        join: "fact_purchase.cid = dim_customer.cid"
      - dimension: dim_product
        join: "fact_purchase.pid = dim_product.id"

measures:
  - unique_name: total_revenue
    expression: "SUM(price * quantity)"
    format: "$#,##0.00"

  - unique_name: customer_lifetime_value
    expression: "SUM(price * quantity)"
    description: "Total spend per customer"

calculated_attributes:
  - unique_name: big_spender
    expression: |
      CASE WHEN SUM(price * quantity) > 10000
           THEN 'Yes' ELSE 'No' END
```

### 7.3 AI-Assisted Model Development

The AI-assisted modeling engine accelerates the Customer 360 model creation:

1. **Schema Discovery** — Scans Aurora and Redshift schemas, identifies tables and relationships
2. **Join Inference** — Detects `cid` as the shared key across systems
3. **Metric Suggestions** — Proposes revenue, count, and average measures based on column types
4. **Hierarchy Detection** — Identifies Product → Category → Department hierarchy
5. **Human Review** — Data engineer validates suggestions, refines definitions
6. **Deployment** — Model published via SML to Git, deployed to AtScale engine

---

## 8. Performance Characteristics

### 8.1 Query Acceleration

| Scenario | Without Aggregates | With Aggregates | Improvement |
|----------|-------------------|-----------------|-------------|
| Single-source query | 500-2000ms | 100-300ms | 5-7x |
| Federated query (2 sources) | 1000-4000ms | 200-800ms | 5x |
| Complex aggregation | 3000-10000ms | 300-1000ms | 10x |

### 8.2 Aggregate Management

AtScale automatically:
- Monitors query patterns across all consumers (BI, AI, API)
- Identifies high-value aggregation opportunities
- Creates and maintains aggregate tables in the warehouse
- Routes queries to aggregates when applicable
- Refreshes aggregates based on data freshness requirements

---

## 9. Extensibility

### 9.1 Additional Data Sources

The same architecture extends to:
- Amazon Athena (data lake queries on S3)
- Amazon Redshift Spectrum (external tables)
- Additional Aurora clusters (multi-region)
- Cross-account data sharing

### 9.2 Additional AI Agent Frameworks

AtScale's MCP server works with:
- AWS Strands Agents (demonstrated in this spec)
- LangChain / LangGraph
- Amazon Bedrock Agents
- Any MCP-compatible framework

### 9.3 BI Tool Integration

The same semantic model simultaneously serves:
- Tableau, Power BI, Excel (SQL/MDX/DAX)
- Looker, Superset, ThoughtSpot
- Jupyter Notebooks (Python/REST)
- Custom applications

---

## 10. Summary

This specification demonstrates how AtScale's universal semantic layer, deployed on Amazon EKS, provides the critical **meaning layer** between AI agents and enterprise data. The architecture delivers:

✅ **Natural language access** to governed enterprise data  
✅ **Federated queries** across Aurora and Redshift without ETL  
✅ **Business logic consistency** across AI agents and BI tools  
✅ **Enterprise security** with SSO, RBAC/ABAC, RLS, and column masking  
✅ **Full traceability** from user question to data source access  
✅ **AI-accelerated modeling** that scales with business evolution  
✅ **Production-ready deployment** on Amazon EKS with managed services  

The semantic layer is the missing piece between powerful foundation models and trustworthy enterprise analytics. AtScale fills that gap with a battle-tested platform purpose-built for this role.

---

## Appendix A: Technology Stack

| Layer | Technology |
|-------|-----------|
| Chat Interface | Streamlit |
| Agent Framework | Strands Agents |
| Foundation Model | Anthropic Claude Sonnet (Amazon Bedrock) |
| Agent Runtime | Amazon Bedrock AgentCore |
| Semantic Layer | AtScale (on Amazon EKS) |
| Semantic Model | SML (version-controlled in Git) |
| AI Modeling | AtScale AI-Assisted Modeling Engine |
| Operational DB | Amazon Aurora PostgreSQL |
| Analytics DB | Amazon Redshift Serverless |
| Container Platform | Amazon EKS |
| Object Storage | Amazon S3 |
| Identity | Keycloak + Enterprise IdP (SSO) |
| Secrets | AWS Secrets Manager |
| Protocol | Model Context Protocol (MCP) |

## Appendix B: Reference Data

Data source: [Stardog C360 Knowledge Kit](https://github.com/stardog-union/knowledge-kits/tree/main/examples/c360/data)

| Database | Tables | Rows (Sample) |
|----------|--------|---------------|
| Aurora PostgreSQL | customer, address, credit_card, rewards_account | ~2,000 |
| Redshift Serverless | purchase, product, category, vendor | ~3,500 |

---

**END OF SPECIFICATION**
