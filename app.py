import math
from dataclasses import dataclass
from typing import Dict, List

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st


@dataclass
class Inputs:
    current_age: int
    retirement_age: int
    current_net_worth: float
    annual_income: float
    savings_rate: float
    allocation: Dict[str, float]
    current_balances: Dict[str, float]
    expected_return: float
    income_growth: float
    expense_growth: float
    annual_expenses: float
    withdrawal_rate: float
    dual_income: bool = False


ACCOUNT_NAMES = ["TFSA", "RA", "Brokerage"]
TFSA_ANNUAL_CAP = 46000.0
TFSA_LIFETIME_CAP = 500000.0
RA_CAP_PCT = 27.5
RA_ANNUAL_CAP = 450000.0

# South African tax brackets (2024/2025)
TAX_BRACKETS = [
    (245100, 0.18),
    (383100, 0.26),
    (530201, 0.31),
    (695801, 0.36),
    (887001, 0.39),
    (1878601, 0.41),
    (float('inf'), 0.45)
]

Tax_Rebate = 17820 # Primary rebate for individuals under 65 (2024/2025)

def calculate_tax(taxable_income: float, dual_income: bool = False) -> float:
    """Calculate income tax based on South African tax brackets."""
   

    if taxable_income <= 0:
        return 0.0

    household_multiplier = 2.0 if dual_income else 1.0
    scaled_brackets = [(limit * household_multiplier, rate) for limit, rate in TAX_BRACKETS]
    scaled_rebate = Tax_Rebate * household_multiplier
    
    tax = 0.0
    previous_bracket = 0.0
    
    for bracket_limit, rate in scaled_brackets:
        if taxable_income <= bracket_limit:
            tax += (taxable_income - previous_bracket) * rate
            break
        else:
            tax += (bracket_limit - previous_bracket) * rate
            previous_bracket = bracket_limit
    
    final_tax = max(0.0, tax - scaled_rebate)

    return final_tax


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, float(value)))


def max_savings_rate_pct(annual_income: float, dual_income: bool = False) -> float:
    if annual_income <= 0:
        return 0.0
    after_tax_income = max(0.0, annual_income - calculate_tax(annual_income, dual_income=dual_income))
    return max(0.0, min(100.0, (after_tax_income / annual_income) * 100.0))


def slider_with_number_input(
    label: str,
    min_value: float,
    max_value: float,
    default_value: float,
    step: float,
    key: str,
    disabled: bool = False,
    help_text: str | None = None,
    fixed_value: float | None = None,
) -> float:
    slider_key = f"{key}_slider"
    if max_value < min_value:
        max_value = min_value
    fixed_range = math.isclose(min_value, max_value, abs_tol=max(step / 10.0, 1e-9))
    initial_value = clamp(default_value, min_value, max_value)

    if slider_key not in st.session_state:
        st.session_state[slider_key] = initial_value

    if fixed_value is not None or fixed_range:
        locked_value = min_value if fixed_value is None else fixed_value
        fixed_clamped = clamp(locked_value, min_value, max_value)
        st.session_state[slider_key] = fixed_clamped
    else:
        st.session_state[slider_key] = clamp(st.session_state[slider_key], min_value, max_value)

    if fixed_range:
        st.slider(
            label,
            min_value=min_value,
            max_value=min_value + step,
            value=min_value,
            step=step,
            disabled=True,
            help=help_text,
        )
    else:
        st.slider(
            label,
            min_value=min_value,
            max_value=max_value,
            step=step,
            key=slider_key,
            disabled=disabled,
            help=help_text,
        )

    return float(st.session_state[slider_key])


st.set_page_config(page_title="FIRE Planner", layout="wide")

st.title("FIRE Net Worth vs FIRE Number")
st.caption("Adjust inputs to see how your net worth grows against your FIRE number.")
st.caption("All values are in ZAR and are excluding inflation. The final amount is in today's money value.")
st.caption("Currency: ZAR")

