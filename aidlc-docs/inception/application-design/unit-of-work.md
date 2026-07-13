# Units of Work

## Decomposition Strategy

**Approach:** Sequential units aligned with deployment dependencies  
**Rationale:** Each unit must complete before the next can begin (strict dependency chain)  
**Team Model:** Single developer (POC)

---

## Unit 1: Infrastructure

### Definition
| Field | Value |
|-------|-------|
| **Name** | Infrastructure |
| **Type** | Infrastructure-as-Code |
| **Technology** | AWS CDK (Python) |
| **Scope** | All AWS resources required by the system |
| **Output** | Deployed VPC, EKS, Aurora, Redshift, S3, IAM |

### Responsibilities
- VPC with public/private subnets across 2 AZs
- EKS cluster with managed node group (m5.2xlarge × 2-4)
- Aurora PostgreSQL 15.x (db.r6g.large, single writer)
- Redshift Serverless (8 RPU)
- S3 bucket for data staging and AtScale aggregates
- IAM roles for EKS, Redshift COPY, Bedrock access, AtScale
- Security groups for all cross-component communication
- Secrets Manager entries for database credentials
- EKS add-ons: EBS CSI driver, ALB Ingress Controller

### Code Organization
```
infrastructure/
├── app.py                    # CDK app entry point
├── cdk.json                  # CDK configuration
├── requirements.txt          # Python dependencies
├── stacks/
│   ├── __init__.py
│   ├── networking_stack.py   # VPC, subnets, SGs, NAT
│   ├── storage_stack.py      # S3 bucket
│   ├── database_stack.py     # Aurora, Redshift
│   ├── eks_stack.py          # EKS cluster, node groups
│   └── iam_stack.py          # Roles, policies
└── tests/
    └── test_stacks.py        # CDK assertion tests
```

### Acceptance Criteria
- [ ] `cdk deploy --all` completes without errors
- [ ] VPC created with correct CIDR (10.1.0.0/16)
- [ ] EKS cluster is ACTIVE, kubectl connects
- [ ] Aurora writer endpoint accessible from EKS nodes
- [ ] Redshift serverless endpoint accessible from EKS nodes
- [ ] S3 bucket created with correct name
- [ ] All security groups have correct inbound rules

---

## Unit 2: Data Layer

### Definition
| Field | Value |
|-------|-------|
| **Name** | Data Layer |
| **Type** | Data pipeline scripts |
| **Technology** | Python (psycopg2, boto3) |
| **Scope** | Download, transform, load C360 data |
| **Output** | Populated Aurora + Redshift tables |

### Responsibilities
- Download CSV files from Stardog C360 GitHub repository
- Create DDL schemas in Aurora (customer, address, credit_card, rewards_account)
- Create DDL schemas in Redshift (purchase, product, category, vendor)
- Upload CSVs to S3 staging bucket
- Load data into Aurora via psycopg2 COPY
- Load data into Redshift via COPY FROM S3
- Validate row counts and data integrity
- Create indexes on join keys

### Code Organization
```
data/
├── csv/                       # Downloaded CSV files (gitignored)
├── scripts/
│   ├── download_data.py       # Fetch CSVs from GitHub
│   ├── aurora_ddl.sql         # Aurora schema DDL
│   ├── redshift_ddl.sql       # Redshift schema DDL
│   ├── load_aurora.py         # Load data into Aurora
│   ├── load_redshift.py       # Upload to S3 + COPY into Redshift
│   ├── validate_data.py       # Row count and integrity checks
│   └── load_all.py            # Orchestrator: run all steps
├── requirements.txt
└── README.md
```

### Acceptance Criteria
- [ ] All 8 CSV files downloaded from GitHub
- [ ] Aurora tables created with correct schemas
- [ ] Redshift tables created with correct schemas
- [ ] Aurora: 4 tables loaded, row counts match CSVs
- [ ] Redshift: 4 tables loaded, row counts match CSVs
- [ ] Cross-reference: `customer.cid` values exist in `purchase.cid`
- [ ] Indexes created on cid columns

---

## Unit 3: Semantic Layer

### Definition
| Field | Value |
|-------|-------|
| **Name** | Semantic Layer |
| **Type** | Platform deployment + configuration |
| **Technology** | AtScale (Helm on EKS), SML |
| **Scope** | Deploy AtScale, configure model |
| **Output** | Queryable semantic layer endpoint |

