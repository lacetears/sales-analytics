"""Analyze UCI Online Retail; retain signed credits and report exclusions."""

import argparse, csv, hashlib, json, sqlite3
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from datetime import datetime
from openpyxl import load_workbook

BASE = Path(__file__).parent


def prepare(rows):
    seen = set()
    counts = Counter()
    records = []
    for values in rows:
        counts["source_rows"] += 1
        if not isinstance(values, (tuple, list)) or len(values) != 8 or any(isinstance(v, (dict, list, set)) for v in values):
            counts["invalid_schema"] += 1
            continue
        key = tuple(values)
        if key in seen:
            counts["exact_duplicates"] += 1
            continue
        seen.add(key)
        invoice, stock, description, quantity, when, price, customer, country = values
        if not invoice or not stock or not isinstance(when, datetime) or not country:
            counts["invalid_identity_date_country"] += 1
            continue
        try:
            quantity = Decimal(str(quantity))
            price = Decimal(str(price))
            if (
                not quantity.is_finite()
                or not price.is_finite()
                or quantity != quantity.to_integral_value()
            ):
                raise ValueError("Invalid numeric value")
            if price <= 0 or quantity == 0:
                counts["nonpositive_price_or_zero_quantity"] += 1
                continue
        except (ValueError, ArithmeticError):
            counts["invalid_numeric"] += 1
            continue
        try:
            amount = int((quantity * price * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            if abs(amount) > 2**53-1 or abs(quantity) > 2**53-1:
                raise ValueError("Outside exact JavaScript integer range")
        except (ValueError, ArithmeticError):
            counts["invalid_numeric"] += 1
            continue
        counts["kept_rows"] += 1
        if customer is None:
            counts["kept_missing_customer"] += 1
        if amount < 0:
            counts["credit_or_adjustment_lines"] += 1
        records.append(
            (
                str(invoice),
                str(stock),
                str(description or "Unknown"),
                when.strftime("%Y-%m-%d"),
                str(country),
                int(quantity),
                amount,
            )
        )
    return records, dict(counts)


def render_dashboard(payload, output):
    template = (BASE / "dashboard.template.html").read_text(encoding="utf-8")
    output.write_text(template.replace("__REPORT_DATA__", json.dumps(payload).replace("<", "\\u003c")), encoding="utf-8")


def run(source, output=None):
    source = Path(source)
    workbook = load_workbook(source, read_only=True, data_only=True)
    try:
        iterator = workbook.active.iter_rows(values_only=True)
        headers = next(iterator, ())
        if tuple(headers) != (
            "InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate",
            "UnitPrice", "CustomerID", "Country",
        ):
            raise ValueError("Unexpected source schema")
        records, quality = prepare(iterator)
    finally:
        workbook.close()
    out = Path(output) if output is not None else BASE / "output"
    out.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(out / "retail.db") as db:
        db.execute("DROP TABLE IF EXISTS lines")
        db.execute(
            "CREATE TABLE lines(invoice TEXT,stock TEXT,description TEXT,day TEXT,country TEXT,quantity INTEGER,amount_pence INTEGER)"
        )
        db.executemany("INSERT INTO lines VALUES (?,?,?,?,?,?,?)", records)
        db.row_factory = sqlite3.Row
        queries = (BASE / "queries.sql").read_text().split(";")
        result = [[dict(r) for r in db.execute(q)] for q in queries if q.strip()]
    payload = {
        "source": "UCI Online Retail, Daqing Chen (2015), CC BY 4.0",
        "source_url": "https://archive.ics.uci.edu/dataset/352/online-retail",
        "period": f"{result[2][0]['first_day']} to {result[2][0]['last_day']}" if records else "No retained records",
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "quality": quality,
        "monthly_country": result[0],
        "products": result[1],
        "totals": result[2][0],
    }
    # Reconcile against cleaned source values, independently of SQL aggregation.
    expected_net = sum(record[-1] for record in records)
    totals = payload["totals"]
    if (totals["net_pence"] != expected_net
            or sum(row["net_pence"] for row in payload["monthly_country"]) != expected_net
            or totals["sales_pence"] - totals["credits_pence"] != expected_net):
        raise ValueError("Aggregation failed source reconciliation")
    excluded = sum(quality.get(k, 0) for k in ("exact_duplicates", "invalid_schema", "invalid_identity_date_country", "nonpositive_price_or_zero_quantity", "invalid_numeric"))
    if quality.get("source_rows", 0) != quality.get("kept_rows", 0) + excluded:
        raise ValueError("Row accounting mismatch")
    if any(abs(totals[k]) > 2**53-1 for k in ("sales_pence", "credits_pence", "net_pence")):
        raise ValueError("Aggregate outside exact dashboard integer range")
    (out / "report.json").write_text(json.dumps(payload, indent=2) + "\n")
    for name, rows in [("monthly_country", result[0]), ("top_products", result[1])]:
        with (out / (name + ".csv")).open("w", newline="") as f:
            w = csv.DictWriter(f, lineterminator="\n", fieldnames=(list(rows[0]) if rows else (["month","country","sales_pence","credits_pence","net_pence","sales_invoices","lines"] if name == "monthly_country" else ["stock","description","net_pence","net_units"])))
            w.writeheader()
            w.writerows(rows)
    render_dashboard(payload, out / "dashboard.html")
    print(json.dumps({"quality": quality, "totals": payload["totals"]}, indent=2))
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        run(args.source, args.output)
    except (OSError, ValueError) as error:
        parser.exit(2, f"Error: {error}\n")
