# Implementing a Semantic Layer using AtScale and AWS AI Services

**Research Date:** July 13, 2026  
**Reference Architecture:** Based on AWS blog post - "Build a semantic layer for agentic AI on AWS with Stardog and Amazon Bedrock AgentCore"

---

## Executive Summary

This research document provides comprehensive guidance on implementing a semantic layer using **AtScale** and **AWS AI services** (particularly Amazon Bedrock AgentCore), adapted from the reference architecture that uses Stardog. The implementation enables agentic AI systems to query enterprise data with business context, governance, and consistent results across multiple data sources.

### Key Findings

1. **AtScale provides a universal semantic layer** that can replace Stardog's knowledge graph approach with a more traditional dimensional modeling paradigm
2. **Model Context Protocol (MCP)** is the key integration point between AtScale and Amazon Bedrock AgentCore
3. **AtScale's MCP Server** enables AI agents to access semantically-rich data models with built-in governance
4. **Architecture differences** exist but the overall pattern remains similar: semantic layer sits between AI agents and raw data sources
5. **Data stays in place** - AtScale federates queries to AWS data sources (Redshift, Athena, Aurora) without ETL

### Critical Differences: AtScale vs. Stardog

| Aspect | Stardog | AtScale |
|--------|---------|---------|
| **Data Model** | Knowledge Graph (RDF/OWL ontologies) | Dimensional/Star Schema (cubes) |
| **Query Language** | SPARQL | SQL, MDX, DAX |
| **Identity Model** | IRIs (Internationalized Resource Identifiers) | Traditional dimension keys |
| **Reasoning** | OWL reasoning + rules (SRS/SWRL) | Calculated measures + hierarchies |
| **Federation** | Virtual graphs via SPARQL-to-SQL | Live query push-down via SQL |
| **Tool Integration** | Native MCP server (Voicebox) | AtScale MCP Server |

