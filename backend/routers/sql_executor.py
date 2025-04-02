from typing import List, Tuple, Union, Optional, Dict, Any
import logging
from ..database import get_db_connection

logger = logging.getLogger(__name__)


def execute_sql_query(query_info: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """
    Execute a SQL query safely and return the results.
    For SELECT queries, returns a list of tuples.
    For other operations, returns the number of affected rows.
    """
    if not query_info["success"]:
        return {
            "success": False,
            "error": query_info.get("error", "Failed to generate SQL query"),
            "data": None,
        }

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        sql = query_info["sql"]
        params = query_info.get("params", {})
        operation = query_info.get("operation", "select")

        # Add user_id to params
        params["user_id"] = user_id

        logger.debug(f"Executing {operation} query: {sql}")
        logger.debug(f"Query parameters: {params}")
        cursor.execute(sql, params)

        result = {"success": True, "error": None, "operation": operation, "data": None}

        if operation.lower() == "select":
            rows = cursor.fetchall()
            result["data"] = rows
            logger.debug(f"Query returned {len(rows)} results")
        else:
            affected_rows = cursor.rowcount
            conn.commit()
            result["data"] = affected_rows
            logger.debug(f"Query affected {affected_rows} rows")

        return result

    except Exception as e:
        logger.error(f"Error executing SQL query: {e}")
        if operation.lower() != "select":
            conn.rollback()
        return {"success": False, "error": str(e), "data": None}

    finally:
        cursor.close()
        conn.close()
