from enum import StrEnum

from app.enums.engineering_knowledge import (
    EngineeringAuthorityStanding,
    EngineeringConfidentiality,
    EngineeringDiscipline,
    EngineeringIdentifierKind,
    EngineeringLifecycle,
    EngineeringObjectFamily,
    EngineeringObjectType,
    EngineeringRelationshipFamily,
    EngineeringResponsibilityRole,
)


ENUM_CONTRACTS = {
    EngineeringObjectFamily: {
        "instrumentation",
        "electrical",
        "automation",
        "shared",
    },
    EngineeringObjectType: {
        "instrument",
        "transmitter",
        "analyzer",
        "flowmeter",
        "control_valve",
        "instrument_loop",
        "junction_box",
        "instrument_panel",
        "motor",
        "transformer",
        "mcc",
        "switchgear",
        "electrical_panel",
        "electrical_cable",
        "plc",
        "dcs_controller",
        "esd_controller",
        "control_cabinet",
        "io_channel",
        "hmi",
        "control_logic",
        "project",
        "vendor",
        "requirement",
        "standard",
        "datasheet",
        "drawing",
        "technical_decision",
    },
    EngineeringDiscipline: {
        "instrumentation",
        "electrical",
        "industrial_automation",
        "shared_engineering",
    },
    EngineeringLifecycle: {
        "proposed",
        "active",
        "superseded",
        "withdrawn",
        "retired",
    },
    EngineeringAuthorityStanding: {
        "draft",
        "proposed",
        "reviewed",
        "approved",
        "disputed",
        "rejected",
    },
    EngineeringConfidentiality: {
        "organization",
        "customer",
        "project",
        "workspace",
        "restricted",
    },
    EngineeringRelationshipFamily: {
        "structural",
        "physical",
        "electrical",
        "instrumentation",
        "automation",
        "evidence",
        "dependency",
        "governance",
    },
    EngineeringIdentifierKind: {
        "tag_number",
        "equipment_number",
        "loop_number",
        "cable_number",
        "panel_number",
        "feeder_number",
        "system_identifier",
        "subsystem_identifier",
        "vendor_reference",
        "manufacturer_model_reference",
        "controlled_external_key",
    },
    EngineeringResponsibilityRole: {
        "creator",
        "owner",
        "steward",
        "discipline_owner",
        "reviewer",
        "approver",
        "assignee",
        "source_authority",
    },
}


def test_engineering_knowledge_enums_are_string_enums():
    for enum_type in ENUM_CONTRACTS:
        assert issubclass(enum_type, StrEnum)


def test_engineering_knowledge_enum_values_are_stable():
    for enum_type, expected_values in ENUM_CONTRACTS.items():
        actual_values = {member.value for member in enum_type}

        assert actual_values == expected_values
        assert len(actual_values) == len(enum_type)


def test_engineering_knowledge_enum_values_are_normalized():
    for enum_type in ENUM_CONTRACTS:
        for member in enum_type:
            assert member.value
            assert member.value == member.value.strip()
            assert member.value == member.value.lower()
            assert " " not in member.value
            assert "-" not in member.value


def test_approved_authority_standing_is_explicit():
    assert EngineeringAuthorityStanding.APPROVED.value == "approved"


def test_responsibility_roles_do_not_include_ai_or_anonymous():
    prohibited_values = {"ai", "anonymous", "service_account"}

    actual_values = {
        member.value
        for member in EngineeringResponsibilityRole
    }

    assert actual_values.isdisjoint(prohibited_values)
