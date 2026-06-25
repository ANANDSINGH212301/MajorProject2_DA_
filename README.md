# Retail Sales - SQL Analysis & KPI Dashboard

Built a normalized SQLite database from raw sales data and wrote analytical SQL (joins, CTEs, window functions) to compute key business KPIs. Query outputs are exported as CSV, ready to plug into Power BI or Excel for an interactive dashboard.

## What this project does
- Designs a simple relational schema (customers, products, orders) from flat raw data
- Writes SQL using window functions (RANK, LAG) and CTEs to compute:
  - Monthly revenue, profit, and average order value
  - Running total sales and month-over-month growth %
  - Top 5 customers by lifetime profit
  - Best-selling product per category (ranked)
  - Delivery performance by shipping mode
- Exports each query result as CSV for direct use in Power BI / Excel dashboards

## Files
- `sql_analysis.py` - builds DB, runs all queries, exports CSVs
- `retail_sales.db` - SQLite database
- `*.csv` - query results (dashboard-ready)

## How to run
```
pip install pandas
python3 sql_analysis.py
```

## Tools
SQL (SQLite), Python, Pandas, Power BI / Excel (for dashboarding on exported CSVs)
