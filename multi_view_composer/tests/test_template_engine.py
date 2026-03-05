"""Tests for template_engine module."""

import pytest

from multi_view_composer import (
    render_template,
    evaluate_condition,
    evaluate_formula,
    resolve_variable,
    evaluate_color_rules,
    build_context,
)
from multi_view_composer.config import VariableConfig, VariableCondition, ColorRule


class TestRenderTemplate:
    def test_basic_substitution(self):
        result = render_template("Hello {name}", {"name": "World"})
        assert result == "Hello World"

    def test_format_specifier(self):
        result = render_template("Value: {val:.2f}", {"val": 3.14159})
        assert result == "Value: 3.14"

    def test_missing_variable_keeps_placeholder(self):
        result = render_template("Hello {name}", {})
        assert result == "Hello {name}"

    def test_multiple_variables(self):
        result = render_template("{a} + {b} = {c}", {"a": 1, "b": 2, "c": 3})
        assert result == "1 + 2 = 3"

    def test_integer_format(self):
        result = render_template("Count: {n:d}", {"n": 42})
        assert result == "Count: 42"


class TestEvaluateCondition:
    def test_equal(self):
        assert evaluate_condition("{x} == 5", {"x": 5}) is True
        assert evaluate_condition("{x} == 5", {"x": 3}) is False

    def test_not_equal(self):
        assert evaluate_condition("{x} != 5", {"x": 3}) is True
        assert evaluate_condition("{x} != 5", {"x": 5}) is False

    def test_less_than(self):
        assert evaluate_condition("{x} < 10", {"x": 5}) is True
        assert evaluate_condition("{x} < 10", {"x": 15}) is False

    def test_greater_than(self):
        assert evaluate_condition("{x} > 10", {"x": 15}) is True
        assert evaluate_condition("{x} > 10", {"x": 5}) is False

    def test_less_equal(self):
        assert evaluate_condition("{x} <= 10", {"x": 10}) is True
        assert evaluate_condition("{x} <= 10", {"x": 11}) is False

    def test_greater_equal(self):
        assert evaluate_condition("{x} >= 10", {"x": 10}) is True
        assert evaluate_condition("{x} >= 10", {"x": 9}) is False

    def test_and_operator(self):
        ctx = {"a": 5, "b": 10}
        assert evaluate_condition("{a} > 0 & {b} > 0", ctx) is True
        assert evaluate_condition("{a} > 0 & {b} < 0", ctx) is False

    def test_or_operator(self):
        ctx = {"a": 5, "b": -1}
        assert evaluate_condition("{a} > 0 | {b} > 0", ctx) is True
        assert evaluate_condition("{a} < 0 | {b} < 0", ctx) is True
        assert evaluate_condition("{a} < 0 | {b} > 0", ctx) is False

    def test_boolean_true(self):
        assert evaluate_condition("true", {}) is True

    def test_boolean_false(self):
        assert evaluate_condition("false", {}) is False

    def test_string_comparison(self):
        assert evaluate_condition("{mode} == 'auto'", {"mode": "auto"}) is True
        assert evaluate_condition("{mode} == 'auto'", {"mode": "manual"}) is False

    def test_empty_expression_returns_true(self):
        assert evaluate_condition("", {}) is True


class TestEvaluateFormula:
    def test_addition(self):
        result = evaluate_formula("{a} + {b}", {"a": 3, "b": 4})
        assert result == 7

    def test_subtraction(self):
        result = evaluate_formula("{a} - {b}", {"a": 10, "b": 3})
        assert result == 7

    def test_multiplication(self):
        result = evaluate_formula("{speed} * 3.6", {"speed": 10})
        assert result == pytest.approx(36.0)

    def test_division(self):
        result = evaluate_formula("{a} / {b}", {"a": 10, "b": 2})
        assert result == pytest.approx(5.0)

    def test_parentheses(self):
        result = evaluate_formula("({a} + {b}) * 2", {"a": 3, "b": 4})
        assert result == 14

    def test_variable_substitution(self):
        result = evaluate_formula("{x} * 100", {"x": 0.5})
        assert result == pytest.approx(50.0)


