# Research Findings: AtScale Federation & Multi-Source Query Patterns

**Date:** July 17, 2026  
**Status:** For Future Reference  
**Context:** Evaluated during C360 Semantic Layer POC

---

## Finding: AtScale Does NOT Perform Runtime Cross-Database JOINs

### What AtScale's "Cross-Cloud Federation" Actually Means

| Term | Industry Definition | AtScale's Implementation |
|------|--------------------|--------------------------| 
| Cross-Cloud Federation | Runtime JOIN across multiple databases | Unified semantic model with connections to multiple clouds — queries route independently to each engine |
| Data Virtualization | Pull from multiple sources, join in-memory | Query pushdown to a single warehouse — the "virtual" part is the model, not the execution |
| Virtual Data Warehouse | Trino/Presto-like federated SQL | Logical dimensional model on top of physical tables — no cross-engine joins |

### Key Insight

AtScale pushes queries to individual databases. It does NOT:
- Pull data from Database A and Database B and join them
- Act as a federated SQL engine (like Trino, Presto, or Stardog)
- Execute a single query spanning two different database connections

### What AtScale DOES Support

- ✅ Multiple data source connections (Redshift + Snowflake + BigQuery simultaneously)
- ✅ Unified metrics/dimensions defined once, consumed across connections
- ✅ Per-query routing to the appropriate engine
- ✅ Aggregates materialized in "preferred storage" per connection
- ✅ Consistent business logic regardless of which warehouse is queried

---

## Alternative Pattern: Agent-Mediated Federation

### How It Works

When data lives in separate databases (e.g., Aurora + Redshift), the AI agent can act as the "federation layer":

1. Agent identifies question requires data from two domains
2. Agent makes **separate** AtScale queries to each source
3. Agent receives two result sets
4. LLM combines/joins results in-context
5. Agent produces unified answer

### Viability Assessment

| Factor | Small Data (POC) | Large Data (Production) |
|--------|-----------------|------------------------|
| Correctness | ✅ Works | ⚠️ Risk (LLM joins are probabilistic) |
| Performance | ✅ Acceptable | ❌ Slow (two round-trips + LLM processing) |
| Scalability | ✅ 500 rows fine | ❌ Context window limits (~200K tokens) |
| Auditability | ⚠️ Limited | ❌ No SQL audit trail for the "join" |
| Cost | ⚠️ More tokens | ❌ Expensive at scale |
| Reproducibility | ⚠️ Mostly | ❌ Non-deterministic |

### When To Use This Pattern

✅ **Good for:**
- POC/demos with small data (<1000 rows per query)
- Top-N queries (agent fetches top results from each, matches them)
- Questions where one source filters and the other provides the answer
- Scenarios where data CANNOT be co-located (regulatory, multi-org)

❌ **Not recommended for:**
- Production analytics requiring exact, auditable results
- Large-scale aggregations (millions of rows)
- Compliance-sensitive use cases (non-deterministic joins)
- High-throughput scenarios (cost + latency)

---

## Architecture Decision: Co-Locate in Redshift (Current Plan)

### Decision Rationale

| Option | Chosen? | Reason |
|--------|---------|--------|
| **All data in Redshift** | ✅ Yes | Deterministic JOINs, single pushdown, auditable, scales |
| Agent-mediated multi-source | No (future consideration) | Works for POC but not production-grade |
| Redshift Federated Query to Aurora | No | Adds complexity without clear benefit for POC |
| AtScale cross-database JOIN | N/A | Not a supported capability |

### Production Recommendation

```
Aurora PostgreSQL (operational) → CDC/ETL → Redshift (analytical copy)
                                                    ↓
                                              AtScale queries Redshift
                                                    ↓
                                              AI Agent gets answers
```

---

## Future Considerations

### When to Revisit Multi-Source Architecture

1. **Regulatory requirement** prevents data co-location (e.g., PII must stay in Aurora)
2. **Real-time operational queries** needed alongside analytics (Aurora for < 1 second, Redshift for complex aggregations)
3. **Multi-cloud enterprise** with data in Snowflake + Redshift + BigQuery
4. **AtScale adds native federation** in a future release

### If Multi-Source Needed, Explore

- **Amazon Redshift Federated Query** — Redshift queries Aurora via connector (single SQL endpoint, Redshift handles the join)
- **AWS Glue / Athena Federation** — Query multiple sources via Athena connectors
- **Trino/Starburst** — Dedicated federated SQL engine (could sit between AtScale and data sources)
- **Agent-mediated pattern** — For small-scale, demo-quality cross-source queries

---

## References

- AtScale Cross-Cloud Federation Webinar: https://www.atscale.com/resource/cross-cloud-federation-and-semantic-layers/
- AtScale Data Virtualization Blog: https://www.atscale.com/blog/how-data-virtualization-supports-bi-analytics/
- AtScale Breaking Data Silos Blog: https://www.atscale.com/blog/breaking-data-silos-cross-cloud-semantic-layers/
- TDWI Expert Panel (2025): Cross-Cloud Federation and Semantic Layers

---

**Decision:** Proceed with Redshift-only architecture. Save this document for future architecture discussions.
