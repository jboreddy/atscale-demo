# AtScale + AWS AI Services - Quick Reference Guide

**Date:** July 13, 2026  
**Companion to:** AtScale Semantic Layer Implementation Guide

---

## Quick Start Checklist

### Prerequisites
- [ ] AWS account with appropriate permissions
- [ ] Amazon Bedrock access enabled
- [ ] Amazon Redshift or Aurora instance running
- [ ] AtScale account (free tier or paid)
- [ ] Basic understanding of dimensional modeling

### Setup Steps (Condensed)

**Phase 1: Data Layer (Day 1-2)**
```bash
# 1. Configure security groups
aws ec2 authorize-security-group-ingress \
  --group-id sg-redshift \
  --protocol tcp --port 5439 \
  --cidr <ATSCALE_EGRESS_IP>

# 2. Create AtScale service user in Redshift
CREATE USER atscale_service PASSWORD 'secure_pass';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO atscale_service;
```

**Phase 2: Semantic Layer (Day 3-5)**
```yaml
# 1. Create data connection in AtScale Design Center
- Name: redshift_analytics
- Type: Amazon Redshift
- Host: my-cluster.redshift.amazonaws.com
- Credentials: atscale_service

# 2. Create semantic model
- Add dimensions (Customer, Product, Date)
- Add fact tables (Orders)
- Define relationships
- Create calculated measures
- Publish model
```

**Phase 3: AI Agent (Day 6-10)**
```python
# 1. Deploy AtScale MCP Server
docker run -d -p 8080:8080 \
  -e ATSCALE_SERVER=https://yourorg.atscale.com \
  atscale/mcp-server:latest

# 2. Register with AgentCore Gateway
aws bedrock-agent register-tool-target \
  --tool-target-id atscale-mcp \
  --endpoint https://atscale-mcp.example.com

# 3. Deploy Strands Agent
# (see full guide for agent code)
```

---

## Architecture Patterns

### Pattern 1: Single Source Query

```
User Question
    ↓
Agent (Claude)
    ↓
atscale_ask tool
    ↓
AtScale MCP Server
    ↓
AtScale Query Engine
    ↓
Redshift (single query)
    ↓
Results → Agent → User
```

**Example:** "Top 10 products by revenue"  
**Sources:** Redshift only  
**Latency:** 200-500ms (with aggregates)

### Pattern 2: Federated Query

```
User Question
    ↓
Agent (Claude)
    ↓
atscale_ask tool
    ↓
AtScale MCP Server
    ↓
AtScale Query Engine
    ├─→ Aurora (customers, addresses)
    └─→ Redshift (orders)
    ↓
Join on customer_id
    ↓
Results → Agent → User
```

**Example:** "Top spenders by state"  
**Sources:** Aurora + Redshift  
**Latency:** 500-2000ms

### Pattern 3: Calculated Metrics

```
User Question
    ↓
Agent identifies need for derived metric
    ↓
atscale_ask tool
    ↓
AtScale applies calculated measure
    ↓
Federated query with calculation
    ↓
Results → Agent → User
```

**Example:** "Big spenders per region"  
**Calculation:** IF(SUM(spend) > 10000, 'Yes', 'No')  
**Sources:** Aurora + Redshift + calculation

---

## Common Commands

### AtScale Data Connection Test
```bash
# Test Redshift connectivity
curl -X POST https://yourorg.atscale.com/api/1.0/org/connections/test \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "type": "REDSHIFT",
    "host": "cluster.region.redshift.amazonaws.com",
    "port": 5439,
    "database": "analytics"
  }'
```

### AtScale MCP Server Health Check
```bash
# Check MCP server status
curl http://atscale-mcp.example.com/health

# List available tools
curl http://atscale-mcp.example.com/tools
```

### AgentCore Gateway Query
```bash
# Invoke agent via Gateway
curl -X POST https://gateway.bedrock.aws.amazon.com/customer360 \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "message": "Top 10 customers by revenue"
    },
    "sessionId": "test-session-123"
  }'
```

### Monitor Query Performance
```sql
-- In AtScale query log
SELECT 
    query_id,
    user_name,
    query_text,
    execution_time_ms,
    rows_returned,
    from_aggregate
FROM atscale.query_log
WHERE query_date >= CURRENT_DATE - 7
ORDER BY execution_time_ms DESC
LIMIT 20;
```

