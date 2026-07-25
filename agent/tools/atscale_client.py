"""AtScale client — connects via PostgreSQL wire protocol (port 15432)."""

import os
import psycopg2
from typing import Optional


class AtScaleClient:
    """Client for querying AtScale semantic layer via PostgreSQL protocol."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.host = host or os.environ.get(
            "ATSCALE_HOST",
            "k8s-atscale-atscalei-ba4358e717-dc18b0c39e9fcefe.elb.us-east-1.amazonaws.com",
        )
        self.port = port or int(os.environ.get("ATSCALE_PORT", "15432"))
        self.database = database or os.environ.get(
            "ATSCALE_DATABASE", "customer_360_catalog_main"
        )
        self.username = username or os.environ.get("ATSCALE_USERNAME", "atscale-kc-admin")
        self.password = password or os.environ.get("ATSCALE_PASSWORD", "")

    def _get_connection(self):
        """Create a new database connection."""
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.database,
            user=self.username,
            password=self.password,
            sslmode="require",
            connect_timeout=30,
        )

    def execute_query(self, sql: str) -> dict:
        """
        Execute a SQL query against the AtScale semantic model.

        Args:
            sql: SQL query using semantic model dimensions and measures.

        Returns:
            dict with keys: columns, rows, row_count, sql_used, success
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(sql)

            # Get column names
            columns = [desc[0] for desc in cur.description] if cur.description else []

            # Get rows
            rows = cur.fetchall()

            # Convert to list of dicts for easier consumption
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))

            cur.close()
            conn.close()

            return {
                "columns": columns,
                "rows": results,
                "row_count": len(results),
                "sql_used": sql,
                "success": True,
            }

        except psycopg2.OperationalError as e:
            return {
                "columns": [],
                "rows": [],
                "row_count": 0,
                "sql_used": sql,
                "success": False,
                "error": f"Connection error: {str(e)}",
            }
        except psycopg2.Error as e:
            return {
                "columns": [],
                "rows": [],
                "row_count": 0,
                "sql_used": sql,
                "success": False,
                "error": f"Query error: {str(e)}",
            }
        except Exception as e:
            return {
                "columns": [],
                "rows": [],
                "row_count": 0,
                "sql_used": sql,
                "success": False,
                "error": str(e),
            }

    def health_check(self) -> bool:
        """Check if AtScale is reachable and healthy."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            conn.close()
            return True
        except Exception:
            return False
