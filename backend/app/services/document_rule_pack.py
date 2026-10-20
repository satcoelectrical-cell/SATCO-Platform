"""Versioned, deterministic rules for Human-reviewed document assertions only."""

from dataclasses import dataclass
from decimal import Decimal
import re
from typing import Literal
from uuid import UUID


RULE_PACK_ID = "satco.document-correlation.v2"
RULE_PACK_VERSION = 2
CONSISTENCY_RULE_ID = "document.reviewed-assertion-consistency"
EXPLICIT_MISSING_RULE_ID = "document.explicit-missing-placeholder"
_MISSING_TOKENS = frozenset({
    "tbd", "tbc", "to be determined", "to be confirmed", "not specified",
    "missing", "unknown",
})
_REVIEWED_STATES = frozenset({"accepted", "corrected"})

_TAG = r"[A-Za-z0-9]+(?:[-_/][A-Za-z0-9]+)+"
_NUMBER = r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)"
_FAIL_POSITION = re.compile(
    rf"(?:the\s+)?(?:specified\s+)?fail(?:ure)?\s+position\s+"
    rf"(?:for|of)\s+(?P<subject>{_TAG})\s+(?:is|=|:)\s*"
    rf"(?P<value>fail\s+open|fail\s+closed|fo|fc)"
    rf"(?:\s*\((?:fo|fc)\))?[.]?",
    re.IGNORECASE,
)
_DESIGN_PRESSURE = re.compile(
    rf"(?:the\s+)?(?:stated\s+)?design\s+pressure\s+(?:for|of)\s+"
    rf"(?:(?:line|equipment|tag)\s+)?(?P<subject>{_TAG})\s+"
    rf"(?:is|=|:)\s*(?P<number>{_NUMBER})\s*(?P<unit>[A-Za-z]+)[.]?",
    re.IGNORECASE,
)
_SHUTDOWN_DELAY = re.compile(
    rf"(?:the\s+)?(?:(?P<scope>emergency|process|unit)\s+shutdown|esd)\s+delay"
    rf"(?:\s+(?:for|of)\s+(?P<subject>{_TAG}))?\s+(?:is|=|:)\s*"
    rf"(?P<number>{_NUMBER})\s*(?P<unit>[A-Za-z]+)[.]?",
    re.IGNORECASE,
)

_UNIT_ALIASES = {
    "pa": ("pressure", "Pa", Decimal("1")),
    "kpa": ("pressure", "Pa", Decimal("1000")),
    "mpa": ("pressure", "Pa", Decimal("1000000")),
    "bar": ("pressure", "Pa", Decimal("100000")),
    # Gauge pressure is deliberately a distinct dimension from generic pressure.
    "barg": ("gauge_pressure", "Pa(g)", Decimal("100000")),
    "ms": ("time", "s", Decimal("0.001")),
    "millisecond": ("time", "s", Decimal("0.001")),
    "milliseconds": ("time", "s", Decimal("0.001")),
    "s": ("time", "s", Decimal("1")),
    "sec": ("time", "s", Decimal("1")),
    "second": ("time", "s", Decimal("1")),
    "seconds": ("time", "s", Decimal("1")),
    "min": ("time", "s", Decimal("60")),
    "minute": ("time", "s", Decimal("60")),
    "minutes": ("time", "s", Decimal("60")),
    "h": ("time", "s", Decimal("3600")),
    "hour": ("time", "s", Decimal("3600")),
    "hours": ("time", "s", Decimal("3600")),
}
_FAIL_VALUES = {
    "fo": "fail_open",
    "fail open": "fail_open",
    "fc": "fail_closed",
    "fail closed": "fail_closed",
}


@dataclass(frozen=True, slots=True)
class ReviewedRuleCandidate:
    candidate_id: UUID
    analysis_run_id: UUID
    kind: str
    subject_key: str | None
    subject_label: str | None
    raw_value: str
    normalized_value: str | None
    numeric_value: Decimal | None
    unit: str | None
    quantity_type: str | None
    uncertainty: str | None
    condition: str | None = None
    review_state: str = "accepted"


@dataclass(frozen=True, slots=True)
class _ComparisonProjection:
    candidate: ReviewedRuleCandidate
    subject_key: str
    subject_label: str
    parameter_key: str
    condition_key: str
    value_kind: Literal["numeric", "categorical"]
    value: Decimal | str
    display_value: str
    unit: str | None
    reason_codes: tuple[str, ...]

    @property
    def key(self) -> tuple[str, str, str, str]:
        return (
            self.subject_key,
            self.parameter_key,
            self.condition_key,
            self.value_kind,
        )


@dataclass(frozen=True, slots=True)
class DocumentRuleOutcome:
    rule_id: str
    rule_version: int
    left_candidate_id: UUID
    right_candidate_id: UUID | None
    status: Literal["consistent", "discrepant", "missing_information"]
    applicability: str
    reason_codes: tuple[str, ...]
    summary: str
    finding_kind: Literal["discrepancy", "missing_information"] | None = None
    finding_title: str | None = None
    finding_explanation: str | None = None
    uncertainty: str | None = None


