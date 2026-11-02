import importlib.util,json
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('retail',ROOT/'retail/analyze_retail.py');retail=importlib.util.module_from_spec(spec);spec.loader.exec_module(retail)
def row(q=2,p=1.25):return ('100','A','Item',q,datetime(2011,1,1),p,None,'UK')
def test_signed_credits_and_duplicates():
    records,quality=retail.prepare([row(),row(),row(-1),row(p=0)])
    assert len(records)==2
    assert sum(r[-1] for r in records)==125
    assert quality['exact_duplicates']==1
    assert quality['nonpositive_price_or_zero_quantity']==1
    assert quality['kept_missing_customer']==2

def test_report_reconciles():
    r=json.loads((ROOT/'retail/output/report.json').read_text());q=r['quality'];t=r['totals']
    assert q['source_rows']==q['kept_rows']+q['exact_duplicates']+q['nonpositive_price_or_zero_quantity']
    assert sum(a['net_pence'] for a in r['monthly_country'])==t['net_pence']
    assert t['sales_pence']-t['credits_pence']==t['net_pence']==974813107