---

## Troubleshooting Guide

### Issue: "Connection refused" to data source

**Symptoms:** AtScale can't connect to Redshift/Aurora

**Checklist:**
1. Security group allows AtScale egress IPs?
   ```bash
   aws ec2 describe-security-groups --group-ids sg-xyz
   ```
2. Database user exists and has permissions?
   ```sql
   SELECT * FROM pg_user WHERE usename = 'atscale_service';
   ```
3. Network path exists (VPC peering, transit gateway)?
4. TLS/SSL certificate valid?

**Solution:**
```bash
# Add AtScale IPs to security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-xyz \
  --protocol tcp --port 5439 \
  --cidr 52.1.1.0/24
```

### Issue: MCP Server not responding

**Symptoms:** AgentCore Gateway can't reach MCP server

**Checklist:**
1. MCP server container running?
   ```bash
   docker ps | grep atscale-mcp
   ```
2. Health endpoint responding?
   ```bash
   curl http://atscale-mcp:8080/health
   ```
3. Gateway has correct endpoint URL?
4. Credentials configured in AgentCore Identity?

**Solution:**
```bash
# Restart MCP server with logging
docker logs -f atscale-mcp-container

# Verify Gateway registration
aws bedrock-agent get-tool-target --tool-target-id atscale-mcp
```

### Issue: Slow query performance

**Symptoms:** Queries taking >5 seconds

**Diagnosis:**
1. Check if using aggregates:
   ```sql
   -- In AtScale
   SELECT * FROM query_log WHERE query_id = 'xyz';
   -- Look for from_aggregate = true
   ```
2. Check source query performance:
   ```sql
   -- In Redshift
   SELECT query, elapsed, rows FROM stl_query
   WHERE querytxt LIKE '%atscale%'
   ORDER BY starttime DESC LIMIT 10;
   ```

**Solutions:**
- Enable aggregate recommendations in AtScale
- Pre-build aggregates for common queries
- Add indexes on join keys in source databases
- Consider materializing complex calculations

### Issue: Security policy not working

**Symptoms:** Users see data they shouldn't

**Checklist:**
1. Policy applied to correct role?
2. User mapped to correct role?
3. Policy syntax correct?
4. Dimension/attribute names match model?

**Debug:**
```yaml
# Check user's role in AtScale
GET /api/1.0/users/{username}/roles

# Review applied policies
GET /api/1.0/models/{model}/security/policies

# Test query as specific user
POST /api/1.0/query
Headers: X-Impersonate-User: testuser@company.com
```

---

## Cost Optimization Tips

### 1. Enable Prompt Caching
```python
# In Strands agent
agent = Agent(
    model="anthropic.claude-sonnet-4-6-v1:0",
    cache_system_prompt=True,  # Cache semantic model context
    ...
)
```
**Savings:** 70-90% on input token costs for repeated queries

### 2. Pre-Build Aggregates
```yaml
# In AtScale Design Center
aggregates:
  - name: "daily_revenue_by_product"
    schedule: "0 1 * * *"  # Daily at 1 AM
    dimensions: [Product, Date]
    measures: [Total_Revenue, Order_Count]
```
**Savings:** 10-100x query speedup, reduced source costs

### 3. Set Query Limits
```yaml
# In AtScale MCP Server config
query_limits:
  max_rows: 10000
  timeout_seconds: 30
  max_memory_mb: 2048
```
**Savings:** Prevent runaway queries, control costs

### 4. Use Read Replicas
```yaml
# Aurora connection to read replica
connection:
  host: "replica.cluster-xyz.us-east-1.rds.amazonaws.com"
  read_only: true
```
**Savings:** Reduce load on primary, lower operational costs

### 5. Co-locate Services
```
Same Region:
- AtScale MCP Server (ECS in us-east-1)
- Redshift (us-east-1)
- Aurora (us-east-1)
- AgentCore (us-east-1)
```
**Savings:** Eliminate cross-region data transfer fees

---

## Security Checklist

### Network Security
- [ ] Data sources in private subnets
- [ ] Security groups with least privilege
- [ ] TLS 1.2+ for all connections
- [ ] No public endpoints for databases
- [ ] AtScale Cloud uses PrivateLink (if Enterprise tier)

