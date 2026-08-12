"""Tests for the safe formula engine used in the Report Builder."""

from django.test import TestCase

from apps.reports.formulas import (
    InvalidFormulaError,
    evaluate_formula,
    extract_field_references,
    validate_formula,
)


class FormulaEngineTests(TestCase):
    def test_valid_simple_formula(self):
        formula = "sum(a, b)"
        # should not raise
        validate_formula(formula)
        refs = extract_field_references(formula)
        self.assertCountEqual(refs, {"a", "b"})
        result = evaluate_formula(formula, {"a": 2, "b": 3})
        self.assertEqual(result, 5)

    def test_invalid_function(self):
        with self.assertRaises(InvalidFormulaError):
            validate_formula("evil_func(x)")

    def test_boolean_literal(self):
        # boolean literals are allowed but not treated as references
        formula = "if(true, a, b)"
        validate_formula(formula)
        refs = extract_field_references(formula)
        self.assertCountEqual(refs, {"a", "b"})
        self.assertEqual(evaluate_formula(formula, {"a": 1, "b": 0}), 1)

    def test_complex_expression(self):
        formula = "(a + b) * max(c, d) - round(e / f)"
        validate_formula(formula)
        refs = extract_field_references(formula)
        self.assertCountEqual(refs, {"a", "b", "c", "d", "e", "f"})
        data = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 9, "f": 2}
        # manual calculation: (1+2)*max(3,4) - round(9/2) = 3*4 - 4 = 12 - 4 = 8
        self.assertEqual(evaluate_formula(formula, data), 8)
