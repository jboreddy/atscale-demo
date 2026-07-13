# Application Design - Component Methods

## Component 1: Infrastructure (CDK Stacks)

### NetworkingStack
| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `__init__()` | vpc_cidr, az_count | VPC, Subnets, NAT, IGW, SGs | Create all networking resources |

### DatabaseStack
| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `__init__()` | vpc, security_groups | Aurora cluster, Redshift namespace | Create database resources |

### EksStack
| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `__init__()` | vpc, security_groups | EKS cluster, node group, add-ons | Create container platform |

### StorageStack
| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `__init__()` | account_id, region | S3 bucket | Create staging storage |

### IamStack
| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `__init__()` | resource ARNs | IAM roles, policies | Create access controls |

---

## Component 2: Data Layer (Scripts)

### data_loader.py
| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `download_csvs(repo_url, output_dir)` | GitHub URL, local path | CSV files on disk | Fetch C360 data |
| `upload_to_s3(local_dir, bucket, prefix)` | Path, bucket, prefix | S3 objects | Stage CSVs for Redshift COPY |
| `create_aurora_schema(conn_string)` | Aurora connection | DDL executed | Create Aurora tables |
| `create_redshift_schema(conn_string)` | Redshift connection | DDL executed | Create Redshift tables |
| `load_aurora_data(conn_string, csv_dir)` | Connection, CSV path | Rows inserted | Load customer data |
| `load_redshift_data(conn_string, bucket, role_arn)` | Connection, S3, IAM role | Rows loaded | COPY from S3 |
| `validate_data(aurora_conn, redshift_conn)` | Both connections | Validation report | Verify row counts |

---

## Component 3: Semantic Layer (AtScale)

### atscale_deploy.py (Deployment Helper)
| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `deploy_helm_chart(kubeconfig, values_file)` | K8s config, Helm values | AtScale pods running | Deploy AtScale on EKS |
| `wait_for_ready(namespace, timeout)` | Namespace, timeout | Ready status | Health check |
| `configure_connections(atscale_url, connections)` | URL, connection configs | Connections created | Set up data sources |

### Customer_360 Model (SML)
| Artifact | Purpose |
|----------|---------|
| `datasets/aurora_customer.yml` | Dataset definition for Aurora customer table |
| `datasets/aurora_address.yml` | Dataset definition for Aurora address table |
| `datasets/redshift_purchase.yml` | Dataset definition for Redshift purchase table |
| `datasets/redshift_product.yml` | Dataset definition for Redshift product table |
| `datasets/redshift_category.yml` | Dataset definition for Redshift category table |
| `datasets/redshift_vendor.yml` | Dataset definition for Redshift vendor table |
| `models/customer_360.yml` | Main model with dimensions, facts, measures |
| `relationships/` | Relationship definitions between dimensions and facts |

---

## Component 4: AI Agent

### agent.py (Strands Agent)
| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `create_agent()` | None | Agent instance | Initialize Strands Agent with tools and system prompt |
| `invoke(question, session_id)` | NL question, session | AgentResponse (answer, metadata) | Process a user question |

### tools/atscale_tool.py
| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `query_atscale(sql: str) -> dict` | SQL string | {results, columns, row_count} | Execute SQL against AtScale |
| `get_model_metadata() -> dict` | None | {dimensions, measures, relationships} | Get semantic model schema |

### tools/atscale_client.py
| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `__init__(endpoint, username, password)` | Connection params | Client instance | Create AtScale REST client |
| `execute_query(sql, model_name)` | SQL, model | ResultSet | Submit query via REST API |
| `get_catalogs()` | None | List[Catalog] | List available models |
| `health_check()` | None | bool | Verify AtScale is reachable |

---

## Component 5: Chat Application

### app.py (Streamlit)
| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `main()` | None | Streamlit UI | Application entry point |
| `render_chat_history(messages)` | List[Message] | UI elements | Display conversation |
| `process_question(question)` | User input string | Agent response | Invoke agent and get answer |
| `render_results(response)` | AgentResponse | UI (text + table) | Format and display answer |
| `render_sql_panel(sql)` | SQL string | Expandable panel | Show generated SQL |
| `render_sources(sources)` | List[str] | Badge elements | Show data sources used |
