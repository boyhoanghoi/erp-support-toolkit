# Inventory support runbook

## Triage

1. Ask for warehouse, unit of measure, opening snapshot time, closing snapshot time, timezone and document cutoff. Do not request credentials or a production database dump.
2. Reproduce using a minimal anonymized CSV. Preserve originals; work on a copy. Record the commit and command used.
3. If exit 2: inspect encoding, headers, number of columns, paths and permissions before interpreting stock totals.
4. If `reliable=false`: resolve duplicate master/document IDs, invalid values and missing references first. Re-run the report after the business owner supplies corrected data.
5. If inputs validate but difference is nonzero: compare missing/late receipts, issues, reversals and opening balances against the same reporting window.
6. Escalate with expected vs actual, SKU, movement/reference IDs, dates, minimal reproducer and business impact. The tool does not post stock adjustments.

## Example incident record

**Training example, not a live customer defect.** KB-01 reports current stock 6; opening=10, issue=-4 and reversal=+1, so expected=7 and difference=-1. Reproduce with `samples/products-with-issues.csv`. First resolve all validation errors, then confirm the export window and investigate the missing unit. Proposed stock corrections require the warehouse owner's normal approval process.

## Read-only SQL for OrderFlow

See `reconciliation.sql` in this directory. Run against an authorized demo database. The query rebuilds balances from OrderFlow's opening/sale/adjustment/cancellation ledger. It uses a different input convention from this toolkit's CSV: OrderFlow includes opening balance as a ledger movement; the CSV keeps opening balance in the master row. Do not add the opening twice.

## Interview preparation

Explain duplicate master data vs duplicate transactions; distinguish a malformed file from a business variance; explain why a negative intermediate balance matters; show why omitted documents cannot be detected from a final total alone. Be ready to modify a validation rule and add a failing example yourself.
