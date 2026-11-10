import importlib.util, json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


analytics = module("analytics", "data-analytics/analyze.py")


def valid_row():
    return dict(
        order_id="A",
        order_date="2025-01-01",
        region=" north ",
        product="Laptop",
        quantity="2",
        unit_price_cents="10001",
        unit_cost_cents="5000",
        discount_pct="5",
        status="Completed",
    )


def test_cleaning_rounding_dedup():
    row = valid_row()
    good, rejected, dupes = analytics.clean(
        [row, row, dict(row, order_id="B", quantity="-1")]
    )
    assert len(good) == 1
    assert dupes == 1
    assert len(rejected) == 1
    assert good[0]["region"] == "North"
    assert good[0]["net_revenue_cents"] == 19002
    assert good[0]["gross_profit_cents"] == 9002


def test_returns_no_revenue():
    rows, _, _ = analytics.clean([dict(valid_row(), status="Returned")])
    assert rows[0]["net_revenue_cents"] == 0
    assert rows[0]["gross_profit_cents"] == 0


def test_bad_date():
    good, rejected, _ = analytics.clean([dict(valid_row(), order_date="2025-02-30")])
    assert not good
    assert len(rejected) == 1


def test_pipeline_totals():
    import csv

    rows = list(csv.DictReader((ROOT / "data-analytics/output/clean_sales.csv").open()))
    quality = json.loads(
        (ROOT / "data-analytics/output/quality_report.json").read_text()
    )
    assert (
        quality["input_rows"]
        == quality["valid_rows"] + quality["duplicate_rows"] + quality["rejected_rows"]
    )
    assert len(rows) == 1200
    assert quality["rejected_rows"] == 3
    assert quality["duplicate_rows"] == 10
    result = json.loads((ROOT / "data-analytics/output/query_results.json").read_text())
    assert round(sum(r["revenue_usd"] for r in result["monthly"]) * 100) == sum(
        int(r["net_revenue_cents"]) for r in rows
    )


def test_conflicting_order_is_rejected():
    good,rejects,dupes=analytics.clean([valid_row(),dict(valid_row(),quantity='3')])
    assert len(good)==1 and dupes==0
    assert rejects[0]['reason']=='Conflicting duplicate order id'


@pytest.mark.parametrize('bad',[dict(valid_row(),region=None),dict(valid_row(),order_id=None),dict(valid_row(),extra='unexpected')])
def test_malformed_csv(bad):
    good,rejects,dupes=analytics.clean([bad])
    assert not good and len(rejects)==1 and dupes==0


def test_fresh_pipeline_reconciles(tmp_path,monkeypatch):
    import shutil, csv
    for name in ('queries.sql','dashboard.template.html'):
        shutil.copy(ROOT/'data-analytics'/name,tmp_path/name)
    shutil.copytree(ROOT/'data-analytics/data',tmp_path/'data')
    monkeypatch.setattr(analytics,'BASE',tmp_path)
    analytics.main()
    result=json.loads((tmp_path/'output/query_results.json').read_text())
    rows,_,_=analytics.clean(csv.DictReader((tmp_path/'data/raw_sales.csv').open()))
    assert round(sum(r['revenue_usd'] for r in result['monthly'])*100)==sum(r['net_revenue_cents'] for r in rows)
    assert sum(r['orders'] for r in result['monthly'])==sum(r['status']=='Completed' for r in rows)


def test_date_normalized_before_sql_grouping():
    rows,rejects,_=analytics.clean([dict(valid_row(),order_date='20250101')])
    assert not rejects and rows[0]['order_date']=='2025-01-01'


def test_no_completed_orders(tmp_path,monkeypatch):
    import csv, shutil
    for name in ('queries.sql','dashboard.template.html'):
        shutil.copy(ROOT/'data-analytics'/name,tmp_path/name)
    (tmp_path/'data').mkdir()
    with (tmp_path/'data/raw_sales.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=valid_row().keys());writer.writeheader();writer.writerow(dict(valid_row(),status='Returned'))
    monkeypatch.setattr(analytics,'BASE',tmp_path)
    analytics.main()
    assert 'Highest-revenue product: None' in (tmp_path/'output/findings.md').read_text()
