"""Reproducible synthetic sales data with deliberate quality issues."""
import csv,random
from pathlib import Path
from datetime import date,timedelta
BASE=Path(__file__).parent
PRODUCTS=[('Laptop',89900,64000),('Monitor',24900,15500),('Keyboard',6900,2800),('Dock',12900,6500)]
def generate():
    rng=random.Random(42); rows=[]
    for i in range(1200):
        product,price,cost=rng.choice(PRODUCTS)
        rows.append(dict(order_id=f'ORD-{i+1:05}',order_date=str(date(2025,1,1)+timedelta(days=rng.randrange(365))),region=rng.choice(['North','South','East','West']),product=product,quantity=rng.randint(1,5),unit_price_cents=price,unit_cost_cents=cost,discount_pct=rng.choice([0,0,5,10,15]),status=rng.choices(['Completed','Returned','Cancelled'],[88,8,4])[0]))
    for r in rows[:20]: r['region']=' '+r['region'].lower()+' '
    dirty=rows+[dict(r) for r in rows[:10]]
    dirty.append(dict(rows[0],order_id='BAD-001',quantity=-2))
    dirty.append(dict(rows[0],order_id='BAD-002',order_date='not-a-date'))
    dirty.append(dict(rows[0],order_id='BAD-003',region=''))
    BASE.joinpath('data').mkdir(exist_ok=True)
    with BASE.joinpath('data/raw_sales.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(dirty)
if __name__=='__main__': generate()
