# Product Requirements Document (PRD)
# Customer 360 Semantic Layer with AtScale and AWS AI Services

**Document Version:** 1.0  
**Date:** July 13, 2026  
**Author:** JP Boreddy  
**Status:** Draft  

---

## Document Information

| Field | Value |
|-------|-------|
| **Project Name** | Customer 360 Semantic Layer POC |
| **GitHub Repository** | https://github.com/jboreddy/atscale-demo.git |
| **AWS Account** | 652341767951 |
| **AWS Region** | us-east-1 |
| **Target Completion** | 4-6 weeks |
| **Type** | Proof of Concept (POC) |

---

## 1. Executive Summary

### 1.1 Purpose

Build a proof-of-concept that demonstrates an end-to-end **semantic layer for agentic AI** using **AtScale** (deployed on Amazon EKS) and **AWS AI services** (Amazon Bedrock AgentCore, Strands Agents). The system enables natural language querying of Customer 360 data that spans two databases — **Aurora PostgreSQL** (customer/operational data) and **Amazon Redshift** (product/purchase analytics) — through a unified semantic layer, ensuring consistent, governed answers regardless of where the data resides.

### 1.2 Business Context

This POC is inspired by the AWS blog post ["Build a semantic layer for agentic AI on AWS with Stardog and Amazon Bedrock AgentCore"](https://aws.amazon.com/blogs/machine-learning/build-a-semantic-layer-for-agentic-ai-on-aws-with-stardog-and-amazon-bedrock-agentcore/) and adapts the same architecture using **AtScale** instead of Stardog. The key difference is that AtScale uses dimensional modeling (star schema) rather than knowledge graphs (RDF/SPARQL), making it more familiar to traditional BI teams while delivering equivalent semantic layer capabilities for AI agents.

### 1.3 Success Criteria

| Criteria | Target |
|----------|--------|
| End-to-end query flow works | Natural language → AtScale → Data → Answer |
| Federated queries succeed | Join customer (Aurora) + orders (Redshift) |
| Single-source queries work | Aurora-only and Redshift-only queries |
| Calculated metrics work | "Big Spender" derived attribute returns correctly |
| Chat UI functional | Streamlit app accepts questions, returns answers |
| Response latency | < 10 seconds for POC (not optimized) |
| Data accuracy | Results match direct SQL verification |

---

## 2. Problem Statement

Enterprise data is fragmented across operational databases and analytics warehouses. AI agents (LLMs) can write SQL, but without business context they produce:

- Technically valid queries that return **wrong answers** (wrong joins, wrong definitions)
- **Conflicting results** when the same question is asked differently
- **No governance** — agents query raw tables without access controls

A semantic layer solves this by providing a single, governed, business-context-aware interface between AI agents and underlying data sources.

---

## 3. Solution Overview

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Streamlit Chat Application                  │
│              (Natural Language Interface)                     │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTP/WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Strands Agent (Phase 1: Direct SQL Tool)        │
│              + Amazon Bedrock (Claude Sonnet)                │
│                                                              │
│   Phase 2: AgentCore Gateway + AtScale MCP Server           │
└──────────────────────────┬───────────────────────────────────┘
                           │ SQL/REST API
                           ▼
┌─────────────────────────────────────────────────────────────┐
│            AtScale Semantic Layer (on Amazon EKS)            │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Customer 360 Semantic Model                         │   │
│  │  - Dim_Customer (from Aurora)                        │   │
│  │  - Dim_Address (from Aurora)                         │   │
│  │  - Dim_Product (from Redshift)                       │   │
│  │  - Dim_Category (from Redshift)                      │   │
│  │  - Dim_Vendor (from Redshift)                        │   │
│  │  - Fact_Purchase (from Redshift)                     │   │
│  │  - Calculated: Big_Spender, Large_Order              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└────────────────┬─────────────────────────┬───────────────────┘
                 │                         │
                 ▼                         ▼
┌────────────────────────┐   ┌────────────────────────────────┐
│   Aurora PostgreSQL    │   │      Amazon Redshift           │
│                        │   │                                │
│  - customer            │   │  - purchase                    │
│  - address             │   │  - product                     │
│  - credit_card         │   │  - category                    │
│  - rewards_account     │   │  - vendor                      │
└────────────────────────┘   └────────────────────────────────┘
```

### 3.2 Phased Approach

| Phase | Scope | Integration Path |
|-------|-------|-----------------|
| **Phase 1** (Weeks 1-4) | Direct SQL tool in Strands Agent queries AtScale via JDBC/REST | Simple, no MCP dependency |
| **Phase 2** (Weeks 5-6) | AtScale MCP Server registered with AgentCore Gateway | Production-grade pattern |

---

## 4. Data Requirements

### 4.1 Data Source

**Source:** [Stardog C360 Knowledge Kit](https://github.com/stardog-union/knowledge-kits/tree/main/examples/c360/data)

The following CSV files will be loaded into the respective databases:

### 4.2 Aurora PostgreSQL Tables (Customer/Operational Data)

| CSV File | Target Table | Description |
|----------|-------------|-------------|
| `customer.csv` | `public.customer` | Customer profiles (cid, first_name, last_name, email, ssn, phone, location) |
| `address.csv` | `public.address` | Customer addresses (id, cid, city, state, zip, street_name) |
| `credit_card.csv` | `public.credit_card` | Credit card info (id, cid, card_num, card_type) |
| `rewards_account.csv` | `public.rewards_account` | Loyalty program (id, cid, account_id, create_date) |

**Aurora PostgreSQL Schema:**

```sql
-- Database: customer360_db
-- Schema: public

CREATE TABLE customer (
    cid INTEGER PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(200),
    ssn VARCHAR(11),
    phone VARCHAR(20),
    location INTEGER  -- FK to address
);

CREATE TABLE address (
    id INTEGER PRIMARY KEY,
    cid INTEGER REFERENCES customer(cid),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(10),
    street_name VARCHAR(200)
);

CREATE TABLE credit_card (
    id INTEGER PRIMARY KEY,
    cid INTEGER REFERENCES customer(cid),
    card_num VARCHAR(20),
    card_type VARCHAR(50)
);

CREATE TABLE rewards_account (
    id INTEGER PRIMARY KEY,
    cid INTEGER REFERENCES customer(cid),
    account_id VARCHAR(50),
    create_date DATE
);

-- Indexes for join performance
CREATE INDEX idx_address_cid ON address(cid);
CREATE INDEX idx_credit_card_cid ON credit_card(cid);
CREATE INDEX idx_rewards_cid ON rewards_account(cid);
```

### 4.3 Amazon Redshift Tables (Product/Purchase Analytics Data)

| CSV File | Target Table | Description |
|----------|-------------|-------------|
| `purchase.csv` | `public.purchase` | Purchase transactions (id, cid, pid, date, quantity, price, card) |
| `product.csv` | `public.product` | Product catalog (id, name, brand, price, dept) |
| `category.csv` | `public.category` | Product categories (id, dept_name, parent) |
| `vendor.csv` | `public.vendor` | Vendors/suppliers (id, vendor_name, industry) |

**Amazon Redshift Schema:**

```sql
-- Database: analytics_db
-- Schema: public

CREATE TABLE purchase (
    id INTEGER,
    cid INTEGER,          -- Shared key with Aurora customer.cid
    pid INTEGER,          -- FK to product.id
    purchase_date DATE,
    quantity INTEGER,
    price DECIMAL(10,2),
    card INTEGER
) DISTSTYLE KEY DISTKEY(cid) SORTKEY(purchase_date);

CREATE TABLE product (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200),
    brand VARCHAR(100),
    price DECIMAL(10,2),
    dept INTEGER          -- FK to category.id
);

