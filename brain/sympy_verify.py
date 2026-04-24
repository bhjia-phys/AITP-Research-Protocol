"""SymPy-based mathematical verification for theoretical physics derivations.

Pure symbolic checks — no LLM involved. Catches dimensional errors,
algebraic mistakes, and limit-behavior violations before claims enter L2.

Integration: called from mcp_server.py MCP tools, requires sympy installed.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Dimension system
# ---------------------------------------------------------------------------

# Base dimensions as (mass, length, time, charge, temperature)
# A physical quantity's dimension is represented as a tuple of exponents.
# e.g., velocity = L/T = (0, 1, -1, 0, 0)

_DIMENSION_MAP: dict[str, tuple[int, int, int, int, int]] = {
    # Base
    "mass": (1, 0, 0, 0, 0),
    "length": (0, 1, 0, 0, 0),
    "time": (0, 0, 1, 0, 0),
    "charge": (0, 0, 0, 1, 0),
    "temperature": (0, 0, 0, 0, 1),
    # Derived — mechanics
    "velocity": (0, 1, -1, 0, 0),
    "speed": (0, 1, -1, 0, 0),
    "acceleration": (0, 1, -2, 0, 0),
    "force": (1, 1, -2, 0, 0),
    "energy": (1, 2, -2, 0, 0),
    "work": (1, 2, -2, 0, 0),
    "action": (1, 2, -1, 0, 0),
    "momentum": (1, 1, -1, 0, 0),
    "pressure": (1, -1, -2, 0, 0),
    "power": (1, 2, -3, 0, 0),
    "frequency": (0, 0, -1, 0, 0),
    "angular_frequency": (0, 0, -1, 0, 0),
    "wavenumber": (0, -1, 0, 0, 0),
    "area": (0, 2, 0, 0, 0),
    "volume": (0, 3, 0, 0, 0),
    "density": (1, -3, 0, 0, 0),
    "angular_momentum": (1, 2, -1, 0, 0),
    "torque": (1, 2, -2, 0, 0),
    "moment_of_inertia": (1, 2, 0, 0, 0),
    # Electromagnetic
    "electric_field": (1, 1, -3, -1, 0),
    "magnetic_field": (1, 0, -2, -1, 0),
    "electric_potential": (1, 2, -3, -1, 0),
    "capacitance": (-1, -2, 4, 2, 0),
    "inductance": (1, 2, -2, -2, 0),
    "resistance": (1, 2, -3, -2, 0),
    "conductance": (-1, -2, 3, 2, 0),
    "permittivity": (-1, -3, 4, 2, 0),
    "permeability": (1, 1, -2, -2, 0),
    # Quantum
    "wavefunction": (0, -1, 0, 0, 0),  # 1/sqrt(L) in 1D; simplified
    "probability_density": (0, -1, 0, 0, 0),  # 1/L in 1D
    "cross_section": (0, 2, 0, 0, 0),
    # Thermodynamic
    "entropy": (1, 2, -2, 0, -1),
    "heat_capacity": (1, 2, -2, 0, -1),
    "thermal_conductivity": (1, 1, -3, 0, -1),
    # Dimensionless
    "dimensionless": (0, 0, 0, 0, 0),
    "number": (0, 0, 0, 0, 0),
    "angle": (0, 0, 0, 0, 0),
    "pure_number": (0, 0, 0, 0, 0),
    "constant": (0, 0, 0, 0, 0),
}

# Human-readable dimension names
_DIM_NAMES = ["mass", "length", "time", "charge", "temperature"]


def _dim_to_str(dim: tuple[int, ...]) -> str:
    """Convert a dimension tuple to a human-readable string."""
    parts = []
    for i, exp in enumerate(dim):
        if exp != 0:
            name = _DIM_NAMES[i]
            if exp == 1:
                parts.append(name)
            else:
                parts.append(f"{name}^{exp}")
    return " * ".join(parts) if parts else "dimensionless"


def _parse_dimension(name: str) -> tuple[int, ...] | None:
    """Parse a named dimension. Supports composite like 'energy' and
    power notation like 'mass * length^2 / time^2'."""
    name = name.strip().lower().replace(" ", "")
    if name in _DIMENSION_MAP:
        return _DIMENSION_MAP[name]

    # Try to parse composite: "mass*length^2/time^2"
    try:
        total = [0, 0, 0, 0, 0]
        # Split by * and /
        if "/" in name:
            num, den = name.split("/", 1)
        else:
            num, den = name, ""

        for part in re.findall(r'([a-z_]+)(\^?)(-?\d*)', num):
            base_name, hat, exp_str = part
            if hat != "^":
                continue
            exp = int(exp_str) if exp_str else 1
            if base_name in _DIMENSION_MAP:
                base_dim = _DIMENSION_MAP[base_name]
                for i in range(5):
                    total[i] += base_dim[i] * exp

        for part in re.findall(r'([a-z_]+)(\^?)(-?\d*)', den):
            base_name, hat, exp_str = part
            if hat != "^":
                continue
            exp = int(exp_str) if exp_str else 1
            if base_name in _DIMENSION_MAP:
                base_dim = _DIMENSION_MAP[base_name]
                for i in range(5):
                    total[i] -= base_dim[i] * exp

        if any(total):
            return tuple(total)
    except (ValueError, IndexError):
        pass

    return None


# ---------------------------------------------------------------------------
# Dimensional analysis
# ---------------------------------------------------------------------------

def check_dimensions(
    expression: str,
    variable_dimensions: dict[str, str],
) -> dict[str, Any]:
    """Verify dimensional consistency of a physics equation.

    Args:
        expression: A physics equation like "E = m * c**2" or "H = hbar * omega * (N + 1/2)"
        variable_dimensions: Map of variable name → dimension name.
            e.g., {"E": "energy", "m": "mass", "c": "velocity"}

    Returns:
        Dict with:
        - pass: bool — whether dimensions are consistent
        - lhs_dimension: str — human-readable LHS dimension
        - rhs_dimension: str — human-readable RHS dimension
        - details: list[str] — term-by-term breakdown
    """
    expression = expression.strip()

    # Parse LHS and RHS
    if "=" not in expression:
        return {
            "pass": False,
            "error": "Expression does not contain '='. Provide an equation like 'E = m * c^2'.",
        }

    lhs_raw, rhs_raw = expression.split("=", 1)
    lhs_raw = lhs_raw.strip()
    rhs_raw = rhs_raw.strip()

    # Parse LHS: a single variable or simple product
    lhs_dim = _parse_expression_dimension(lhs_raw, variable_dimensions)
    if lhs_dim is None:
        return {
            "pass": False,
            "error": f"Cannot determine dimension of LHS '{lhs_raw}'. "
                      f"Ensure all variables have dimension entries: {list(variable_dimensions.keys())}",
        }
    lhs_str = _dim_to_str(lhs_dim)

    # Parse RHS: sum of terms, each term is a product of factors
    rhs_terms = _split_terms(rhs_raw)
    term_dims = []
    details = []
    all_consistent = True

    for term in rhs_terms:
        term = term.strip()
        if not term:
            continue
        dim = _parse_expression_dimension(term, variable_dimensions)
        if dim is None:
            details.append(f"TERM '{term}': UNKNOWN (need dimension for each variable)")
            all_consistent = False
            continue
        dim_str = _dim_to_str(dim)
        consistent = dim == lhs_dim
        status = "PASS" if consistent else "MISMATCH"
        if not consistent:
            all_consistent = False
        details.append(f"TERM '{term}': [{dim_str}] — {status}")
        term_dims.append(dim)

    if not term_dims:
        return {"pass": False, "error": "No valid terms found on RHS."}

    return {
        "pass": all_consistent,
        "lhs": lhs_raw,
        "lhs_dimension": lhs_str,
        "rhs_dimensions": [_dim_to_str(d) for d in term_dims],
        "details": details,
        "verdict": (
            "All terms dimensionally consistent."
            if all_consistent
            else "DIMENSIONAL MISMATCH: some RHS terms do not match LHS."
        ),
    }


def _split_by_operator(expr: str, op: str) -> list[str]:
    """Split expression by operator at depth 0 (respecting parentheses)."""
    parts = []
    depth = 0
    current = []
    op_len = len(op)
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch in "([{":
            depth += 1
            current.append(ch)
        elif ch in ")]}":
            depth -= 1
            current.append(ch)
        elif depth == 0 and expr[i:i + op_len] == op:
            parts.append("".join(current))
            current = []
            i += op_len
            continue
        else:
            current.append(ch)
        i += 1
    if current:
        parts.append("".join(current))
    return parts


def _split_terms(expr: str) -> list[str]:
    """Split an expression into additive terms, respecting parentheses."""
    terms = []
    depth = 0
    current = []
    for ch in expr:
        if ch in "([{":
            depth += 1
            current.append(ch)
        elif ch in ")]}":
            depth -= 1
            current.append(ch)
        elif ch in "+-" and depth == 0 and current:
            # Check if this is a binary +/- (not part of a number exponent like e-5)
            stripped = "".join(current).rstrip()
            if stripped and stripped[-1] not in "eE^*/":
                terms.append("".join(current))
                current = [ch] if ch == "-" else []
                continue
            current.append(ch)
        else:
            current.append(ch)
    if current:
        terms.append("".join(current))
    return terms


def _parse_expression_dimension(
    expr: str,
    var_dims: dict[str, str],
) -> tuple[int, ...] | None:
    """Parse the dimension of an expression term.

    Handles: variables, products, powers, fractions.
    Returns dimension tuple or None if any variable has unknown dimension.
    """
    total = [0, 0, 0, 0, 0]

    # Normalize: remove whitespace, handle ** and ^
    expr = expr.strip()
    expr = expr.replace("**", "^")

    # Check for pure numbers (including fractions like 1/2)
    stripped = expr.strip("() ")
    # Try to match pure number: integer, decimal, or simple fraction
    if re.match(r'^[+-]?\d+(\.\d+)?(/\d+(\.\d+)?)?$', stripped):
        return (0, 0, 0, 0, 0)

    # Split into factors by * at depth 0 (respecting parentheses)
    factors_raw = _split_by_operator(expr, "*")
    factors = []
    for f in factors_raw:
        f = f.strip()
        if not f:
            continue
        # Preserve parenthesized sums/differences — don't split internal /
        if f.startswith("(") and f.endswith(")"):
            factors.append(f)
            continue
        f_clean = f.strip("() ")
        if not f_clean:
            continue
        # Check for fraction bar within this atomic factor (no +/- to avoid sum splitting)
        if "/" in f_clean and "+" not in f_clean and "-" not in f_clean:
            sub_parts = f_clean.split("/")
            # Numerator
            for num_part in sub_parts[0].split("*"):
                num_part = num_part.strip("() ")
                if num_part:
                    factors.append(num_part)
            # Denominator — each factor gets ^-1
            for sp in sub_parts[1:]:
                # Strip outer parens if present, then split by *
                sp_clean = sp.strip("() ")
                for den_part in sp_clean.split("*"):
                    den_part = den_part.strip()
                    if den_part:
                        factors.append(f"{den_part}^-1")
        else:
            factors.append(f_clean)

    for factor in factors:
        factor_stripped = factor.strip()
        if not factor_stripped:
            continue

        # Handle parenthesized sub-expressions like (N + 1/2):
        # the dimension of a sum is the dimension of any term (must all match)
        if factor_stripped.startswith("(") and factor_stripped.endswith(")"):
            inner = factor_stripped[1:-1].strip()
            sub_terms = _split_terms(inner)
            sub_dims = []
            for st in sub_terms:
                st = st.strip()
                if not st:
                    continue
                sd = _parse_expression_dimension(st, var_dims)
                if sd is None:
                    return None
                sub_dims.append(sd)
            if sub_dims:
                # All sub-terms must have the same dimension
                if any(d != sub_dims[0] for d in sub_dims):
                    return None  # inconsistent sum
                # Contribute the dimension of the sum
                result = sub_dims[0]
                for i in range(5):
                    total[i] += result[i]
                continue
            # Empty sum → dimensionless
            continue

        # Standard case: strip outer parens for non-sum factors
        factor = factor_stripped.strip("() ")
        if not factor:
            continue

        # Check for power: base^exp
        if "^" in factor:
            base_raw, exp_raw = factor.rsplit("^", 1)
            base_raw = base_raw.strip("() ")
            exp_raw = exp_raw.strip("() ")
            try:
                exp_val = float(exp_raw)
            except ValueError:
                # Non-numeric exponent — treat as symbolic, skip
                continue
        else:
            base_raw = factor
            exp_val = 1.0

        # Try to parse the base
        if re.match(r'^[+-]?\d+(\.\d+)?$', base_raw):
            continue  # Pure number, dimensionless

        dim = _resolve_base_dimension(base_raw, var_dims)
        if dim is None:
            return None

        for i in range(5):
            total[i] += int(dim[i] * exp_val)

    return tuple(total)


def _resolve_base_dimension(
    base: str,
    var_dims: dict[str, str],
) -> tuple[int, ...] | None:
    """Resolve a variable or named constant to its dimension tuple."""
    base_clean = base.strip("() ")
    # Check variable map
    for var_name, dim_name in var_dims.items():
        # Normalize both for matching
        if _normalize_var(var_name) == _normalize_var(base_clean):
            dim = _parse_dimension(dim_name)
            if dim is not None:
                return dim
            # dim_name might itself be a composite
            # Try base dimensions directly
            if dim_name.lower().replace(" ", "") in _DIMENSION_MAP:
                return _DIMENSION_MAP[dim_name.lower().replace(" ", "")]
    return None


def _normalize_var(name: str) -> str:
    """Normalize variable names for matching: remove sub/superscript markers."""
    name = name.strip("() ").lower()
    # Remove LaTeX-like _ and ^ suffixes
    name = re.sub(r'[_^]\{[^}]*\}', '', name)
    name = re.sub(r'[_^]\w', '', name)
    return name


# ---------------------------------------------------------------------------
# Algebraic identity verification (SymPy)
# ---------------------------------------------------------------------------

def check_algebra(
    lhs: str,
    rhs: str,
    assumptions: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Verify an algebraic identity using SymPy.

    Args:
        lhs: Left-hand side expression string (SymPy-compatible syntax)
        rhs: Right-hand side expression string
        assumptions: Optional dict of variable→definition mappings.
            e.g., {"N": "a_dag * a", "hbar": "h/(2*pi)"}

    Returns:
        Dict with pass, simplified_difference, and details.
    """
    try:
        import sympy
    except ImportError:
        return {
            "pass": False,
            "error": "SymPy is not installed. Run: pip install sympy",
        }

    try:
        # Build local symbol namespace
        namespace: dict[str, Any] = {}

        # Parse assumptions first (they may define new symbols)
        if assumptions:
            for var, defn in assumptions.items():
                try:
                    namespace[var] = sympy.sympify(defn)
                except sympy.SympifyError as e:
                    return {"pass": False, "error": f"Cannot parse assumption '{var} = {defn}': {e}"}

        # Parse LHS and RHS
        try:
            lhs_expr = sympy.sympify(lhs, locals=namespace)
        except sympy.SympifyError as e:
            return {"pass": False, "error": f"Cannot parse LHS '{lhs}': {e}"}

        try:
            rhs_expr = sympy.sympify(rhs, locals=namespace)
        except sympy.SympifyError as e:
            return {"pass": False, "error": f"Cannot parse RHS '{rhs}': {e}"}

        # Compute difference
        diff = sympy.simplify(lhs_expr - rhs_expr)

        # Handle operator-level checks (non-commutative)
        # If expressions contain non-commutative symbols, use expand
        if diff.free_symbols:
            diff_expanded = sympy.expand(diff)
        else:
            diff_expanded = diff

        is_zero = diff_expanded == 0

        return {
            "pass": is_zero,
            "lhs": str(lhs_expr),
            "rhs": str(rhs_expr),
            "simplified_difference": str(diff_expanded),
            "verdict": (
                "Algebraic identity verified: LHS = RHS."
                if is_zero
                else f"IDENTITY FAILS: LHS - RHS = {diff_expanded} ≠ 0"
            ),
        }

    except Exception as e:
        return {"pass": False, "error": f"SymPy evaluation error: {e}"}


