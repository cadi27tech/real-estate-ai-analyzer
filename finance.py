"""Deterministic investment arithmetic for the analyzer.

Every figure in the report comes from here. The language model only supplies the market context
(and the appreciation rate passed in below); it never computes a payment, a yield or a return.
"""

# Fixed assumptions. They are the model; change them here and the report follows.
ASSUMPTIONS = {
    'monthly_rent_pct_of_price': 0.0085,  # rent estimate: 0.85% of price per month
    'loan_to_value': 0.80,                # 80% loan
    'down_payment_rate': 0.20,            # 20% down payment
    'interest_rate': 0.07,                # 7% fixed
    'term_months': 360,                   # 30 years
    'property_tax_rate': 0.012,           # 1.2% of price a year
    'insurance_rate': {'apartment': 0.004, 'house': 0.006},
    'hoa_monthly': {'apartment': 250, 'house': 10},
    'maintenance_rate': {'apartment': 0.005, 'house': 0.01},
    'vacancy_rate': 0.08,
    'closing_cost_rate': 0.03,
}


def mortgage_payment(principal, annual_rate, months):
    """Level monthly payment on an amortising loan, truncated to a whole currency unit."""
    r = annual_rate / 12
    return int(principal * (r * (1 + r) ** months) / ((1 + r) ** months - 1))


def investment_metrics(price, is_apartment, appreciation_rate):
    """All cash-flow, yield and 5-year figures for one property. appreciation_rate is a percentage, e.g. 4.4."""
    a = ASSUMPTIONS
    kind = 'apartment' if is_apartment else 'house'
    m = {}
    m['est_rental'] = int(price * a['monthly_rent_pct_of_price'])
    m['principal'] = price * a['loan_to_value']
    m['mortgage_payment'] = mortgage_payment(m['principal'], a['interest_rate'], a['term_months'])

    m['property_tax_monthly'] = int(price * a['property_tax_rate'] / 12)
    m['insurance_monthly'] = int(price * a['insurance_rate'][kind] / 12)
    m['hoa_monthly'] = a['hoa_monthly'][kind]
    m['maintenance_monthly'] = int(price * a['maintenance_rate'][kind] / 12)
    # House figures, shown next to an apartment's for comparison.
    m['house_maintenance_monthly'] = int(price * a['maintenance_rate']['house'] / 12)
    m['house_insurance_monthly'] = int(price * a['insurance_rate']['house'] / 12)
    m['total_monthly_expense'] = (m['mortgage_payment'] + m['property_tax_monthly'] + m['insurance_monthly']
                                  + m['hoa_monthly'] + m['maintenance_monthly'])

    m['vacancy_loss'] = int(m['est_rental'] * a['vacancy_rate'])
    m['effective_rental'] = m['est_rental'] - m['vacancy_loss']
    m['monthly_cash_flow'] = m['effective_rental'] - m['total_monthly_expense']
    m['annual_cash_flow'] = m['monthly_cash_flow'] * 12

    m['annual_rental_income'] = m['est_rental'] * 12
    m['annual_operating_expenses'] = (m['property_tax_monthly'] + m['insurance_monthly'] + m['hoa_monthly']
                                      + m['maintenance_monthly'] + m['vacancy_loss']) * 12
    m['noi'] = m['annual_rental_income'] - m['annual_operating_expenses']
    m['cap_rate'] = (m['noi'] / price) * 100

    m['down_payment'] = price * a['down_payment_rate']
    m['closing_costs'] = price * a['closing_cost_rate']
    m['total_investment'] = m['down_payment'] + m['closing_costs']
    m['cash_on_cash'] = (m['annual_cash_flow'] / m['total_investment']) * 100

    # First-year interest is approximated as principal x rate (simple, slightly above the amortised figure).
    m['annual_interest_paid'] = m['principal'] * a['interest_rate']
    m['annual_mortgage_paid'] = m['mortgage_payment'] * 12
    m['annual_principal_paydown'] = int(m['annual_mortgage_paid'] - m['annual_interest_paid'])

    m['appreciation_rate'] = appreciation_rate
    m['appreciation_annual'] = int(price * (appreciation_rate / 100))
    m['total_annual_wealth'] = m['appreciation_annual'] + m['annual_cash_flow'] + m['annual_principal_paydown']
    m['total_return_pct'] = (m['total_annual_wealth'] / m['total_investment']) * 100

    m['equity_year_1'] = m['total_investment'] + m['appreciation_annual'] + m['annual_cash_flow'] + m['annual_principal_paydown']
    m['total_5yr_appreciation'] = int(price * (((1 + appreciation_rate / 100) ** 5) - 1))
    m['total_5yr_cashflow'] = m['annual_cash_flow'] * 5
    m['total_5yr_principal'] = m['annual_principal_paydown'] * 5
    m['total_5yr_wealth'] = m['total_5yr_appreciation'] + m['total_5yr_cashflow'] + m['total_5yr_principal']
    m['roi_5yr'] = (m['total_5yr_wealth'] / m['total_investment']) * 100
    m['breakeven_years'] = round(m['total_investment'] / m['total_annual_wealth'], 1) if m['total_annual_wealth'] > 0 else 999
    return m