---

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Core Components](#core-components)
4. [Implementation Approach](#implementation-approach)
5. [Technical Architecture](#technical-architecture)
6. [Integration Patterns](#integration-patterns)
7. [Data Sources and Connectivity](#data-sources-and-connectivity)
8. [Security and Governance](#security-and-governance)
9. [Deployment Options](#deployment-options)
10. [Step-by-Step Implementation](#step-by-step-implementation)
11. [Sample Use Case](#sample-use-case)
12. [Limitations and Considerations](#limitations-and-considerations)
13. [Conclusion and Recommendations](#conclusion-and-recommendations)

---

## 1. Introduction

### The Problem: Why Semantic Layers Matter for Agentic AI

Enterprise data is fragmented across multiple systems with inconsistent definitions:
- "Customer" in CRM ≠ "Customer" in billing system
- "Revenue" calculated differently by regional teams
- Data scattered across Aurora, Redshift, Athena, S3

**Generative AI agents** can plan and write SQL, but without business context, they produce:
- Technically valid queries that return wrong answers
- Conflicting results for the same question
- Unexplainable outputs that erode trust

### The Solution: Semantic Layer + AI Agents

A **semantic layer** sits between AI agents and raw data, providing:
1. **Unified business definitions** - metrics, relationships, business rules defined once
2. **Data federation** - query across multiple sources without ETL
3. **Governance** - row/column-level security, consistent access policies
4. **Performance** - intelligent aggregation and caching

### Why AtScale for Semantic Layer?

AtScale is a proven **universal semantic layer platform** with:
- 13+ years of enterprise maturity
- Native connectivity to AWS data platforms (Redshift, Athena, Aurora, S3)
- MCP integration for AI agents
- Dimensional modeling approach familiar to BI teams
- Built-in query acceleration through aggregate management
- Support for SQL, MDX, DAX, REST, and Python interfaces


---

## 2. Architecture Overview

### Reference Architecture (Stardog Pattern)

The Stardog blog post demonstrates a three-layer architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
│              (Application, Agent, Studio)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              AgentCore Gateway (JWT validation)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│     AgentCore Runtime (Strands Agent + Claude Sonnet)      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼ (Two paths)
          ┌────────────┴────────────┐
          │                         │
    Path A: Direct SPARQL     Path B: MCP Server
          │                         │
          ▼                         ▼
┌─────────────────────────────────────────────────────────────┐
│        Stardog Semantic Layer (Knowledge Graph)             │
│  - Ontology (concepts, relationships)                       │
│  - Virtual Graphs (mappings to sources)                     │
│  - Reasoning Rules                                          │
└──────────────┬──────────────────┬────────────────────────────┘
               │                  │
               ▼                  ▼
         ┌─────────┐        ┌──────────┐
         │ Aurora  │        │ Redshift │
         │(RDS PG) │        │          │
         └─────────┘        └──────────┘
```

### Adapted Architecture (AtScale Pattern)

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
│              (Application, Agent, Studio)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│     Amazon Bedrock AgentCore Gateway (JWT validation)       │
│              + Identity (Credential Management)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│     AgentCore Runtime (Strands Agent + Claude Sonnet)      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼ (MCP Protocol)
┌─────────────────────────────────────────────────────────────┐
│              AtScale MCP Server                             │
│         (Registered as Gateway Tool Target)                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         AtScale Semantic Layer (Universal SL)               │
│  - Semantic Models (cubes, dimensions, measures)            │
│  - Data Connections (to AWS sources)                        │
│  - Business Logic & Calculations                            │
│  - Query Acceleration (aggregate tables)                    │
└──────────────┬──────────────────┬────────────────────────────┘
               │                  │                  │
               ▼                  ▼                  ▼
         ┌─────────┐        ┌──────────┐      ┌────────┐
         │ Aurora  │        │ Redshift │      │ Athena │
         │(RDS PG) │        │          │      │  (S3)  │
         └─────────┘        └──────────┘      └────────┘
```

### Key Architectural Differences

1. **Model Abstraction Layer**
   - **Stardog:** RDF ontology with virtual graphs
   - **AtScale:** Star schema with dimensional models (cubes)

2. **Integration Protocol**
   - **Stardog:** Direct SPARQL or MCP (Voicebox API)
   - **AtScale:** MCP Server (always via Model Context Protocol)

3. **Query Translation**
   - **Stardog:** SPARQL → SQL per virtual graph
   - **AtScale:** Natural language/SQL → Optimized SQL with aggregates

4. **Query Acceleration**
   - **Stardog:** Query planning + federation optimization
   - **AtScale:** Automatic aggregate table creation and management



---

## 3. Core Components

### 3.1 Amazon Bedrock AgentCore

**AgentCore** is AWS's fully managed platform for building, deploying, and operating AI agents at scale.

#### AgentCore Gateway
- **Function:** Entry point for inbound agent requests
- **Capabilities:**
  - JWT validation from identity providers
  - Request routing to AgentCore Runtime
  - MCP server registration and management
  - Tool discovery and invocation
  - Credential injection from AgentCore Identity

#### AgentCore Runtime
- **Function:** Hosts and executes AI agents
- **Capabilities:**
  - Agent session management
  - Concurrency handling
  - Memory management
  - Foundation model integration (Amazon Bedrock)
  - Tool invocation framework

#### AgentCore Identity
- **Function:** Centralized credential management
- **Capabilities:**
  - Secure storage of service credentials
  - Token injection at Gateway hop
  - No credentials in agent code
  - Integration with AWS Secrets Manager

### 3.2 AtScale Platform

**AtScale** is a universal semantic layer platform that virtualizes data access and centralizes business logic.

#### AtScale Design Center
- **Visual modeling interface** for creating semantic models
- **Capabilities:**
  - Drag-and-drop dimensional modeling
  - Relationship definition (star/snowflake schemas)
  - Calculated measure creation
  - Hierarchy definition
  - Security model configuration

#### AtScale Query Engine
- **High-performance query processor** with intelligent optimization
- **Capabilities:**
  - Live query federation across data sources
  - Automatic aggregate detection and usage
  - Query rewriting and optimization
  - Cache management
  - Connection pooling

#### AtScale MCP Server
- **MCP-compliant service** for AI agent integration
- **Status:** Available as containerized service
- **Capabilities:**
  - Natural language query support
  - Semantic model metadata exposure
  - Business context delivery to LLMs
  - SQL generation from natural language
  - Query result formatting

#### AtScale Data Connections
- **JDBC-based connectivity** to enterprise data sources
- **AWS Integrations:**
  - Amazon Redshift (native connector)
  - Amazon Aurora (PostgreSQL/MySQL)
  - Amazon Athena (via JDBC)
  - Amazon S3 (via Redshift Spectrum/Athena)
  - Other AWS databases (RDS, DocumentDB via JDBC)

### 3.3 Foundation Model Layer

#### Amazon Bedrock
- **Managed service** providing access to multiple foundation models
- **Recommended Model:** Anthropic Claude Sonnet 4.6
- **Capabilities:**
  - Multi-step planning
  - Schema reasoning
  - SQL generation
  - Natural language understanding
  - Tool invocation

#### Prompt Caching (Recommended)
- **Function:** Reduces input token costs for repeated prompts
- **Use Case:** Semantic model metadata reused across queries
- **Benefit:** Significant cost reduction on high-volume deployments

### 3.4 Data Source Layer

#### Amazon Redshift
- **Role:** Primary analytics data warehouse
- **AtScale Integration:**
  - Direct JDBC connection
  - Aggregate table storage
  - High-performance query pushdown
  - Redshift Spectrum for S3 access

#### Amazon Aurora (PostgreSQL/MySQL)
- **Role:** Operational database for transactional data
- **AtScale Integration:**
  - JDBC connection
  - Real-time query federation
  - Join with analytical data in Redshift

#### Amazon Athena
- **Role:** Query S3 data lake without loading
- **AtScale Integration:**
  - JDBC connection via Athena driver
  - Schema discovery from AWS Glue Data Catalog
  - Query pushdown to Athena

#### Amazon S3 (Data Lake)
- **Role:** Raw and semi-structured data storage
- **AtScale Access Patterns:**
  - Via Redshift Spectrum (external tables)
  - Via Athena (Glue catalog tables)
  - Direct S3 integration for AtScale aggregate storage



---

## 4. Implementation Approach

### 4.1 Overall Strategy

The implementation follows a **layered approach** similar to the Stardog reference architecture but adapted for AtScale's dimensional modeling paradigm.

#### Phase 1: Data Layer Setup
1. Configure AWS data sources (Redshift, Aurora, Athena)
2. Establish connectivity and security groups
3. Prepare sample data for Customer 360 use case

#### Phase 2: Semantic Layer Development
1. Deploy AtScale platform (SaaS or self-managed)
2. Create data connections to AWS sources
3. Design dimensional models (cubes)
4. Define business logic and calculations
5. Configure security and governance

#### Phase 3: AI Agent Integration
1. Deploy AtScale MCP Server
2. Configure AgentCore Gateway with MCP target
3. Build Strands Agent with tool integration
4. Deploy agent to AgentCore Runtime
5. Configure authentication and credentials

#### Phase 4: Testing and Optimization
1. Run validation queries across data sources
2. Monitor query performance
3. Review and optimize aggregate strategies
4. Validate governance policies
5. Enable prompt caching

### 4.2 Key Design Decisions

#### Decision 1: AtScale Deployment Model

**Options:**
- **AtScale Cloud (SaaS):** Managed service, 99.9% SLA, automatic updates
- **Self-managed on AWS:** Container-based on EKS/ECS, full control

**Recommendation:** Start with **AtScale Cloud** for faster time-to-value, transition to self-managed if:
- Data sources must stay within VPC
- Specific version control required
- Compliance requires on-premises control

**Rationale:** AtScale Cloud reduces operational overhead and provides faster deployment.

#### Decision 2: MCP Integration Path

**AtScale MCP Server** is the only integration path (unlike Stardog's two paths).

**Architecture:**
```
Agent → AgentCore Gateway → AtScale MCP Server → AtScale Platform → Data Sources
```

**Components:**
- AtScale MCP Server: Lightweight containerized service
- Deployment: Kubernetes, ECS, or Lambda
- Protocol: Standard MCP over HTTP/SSE
- Registration: Via AgentCore Gateway

#### Decision 3: Semantic Model Approach

**Star Schema vs. Normalized**

**Recommendation:** Use **Star Schema** (denormalized) for:
- Better query performance
- Simpler joins for AI agents
- Familiar pattern for BI teams

**Example Structure:**
```
Fact_Orders (center)
  ├── Dim_Customer (snowflaked to Dim_Location)
  ├── Dim_Product (snowflaked to Dim_Category)
  ├── Dim_Date
  └── Dim_Channel
```

#### Decision 4: Cross-Source Identity

**Challenge:** Join customers from Aurora with orders from Redshift

**Stardog Approach:** Shared IRI template
```
urn:stardog:demos:c360:customer:{cid}
```

**AtScale Approach:** Shared dimension keys
```
Customer dimension sourced from Aurora (cid as key)
Order fact table from Redshift (cid as foreign key)
```

**Key Difference:** AtScale relies on traditional foreign key relationships rather than IRI matching.

### 4.3 Migration Considerations (From Stardog)

If you're adapting an existing Stardog implementation:

#### Model Translation

| Stardog Concept | AtScale Equivalent |
|-----------------|-------------------|
| Ontology Class (`:Customer`) | Dimension (`Dim_Customer`) |
| Object Property (`:purchasedBy`) | Foreign Key Relationship |
| Datatype Property (`:firstName`) | Dimension Attribute |
| Virtual Graph | Data Connection |
| Named Graph (security) | Row-Level Security Policy |
| Reasoning Rule | Calculated Measure |
| IRI Template | Dimension Key |
| SPARQL Query | SQL/MDX Query |

#### Preserved Capabilities
✅ Federation across multiple data sources  
✅ Row-level and column-level security  
✅ Business logic centralization  
✅ Query optimization  
✅ MCP integration  

#### Lost Capabilities (vs. Stardog)
❌ Graph traversal and complex relationships  
❌ OWL reasoning and inference  
❌ RDF/Linked Data standards compliance  
❌ Triple store semantics  

#### Gained Capabilities (vs. Stardog)
✅ Familiar dimensional modeling  
✅ Automatic aggregate management  
✅ Native BI tool integration (Tableau, Power BI, Excel)  
✅ MDX support for OLAP clients  
✅ Mature enterprise-grade platform (13+ years)  



---

## 5. Technical Architecture

### 5.1 Component Interaction Flow

#### Query Flow: Natural Language to Results

```
1. User asks: "Who are our top spenders in Wisconsin?"
   │
   ▼
2. AgentCore Gateway validates JWT, routes to Runtime
   │
   ▼
3. Strands Agent (in Runtime) sends to Claude Sonnet
   │
   ▼
4. Claude identifies need for data, invokes AtScale MCP tool
   │
   ▼
5. Gateway calls AtScale MCP Server with injected credentials
   │
   ▼
6. AtScale MCP Server translates to SQL based on semantic model
   │
   ▼
7. AtScale Query Engine:
   ├─ Checks for suitable aggregate table
   ├─ If found: Query aggregate
   └─ If not: Query source(s) directly
   │
   ▼
8. Query Execution:
   ├─ Aurora query (customer profiles, addresses)
   └─ Redshift query (order totals)
   │
   ▼
9. AtScale joins results on shared customer dimension key
   │
   ▼
10. Results returned to MCP Server → Agent → User
```

### 5.2 Network Architecture

#### AtScale Cloud Deployment

```
┌─────────────────────────────────────────────────────────┐
│                    AWS Account (Customer)                │
│                                                          │
│  ┌────────────────┐         ┌────────────────┐         │
│  │ VPC            │         │ VPC            │         │
│  │                │         │                │         │
│  │  Aurora RDS    │         │  Redshift      │         │
│  │  (Private)     │         │  (Private)     │         │
│  └───────┬────────┘         └────────┬───────┘         │
│          │ Security Group            │ Security Group   │
│          │ Allow from AtScale        │ Allow from       │
│          │ Egress IPs                │ AtScale IPs      │
└──────────┼───────────────────────────┼──────────────────┘
           │                           │
           │ JDBC (TLS)                │ JDBC (TLS)
           │                           │
┌──────────▼───────────────────────────▼──────────────────┐
│              AtScale Cloud (SaaS)                        │
│                                                          │
│  ┌───────────────────────────────────────────┐         │
│  │       AtScale Semantic Layer              │         │
│  │  - Design Center                          │         │
│  │  - Query Engine                           │         │
│  │  - Data Connections                       │         │
│  │  - MCP Server                             │         │
│  └───────────────────────────────────────────┘         │
│                                                          │
└──────────────────────────┬───────────────────────────────┘
                           │ MCP/HTTPS
                           │
┌──────────────────────────▼───────────────────────────────┐
│         Amazon Bedrock AgentCore                         │
│                                                          │
│  ┌─────────────────────────────────────────┐           │
│  │   Gateway (MCP registration)            │           │
│  └─────────────────┬───────────────────────┘           │
│                    │                                     │
│  ┌─────────────────▼───────────────────────┐           │
│  │   Runtime (Strands Agent)               │           │
│  └─────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────┘
```

#### Key Networking Requirements

1. **Egress from Data Sources:**
   - Aurora/Redshift security groups must allow inbound JDBC from AtScale
   - AtScale Cloud publishes egress IP ranges
   - Add to security group allowlist

2. **AgentCore to AtScale MCP:**
   - HTTPS/SSE connection
   - AtScale MCP Server endpoint registered in Gateway
   - Credentials stored in AgentCore Identity

3. **PrivateLink Option (Enterprise):**
   - For AtScale Enterprise tier
   - VPC endpoint service
   - Traffic stays within AWS backbone

### 5.3 Data Flow Patterns

#### Pattern 1: Single-Source Query (Redshift Only)

```
User: "Top 10 products by units sold"

Agent → MCP → AtScale → Redshift
                ↓
          Aggregate table (if exists)
                OR
          Fact_Orders table
```

**AtScale Optimization:** Checks for pre-built aggregate, uses if available.

#### Pattern 2: Federated Query (Aurora + Redshift)

```
User: "Top customer spenders with their state"

Agent → MCP → AtScale
                ├─→ Aurora: Customer + Address (cid, state)
                └─→ Redshift: Orders (cid, total_spend)
                ↓
          Join on cid dimension key
                ↓
          Results merged
```

**Key Difference from Stardog:** Traditional dimension key join, not IRI matching.

#### Pattern 3: Derived Metrics

```
User: "How many big spenders per state?"

Agent → MCP → AtScale
                ↓
          Calculated Measure: "Big Spender"
          IF (Total_Spend > $10,000) THEN 1 ELSE 0
                ↓
          Federated query with calculation
                ↓
          Aggregation by state
```

**AtScale Approach:** Calculated measures in semantic model, not reasoning rules.

---

## 6. Integration Patterns

### 6.1 AtScale MCP Server Integration

#### MCP Server Architecture

```
┌─────────────────────────────────────────────────────┐
│           AtScale MCP Server                        │
│                                                     │
│  ┌──────────────────────────────────────────┐     │
│  │   MCP Protocol Handler                   │     │
│  │   - Capabilities negotiation             │     │
│  │   - Tool registration                    │     │
│  │   - Request/response handling            │     │
│  └──────────────────┬───────────────────────┘     │
│                     │                              │
│  ┌──────────────────▼───────────────────────┐     │
│  │   Semantic Model Adapter                 │     │
│  │   - Model metadata extraction            │     │
│  │   - Natural language → SQL translation   │     │
│  │   - Result formatting                    │     │
│  └──────────────────┬───────────────────────┘     │
│                     │                              │
│  ┌──────────────────▼───────────────────────┐     │
│  │   AtScale REST API Client                │     │
│  │   - Authentication                       │     │
│  │   - Query submission                     │     │
│  │   - Result retrieval                     │     │
│  └──────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

#### MCP Tools Exposed

The AtScale MCP Server exposes tools similar to Stardog's Voicebox:

1. **`atscale_ask`**
   - Input: Natural language question
   - Output: Results + SQL used + provenance
   - Example: "Show me top 10 customers by revenue"

2. **`atscale_query`**
   - Input: SQL query (for direct control)
   - Output: Result set
   - Use case: Agent writes SQL, submits directly

3. **`atscale_schema`**
   - Input: Model name (optional)
   - Output: Model metadata (dimensions, measures, hierarchies)
   - Use case: Agent understands available data

4. **`atscale_settings`**
   - Input: Configuration parameters
   - Output: Query settings confirmation
   - Use case: Set row limits, timeout, etc.

#### MCP Server Deployment

**Option 1: Container on ECS/EKS**
```bash
# Docker deployment
docker pull atscale/mcp-server:latest
docker run -d \
  -p 8080:8080 \
  -e ATSCALE_SERVER=https://yourorg.atscale.com \
  -e ATSCALE_USERNAME=service_account \
  -e ATSCALE_PASSWORD=${ATSCALE_PASSWORD} \
  atscale/mcp-server:latest
```

**Option 2: Lambda Function**
- Containerized Lambda
- Event-driven invocation
- Cost-effective for low-volume use

**Option 3: EKS with Service Mesh**
- High availability
- Built-in observability
- Traffic management

### 6.2 AgentCore Gateway Configuration

#### Register AtScale MCP Server as Tool Target

```json
{
  "toolTargetId": "atscale-mcp-server",
  "toolTargetType": "MCP_SERVER",
  "endpoint": "https://atscale-mcp.example.com",
  "authentication": {
    "type": "CREDENTIAL_PROVIDER",
    "credentialProviderId": "atscale-credentials"
  },
  "tools": [
    {
      "name": "atscale_ask",
      "description": "Query AtScale semantic layer with natural language",
      "inputSchema": {
        "type": "object",
        "properties": {
          "question": { "type": "string" },
          "model": { "type": "string" }
        },
        "required": ["question"]
      }
    },
    {
      "name": "atscale_query",
      "description": "Execute SQL query against AtScale semantic layer",
      "inputSchema": {
        "type": "object",
        "properties": {
          "sql": { "type": "string" },
          "model": { "type": "string" }
        },
        "required": ["sql"]
      }
    }
  ]
}
```

#### Credential Configuration (AgentCore Identity)

```json
{
  "credentialProviderId": "atscale-credentials",
  "credentialType": "API_KEY",
  "configuration": {
    "apiKeyLocation": "HEADER",
    "apiKeyName": "Authorization",
    "apiKeyPrefix": "Bearer",
    "secretArn": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:atscale-token"
  }
}
```

### 6.3 Agent Implementation (Strands Agent)

#### Agent Structure

```python
from strands import Agent, tool
from atscale_mcp_client import AtScaleMCPClient

# Initialize AtScale MCP client
atscale_client = AtScaleMCPClient(
    endpoint=os.environ["ATSCALE_MCP_ENDPOINT"],
    model_name="customer_360"
)

@tool
def query_semantic_layer(question: str) -> dict:
    """
    Query the AtScale semantic layer with a natural language question.
    
    Args:
        question: Natural language business question
    
    Returns:
        Dictionary with results, SQL used, and metadata
    """
    response = atscale_client.ask(question)
    return {
        "results": response.data,
        "sql": response.sql,
        "row_count": len(response.data),
        "sources": response.sources
    }

# Create agent
agent = Agent(
    name="Customer360Agent",
    model="anthropic.claude-sonnet-4-6-v1:0",
    tools=[query_semantic_layer],
    system_prompt="""
    You are a customer analytics assistant. You have access to a semantic
    layer that provides governed, consistent customer data across multiple
    systems. When answering questions:
    
    1. Use the query_semantic_layer tool to get data
    2. Interpret results in business terms
    3. Cite the data sources used
    4. Flag any limitations or assumptions
    """
)
```



---

## 7. Data Sources and Connectivity

### 7.1 Amazon Redshift Integration

#### Connection Configuration

```yaml
# AtScale Data Connection for Redshift
connection:
  name: "redshift_analytics"
  type: "REDSHIFT"
  host: "my-cluster.redshift.amazonaws.com"
  port: 5439
  database: "analytics_db"
  schema: "public"
  authentication:
    type: "IAM"  # or "PASSWORD"
    role_arn: "arn:aws:iam::ACCOUNT:role/AtScaleRedshiftAccess"
  
  # Connection pool settings
  pool:
    min_connections: 2
    max_connections: 20
    connection_timeout: 30s
    
  # SSL/TLS
  ssl:
    enabled: true
    verify_server_certificate: true
```

#### Use Cases
- **Analytics warehouse** - primary home for aggregated data
- **Aggregate storage** - AtScale stores acceleration structures here
- **External tables** - access S3 via Redshift Spectrum

#### Best Practices
1. **Use IAM authentication** for credential rotation
2. **Configure workload management (WLM)** for AtScale queries
3. **Create dedicated schema** for AtScale aggregates
4. **Enable query monitoring** for performance tuning

### 7.2 Amazon Aurora Integration

#### Connection Configuration

```yaml
# AtScale Data Connection for Aurora PostgreSQL
connection:
  name: "aurora_operational"
  type: "POSTGRESQL"  # or "MYSQL" for Aurora MySQL
  host: "my-cluster.cluster-xyz.us-east-1.rds.amazonaws.com"
  port: 5432
  database: "customer_db"
  schema: "public"
  authentication:
    type: "PASSWORD"
    username: "atscale_reader"
    password_secret: "arn:aws:secretsmanager:..."
  
  # Read replica configuration
  read_replicas:
    enabled: true
    endpoints:
      - "replica1.cluster-xyz.us-east-1.rds.amazonaws.com"
      - "replica2.cluster-xyz.us-east-1.rds.amazonaws.com"
    
  # Connection pool
  pool:
    min_connections: 1
    max_connections: 10
```

#### Use Cases
- **Operational data** - customer profiles, addresses, accounts
- **Real-time joins** - combine with Redshift analytics
- **Transactional queries** - low-latency lookups

#### Best Practices
1. **Use read replicas** to avoid impacting production workload
2. **Create read-only user** with minimal permissions
3. **Index dimension keys** (e.g., customer_id) for join performance
4. **Consider Aurora Global Database** for multi-region

### 7.3 Amazon Athena Integration

#### Connection Configuration

```yaml
# AtScale Data Connection for Athena
connection:
  name: "athena_datalake"
  type: "ATHENA"
  region: "us-east-1"
  workgroup: "atscale_workgroup"
  catalog: "AwsDataCatalog"
  database: "datalake_db"
  
  # S3 staging location
  s3_staging_dir: "s3://my-bucket/athena-results/"
  
  # Authentication
  authentication:
    type: "IAM"
    role_arn: "arn:aws:iam::ACCOUNT:role/AtScaleAthenaAccess"
  
  # Query settings
  query:
    output_encryption: "SSE_S3"
    query_queue_timeout: 300
```

#### Use Cases
- **Data lake queries** - access raw/semi-structured data in S3
- **Infrequent access** - ad-hoc analysis of historical data
- **Schema-on-read** - flexible data exploration

#### Best Practices
1. **Use partitioning** in Glue catalog for performance
2. **Convert to columnar formats** (Parquet/ORC) for cost efficiency
3. **Set query limits** to control costs
4. **Use workgroups** for governance and cost tracking

### 7.4 Redshift Spectrum for S3 Access

#### Configuration Pattern

```sql
-- In Redshift: Create external schema
CREATE EXTERNAL SCHEMA spectrum_datalake
FROM DATA CATALOG
DATABASE 'datalake_db'
IAM_ROLE 'arn:aws:iam::ACCOUNT:role/RedshiftSpectrumRole'
CREATE EXTERNAL DATABASE IF NOT EXISTS;

-- Create external table pointing to S3
CREATE EXTERNAL TABLE spectrum_datalake.customer_events (
    event_id VARCHAR(50),
    customer_id VARCHAR(50),
    event_type VARCHAR(50),
    event_timestamp TIMESTAMP,
    event_data VARCHAR(MAX)
)
STORED AS PARQUET
LOCATION 's3://my-bucket/customer-events/';
```

#### AtScale Configuration

```yaml
# Reference the Redshift connection
# Spectrum tables appear as regular tables
connection: "redshift_analytics"
table: "spectrum_datalake.customer_events"
type: "EXTERNAL"
```

#### Advantages
- **Query S3 without loading** - save time and storage
- **Join with Redshift tables** - combine lake and warehouse
- **Unified interface** - one AtScale connection for both

---

## 8. Security and Governance

### 8.1 Row-Level Security (RLS)

#### Comparison: Stardog vs. AtScale

**Stardog Approach: Named Graph Security**
```sparql
-- HR user sees all data
GRAPH <aurora_c360_pii>
GRAPH <aurora_c360_safe>

-- Marketing user only sees safe data
GRAPH <aurora_c360_safe>
```

**AtScale Approach: Row-Level Security Policies**

```yaml
# In AtScale Design Center
row_security:
  policies:
    - name: "regional_access"
      dimension: "Dim_Customer"
      filter_expression: "[Dim_Customer].[Region] = SESSION('user_region')"
      applies_to:
        - "marketing_role"
        - "sales_role"
    
    - name: "pii_access"
      dimension: "Dim_Customer"
      exclude_attributes:
        - "ssn"
        - "credit_card_number"
      applies_to:
        - "marketing_role"
      
    - name: "full_access"
      dimension: "Dim_Customer"
      applies_to:
        - "hr_role"
        - "fraud_role"
```

#### Implementation Example

```sql
-- AtScale translates queries based on user role

-- Marketing user query:
SELECT customer_name, state, total_spend
FROM customer_360

-- Becomes (with RLS applied):
SELECT customer_name, state, total_spend
FROM customer_360
WHERE region = 'North America'  -- Added by RLS
  AND customer_name IS NOT NULL  -- PII excluded
```

### 8.2 Column-Level Security

#### Sensitive Attribute Masking

```yaml
# In AtScale Design Center
column_security:
  attributes:
    - name: "SSN"
      dimension: "Dim_Customer"
      masking_rule:
        type: "REDACT"
        show_last_n: 4
        replacement: "XXX-XX-"
      visible_to:
        - "hr_role"
        - "compliance_role"
    
    - name: "Credit_Card"
      dimension: "Dim_Customer"
      masking_rule:
        type: "HASH"
        algorithm: "SHA256"
      visible_to:
        - "finance_role"
```

#### Result Example

**HR User (full access):**
```
SSN: 123-45-6789
```

**Marketing User (masked):**
```
SSN: XXX-XX-6789
```

**Unauthorized User:**
```
SSN: [REDACTED]
```

### 8.3 Authentication and Authorization

#### Multi-Layer Auth Model

```
1. Client → AgentCore Gateway
   │
   ├─ JWT validation (IdP: Okta, Azure AD, Cognito)
   └─ User identity extracted
   
2. Gateway → AtScale MCP Server
   │
   ├─ Service account credential (from AgentCore Identity)
   └─ User context passed in header
   
3. AtScale MCP Server → AtScale Platform
   │
   ├─ User impersonation (if supported)
   └─ Apply user's role-based policies
   
4. AtScale → Data Sources
   │
   ├─ Service account credentials
   └─ Query rewritten with security filters
```

#### Configuration

**AgentCore Identity (Service Account):**
```json
{
  "secretArn": "arn:aws:secretsmanager:...:atscale-service-token",
  "secretValue": {
    "username": "agentcore_service",
    "token": "eyJ..."
  }
}
```

**AtScale User Mapping:**
```yaml
# Map IdP users to AtScale roles
user_mapping:
  - idp_group: "marketing@company.com"
    atscale_role: "marketing_role"
  
  - idp_group: "hr@company.com"
    atscale_role: "hr_role"
  
  - idp_group: "data-science@company.com"
    atscale_role: "analyst_role"
```

### 8.4 Audit and Compliance

#### Query Auditing

AtScale logs all queries with:
- User identity
- Query text
- Data sources accessed
- Results row count
- Execution time
- Security policies applied

```json
{
  "timestamp": "2026-07-13T12:34:56Z",
  "user": "jsmith@company.com",
  "role": "marketing_role",
  "query": "SELECT customer_name, total_spend FROM customer_360",
  "model": "C360_Model",
  "sources": ["redshift_analytics", "aurora_operational"],
  "rls_applied": ["regional_access", "pii_access"],
  "rows_returned": 1247,
  "execution_time_ms": 850,
  "from_aggregate": true
}
```

#### Compliance Features

**GDPR / Privacy Compliance:**
- Right to erasure: Refresh AtScale connections to reflect deleted data
- Data minimization: Column-level security
- Purpose limitation: Role-based access
- Audit trail: Complete query history

**SOC 2 / Enterprise:**
- Encryption in transit (TLS 1.2+)
- Encryption at rest (source-dependent)
- Access logging
- Change management (model versioning)



---

## 9. Deployment Options

### 9.1 AtScale Cloud (SaaS) - RECOMMENDED

#### Characteristics
- **Managed by AtScale**
- SOC 2 Type II certified
- 99.9% SLA
- Automatic updates and patches
- Global availability

#### Architecture
```
┌──────────────────────────────────────────┐
│         AtScale Cloud (Multi-tenant)      │
│                                          │
│  Your Org Workspace                      │
│  ├─ Design Center                        │
│  ├─ Query Engine                         │
│  ├─ Data Connections (to your AWS)      │
│  └─ MCP Server endpoint                  │
│                                          │
│  Security: Isolated by organization      │
│  Data: Never stored, query-time only     │
└──────────────────────────────────────────┘
```

#### Connectivity Requirements
- Outbound JDBC from your VPC
- Add AtScale egress IPs to security groups
- Optional: PrivateLink for Enterprise tier

#### Pricing Tiers
1. **Free Tier**: Single user, limited data sources
2. **Essentials**: Team collaboration, more connections
3. **Enterprise**: PrivateLink, SLA, advanced security

#### When to Choose
✅ Want fastest time to deployment  
✅ Don't want to manage infrastructure  
✅ Data sources accessible via JDBC  
✅ Standard compliance requirements (SOC 2, GDPR)  

### 9.2 Self-Managed on AWS

#### Deployment Options

**Option A: Amazon EKS (Kubernetes)**

```yaml
# Helm values for AtScale on EKS
replicaCount: 3
image:
  repository: atscale/atscale-engine
  tag: "2024.1.0"

resources:
  limits:
    cpu: 4000m
    memory: 16Gi
  requests:
    cpu: 2000m
    memory: 8Gi

persistence:
  enabled: true
  storageClass: "gp3"
  size: 100Gi

ingress:
  enabled: true
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internal
  hosts:
    - host: atscale.internal.company.com
```

**Option B: Amazon ECS (Fargate)**

```json
{
  "family": "atscale-engine",
  "cpu": "4096",
  "memory": "16384",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "atscale-engine",
      "image": "atscale/atscale-engine:2024.1.0",
      "portMappings": [
        {
          "containerPort": 10500,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ATSCALE_LICENSE_KEY",
          "value": "..."
        }
      ],
      "secrets": [
        {
          "name": "DB_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:..."
        }
      ]
    }
  ]
}
```

#### Infrastructure Components

```
┌──────────────────────────────────────────────────────┐
│              AWS Account (Your VPC)                   │
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  Application Subnet                          │    │
│  │                                              │    │
│  │  ┌──────────────────────────────────┐       │    │
│  │  │   EKS/ECS (AtScale Services)     │       │    │
│  │  │   - Engine (3+ replicas)         │       │    │
│  │  │   - Design Center                │       │    │
│  │  │   - MCP Server                   │       │    │
│  │  └──────────────────────────────────┘       │    │
│  │                                              │    │
│  │  ┌──────────────────────────────────┐       │    │
│  │  │   Application Load Balancer      │       │    │
│  │  └──────────────────────────────────┘       │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  Data Subnet                                 │    │
│  │                                              │    │
│  │  ┌──────────────────────────────────┐       │    │
│  │  │   RDS PostgreSQL                 │       │    │
│  │  │   (AtScale metadata)             │       │    │
│  │  └──────────────────────────────────┘       │    │
│  │                                              │    │
│  │  ┌──────────────────────────────────┐       │    │
│  │  │   Aurora / Redshift              │       │    │
│  │  │   (Your data sources)            │       │    │
│  │  └──────────────────────────────────┘       │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  ElastiCache Redis                           │    │
│  │  (AtScale query cache)                       │    │
│  └─────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────┘
```

#### When to Choose Self-Managed
✅ Data must stay within VPC (compliance)  
✅ Need specific version control  
✅ Custom network topology  
✅ Integration with internal tools  
❌ Have Kubernetes/container expertise  

### 9.3 Hybrid Approach

**AtScale Cloud + PrivateLink**

```
Your VPC                    AWS PrivateLink         AtScale Cloud
┌────────────┐             ┌─────────────┐         ┌─────────────┐
│  Redshift  │────────────▶│  Endpoint   │────────▶│  AtScale    │
│  Aurora    │             │  Service    │         │  Platform   │
└────────────┘             └─────────────┘         └─────────────┘
                          (No Internet egress)
```

**Benefits:**
- Managed service convenience
- Data never leaves AWS backbone
- Enhanced security posture
- Lower egress costs

---

## 10. Step-by-Step Implementation

### Phase 1: AWS Data Layer Setup

#### Step 1.1: Prepare Amazon Redshift

```sql
-- Create schema for AtScale aggregates
CREATE SCHEMA atscale_agg;

-- Grant permissions to AtScale service account
CREATE USER atscale_service WITH PASSWORD 'secure_password';

GRANT USAGE ON SCHEMA public TO atscale_service;
GRANT USAGE ON SCHEMA atscale_agg TO atscale_service;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO atscale_service;
GRANT ALL ON SCHEMA atscale_agg TO atscale_service;
GRANT ALL ON ALL TABLES IN SCHEMA atscale_agg TO atscale_service;

-- Enable automatic granting for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT ON TABLES TO atscale_service;
```

#### Step 1.2: Prepare Amazon Aurora

```sql
-- Create read-only user for AtScale
CREATE USER atscale_reader WITH PASSWORD 'secure_password';

-- Grant read permissions
GRANT CONNECT ON DATABASE customer_db TO atscale_reader;
GRANT USAGE ON SCHEMA public TO atscale_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO atscale_reader;

-- For future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT ON TABLES TO atscale_reader;

-- Create indexes on join keys for performance
CREATE INDEX idx_customer_id ON customers(customer_id);
CREATE INDEX idx_customer_location ON addresses(customer_id);
```

#### Step 1.3: Configure Security Groups

```bash
# Redshift security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-redshift \
  --protocol tcp \
  --port 5439 \
  --cidr 52.1.1.0/24  # AtScale egress IP range

# Aurora security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-aurora \
  --protocol tcp \
  --port 5432 \
  --cidr 52.1.1.0/24  # AtScale egress IP range
```

#### Step 1.4: Create Sample Data (Customer 360)

```sql
-- In Aurora (operational DB)
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(200),
    ssn VARCHAR(11),  -- Sensitive
    phone VARCHAR(20),
    created_date DATE
);

CREATE TABLE addresses (
    address_id INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    street VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10)
);

-- In Redshift (analytics DW)
CREATE TABLE orders (
    order_id INTEGER,
    customer_id INTEGER,
    product_id INTEGER,
    order_date DATE,
    quantity INTEGER,
    unit_price DECIMAL(10,2),
    total_amount DECIMAL(10,2)
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name VARCHAR(200),
    category VARCHAR(100),
    brand VARCHAR(100)
);
```

### Phase 2: AtScale Semantic Layer Setup

#### Step 2.1: Sign Up for AtScale Cloud

1. Go to https://www.atscale.com/free-trial
2. Create account (free tier available)
3. Verify email
4. Log into Design Center

#### Step 2.2: Create Data Connections

**Redshift Connection:**
```yaml
# In AtScale Design Center UI
Name: redshift_analytics
Type: Amazon Redshift
Host: my-cluster.redshift.amazonaws.com
Port: 5439
Database: analytics_db
Username: atscale_service
Password: [from secrets manager]
Schema: public
Aggregate Schema: atscale_agg
```

**Aurora Connection:**
```yaml
# In AtScale Design Center UI
Name: aurora_operational
Type: PostgreSQL
Host: my-cluster.cluster-xyz.us-east-1.rds.amazonaws.com
Port: 5432
Database: customer_db
Username: atscale_reader
Password: [from secrets manager]
Schema: public
```

#### Step 2.3: Create Semantic Model (Customer 360)

**Model Structure:**

```
Customer_360_Model
│
├── Dimensions
│   ├── Dim_Customer (from Aurora)
│   │   ├── customer_id (key)
│   │   ├── first_name
│   │   ├── last_name
│   │   ├── email
│   │   ├── ssn (marked sensitive)
│   │   └── phone
│   │
│   ├── Dim_Location (from Aurora, snowflaked)
│   │   ├── address_id (key)
│   │   ├── city
│   │   ├── state
│   │   └── zip_code
│   │
│   ├── Dim_Product (from Redshift)
│   │   ├── product_id (key)
│   │   ├── product_name
│   │   ├── category
│   │   └── brand
│   │
│   └── Dim_Date (generated)
│       ├── date_key
│       ├── year
│       ├── quarter
│       └── month
│
└── Fact Tables
    └── Fact_Orders (from Redshift)
        ├── order_id
        ├── customer_id (FK to Dim_Customer)
        ├── product_id (FK to Dim_Product)
        ├── order_date (FK to Dim_Date)
        ├── quantity
        └── total_amount
```

**In AtScale Design Center:**

1. **Create Model:** Click "New Model" → "Customer_360"

2. **Add Customer Dimension:**
   - Source: aurora_operational
   - Table: customers
   - Key: customer_id
   - Attributes: first_name, last_name, email, phone
   - Security: Mark ssn as "Sensitive"

3. **Add Location Dimension (Snowflaked):**
   - Source: aurora_operational
   - Table: addresses
   - Key: address_id
   - Relationship: Many-to-One with Dim_Customer (customer_id)

4. **Add Product Dimension:**
   - Source: redshift_analytics
   - Table: products
   - Key: product_id

5. **Add Fact Table:**
   - Source: redshift_analytics
   - Table: orders
   - Relationships:
     - customer_id → Dim_Customer
     - product_id → Dim_Product

6. **Create Calculated Measures:**

```javascript
// Total Revenue
SUM([Fact_Orders].[total_amount])

// Average Order Value
SUM([Fact_Orders].[total_amount]) / COUNT([Fact_Orders].[order_id])

// Big Spender (Derived Dimension)
IF (SUM([Fact_Orders].[total_amount]) > 10000, "Yes", "No")

// Customer Lifetime Value
SUM([Fact_Orders].[total_amount]) OVER (PARTITION BY [Dim_Customer].[customer_id])
```

7. **Publish Model**

#### Step 2.4: Configure Security Policies

```yaml
# In AtScale Design Center → Security

# Policy 1: Regional Access
row_level_security:
  - name: "regional_filter"
    dimension: "Dim_Location"
    filter: "[Dim_Location].[state] IN ('CA', 'OR', 'WA')"
    roles: ["west_coast_sales"]

# Policy 2: PII Protection
column_level_security:
  - attribute: "Dim_Customer.ssn"
    masking: "redact_all_but_last_4"
    visible_to: ["hr_role", "compliance_role"]

# Policy 3: Full Access
access_policy:
  - role: "admin_role"
    permissions: "full_access"
```



### Phase 3: AI Agent Integration

#### Step 3.1: Deploy AtScale MCP Server

**Using Docker on ECS:**

```bash
# 1. Build or pull AtScale MCP Server image
docker pull atscale/mcp-server:latest

# 2. Create ECS task definition
aws ecs register-task-definition --cli-input-json file://atscale-mcp-task.json

# atscale-mcp-task.json
{
  "family": "atscale-mcp-server",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "mcp-server",
      "image": "atscale/mcp-server:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ATSCALE_SERVER",
          "value": "https://yourorg.atscale.com"
        },
        {
          "name": "ATSCALE_MODEL",
          "value": "Customer_360"
        }
      ],
      "secrets": [
        {
          "name": "ATSCALE_TOKEN",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:atscale-token"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/atscale-mcp",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "mcp"
        }
      }
    }
  ]
}

# 3. Create ECS service
aws ecs create-service \
  --cluster my-cluster \
  --service-name atscale-mcp-server \
  --task-definition atscale-mcp-server \
  --desired-count 2 \
  --launch-type FARGATE \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=mcp-server,containerPort=8080
```

#### Step 3.2: Store AtScale Credentials in AgentCore Identity

```bash
# 1. Create secret in Secrets Manager
aws secretsmanager create-secret \
  --name atscale-api-token \
  --description "AtScale API token for AgentCore" \
  --secret-string '{"token":"eyJhbGc..."}'

# 2. Configure AgentCore Identity credential provider
aws bedrock-agent create-credential-provider \
  --credential-provider-id atscale-credentials \
  --credential-type API_TOKEN \
  --secret-arn arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:atscale-api-token
```

#### Step 3.3: Register MCP Server in AgentCore Gateway

```python
import boto3

bedrock_agent = boto3.client('bedrock-agent')

response = bedrock_agent.register_tool_target(
    toolTargetId='atscale-mcp-server',
    toolTargetType='MCP_SERVER',
    configuration={
        'mcpServer': {
            'endpoint': 'https://atscale-mcp.example.com',
            'transport': 'SSE',
            'authentication': {
                'type': 'CREDENTIAL_PROVIDER',
                'credentialProviderId': 'atscale-credentials'
            }
        }
    },
    tools=[
        {
            'name': 'atscale_ask',
            'description': 'Query the Customer 360 semantic layer with natural language. Returns customer data with business context and governance applied.',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'question': {
                        'type': 'string',
                        'description': 'Natural language business question about customers, orders, or products'
                    }
                },
                'required': ['question']
            }
        },
        {
            'name': 'atscale_query',
            'description': 'Execute a SQL query against the Customer 360 semantic layer',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'sql': {
                        'type': 'string',
                        'description': 'SQL query using semantic model dimensions and measures'
                    }
                },
                'required': ['sql']
            }
        },
        {
            'name': 'atscale_schema',
            'description': 'Get metadata about the Customer 360 semantic model including available dimensions, measures, and hierarchies',
            'inputSchema': {
                'type': 'object',
                'properties': {}
            }
        }
    ]
)
```

#### Step 3.4: Build and Deploy Strands Agent

**Agent Code (`c360_agent.py`):**

```python
from strands import Agent, tool
import os
import json

