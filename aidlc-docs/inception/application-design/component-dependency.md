# Application Design - Component Dependencies

## Dependency Matrix

| Component | Depends On | Depended By | Communication |
|-----------|-----------|-------------|---------------|
| **Infrastructure** | None | All others | CloudFormation exports |
| **Data Layer** | Infrastructure | Semantic Layer, Application | SQL (psycopg2, S3 SDK) |
| **Semantic Layer** | Infrastructure, Data Layer | Application | REST API / JDBC |
| **AI Agent** | Semantic Layer, Bedrock | Chat App | In-process function call |
| **Chat App** | AI Agent | None (end user) | HTTP (Streamlit) |

---

## Dependency Graph

```
                    ┌──────────────────┐
                    │  Infrastructure   │
                    │  (CDK Stacks)     │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────┐  ┌──────────────┐  ┌──────────┐
    │ Data Layer  │  │ EKS Cluster  │  │ Bedrock  │
    │ (Scripts)   │  │ (AtScale)    │  │ (Model)  │
    └──────┬──────┘  └──────┬───────┘  └────┬─────┘
           │                │               │
           │                ▼               │
           │       ┌──────────────┐         │
           └──────▶│Semantic Layer│         │
                   │  (AtScale)   │         │
                   └──────┬───────┘         │
                          │                 │
                          ▼                 ▼
                   ┌─────────────────────────────┐
                   │       AI Agent              │
                   │   (Strands + Tools)         │
                   └──────────┬──────────────────┘
                              │
                              ▼
                   ┌─────────────────────────────┐
                   │      Chat Application       │
                   │       (Streamlit)           │
                   └─────────────────────────────┘
```

---

## Build Order (Sequential)

```
Phase 1: Infrastructure
    └── Deploy CDK stacks (VPC, EKS, Aurora, Redshift, S3, IAM)

Phase 2: Data Layer
    └── Load data into Aurora and Redshift (requires infra)

Phase 3: Semantic Layer
    └── Deploy AtScale on EKS, configure model (requires infra + data)

Phase 4: Application
    └── Build agent + chat app (requires semantic layer endpoint)
```

---

## Data Flow

### Query Flow (Runtime)

```
User Question: "Top 10 spenders in Wisconsin"
         │
         ▼
┌─ Streamlit ─────────────────────────────────────────────────┐
│  1. Capture user input                                       │
│  2. Call agent.invoke(question, session_id)                   │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌─ Strands Agent ──────────────────────────────────────────────┐
│  3. Send question + system prompt to Claude Sonnet (Bedrock) │
│  4. Claude reasons about data needed                         │
│  5. Claude generates SQL for AtScale semantic model          │
│  6. Agent invokes query_atscale(sql) tool                    │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌─ AtScale Tool ───────────────────────────────────────────────┐
│  7. Submit SQL to AtScale REST endpoint                      │
│  8. AtScale parses semantic SQL                              │
│  9. AtScale plans federated query execution                  │
└──────────────────────────┬───────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
┌─ Aurora ──────────┐     ┌─ Redshift ──────────┐
│  10a. Query:      │     │  10b. Query:         │
│  SELECT cid,      │     │  SELECT cid,         │
│    first_name,    │     │    SUM(price*qty)    │
│    state          │     │  FROM purchase       │
│  FROM customer    │     │  GROUP BY cid        │
│  JOIN address     │     │                      │
│  WHERE state='WI' │     │                      │
└────────┬──────────┘     └──────────┬───────────┘
         │                           │
         └────────────┬──────────────┘
                      │
                      ▼
┌─ AtScale (Join) ────────────────────────────────────────────┐
│  11. Join results on cid dimension key                       │
│  12. Apply ordering (DESC by spend)                          │
│  13. Apply LIMIT 10                                          │
│  14. Return result set                                       │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌─ Agent ──────────────────────────────────────────────────────┐
│  15. Receive results from tool                               │
│  16. Send results back to Claude for summarization           │
│  17. Claude formats human-readable answer                    │
│  18. Return to Streamlit                                     │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌─ Streamlit ──────────────────────────────────────────────────┐
│  19. Render answer text                                      │
│  20. Render results table (if applicable)                    │
│  21. Show SQL in expandable panel                            │
│  22. Show data sources used                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Configuration Dependencies

| Component | Configuration Source | Format |
|-----------|---------------------|--------|
| CDK Stacks | `infrastructure/cdk.json` + context | Python/JSON |
| Data Loader | Environment variables (endpoints, credentials) | .env file |
| AtScale | Helm values + REST API | YAML + JSON |
| Agent | Environment variables (Bedrock region, AtScale endpoint) | .env file |
| Streamlit | `app/.streamlit/config.toml` + env vars | TOML + .env |

---

## Failure Modes & Recovery

| Failure | Impact | Recovery |
|---------|--------|----------|
| Aurora unavailable | Customer queries fail | AtScale returns error; agent reports "unable to access customer data" |
| Redshift unavailable | Product/purchase queries fail | AtScale returns error; agent reports "unable to access analytics data" |
| AtScale pods crash | All queries fail | K8s restarts pods; agent retries after delay |
| Bedrock throttled | Agent can't reason | Retry with exponential backoff |
| Streamlit crash | UI unavailable | Process manager restarts; user refreshes browser |
| Network partition | Cross-component communication fails | Timeout errors surfaced to user |
