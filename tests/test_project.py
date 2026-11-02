import importlib.util, json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
analytics=module('analytics','data-analytics/analyze.py')

def valid_row(): return dict(order_id='A',order_date='2025-01-01',region=' north ',product='Laptop',quantity='2',unit_price_cents='10001',unit_cost_cents='5000',discount_pct='5',status='Completed')

def test_cleaning_rounding_dedup():
    row=valid_row(); good,rejected,dupes=analytics.clean([row,row,dict(row,order_id='B',quantity='-1')]);assert len(good)==1;assert dupes==1;assert len(rejected)==1;assert good[0]['region']=='North';assert good[0]['net_revenue_cents']==19002;assert good[0]['gross_profit_cents']==9002

def test_returns_no_revenue():
    rows,_,_=analytics.clean([dict(valid_row(),status='Returned')]);assert rows[0]['net_revenue_cents']==0;assert rows[0]['gross_profit_cents']==0

def test_bad_date():
    good,rejected,_=analytics.clean([dict(valid_row(),order_date='2025-02-30')]);assert not good;assert len(rejected)==1

def test_pipeline_totals():
    import csv
    rows=list(csv.DictReader((ROOT/'data-analytics/output/clean_sales.csv').open()))
    quality=json.loads((ROOT/'data-analytics/output/quality_report.json').read_text())
    assert quality['input_rows']==quality['valid_rows']+quality['duplicate_rows']+quality['rejected_rows']
    assert len(rows)==1200;assert quality['rejected_rows']==3;assert quality['duplicate_rows']==10
    result=json.loads((ROOT/'data-analytics/output/query_results.json').read_text())
    assert round(sum(r['revenue_usd'] for r in result['monthly'])*100)==sum(int(r['net_revenue_cents']) for r in rows)
