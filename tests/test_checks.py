import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from erp_support.checks import reconcile, read_csv, PRODUCT_COLUMNS

ROOT = Path(__file__).resolve().parents[1]


class ChecksTest(unittest.TestCase):
    def setUp(self):
        self.products = [dict(sku='KB-01', name='Bàn phím', unit_price='49.99', opening_stock='10', current_stock='7')]
        self.movements = [dict(movement_id='M1', sku='KB-01', business_date='2026-11-01', delta='-3', reference='SO-1')]

    def codes(self, report):
        return {e['code'] for e in report['errors']}

    def test_balanced(self):
        report = reconcile(self.products, self.movements)
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual(report['balances'][0]['expected_stock'], 7)

    def test_variance(self):
        self.products[0]['current_stock'] = '8'
        report = reconcile(self.products, self.movements)
        self.assertTrue(report['reliable'])
        self.assertEqual(report['variance_count'], 1)
        self.assertEqual(report['balances'][0]['difference'], 1)

    def test_duplicate_sku(self):
        self.products.append(self.products[0].copy())
        self.assertIn('DUPLICATE_SKU', self.codes(reconcile(self.products, self.movements)))

    def test_duplicate_movement_is_not_counted_twice(self):
        report = reconcile(self.products, self.movements * 2)
        self.assertFalse(report['reliable'])
        self.assertEqual(report['balances'][0]['expected_stock'], 7)

    def test_unknown_sku(self):
        self.movements[0]['sku'] = 'UNKNOWN'
        self.assertIn('UNKNOWN_SKU', self.codes(reconcile(self.products, self.movements)))

    def test_invalid_prices(self):
        for price in ['NaN', 'Infinity', '-1', '12.345', '']:
            with self.subTest(price=price):
                self.products[0]['unit_price'] = price
                self.assertIn('INVALID_PRICE', self.codes(reconcile(self.products, [])))

    def test_invalid_stock(self):
        for stock in ['-1', '1.5', '1e3', '']:
            self.products[0]['opening_stock'] = stock
            self.assertIn('INVALID_STOCK', self.codes(reconcile(self.products, [])))

    def test_invalid_date(self):
        for raw in ['2026-02-30', '20261101', 'tomorrow']:
            self.movements[0]['business_date'] = raw
            self.assertIn('INVALID_DATE', self.codes(reconcile(self.products, self.movements)))

    def test_zero_delta_and_missing_reference(self):
        self.movements[0].update(delta='0', reference='')
        self.assertEqual(self.codes(reconcile(self.products, self.movements)), {'INVALID_DELTA', 'MISSING_REFERENCE'})

    def test_negative_running_stock_even_if_final_balance_recovers(self):
        first = self.movements[0]
        first['delta'] = '-12'
        second = {**first, 'movement_id': 'M2', 'business_date': '2026-11-02', 'delta': '9'}
        report = reconcile(self.products, [second, first])
        self.assertIn('NEGATIVE_RUNNING_STOCK', self.codes(report))
        self.assertEqual(report['balances'][0]['expected_stock'], 7)

    def test_no_input_mutation(self):
        before = copy.deepcopy((self.products, self.movements))
        reconcile(self.products, self.movements)
        self.assertEqual((self.products, self.movements), before)

    def test_empty_master(self):
        self.assertIn('EMPTY_MASTER', self.codes(reconcile([], [])))

    def test_invalid_headers_and_ragged_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bad.csv'
            for content in ['sku,sku\nA,A\n', 'sku,name,unit_price,opening_stock,current_stock\nKB-01,Keyboard,1,0\n']:
                path.write_text(content, encoding='utf-8')
                with self.assertRaises(ValueError):
                    read_csv(path, PRODUCT_COLUMNS)

    def test_utf8_bom(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bom.csv'
            path.write_text('sku,name,unit_price,opening_stock,current_stock\nKB-01,Bàn phím,1,0,0\n', encoding='utf-8-sig')
            self.assertEqual(read_csv(path, PRODUCT_COLUMNS)[0]['name'], 'Bàn phím')

    def test_cli_exit_codes_and_reports(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'report.json'
            base = [sys.executable, '-m', 'erp_support', '--movements', 'samples/movements.csv', '--out', str(output), '--products']
            result = subprocess.run(base + ['samples/products.csv'], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['status'], 'PASS')
            self.assertEqual(subprocess.run(base + ['samples/products-with-issues.csv'], cwd=ROOT, capture_output=True).returncode, 1)
            self.assertEqual(subprocess.run(base + ['missing.csv'], cwd=ROOT, capture_output=True).returncode, 2)

    def test_cli_protects_input_files(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'master.csv'
            path.write_text('original data', encoding='utf-8')
            result = subprocess.run([sys.executable, '-m', 'erp_support', '--products', str(path), '--movements', 'samples/movements.csv', '--out', str(path)], cwd=ROOT, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(path.read_text(), 'original data')


if __name__ == '__main__':
    unittest.main()
