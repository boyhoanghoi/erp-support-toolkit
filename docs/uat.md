# ERP support UAT practice

Training scenario: a single warehouse exports product opening/current balances and all movement documents for one period. All sample data is fictional. This is an acceptance plan, not a claim that business users approved a live ERP deployment.

| ID | Requirement | Steps and data | Expected result | Automated evidence |
| --- | --- | --- | --- | --- |
| UAT-01 | Balanced stock can be reviewed | Run CLI with clean samples | PASS, 2 SKUs, 4 movements, no issues | `test_balanced`, CLI test |
| UAT-02 | Duplicate SKUs block approval | Duplicate KB-01 master row | DUPLICATE_SKU, reliable false | `test_duplicate_sku` |
| UAT-03 | Duplicate documents cannot double-count stock | Repeat M1 | INVALID_MOVEMENT_ID, one accepted quantity | duplicate movement test |
| UAT-04 | Invalid master values are explained | Negative/NaN price or fractional opening | INVALID_PRICE / INVALID_STOCK, row number | invalid price/stock tests |
| UAT-05 | Unknown products are escalated | Use UNKNOWN SKU in movement | UNKNOWN_SKU, reliable false | unknown SKU test |
| UAT-06 | Variance remains visible | Current 8, opening 10, issue 3 | Expected 7, difference +1, review required | `test_variance` |
| UAT-07 | Invalid dates block sign-off | Date 2026-02-30 | INVALID_DATE | invalid date test |
| UAT-08 | Interim negative stock is flagged | Opening 10, issue 12, receive 9 | Negative running stock even though final=7 | negative running-stock test |
| UAT-09 | Input files are protected | Set output equal to product input | Exit 2; original bytes unchanged | CLI protection test |
| UAT-10 | Blank master is not a clean import | Header-only master | EMPTY_MASTER | empty master test |

## Manual execution record template

Record case ID, executor, date, Python version, git commit, exact command, source-file checksum, actual result, report path, pass/fail, and issue reference. Keep source exports immutable. Do not mark a case executed until the command and output have been captured.

The automated sample execution is documented in `sample-results.md`. These manual cases remain a practice checklist until an executor records results.