CREATE TABLE category (
    id INTEGER PRIMARY KEY,
    dept_name VARCHAR(100),
    parent INTEGER
);

CREATE TABLE vendor (
    id INTEGER PRIMARY KEY,
    vendor_name VARCHAR(200),
    industry VARCHAR(100)
);
```

### 4.4 Cross-Source Identity

The **shared identifier** across both databases is `cid` (customer ID):
- In Aurora: `customer.cid` is the primary key
- In Redshift: `purchase.cid` is a reference column (no foreign key constraint across databases)

AtScale resolves this by defining a **Customer dimension** with `cid` as the key, sourced from Aurora, and referenced by the Purchase fact table in Redshift.

### 4.5 Data Loading Requirements

| Requirement | Details |
|-------------|---------|
| Load method | CSV import via `psql \copy` (Aurora) and Redshift `COPY` from S3 |
| Data volume | Sample data from C360 kit (~100-1000 rows per table) |
| Refresh frequency | One-time load for POC |
| S3 staging bucket | Required for Redshift COPY command |
| Data validation | Row counts match CSV source; foreign keys resolve |



---

## 5. Infrastructure Requirements

### 5.1 AWS Account & Region

| Parameter | Value |
|-----------|-------|
| **AWS Account ID** | 652341767951 |
| **Primary Region** | us-east-1 |
| **Provisioning Method** | Infrastructure as Code (CDK/Terraform) |
| **Provisioning Scope** | Full stack from scratch |

### 5.2 Networking (VPC)

| Resource | Configuration |
|----------|--------------|
| **VPC** | New VPC, CIDR: 10.1.0.0/16 |
| **Public Subnets** | 2x (10.1.1.0/24, 10.1.2.0/24) — ALB, NAT Gateway |
| **Private Subnets** | 2x (10.1.10.0/24, 10.1.11.0/24) — EKS, Aurora, Redshift |
| **NAT Gateway** | 1x (for outbound internet from private subnets) |
| **Internet Gateway** | 1x (for ALB + NAT) |
| **Availability Zones** | us-east-1a, us-east-1b |

### 5.3 Amazon EKS (AtScale Platform)

**Reference:** [AtScale K8s Blueprints](https://github.com/AtScaleInc/atscale-k8s-blueprints)

| Resource | Configuration |
|----------|--------------|
| **EKS Cluster** | Kubernetes 1.36 |
| **Node Group** | Managed, 2-4 nodes |
| **Instance Type** | m5.2xlarge (8 vCPU, 32 GB RAM) |
| **Storage** | gp3 EBS volumes, 100GB per node |
| **Namespace** | `atscale` |
| **Load Balancer** | AWS ALB (via ALB Ingress Controller) |
| **Add-ons** | CoreDNS, kube-proxy, VPC CNI, EBS CSI Driver |

**AtScale Components on EKS:**
- AtScale Engine (query processing)
- AtScale Design Center (modeling UI)
- AtScale Metadata Store (PostgreSQL or bundled)
- AtScale MCP Server (Phase 2)

### 5.4 Amazon Aurora PostgreSQL

| Resource | Configuration |
|----------|--------------|
| **Engine** | Aurora PostgreSQL 16.13 |
| **Instance Class** | db.r6g.large (2 vCPU, 16 GB) |
| **Storage** | Aurora auto-scaling (min 10 GB) |
| **Database Name** | customer360_db |
| **Master Username** | postgres |
| **Multi-AZ** | No (POC — single writer) |
| **Subnet Group** | Private subnets |
| **Security Group** | Allow 5432 from EKS nodes + Streamlit app |
| **Encryption** | At rest (AWS KMS default key) |
| **Backup** | 1 day retention (POC) |

**Service Accounts:**
- `atscale_reader` — SELECT permissions for AtScale
- `app_loader` — INSERT permissions for data loading

### 5.5 Amazon Redshift

| Resource | Configuration |
|----------|--------------|
| **Type** | Redshift Serverless (or ra3.xlplus single-node) |
| **Namespace** | c360-atscale-ns |
| **Workgroup** | c360-atscale-wg |
| **Database** | analytics_db |
| **Base Capacity** | 8 RPU (Serverless) or 1 node (Provisioned) |
| **Subnet Group** | Private subnets |
| **Security Group** | Allow 5439 from EKS nodes |
| **Encryption** | At rest (AWS KMS default key) |
| **S3 Access** | IAM role for COPY command |

**Recommendation:** Use **Redshift Serverless** for POC to minimize cost (scales to zero when idle).

**Service Accounts:**
- `atscale_service` — SELECT on all tables + full access on `atscale_agg` schema
- `app_loader` — INSERT for data loading

### 5.6 Amazon S3 (Staging)

| Resource | Configuration |
|----------|--------------|
| **Bucket Name** | `c360-poc-data-652341767951-us-east-1` |
| **Purpose** | CSV staging for Redshift COPY, AtScale aggregate storage |
| **Encryption** | SSE-S3 (default) |
| **Lifecycle** | Delete staging objects after 7 days |
| **Access** | Redshift IAM role, EKS service account |

### 5.7 Amazon Bedrock

| Resource | Configuration |
|----------|--------------|
| **Foundation Model** | Anthropic Claude Sonnet 4.6 (`anthropic.claude-sonnet-4-6-v1:0`) |
| **Model Access** | Enable in us-east-1 (Bedrock console) |
| **AgentCore Runtime** | Phase 2 |
| **AgentCore Gateway** | Phase 2 |
| **Prompt Caching** | Enabled (Phase 2) |

### 5.8 Compute for Chat Application

| Resource | Configuration |
|----------|--------------|
| **Type** | EC2 instance or EKS pod |
| **Instance** | t3.medium (2 vCPU, 4 GB) |
| **OS** | Amazon Linux 2023 |
| **Runtime** | Python 3.11+ |
| **Framework** | Streamlit |
| **Access** | Public ALB or port forwarding for POC |

### 5.9 IAM Roles & Policies

| Role | Purpose | Key Permissions |
|------|---------|-----------------|
| `EKSNodeRole` | EKS managed node group | EC2, ECR, EBS, CloudWatch |
| `AtScaleServiceRole` | AtScale to access AWS resources | Redshift, Aurora, S3, Secrets Manager |
| `RedshiftCopyRole` | Redshift COPY from S3 | S3:GetObject on staging bucket |
| `BedrockAgentRole` | Strands Agent to invoke Bedrock | bedrock:InvokeModel |
| `StreamlitAppRole` | Chat app to invoke agent | Bedrock access, network access |

### 5.10 Security Groups

| Security Group | Inbound Rules | Attached To |
|----------------|---------------|-------------|
| `sg-eks-nodes` | 443 from ALB; all from self | EKS nodes |
| `sg-aurora` | 5432 from sg-eks-nodes, sg-streamlit | Aurora |
| `sg-redshift` | 5439 from sg-eks-nodes | Redshift |
| `sg-alb` | 80/443 from 0.0.0.0/0 (POC) | Application Load Balancer |
| `sg-streamlit` | 8501 from sg-alb | Streamlit EC2/pod |

### 5.11 Infrastructure as Code

**Tool:** AWS CDK (Python) or Terraform  
**Repository:** https://github.com/jboreddy/atscale-demo.git (under `infrastructure/` directory)

**Modules/Stacks:**

```
infrastructure/
├── networking/          # VPC, subnets, security groups, NAT
├── database/            # Aurora PostgreSQL, Redshift Serverless
├── eks/                 # EKS cluster, node groups, add-ons
├── storage/             # S3 buckets
├── iam/                 # Roles, policies
├── atscale/             # Helm chart deployment on EKS
└── app/                 # Streamlit app deployment
```

**Estimated provisioning time:** 30-45 minutes (CDK deploy)



---

## 6. Semantic Model Requirements

### 6.1 AtScale Deployment on EKS

**Reference:** [AtScale K8s Blueprints](https://github.com/AtScaleInc/atscale-k8s-blueprints)

| Requirement | Details |
|-------------|---------|
| Deploy AtScale on EKS | Using Helm charts from K8s blueprints repo |
| AtScale License | Obtain trial/POC license from AtScale |
| Metadata Database | PostgreSQL (can be Aurora or embedded) |
| Ingress | ALB Ingress Controller for Design Center UI |
| Persistent Storage | EBS gp3 volumes via EBS CSI Driver |
| Namespace | `atscale` |

### 6.2 Data Connections

| Connection Name | Type | Target | Purpose |
|----------------|------|--------|---------|
| `aurora_c360` | PostgreSQL | Aurora cluster (customer360_db) | Customer operational data |
| `redshift_c360` | Redshift | Redshift Serverless (analytics_db) | Purchase/product analytics |

### 6.3 Semantic Model: Customer_360

#### Dimensions

| Dimension | Source DB | Source Table | Primary Key | Key Attributes |
|-----------|-----------|-------------|-------------|----------------|
| **Dim_Customer** | Aurora | customer | cid | first_name, last_name, email, phone |
| **Dim_Address** | Aurora | address | id | city, state, zip, street_name |
| **Dim_Credit_Card** | Aurora | credit_card | id | card_type (masked: card_num) |
| **Dim_Rewards** | Aurora | rewards_account | id | account_id, create_date |
| **Dim_Product** | Redshift | product | id | name, brand, price, dept |
| **Dim_Category** | Redshift | category | id | dept_name, parent |
| **Dim_Vendor** | Redshift | vendor | id | vendor_name, industry |
| **Dim_Date** | Generated | — | date_key | year, quarter, month, day |

#### Fact Table

| Fact Table | Source DB | Source Table | Grain | Measures |
|-----------|-----------|-------------|-------|----------|
| **Fact_Purchase** | Redshift | purchase | One row per purchase transaction | quantity, price (unit), total_amount (calculated) |

#### Relationships

```
Dim_Customer (cid) ←─── Fact_Purchase (cid)
Dim_Product (id) ←─── Fact_Purchase (pid)
Dim_Customer (cid) ←─── Dim_Address (cid)
Dim_Customer (cid) ←─── Dim_Credit_Card (cid)
Dim_Customer (cid) ←─── Dim_Rewards (cid)
Dim_Product (dept) ──→ Dim_Category (id)
```

#### Calculated Measures

| Measure | Formula | Description |
|---------|---------|-------------|
| **Total Revenue** | `SUM(Fact_Purchase.price * Fact_Purchase.quantity)` | Total sales amount |
| **Order Count** | `COUNT(Fact_Purchase.id)` | Number of transactions |
| **Avg Order Value** | `Total Revenue / Order Count` | Average spend per order |
| **Customer Lifetime Value** | `SUM(price * quantity) per customer` | Total spend by customer |
| **Units Sold** | `SUM(Fact_Purchase.quantity)` | Total units sold |

#### Derived Attributes (Calculated Dimensions)

| Attribute | Logic | Description |
|-----------|-------|-------------|
| **Big_Spender** | `IF Customer_Lifetime_Value > threshold THEN 'Yes' ELSE 'No'` | High-value customer flag |
| **Large_Order** | `IF (price * quantity) > threshold THEN 'Yes' ELSE 'No'` | High-value order flag |
| **Spend_Tier** | `CASE WHEN CLV > 50000 THEN 'Platinum' WHEN CLV > 10000 THEN 'Gold' ELSE 'Standard'` | Customer segment |

### 6.4 Semantic Model in SML (Semantic Modeling Language)

AtScale supports programmatic model definition via **SML** (stored in Git). The Customer_360 model should be defined in SML for version control.

```yaml
# Example SML structure (simplified)
model:
  name: Customer_360
  description: "Customer 360 semantic model spanning operational and analytics data"
  
  connections:
    - name: aurora_c360
      type: postgresql
    - name: redshift_c360
      type: redshift
  
  dimensions:
    - name: Dim_Customer
      connection: aurora_c360
      table: customer
      primary_key: cid
      attributes:
        - name: first_name
        - name: last_name
        - name: email
        - name: phone
        - name: ssn
          security: sensitive
  
  facts:
    - name: Fact_Purchase
      connection: redshift_c360
      table: purchase
      relationships:
        - dimension: Dim_Customer
          join: "Fact_Purchase.cid = Dim_Customer.cid"
        - dimension: Dim_Product
          join: "Fact_Purchase.pid = Dim_Product.id"
      measures:
        - name: Total_Revenue
          expression: "SUM(price * quantity)"
        - name: Order_Count
          expression: "COUNT(id)"