# System prompt with semantic model context
SYSTEM_PROMPT = """
You are a Customer 360 Analytics Assistant. You help business users answer 
questions about customers, orders, and products using a governed semantic layer.

## Available Data

**Dimensions:**
- Customer: customer_id, first_name, last_name, email, phone, state
- Location: city, state, zip_code
- Product: product_id, product_name, category, brand
- Date: year, quarter, month, day

**Measures:**
- Total Revenue: Sum of order amounts
- Order Count: Number of orders
- Average Order Value: Revenue / Order Count
- Customer Lifetime Value: Total revenue per customer

**Derived Attributes:**
- Big Spender: Customers with >$10,000 lifetime spend

## Capabilities

1. Use atscale_ask for natural language questions
2. Use atscale_query for complex SQL when needed
3. Use atscale_schema to explore available data
4. Always cite data sources in your answers
5. Explain any business rules applied

## Security

- PII (SSN) is automatically masked for non-privileged users
- Regional filters apply based on user role
- All queries are audited
"""

@tool
def atscale_ask(question: str) -> dict:
    """
    Query the Customer 360 semantic layer with natural language.
    
    Args:
        question: Natural language business question
        
    Returns:
        Dictionary with results, SQL used, and metadata
    """
    # This tool is implemented by AgentCore Gateway
    # calling the registered MCP server
    pass

