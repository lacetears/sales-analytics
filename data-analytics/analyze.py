import csv, json, sqlite3
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

BASE = Path(__file__).parent
FIELDS = [
    "order_id",
    "order_date",
    "region",
    "product",
    "quantity",
    "unit_price_cents",
    "unit_cost_cents",
    "discount_pct",
    "status",
    "net_revenue_cents",
    "gross_profit_cents",
]


def clean(rows):
    seen = {}
    good = []
    rejects = []
    duplicates = 0
    for number, raw in enumerate(rows, 2):
        try:
            row = dict(raw)
            if set(row) != set(FIELDS[:9]) or any(value is None for value in row.values()):
                raise ValueError("Unexpected or missing CSV fields")
            row["order_id"] = row["order_id"].strip()
            if not row["order_id"]:
                raise ValueError("Missing order id")
            row["order_date"] = date.fromisoformat(row["order_date"]).isoformat()
            row["region"] = row["region"].strip().title()
            if row["region"] not in ("North", "South", "East", "West"):
                raise ValueError("Invalid region")
            if row["product"] not in ("Laptop", "Monitor", "Keyboard", "Dock"):
                raise ValueError("Invalid product")
            if row["status"] not in ("Completed", "Returned", "Cancelled"):
                raise ValueError("Invalid status")
            for k in (
                "quantity",
                "unit_price_cents",
                "unit_cost_cents",
                "discount_pct",
            ):
                row[k] = int(row[k])
            if (
                row["quantity"] <= 0
                or min(row["unit_price_cents"], row["unit_cost_cents"]) < 0
                or not 0 <= row["discount_pct"] <= 100
            ):
                raise ValueError("Invalid numeric range")
            if row["order_id"] in seen:
                if row != seen[row["order_id"]]:
                    raise ValueError("Conflicting duplicate order id")
                duplicates += 1
                continue
            seen[row["order_id"]] = dict(row)
            amount = (
                Decimal(row["quantity"] * row["unit_price_cents"])
                * (100 - row["discount_pct"])
                / 100
            )
            revenue = (
                int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
                if row["status"] == "Completed"
                else 0
            )
            row["net_revenue_cents"] = revenue
            row["gross_profit_cents"] = (
                revenue - row["quantity"] * row["unit_cost_cents"]
                if row["status"] == "Completed"
                else 0
            )
            good.append(row)
        except (ValueError, KeyError, TypeError, AttributeError, ArithmeticError) as error:
            rejects.append(dict(csv_row=number, reason=str(error), raw=raw))
    return good, rejects, duplicates


def main():
    out = BASE / "output"
    out.mkdir(exist_ok=True)
    with (BASE / "data/raw_sales.csv").open() as f:
        raw = list(csv.DictReader(f))
    rows, rejects, duplicates = clean(raw)
    with (out / "clean_sales.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with sqlite3.connect(out / "sales.db") as db:
        db.execute("DROP TABLE IF EXISTS sales")
        db.execute(
            "CREATE TABLE sales ("
            + ", ".join(
                k + (" INTEGER" if k in FIELDS[4:8] + FIELDS[9:] else " TEXT")
                for k in FIELDS
            )
            + ", PRIMARY KEY(order_id))"
        )
        db.executemany(
            "INSERT INTO sales VALUES (" + ",".join("?" for _ in FIELDS) + ")",
            [[r[k] for k in FIELDS] for r in rows],
        )
        db.row_factory = sqlite3.Row
        results = []
        for sql in (BASE / "queries.sql").read_text().split(";"):
            if sql.strip():
                results.append([dict(r) for r in db.execute(sql)])
    quality = dict(
        input_rows=len(raw),
        valid_rows=len(rows),
        duplicate_rows=duplicates,
        rejected_rows=len(rejects),
        rejects=rejects,
    )
    (out / "quality_report.json").write_text(json.dumps(quality, indent=2) + "\n")
    (out / "query_results.json").write_text(
        json.dumps(
            dict(monthly=results[0], products=results[1], regions=results[2]), indent=2
        )
        + "\n"
    )
    template = (BASE / "dashboard.template.html").read_text()
    (out / "dashboard.html").write_text(
        template.replace("__SALES_DATA__", json.dumps(rows).replace("<", "\\u003c"))
    )
    total = sum(r["net_revenue_cents"] for r in rows)
    profit = sum(r["gross_profit_cents"] for r in rows)
    best = results[1][0] if results[1] else {"product": "None", "revenue_usd": 0}
    month = max(results[0], key=lambda r: r["revenue_usd"]) if results[0] else {"month": "None", "revenue_usd": 0}
    (out / "findings.md").write_text(
        f'# Sales findings\n\nSynthetic 2025 dataset, generated with seed 42. Not real company results.\n\n- {len(raw):,} input rows; {len(rows):,} valid orders; {duplicates} duplicates removed; {len(rejects)} rows rejected.\n- Recognized revenue: ${total/100:,.2f}. Gross profit: ${profit/100:,.2f}.\n- Highest-revenue product: {best["product"]}, ${best["revenue_usd"]:,.2f}.\n- Highest-revenue month: {month["month"]}, ${month["revenue_usd"]:,.2f}.\n\nInvestigate product mix and discounting by region before changing inventory. These descriptive results do not establish causes or predict demand. Gross profit excludes operating expenses, tax, shipping, and return-processing costs.\n'
    )
    print(json.dumps({k: v for k, v in quality.items() if k != "rejects"}))
    print(f"Revenue ${total/100:,.2f}; gross profit ${profit/100:,.2f}")


if __name__ == "__main__":
    main()
