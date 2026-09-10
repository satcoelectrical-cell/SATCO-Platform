from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from .contracts import ComparisonResult, QuantityV1, RangeV1


def _result(value: bool) -> ComparisonResult:
    return ComparisonResult("satisfied" if value else "violated")


def _same(left: Any, right: Any) -> tuple[Any, Any] | None:
    if isinstance(left, QuantityV1) and isinstance(right, QuantityV1):
        return (left.canonical_magnitude, right.canonical_magnitude) if left.dimension == right.dimension else None
    if isinstance(left, bool) != isinstance(right, bool): return None
    if type(left) is not type(right): return None
    return left, right


def equal(left: Any, right: Any) -> ComparisonResult:
    pair = _same(left, right)
    return ComparisonResult("indeterminate", "unsupported_value") if pair is None else _result(pair[0] == pair[1])


def not_equal(left: Any, right: Any) -> ComparisonResult:
    result = equal(left, right)
    if result.outcome == "satisfied": return ComparisonResult("violated")
    if result.outcome == "violated": return ComparisonResult("satisfied")
    return result


def _range_value(value: Any) -> Any:
    return value.canonical_magnitude if isinstance(value, QuantityV1) else value


def range_contains(container: RangeV1, value: Any) -> ComparisonResult:
    try:
        lower, upper = _range_value(container.lower), _range_value(container.upper)
        if type(lower) is not type(upper) or lower > upper:
            return ComparisonResult("indeterminate", "unsupported_value")
        target_lo, target_hi = (_range_value(value.lower), _range_value(value.upper)) if isinstance(value, RangeV1) else (_range_value(value), _range_value(value))
        if type(target_lo) is not type(lower) or type(target_hi) is not type(upper):
            return ComparisonResult("indeterminate", "unsupported_value")
        low_ok = target_lo > lower or (
            container.lower_inclusive
            and (not isinstance(value, RangeV1) or value.lower_inclusive)
            and target_lo == lower
        )
        high_ok = target_hi < upper or (
            container.upper_inclusive
            and (not isinstance(value, RangeV1) or value.upper_inclusive)
            and target_hi == upper
        )
        ok = low_ok and high_ok
        return _result(ok)
    except (TypeError, AttributeError): return ComparisonResult("indeterminate", "unsupported_value")


def range_overlaps(left: RangeV1, right: RangeV1) -> ComparisonResult:
    try:
        lu, rl = _range_value(left.upper), _range_value(right.lower)
        ru, ll = _range_value(right.upper), _range_value(left.lower)
        if not (type(lu) is type(rl) is type(ru) is type(ll)):
            return ComparisonResult("indeterminate", "unsupported_value")
        separated = lu < rl or ru < ll
        touching_excluded = (
            lu == rl and not (left.upper_inclusive and right.lower_inclusive)
        ) or (
            ru == ll and not (right.upper_inclusive and left.lower_inclusive)
        )
        return _result(not separated and not touching_excluded)
    except TypeError: return ComparisonResult("indeterminate", "unsupported_value")


def within_absolute_tolerance(left: Any, right: Any, tolerance: Decimal | QuantityV1) -> ComparisonResult:
    pair = _same(left, right)
    if pair is None: return ComparisonResult("indeterminate", "unsupported_value")
    tol = tolerance.canonical_magnitude if isinstance(tolerance, QuantityV1) else tolerance
    try:
        if tol < 0: return ComparisonResult("indeterminate", "unsupported_value")
        return _result(abs(pair[0] - pair[1]) <= tol)
    except TypeError: return ComparisonResult("indeterminate", "unsupported_value")


def enum_map_equal(left: str, right: str, mapping: dict[str, str]) -> ComparisonResult:
    if left not in mapping: return ComparisonResult("indeterminate", "unsupported_value")
    return _result(mapping[left] == right)


def set_contains(container: tuple[Any, ...] | frozenset[Any], value: Any) -> ComparisonResult:
    if len(container) > 64 or (isinstance(value, (tuple, frozenset, list)) and len(value) > 64):
        return ComparisonResult("indeterminate", "resource_limit_exceeded")
    try: return _result(set(value).issubset(set(container)) if isinstance(value, (tuple, frozenset, list)) else value in container)
    except TypeError: return ComparisonResult("indeterminate", "unsupported_value")


def set_equal(left: tuple[Any, ...] | frozenset[Any], right: tuple[Any, ...] | frozenset[Any]) -> ComparisonResult:
    if len(left) > 64 or len(right) > 64:
        return ComparisonResult("indeterminate", "resource_limit_exceeded")
    try: return _result(set(left) == set(right))
    except TypeError: return ComparisonResult("indeterminate", "unsupported_value")


def present(value: str, complete: bool) -> ComparisonResult:
    if value == "present": return ComparisonResult("satisfied")
    if value == "absent" and complete: return ComparisonResult("violated")
    return ComparisonResult("indeterminate", "source_incomplete")


def stale_after(observed_at: datetime, reference_at: datetime, threshold_seconds: int) -> ComparisonResult:
    if observed_at.tzinfo is None or reference_at.tzinfo is None or threshold_seconds < 0: return ComparisonResult("indeterminate", "unsupported_value")
    if observed_at > reference_at:
        return ComparisonResult("indeterminate", "source_ambiguous")
    return _result((reference_at - observed_at).total_seconds() <= threshold_seconds)


def disagrees(left: Any, right: Any) -> ComparisonResult:
    return not_equal(left, right)


def applicable_if(*conditions: bool | None) -> ComparisonResult:
    if any(condition is None for condition in conditions): return ComparisonResult("indeterminate", "source_incomplete")
    return ComparisonResult("satisfied" if all(conditions) else "not_applicable")


HANDLERS = {
    name: globals()[name]
    for name in (
        "equal", "not_equal", "range_contains", "range_overlaps",
        "within_absolute_tolerance", "enum_map_equal", "set_contains",
        "set_equal", "present", "stale_after", "disagrees", "applicable_if",
    )
}