@tool
def atscale_query(sql: str) -> dict:
    """
    Execute SQL query against the semantic layer.
    
    Args:
        sql: SQL query using semantic model
        
    Returns:
        Query results
    """
    pass

@tool
def atscale_schema() -> dict:
    """
    Get semantic model metadata.
    
    Returns:
        Model structure and available elements
    """
    pass

# Create agent
agent = Agent(
    name="Customer360Agent",
    model="anthropic.claude-sonnet-4-6-v1:0",
    tools=[atscale_ask, atscale_query, atscale_schema],
    system_prompt=SYSTEM_PROMPT,
    # Enable prompt caching for cost optimization
    cache_system_prompt=True
)

# Handler for AgentCore Runtime
def handler(event, context):
    """
    Lambda/AgentCore handler for agent invocation.
    """
    user_message = event['input']['message']
    session_id = event.get('sessionId', 'default')
    
    # Invoke agent
    response = agent.run(
        message=user_message,
        session_id=session_id
    )
    
    return {
        'output': {
            'message': response.content,
            'metadata': {
                'toolsUsed': response.tool_calls,
                'sourcesSummary': response.sources
            }
        }
    }
```

**Deploy to AgentCore Runtime:**

```bash
# 1. Package agent code
zip agent.zip c360_agent.py requirements.txt

