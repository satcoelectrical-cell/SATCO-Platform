from dataclasses import replace
from decimal import Decimal
from uuid import uuid4

from app.services.document_rule_pack import (
    CONSISTENCY_RULE_ID,
    EXPLICIT_MISSING_RULE_ID,
    RULE_PACK_VERSION,
    DocumentRulePackV2,
    ReviewedRuleCandidate,
)


def _candidate(
    *, run_id=None, subject="line_101", value="12",
    numeric=Decimal("12"), unit="bar", quantity="pressure",
    condition=None, review_state="accepted",
):
    return ReviewedRuleCandidate(
        candidate_id=uuid4(), analysis_run_id=run_id or uuid4(),
        kind="engineering_value", subject_key=subject,
        subject_label=subject, raw_value=value,
        normalized_value=value, numeric_value=numeric,
        unit=unit, quantity_type=quantity, uncertainty=None,
        condition=condition, review_state=review_state,
    )


def _narrative(value, *, run_id=None, condition=None, review_state="accepted"):
    return _candidate(
        run_id=run_id, subject="document_section", value=value,
        numeric=None, unit=None, quantity=None, condition=condition,
        review_state=review_state,
    )


def test_same_equipment_parameter_and_compatible_units_match():
    left = _candidate(value="1 bar", numeric=Decimal("1"), unit="bar")
    right = _candidate(value="100 kPa", numeric=Decimal("100"), unit="kPa")

    outcomes = DocumentRulePackV2().evaluate((right, left))

    assert len(outcomes) == 1
    assert outcomes[0].rule_id == CONSISTENCY_RULE_ID
    assert outcomes[0].rule_version == RULE_PACK_VERSION == 2
    assert outcomes[0].status == "consistent"
    assert outcomes[0].finding_kind is None


def test_numeric_narrative_conflict_is_advisory_discrepancy():
    left = _narrative("The stated design pressure for line 10-P-101 is 12 bar.")
    right = _narrative("The stated design pressure for line 10-P-101 is 15 bar.")

    outcome = DocumentRulePackV2().evaluate((left, right))[0]

    assert outcome.status == "discrepant"
    assert outcome.finding_kind == "discrepancy"
    assert "not determined which value is correct" in outcome.finding_explanation
    assert "responsible engineer" in outcome.uncertainty


def test_categorical_narrative_conflict_is_detected_without_truth_selection():
    left = _narrative("The specified fail position for XV-101 is Fail Closed (FC).")
    right = _narrative("The specified fail position for XV-101 is Fail Open (FO).")

    outcome = DocumentRulePackV2().evaluate((left, right))[0]

    assert outcome.status == "discrepant"
    assert "XV-101" in outcome.finding_title
    assert "canonical_category" in outcome.reason_codes


def test_human_correction_can_supply_structured_categorical_comparison():
    left = _candidate(
        subject="XV-101", value="Fail Closed (FC)", numeric=None, unit=None,
        quantity="fail_position", condition="failure", review_state="corrected",
    )
    right = _candidate(
        subject="XV-101", value="Fail Open", numeric=None, unit=None,
        quantity="fail_position", condition="failure", review_state="corrected",
    )

    outcome = DocumentRulePackV2().evaluate((left, right))[0]

    assert outcome.status == "discrepant"
    assert "reviewed_structured_value" in outcome.reason_codes


def test_different_equipment_or_conditions_are_excluded():
    assert DocumentRulePackV2().evaluate((
        _narrative("The specified fail position for XV-101 is Fail Closed (FC)."),
        _narrative("The specified fail position for XV-102 is Fail Open (FO)."),
    )) == ()
    assert DocumentRulePackV2().evaluate((
        _candidate(condition="normal"),
        _candidate(condition="startup"),
    )) == ()


def test_same_run_missing_or_ambiguous_units_are_excluded():
    run_id = uuid4()
    assert DocumentRulePackV2().evaluate((
        _candidate(run_id=run_id), _candidate(run_id=run_id),
    )) == ()
    assert DocumentRulePackV2().evaluate((
        _narrative("The stated design pressure for line 10-P-101 is 12."),
        _narrative("The stated design pressure for line 10-P-101 is 15."),
    )) == ()
    assert DocumentRulePackV2().evaluate((
        _narrative("The stated design pressure for line 10-P-101 is 12 bar or 174 psi."),
        _narrative("The stated design pressure for line 10-P-101 is 15 bar."),
    )) == ()


def test_unreviewed_candidates_are_excluded_by_rule_pack_defense_in_depth():
    accepted = _candidate()
    unreviewed = _candidate(numeric=Decimal("15"), review_state="unreviewed")

    assert DocumentRulePackV2().evaluate((accepted, unreviewed)) == ()


def test_only_explicit_reviewed_placeholders_create_missing_information():
    blank = _candidate(value="", numeric=None, unit=None)
    missing = _candidate(value="To be determined", numeric=None, unit=None)
    rejected_missing = replace(missing, candidate_id=uuid4(), review_state="rejected")

    outcomes = DocumentRulePackV2().evaluate((blank, missing, rejected_missing))

    assert len(outcomes) == 1
    assert outcomes[0].rule_id == EXPLICIT_MISSING_RULE_ID
    assert outcomes[0].status == "missing_information"
    assert "blank cells are not evaluated" in outcomes[0].applicability


def test_demo_narratives_produce_three_traceable_discrepancies_deterministically():
    pid_run, control_run = uuid4(), uuid4()
    candidates = (
        _narrative("The specified fail position for XV-101 is Fail Closed (FC).", run_id=pid_run),
        _narrative("The stated design pressure for line 10-P-101 is 12 bar.", run_id=pid_run),
        _narrative("The emergency shutdown delay is 3 seconds.", run_id=pid_run),
        _narrative("The specified fail position for XV-101 is Fail Open (FO).", run_id=control_run),
        _narrative("The stated design pressure for line 10-P-101 is 15 bar.", run_id=control_run),
        _narrative("The emergency shutdown delay is 5 seconds.", run_id=control_run),
    )
    before = candidates

    first = DocumentRulePackV2().evaluate(candidates)
    second = DocumentRulePackV2().evaluate(candidates)

    assert first == second
    assert candidates == before
    assert len(first) == 3
    assert {item.status for item in first} == {"discrepant"}
    assert all("strict_narrative_projection" in item.reason_codes for item in first)


def test_empty_candidate_set_has_no_invented_findings():
    assert DocumentRulePackV2().evaluate(()) == ()
