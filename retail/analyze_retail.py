"""Analyze UCI Online Retail; retain signed credits and report exclusions."""
import argparse, csv, hashlib, json, sqlite3
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from datetime import datetime
from openpyxl import load_workbook
BASE=Path(__file__).parent

def prepare(rows):
    seen=set(); counts=Counter(); records=[]
    for values in rows:
        counts['source_rows']+=1
        key=tuple(values)
        if key in seen:
            counts['exact_duplicates']+=1; continue
        seen.add(key)
        invoice,stock,description,quantity,when,price,customer,country=values
        if not invoice or not stock or not isinstance(when,datetime) or not country:
            counts['invalid_identity_date_country']+=1; continue
        try:
            quantity=Decimal(str(quantity)); price=Decimal(str(price))
            if not quantity.is_finite() or not price.is_finite() or quantity!=quantity.to_integral_value():
                raise ValueError('Invalid numeric value')
            if price<=0 or quantity==0:
                counts['nonpositive_price_or_zero_quantity']+=1;continue
        except (ValueError,ArithmeticError):
            counts['invalid_numeric']+=1;continue
        amount=int((quantity*price*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
        counts['kept_rows']+=1
        if customer is None:counts['kept_missing_customer']+=1
        if amount<0:counts['credit_or_adjustment_lines']+=1
        records.append((str(invoice),str(stock),str(description or 'Unknown'),when.strftime('%Y-%m-%d'),str(country),int(quantity),amount))
    return records,dict(counts)

def run(source):
    workbook=load_workbook(source,read_only=True,data_only=True)
    iterator=workbook.active.iter_rows(values_only=True);headers=next(iterator)
    if tuple(headers)!=('InvoiceNo','StockCode','Description','Quantity','InvoiceDate','UnitPrice','CustomerID','Country'):
        raise ValueError('Unexpected source schema')
    records,quality=prepare(iterator);workbook.close()
    out=BASE/'output';out.mkdir(exist_ok=True)
    with sqlite3.connect(out/'retail.db') as db:
        db.execute('DROP TABLE IF EXISTS lines')
        db.execute('CREATE TABLE lines(invoice TEXT,stock TEXT,description TEXT,day TEXT,country TEXT,quantity INTEGER,amount_pence INTEGER)')
        db.executemany('INSERT INTO lines VALUES (?,?,?,?,?,?,?)',records)
        db.row_factory=sqlite3.Row
        queries=(BASE/'queries.sql').read_text().split(';')
        result=[[dict(r) for r in db.execute(q)] for q in queries if q.strip()]
    payload={'source':'UCI Online Retail, Daqing Chen (2015), CC BY 4.0','source_url':'https://archive.ics.uci.edu/dataset/352/online-retail','period':'2010-12-01 to 2011-12-09','sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'quality':quality,'monthly_country':result[0],'products':result[1],'totals':result[2][0]}
    (out/'report.json').write_text(json.dumps(payload,indent=2)+'\n')
    for name,rows in [('monthly_country',result[0]),('top_products',result[1])]:
        with (out/(name+'.csv')).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    print(json.dumps({'quality':quality,'totals':payload['totals']},indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);run(parser.parse_args().source)
