"""Usage: python -m erp_support --products ... --movements ... --out ..."""
import argparse
import csv
import json
import sys
from pathlib import Path
from .checks import read_csv, reconcile, PRODUCT_COLUMNS, MOVEMENT_COLUMNS


def main(argv=None):
    parser = argparse.ArgumentParser(description='Read-only ERP data quality and stock reconciliation')
    parser.add_argument('--products', type=Path, required=True)
    parser.add_argument('--movements', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True, help='JSON report, must differ from both inputs')
    args = parser.parse_args(argv)
    try:
        if args.out.resolve() in {args.products.resolve(), args.movements.resolve()}:
            raise ValueError('Output path must not overwrite input data')
        report = reconcile(read_csv(args.products, PRODUCT_COLUMNS), read_csv(args.movements, MOVEMENT_COLUMNS))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    except (OSError, ValueError, csv.Error) as exc:
        print(f'Input/output error: {exc}', file=sys.stderr)
        return 2
    print(f"{report['status']}: {report['product_rows']} products, {report['movement_rows']} movements, "
          f"{report['error_count']} errors, {report['variance_count']} variances")
    if not report['reliable']:
        print('Balances are provisional: correct validation errors before reconciliation sign-off.')
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
