# Integration Test Instructions

## Test Matrix

Test all 13 sample queries from the PRD to validate end-to-end functionality.

---

## Pre-Test Checks

```bash
# 1. Verify infrastructure
kubectl get nodes                              # EKS nodes running
kubectl -n atscale get pods                   # AtScale pods running
aws rds describe-db-clusters --query 'DBClusters[?DBClusterIdentifier==`c360-poc-aurora`].Status' --output text  # "available"
aws redshift-serverless get-workgroup --workgroup-name c360-atscale-wg --query 'workgroup.status' --output text  # "AVAILABLE"

# 2. Verify data
psql -h $AURORA_HOST -U postgres -d customer360_db -c "SELECT COUNT(*) FROM customer;"
psql -h $REDSHIFT_HOST -U admin -d analytics_db -p 5439 -c "SELECT COUNT(*) FROM purchase;"

# 3. Verify AtScale
curl -s "$ATSCALE_URL/health" | grep -q "ok" && echo "AtScale: OK" || echo "AtScale: FAIL"

# 4. Verify Bedrock access
aws bedrock list-foundation-models --query 'modelSummaries[?modelId==`anthropic.claude-sonnet-4-6-v1:0`].modelId' --output text
```

---

## Test Categories

### Category 1: Aurora-Only Queries (Customer Data)

| # | Question | Expected | Pass Criteria |
|---|----------|----------|---------------|
| Q1 | "List 10 customers and their state" | Table with names + states | 10 rows, all have state values |
| Q2 | "How many customers are in Wisconsin?" | Count number | Positive integer, source: Aurora |
| Q3 | "Show customer email addresses in California" | List of emails | Emails listed, state=CA filter applied |

### Category 2: Redshift-Only Queries (Product/Purchase Data)

| # | Question | Expected | Pass Criteria |
|---|----------|----------|---------------|
| Q4 | "Top 10 products by units sold" | Ranked product list | 10 products, ordered by quantity DESC |
| Q5 | "Revenue by product category" | Category + revenue | Multiple categories with $ amounts |
| Q6 | "Which vendors have the most products?" | Vendor + count | Vendors ranked by product count |

### Category 3: Federated Queries (Aurora + Redshift)

| # | Question | Expected | Pass Criteria |
|---|----------|----------|---------------|
| Q7 | "Who are our top 10 customer spenders, with their state?" | Name + state + spend | 10 rows, has both name (Aurora) and spend (Redshift) |
| Q8 | "Big spenders in Wisconsin" | Filtered customer list | Only WI state, spend > $10K threshold |
| Q9 | "Average order value by customer state" | State + AOV | Multiple states with dollar amounts |
| Q10 | "Which state has the highest total revenue?" | Single state + amount | One state name with revenue figure |

### Category 4: Derived Metrics

| # | Question | Expected | Pass Criteria |
|---|----------|----------|---------------|
| Q11 | "How many big spenders do we have per state?" | State + count | States with counts, uses Big_Spender rule |
| Q12 | "List all large orders above $500" | Order list | Orders where price*qty > 500 |
| Q13 | "What is the customer lifetime value for the top customer?" | Name + CLV | Single customer with total $ spend |

---

## Test Execution

### Manual Testing (Chat UI)

1. Open Streamlit at http://localhost:8501 (or ALB URL)
2. Type each question from Q1-Q13
3. Verify:
   - ✓ Answer is relevant and correct
   - ✓ Data is formatted (tables for multi-row, text for single values)
   - ✓ SQL panel shows generated query
   - ✓ Sources badge shows correct databases
   - ✓ No errors or "I don't know" for valid questions

### Automated Testing (Agent CLI)

```bash
cd agent/

# Run agent directly with test questions
python agent.py "List 10 customers and their state"
python agent.py "Top 10 products by units sold"
python agent.py "Who are our top 10 customer spenders, with their state?"
python agent.py "How many big spenders per state?"
```

### Validation Criteria

For each query, verify:

| Check | How to Verify |
|-------|---------------|
| **Correctness** | Compare agent answer with direct SQL result |
| **Completeness** | Answer addresses the full question |
| **Source Attribution** | Correct databases cited (Aurora/Redshift/Both) |
| **SQL Quality** | Generated SQL is valid and efficient |
| **Latency** | Response within 10 seconds |
| **Error Handling** | Invalid questions return graceful "I can't answer that" |

---

## Direct SQL Verification

Run these queries directly against the databases to verify expected results:

```sql
-- Q1 Verification (Aurora)
SELECT c.first_name, c.last_name, a.state
FROM customer c JOIN address a ON c.cid = a.cid
LIMIT 10;

-- Q4 Verification (Redshift)
SELECT p.name, SUM(pu.quantity) as units
FROM purchase pu JOIN product p ON pu.pid = p.id
GROUP BY p.name ORDER BY units DESC LIMIT 10;

-- Q7 Verification (Manual cross-DB join)
-- Aurora:
SELECT cid, first_name || ' ' || last_name as name, state
FROM customer c JOIN address a ON c.cid = a.cid;

-- Redshift:
SELECT cid, SUM(price * quantity) as total_spend
FROM purchase GROUP BY cid ORDER BY total_spend DESC LIMIT 10;

-- Join manually and verify AtScale produces same result
```

---

## Test Results Template

| # | Question | Status | Latency | Notes |
|---|----------|--------|---------|-------|
| Q1 | List 10 customers + state | ⬜ | | |
| Q2 | Customers in Wisconsin | ⬜ | | |
| Q3 | Emails in California | ⬜ | | |
| Q4 | Top products by units | ⬜ | | |
| Q5 | Revenue by category | ⬜ | | |
| Q6 | Vendors by product count | ⬜ | | |
| Q7 | Top spenders + state | ⬜ | | |
| Q8 | Big spenders in WI | ⬜ | | |
| Q9 | AOV by state | ⬜ | | |
| Q10 | Highest revenue state | ⬜ | | |
| Q11 | Big spenders per state | ⬜ | | |
| Q12 | Large orders >$500 | ⬜ | | |
| Q13 | CLV for top customer | ⬜ | | |

**Pass threshold:** All 13 queries return correct, non-empty results.

---

## Troubleshooting

### Agent returns "I don't have access to data"
- Check: AtScale URL reachable from agent (`curl $ATSCALE_URL/health`)
- Check: AtScale credentials correct
- Check: Model published in AtScale

### Federated queries return partial data
- Check: Both Aurora and Redshift connections work in AtScale (test in Design Center)
- Check: `cid` values overlap between databases (`validate_data.py`)

### Slow queries (>10s)
- Check: AtScale aggregate tables (first query may be slower)
- Check: Redshift base capacity (scale up if needed)
- Check: Network latency (all in same region?)

### Bedrock errors
- Check: Model access enabled in Bedrock console
- Check: IAM role has `bedrock:InvokeModel` permission
- Check: AWS region is us-east-1