def _canonical_text(value: str | None, *, fallback: str) -> str:
    if not value or not value.strip():
        return fallback
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_") or fallback


def _numeric_projection(
    candidate: ReviewedRuleCandidate,
    *,
    subject_key: str,
    subject_label: str,
    parameter_key: str,
    condition_key: str,
    numeric_value: Decimal,
    unit: str,
    expected_dimension: str,
    projection_reason: str,
) -> _ComparisonProjection | None:
    normalized_unit = _UNIT_ALIASES.get(unit.strip().casefold())
    if normalized_unit is None:
        return None
    dimension, base_unit, factor = normalized_unit
    if dimension != expected_dimension:
        return None
    base_value = numeric_value * factor
    return _ComparisonProjection(
        candidate=candidate,
        subject_key=_canonical_text(subject_key, fallback="unspecified_subject"),
        subject_label=subject_label.strip(),
        parameter_key=parameter_key,
        condition_key=_canonical_text(condition_key, fallback="unspecified_condition"),
        value_kind="numeric",
        value=base_value,
        display_value=f"{numeric_value} {unit.strip()}",
        unit=base_unit,
        reason_codes=(projection_reason, "compatible_unit_normalized"),
    )


def _structured_projection(candidate: ReviewedRuleCandidate) -> _ComparisonProjection | None:
    if candidate.subject_key is None:
        return None
    quantity = _canonical_text(candidate.quantity_type, fallback="")
    if quantity == "fail_position" and candidate.numeric_value is None:
        token = re.sub(
            r"\s*\((?:fo|fc)\)\s*$", "",
            (candidate.normalized_value or candidate.raw_value).strip().casefold(),
        )
        value = _FAIL_VALUES.get(re.sub(r"\s+", " ", token))
        if value is None:
            return None
        return _ComparisonProjection(
            candidate=candidate,
            subject_key=_canonical_text(candidate.subject_key, fallback="unspecified_subject"),
            subject_label=candidate.subject_label or candidate.subject_key,
            parameter_key="fail_position",
            condition_key=_canonical_text(candidate.condition, fallback="failure"),
            value_kind="categorical",
            value=value,
            display_value=value.replace("_", " "),
            unit=None,
            reason_codes=("reviewed_structured_value", "canonical_category"),
        )
    if candidate.numeric_value is None:
        return None
    dimension_by_quantity = {
        "pressure": "pressure",
        "design_pressure": "pressure",
        "gauge_pressure": "gauge_pressure",
        "time": "time",
        "delay": "time",
    }
    dimension = dimension_by_quantity.get(quantity)
    if dimension is None or not candidate.unit:
        return None
    condition = candidate.condition
    parameter = quantity
    if quantity == "design_pressure":
        parameter, condition = "pressure", condition or "design"
    elif quantity == "delay":
        parameter = "delay"
    return _numeric_projection(
        candidate,
        subject_key=candidate.subject_key,
        subject_label=candidate.subject_label or candidate.subject_key,
        parameter_key=parameter,
        condition_key=condition or "unspecified_condition",
        numeric_value=candidate.numeric_value,
        unit=candidate.unit,
        expected_dimension=dimension,
        projection_reason="reviewed_structured_value",
    )


def _narrative_projection(candidate: ReviewedRuleCandidate) -> _ComparisonProjection | None:
    text = (candidate.normalized_value or candidate.raw_value).strip()

    match = _FAIL_POSITION.fullmatch(text)
    if match:
        value = _FAIL_VALUES[re.sub(r"\s+", " ", match.group("value").casefold())]
        subject = match.group("subject")
        return _ComparisonProjection(
            candidate=candidate,
            subject_key=_canonical_text(subject, fallback="unspecified_subject"),
            subject_label=subject,
            parameter_key="fail_position",
            condition_key=_canonical_text(candidate.condition, fallback="failure"),
            value_kind="categorical",
            value=value,
            display_value=value.replace("_", " "),
            unit=None,
            reason_codes=("strict_narrative_projection", "canonical_category"),
        )

    match = _DESIGN_PRESSURE.fullmatch(text)
    if match:
        # An explicit conflicting condition makes the assertion unsafe to project.
        if candidate.condition and _canonical_text(candidate.condition, fallback="") != "design":
            return None
        subject = match.group("subject")
        return _numeric_projection(
            candidate,
            subject_key=subject,
            subject_label=subject,
            parameter_key="pressure",
            condition_key="design",
            numeric_value=Decimal(match.group("number")),
            unit=match.group("unit"),
            expected_dimension="pressure",
            projection_reason="strict_narrative_projection",
        )

    match = _SHUTDOWN_DELAY.fullmatch(text)
    if match:
        scope = (match.group("scope") or "emergency").casefold()
        derived_condition = f"{scope}_shutdown"
        if candidate.condition and _canonical_text(candidate.condition, fallback="") != derived_condition:
            return None
        subject = match.group("subject") or f"{scope}_shutdown_system"
        return _numeric_projection(
            candidate,
            subject_key=subject,
            subject_label=subject.replace("_", " "),
            parameter_key="delay",
            condition_key=derived_condition,
            numeric_value=Decimal(match.group("number")),
            unit=match.group("unit"),
            expected_dimension="time",
            projection_reason="strict_narrative_projection",
        )
    return None


