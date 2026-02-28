import ast
import math
import types
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def load_calculation_symbols() -> types.SimpleNamespace:
    source = APP_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    wanted_assignments = {
        "ACCOUNT_NAMES",
        "TFSA_ANNUAL_CAP",
        "TFSA_LIFETIME_CAP",
        "TAX_BRACKETS",
        "Tax_Rebate",
    }
    wanted_defs = {
        "Inputs",
        "calculate_tax",
        "project",
        "format_number",
    }

    selected_nodes = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in wanted_assignments:
                    selected_nodes.append(node)
                    break
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in wanted_defs:
            selected_nodes.append(node)

    module = ast.Module(body=selected_nodes, type_ignores=[])
    ast.fix_missing_locations(module)

    namespace = {
        "math": math,
        "np": np,
        "pd": pd,
        "dataclass": dataclass,
        "Dict": Dict,
        "List": List,
    }
    exec(compile(module, filename=str(APP_PATH), mode="exec"), namespace)

    return types.SimpleNamespace(**namespace)


CALC = load_calculation_symbols()


class TestCalculations(unittest.TestCase):
    def test_calculate_tax_zero_and_negative_income(self) -> None:
        self.assertEqual(CALC.calculate_tax(0), 0.0)
        self.assertEqual(CALC.calculate_tax(-1000), 0.0)

    def test_calculate_tax_known_bracket_value(self) -> None:
        taxable_income = 300_000.0
        expected = (245_100 * 0.18) + ((300_000 - 245_100) * 0.26) - CALC.Tax_Rebate
        expected = max(0.0, expected)
        self.assertAlmostEqual(CALC.calculate_tax(taxable_income), expected, places=2)

    def test_calculate_tax_dual_income_scales_brackets_and_rebate(self) -> None:
        taxable_income = 300_000.0
        single_tax = CALC.calculate_tax(taxable_income, dual_income=False)
        dual_tax = CALC.calculate_tax(taxable_income, dual_income=True)

        expected_dual = max(0.0, (taxable_income * 0.18) - (CALC.Tax_Rebate * 2))
        self.assertAlmostEqual(dual_tax, expected_dual, places=2)
        self.assertLess(dual_tax, single_tax)

    def test_project_tracks_balances_with_tfsa_annual_cap(self) -> None:
        inputs = CALC.Inputs(
            current_age=30,
            retirement_age=32,
            current_net_worth=0.0,
            annual_income=100_000.0,
            savings_rate=0.5,
            allocation={"TFSA": 1.0, "RA": 0.0, "Brokerage": 0.0},
            current_balances={"TFSA": 0.0, "RA": 0.0, "Brokerage": 0.0},
            expected_return=0.0,
            income_growth=0.0,
            expense_growth=0.0,
            annual_expenses=50_000.0,
            withdrawal_rate=0.04,
        )

        df = CALC.project(inputs)

        self.assertEqual(len(df), 3)
        self.assertEqual(df.iloc[0]["NetWorth"], 0.0)
        self.assertEqual(df.iloc[1]["TFSA_Balance"], 46_000.0)
        self.assertEqual(df.iloc[1]["Brokerage_Balance"], 4_000.0)
        self.assertEqual(df.iloc[2]["TFSA_Balance"], 92_000.0)
        self.assertEqual(df.iloc[2]["Brokerage_Balance"], 8_000.0)
        self.assertEqual(df.iloc[2]["NetWorth"], 100_000.0)

    def test_project_respects_tfsa_lifetime_cap(self) -> None:
        inputs = CALC.Inputs(
            current_age=40,
            retirement_age=41,
            current_net_worth=0.0,
            annual_income=60_000.0,
            savings_rate=1.0,
            allocation={"TFSA": 1.0, "RA": 0.0, "Brokerage": 0.0},
            current_balances={"TFSA": 499_000.0, "RA": 0.0, "Brokerage": 0.0},
            expected_return=0.0,
            income_growth=0.0,
            expense_growth=0.0,
            annual_expenses=50_000.0,
            withdrawal_rate=0.04,
        )

        df = CALC.project(inputs)
        self.assertEqual(df.iloc[1]["TFSA_Balance"], 500_000.0)
        self.assertEqual(df.iloc[1]["Brokerage_Balance"], 9_000.0)

    def test_project_dual_income_doubles_tfsa_annual_cap(self) -> None:
        inputs = CALC.Inputs(
            current_age=30,
            retirement_age=31,
            current_net_worth=0.0,
            annual_income=200_000.0,
            savings_rate=1.0,
            allocation={"TFSA": 1.0, "RA": 0.0, "Brokerage": 0.0},
            current_balances={"TFSA": 0.0, "RA": 0.0, "Brokerage": 0.0},
            expected_return=0.0,
            income_growth=0.0,
            expense_growth=0.0,
            annual_expenses=0.0,
            withdrawal_rate=0.04,
            dual_income=True,
        )

        df = CALC.project(inputs)
        self.assertEqual(df.iloc[1]["TFSA_Balance"], 92_000.0)
        self.assertEqual(df.iloc[1]["Brokerage_Balance"], 108_000.0)

    def test_format_number_truncates_to_nearest_thousand(self) -> None:
        self.assertEqual(CALC.format_number(123_456), "123 000")
        self.assertEqual(CALC.format_number(999), "0")
        self.assertEqual(CALC.format_number(np.nan), "")


if __name__ == "__main__":
    unittest.main()
