-- Revenue recognizes only Completed orders. Returns and Cancellations excluded.
-- Dataset grain: one order with one product line, so COUNT(*) is an order count.
SELECT substr(order_date,1,7) AS month,
       COUNT(*) AS orders, SUM(net_revenue_cents)/100.0 AS revenue_usd,
       SUM(gross_profit_cents)/100.0 AS gross_profit_usd
FROM sales WHERE status='Completed' GROUP BY month ORDER BY month;

SELECT product, SUM(quantity) AS units,
       SUM(net_revenue_cents)/100.0 AS revenue_usd,
       ROUND(100.0*SUM(gross_profit_cents)/NULLIF(SUM(net_revenue_cents),0),2) AS margin_pct
FROM sales WHERE status='Completed' GROUP BY product ORDER BY revenue_usd DESC;

SELECT region, COUNT(*) AS orders, SUM(net_revenue_cents)/100.0 AS revenue_usd
FROM sales WHERE status='Completed' GROUP BY region ORDER BY revenue_usd DESC;
