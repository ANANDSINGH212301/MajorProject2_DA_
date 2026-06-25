"""
sql_analysis.py
Project 2: Loads the cleaned retail sales data into a SQLite database
and runs analytical SQL queries (joins, CTEs, window functions) to
compute business KPIs. Also exports results to CSV for a BI tool
(Power BI / Excel) to build a dashboard on top of.
"""
import pandas as pd
import sqlite3

# --- Load and reuse the cleaned data from Project 1 ---
df = pd.read_csv("../retail_sales_raw.csv", parse_dates=["Order_Date", "Ship_Date"])

# quick clean (same logic as EDA project, condensed)
df = df.drop_duplicates()
for col in ["Region", "Category", "Sub_Category", "Segment", "Ship_Mode"]:
    df[col] = df[col].astype(str).str.strip().str.title().replace("Nan", None)
df["Quantity"] = df["Quantity"].abs()
df["Discount"] = df["Discount"].fillna(0)
df = df.dropna(subset=["Region", "Ship_Mode"])
avg_margin = (df["Profit"] / df["Sales"]).mean()
df.loc[df["Profit"].isna(), "Profit"] = df["Sales"] * avg_margin

# --- Build normalized tables (simulate a real relational schema) ---
customers = df[["Customer_ID", "Segment", "Region"]].drop_duplicates(subset="Customer_ID").reset_index(drop=True)
products = df[["Category", "Sub_Category"]].drop_duplicates().reset_index(drop=True)
products["Product_ID"] = ["PROD-" + str(i+1).zfill(4) for i in range(len(products))]

orders = df.merge(products, on=["Category", "Sub_Category"], how="left")
orders = orders[["Order_ID", "Order_Date", "Ship_Date", "Customer_ID", "Product_ID",
                  "Ship_Mode", "Quantity", "Unit_Price", "Discount", "Sales", "Profit"]]

# --- Write to SQLite ---
conn = sqlite3.connect("retail_sales.db")
customers.to_sql("customers", conn, if_exists="replace", index=False)
products.to_sql("products", conn, if_exists="replace", index=False)
orders.to_sql("orders", conn, if_exists="replace", index=False)
conn.commit()

print("Database built. Tables:", customers.shape, products.shape, orders.shape)

# ============================================================
# ANALYTICAL SQL QUERIES
# ============================================================

queries = {}

queries["monthly_revenue_kpi"] = """
SELECT
    strftime('%Y-%m', Order_Date) AS month,
    ROUND(SUM(Sales), 2) AS total_sales,
    ROUND(SUM(Profit), 2) AS total_profit,
    COUNT(DISTINCT Order_ID) AS total_orders,
    ROUND(SUM(Sales) / COUNT(DISTINCT Order_ID), 2) AS avg_order_value
FROM orders
GROUP BY month
ORDER BY month;
"""

# Window function: running total of sales + month-over-month growth %
queries["running_total_and_growth"] = """
WITH monthly AS (
    SELECT
        strftime('%Y-%m', Order_Date) AS month,
        SUM(Sales) AS total_sales
    FROM orders
    GROUP BY month
)
SELECT
    month,
    total_sales,
    ROUND(SUM(total_sales) OVER (ORDER BY month), 2) AS running_total_sales,
    ROUND(
        (total_sales - LAG(total_sales) OVER (ORDER BY month))
        / LAG(total_sales) OVER (ORDER BY month) * 100
    , 2) AS mom_growth_pct
FROM monthly
ORDER BY month;
"""

# Joins + CTE: top 5 customers by lifetime profit, with their region/segment
queries["top_customers_by_profit"] = """
WITH customer_profit AS (
    SELECT
        o.Customer_ID,
        SUM(o.Sales) AS lifetime_sales,
        SUM(o.Profit) AS lifetime_profit,
        COUNT(DISTINCT o.Order_ID) AS total_orders
    FROM orders o
    GROUP BY o.Customer_ID
)
SELECT
    cp.Customer_ID,
    c.Segment,
    c.Region,
    cp.total_orders,
    ROUND(cp.lifetime_sales, 2) AS lifetime_sales,
    ROUND(cp.lifetime_profit, 2) AS lifetime_profit
FROM customer_profit cp
JOIN customers c ON cp.Customer_ID = c.Customer_ID
ORDER BY cp.lifetime_profit DESC
LIMIT 5;
"""

# Rank products within each category by total revenue (window function)
queries["top_product_per_category"] = """
WITH product_sales AS (
    SELECT
        p.Category,
        p.Sub_Category,
        SUM(o.Sales) AS total_sales,
        SUM(o.Profit) AS total_profit
    FROM orders o
    JOIN products p ON o.Product_ID = p.Product_ID
    GROUP BY p.Category, p.Sub_Category
)
SELECT *
FROM (
    SELECT
        Category,
        Sub_Category,
        ROUND(total_sales, 2) AS total_sales,
        ROUND(total_profit, 2) AS total_profit,
        RANK() OVER (PARTITION BY Category ORDER BY total_sales DESC) AS rank_in_category
    FROM product_sales
)
WHERE rank_in_category = 1;
"""

# Delivery performance KPI by ship mode
queries["delivery_performance"] = """
SELECT
    Ship_Mode,
    ROUND(AVG(JULIANDAY(Ship_Date) - JULIANDAY(Order_Date)), 2) AS avg_delivery_days,
    COUNT(*) AS total_orders
FROM orders
GROUP BY Ship_Mode
ORDER BY avg_delivery_days;
"""

print("\n" + "="*60)
for name, query in queries.items():
    print(f"\n--- {name} ---")
    result = pd.read_sql_query(query, conn)
    print(result.head(10))
    # export for Power BI / Excel dashboard
    result.to_csv(f"{name}.csv", index=False)

conn.close()
print("\nAll query results exported as CSV for dashboarding (Power BI / Excel ready).")