with st.sidebar:
    st.header("Inputs")
    dual_income = st.checkbox("Dual income household", value=False)
    current_age = st.number_input("Current age", min_value=18, max_value=90, value=22, step=1)
    retirement_age = st.number_input("Target retirement age", min_value=current_age + 1, max_value=100, value=65, step=1)

    st.subheader("Income & Savings")
    if dual_income:
        annual_income_person_1 = st.number_input(
            "Annual income - Person 1 (before tax) (ZAR)",
            min_value=0.0,
            value=260000.0,
            step=10000.0,
        )
        annual_income_person_2 = st.number_input(
            "Annual income - Person 2 (before tax) (ZAR)",
            min_value=0.0,
            value=260000.0,
            step=10000.0,
        )
        max_savings_rate_person_1_pct = max_savings_rate_pct(annual_income_person_1)
        max_savings_rate_person_2_pct = max_savings_rate_pct(annual_income_person_2)
        savings_rate_person_1 = slider_with_number_input(
            "Savings rate - Person 1 (% of income)",
            0.0,
            max_savings_rate_person_1_pct,
            min(15.0, max_savings_rate_person_1_pct),
            1.0,
            "savings_rate_person_1_pct",
        ) / 100.0
        savings_rate_person_2 = slider_with_number_input(
            "Savings rate - Person 2 (% of income)",
            0.0,
            max_savings_rate_person_2_pct,
            min(15.0, max_savings_rate_person_2_pct),
            1.0,
            "savings_rate_person_2_pct",
        ) / 100.0
        income_growth_person_1 = slider_with_number_input(
            "Income growth - Person 1 (% / year)",
            0.0,
            15.0,
            2.5,
            0.5,
            "income_growth_person_1_pct",
        ) / 100.0
        income_growth_person_2 = slider_with_number_input(
            "Income growth - Person 2 (% / year)",
            0.0,
            15.0,
            2.5,
            0.5,
            "income_growth_person_2_pct",
        ) / 100.0
        annual_income = annual_income_person_1 + annual_income_person_2
        total_annual_savings = (
            annual_income_person_1 * savings_rate_person_1
            + annual_income_person_2 * savings_rate_person_2
        )
        savings_rate = (total_annual_savings / annual_income) if annual_income > 0 else 0.0
        total_income_growth_weighted = (
            annual_income_person_1 * income_growth_person_1
            + annual_income_person_2 * income_growth_person_2
        )
        income_growth = (total_income_growth_weighted / annual_income) if annual_income > 0 else 0.0
        max_combined_savings_rate_pct = max_savings_rate_pct(annual_income, dual_income=dual_income)
        st.write(f"Combined annual income (before tax): ZAR {annual_income:,.0f}")
        st.write(f"Combined savings rate: {savings_rate * 100:.1f}%")
        st.caption(f"Combined max savings rate based on after-tax income: {max_combined_savings_rate_pct:.1f}%")
        st.write(f"Combined income growth above inflation: {income_growth * 100:.1f}%")
    else:
        annual_income = st.number_input("Annual income (before tax) (ZAR)", min_value=0.0, value=260000.0, step=10000.0)
        max_savings_rate_single_pct = max_savings_rate_pct(annual_income, dual_income=dual_income)
        savings_rate = slider_with_number_input(
            "Initial savings rate (% of income)",
            0.0,
            max_savings_rate_single_pct,
            min(15.0, max_savings_rate_single_pct),
            1.0,
            "savings_rate_pct",
        ) / 100.0
        st.caption(f"Max savings rate based on after-tax income: {max_savings_rate_single_pct:.1f}%")
        income_growth = slider_with_number_input("Income growth above inflation (% / year)", 0.0, 15.0, 2.5, 0.5, "income_growth_pct") / 100.0

    st.subheader("Spending")
    estimated_income_tax = calculate_tax(annual_income, dual_income=dual_income)
    estimated_after_tax_income = annual_income - estimated_income_tax
    annual_expenses_default = max(0.0, estimated_after_tax_income - (annual_income * savings_rate))
    annual_expenses = st.number_input("Annual expenses (ZAR)", min_value=0.0, value=annual_expenses_default, step=10000.0, disabled = True)
    expense_growth = slider_with_number_input("Expense growth above inflation (% / year)", 0.0, 15.0, 1.5, 0.5, "expense_growth_pct") / 100.0
    
    withdrawal_rate = slider_with_number_input("Safe withdrawal rate (%)", 2.5, 6.0, 4.0, 0.1, "withdrawal_rate_pct") / 100.0
    
    st.caption("💡 The percentage of your portfolio you can safely withdraw annually at retirement. The 4% rule assumes a 30-year retirement. Lower rates (3%) are more conservative; higher rates (4-5%) are more aggressive.", help="Safe Withdrawal Rate")

    st.subheader("Allocation of Savings")
    savings_rate_pct = savings_rate * 100.0
    household_multiplier = 2.0 if dual_income else 1.0
    tfsa_annual_cap = TFSA_ANNUAL_CAP * household_multiplier
    tfsa_lifetime_cap = TFSA_LIFETIME_CAP * household_multiplier
    tfsa_income_cap_pct = (tfsa_annual_cap / annual_income * 100.0) if annual_income > 0 else 0.0
    tfsa_slider_max = min(savings_rate_pct, tfsa_income_cap_pct)
    alloc_tfsa = slider_with_number_input(
        "TFSA allocation (% of income)",
        0.0,
        tfsa_slider_max,
        min(25.0, tfsa_slider_max),
        1.0,
        "alloc_tfsa_pct_income",
    )
    st.caption(
        f"💡 Tax-Free Savings Account: Annual limit R{tfsa_annual_cap:,.0f} | Lifetime limit R{tfsa_lifetime_cap:,.0f}. Growth and withdrawals are tax-free.",
        help="TFSA Info",
    )
    #add a box that shows the value being added to the account based on the allocation
    st.write(f"Monthly TFSA amount: ZAR {alloc_tfsa / 100.0 * annual_income/12:,.2f}")
    
    remaining_after_tfsa = max(0.0, savings_rate_pct - alloc_tfsa)
    ra_income_cap_pct = (RA_ANNUAL_CAP / annual_income * 100.0) if annual_income > 0 else 0.0
    ra_slider_max = min(remaining_after_tfsa, RA_CAP_PCT, ra_income_cap_pct)
    alloc_ra = slider_with_number_input(
        "RA allocation (% of income)",
        0.0,
        ra_slider_max,
        min(ra_slider_max, 10.0),
        1.0,
        "alloc_ra_pct_income",
    )
    st.caption(
        f"💡 Retirement Annuity: Tax-deductible contributions up to {RA_CAP_PCT:.1f}% of income or ZAR {RA_ANNUAL_CAP:,.0f} per year, whichever is lower. Funds are locked until retirement.",
        help="RA Info",
    )
    #add a box that shows the value being added to the account based on the allocation
    st.write(f"Monthly RA amount: ZAR {alloc_ra / 100.0 * annual_income/12:,.2f}")
    
    remaining_after_ra = max(0.0, savings_rate_pct - (alloc_tfsa + alloc_ra))
    alloc_brokerage = slider_with_number_input(
        "Brokerage allocation (% of income)",
        0.0,
        savings_rate_pct,
        remaining_after_ra,
        1.0,
        "alloc_brokerage_pct_income",
        disabled=True,
        fixed_value=remaining_after_ra,
    )
    st.caption("💡 Standard Brokerage: Unrestricted investment account. Subject to capital gains tax but flexible access.", help="Brokerage Info")
    #add a box that shows the value being added to the account based on the allocation
    st.write(f"Monthly Brokerage amount: ZAR {alloc_brokerage / 100.0 * annual_income/12:,.2f}")
    
    st.write(f"Monthly amount invested: ZAR {savings_rate * annual_income/12:,.2f}")
    alloc_total = alloc_tfsa + alloc_ra + alloc_brokerage
    if not math.isclose(alloc_total, savings_rate_pct, abs_tol=0.5):
        st.warning("Allocation percentages should sum to your savings rate (% of income).")

    st.subheader("Current Balances")
    current_tfsa = st.number_input("Current TFSA balance (ZAR)", min_value=0.0, value=0.0, step=10000.0)
    current_ra = st.number_input("Current RA balance (ZAR)", min_value=0.0, value=0.0, step=10000.0)
    current_brokerage = st.number_input("Current Brokerage balance (ZAR)", min_value=0.0, value=0.0, step=10000.0)

    st.subheader("Assumptions")
    allow_expected_return_edit = st.checkbox("Allow editing expected return", value=False)
    expected_return = slider_with_number_input(
        "Expected annual return (after inflation) (%)",
        0.0,
        20.0,
        3.5,
        0.5,
        "expected_return_pct",
        disabled=not allow_expected_return_edit,
    ) / 100.0
    st.info("Returns are modelled conservatively and are treated as an external uncertainty. The intent is to focus analysis on controllable inputs like savings rate and investment horizon.")