# 2. Upload to S3
aws s3 cp agent.zip s3://my-bucket/agents/c360_agent.zip

# 3. Create AgentCore Runtime application
aws bedrock-agent create-agent-runtime \
  --agent-name Customer360Agent \
  --runtime-role-arn arn:aws:iam::ACCOUNT:role/AgentRuntimeRole \
  --agent-resource-arn s3://my-bucket/agents/c360_agent.zip \
  --handler c360_agent.handler \
  --foundation-model anthropic.claude-sonnet-4-6-v1:0 \
  --prompt-caching-enabled
```

#### Step 3.5: Configure AgentCore Gateway Endpoint

```bash
# Create Gateway endpoint for agent
aws bedrock-agent create-gateway-endpoint \
  --endpoint-name customer360-agent \
  --agent-runtime-id <runtime-id-from-previous-step> \
  --authentication-config '{
    "type": "JWT",
    "jwtConfig": {
      "issuer": "https://your-idp.com",
      "audience": "customer360-agent",
      "jwksUri": "https://your-idp.com/.well-known/jwks.json"
    }
  }'
```

### Phase 4: Testing and Validation

#### Step 4.1: Test Direct Queries

**Aurora-only query:**
```bash
curl -X POST https://gateway.bedrock.aws.amazon.com/customer360-agent \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "message": "List 10 customers from California"
    }
  }'
