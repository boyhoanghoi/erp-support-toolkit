-- Read-only diagnostic against an OrderFlow 1.1 demo database.
-- Opening balance is already a stock_movements entry.
SELECT p.id AS product_id, p.name, p.stock AS actual_stock,
       COALESCE(SUM(m.delta), 0) AS ledger_stock,
       p.stock - COALESCE(SUM(m.delta), 0) AS difference
FROM products AS p
LEFT JOIN stock_movements AS m ON m.product_id = p.id
GROUP BY p.id, p.name, p.stock
HAVING p.stock <> COALESCE(SUM(m.delta), 0)
ORDER BY p.id;
