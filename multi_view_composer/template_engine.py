"""Template engine for rendering text overlays with variable substitution and conditional logic."""

from __future__ import annotations
import re
import operator
from typing import Dict, Any, Tuple, List

from .config import VariableConfig, ColorRule
from .logging_config import get_logger


logger = get_logger("template_engine")


# Precompiled regex patterns for performance
_VAR_PATTERN = re.compile(r'\{(\w+)\}')
_TEMPLATE_PATTERN = re.compile(r'\{(\w+)(:[^}]+)?\}')

# Supported operators for safe expression evaluation (ordered by length for correct matching)
OPERATORS = {
    '==': operator.eq,
    '!=': operator.ne,
    '<=': operator.le,
    '>=': operator.ge,
    '<': operator.lt,
    '>': operator.gt,
}


def _substitute_variables(expr: str, context: Dict[str, Any]) -> str:
    """Replace {variable} placeholders with their values from context."""
    def replace_var(match):
        var_name = match.group(1)
        if var_name in context:
            return str(context[var_name])
        return match.group(0)  # Keep original if not found

    return _VAR_PATTERN.sub(replace_var, expr)


def evaluate_condition(expr: str, context: Dict[str, Any]) -> bool:
    """
    Safely evaluate a condition expression.

    Supports expressions like:
    - "{laser_distance} > 44"
    - "{is_manual_review} == true"
    - "{robot_status} == 'ERROR'"

    Args:
        expr: Condition expression string
        context: Dictionary of variable values

    Returns:
        Boolean result of the condition
    """
    if not expr:
        return True

    # Substitute variables first
    substituted = _substitute_variables(expr, context)

    # Find operator
    for op_str, op_func in OPERATORS.items():
        if op_str in substituted:
            parts = substituted.split(op_str, 1)
            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()

                # Parse left side
                left_val = _parse_value(left, context)
                # Parse right side
                right_val = _parse_value(right, context)

                try:
                    return op_func(left_val, right_val)
                except (TypeError, ValueError):
                    return False

    # Handle simple boolean variable
    substituted = substituted.strip()
    if substituted.lower() == 'true':
        return True
    if substituted.lower() == 'false':
        return False

    # Try to get as boolean from context
    return bool(context.get(substituted, False))


def _parse_value(value_str: str, context: Dict[str, Any]) -> Any:
    """Parse a value string into its appropriate type."""
    value_str = value_str.strip()

    # Boolean literals
    if value_str.lower() == 'true':
        return True
    if value_str.lower() == 'false':
        return False

    # String literals (quoted)
    if (value_str.startswith("'") and value_str.endswith("'")) or \
       (value_str.startswith('"') and value_str.endswith('"')):
        return value_str[1:-1]

    # Try numeric
    try:
        if '.' in value_str:
            return float(value_str)
        return int(value_str)
    except ValueError:
        pass

    # Return as string
    return value_str


def evaluate_formula(expr: str, context: Dict[str, Any]) -> Any:
    """
    Safely evaluate a simple formula expression.

    Supports basic arithmetic: +, -, *, /

    Args:
        expr: Formula expression like "{laser_distance} * 0.1"
        context: Dictionary of variable values

    Returns:
        Computed result
    """
    # Substitute variables
    substituted = _substitute_variables(expr, context)

    # Only allow safe characters
    allowed = set('0123456789.+-*/ ()')
    if not all(c in allowed for c in substituted.replace(' ', '')):
        # Contains unsafe characters, return as-is
        try:
            return float(substituted)
        except ValueError:
            return substituted

    try:
        # Safe eval with no builtins
        result = eval(substituted, {"__builtins__": {}}, {})
        return result
    except (SyntaxError, NameError, TypeError, ZeroDivisionError) as e:
        logger.debug(f"Formula evaluation failed for '{expr}': {e}")
        return substituted


def resolve_variable(var_config: VariableConfig, context: Dict[str, Any]) -> Any:
    """
    Resolve a variable based on its configuration.

    Args:
        var_config: Variable configuration
        context: Current context with sensor data and computed variables

    Returns:
        Resolved variable value
    """
    if var_config.type == "direct":
        # Direct reference to a context variable
        if var_config.expr:
            var_name = var_config.expr.strip('{}')
            return context.get(var_name, var_config.expr)
        return None

    elif var_config.type == "formula":
        # Compute formula
        if var_config.expr:
            return evaluate_formula(var_config.expr, context)
        return None

    elif var_config.type == "conditional":
        # Evaluate conditions in order
        for cond in var_config.conditions:
            if cond.when is None:
                # This is the 'else' clause
                if cond.value is not None:
                    return cond.value
                if cond.format is not None:
                    return render_template(cond.format, context)
                return None

            if evaluate_condition(cond.when, context):
                if cond.value is not None:
                    return cond.value
                if cond.format is not None:
                    return render_template(cond.format, context)
                return None

        return None

    return None


def render_template(template: str, context: Dict[str, Any]) -> str:
    """
    Render a template string with variable substitution.

    Supports:
    - Simple substitution: {variable}
    - Formatted substitution: {variable:.2f}

    Args:
        template: Template string with placeholders
        context: Dictionary of variable values

    Returns:
        Rendered string
    """
    def replace_placeholder(match):
        full_match = match.group(0)  # e.g., "{distance_cm:.2f}"
        var_name = match.group(1)     # e.g., "distance_cm"
        format_spec = match.group(2)  # e.g., ":.2f" or None

        if var_name not in context:
            return full_match  # Keep original if not found

        value = context[var_name]

        if format_spec:
            try:
                # Apply format spec
                return format(value, format_spec[1:])  # Remove leading ':'
            except (ValueError, TypeError):
                return str(value)

        return str(value)

    return _TEMPLATE_PATTERN.sub(replace_placeholder, template)


def evaluate_color_rules(
    rules: List[ColorRule],
    context: Dict[str, Any],
    default_color: Tuple[int, int, int] = (255, 255, 255)
) -> Tuple[int, int, int]:
    """
    Evaluate color rules and return the first matching color.

    Args:
        rules: List of color rules to evaluate
        context: Variable context
        default_color: Color to return if no rules match

    Returns:
        BGR color tuple
    """
    for rule in rules:
        if rule.when is None:
            # This is the 'else' clause
            return rule.color

        if evaluate_condition(rule.when, context):
            return rule.color

    return default_color


def build_context(
    sensor_data: Dict[str, Any],
    variables: Dict[str, VariableConfig]
) -> Dict[str, Any]:
    """
    Build a context dictionary from sensor data and computed variables.

    Variables are resolved in order, allowing later variables to reference earlier ones.

    Args:
        sensor_data: Base sensor data dictionary
        variables: Variable configurations to compute

    Returns:
        Complete context dictionary
    """
    context = dict(sensor_data)

    # Resolve variables in order (may depend on each other)
    for var_name, var_config in variables.items():
        context[var_name] = resolve_variable(var_config, context)

    return context