```

**Expected flow:**
1. Agent receives question
2. Calls `atscale_ask` tool
3. MCP Server translates to SQL
4. AtScale queries Aurora only
5. Results returned with customer names and details

**Redshift-only query:**
```bash
curl -X POST https://gateway.bedrock.aws.amazon.com/customer360-agent \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "message": "What are the top 5 product categories by revenue?"
    }
  }'
```

**Expected flow:**
1. Agent calls `atscale_ask`
2. AtScale queries Redshift orders and products
3. Returns aggregated results

#### Step 4.2: Test Federated Queries

**Cross-source join:**
```bash
curl -X POST https://gateway.bedrock.aws.amazon.com/customer360-agent \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "message": "Show me the top 10 customers by total spend, with their state"
    }
  }'
```

**Expected flow:**
1. Agent calls `atscale_ask`
2. AtScale identifies need for:
   - Customer data (Aurora): customer_id, name, state
   - Order data (Redshift): customer_id, sum(total_amount)
3. Executes queries to both sources
4. Joins on customer_id dimension key
5. Returns unified results

**Verification:**
```json
{
  "output": {
    "message": "Here are the top 10 customers by total spend:\n\n1. John Smith (CA) - $45,230\n2. Jane Doe (TX) - $38,920\n...",
    "metadata": {
      "toolsUsed": ["atscale_ask"],
      "sourcesSummary": [
        "aurora_operational.customers",
        "aurora_operational.addresses",
        "redshift_analytics.orders"
      ]
    }
  }
}
```

#### Step 4.3: Test Derived Metrics

**Calculated measure query:**
```bash
curl -X POST https://gateway.bedrock.aws.amazon.com/customer360-agent \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "message": "How many big spenders do we have in each state?"
    }
  }'
```

**Expected behavior:**
- AtScale applies "Big Spender" calculation (lifetime spend > $10,000)
- Queries federated data
- Groups by state
- Returns counts per state

#### Step 4.4: Verify Security Policies

**Test PII masking:**
```bash
# As marketing user (no PII access)
curl -X POST https://gateway.bedrock.aws.amazon.com/customer360-agent \
  -H "Authorization: Bearer $MARKETING_JWT" \
  -d '{
    "input": {
      "message": "Show me customer details for customer_id 12345"
    }
  }'