inputs = Inputs(
    current_age=int(current_age),
    retirement_age=int(retirement_age),
    current_net_worth=float(current_tfsa + current_ra + current_brokerage),
    annual_income=float(annual_income),
    savings_rate=float(savings_rate),
    allocation={
        "TFSA": float((alloc_tfsa / 100.0) / savings_rate) if savings_rate > 0 else 0.0,
        "RA": float((alloc_ra / 100.0) / savings_rate) if savings_rate > 0 else 0.0,
        "Brokerage": float((alloc_brokerage / 100.0) / savings_rate) if savings_rate > 0 else 0.0,
    },
    current_balances={
        "TFSA": float(current_tfsa),
        "RA": float(current_ra),
        "Brokerage": float(current_brokerage),
    },
    expected_return=float(expected_return),
    income_growth=float(income_growth),
    expense_growth=float(expense_growth),
    annual_expenses=float(annual_expenses),
    withdrawal_rate=float(withdrawal_rate),
    dual_income=bool(dual_income),
)


def project(inputs: Inputs) -> pd.DataFrame:
    years = inputs.retirement_age - inputs.current_age
    rows: List[Dict[str, float]] = []

    balances = inputs.current_balances.copy()
    # Track cumulative TFSA contributions separately (growth doesn't count against contribution limit)
    # Assumes current TFSA balance represents cumulative contributions to date
    tfsa_cumulative_contributions = inputs.current_balances.get("TFSA", 0.0)
    income = inputs.annual_income
    expenses = inputs.annual_expenses

    for year_index in range(years + 1):
        age = inputs.current_age + year_index
        net_worth = sum(balances.values())
        fire_number = expenses / inputs.withdrawal_rate if inputs.withdrawal_rate > 0 else np.nan
        annual_savings = max(0.0, income - expenses)
        effective_savings_rate = (annual_savings / income) * 100 if income > 0 else 0.0

        rows.append(
            {
                "Age": age,
                "Year": year_index,
                "Savings Rate": effective_savings_rate,




                "NetWorth": net_worth,
                "FireNumber": fire_number,
                **{f"{name}_Balance": bal for name, bal in balances.items()},
            }
        )

        contributions = {
            name: annual_savings * inputs.allocation.get(name, 0.0) for name in ACCOUNT_NAMES
        }

        # Calculate remaining TFSA room based on cumulative contributions (not balance)
        household_multiplier = 2.0 if inputs.dual_income else 1.0
        tfsa_annual_cap = TFSA_ANNUAL_CAP * household_multiplier
        tfsa_lifetime_cap = TFSA_LIFETIME_CAP * household_multiplier
        tfsa_remaining_lifetime = max(0.0, tfsa_lifetime_cap - tfsa_cumulative_contributions)
        tfsa_allowed = min(tfsa_annual_cap, tfsa_remaining_lifetime)
        tfsa_contribution = min(contributions["TFSA"], tfsa_allowed)
        tfsa_excess = contributions["TFSA"] - tfsa_contribution

        contributions["TFSA"] = tfsa_contribution
        contributions["Brokerage"] += tfsa_excess

        ra_allowed = min((RA_CAP_PCT / 100.0) * income, RA_ANNUAL_CAP)
        ra_contribution = min(contributions["RA"], ra_allowed)
        ra_excess = contributions["RA"] - ra_contribution
        contributions["RA"] = ra_contribution
        contributions["Brokerage"] += ra_excess
        
        # Track cumulative TFSA contributions
        tfsa_cumulative_contributions += tfsa_contribution

        for name in ACCOUNT_NAMES:
            balances[name] = (balances[name] + contributions.get(name, 0.0)) * (1 + inputs.expected_return)

        income *= 1 + inputs.income_growth
        expenses *= 1 + inputs.expense_growth

    return pd.DataFrame(rows)


