# Sales Data Analysis & Dashboard
A deterministic synthetic retail dataset, a cleaning pipeline, SQLite queries, and a filterable dashboard.

## Run
```sh
python data-analytics/generate_data.py
python data-analytics/analyze.py
```
Open `output/dashboard.html`. Region and product filters update all cards, monthly bars, the product table, and outcome counts. No internet connection is needed to view it.

## Data and methodology
`data/raw_sales.csv` contains 1,213 rows: 1,200 valid orders, 10 duplicate IDs and 3 invalid rows. Twenty region values deliberately contain whitespace and inconsistent casing. Seed 42 makes the generator reproducible. One row is one order with one product line; real multi-line orders require a different order-count calculation.

The pipeline validates dates, categories and numeric ranges; normalizes regions; keeps the first valid instance of an ID; and records rejected rows with reasons. Duplicate IDs are counted, not assumed to be additional sales. The reject report retains raw synthetic rows for audit.

Revenue is quantity × unit price × (1 − discount), rounded half-up to integer cents per order. Completed orders alone recognize revenue and cost. Returned/cancelled orders contribute zero. Gross profit excludes shipping, taxes, operating expenses and return-processing costs. This is an analytical convention for the example, not accounting guidance.

## Outputs
- `clean_sales.csv`: validated records and derived integer-cent measures; import into Excel or Power BI.
- `sales.db`: regenerated SQLite database (ignored by Git).
- `quality_report.json`: row reconciliation and rejection reasons.
- `query_results.json`: SQL monthly, product, and region aggregates.
- `findings.md`: generated observations and limitations.
- `dashboard.html`: interactive report, independently usable in a browser.

The SQL source is `queries.sql`. See `powerbi/` for DAX measures and native Power BI/Excel completion steps. No `.pbix` or Excel workbook is included.

## Data dictionary
| Column | Meaning |
| --- | --- |
| order_id | Unique synthetic order identifier |
| order_date | ISO date within 2025 |
| region | North, South, East or West |
| product | Laptop, Monitor, Keyboard or Dock |
| quantity | Positive integer units |
| unit_price_cents / unit_cost_cents | Nonnegative USD cents per unit |
| discount_pct | Whole-number percentage, 0–100 |
| status | Completed, Returned or Cancelled |
| net_revenue_cents / gross_profit_cents | Derived recognized measures in cents |
