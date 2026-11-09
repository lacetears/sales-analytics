import importlib.util, json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "retail", ROOT / "retail/analyze_retail.py"
)
retail = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retail)


def row(q=2, p=1.25):
    return ("100", "A", "Item", q, datetime(2011, 1, 1), p, None, "UK")


def test_signed_credits_and_duplicates():
    records, quality = retail.prepare([row(), row(), row(-1), row(p=0)])
    assert len(records) == 2
    assert sum(r[-1] for r in records) == 125
    assert quality["exact_duplicates"] == 1
    assert quality["nonpositive_price_or_zero_quantity"] == 1
    assert quality["kept_missing_customer"] == 2


def test_report_reconciles():
    r = json.loads((ROOT / "retail/output/report.json").read_text())
    q = r["quality"]
    t = r["totals"]
    assert (
        q["source_rows"]
        == q["kept_rows"]
        + q["exact_duplicates"]
        + q["nonpositive_price_or_zero_quantity"]
    )
    assert sum(a["net_pence"] for a in r["monthly_country"]) == t["net_pence"]
    assert t["sales_pence"] - t["credits_pence"] == t["net_pence"] == 974813107


def workbook(path, rows):
    from openpyxl import Workbook
    book=Workbook(); sheet=book.active
    sheet.append(('InvoiceNo','StockCode','Description','Quantity','InvoiceDate','UnitPrice','CustomerID','Country'))
    for values in rows: sheet.append(values)
    book.save(path); book.close()


def test_pipeline_from_workbook_and_dashboard(tmp_path):
    source=tmp_path/'source.xlsx'; out=tmp_path/'out'
    workbook(source,[row(),row(),row(-1),row(p=0)])
    report=retail.run(source,out)
    assert report['totals']['net_pence']==125
    assert report['period']=='2011-01-01 to 2011-01-01'
    assert report['quality']['source_rows']==4
    html=(out/'dashboard.html').read_text()
    embedded=json.loads(html.split('const report=',1)[1].split(';const rows=',1)[0])
    assert embedded==report
    assert '541,909' not in html and '__REPORT_DATA__' not in html
    original=(out/'report.json').read_bytes()
    retail.run(source,out)
    assert (out/'report.json').read_bytes()==original


def test_empty_workbook(tmp_path):
    source=tmp_path/'empty.xlsx'; workbook(source,[])
    report=retail.run(source,tmp_path/'out')
    assert report['totals']['net_pence']==0
    assert report['monthly_country']==[]
    assert (tmp_path/'out/top_products.csv').read_text().startswith('stock,description')


def test_bad_rows_and_rounding():
    records,quality=retail.prepare([(),None,row(p=float('nan')),row(q=1.5),row(q=1,p=1.005),row(q=-1,p=1.005),row(p=1e100)])
    assert quality['invalid_schema']==2
    assert quality['invalid_numeric']==3
    assert [r[-1] for r in records]==[101,-101]


def test_bad_headers(tmp_path):
    import pytest
    from openpyxl import Workbook
    source=tmp_path/'bad.xlsx'; book=Workbook();book.active.append(['wrong']);book.save(source);book.close()
    with pytest.raises(ValueError,match='schema'):retail.run(source,tmp_path/'out')
    assert not (tmp_path/'out/report.json').exists()


def test_script_injection_escaped(tmp_path):
    payload={'products':[{'description':'</script><script>alert(1)</script>'}], 'monthly_country':[]}
    output=tmp_path/'report.html';retail.render_dashboard(payload,output)
    assert '</script><script>alert(1)</script>' not in output.read_text()