### Responsibilities
- Deploy AtScale on EKS using Helm chart (atscale-k8s-blueprints)
- Configure AtScale data connection to Aurora PostgreSQL
- Configure AtScale data connection to Redshift Serverless
- Define Customer_360 semantic model (SML or Design Center)
  - 6 dimensions: Customer, Address, Product, Category, Vendor, Date
  - 1 fact table: Purchase
  - 5 calculated measures: Revenue, Count, AOV, CLV, Units
  - 3 derived attributes: Big_Spender, Large_Order, Spend_Tier
- Publish model
- Verify query endpoint works with test SQL

### Code Organization
```
atscale/
├── helm/
│   ├── values.yaml            # Helm values for EKS deployment
│   └── values-override.yaml   # Environment-specific overrides
├── models/
│   ├── datasets/
│   │   ├── aurora_customer.yml
│   │   ├── aurora_address.yml
│   │   ├── redshift_purchase.yml
│   │   ├── redshift_product.yml
│   │   ├── redshift_category.yml
│   │   └── redshift_vendor.yml
│   ├── models/
│   │   └── customer_360.yml
│   └── relationships/
│       └── customer_360_rels.yml
├── scripts/
│   ├── deploy_atscale.sh      # Helm install/upgrade
│   ├── configure_connections.py  # REST API calls to create connections
│   ├── deploy_model.py        # Import SML model
│   └── verify_queries.py      # Test queries to validate
├── README.md
└── requirements.txt
```

### Acceptance Criteria
- [ ] AtScale pods running in `atscale` namespace (engine + design center)
- [ ] AtScale Design Center accessible via ALB ingress
- [ ] Data connection to Aurora: test connection succeeds
- [ ] Data connection to Redshift: test connection succeeds
- [ ] Customer_360 model published
- [ ] Single-source query works (Redshift only: "SELECT product, SUM(qty) ...")
- [ ] Single-source query works (Aurora only: "SELECT customer, state ...")
- [ ] Federated query works (join customer + purchase on cid)
- [ ] Calculated measure returns correct values

---

## Unit 4: Application

### Definition
| Field | Value |
|-------|-------|
| **Name** | Application |
| **Type** | Python application |
| **Technology** | Strands Agents, Streamlit, Amazon Bedrock |
| **Scope** | AI agent + chat UI |
| **Output** | Working chat application querying semantic layer |

### Responsibilities
- Implement Strands Agent with Claude Sonnet 4.6
- Implement AtScale query tool (REST API client)
- Write system prompt with semantic model metadata
- Build Streamlit chat interface
- Integrate agent with Streamlit
- Handle errors and edge cases
- Deploy to EC2 or EKS pod

### Code Organization
```
agent/
├── agent.py                   # Strands Agent creation and invocation
├── tools/
│   ├── __init__.py
│   ├── atscale_tool.py        # @tool decorated query function
│   └── atscale_client.py      # REST client for AtScale API
├── prompts/
│   └── system_prompt.py       # System prompt with model metadata
├── config.py                  # Configuration (endpoints, model name)
├── requirements.txt
└── tests/
    ├── test_agent.py          # Agent response tests
    └── test_atscale_client.py # Client unit tests

app/
├── app.py                     # Streamlit main app
├── components/
│   ├── chat.py                # Chat UI component
│   ├── results.py             # Results display (tables, SQL)
│   └── sidebar.py             # Sidebar info/config
├── .streamlit/
│   └── config.toml            # Streamlit configuration
├── requirements.txt
├── Dockerfile                 # Container image for deployment
└── README.md
```

### Acceptance Criteria
- [ ] Agent answers Q1 correctly (Aurora-only: "List 10 customers and their state")
- [ ] Agent answers Q4 correctly (Redshift-only: "Top 10 products by units sold")
- [ ] Agent answers Q7 correctly (Federated: "Top 10 spenders with their state")
- [ ] Agent answers Q11 correctly (Derived: "Big spenders per state")
- [ ] All 13 sample queries (Q1-Q13) return correct results
- [ ] Streamlit UI renders chat messages
- [ ] Streamlit shows results in table format
- [ ] Streamlit shows generated SQL (expandable)
- [ ] Error handling works (invalid question, timeout)
- [ ] Application accessible via browser

---

## Summary

| Unit | Technology | Est. Effort | Dependencies |
|------|-----------|-------------|--------------|
| 1. Infrastructure | CDK Python | 2-3 days | None |
| 2. Data Layer | Python scripts | 1-2 days | Unit 1 |
| 3. Semantic Layer | AtScale/Helm | 2-3 days | Units 1, 2 |
| 4. Application | Python/Streamlit | 3-4 days | Units 1, 3 |
| **Total** | | **8-12 days** | Sequential |