class TestResolveVariable:
    def test_direct_type(self):
        config = VariableConfig(type="direct", expr="{temperature}")
        result = resolve_variable(config, {"temperature": 42.0})
        assert result == 42.0

    def test_formula_type(self):
        config = VariableConfig(type="formula", expr="{speed} * 3.6")
        result = resolve_variable(config, {"speed": 10})
        assert result == pytest.approx(36.0)

    def test_conditional_with_match(self):
        config = VariableConfig(
            type="conditional",
            conditions=[
                VariableCondition(when="{mode} == 'auto'", value="AUTO"),
                VariableCondition(when="{mode} == 'manual'", value="MANUAL"),
                VariableCondition(when=None, value="STANDBY"),
            ],
        )
        result = resolve_variable(config, {"mode": "auto"})
        assert result == "AUTO"

    def test_conditional_falls_through_to_else(self):
        config = VariableConfig(
            type="conditional",
            conditions=[
                VariableCondition(when="{mode} == 'auto'", value="AUTO"),
                VariableCondition(when=None, value="STANDBY"),
            ],
        )
        result = resolve_variable(config, {"mode": "manual"})
        assert result == "STANDBY"

    def test_conditional_with_format(self):
        config = VariableConfig(
            type="conditional",
            conditions=[
                VariableCondition(when="{val} < 10", value="LOW!"),
                VariableCondition(when=None, format="{val:.0f}%"),
            ],
        )
        result = resolve_variable(config, {"val": 75})
        assert result == "75%"

    def test_direct_with_no_expr_returns_none(self):
        config = VariableConfig(type="direct")
        result = resolve_variable(config, {})
        assert result is None


class TestEvaluateColorRules:
    def test_matching_first_rule(self):
        rules = [
            ColorRule(color=(0, 255, 0), when="{level} >= 70"),
            ColorRule(color=(0, 200, 255), when="{level} >= 30"),
            ColorRule(color=(0, 0, 255), when=None),
        ]
        result = evaluate_color_rules(rules, {"level": 80})
        assert result == (0, 255, 0)

    def test_matching_second_rule(self):
        rules = [
            ColorRule(color=(0, 255, 0), when="{level} >= 70"),
            ColorRule(color=(0, 200, 255), when="{level} >= 30"),
            ColorRule(color=(0, 0, 255), when=None),
        ]
        result = evaluate_color_rules(rules, {"level": 50})
        assert result == (0, 200, 255)

    def test_fallback_to_else(self):
        rules = [
            ColorRule(color=(0, 255, 0), when="{level} >= 70"),
            ColorRule(color=(0, 0, 255), when=None),
        ]
        result = evaluate_color_rules(rules, {"level": 10})
        assert result == (0, 0, 255)

    def test_no_match_returns_default(self):
        rules = [
            ColorRule(color=(0, 255, 0), when="{level} >= 70"),
        ]
        result = evaluate_color_rules(rules, {"level": 10})
        assert result == (255, 255, 255)

    def test_custom_default_color(self):
        rules = []
        result = evaluate_color_rules(rules, {}, default_color=(128, 128, 128))
        assert result == (128, 128, 128)


class TestBuildContext:
    def test_merges_sensor_data(self):
        ctx = build_context({"temp": 25, "speed": 10}, {})
        assert ctx["temp"] == 25
        assert ctx["speed"] == 10

    def test_resolves_variables(self):
        variables = {
            "speed_kmh": VariableConfig(type="formula", expr="{speed} * 3.6"),
        }
        ctx = build_context({"speed": 10}, variables)
        assert ctx["speed"] == 10
        assert ctx["speed_kmh"] == pytest.approx(36.0)

    def test_variables_can_reference_earlier_variables(self):
        variables = {
            "doubled": VariableConfig(type="formula", expr="{val} * 2"),
            "quadrupled": VariableConfig(type="formula", expr="{doubled} * 2"),
        }
        ctx = build_context({"val": 5}, variables)
        assert ctx["doubled"] == 10
        assert ctx["quadrupled"] == 20

    def test_does_not_mutate_input(self):
        sensor_data = {"temp": 25}
        build_context(sensor_data, {})
        assert sensor_data == {"temp": 25}