```

---

## 7. Functional Requirements

### 7.1 Chat Application (Streamlit)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | User can type natural language questions about C360 data | Must |
| FR-02 | Agent processes question and returns answer with supporting data | Must |
| FR-03 | Display tabular results when applicable | Must |
| FR-04 | Show the SQL generated by the semantic layer (for transparency) | Should |
| FR-05 | Maintain conversation history within a session | Should |
| FR-06 | Handle errors gracefully (connection issues, timeouts) | Must |
| FR-07 | Display data source(s) used for each answer | Should |
| FR-08 | Support follow-up questions (context retention) | Nice to have |

### 7.2 Sample Queries (Must Support)

The POC must correctly answer these categories of questions:

#### Aurora-Only Queries
| # | Question | Expected Behavior |
|---|----------|-------------------|
| Q1 | "List 10 customers and their state" | Query Aurora only |
| Q2 | "How many customers are in Wisconsin?" | Count with state filter |
| Q3 | "Show customer email addresses in California" | Filter by state |

#### Redshift-Only Queries
| # | Question | Expected Behavior |
|---|----------|-------------------|
| Q4 | "Top 10 products by units sold" | Aggregate from Redshift |
| Q5 | "Revenue by product category" | Join product + category + purchase |
| Q6 | "Which vendors have the most products?" | Group by vendor |

#### Federated Queries (Aurora + Redshift)
| # | Question | Expected Behavior |
|---|----------|-------------------|
| Q7 | "Who are our top 10 customer spenders, with their state?" | Join customer (Aurora) + purchases (Redshift) on cid |
| Q8 | "Big spenders in Wisconsin" | Federated + derived attribute |
| Q9 | "Average order value by customer state" | Federated aggregation |
| Q10 | "Which state has the highest total revenue?" | Federated + group by state |

#### Derived Metric Queries
| # | Question | Expected Behavior |
|---|----------|-------------------|
| Q11 | "How many big spenders do we have per state?" | Apply Big_Spender rule, group by state |
| Q12 | "List all large orders above $500" | Apply Large_Order threshold |
| Q13 | "What is the customer lifetime value for John Smith?" | Calculate CLV per customer |

### 7.3 Agent Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| AG-01 | Use Strands Agents framework | Must |
| AG-02 | Foundation model: Claude Sonnet on Amazon Bedrock | Must |
| AG-03 | Phase 1: Direct SQL/REST tool to query AtScale | Must |
| AG-04 | Phase 2: AtScale MCP Server via AgentCore Gateway | Should |
| AG-05 | System prompt includes semantic model metadata | Must |
| AG-06 | Agent can determine which tool to use based on question | Must |
| AG-07 | Agent formats results in human-readable form | Must |
| AG-08 | Agent handles "I don't know" gracefully | Must |

### 7.4 Phase 1: Direct Tool Integration

```python
# Strands Agent with direct AtScale tool
@tool
def query_atscale(sql: str) -> dict:
    """
    Execute a SQL query against the AtScale semantic layer.
    AtScale translates this into optimized queries against 
    Aurora PostgreSQL and/or Amazon Redshift.
    
    Available dimensions: Dim_Customer, Dim_Address, Dim_Product, 
    Dim_Category, Dim_Vendor
    Available measures: Total_Revenue, Order_Count, Avg_Order_Value,
    Customer_Lifetime_Value, Units_Sold
    
    Args:
        sql: SQL query using AtScale semantic model
    Returns:
        Query results as list of dictionaries
    """
    # Connect to AtScale via JDBC/REST
    pass
