# Unit of Work - Dependency Matrix

## Dependency Graph

```
Unit 1: Infrastructure
    │
    ├──────────────────────────┐
    │                          │
    ▼                          ▼
Unit 2: Data Layer      Unit 3: Semantic Layer
    │                          │
    └──────────┬───────────────┘
               │
               ▼
         Unit 4: Application
```

## Dependency Matrix

| Unit | Depends On | Provides To | Blocking? |
|------|-----------|-------------|-----------|
| **1. Infrastructure** | — | Units 2, 3, 4 | Yes (all others blocked) |
| **2. Data Layer** | Unit 1 (DB endpoints, S3) | Unit 3 (data in tables) | Yes (Unit 3 needs data) |
| **3. Semantic Layer** | Unit 1 (EKS), Unit 2 (data) | Unit 4 (query endpoint) | Yes (Unit 4 needs AtScale) |
| **4. Application** | Unit 1 (compute), Unit 3 (AtScale endpoint) | End User | No (terminal unit) |

## Detailed Dependencies

### Unit 1 → Unit 2
| What Unit 2 needs from Unit 1 | How it's provided |
|-------------------------------|-------------------|
| Aurora endpoint | CDK Stack output / SSM parameter |
| Redshift endpoint | CDK Stack output / SSM parameter |
| S3 bucket name | CDK Stack output / SSM parameter |
| Database credentials | Secrets Manager ARN |
| IAM role ARN (Redshift COPY) | CDK Stack output |
| Network access (SG rules) | Security group configuration |

### Unit 1 → Unit 3
| What Unit 3 needs from Unit 1 | How it's provided |
|-------------------------------|-------------------|
| EKS cluster kubeconfig | `aws eks update-kubeconfig` |
| EKS namespace | kubectl create |
| ALB Ingress Controller | EKS add-on |
| EBS CSI Driver | EKS add-on |
| Network access to Aurora | Security group rules |
| Network access to Redshift | Security group rules |

### Unit 2 → Unit 3
| What Unit 3 needs from Unit 2 | How it's provided |
|-------------------------------|-------------------|
| Tables populated with data | Data loading scripts complete |
| Schema structure (for modeling) | DDL files as reference |

### Unit 3 → Unit 4
| What Unit 4 needs from Unit 3 | How it's provided |
|-------------------------------|-------------------|
| AtScale query endpoint URL | Ingress/Service URL |
| AtScale credentials | Created during AtScale setup |
| Semantic model name | Published model identifier |
| Model metadata (dims, measures) | AtScale REST API or hardcoded in prompt |

### Unit 1 → Unit 4
| What Unit 4 needs from Unit 1 | How it's provided |
|-------------------------------|-------------------|
| Bedrock access (IAM role) | Instance profile or pod IAM |
| Compute (EC2 or EKS pod) | Infrastructure stack |
| ALB for public access | Ingress configuration |

## Execution Order

```
Week 1-2:  [====Unit 1: Infrastructure====]
                                          |
Week 2:                              [==Unit 2: Data==]
                                                     |
Week 2-3:                                       [===Unit 3: Semantic===]
                                                                      |
Week 3-4:                                                        [====Unit 4: App====]
```

## Integration Points

| Integration | Test | Validates |
|-------------|------|-----------|
| CDK → Aurora | `psql -h <endpoint>` | Network + credentials |
| CDK → Redshift | `psql -h <endpoint> -p 5439` | Network + credentials |
| CDK → EKS | `kubectl get nodes` | Cluster access |
| Data → Aurora | `SELECT COUNT(*) FROM customer` | Data loaded |
| Data → Redshift | `SELECT COUNT(*) FROM purchase` | Data loaded |
| AtScale → Aurora | AtScale "Test Connection" | JDBC connectivity |
| AtScale → Redshift | AtScale "Test Connection" | JDBC connectivity |
| AtScale → Model | SQL query returns results | Model published correctly |
| Agent → Bedrock | Agent invokes model | IAM + model access |
| Agent → AtScale | Tool returns query results | REST API connectivity |
| Streamlit → Agent | UI shows formatted answer | End-to-end flow |

## Risk: Circular Dependencies

**None identified.** The dependency graph is a strict DAG (directed acyclic graph) with no cycles.