# Expected: SSN field is masked (XXX-XX-6789)
```

**Test row-level security:**
```bash
# As west coast sales user
curl -X POST https://gateway.bedrock.aws.amazon.com/customer360-agent \
  -H "Authorization: Bearer $WESTCOAST_JWT" \
  -d '{
    "input": {
      "message": "List all customers"
    }
  }'

# Expected: Only CA, OR, WA customers returned
```

---

## 11. Sample Use Case: Customer 360 Analytics

### Business Scenario

**Company:** Online retailer  
**Challenge:** Customer data split between operational DB (Aurora) and analytics warehouse (Redshift)  
**Users:** Sales, Marketing, Customer Success teams  
**Goal:** Self-service analytics with AI agent

### Data Architecture

```
Aurora (Operational)              Redshift (Analytics)
┌─────────────────────┐          ┌──────────────────────┐
│ Customers           │          │ Orders               │
│ - customer_id (PK)  │          │ - order_id           │
│ - name              │          │ - customer_id        │
│ - email             │          │ - product_id         │
│ - ssn               │          │ - order_date         │
│ - phone             │          │ - total_amount       │
│                     │          │                      │
│ Addresses           │          │ Products             │
│ - address_id (PK)   │          │ - product_id (PK)    │
│ - customer_id (FK)  │          │ - product_name       │
│ - city, state, zip  │          │ - category           │
└─────────────────────┘          └──────────────────────┘
```

### Sample Questions and Flows

#### Question 1: "Who are our VIP customers in New York?"

**Agent Processing:**
```
1. Parse intent: Need customers filtered by state and VIP status
2. Call atscale_ask("Who are our VIP customers in New York?")
3. AtScale translates to semantic query
4. Identify required data:
   - Dim_Customer (Aurora): name, email
   - Dim_Location (Aurora): state
   - Fact_Orders (Redshift): total spend
5. Apply VIP logic: SUM(total_amount) > $10,000
6. Execute queries
7. Join results
8. Return answer
```

**SQL Generated by AtScale:**

```sql
-- Aurora query
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name as customer_name,
    c.email,
    a.state
FROM customers c
JOIN addresses a ON c.customer_id = a.customer_id
WHERE a.state = 'NY';

-- Redshift query
SELECT 
    customer_id,
    SUM(total_amount) as lifetime_spend
FROM orders
GROUP BY customer_id
HAVING SUM(total_amount) > 10000;

-- AtScale joins on customer_id and returns merged results
```

**Response to User:**
```
I found 47 VIP customers in New York. Here are the top 10:

1. Sarah Johnson (sjohnson@email.com) - $23,450 lifetime spend
2. Michael Chen (mchen@email.com) - $19,230 lifetime spend
3. Emily Rodriguez (erodriguez@email.com) - $17,890 lifetime spend
...

These customers have spent over $10,000 with us. Would you like me to 
export the full list or analyze their purchase patterns?

Sources: Aurora (customers, addresses), Redshift (orders)
```

#### Question 2: "What's the average order value for customers in California?"

**Agent Processing:**
```
1. Identify metrics: Average Order Value (AOV)
2. Filter: California customers
3. Call atscale_ask
4. AtScale uses calculated measure: Total Revenue / Order Count
5. Federated query with state filter
6. Return aggregated result
```

**Response:**
```
The average order value for California customers is $127.45.

This is based on:
- 15,234 orders
- $1,941,230 total revenue
- 3,892 unique customers

California customers have a 15% higher AOV compared to the national 
average of $110.80.

Sources: Aurora (addresses), Redshift (orders)
```

#### Question 3: "Show me purchase trends for electronics category over the last 6 months"

**Agent Processing:**
```
1. Identify: Time series analysis
2. Filter: Electronics category, last 6 months
3. Call atscale_ask
4. AtScale queries:
   - Redshift: orders + products
   - Date dimension for month grouping
5. Return aggregated time series
```

**Response:**
```
Electronics purchase trends (Last 6 months):

January 2026:   $145,230 (1,234 orders)
February 2026:  $132,890 (1,098 orders)
March 2026:     $167,450 (1,445 orders)
April 2026:     $189,230 (1,623 orders)
May 2026:       $201,340 (1,789 orders)
June 2026:      $223,450 (1,923 orders)

Trend: +54% growth over 6 months
Peak month: June 2026

Would you like me to break this down by specific product sub-categories 
or compare with other categories?

Sources: Redshift (orders, products)
```



---

## 12. Limitations and Considerations

### 12.1 Architectural Tradeoffs

#### AtScale vs. Stardog Comparison

| Capability | Stardog | AtScale | Impact |
|------------|---------|---------|--------|
| **Graph Relationships** | Native (RDF triples) | Via dimension relationships | Complex multi-hop queries harder in AtScale |
| **Semantic Richness** | OWL ontologies with inference | Business dimensions | Stardog more flexible for complex domains |
| **Query Language** | SPARQL (W3C standard) | SQL/MDX (industry standard) | AtScale more familiar to BI teams |
| **Reasoning** | OWL + rules (automatic inference) | Calculated measures (explicit) | Stardog can derive new facts automatically |
| **Standards Compliance** | RDF, OWL, SPARQL | Proprietary (SQL-based) | Stardog better for linked data initiatives |
| **BI Tool Integration** | Limited (via SQL endpoint) | Native (Tableau, Power BI, Excel) | AtScale better for traditional BI |
| **Learning Curve** | Steep (knowledge graphs) | Moderate (dimensional modeling) | AtScale faster adoption |
| **Query Optimization** | Graph query planning | Aggregate management | AtScale better for repetitive queries |

**When to Choose Stardog:**
- Complex domain with many-to-many relationships
- Need automatic reasoning and inference
- Linked data / semantic web initiatives
- Integration with RDF/OWL ecosystem
- Research or pharma use cases

**When to Choose AtScale:**
- Traditional analytics use cases
- Strong existing BI tool ecosystem
- Dimensional modeling mindset
- Need mature aggregate management
- Cost-conscious (well-established pricing)

### 12.2 Current Limitations (July 2026)

#### MCP Integration Status

**AtScale MCP Server:**
- ✅ Core protocol support (tools, resources)
- ✅ Natural language query translation
- ⚠️ **Beta status** - not yet GA (as of July 2026)
- ⚠️ Limited to certain AtScale Cloud tiers
- ❌ No sampling for MCP (full results only)

**AgentCore Gateway:**
- ✅ MCP server registration
- ✅ Credential injection
- ⚠️ Tool discovery may require manual schema definition
- ❌ No built-in tool versioning

**Recommendation:** Prototype with current MCP support, but plan for potential API changes.

#### Query Performance

**Factors Affecting Performance:**

1. **Cold Start (No Aggregates):**
   - First query to large dataset: 10-60 seconds
   - AtScale must query sources directly
   - Solution: Pre-build aggregates for common queries

2. **Federated Joins:**
   - Join across Aurora + Redshift adds overhead
   - Network latency between sources
   - Solution: Co-locate frequently joined data when possible

3. **Real-time Data:**
   - AtScale caches metadata and aggregates
   - Fresh data may require cache refresh
   - Solution: Configure appropriate TTL based on data freshness needs

**Performance Tuning:**
- Enable AtScale aggregate recommendations
- Pre-build aggregates for top agent queries
- Monitor query logs and optimize slow queries
- Consider materialized views in source systems

### 12.3 Cost Considerations

#### AtScale Licensing

**Pricing Model:**
- Free tier: Limited (1 user, 2 data sources)
- Essentials: ~$10K-$30K/year
- Enterprise: ~$50K-$150K/year (varies by data volume)

**Cost Drivers:**
- Number of users
- Data volume queried
- Number of data sources
- Support level
- Deployment model (Cloud vs. self-managed)

#### AWS Costs

**AgentCore:**
- Gateway: ~$0.50 per 1K requests
- Runtime: ~$0.002 per second of execution
- Identity: ~$0.50 per 10K credential retrievals

**Bedrock (Claude Sonnet 4.6):**
- Input tokens: ~$3 per 1M tokens
- Output tokens: ~$15 per 1M tokens
- Prompt caching: ~$0.90 per 1M cached tokens (significant savings)

**Data Transfer:**
- Aurora → AtScale: Egress charges if different region
- Redshift → AtScale: Same region recommended
- AtScale Cloud → AgentCore: Internet egress

**Optimization Strategies:**
1. **Enable prompt caching** - semantic model metadata reused
2. **Use aggregate tables** - reduce source query cost
3. **Co-locate services** - minimize egress
4. **Set query limits** - prevent runaway costs

### 12.4 Operational Considerations

#### Monitoring and Observability

**What to Monitor:**

```yaml
atscale_metrics:
  - query_count_per_minute
  - query_latency_p50_p95_p99
  - aggregate_hit_rate
  - connection_pool_usage
  - cache_hit_rate
  - failed_query_rate

