SELECT substr(day,1,7) month,country,
SUM(CASE WHEN amount_pence>0 THEN amount_pence ELSE 0 END) sales_pence,
-SUM(CASE WHEN amount_pence<0 THEN amount_pence ELSE 0 END) credits_pence,
SUM(amount_pence) net_pence,
COUNT(DISTINCT CASE WHEN amount_pence>0 THEN invoice END) sales_invoices,
COUNT(*) lines
FROM lines GROUP BY month,country ORDER BY month,country;
SELECT stock, MIN(description) description, SUM(amount_pence) net_pence,
SUM(quantity) net_units
FROM lines GROUP BY stock ORDER BY net_pence DESC LIMIT 10;
SELECT COUNT(*) lines,COUNT(DISTINCT invoice) invoices,
SUM(CASE WHEN amount_pence>0 THEN amount_pence ELSE 0 END) sales_pence,
-SUM(CASE WHEN amount_pence<0 THEN amount_pence ELSE 0 END) credits_pence,
SUM(amount_pence) net_pence,MIN(day) first_day,MAX(day) last_day
FROM lines;
