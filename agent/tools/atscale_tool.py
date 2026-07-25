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

    The semantic layer provides a unified view of customer, product, and purchase
    data. All queries use the "customer_360" model.

    Available Dimensions (use these as column names in SELECT/WHERE/GROUP BY):
    - "Customer Name" — full name of the customer
    - "First Name" — customer first name
    - "Last Name" — customer last name
    - "Email" — customer email address
    - "Phone" — customer phone number
    - "State" — customer state (from address)
    - "City" — customer city (from address)
    - "Zip Code" — postal code
    - "Product Name" — name of the product
    - "Brand" — product brand
    - "List Price" — product list price
    - "Category" — product category/department
    - "Vendor Name" — vendor/supplier name
    - "Industry" — vendor industry

    Available Metrics (use these as column names, they auto-aggregate):
    - "Total Revenue" — SUM(price * quantity) in dollars
    - "Order Count" — count of purchase transactions
    - "Units Sold" — SUM(quantity)
    - "Distinct Customers" — COUNT DISTINCT customers

    Important SQL rules:
    - Table name: "customer_360" (in FROM clause)
    - Column names MUST be in double quotes (they contain spaces)
    - Metrics auto-aggregate when grouped by dimensions
    - Use ORDER BY and LIMIT for top-N queries

    Example queries:
    - SELECT "Customer Name", "State", "Total Revenue" FROM "customer_360" ORDER BY "Total Revenue" DESC LIMIT 10
    - SELECT "State", "Total Revenue", "Distinct Customers" FROM "customer_360" ORDER BY "Total Revenue" DESC LIMIT 5
    - SELECT "Product Name", "Units Sold" FROM "customer_360" ORDER BY "Units Sold" DESC LIMIT 10
    - SELECT "Category", "Total Revenue" FROM "customer_360" ORDER BY "Total Revenue" DESC

    Args:
        sql: SQL query using the semantic model column names listed above.

    Returns:
        Dictionary with:
        - columns: list of column names
        - rows: list of row dictionaries
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

    Returns available dimensions, metrics, and example queries.
    """
    return {
        "model_name": "customer_360",
        "catalog": "customer_360_catalog_main",
        "description": "Unified Customer 360 model with all data in Amazon Redshift",
        "dimensions": {
            "Customer Name": "Full name of the customer",
            "First Name": "Customer first name",
            "Last Name": "Customer last name",
            "Email": "Customer email address",
            "Phone": "Customer phone number",
            "State": "Customer state (geographic)",
            "City": "Customer city",
            "Zip Code": "Postal code",
            "Product Name": "Name of product purchased",
            "Brand": "Product brand",
            "List Price": "Product list price",
            "Category": "Product category/department",
            "Vendor Name": "Vendor/supplier name",
            "Industry": "Vendor industry",
        },
        "metrics": {
            "Total Revenue": "SUM(price * quantity) — total sales dollars",
            "Order Count": "Count of purchase transactions",
            "Units Sold": "SUM(quantity) — total items sold",
            "Distinct Customers": "Count of unique customers",
        },
        "example_queries": [
            'SELECT "Customer Name", "State", "Total Revenue" FROM "customer_360" ORDER BY "Total Revenue" DESC LIMIT 10',
            'SELECT "State", "Total Revenue", "Distinct Customers" FROM "customer_360" ORDER BY "Total Revenue" DESC',
            'SELECT "Product Name", "Units Sold", "Total Revenue" FROM "customer_360" ORDER BY "Units Sold" DESC LIMIT 10',
        ],
    }