```

### 7.5 Phase 2: MCP Integration

| ID | Requirement | Priority |
|----|-------------|----------|
| MCP-01 | Deploy AtScale MCP Server as container on EKS | Should |
| MCP-02 | Register MCP Server with AgentCore Gateway | Should |
| MCP-03 | Configure AgentCore Identity with AtScale credentials | Should |
| MCP-04 | Agent accesses semantic layer via MCP tools | Should |
| MCP-05 | Deploy agent to AgentCore Runtime | Should |

---

## 8. Non-Functional Requirements

### 8.1 Performance (POC Targets)

| Metric | Target | Notes |
|--------|--------|-------|
| Single-source query latency | < 5 seconds | Includes LLM + AtScale + DB |
| Federated query latency | < 10 seconds | Cross-database join |
| Chat UI responsiveness | Loading indicator within 500ms | User feedback |
| Concurrent users | 1 (POC) | Single user demo |

### 8.2 Reliability (POC Targets)

| Metric | Target |
|--------|--------|
| Availability | Best effort (no SLA for POC) |
| Data freshness | Static (one-time load) |
| Error handling | Graceful degradation with user message |

### 8.3 Security (POC Minimal)

| Requirement | Details |
|-------------|---------|
| Data encryption in transit | TLS for all connections |
| Data encryption at rest | AWS default encryption |
| No public database endpoints | Private subnets only |
| Secrets management | AWS Secrets Manager for DB passwords |
| IAM-based access | Least-privilege roles |
| No PII exposure in chat | SSN not queryable (out of scope for POC) |

### 8.4 Observability (POC Minimal)

| Requirement | Details |
|-------------|---------|
| EKS logging | CloudWatch Container Insights |
| Query logging | AtScale built-in query logs |
| Application logging | Streamlit stdout to CloudWatch |
| Cost monitoring | AWS Cost Explorer tags |



---

## 9. Implementation Plan

### 9.1 Phase 1: Infrastructure & Data (Weeks 1-2)

#### Week 1: AWS Infrastructure Provisioning

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Create IaC project (CDK/Terraform) | Repository initialized |
| 1-2 | Provision VPC, subnets, security groups | Networking stack deployed |
| 2-3 | Deploy Aurora PostgreSQL | Database available, schemas created |
| 3 | Deploy Redshift Serverless | Namespace/workgroup available |
| 3-4 | Create S3 bucket, IAM roles | Staging infrastructure ready |
| 4-5 | Deploy EKS cluster | Cluster running with node group |
| 5 | Validate networking (connectivity tests) | All services can communicate |

#### Week 2: Data Loading & AtScale Setup

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Download C360 CSVs from GitHub | Data files ready |
| 1-2 | Load customer data into Aurora | 4 tables populated, verified |
| 2 | Upload CSVs to S3, COPY into Redshift | 4 tables populated, verified |
| 2-3 | Validate data (counts, joins, foreign keys) | Data quality confirmed |
| 3-4 | Deploy AtScale on EKS (Helm chart) | AtScale Design Center accessible |
| 4-5 | Create AtScale data connections | Aurora + Redshift connected |
| 5 | Build Customer_360 semantic model | Model published, test queries pass |

### 9.2 Phase 1: Agent & Chat App (Weeks 3-4)

#### Week 3: Agent Development

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Set up Python project (Strands Agent) | Project structure, dependencies |
| 1-2 | Implement direct SQL tool (JDBC/REST to AtScale) | Tool can query AtScale |
| 2-3 | Write system prompt with model metadata | Agent understands available data |
| 3-4 | Test agent against all sample queries (Q1-Q13) | All queries return correct results |
| 4-5 | Handle edge cases (errors, no data, ambiguity) | Robust error handling |
| 5 | Performance baseline (measure latencies) | Baseline metrics documented |

#### Week 4: Chat Application

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Build Streamlit UI (chat interface) | Basic chat layout working |
| 2-3 | Integrate agent with Streamlit | End-to-end flow works |
| 3 | Add result formatting (tables, text) | Results display clearly |
| 3-4 | Add SQL transparency view | User can see generated SQL |
| 4 | Deploy Streamlit to EC2/EKS | App accessible via browser |
| 5 | End-to-end demo testing | All Q1-Q13 pass via UI |

### 9.3 Phase 2: MCP & AgentCore (Weeks 5-6)

#### Week 5: MCP Server Setup

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Deploy AtScale MCP Server on EKS | MCP endpoint available |
| 2-3 | Register MCP with AgentCore Gateway | Gateway routes to MCP |
| 3-4 | Configure AgentCore Identity (credentials) | Auth chain works |
| 4-5 | Test MCP tools (atscale_ask, atscale_query) | MCP invocation succeeds |

#### Week 6: AgentCore Runtime & Polish

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Deploy agent to AgentCore Runtime | Agent running in managed env |
| 2-3 | Update Streamlit to call via Gateway | E2E via AgentCore |
| 3-4 | Enable prompt caching | Cost optimized |
| 4-5 | Final demo preparation & documentation | POC complete |

---

## 10. Milestones & Acceptance Criteria

### Milestone 1: Infrastructure Ready (End of Week 1)

**Acceptance Criteria:**
- [ ] VPC with public/private subnets deployed
- [ ] Aurora PostgreSQL accessible from private subnet
- [ ] Redshift Serverless accessible from private subnet
- [ ] EKS cluster running with 2+ nodes
- [ ] S3 bucket created
- [ ] All security groups configured
- [ ] IAM roles created with least-privilege

### Milestone 2: Data & Semantic Layer Ready (End of Week 2)

**Acceptance Criteria:**
- [ ] All C360 CSV data loaded into Aurora (4 tables)
- [ ] All C360 CSV data loaded into Redshift (4 tables)
- [ ] Data validated (row counts, sample queries)
- [ ] AtScale deployed on EKS and Design Center accessible
- [ ] AtScale connected to Aurora and Redshift
- [ ] Customer_360 semantic model created and published
- [ ] Test SQL query through AtScale returns correct results

### Milestone 3: Agent Working (End of Week 3)

**Acceptance Criteria:**
- [ ] Strands Agent can invoke Claude Sonnet via Bedrock
- [ ] Agent tool can query AtScale semantic layer
- [ ] All 13 sample queries (Q1-Q13) return correct answers
- [ ] Federated queries join Aurora + Redshift data correctly
- [ ] Derived metrics (Big_Spender) calculate correctly
- [ ] Error handling works for invalid questions

### Milestone 4: Chat Application Live (End of Week 4)

**Acceptance Criteria:**
- [ ] Streamlit app accessible via browser
- [ ] User can type natural language questions
- [ ] Agent returns formatted answers
- [ ] SQL transparency visible
- [ ] Session history maintained
- [ ] End-to-end demo passes all sample queries

### Milestone 5: MCP Integration (End of Week 6) — Optional

**Acceptance Criteria:**
- [ ] AtScale MCP Server deployed on EKS
- [ ] MCP registered with AgentCore Gateway
- [ ] Agent invokes semantic layer via MCP protocol
- [ ] Agent deployed to AgentCore Runtime
- [ ] Prompt caching enabled and verified

---

## 11. Risks & Mitigations

| # | Risk | Probability | Impact | Mitigation |
|---|------|-------------|--------|------------|
| R1 | AtScale K8s blueprint compatibility issues with EKS | Medium | High | Test early; contact AtScale support; fall back to Docker Compose if needed |
| R2 | AtScale license not available for POC | Medium | High | Request trial license early; have backup plan with AtScale Cloud free tier |
| R3 | AtScale MCP Server not GA or limited functionality | Medium | Medium | Phase 1 uses direct tool (no MCP dependency); Phase 2 is optional |
| R4 | Federated query performance below expectations | Low | Medium | Accept higher latency for POC; optimize with aggregates later |
| R5 | C360 CSV data doesn't match expected schema | Low | Low | Review CSVs first; adapt DDL to actual column names |
| R6 | Bedrock model access not enabled in account | Low | High | Request model access early; verify in Bedrock console |
| R7 | EKS node sizing insufficient for AtScale | Medium | Medium | Start with m5.2xlarge; scale up if needed |
| R8 | Cross-database join via AtScale doesn't work as expected | Low | High | Validate with simple 2-table join first; escalate to AtScale support |
| R9 | Strands Agent framework limitations | Low | Low | Fallback to LangChain/LangGraph if needed |
| R10 | Cost overruns (EKS + Aurora + Redshift + Bedrock) | Medium | Low | Use Serverless where possible; shut down when not demoing |

---

## 12. Cost Estimate (Monthly, POC)

| Service | Configuration | Est. Monthly Cost |
|---------|--------------|-------------------|
| **EKS Cluster** | Control plane | $73 |
| **EKS Nodes** | 2x m5.2xlarge (on-demand) | $560 |
| **Aurora PostgreSQL** | db.r6g.large, single-AZ | $180 |
| **Redshift Serverless** | 8 RPU base, low usage | $50-150 |
| **S3** | <1 GB staging | $1 |
| **NAT Gateway** | 1x, moderate traffic | $45 |
| **ALB** | 1x, low traffic | $25 |
| **Bedrock (Claude)** | ~100 queries/day testing | $30-60 |
| **EC2 (Streamlit)** | t3.medium | $30 |
| **Secrets Manager** | 3-4 secrets | $2 |
| **CloudWatch** | Logs + metrics | $10 |
| **Total Estimate** | | **~$1,000 - $1,200/month** |

**Cost Optimization for POC:**
- Shut down EKS nodes outside business hours (saves ~60% on nodes)
- Use Redshift Serverless (scales to zero)
- Consider Spot Instances for EKS nodes (saves ~70%)
- Stop Aurora outside business hours

---

## 13. Dependencies & Prerequisites

### External Dependencies

| Dependency | Owner | Required By | Status |
|-----------|-------|-------------|--------|
| AtScale trial/POC license | AtScale Sales | Week 2 | ⬜ Not started |
| AtScale K8s blueprints (Helm chart access) | AtScale / GitHub | Week 2 | ⬜ Public repo |
| Amazon Bedrock model access (Claude Sonnet) | AWS | Week 3 | ⬜ Request needed |
| C360 CSV data files | Stardog GitHub | Week 2 | ✅ Public repo |
| AWS account access (652341767951) | Internal | Week 1 | ⬜ Verify permissions |

### Project Repository

| Field | Value |
|-------|-------|
| **GitHub Repository** | https://github.com/jboreddy/atscale-demo.git |
| **Purpose** | Store all project artifacts (IaC, agent code, models, scripts, docs) |

**Repository Structure:**
```
atscale-demo/
├── README.md                    # Project overview and setup instructions
├── docs/                        # PRD, architecture docs, research
│   └── PRD.md
├── infrastructure/              # IaC (CDK/Terraform)
│   ├── networking/              # VPC, subnets, security groups
│   ├── database/                # Aurora, Redshift
│   ├── eks/                     # EKS cluster, node groups
│   ├── storage/                 # S3 buckets
│   ├── iam/                     # Roles, policies
│   └── app/                     # Streamlit deployment
├── data/                        # C360 CSV files + loading scripts
│   ├── csv/                     # Raw CSV from Stardog C360 kit
│   ├── aurora/                  # Aurora DDL + load scripts
│   └── redshift/                # Redshift DDL + load scripts
├── atscale/                     # AtScale configuration
│   ├── helm/                    # Helm values for EKS deployment
│   └── models/                  # SML model definitions
├── agent/                       # Strands Agent code
│   ├── tools/                   # AtScale query tools
│   ├── prompts/                 # System prompts
│   └── tests/                   # Agent test cases (Q1-Q13)
├── app/                         # Streamlit chat application
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
└── scripts/                     # Utility scripts
    ├── setup.sh                 # One-click setup
    ├── load-data.sh             # Data loading automation
    └── teardown.sh              # Clean up all resources