### Authentication & Authorization
- [ ] JWT validation at AgentCore Gateway
- [ ] Service account credentials in Secrets Manager
- [ ] Credentials rotated every 90 days
- [ ] MFA enabled for administrative access
- [ ] Role-based access in AtScale

### Data Protection
- [ ] Row-level security policies defined
- [ ] PII columns masked or restricted
- [ ] Encryption at rest in sources
- [ ] Encryption in transit everywhere
- [ ] No data stored in AtScale (query-time only)

### Audit & Compliance
- [ ] Query logging enabled
- [ ] Logs retained per policy (90+ days)
- [ ] Regular access reviews scheduled
- [ ] Incident response plan documented
- [ ] SOC 2 / compliance requirements met

---

## Performance Benchmarks

### Typical Query Latencies

| Query Type | Without Aggregates | With Aggregates | Notes |
|------------|-------------------|-----------------|-------|
| Single source | 500-2000ms | 100-300ms | Redshift only |
| Federated (2 sources) | 1000-4000ms | 200-800ms | Aurora + Redshift |
| Complex aggregation | 3000-10000ms | 300-1000ms | Group by + calculations |
| Large result set (10K rows) | 5000-15000ms | 1000-3000ms | Network transfer time |

### Aggregate Build Times

| Data Volume | Initial Build | Incremental Update |
|-------------|---------------|-------------------|
| 1M rows | 30-60 seconds | 5-15 seconds |
| 10M rows | 2-5 minutes | 30-90 seconds |
| 100M rows | 10-30 minutes | 3-10 minutes |

### Concurrent Users

| Deployment | Concurrent Queries | Peak Throughput |
|------------|-------------------|-----------------|
| AtScale Cloud (Essentials) | 10-20 | ~50 queries/min |
| AtScale Cloud (Enterprise) | 50-100 | ~200 queries/min |
| Self-managed (3 replicas) | 100+ | ~500 queries/min |

---

## Quick Reference: SQL Translation Examples

### Natural Language → AtScale SQL

**Question:** "Top 10 customers by revenue in California"

**AtScale Semantic SQL:**
```sql
SELECT 
    [Dim_Customer].[customer_name],
    [Dim_Location].[state],
    SUM([Measures].[Total_Revenue])
FROM [Customer_360_Model]
WHERE [Dim_Location].[state] = 'CA'
GROUP BY 
    [Dim_Customer].[customer_name],
    [Dim_Location].[state]
ORDER BY SUM([Measures].[Total_Revenue]) DESC
LIMIT 10
```

**Translated to Aurora:**
```sql
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name,
    a.state
FROM customers c
JOIN addresses a ON c.customer_id = a.customer_id
WHERE a.state = 'CA'
```

**Translated to Redshift:**
```sql
SELECT 
    customer_id,
    SUM(total_amount) as revenue
FROM orders
WHERE customer_id IN (SELECT customer_id FROM customer_ids_from_aurora)
GROUP BY customer_id
```

**Final Join (in AtScale):**
```sql
-- Results merged on customer_id dimension key
```

---

## Resource Links

### AtScale Resources
- Documentation: https://documentation.atscale.com
- Community: https://community.atscale.com
- MCP Demo: https://www.atscale.com/explore/interactive-demos/mcp-integration
- Support: support@atscale.com

### AWS Resources
- Bedrock AgentCore Docs: https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html
- MCP Specification: https://modelcontextprotocol.io
- Strands Agents: https://github.com/strands-agents
- AWS Architecture Center: https://aws.amazon.com/architecture

### Reference Implementations
- Stardog Blog Post: [AWS ML Blog](https://aws.amazon.com/blogs/machine-learning/build-a-semantic-layer-for-agentic-ai-on-aws-with-stardog-and-amazon-bedrock-agentcore/)
- AtScale + Redshift: [AWS Partner Blog](https://aws.amazon.com/blogs/apn/using-atscale-and-amazon-redshift-to-build-a-modern-analytics-program-with-a-lake-house/)
- Sample Code: https://github.com/aws-samples/sample-semantic-layer-using-agents

---

**Last Updated:** July 13, 2026  
**Version:** 1.0  
**For:** Quick reference and troubleshooting
