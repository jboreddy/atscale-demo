"""AtScale query tool for Strands Agent."""

from strands import tool
from .atscale_client import AtScaleClient

# Initialize client (singleton per process)
_client = None


def _get_client() -> AtScaleClient:
    """Get or create AtScale client instance."""
    global _client
    if _client is None:
        _client = AtScaleClient()
    return _client


@tool
def query_atscale(sql: str) -> dict:
    """
    Execute a SQL query against the AtScale Customer 360 semantic layer.
    
    AtScale federates queries across Aurora PostgreSQL (customer data) and
    Amazon Redshift (product/purchase data) and joins them on shared keys.
    
    Available Dimensions:
    - dim_customer: customer_id, first_name, last_name, full_name, email, phone
    - dim_address: city, state, zip_code, street (joined to customer via cid)
    - dim_product: product_id, product_name, brand, product_price
    - dim_category: dept_name, parent_category
    - dim_vendor: vendor_name, industry
    
    Available Measures (from fact_purchase):
    - total_revenue: SUM(price * quantity) — total sales in dollars
    - order_count: COUNT of purchase transactions
    - units_sold: SUM(quantity) — total items sold
    - avg_order_value: total_revenue / order_count
    - customer_lifetime_value: total revenue per customer
    - distinct_customers: COUNT(DISTINCT cid)
    
    Calculated Attributes:
    - big_spender: 'Yes' if customer lifetime value > $10,000
    - large_order: 'Yes' if single order > $500
    - spend_tier: 'Platinum' (>$50K), 'Gold' (>$10K), 'Standard'
    
    Example queries:
    - "SELECT full_name, state, total_revenue FROM customer_360 GROUP BY full_name, state ORDER BY total_revenue DESC LIMIT 10"
    - "SELECT state, COUNT(*) as customer_count FROM customer_360 WHERE state = 'WI' GROUP BY state"
    - "SELECT product_name, units_sold FROM customer_360 GROUP BY product_name ORDER BY units_sold DESC LIMIT 10"
    
    Args:
        sql: SQL query using the semantic model's dimensions and measures.
             Use the table name 'customer_360' as the FROM clause.
             
    Returns:
        Dictionary with:
        - columns: list of column names
        - rows: list of row data
        - row_count: number of rows returned
        - sql_used: the SQL that was executed
        - success: boolean indicating if query succeeded
        - error: error message if success is False
    """
    client = _get_client()
    return client.execute_query(sql)


@tool
def get_semantic_model_info() -> dict:
    """
    Get information about the Customer 360 semantic model structure.
    
    Returns available dimensions, measures, and calculated attributes
    that can be used in SQL queries.
    
    Returns:
        Dictionary with model metadata including available fields.
    """
    return {
        "model_name": "customer_360",
        "description": "Unified Customer 360 model spanning Aurora (customers) and Redshift (products/purchases)",
        "dimensions": {
            "dim_customer": {
                "source": "Aurora PostgreSQL",
                "attributes": ["customer_id", "first_name", "last_name", "full_name", "email", "phone"],
            },
            "dim_address": {
                "source": "Aurora PostgreSQL",
                "attributes": ["city", "state", "zip_code", "street"],
                "joined_via": "customer_id",
            },
            "dim_product": {
                "source": "Redshift",
                "attributes": ["product_id", "product_name", "brand", "product_price"],
            },
            "dim_category": {
                "source": "Redshift",
                "attributes": ["dept_name", "parent_category"],
            },
            "dim_vendor": {
                "source": "Redshift",
                "attributes": ["vendor_name", "industry"],
            },
        },
        "measures": {
            "total_revenue": "SUM(price * quantity) - total sales dollars",
            "order_count": "COUNT of transactions",
            "units_sold": "SUM(quantity)",
            "avg_order_value": "total_revenue / order_count",
            "customer_lifetime_value": "total spend per customer",
            "distinct_customers": "COUNT(DISTINCT customers)",
        },
        "calculated_attributes": {
            "big_spender": "Yes/No based on CLV > $10,000",
            "large_order": "Yes/No based on order > $500",
            "spend_tier": "Platinum/Gold/Standard",
        },
    }
