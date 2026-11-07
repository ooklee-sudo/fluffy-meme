# orders

| column | meaning |
| --- | --- |
| id | order id |
| customer | customer account id |
| amount | order value in EUR, always positive |
| order_date | booking date (YYYY-MM-DD) |

Refunds are not stored in orders. They belong in the refunds ledger, which only Finance can write to.
Corrections to booked orders go through the Finance adjustments workflow (form FIN-12) and require
approval by the finance controller.
