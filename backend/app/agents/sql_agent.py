"""
SQL agent — natural language -> SQL -> KPI computation.

Deliberately keyword/entity driven rather than a raw "LLM writes arbitrary
SQL" chain: it only ever composes queries from a small set of vetted
templates, which keeps the demo safe to run (no SQL injection surface) and
keeps token cost near zero for the common-case questions BI teams actually
ask. Swap `_build_query` for a LangChain SQL toolkit + schema-aware prompt
if you need fully open-ended querying.
"""
import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "warehouse.db"

REGIONS = ["northeast", "southeast", "midwest", "west"]
QUARTERS = ["2026-q1", "2026-q2"]


def _extract_entities(query: str) -> dict:
    q = query.lower()
    region = next((r for r in REGIONS if r in q), None)
    quarter = next((qq for qq in QUARTERS if qq.replace("-", " ") in q or qq in q), None)
    return {"region": region.title() if region else None, "quarter": quarter.upper() if quarter else None}


def _build_query(entities: dict) -> tuple[str, list]:
    where, params = [], []
    if entities.get("region"):
        where.append("region = ?")
        params.append(entities["region"])
    if entities.get("quarter"):
        where.append("quarter = ?")
        params.append(entities["quarter"])
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    sql = (
        "SELECT region, quarter, SUM(units_sold) AS units, "
        "SUM(revenue_usd) AS revenue, SUM(target_revenue_usd) AS target "
        f"FROM sales {clause} GROUP BY region, quarter ORDER BY region, quarter"
    )
    return sql, params


async def run_sql_agent(state: dict) -> dict:
    entities = _extract_entities(state["user_query"])
    sql, params = _build_query(entities)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    conn.close()

    for r in rows:
        r["attainment_pct"] = round(100 * r["revenue"] / r["target"], 1) if r["target"] else None
        r["yoy_or_qoq_flag"] = "below_target" if r["attainment_pct"] and r["attainment_pct"] < 95 else "on_track"

    return {"sql_result": {"sql": sql, "params": params, "rows": rows, "entities": entities}}
