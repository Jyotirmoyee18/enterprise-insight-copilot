"""Seeds a small SQLite warehouse with sample retail sales data so the SQL
agent has something real to query out of the box."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "warehouse.db"

REGIONS = ["Northeast", "Southeast", "Midwest", "West"]
SKUS = [
    ("SKU-1001", "Sparkling Water 12pk", "Beverages"),
    ("SKU-1002", "Organic Granola Bar", "Snacks"),
    ("SKU-1003", "Cold Brew Concentrate", "Beverages"),
    ("SKU-1004", "Protein Chips", "Snacks"),
    ("SKU-1005", "Herbal Tea Sampler", "Beverages"),
]


def seed():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript(
        """
        DROP TABLE IF EXISTS sales;
        DROP TABLE IF EXISTS inventory;

        CREATE TABLE sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT, product_name TEXT, category TEXT,
            region TEXT, quarter TEXT,
            units_sold INTEGER, revenue_usd REAL, target_revenue_usd REAL
        );

        CREATE TABLE inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT, region TEXT, quarter TEXT,
            units_on_hand INTEGER, days_of_inventory REAL
        );
        """
    )

    import random

    random.seed(42)
    quarters = ["2026-Q1", "2026-Q2"]
    for quarter in quarters:
        for region in REGIONS:
            for sku, name, category in SKUS:
                units = random.randint(800, 6000)
                revenue = round(units * random.uniform(2.5, 6.5), 2)
                target = round(revenue * random.uniform(0.85, 1.2), 2)
                cur.execute(
                    "INSERT INTO sales (sku, product_name, category, region, quarter, "
                    "units_sold, revenue_usd, target_revenue_usd) VALUES (?,?,?,?,?,?,?,?)",
                    (sku, name, category, region, quarter, units, revenue, target),
                )
                on_hand = random.randint(200, 3000)
                doi = round(on_hand / (units / 90), 1)
                cur.execute(
                    "INSERT INTO inventory (sku, region, quarter, units_on_hand, "
                    "days_of_inventory) VALUES (?,?,?,?,?)",
                    (sku, region, quarter, on_hand, doi),
                )

    conn.commit()
    conn.close()
    print(f"Seeded {DB_PATH}")


if __name__ == "__main__":
    seed()
