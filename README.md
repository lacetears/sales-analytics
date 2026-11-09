# Retail Sales Analysis

A reproducible Python/SQL analysis of UCI Online Retail transactions, with a generated HTML dashboard. The question: how do positive sales and credits vary by country and month, and what does cleaning exclude?

**Python · SQLite · SQL · Decimal · openpyxl · JavaScript**

## Reproduce the real-data report

Python 3.12 or 3.13 and Node.js 22+ for dashboard tests:

```sh
python -m venv .venv
# Activate .venv for your shell, then:
python -m pip install -r requirements.txt
python retail/download.py
python retail/analyze_retail.py "retail/source/Online Retail.xlsx"
python -m pytest -q
node tests/test_retail_dashboard.cjs
```

Open `retail/output/dashboard.html`. `--output PATH` writes a separate report directory. The original workbook is not committed. Download requires network access. The SHA-256 of the workbook is recorded in `report.json`; reruns using identical source bytes are deterministic.

## Architecture

Workbook → schema/type validation and cleaning → signed integer pence → SQLite → SQL aggregates → reconciliation → JSON/CSV and generated HTML.

`retail/analyze_retail.py` closes workbooks even on errors, accepts an output directory and regenerates the dashboard from `retail/dashboard.template.html`. Quality counts and period come from the current report, not hardcoded values. Empty input produces zero totals and header-only CSV files. Embedded JSON escapes `<`, and product descriptions enter the DOM as text.

The dashboard supports combined country/month filters, exact pence display, negative-value bars and empty selections. The top-product table is explicitly a full-period reference and does not respond to filters. Quality counts also refer to the full source.

## Verified dataset results

- 541,909 source rows; 5,268 exact duplicates; 2,512 nonpositive-price/zero-quantity exclusions; 534,129 retained lines.
- Positive sales £10,642,110.80, credits/adjustments £893,979.73, net transaction value £9,748,131.07.
- December 2011 includes only nine days; comparing it directly with a full month would mislead.

These are historical dataset calculations, not business impact or audited revenue. No profit is calculated: the real dataset has no cost field. One row is an invoice line; invoice counts use distinct invoice numbers. Postage and adjustment stock codes remain included, so the top-products table is more precisely a stock-code ranking.

## Methodology and quality controls

Keep signed credits and missing customer IDs, remove exact source duplicates, reject invalid identities/dates/numerics, and round each line half-up to pence. Exact duplicate removal is an assumption: identical rows could be legitimate repeated purchases. Source rows reconcile to retained and excluded rows; SQL totals reconcile to an independent Python sum and monthly-country totals. Monetary values are bounded to preserve exact integers in the browser.

See [detailed methodology and attribution](retail/README.md). Source: Chen, D. (2015), [Online Retail](https://archive.ics.uci.edu/dataset/352/online-retail), [DOI](https://doi.org/10.24432/C5BW33), CC BY 4.0. Published outputs omit customer IDs.

## Synthetic exercise

`data-analytics/` is a separate, clearly labeled electronics-sales fixture. It models one product per order, completed-order revenue, discounts and gross profit using integer cents. Returns/cancellations recognize zero revenue/cost in this simplified model; it is not the retail credit-accounting model.

```sh
python data-analytics/generate_data.py
python data-analytics/analyze.py
node tests/test_dashboard.cjs
```

Missing CSV fields and conflicting duplicate order IDs are rejected. The first valid record for an order ID is retained; normalized identical duplicates are counted separately.

## Tests and limits

Python tests exercise fresh XLSX-to-report runs, signed credits, rounding, malformed rows, empty data, bad headers, output determinism, HTML embedding and synthetic source reconciliation. JavaScript tests execute generated scripts with a minimal DOM; they are not visual browser or accessibility tests. CI runs both Python versions, the synthetic pipeline, both dashboard suites and verifies committed HTML matches the retail report/template. A manual CI workflow can download and reconcile the full source.

[Earlier published dashboard](https://lacetears.github.io/it-career-portfolio/sales.html) and [existing screenshot](docs/screenshot.jpg) can lag this branch until the portfolio hub is updated. A Power BI guide/DAX example is included, but no PBIX or verified Power BI deployment is claimed.

## Next steps

Add source-level event/line identifiers if available, evaluate duplicate-removal sensitivity, and add a dated analysis of one business question. The batch pipeline keeps cleaned rows in memory and is not designed for warehouse scale. See [security notes](SECURITY.md).
