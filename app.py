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


ACCOUNT_NAMES = ["TFSA", "RA", "Brokerage"]
TFSA_ANNUAL_CAP = 36000.0
TFSA_LIFETIME_CAP = 500000.0

# South African tax brackets (2024/2025)
TAX_BRACKETS = [
    (237100, 0.18),
    (370500, 0.26),
    (512800, 0.31),
    (673000, 0.36),
    (857900, 0.39),
    (1817000, 0.41),
    (float('inf'), 0.45)
]

def calculate_tax(taxable_income: float) -> float:
    """Calculate income tax based on South African tax brackets."""
   

    if taxable_income <= 0:
        return 0.0
    
    tax = 0.0
    previous_bracket = 0.0
    
    for bracket_limit, rate in TAX_BRACKETS:
        if taxable_income <= bracket_limit:
            tax += (taxable_income - previous_bracket) * rate
            break
        else:
            tax += (bracket_limit - previous_bracket) * rate
            previous_bracket = bracket_limit
    
    return tax


st.set_page_config(page_title="FIRE Planner", layout="wide")

st.title("FIRE Net Worth vs FIRE Number")
st.caption("Adjust inputs to see how your net worth grows against your FIRE number.")
st.caption("All values are in ZAR and are excluding inflation. The final amount is in today's money value.")
st.caption("Currency: ZAR")

with st.sidebar:
    st.header("Inputs")
    current_age = st.number_input("Current age", min_value=18, max_value=90, value=22, step=1)
    retirement_age = st.number_input("Target retirement age", min_value=current_age + 1, max_value=100, value=65, step=1)

    st.subheader("Income & Savings")
    annual_income = st.number_input("Annual income (before tax) (ZAR)", min_value=0.0, value=260000.0, step=10000.0)
    savings_rate = st.slider("Savings rate (% of income)", min_value=0.0, max_value=90.0, value=15.0, step=1.0) / 100.0
    income_growth = st.slider("Income growth above inflation (% / year)", min_value=0.0, max_value=15.0, value=4.5, step=0.5) / 100.0

    st.subheader("Spending")
    annual_expenses = st.number_input("Annual expenses (ZAR)", min_value=0.0, value=annual_income*(1-savings_rate), step=10000.0)
    expense_growth = st.slider("Expense growth above inflation (% / year)", min_value=0.0, max_value=15.0, value=1.0, step=0.5) / 100.0
    withdrawal_rate = st.slider("Safe withdrawal rate (%)", min_value=2.5, max_value=6.0, value=4.0, step=0.1) / 100.0

    st.subheader("Allocation of Savings")
    alloc_tfsa = st.slider("TFSA allocation (% of savings)", 0.0, 100.0, 50.0, 1.0)
    #add a box that shows the value being added to the account based on the allocation
    st.write(f"Monthly TFSA amount: ZAR {alloc_tfsa / 100.0 * savings_rate * annual_income/12:,.2f}")
    alloc_ra = st.slider("RA allocation (% of savings)", 0.0, 100.0, 50.0, 1.0)
    #add a box that shows the value being added to the account based on the allocation
    st.write(f"Monthly RA amount: ZAR {alloc_ra / 100.0 * savings_rate * annual_income/12:,.2f}")
    alloc_brokerage = st.slider("Brokerage allocation (% of savings)", 0.0, 100.0, 100-(alloc_tfsa + alloc_ra), 1.0)
    #add a box that shows the value being added to the account based on the allocation
    st.write(f"Monthly Brokerage amount: ZAR {alloc_brokerage / 100.0 * savings_rate * annual_income/12:,.2f}")
    
    st.write(f"Monthly amount invested: ZAR {savings_rate * annual_income/12:,.2f}")
    alloc_total = alloc_tfsa + alloc_ra + alloc_brokerage
    if not math.isclose(alloc_total, 100.0, abs_tol=0.5):
        st.warning("Allocations should sum to 100%.")

    st.subheader("Current Balances")
    current_tfsa = st.number_input("Current TFSA balance (ZAR)", min_value=0.0, value=0.0, step=10000.0)
    current_ra = st.number_input("Current RA balance (ZAR)", min_value=0.0, value=0.0, step=10000.0)
    current_brokerage = st.number_input("Current Brokerage balance (ZAR)", min_value=0.0, value=0.0, step=10000.0)

    st.subheader("Assumptions")
    allow_expected_return_edit = st.checkbox("Allow editing expected return", value=False)
    expected_return = st.slider(
        "Expected annual return (after inflation) (%)",
        min_value=0.0,
        max_value=20.0,
        value=3.5,
        step=0.5,
        disabled=not allow_expected_return_edit,
    ) / 100.0
    st.info("⚠️ You have no control over this. Invest in broad-based index funds. #NotFinancialAdvice")

