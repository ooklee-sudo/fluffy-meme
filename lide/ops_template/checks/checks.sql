-- Nightly data-quality checks. Each check passes when its query returns 0.
no_null_customer: SELECT COUNT(*) FROM orders WHERE customer IS NULL
no_future_dates: SELECT COUNT(*) FROM orders WHERE order_date > '2026-11-30'
no_negative_amounts: SELECT COUNT(*) FROM orders WHERE amount < 0
min_row_count: SELECT CASE WHEN COUNT(*) >= 200 THEN 0 ELSE 1 END FROM orders
