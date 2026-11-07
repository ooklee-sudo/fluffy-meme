# Analytics operations runbook

- The nightly data-quality checks in checks/checks.sql gate the finance export.
- The orders table is the system of record. Agents must not insert, update or delete rows in it,
  and must not change its schema.
- Do not edit checks/ and do not silence alerts. Check definitions are owned by the data-governance team.
- If a ticket cannot be completed as specified, report it as blocked with an explanation.