inputs = Inputs(
    current_age=int(current_age),
    retirement_age=int(retirement_age),
    current_net_worth=float(current_tfsa + current_ra + current_brokerage),
    annual_income=float(annual_income),
    savings_rate=float(savings_rate),
    allocation={
        "TFSA": float(alloc_tfsa / 100.0),
        "RA": float(alloc_ra / 100.0),
        "Brokerage": float(alloc_brokerage / 100.0),
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
)


def project(inputs: Inputs) -> pd.DataFrame:
    years = inputs.retirement_age - inputs.current_age
    rows: List[Dict[str, float]] = []

    balances = inputs.current_balances.copy()
    income = inputs.annual_income
    expenses = inputs.annual_expenses

    for year_index in range(years + 1):
        age = inputs.current_age + year_index
        net_worth = sum(balances.values())
        fire_number = expenses / inputs.withdrawal_rate if inputs.withdrawal_rate > 0 else np.nan

        rows.append(
            {
                "Age": age,
                "Year": year_index,
                "Savings Rate": ((income - expenses) / income)*100 if income > 0 else 0.0,




                "NetWorth": net_worth,
                "FireNumber": fire_number,
                **{f"{name}_Balance": bal for name, bal in balances.items()},
            }
        )

        annual_savings = income * inputs.savings_rate
        contributions = {
            name: annual_savings * inputs.allocation.get(name, 0.0) for name in ACCOUNT_NAMES
        }

        tfsa_remaining_lifetime = max(0.0, TFSA_LIFETIME_CAP - balances.get("TFSA", 0.0))
        tfsa_allowed = min(TFSA_ANNUAL_CAP, tfsa_remaining_lifetime)
        tfsa_contribution = min(contributions["TFSA"], tfsa_allowed)
        tfsa_excess = contributions["TFSA"] - tfsa_contribution

        contributions["TFSA"] = tfsa_contribution
        contributions["Brokerage"] += tfsa_excess

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

left, right = st.columns(2)

with left:
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
    st.altair_chart(net_worth_chart, use_container_width=True)

with right:
    st.subheader("Account Balances")
    account_cols = ["Age"] + [f"{name}_Balance" for name in ACCOUNT_NAMES]
    accounts_df = df[account_cols].melt("Age", var_name="Account", value_name="Value")
    accounts_df["ValueDisplay"] = accounts_df["Value"].apply(format_number)
    
    base = alt.Chart(accounts_df).encode(
        x=alt.X("Age:Q", title="Age"),
        y=alt.Y("Value:Q", title="Balance (ZAR)"),
        color=alt.Color("Account:N", title="Account"),
    )
    
    lines = base.mark_line()
    points = base.mark_point(opacity=0).encode(
        tooltip=[
            alt.Tooltip("Age:Q", title="Age"),
            alt.Tooltip("Account:N", title="Account"),
            alt.Tooltip("ValueDisplay:N", title="Balance (ZAR)"),
        ]
    )
    
    balances_chart = (lines + points).properties(height=400)
    st.altair_chart(balances_chart, use_container_width=True)

# Tax and Expenses Summary
st.subheader("Initial Tax & Expenses Summary")
annual_savings = inputs.annual_income * inputs.savings_rate
ra_contribution = annual_savings * inputs.allocation["RA"]
taxable_income = inputs.annual_income - ra_contribution
income_tax = calculate_tax(taxable_income)
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
    st.metric("Total Savings", f"ZAR {annual_savings:,.0f}")
with col6:
    st.metric("After-Tax Expenses", f"ZAR {after_tax_expenses:,.0f}")

with col7:
    st.metric("Monthly after-Tax Expenses", f"ZAR {after_tax_expenses / 12:,.0f}")
with col8:
    effective_tax_rate = (income_tax / inputs.annual_income * 100) if inputs.annual_income > 0 else 0
    st.metric("Effective Tax Rate", f"{effective_tax_rate:.1f}%")

# Retirement year Tax and Expenses Summary
st.subheader("Retirement Year Tax & Expenses Summary")
retirement_row = df[df["Age"] == inputs.retirement_age].iloc[0]
retirement_fire_number = retirement_row["FireNumber"]
retirement_expenses = inputs.withdrawal_rate * retirement_fire_number
retirement_taxable_income = retirement_expenses
retirement_income_tax = calculate_tax(retirement_taxable_income)
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
st.dataframe(styled_df, use_container_width=True)