```

### Technical Prerequisites

| Prerequisite | Details |
|-------------|---------|
| kubectl configured | For EKS management |
| Helm 3.x installed | For AtScale deployment |
| AWS CLI v2 configured | For infrastructure provisioning |
| Python 3.11+ | For agent and Streamlit app |
| Docker | For local testing |
| Git | For source control |
| CDK CLI or Terraform CLI | For IaC |
| GitHub access | Push to https://github.com/jboreddy/atscale-demo.git |

---

## 14. Out of Scope (POC)

The following are explicitly **out of scope** for this POC:

| Item | Rationale |
|------|-----------|
| Multi-user authentication (SSO, RBAC) | POC is single-user demo |
| Row-level security policies | Deferred to production phase |
| Column masking (SSN, credit card) | Deferred to production phase |
| CI/CD pipeline | Manual deployment for POC |
| Monitoring & alerting (PagerDuty, etc.) | Basic CloudWatch only |
| High availability (Multi-AZ, replicas) | Single-AZ acceptable for POC |
| Data refresh / ETL pipeline | One-time load |
| BI tool integration (Tableau, Power BI) | Focus is on AI agent path |
| Load testing / performance optimization | Functional correctness focus |
| Production hardening | Security, DR, backup |
| Cost allocation tags | Not needed for POC |
| Custom domain / HTTPS certificate | ALB default sufficient |

---

## 15. Appendices

### Appendix A: C360 Data Source (GitHub)

**Repository:** https://github.com/stardog-union/knowledge-kits/tree/main/examples/c360/data

**CSV Files:**
- `customer.csv` — Customer profiles
- `address.csv` — Customer addresses
- `credit_card.csv` — Payment methods
- `rewards_account.csv` — Loyalty program
- `purchase.csv` — Purchase transactions
- `product.csv` — Product catalog
- `category.csv` — Product categories
- `vendor.csv` — Suppliers

### Appendix B: AtScale K8s Blueprints

**Repository:** https://github.com/AtScaleInc/atscale-k8s-blueprints

**Key files:**
- Helm chart values for EKS
- Kubernetes manifests
- Configuration templates
- Deployment instructions

### Appendix C: Reference Architecture Blog

**URL:** https://aws.amazon.com/blogs/machine-learning/build-a-semantic-layer-for-agentic-ai-on-aws-with-stardog-and-amazon-bedrock-agentcore/

**Key architectural patterns adapted:**
1. Three-layer architecture (Model + Meaning + Runtime)
2. Semantic layer sits between agent and databases
3. Data stays in place (no ETL)
4. MCP integration with AgentCore
5. Foundation model for planning + NL understanding
6. Shared identity key for cross-source joins

### Appendix D: Technology Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| **Frontend** | Streamlit | Latest |
| **Agent Framework** | Strands Agents | Latest |
| **Foundation Model** | Claude Sonnet 4.6 | anthropic.claude-sonnet-4-6-v1:0 |
| **Model Provider** | Amazon Bedrock | - |
| **Agent Runtime (Phase 2)** | Amazon Bedrock AgentCore | - |
| **Semantic Layer** | AtScale | Latest (from K8s blueprints) |
| **Semantic Model** | AtScale SML | - |
| **Container Orchestration** | Amazon EKS | 1.29+ |
| **Operational Database** | Aurora PostgreSQL | 15.x |
| **Analytics Database** | Redshift Serverless | - |
| **Object Storage** | Amazon S3 | - |
| **Secrets** | AWS Secrets Manager | - |
| **IaC** | AWS CDK or Terraform | - |
| **Language** | Python | 3.11+ |

### Appendix E: Validation Query Matrix

| Query | Data Source(s) | Join Key | Expected Output |
|-------|---------------|----------|-----------------|
| Q1: List 10 customers + state | Aurora (customer, address) | cid | 10 rows: name, state |
| Q2: Customers in Wisconsin | Aurora (customer, address) | cid | Count by state='WI' |
| Q3: Emails in California | Aurora (customer, address) | cid | Emails where state='CA' |
| Q4: Top 10 products by units | Redshift (purchase, product) | pid | Product name + quantity |
| Q5: Revenue by category | Redshift (purchase, product, category) | pid, dept | Category + sum |
| Q6: Vendors by product count | Redshift (product, vendor) | vendor_id | Vendor + count |
| Q7: Top 10 spenders + state | Aurora + Redshift | **cid** | Name, state, total_spend |
| Q8: Big spenders in WI | Aurora + Redshift | **cid** | Filtered by threshold + state |
| Q9: AOV by state | Aurora + Redshift | **cid** | State + avg(price*qty) |
| Q10: Highest revenue state | Aurora + Redshift | **cid** | State with max revenue |
| Q11: Big spenders per state | Aurora + Redshift | **cid** | Count per state |
| Q12: Large orders > $500 | Redshift (purchase) | — | Orders > threshold |
| Q13: CLV for specific customer | Aurora + Redshift | **cid** | Single customer total |

---

## 16. Approval & Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | | | |
| Technical Lead | | | |
| Data Engineer | | | |
| Solutions Architect | | | |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-13 | JP Boreddy | Initial draft |

---

**END OF PRD**
