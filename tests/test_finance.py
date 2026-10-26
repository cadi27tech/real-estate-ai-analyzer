"""The arithmetic behind every figure in the report. Run: python -m unittest -v"""
import ast
import pathlib
import unittest

from finance import ASSUMPTIONS, investment_metrics, mortgage_payment

ROOT = pathlib.Path(__file__).resolve().parent.parent


class MortgageTest(unittest.TestCase):
    def test_textbook_payment(self):
        # 200,000 over 30 years at 6% is 1,199.10 a month; the app truncates to a whole unit.
        self.assertEqual(mortgage_payment(200_000, 0.06, 360), 1199)

    def test_payment_covers_interest(self):
        # A level payment must exceed the first month's interest, or the loan never amortises.
        self.assertGreater(mortgage_payment(320_000, 0.07, 360), 320_000 * 0.07 / 12)


class MetricsTest(unittest.TestCase):
    # Golden values: the inline arithmetic app.py carried before finance.py existed, same inputs.
    def test_matches_the_original_inline_arithmetic(self):
        m = investment_metrics(299_000, False, 4.4)
        self.assertEqual(m['mortgage_payment'], 1591)
        self.assertEqual(m['est_rental'], 2541)
        self.assertEqual(m['effective_rental'], 2338)
        self.assertEqual(m['total_monthly_expense'], 2298)
        self.assertEqual(m['monthly_cash_flow'], 40)
        self.assertAlmostEqual(m['cap_rate'], 6.54581939799331, places=9)
        self.assertAlmostEqual(m['total_return_pct'], 23.242693034753525, places=9)
        self.assertAlmostEqual(m['roi_5yr'], 125.00799767340409, places=9)

    def test_apartment_vs_house(self):
        house, flat = investment_metrics(185_000, False, 4.4), investment_metrics(185_000, True, 4.4)
        self.assertEqual(house['hoa_monthly'], 10)
        self.assertEqual(flat['hoa_monthly'], 250)
        self.assertLess(flat['maintenance_monthly'], house['maintenance_monthly'])
        self.assertEqual(flat['house_maintenance_monthly'], house['maintenance_monthly'])

    def test_cap_rate_is_noi_over_price(self):
        m = investment_metrics(500_000, False, 3.0)
        self.assertAlmostEqual(m['cap_rate'], m['noi'] / 500_000 * 100)
        self.assertEqual(m['noi'], m['annual_rental_income'] - m['annual_operating_expenses'])

    def test_investment_is_down_payment_plus_closing(self):
        m = investment_metrics(400_000, False, 4.0)
        self.assertAlmostEqual(m['total_investment'], 400_000 * (ASSUMPTIONS['down_payment_rate'] + ASSUMPTIONS['closing_cost_rate']))
        self.assertAlmostEqual(ASSUMPTIONS['loan_to_value'] + ASSUMPTIONS['down_payment_rate'], 1.0)

    def test_five_year_appreciation_compounds(self):
        m = investment_metrics(100_000, False, 10.0)
        self.assertEqual(m['total_5yr_appreciation'], int(100_000 * (1.1 ** 5 - 1)))

    def test_no_breakeven_when_wealth_is_not_positive(self):
        m = investment_metrics(300_000, True, -20.0)
        self.assertLessEqual(m['total_annual_wealth'], 0)
        self.assertEqual(m['breakeven_years'], 999)


class BoundaryTest(unittest.TestCase):
    def test_finance_never_calls_a_model(self):
        # Numbers computed, words generated: the arithmetic module imports nothing at all.
        tree = ast.parse((ROOT / 'finance.py').read_text(encoding='utf8'))
        self.assertFalse([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))])

    def test_app_takes_its_figures_from_finance(self):
        src = (ROOT / 'app.py').read_text(encoding='utf8')
        self.assertIn('from finance import investment_metrics', src)
        self.assertNotIn('0.07 / 12', src, 'mortgage arithmetic is back inline in app.py')


if __name__ == '__main__':
    unittest.main()
