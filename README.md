# FIRE Financial Planner

A comprehensive Financial Independence, Retire Early (FIRE) planning tool built with Streamlit. This application helps South African users calculate their path to financial independence by projecting net worth growth and comparing it against their FIRE number.

## Features

- **Net Worth Projections**: Calculate how your net worth grows over time based on income, savings rate, and investment returns
- **FIRE Number Calculation**: Determine the exact amount needed for retirement based on your spending and safe withdrawal rate
- **Account Allocation**: Manage investments across multiple account types:
  - TFSA (Tax-Free Savings Account) with annual and lifetime contribution caps
  - RA (Retirement Annuity)
  - Brokerage accounts
- **South African Tax Calculation**: Automatic tax calculations based on 2024/2025 tax brackets
- **Inflation-Adjusted Planning**: All projections shown in today's money value
- **Interactive Dashboard**: Real-time adjustments with instant visualization updates

## Setup

### Requirements

- Python 3.7+
- Dependencies listed in `requirements.txt`

### Installation

1. Clone or download this repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Input Parameters

### Personal Information
- **Current age**: Your age (18-90)
- **Target retirement age**: When you plan to retire

### Income & Savings
- **Annual income (before tax)**: Your gross income in ZAR
- **Savings rate**: Percentage of income you save
- **Income growth**: Expected annual growth above inflation

### Spending
- **Annual expenses**: Your current annual spending
- **Expense growth**: Expected annual increase above inflation
- **Safe withdrawal rate**: Percentage of portfolio you can safely withdraw annually (typically 3.5-4%)

### Account Allocation
- **TFSA allocation**: Percentage of savings directed to TFSA
- **RA allocation**: Percentage of savings directed to Retirement Annuity
- **Brokerage allocation**: Remaining savings (unrestricted investment account)

## Features Explained

### TFSA Limits (South African)
- Annual contribution cap: R36,000
- Lifetime contribution cap: R500,000

### Tax Calculations
Automatically applies South African income tax brackets for 2024/2025:
- 18% on first R237,100
- Progressive increases up to 45% on income above R1,817,000

## Currency

All values are in **South African Rand (ZAR)**

## Notes

- All calculations are in today's money value (inflation-adjusted)
- The safe withdrawal rate assumes you can sustainably withdraw a percentage of your portfolio annually
- TFSA contributions are capped and cannot exceed the lifetime limit
- Investment returns and inflation assumptions can be adjusted in the code

## License

Open source - feel free to modify for personal use

## Contact

For questions or suggestions, feel free to reach out!
