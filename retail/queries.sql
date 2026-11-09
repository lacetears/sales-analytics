SELECT substr(day,1,7) month,country,
COALESCE(SUM(CASE WHEN amount_pence>0 THEN amount_pence ELSE 0 END),0) sales_pence,
-COALESCE(SUM(CASE WHEN amount_pence<0 THEN amount_pence ELSE 0 END),0) credits_pence,
COALESCE(SUM(amount_pence),0) net_pence,
COUNT(DISTINCT CASE WHEN amount_pence>0 THEN invoice END) sales_invoices,
COUNT(*) lines
FROM lines GROUP BY month,country ORDER BY month,country;
SELECT stock, MIN(description) description, COALESCE(SUM(amount_pence),0) net_pence,
SUM(quantity) net_units
FROM lines GROUP BY stock ORDER BY net_pence DESC LIMIT 10;
SELECT COUNT(*) lines,COUNT(DISTINCT invoice) invoices,
COALESCE(SUM(CASE WHEN amount_pence>0 THEN amount_pence ELSE 0 END),0) sales_pence,
-COALESCE(SUM(CASE WHEN amount_pence<0 THEN amount_pence ELSE 0 END),0) credits_pence,
COALESCE(SUM(amount_pence),0) net_pence,MIN(day) first_day,MAX(day) last_day
FROM lines;
