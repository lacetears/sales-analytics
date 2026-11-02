# Real-data analysis: UCI Online Retail

Source: Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33. Licensed CC BY 4.0: https://creativecommons.org/licenses/by/4.0/.

The source covers 2010-12-01 through 2011-12-09. It contains historical transactions from a UK retailer. It is not current or real-time data.

## Reproduce
```sh
python -m pip install -r requirements.txt
python retail/download.py
python retail/analyze_retail.py "retail/source/Online Retail.xlsx"
```
The original workbook is not committed. Its SHA-256 checksum is recorded in `output/report.json`. The derived summaries are committed and contain no customer IDs.

## Cleaning decisions
- Remove exact duplicate source rows across all eight original columns. This may remove genuinely repeated lines that happen to be identical; treat this as an analytical assumption.
- Exclude prices <= 0 and zero quantities. Keep negative quantities as credits/adjustments rather than dropping them.
- Retain missing CustomerID because customer segmentation is not part of this report. Do not infer distinct customer counts.
- Reject invalid date, invoice, stock code, country or numeric values. No such extra rejections occurred in this source run.
- Compute line amounts in pence with Decimal and round half-up per line. Values with more than two decimal places can cause small differences from unrounded analyses.
- Group monthly by invoice date as supplied, without timezone conversion.

One row is an invoice line, not an order. SQL uses distinct invoice numbers when counting invoices. Net transaction value includes signed adjustments and is not audited revenue. There is no cost field and no profit calculation. December 2011 is partial and must not be interpreted as a month-over-month sales collapse.

## Validation results
541,909 source rows = 5,268 exact duplicates + 2,512 excluded zero-quantity/nonpositive-price rows + 534,129 retained lines. Of retained lines, 132,565 have no customer ID and 9,251 have a negative amount.

Positive sales: £10,642,110.80. Credits/adjustments: £893,979.73. Net transaction value: £9,748,131.07. Sum of monthly-country groups reconciles to the independent SQL total.

## Published output
`output/report.json`, `monthly_country.csv`, and `top_products.csv` are adaptations of the source under CC BY 4.0. Filtering and aggregation are the modifications. The top-products table is a fixed full-period reference; the dashboard labels this explicitly. Other dashboard metrics and monthly bars respond to filters.
