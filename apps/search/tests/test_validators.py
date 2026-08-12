"""Unit tests for Enterprise Search validators."""

from __future__ import annotations

from django.test import SimpleTestCase

from apps.search.exceptions import SearchValidationError
from apps.search.validators import (
    coerce_entity_type_keys,
    normalize_query,
    validate_entity_type_keys,
    validate_query,
)


class NormalizeQueryTests(SimpleTestCase):
    def test_none_becomes_empty(self):
        self.assertEqual(normalize_query(None), "")

    def test_trims_and_collapses_whitespace(self):
        self.assertEqual(normalize_query("  clean\n  water  "), "clean water")


class ValidateQueryTests(SimpleTestCase):
    def test_empty_raises(self):
        with self.assertRaises(SearchValidationError):
            validate_query("   ")

    def test_short_raises(self):
        with self.assertRaises(SearchValidationError):
            validate_query("a")

    def test_long_raises(self):
        with self.assertRaises(SearchValidationError):
            validate_query("x" * 201)

    def test_reserved_symbol_raises(self):
        for symbol in ('"', "-", "&"):
            with self.assertRaises(SearchValidationError):
                validate_query(f"term{symbol}term")

    def test_valid_query_is_normalized(self):
        self.assertEqual(validate_query("  water  project  "), "water project")


class ValidateEntityTypeKeysTests(SimpleTestCase):
    def test_valid_keys_deduplicated(self):
        result = validate_entity_type_keys(["programs.program", "programs.program"])
        self.assertEqual(result, ["programs.program"])

    def test_unknown_key_raises(self):
        with self.assertRaises(SearchValidationError):
            validate_entity_type_keys(["nonsense.thing"])

    def test_empty_value_is_fine(self):
        self.assertEqual(validate_entity_type_keys(None), [])


class CoerceEntityTypeKeysTests(SimpleTestCase):
    def test_string_input(self):
        result = coerce_entity_type_keys("programs.program, bogus.key")
        self.assertEqual(result, ["programs.program"])

    def test_list_input(self):
        result = coerce_entity_type_keys(
            ["programs.program", "documents.document", "bogus"]
        )
        self.assertEqual(result, ["programs.program", "documents.document"])

    def test_none_input(self):
        self.assertEqual(coerce_entity_type_keys(None), [])