# ---------------------------------------------------------------------------
# Limit behavior check
# ---------------------------------------------------------------------------

def check_limit(
    expression: str,
    limit_var: str,
    limit_value: str,
    expected: str,
    assumptions: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Verify that an expression reduces to expected value in a limit.

    Args:
        expression: The expression to check, e.g., "(n + 1/2) * hbar * omega"
        limit_var: The variable approaching the limit, e.g., "n"
        limit_value: The limit value, e.g., "oo" (infinity), "0"
        expected: Expected limiting form, e.g., "n * hbar * omega"
        assumptions: Optional symbol definitions

    Returns:
        Dict with pass, limit_result, expected, and details.
    """
    try:
        import sympy
    except ImportError:
        return {
            "pass": False,
            "error": "SymPy is not installed. Run: pip install sympy",
        }

    try:
        namespace: dict[str, Any] = {}
        if assumptions:
            for var, defn in assumptions.items():
                namespace[var] = sympy.sympify(defn)

        expr = sympy.sympify(expression, locals=namespace)
        expected_expr = sympy.sympify(expected, locals=namespace)
        var = sympy.Symbol(limit_var)

        # Compute limit
        if limit_value == "oo":
            limit_val = sympy.oo
        elif limit_value == "-oo":
            limit_val = -sympy.oo
        else:
            limit_val = sympy.sympify(limit_value)

        result = sympy.limit(expr, var, limit_val)
        diff = sympy.simplify(result - expected_expr)

        is_match = diff == 0

        return {
            "pass": is_match,
            "expression": str(expr),
            "limit": f"{limit_var} → {limit_value}",
            "limit_result": str(result),
            "expected": str(expected_expr),
            "difference": str(diff),
            "verdict": (
                "Limit matches expected value."
                if is_match
                else f"LIMIT MISMATCH: computed {result}, expected {expected_expr}"
            ),
        }

    except Exception as e:
        return {"pass": False, "error": f"SymPy evaluation error: {e}"}


# ---------------------------------------------------------------------------
# Derivation step verification — Physics Derivation Graph approach
# ---------------------------------------------------------------------------
# Each physics inference rule has a generic validation function that checks
# whether the rule was correctly applied, independent of the specific equation.
# This is the key insight from the Physics Derivation Graph project.

INFERENCE_RULES = [
    "multiply_both_sides",
    "divide_both_sides",
    "add_to_both_sides",
    "subtract_from_both_sides",
    "substitute",
    "expand",
    "factor",
    "simplify",
    "differentiate",
    "integrate",
    "take_limit",
    "series_expand",
    "commutator_eval",
    "apply_identity",
    "rearrange",
]

INFERENCE_RULE_DESCRIPTIONS: dict[str, str] = {
    "multiply_both_sides": "Multiply both sides of an equation by a factor",
    "divide_both_sides": "Divide both sides of an equation by a (non-zero) factor",
    "add_to_both_sides": "Add an expression to both sides",
    "subtract_from_both_sides": "Subtract an expression from both sides",
    "substitute": "Substitute a variable or expression with another",
    "expand": "Expand products and powers algebraically",
    "factor": "Factor an expression",
    "simplify": "Simplify an expression using algebraic identities",
    "differentiate": "Differentiate w.r.t. a variable",
    "integrate": "Integrate w.r.t. a variable",
    "take_limit": "Take the limit as a variable approaches a value",
    "series_expand": "Series expand to given order around a point",
    "commutator_eval": "Evaluate a commutator [A, B] = AB - BA",
    "apply_identity": "Apply a known mathematical/physical identity",
    "rearrange": "Rearrange terms (commutative/associative operations)",
}


def _sympy_parse(expr_str: str, namespace: dict) -> "sympy.Expr":
    """Parse a string into a SymPy expression, handling 'A = B' as Eq(A, B)."""
    import sympy
    stripped = expr_str.strip()
    # Handle equation notation "A = B" → Eq(A, B)
    if "=" in stripped and not stripped.startswith("="):
        # Split on first = that is not part of == or !=
        parts = re.split(r"(?<![=!<>])=(?!=)", stripped, maxsplit=1)
        if len(parts) == 2:
            lhs = sympy.sympify(parts[0].strip(), locals=namespace)
            rhs = sympy.sympify(parts[1].strip(), locals=namespace)
            return sympy.Eq(lhs, rhs)
    return sympy.sympify(stripped, locals=namespace)


def validate_derivation_step(
    rule: str,
    input_expr: str,
    output_expr: str,
    argument: str = "",
    assumptions: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Validate a single derivation step using the specified inference rule.

    Each rule has a generic SymPy-based validator that checks whether the
    output correctly follows from the input using this rule.

    Args:
        rule: One of INFERENCE_RULES
        input_expr: The expression/equation before the operation
        output_expr: The expression/equation after the operation
        argument: The argument to the rule (factor, variable, identity, etc.)
        assumptions: Optional symbol definitions

    Returns:
        Dict with pass, rule, input, output, verification_method, and details.
    """
    if rule not in INFERENCE_RULES:
        return {
            "pass": False,
            "error": f"Unknown rule '{rule}'. Available: {INFERENCE_RULES}",
        }

    try:
        import sympy
    except ImportError:
        return {"pass": False, "error": "SymPy is not installed."}

    namespace: dict[str, Any] = {}
    if assumptions:
        for var, defn in assumptions.items():
            try:
                namespace[var] = sympy.sympify(defn)
            except sympy.SympifyError:
                pass

    try:
        inp = _sympy_parse(input_expr, namespace)
        out = _sympy_parse(output_expr, namespace)
    except (sympy.SympifyError, SyntaxError) as e:
        return {"pass": False, "error": f"Cannot parse expression: {e}"}

    try:
        validator = _RULE_VALIDATORS[rule]
        result = validator(inp, out, argument, namespace)
        result["rule"] = rule
        result["verification_method"] = f"sympy.{rule}"
        return result
    except Exception as e:
        return {
            "pass": False,
            "rule": rule,
            "error": f"Validation error: {e}",
        }


def _parse_equation(expr: "sympy.Expr") -> tuple["sympy.Expr", "sympy.Expr"] | None:
    """If expr is an Eq, return (lhs, rhs). Otherwise return None."""
    import sympy
    if isinstance(expr, sympy.Equality):
        return expr.lhs, expr.rhs
    return None


# ---- Per-rule SymPy validators ----

def _v_multiply_both_sides(inp, out, arg, ns):
    import sympy
    factor = sympy.sympify(arg, locals=ns) if arg else sympy.sympify("1")
    eq = _parse_equation(inp)
    if eq is not None:
        lhs, rhs = eq
        expected = sympy.Eq(sympy.simplify(lhs * factor), sympy.simplify(rhs * factor))
    else:
        expected = sympy.simplify(inp * factor)
    if isinstance(expected, sympy.Equality):
        ok = sympy.simplify(out.lhs - expected.lhs) == 0 and sympy.simplify(out.rhs - expected.rhs) == 0
    else:
        ok = sympy.simplify(out - expected) == 0
    return {"pass": ok, "expected": str(expected),
            "verdict": "Correct." if ok else f"MISMATCH: expected {expected}"}


def _v_divide_both_sides(inp, out, arg, ns):
    import sympy
    factor = sympy.sympify(arg, locals=ns) if arg else sympy.sympify("1")
    eq = _parse_equation(inp)
    if eq is not None:
        lhs, rhs = eq
        expected = sympy.Eq(sympy.simplify(lhs / factor), sympy.simplify(rhs / factor))
    else:
        expected = sympy.simplify(inp / factor)
    if isinstance(expected, sympy.Equality):
        ok = sympy.simplify(out.lhs - expected.lhs) == 0 and sympy.simplify(out.rhs - expected.rhs) == 0
    else:
        ok = sympy.simplify(out - expected) == 0
    return {"pass": ok, "expected": str(expected)}


def _v_add_to_both_sides(inp, out, arg, ns):
    import sympy
    term = sympy.sympify(arg, locals=ns) if arg else 0
    eq = _parse_equation(inp)
    if eq is not None:
        lhs, rhs = eq
        expected = sympy.Eq(sympy.simplify(lhs + term), sympy.simplify(rhs + term))
    else:
        expected = sympy.simplify(inp + term)
    if isinstance(expected, sympy.Equality):
        ok = sympy.simplify(out.lhs - expected.lhs) == 0 and sympy.simplify(out.rhs - expected.rhs) == 0
    else:
        ok = sympy.simplify(out - expected) == 0
    return {"pass": ok, "expected": str(expected)}


def _v_subtract_from_both_sides(inp, out, arg, ns):
    import sympy
    term = sympy.sympify(arg, locals=ns) if arg else 0
    eq = _parse_equation(inp)
    if eq is not None:
        lhs, rhs = eq
        expected = sympy.Eq(sympy.simplify(lhs - term), sympy.simplify(rhs - term))
    else:
        expected = sympy.simplify(inp - term)
    if isinstance(expected, sympy.Equality):
        ok = sympy.simplify(out.lhs - expected.lhs) == 0 and sympy.simplify(out.rhs - expected.rhs) == 0
    else:
        ok = sympy.simplify(out - expected) == 0
    return {"pass": ok, "expected": str(expected)}


def _v_substitute(inp, out, arg, ns):
    import sympy
    if not arg:
        return {"pass": False, "error": "Substitution requires argument like 'x=y'."}
    parts = re.split(r"\s*->\s*|\s*=\s*", arg, maxsplit=1)
    if len(parts) != 2:
        return {"pass": False, "error": f"Cannot parse substitution '{arg}'. Use 'old=new'."}
    old_sym = sympy.sympify(parts[0].strip(), locals=ns)
    new_expr = sympy.sympify(parts[1].strip(), locals=ns)
    expected = sympy.simplify(inp.subs(old_sym, new_expr))
    diff = sympy.simplify(out - expected)
    return {"pass": diff == 0, "expected": str(expected), "difference": str(diff)}


def _v_expand(inp, out, arg, ns):
    import sympy
    expected = sympy.expand(inp)
    diff = sympy.simplify(out - expected)
    return {"pass": diff == 0, "expected": str(expected), "difference": str(diff)}


def _v_factor(inp, out, arg, ns):
    import sympy
    expected = sympy.factor(inp)
    diff = sympy.simplify(out - expected)
    return {"pass": diff == 0, "expected": str(expected), "difference": str(diff)}


def _v_simplify(inp, out, arg, ns):
    import sympy
    diff = sympy.simplify(inp - out)
    is_eq = diff == 0
    if not is_eq:
        try:
            if inp.equals(out):
                is_eq = True
        except Exception:
            pass
    return {"pass": is_eq, "difference": str(diff)}


def _v_differentiate(inp, out, arg, ns):
    import sympy
    if not arg:
        return {"pass": False, "error": "Differentiation requires a variable argument."}
    var = sympy.sympify(arg.strip(), locals=ns)
    expected = sympy.diff(inp, var)
    diff = sympy.simplify(out - expected)
    return {"pass": diff == 0, "expected": str(expected), "difference": str(diff)}


def _v_integrate(inp, out, arg, ns):
    import sympy
    if not arg:
        return {"pass": False, "error": "Integration requires a variable argument."}
    var = sympy.sympify(arg.strip(), locals=ns)
    expected = sympy.integrate(inp, var)
    diff = sympy.simplify(out - expected)
    return {"pass": diff == 0, "expected": str(expected), "difference": str(diff)}


def _v_take_limit(inp, out, arg, ns):
    import sympy
    if not arg:
        return {"pass": False, "error": "Limit requires argument like 'x->0' or 'n->oo'."}
    parts = arg.split("->")
    if len(parts) != 2:
        return {"pass": False, "error": f"Limit format: 'var->value'. Got: '{arg}'."}
    var = sympy.sympify(parts[0].strip(), locals=ns)
    val_str = parts[1].strip()
    val = sympy.oo if val_str == "oo" else (-sympy.oo if val_str == "-oo" else sympy.sympify(val_str, locals=ns))
    expected = sympy.limit(inp, var, val)
    diff = sympy.simplify(out - expected)
    return {"pass": diff == 0, "expected": str(expected), "difference": str(diff)}


def _v_series_expand(inp, out, arg, ns):
    import sympy
    if not arg:
        return {"pass": False, "error": "Series requires argument like 'x,3'."}
    parts = [p.strip() for p in arg.split(",")]
    if len(parts) < 2:
        return {"pass": False, "error": f"Series format: 'var,order'. Got: '{arg}'."}
    var = sympy.sympify(parts[0], locals=ns)
    point = 0 if len(parts) == 2 else sympy.sympify(parts[1], locals=ns)
    order = int(parts[1] if len(parts) == 2 else parts[2])
    expected = sympy.series(inp, var, point, order).removeO()
    diff = sympy.simplify(out - expected)
    return {"pass": diff == 0, "expected": str(expected), "difference": str(diff)}


def _v_commutator_eval(inp, out, arg, ns):
    import sympy
    diff = sympy.simplify(inp - out)
    is_eq = diff == 0
    if not is_eq:
        try:
            if inp.equals(out):
                is_eq = True
        except Exception:
            pass
    return {"pass": is_eq, "difference": str(diff)}


def _v_apply_identity(inp, out, arg, ns):
    import sympy
    if not arg:
        return {"pass": False, "error": "apply_identity requires the identity as argument."}
    parts = re.split(r"\s*=\s*", arg, maxsplit=1)
    if len(parts) == 2:
        old = sympy.sympify(parts[0].strip(), locals=ns)
        new = sympy.sympify(parts[1].strip(), locals=ns)
        expected = sympy.simplify(inp.subs(old, new))
    else:
        ident = sympy.sympify(arg, locals=ns)
        expected = sympy.simplify(inp.subs(ident, sympy.simplify(ident)))
    diff = sympy.simplify(out - expected)
    return {"pass": diff == 0, "expected": str(expected), "difference": str(diff)}


def _v_rearrange(inp, out, arg, ns):
    import sympy
    diff = sympy.simplify(inp - out)
    return {"pass": diff == 0, "difference": str(diff)}


_RULE_VALIDATORS: dict[str, Any] = {
    "multiply_both_sides": _v_multiply_both_sides,
    "divide_both_sides": _v_divide_both_sides,
    "add_to_both_sides": _v_add_to_both_sides,
    "subtract_from_both_sides": _v_subtract_from_both_sides,
    "substitute": _v_substitute,
    "expand": _v_expand,
    "factor": _v_factor,
    "simplify": _v_simplify,
    "differentiate": _v_differentiate,
    "integrate": _v_integrate,
    "take_limit": _v_take_limit,
    "series_expand": _v_series_expand,
    "commutator_eval": _v_commutator_eval,
    "apply_identity": _v_apply_identity,
    "rearrange": _v_rearrange,
}


def validate_derivation_chain(
    steps: list[dict[str, str]],
    assumptions: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Validate an entire derivation chain step by step.

    Args:
        steps: List of dicts, each with keys: rule, input_expr, output_expr, argument (optional)
        assumptions: Optional global symbol definitions

    Returns:
        Dict with overall pass/fail, per-step results, and summary.
    """
    results = []
    all_pass = True
    for i, step in enumerate(steps):
        rule = step.get("rule", "")
        inp = step.get("input_expr", "")
        out = step.get("output_expr", "")
        arg = step.get("argument", "")

        if not rule or not out:
            results.append({
                "step": i + 1, "pass": False,
                "error": "Missing required fields (rule, output_expr).",
                "step_input": step,
            })
            all_pass = False
            continue

        result = validate_derivation_step(rule, inp, out, arg, assumptions)
        result["step"] = i + 1
        results.append(result)
        if not result.get("pass"):
            all_pass = False

    return {
        "pass": all_pass,
        "total_steps": len(steps),
        "passed_steps": sum(1 for r in results if r.get("pass")),
        "failed_steps": sum(1 for r in results if not r.get("pass")),
        "results": results,
        "summary": (
            f"All {len(steps)} steps verified."
            if all_pass
            else f"{sum(1 for r in results if not r.get('pass'))}/{len(steps)} steps failed."
        ),
    }