def format_number(value: object) -> object:
    if pd.isna(value):
        return ""
    if isinstance(value, (int, float, np.floating, np.integer)):
        truncated = math.floor(float(value) / 1000.0) * 1000.0
        return f"{truncated:,.0f}".replace(",", " ")
    return value


df = project(inputs)

crossing = df[df["NetWorth"] >= df["FireNumber"]]
if not crossing.empty:
    fi_age = int(crossing.iloc[0]["Age"])
    st.success(f"Financial Independence reached at age {fi_age}.")
else:
    st.info("Financial Independence not reached by the target retirement age.")

st.subheader("Net Worth vs FIRE Number")
chart_df = df[["Age", "NetWorth", "FireNumber"]].melt(
    "Age", var_name="Series", value_name="Value"
)
chart_df["ValueDisplay"] = chart_df["Value"].apply(format_number)

base = alt.Chart(chart_df).encode(
    x=alt.X("Age:Q", title="Age"),
    y=alt.Y("Value:Q", title="Value (ZAR)"),
    color=alt.Color("Series:N", title="Series"),
)

lines = base.mark_line()
points = base.mark_point(opacity=0).encode(
    tooltip=[
        alt.Tooltip("Age:Q", title="Age"),
        alt.Tooltip("Series:N", title="Series"),
        alt.Tooltip("ValueDisplay:N", title="Value (ZAR)"),
    ]
)

