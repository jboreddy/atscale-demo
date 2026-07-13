# Application Design - Components

## System Overview

The Customer 360 Semantic Layer POC consists of 5 major components deployed across AWS infrastructure.

---

## Component 1: Infrastructure (AWS CDK)

**Purpose:** Provision and manage all AWS resources required by the system.

**Responsibilities:**
- VPC networking (subnets, security groups, NAT, IGW)
- Amazon EKS cluster (nodes, add-ons, IAM)
- Amazon Aurora PostgreSQL (cluster, database, users)
- Amazon Redshift Serverless (namespace, workgroup)
- Amazon S3 (staging bucket)
- IAM roles and policies
- AWS Secrets Manager (credentials)

**Interface:**
- Input: CDK app configuration (account, region, CIDR, sizing)
- Output: CloudFormation stacks deploying all resources
- Exports: VPC ID, Subnet IDs, Cluster endpoints, Security Group IDs, Role ARNs

**Technology:** AWS CDK (Python), CloudFormation

---

## Component 2: Data Layer

**Purpose:** Download C360 CSV data, create database schemas, and load data into Aurora and Redshift.

**Responsibilities:**
- Download CSV files from Stardog C360 GitHub repository
- Create DDL schemas in Aurora PostgreSQL (customer, address, credit_card, rewards_account)
- Create DDL schemas in Redshift (purchase, product, category, vendor)
- Upload CSVs to S3 staging bucket
- Execute COPY commands for Redshift loading
- Execute \copy or INSERT for Aurora loading
- Validate data integrity (row counts, foreign key resolution)

**Interface:**
- Input: Database endpoints (from Infrastructure), CSV files
- Output: Populated tables in Aurora + Redshift
- Validation: Row count verification script

**Technology:** Python scripts, psycopg2, boto3, SQL DDL

---

## Component 3: Semantic Layer (AtScale on EKS)

**Purpose:** Deploy AtScale platform on EKS and configure the Customer_360 semantic model.

**Responsibilities:**
- Deploy AtScale via Helm chart (from atscale-k8s-blueprints)
- Configure data connections to Aurora and Redshift
- Define Customer_360 semantic model (SML)
  - Dimensions: Customer, Address, Product, Category, Vendor, Date
  - Fact: Purchase
  - Calculated measures: Total Revenue, Order Count, AOV, CLV
  - Derived attributes: Big_Spender, Large_Order, Spend_Tier
- Publish model for query access
- Expose REST/SQL endpoint for agent consumption

**Interface:**
- Input: EKS cluster (from Infrastructure), DB endpoints, AtScale license
- Output: AtScale query endpoint (HTTP/SQL)
- API: AtScale REST API for query submission and model metadata

**Technology:** Helm, Kubernetes manifests, AtScale SML (YAML), AtScale Design Center

---

## Component 4: AI Agent (Strands Agent)

**Purpose:** Process natural language questions and query the semantic layer to produce answers.

**Responsibilities:**
- Accept natural language questions from the chat UI
- Invoke Claude Sonnet 4.6 via Amazon Bedrock for reasoning
- Translate questions into SQL queries against AtScale
- Execute queries via direct SQL tool (Phase 1) or MCP (Phase 2)
- Format results into human-readable answers
- Maintain session context for follow-up questions
- Handle errors gracefully

**Interface:**
- Input: Natural language question (string), session_id
- Output: Formatted answer (string), metadata (SQL used, sources, row count)
- Tool Interface: `query_atscale(sql: str) -> dict`
- Model: Amazon Bedrock `anthropic.claude-sonnet-4-6-v1:0`

**Technology:** Python, Strands Agents, boto3 (Bedrock), pyodbc/REST client

---

## Component 5: Chat Application (Streamlit)

**Purpose:** Provide a web-based chat interface for users to interact with the AI agent.

**Responsibilities:**
- Render chat UI (message input, conversation history)
- Send user questions to the Agent component
- Display formatted answers (text + tables)
- Show SQL transparency panel (expandable)
- Display data source metadata
- Maintain session state (conversation history)
- Handle loading states and errors

**Interface:**
- Input: User text input (browser)
- Output: Rendered HTML (chat messages, tables)
- Dependency: Invokes Agent component directly (same process)

**Technology:** Python, Streamlit, pandas (for table formatting)
