# Rebuild the dashboard in Power BI Desktop
A native .pbix is not included. The delivered interactive report is `output/dashboard.html`. These are implementation instructions and measures, not evidence of a completed Power BI deployment.

1. Run the Python data pipeline from the repository root.
2. In Power BI Desktop choose Get data → Text/CSV → `output/clean_sales.csv`.
3. Name the table **Sales**. Use Transform Data to set `order_date` to Date, identifiers and categories to Text, and all quantity, percentage, and cents fields to Whole Number.
4. Add each measure in `measures.dax` separately. Format revenue, profit, and average order value as USD; margin and return rate as percentages.
5. Add cards for Net Revenue, Gross Profit, Completed Orders, and Gross Margin.
6. Add a column chart with order_date by year/month on the axis and Net Revenue as values. Use chronological sorting.
7. Add a product table with product, Net Revenue, and Gross Profit. Add region and product slicers affecting all visuals.
8. Compare totals against `output/findings.md` and monthly values against `output/query_results.json`. Verify each slicer changes all cards and visuals. Save as `sales-performance.pbix`.

## Excel workflow
Open `output/clean_sales.csv` with Data → From Text/CSV. Confirm the date and integer column types. Load as a table; create a PivotTable with product as Rows and net_revenue_cents as Sum. Divide cents by 100 for dollar presentation. Filter status to Completed. Compare the grand total to the findings report. This repository includes CSV inputs, not an authored Excel workbook.