net_worth_chart = (lines + points).properties(height=400)
st.altair_chart(net_worth_chart, width='stretch')

# with right:
#     st.subheader("Account Balances")
#     account_cols = ["Age"] + [f"{name}_Balance" for name in ACCOUNT_NAMES]
#     accounts_df = df[account_cols].melt("Age", var_name="Account", value_name="Value")
#     accounts_df["ValueDisplay"] = accounts_df["Value"].apply(format_number)
    
#     base = alt.Chart(accounts_df).encode(
#         x=alt.X("Age:Q", title="Age"),
#         y=alt.Y("Value:Q", title="Balance (ZAR)"),
#         color=alt.Color("Account:N", title="Account"),
#     )
    
#     lines = base.mark_line()
#     points = base.mark_point(opacity=0).encode(
#         tooltip=[
#             alt.Tooltip("Age:Q", title="Age"),
#             alt.Tooltip("Account:N", title="Account"),
#             alt.Tooltip("ValueDisplay:N", title="Balance (ZAR)"),
#         ]
#     )
    
#     balances_chart = (lines + points).properties(height=400)
#     st.altair_chart(balances_chart, use_container_width=True)

# Tax and Expenses Summary
st.subheader("Initial Tax & Expenses Summary")
annual_savings = inputs.annual_income * inputs.savings_rate
ra_contribution = annual_savings * inputs.allocation["RA"]
taxable_income = inputs.annual_income - ra_contribution
income_tax = calculate_tax(taxable_income, dual_income=inputs.dual_income)
after_tax_income = inputs.annual_income - income_tax
after_tax_expenses = after_tax_income - annual_savings

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Gross Income", f"ZAR {inputs.annual_income:,.0f}")
with col2:
    st.metric("RA Contribution (Tax Deductible)", f"ZAR {ra_contribution:,.0f}")
with col3:
    st.metric("Income Tax", f"ZAR {income_tax:,.0f}")
with col4:
    st.metric("After-Tax Income", f"ZAR {after_tax_income:,.0f}")

col5, col6, col7, col8 = st.columns(4)
with col5:
    st.metric("Total Invested", f"ZAR {annual_savings:,.0f}")
with col6:
    st.metric("After-Tax and Investing Income", f"ZAR {after_tax_expenses:,.0f}")

with col7:
    st.metric("Monthly after-Tax and Investing Income", f"ZAR {after_tax_expenses / 12:,.0f}")
with col8:
    effective_tax_rate = (income_tax / inputs.annual_income * 100) if inputs.annual_income > 0 else 0
    st.metric("Effective Tax Rate", f"{effective_tax_rate:.1f}%")

# Retirement year Tax and Expenses Summary
st.subheader("Retirement Year Tax & Expenses Summary")
retirement_row = df[df["Age"] == inputs.retirement_age].iloc[0]
retirement_net_worth = retirement_row["NetWorth"]
retirement_fire_number = retirement_row["FireNumber"]
retirement_expenses = inputs.withdrawal_rate * retirement_net_worth
retirement_taxable_income = retirement_expenses
retirement_income_tax = calculate_tax(retirement_taxable_income, dual_income=inputs.dual_income)
retirement_after_tax_income = retirement_expenses - retirement_income_tax
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Gross Retirement Income", f"ZAR {retirement_expenses:,.0f}")
with col2:
    st.metric("Income Tax", f"ZAR {retirement_income_tax:,.0f}")
with col3:
    st.metric("After-Tax Retirement Income", f"ZAR {retirement_after_tax_income:,.0f}")
with col4:
    st.metric("Monthly after-Tax Retirement Income", f"ZAR {retirement_after_tax_income / 12:,.0f}")


st.subheader("Projection Table")
format_cols = {col: format_number for col in df.columns if col not in ["Age", "Year", "Savings Rate"]}
format_cols["Savings Rate"] = "{:.1f}%".format
styled_df = df.style.format(format_cols)
st.dataframe(styled_df, width = 'stretch')
