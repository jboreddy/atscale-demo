"""AtScale REST API client for querying the semantic layer."""

import os
import requests
from typing import Optional


class AtScaleClient:
    """Client for querying AtScale semantic layer via REST API."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        model_name: str = "customer_360",
    ):
        self.endpoint = endpoint or os.environ.get(
            "ATSCALE_URL", "http://localhost:10500"
        )
        self.username = username or os.environ.get("ATSCALE_USERNAME", "admin")
        self.password = password or os.environ.get("ATSCALE_PASSWORD", "admin")
        self.model_name = model_name
        self._token: Optional[str] = None

    def _authenticate(self) -> str:
        """Get authentication token."""
        if self._token:
            return self._token

        response = requests.post(
            f"{self.endpoint}/api/1.0/auth/login",
            json={"username": self.username, "password": self.password},
            timeout=10,
        )
        response.raise_for_status()
        self._token = response.json().get("token")
        return self._token

    def _headers(self) -> dict:
        """Get authenticated headers."""
        token = self._authenticate()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def execute_query(self, sql: str) -> dict:
        """
        Execute a SQL query against the AtScale semantic model.

        Args:
            sql: SQL query using semantic model dimensions and measures.

        Returns:
            dict with keys: columns, rows, row_count, sql_used
        """
        try:
            response = requests.post(
                f"{self.endpoint}/api/1.0/query",
                headers=self._headers(),
                json={
                    "query": sql,
                    "catalog": self.model_name,
                    "schema": "public",
                },
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            return {
                "columns": result.get("columns", []),
                "rows": result.get("rows", []),
                "row_count": len(result.get("rows", [])),
                "sql_used": sql,
                "success": True,
            }

        except requests.Timeout:
            return {
                "columns": [],
                "rows": [],
                "row_count": 0,
                "sql_used": sql,
                "success": False,
                "error": "Query timed out after 30 seconds",
            }
        except requests.HTTPError as e:
            return {
                "columns": [],
                "rows": [],
                "row_count": 0,
                "sql_used": sql,
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
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

    def get_model_metadata(self) -> dict:
        """Get metadata about the semantic model (dimensions, measures)."""
        try:
            response = requests.get(
                f"{self.endpoint}/api/1.0/catalogs/{self.model_name}",
                headers=self._headers(),
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def health_check(self) -> bool:
        """Check if AtScale is reachable and healthy."""
        try:
            response = requests.get(
                f"{self.endpoint}/health",
                timeout=5,
            )
            return response.status_code == 200
        except Exception:
            return False