def _projection(candidate: ReviewedRuleCandidate) -> _ComparisonProjection | None:
    if candidate.review_state not in _REVIEWED_STATES:
        return None
    # Structured reviewed values take precedence. Narrative projection is a bounded
    # fallback and never mutates the stored candidate or its review history.
    return _structured_projection(candidate) or _narrative_projection(candidate)


class DocumentRulePackV2:
    """P0 correlation rules; advisory only and never a source of engineering truth."""

    rule_pack_id = RULE_PACK_ID
    version = RULE_PACK_VERSION

    def evaluate(self, candidates: tuple[ReviewedRuleCandidate, ...]):
        ordered = tuple(sorted(
            (item for item in candidates if item.review_state in _REVIEWED_STATES),
            key=lambda item: (str(item.analysis_run_id), str(item.candidate_id)),
        ))
        outcomes: list[DocumentRuleOutcome] = []

        for candidate in ordered:
            token = (candidate.normalized_value or candidate.raw_value).strip().casefold()
            if candidate.subject_key and token in _MISSING_TOKENS:
                outcomes.append(DocumentRuleOutcome(
                    rule_id=EXPLICIT_MISSING_RULE_ID,
                    rule_version=RULE_PACK_VERSION,
                    left_candidate_id=candidate.candidate_id,
                    right_candidate_id=None,
                    status="missing_information",
                    applicability=(
                        "Applies only because a Human-reviewed source value is an explicit "
                        "missing-information placeholder; blank cells are not evaluated."
                    ),
                    reason_codes=("human_reviewed", "explicit_placeholder"),
                    summary=f"{candidate.subject_label or candidate.subject_key} is explicitly recorded as {candidate.raw_value!r}.",
                    finding_kind="missing_information",
                    finding_title=f"Missing information: {candidate.subject_label or candidate.subject_key}",
                    finding_explanation=(
                        "The bound source explicitly uses a missing-information placeholder. "
                        "This is advisory and requires engineering disposition."
                    ),
                    uncertainty=candidate.uncertainty,
                ))

        projections = tuple(
            projection for projection in (_projection(item) for item in ordered)
            if projection is not None
        )
        groups: dict[tuple[str, str, str, str], list[_ComparisonProjection]] = {}
        for projection in projections:
            groups.setdefault(projection.key, []).append(projection)

        for key in sorted(groups):
            members = groups[key]
            for left_index, left in enumerate(members):
                for right in members[left_index + 1:]:
                    if left.candidate.analysis_run_id == right.candidate.analysis_run_id:
                        continue
                    same = left.value == right.value
                    subject = left.subject_label or right.subject_label or key[0]
                    parameter = key[1].replace("_", " ")
                    outcomes.append(DocumentRuleOutcome(
                        rule_id=CONSISTENCY_RULE_ID,
                        rule_version=RULE_PACK_VERSION,
                        left_candidate_id=left.candidate.candidate_id,
                        right_candidate_id=right.candidate.candidate_id,
                        status="consistent" if same else "discrepant",
                        applicability=(
                            "Applies only to Human-reviewed assertions from different document runs "
                            "that have one unambiguous deterministic projection with the same subject, "
                            "parameter, condition, value kind, and safely compatible unit dimension."
                        ),
                        reason_codes=(
                            "human_reviewed", "cross_document", "same_subject",
                            "same_parameter", "same_condition", *left.reason_codes,
                            *right.reason_codes,
                        ),
                        summary=(
                            f"{subject} — {parameter}: reviewed values agree at {left.display_value}."
                            if same else
                            f"{subject} — {parameter}: reviewed values differ "
                            f"({left.display_value} versus {right.display_value})."
                        ),
                        finding_kind=None if same else "discrepancy",
                        finding_title=None if same else f"Cross-document discrepancy: {subject} — {parameter}",
                        finding_explanation=None if same else (
                            "Two Human-reviewed source assertions with the same deterministic "
                            "comparison key have different values. SATCO has not determined which "
                            "value is correct."
                        ),
                        uncertainty=None if same else (
                            "The deterministic projection is advisory; a responsible engineer must "
                            "confirm source meaning, operating condition, and disposition."
                        ),
                    ))
        return tuple(outcomes)
