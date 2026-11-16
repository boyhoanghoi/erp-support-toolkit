# Reproducible sample results

Executed locally on 17 November 2026 with Python 3.12. These are fictional CSV samples, not a customer environment.

```text
python -m unittest discover -s tests -v
Ran 16 tests
OK

python -m erp_support --products samples/products.csv --movements samples/movements.csv --out docs/evidence/clean.json
PASS: 2 products, 4 movements, 0 errors, 0 variances
exit code: 0

python -m erp_support --products samples/products-with-issues.csv --movements samples/movements.csv --out docs/evidence/review.json
REVIEW_REQUIRED: 4 products, 4 movements, 5 errors, 1 variances
exit code: 1
```

The [clean JSON](evidence/clean.json) and [review JSON](evidence/review.json) are actual generated outputs. Clean KB-01: opening 10, movement total -3, expected/current 7, difference 0. Dirty KB-01: current 6, expected 7, difference -1. The dirty report is provisional (`reliable=false`) because its master also contains invalid rows.

Re-run the commands to verify results for your current commit. CI additionally publishes a generated clean report; a manual UAT sign-off is not implied.