agent_metrics:
  - invocation_count
  - tool_call_success_rate
  - average_response_time
  - error_rate_by_type
  - cost_per_query

data_source_metrics:
  - aurora_connection_count
  - redshift_queue_time
  - query_pushdown_success_rate
```

**Monitoring Tools:**
- **AtScale:** Built-in query monitoring dashboard
- **AgentCore:** CloudWatch metrics and logs
- **Custom:** Grafana dashboards for end-to-end visibility

#### Maintenance Tasks

**Regular (Weekly/Monthly):**
- Review AtScale aggregate recommendations
- Analyze slow queries and optimize
- Monitor security policy effectiveness
- Check for failed data connections
- Review agent conversation quality

**Periodic (Quarterly):**
- Update semantic models for new data sources
- Refresh user/role mappings
- Audit security policies
- Review cost optimization opportunities
- Update agent prompts based on user feedback

**Ad-hoc:**
- Add new dimensions/measures as needed
- Onboard new users and roles
- Respond to security incidents
- Troubleshoot query failures

### 12.5 Security Best Practices

#### Defense in Depth

**Layer 1: Network Security**
- VPC isolation for data sources
- Security group restrictions (least privilege)
- TLS 1.2+ for all connections
- Private endpoints where possible

**Layer 2: Authentication**
- JWT validation at Gateway
- Service account credentials in Secrets Manager
- Rotate credentials regularly (90 days)
- MFA for administrative access

**Layer 3: Authorization**
- Role-based access in AtScale
- Row-level security policies
- Column-level masking for PII
- Audit all queries

**Layer 4: Data Protection**
- Encryption at rest (source-dependent)
- Encryption in transit (TLS)
- No data stored in AtScale (query-time only)
- MCP Server stateless design

**Layer 5: Compliance**
- Regular access reviews
- Query audit logs retained
- SOC 2 compliance (AtScale Cloud)
- GDPR data minimization

---

## 13. Conclusion and Recommendations

### Summary

This research provides a comprehensive guide for implementing a **semantic layer using AtScale and AWS AI services** as an alternative to the Stardog-based reference architecture. The key findings:

1. **AtScale provides equivalent semantic layer capabilities** using familiar dimensional modeling instead of knowledge graphs

2. **MCP integration** enables seamless connection to Amazon Bedrock AgentCore, similar to Stardog's Voicebox

3. **Architecture pattern translates well** from Stardog to AtScale with some adjustments for dimensional vs. graph paradigms

4. **Data federation works similarly** - both systems query sources at runtime without ETL

5. **Security and governance** capabilities are comparable with different implementation approaches

### Recommended Approach

#### For New Implementations

**Start with AtScale if:**
- Team has BI/data warehouse background
- Need strong BI tool integration
- Traditional analytics use cases
- Cost predictability important
- Faster time-to-value needed

**Start with Stardog if:**
- Complex domain with graph-like relationships
- Need semantic web standards compliance
- Advanced reasoning requirements
- Research/scientific use cases
- Graph database expertise available

#### Migration Path (Proof of Concept)

**Phase 1: Quick Win (2-4 weeks)**
1. Set up AtScale Cloud free tier
2. Connect to one AWS data source (Redshift)
3. Create simple semantic model (3-5 dimensions)
4. Deploy basic agent on AgentCore
5. Test with 5-10 sample questions

**Phase 2: Production Pilot (4-8 weeks)**
1. Add second data source (Aurora)
2. Implement federated queries
3. Configure security policies
4. Deploy AtScale MCP Server
5. Onboard 10-20 pilot users
6. Measure performance and cost

**Phase 3: Scale (8-12 weeks)**
1. Expand semantic models
2. Add remaining data sources
3. Optimize aggregates
4. Deploy to all users
5. Integrate with existing BI tools
6. Establish monitoring and governance

### Key Success Factors

1. **Executive Sponsorship:** Semantic layer requires cross-functional buy-in
2. **Data Governance:** Establish clear ownership of business definitions
3. **Iterative Approach:** Start small, learn, expand
4. **User Training:** Both agent users and semantic modelers need training
5. **Performance Monitoring:** Track query patterns and optimize continuously

### Next Steps

1. **Review with stakeholders:** Architecture, use cases, timeline
2. **Provision AWS accounts:** Separate dev/test/prod environments
3. **Sign up for AtScale:** Free tier for initial testing
4. **Set up data sources:** Aurora, Redshift with sample data
5. **Build first model:** Customer 360 or similar use case
6. **Deploy agent:** AgentCore Runtime with MCP integration
7. **Test and iterate:** Gather feedback, optimize, expand

### Additional Resources

**AtScale Documentation:**
- Product Documentation: https://documentation.atscale.com
- MCP Integration Guide: https://www.atscale.com/explore/interactive-demos/mcp-integration
- AWS Integration: https://www.atscale.com/integrations/atscale-and-amazon

**AWS Resources:**
- Amazon Bedrock AgentCore: https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html
- Model Context Protocol: https://github.com/modelcontextprotocol
- Strands Agents: https://github.com/strands-agents

**Reference Implementations:**
- Stardog blog post: https://aws.amazon.com/blogs/machine-learning/build-a-semantic-layer-for-agentic-ai-on-aws-with-stardog-and-amazon-bedrock-agentcore/
- AWS Samples: https://github.com/aws-samples/sample-semantic-layer-using-agents

---

## Appendix A: Glossary

**Semantic Layer:** An abstraction layer that provides a business-friendly view of data, centralizing definitions, relationships, and calculations.

**Model Context Protocol (MCP):** Open standard for connecting AI agents to data sources and tools.

**AgentCore:** AWS managed service for building, deploying, and operating AI agents.

**AtScale:** Universal semantic layer platform for BI and ML on cloud data platforms.

**Dimensional Model:** Star/snowflake schema approach to organizing data with facts and dimensions.

**Knowledge Graph:** Graph-structured knowledge base using semantic web standards (RDF, OWL, SPARQL).

**Virtual Graph (Stardog):** Mapping from ontology to relational data source.

**Aggregate Table:** Pre-computed summary table for query acceleration.

**Row-Level Security (RLS):** Security policy that filters data based on user attributes.

**Federation:** Querying multiple data sources as if they were one unified system.

---

## Appendix B: Comparison Matrix

### Feature Comparison: Stardog vs. AtScale

| Feature Category | Stardog | AtScale | Notes |
|------------------|---------|---------|-------|
| **Data Modeling** | | | |
| Modeling Paradigm | Knowledge Graph (RDF) | Dimensional (Star/Snowflake) | Different mental models |
| Modeling Tool | Stardog Designer | AtScale Design Center | Both visual, different concepts |
| Relationships | Object Properties (RDF) | Foreign Keys | Stardog more flexible |
| Inheritance | OWL class hierarchy | Dimension hierarchies | Stardog supports inference |
| **Query & Access** | | | |
| Query Language | SPARQL | SQL, MDX, DAX, REST, Python | AtScale more versatile |
| Natural Language | Voicebox (MCP) | AtScale MCP Server | Similar via MCP |
| BI Tool Support | Limited (SQL endpoint) | Native connectors | AtScale stronger |
| API Access | REST + SPARQL | REST + JDBC/ODBC | AtScale more standard |
| **Performance** | | | |
| Query Optimization | Graph query planning | Aggregate management | Different approaches |
| Caching | Query result cache | Multi-layer cache + aggregates | AtScale more sophisticated |
| Parallel Processing | Yes | Yes | Both support |
| **Security** | | | |
| Row-Level Security | Named graph security | RLS policies | Both effective |
| Column Security | Property masking | Attribute masking | Similar capabilities |
| Audit Logging | Complete | Complete | Both comprehensive |
| **Data Sources** | | | |
| AWS Support | Redshift, Aurora, Athena | Redshift, Aurora, Athena, more | AtScale broader |
| Federation | Virtual graphs | Live connections | Both query-time |
| Data Movement | None (virtual) | None (virtual) | Both leave data in place |
| **AI Integration** | | | |
| MCP Support | Yes (Voicebox) | Yes (MCP Server) | Both support |
| AgentCore Ready | Yes | Yes | Both work with AgentCore |
| LLM Integration | Direct + MCP | MCP only | Stardog more options |
| **Enterprise** | | | |
| Maturity | ~10 years | ~13 years | Both proven |
| Deployment | Cloud, On-prem, Hybrid | Cloud, Self-managed | Similar options |
| Pricing | ~$50K-$200K+ | ~$30K-$150K+ | Varies widely |
| Support | 24/7 available | 24/7 available | Both enterprise-grade |

---

## Document Metadata

**Author:** Research conducted on July 13, 2026  
**Version:** 1.0  
**Last Updated:** July 13, 2026  
**Target Audience:** Solution Architects, Data Engineers, AI/ML Engineers  
**Estimated Reading Time:** 60 minutes  
**Implementation Time:** 4-12 weeks (varies by scope)

---

**END OF DOCUMENT**
