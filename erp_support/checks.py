"""Deterministic checks for a complete opening-balance + movement window."""
import csv
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

PRODUCT_COLUMNS = {'sku', 'name', 'unit_price', 'opening_stock', 'current_stock'}
MOVEMENT_COLUMNS = {'movement_id', 'sku', 'business_date', 'delta', 'reference'}


def read_csv(path: Path, required: set[str]) -> list[dict]:
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)) or not required.issubset(headers):
            raise ValueError(f'{path.name}: missing required or duplicate columns; expected {sorted(required)}')
        rows = list(reader)
        if any(None in row or any(value is None for value in row.values()) for row in rows):
            raise ValueError(f'{path.name}: row does not match header column count')
        return [{key: value.strip() for key, value in row.items()} for row in rows]


def integer(value: str) -> int:
    if not re.fullmatch(r'-?\d+', value):
        raise ValueError('Expected a whole number')
    return int(value)


def reconcile(products: list[dict], movements: list[dict]) -> dict:
    """Report all validation errors; never mutate inputs or an ERP database."""
    errors, master, seen_skus, seen_moves = [], {}, set(), set()

    def error(source, row, code, detail):
        errors.append(dict(source=source, row=row, code=code, detail=detail))

    if not products:
        error('products', 1, 'EMPTY_MASTER', 'Product master must contain at least one row')
    for rownum, row in enumerate(products, 2):
        sku = row.get('sku', '')
        valid = True
        if not re.fullmatch(r'[A-Z0-9][A-Z0-9_-]{1,39}', sku):
            error('products', rownum, 'INVALID_SKU', 'SKU must have 2-40 uppercase letters, digits, underscore or hyphen')
            valid = False
        if sku in seen_skus:
            error('products', rownum, 'DUPLICATE_SKU', sku)
            valid = False
        seen_skus.add(sku)
        if not row.get('name'):
            error('products', rownum, 'MISSING_NAME', sku)
            valid = False
        try:
            price = Decimal(row.get('unit_price', ''))
            if not price.is_finite() or price < 0 or price.as_tuple().exponent < -2:
                raise ValueError
        except (InvalidOperation, ValueError):
            error('products', rownum, 'INVALID_PRICE', 'Price must be finite, nonnegative, with at most two decimal places')
            valid = False
        try:
            opening, current = integer(row.get('opening_stock', '')), integer(row.get('current_stock', ''))
            if min(opening, current) < 0:
                raise ValueError
        except ValueError:
            error('products', rownum, 'INVALID_STOCK', 'Opening/current stock must be nonnegative integers')
            valid = False
        if valid:
            master[sku] = dict(sku=sku, opening_stock=opening, movement_total=0,
                               expected_stock=opening, current_stock=current, difference=current-opening)

    valid_movements = []
    for rownum, row in enumerate(movements, 2):
        valid = True
        mid, sku = row.get('movement_id', ''), row.get('sku', '')
        if not mid or mid in seen_moves:
            error('movements', rownum, 'INVALID_MOVEMENT_ID', 'Movement ID is missing or duplicated: ' + mid)
            valid = False
        seen_moves.add(mid)
        if sku not in master:
            error('movements', rownum, 'UNKNOWN_SKU', sku)
            valid = False
        try:
            raw_date = row.get('business_date', '')
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', raw_date):
                raise ValueError
            business_date = date.fromisoformat(raw_date)
        except ValueError:
            error('movements', rownum, 'INVALID_DATE', 'Use a valid YYYY-MM-DD date')
            valid = False
        try:
            delta = integer(row.get('delta', ''))
            if delta == 0:
                raise ValueError
        except ValueError:
            error('movements', rownum, 'INVALID_DELTA', 'Movement quantity must be a nonzero integer')
            valid = False
        if not row.get('reference'):
            error('movements', rownum, 'MISSING_REFERENCE', 'Document reference is required for traceability')
            valid = False
        if valid:
            valid_movements.append((business_date, rownum, sku, delta))

    # Same-day movements retain source row order. All movements must belong to
    # the supplied opening/current stock window; this is an explicit input contract.
    for _, rownum, sku, delta in sorted(valid_movements):
        entry = master[sku]
        entry['movement_total'] += delta
        entry['expected_stock'] += delta
        if entry['expected_stock'] < 0:
            error('movements', rownum, 'NEGATIVE_RUNNING_STOCK', sku)
    for entry in master.values():
        entry['difference'] = entry['current_stock'] - entry['expected_stock']
    balances = sorted(master.values(), key=lambda entry: entry['sku'])
    variances = sum(entry['difference'] != 0 for entry in balances)
    return dict(schema_version=1, status='PASS' if not errors and not variances else 'REVIEW_REQUIRED',
                reliable=not errors, product_rows=len(products), movement_rows=len(movements),
                error_count=len(errors), variance_count=variances, errors=errors, balances=balances)
