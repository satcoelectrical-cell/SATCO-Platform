"""Literal PATCH-052 E/I/C descriptor source; no runtime discovery or I/O."""

from __future__ import annotations

from app.adapters.discipline_package_registry import StaticDisciplinePackageAdapter
from app.discipline_packages.canonical import descriptor_digest
from app.discipline_packages.conformance_manifest import (
    CONFORMANCE_VECTORS_V1, expected_result_digest,
)
from app.discipline_packages.contributions import (
    AuthorizationRequirementDeclarationV1, ConformanceEvidenceDeclarationV1,
    ContextContributionDeclarationV1, DeliverableDeclarationV1,
    DeterministicRuleHookDeclarationV1, EngineeringInputDeclarationV1,
    EvidenceRequirementDeclarationV1, FrontendMetadataV1, InterfaceDeclarationV1,
    ObjectTypeDeclarationV1, PackageContributionsV1, RelationshipTypeDeclarationV1,
    ResourceDeclarationV1, RoleRequirementDeclarationV1, StandardsApplicabilityHookV1,
    StandardsApplicabilityCandidateV1,
    TaxonomyFamilyDeclarationV1,
)
from app.discipline_packages.contracts import DisciplinePackageDescriptorV1
from app.discipline_packages.identity import PackageKey, PackageVersion
from app.discipline_packages.operational import (
    ObjectOperationDeclarationV1,
    OperationalPackageContractV1,
    RelationshipOperationDeclarationV1,
    RuleSpecV1,
)


_OBJECTS = {
    "electrical": ("motor", "transformer", "mcc", "switchgear", "electrical_panel", "electrical_cable", "electrical_feeder", "electrical_power_source"),
    "instrumentation": ("instrument", "transmitter", "analyzer", "flowmeter", "control_valve", "instrument_loop", "junction_box", "instrument_panel"),
    "control_automation": ("plc", "dcs_controller", "esd_controller", "control_cabinet", "io_channel", "hmi", "control_logic"),
}
_RELATIONSHIPS = {
    "electrical": ("powered_by", "protected_by", "isolated_by", "earthed_through", "connected_to_busbar", "controlled_by_feeder", "backed_up_by_ups"),
    "instrumentation": ("transmits_to", "connected_to_loop", "connected_to_io_channel", "provides_feedback_to", "calibrated_against"),
    "control_automation": ("controlled_by", "commands", "receives_signal_from", "sends_signal_to", "implemented_in", "interlocked_with", "trips", "initiates", "inhibits", "participates_in_sequence", "monitored_by", "generates_alarm_for", "executes_logic_for"),
}
_CONTEXTS = {
    "electrical": ("system_voltage_basis", "load_duty_basis", "source_feeder_basis", "protection_basis", "earthing_basis"),
    "instrumentation": ("measurement_service", "operating_range", "design_conditions", "signal_basis", "loop_basis"),
    "control_automation": ("control_philosophy_basis", "io_allocation_basis", "alarm_interlock_basis", "cause_effect_basis", "availability_redundancy_basis"),
}
_DELIVERABLES = {
    "electrical": ("electrical_load_list", "single_line_diagram", "electrical_cable_schedule", "electrical_equipment_datasheet"),
    "instrumentation": ("instrument_index", "instrument_datasheet", "instrument_loop_diagram", "instrument_io_list"),
    "control_automation": ("control_io_list", "control_narrative", "cause_effect_matrix", "alarm_interlock_schedule", "control_system_architecture_diagram"),
}
_EVIDENCE = {
    "electrical": ("voltage_source_basis_evidence", "load_basis_evidence", "protection_feeder_basis_evidence", "deliverable_review_evidence"),
    "instrumentation": ("measurement_process_basis_evidence", "range_condition_basis_evidence", "loop_calibration_basis_evidence", "deliverable_review_evidence"),
    "control_automation": ("control_philosophy_evidence", "io_allocation_evidence", "cause_effect_interlock_evidence", "deliverable_review_evidence"),
}
_RULES = {
    "electrical": ("object_relationship_integrity", "required_input_completeness", "source_feeder_connectivity", "evidence_sufficiency", "deliverable_readiness"),
    "instrumentation": ("object_relationship_integrity", "required_input_completeness", "loop_signal_connectivity", "evidence_sufficiency", "deliverable_readiness"),
    "control_automation": ("object_relationship_integrity", "required_input_completeness", "io_logic_connectivity", "evidence_sufficiency", "deliverable_readiness"),
}
_INTERFACE = {
    "electrical": ("electrical.power_supply_interface", "electrical", "instrumentation", "provides"),
    "instrumentation": ("instrumentation.signal_interface", "instrumentation", "control_automation", "provides"),
    "control_automation": ("control_automation.command_interface", "control_automation", "electrical", "constrains"),
}
_DISPLAY = {"electrical": "Electrical V1", "instrumentation": "Instrumentation V1", "control_automation": "Control & Automation V1"}

_ELECTRICAL_PRIMARY_KIND = {
    "motor": "equipment_number", "transformer": "equipment_number",
    "mcc": "panel_number", "switchgear": "panel_number",
    "electrical_panel": "panel_number", "electrical_cable": "cable_number",
    "electrical_feeder": "feeder_number", "electrical_power_source": "equipment_number",
}
_ELECTRICAL_CONTEXT_BY_OBJECT = {
    "motor": (0, 1, 2, 3, 4), "electrical_cable": (0, 1, 2, 3, 4),
    "transformer": (0, 1, 3, 4), "mcc": (0, 1, 3, 4),
    "switchgear": (0, 1, 3, 4), "electrical_panel": (0, 1, 3, 4),
    "electrical_feeder": (0, 2, 3), "electrical_power_source": (0, 2),
}
_ELECTRICAL_RELATIONSHIP_ENDPOINTS = {
    "powered_by": (
        {"motor", "mcc", "switchgear", "electrical_panel", "electrical_cable", "electrical_feeder"},
        {"electrical_power_source", "transformer", "switchgear", "mcc", "electrical_panel"},
    ),
    "protected_by": (
        {"motor", "transformer", "mcc", "electrical_panel", "electrical_cable", "electrical_feeder"},
        {"switchgear", "mcc", "electrical_panel"},
    ),
    "isolated_by": (
        {"motor", "transformer", "mcc", "electrical_panel", "electrical_cable", "electrical_feeder"},
        {"switchgear", "mcc", "electrical_panel", "electrical_feeder"},
    ),
    "earthed_through": (set(_OBJECTS["electrical"]), {"electrical_cable"}),
    "connected_to_busbar": ({"transformer", "electrical_cable", "electrical_feeder"}, {"switchgear", "mcc", "electrical_panel"}),
    "controlled_by_feeder": ({"motor", "electrical_panel", "electrical_cable"}, {"electrical_feeder"}),
    "backed_up_by_ups": ({"motor", "mcc", "switchgear", "electrical_panel"}, {"electrical_power_source"}),
}
_ELECTRICAL_DELIVERABLE_INPUTS = {
    "electrical_load_list": (0, 1, 5, 6),
    "single_line_diagram": (0, 2, 3, 4, 5, 7),
    "electrical_cable_schedule": (0, 1, 2, 3, 4, 6, 7),
    "electrical_equipment_datasheet": (0, 1, 3, 4, 5, 6, 7),
}
_ELECTRICAL_REPRESENTATIONS = {
    "electrical_load_list": ("spreadsheet",),
    "single_line_diagram": ("cad", "document", "eplan"),
    "electrical_cable_schedule": ("eplan", "spreadsheet"),
    "electrical_equipment_datasheet": ("document",),
}

_INSTRUMENTATION_PRIMARY_KIND = {
    "instrument": "tag_number", "transmitter": "tag_number",
    "analyzer": "tag_number", "flowmeter": "tag_number",
    "control_valve": "tag_number", "instrument_loop": "loop_number",
    "junction_box": "panel_number", "instrument_panel": "panel_number",
}
_INSTRUMENTATION_CONTEXT_BY_OBJECT = {
    "instrument": (0, 1, 2, 3, 4), "transmitter": (0, 1, 2, 3, 4),
    "analyzer": (0, 1, 2, 3, 4), "flowmeter": (0, 1, 2, 3, 4),
    "control_valve": (0, 1, 2, 3, 4),
    "instrument_loop": (0, 3, 4),
    "junction_box": (3, 4), "instrument_panel": (3, 4),
}
_INSTRUMENTATION_RELATIONSHIP_ENDPOINTS = {
    "transmits_to": (
        {"transmitter", "analyzer", "flowmeter"},
        {"junction_box", "instrument_panel"}, False,
    ),
    "connected_to_loop": (
        {"instrument", "transmitter", "analyzer", "flowmeter", "control_valve"},
        {"instrument_loop"}, False,
    ),
    "connected_to_io_channel": (
        {"instrument", "transmitter", "analyzer", "flowmeter", "control_valve"},
        {"io_channel"}, True,
    ),
    "provides_feedback_to": (
        {"instrument", "transmitter", "analyzer", "flowmeter"},
        {"instrument_loop", "instrument_panel", "io_channel"}, True,
    ),
    "calibrated_against": (
        {"instrument", "transmitter", "analyzer", "flowmeter", "control_valve"},
        {"instrument", "analyzer"}, False,
    ),
}
_INSTRUMENTATION_DELIVERABLE_INPUTS = {
    "instrument_index": (0, 3, 4, 5),
    "instrument_datasheet": (0, 1, 2, 3, 5, 6),
    "instrument_loop_diagram": (0, 3, 4, 5, 7),
    "instrument_io_list": (0, 3, 4, 5),
}
_INSTRUMENTATION_REPRESENTATIONS = {
    "instrument_index": ("spreadsheet",),
    "instrument_datasheet": ("document",),
    "instrument_loop_diagram": ("cad", "document"),
    "instrument_io_list": ("spreadsheet",),
}

_CONTROL_AUTOMATION_PRIMARY_KIND = {
    "plc": "equipment_number", "dcs_controller": "equipment_number",
    "esd_controller": "equipment_number", "control_cabinet": "panel_number",
    "io_channel": "controlled_external_key", "hmi": "panel_number",
    "control_logic": "system_identifier",
}
_CONTROL_AUTOMATION_CONTEXT_BY_OBJECT = {
    "plc": (0, 1, 2, 4), "dcs_controller": (0, 1, 2, 4),
    "esd_controller": (0, 1, 2, 4), "control_cabinet": (0, 1, 2, 4),
    "io_channel": (0, 1, 2, 4), "hmi": (0, 2, 4),
    "control_logic": (0, 2, 3),
}
_CONTROL_AUTOMATION_RELATIONSHIP_ENDPOINTS = {
    "controlled_by": (
        {"hmi", "io_channel", "control_logic"},
        {"plc", "dcs_controller", "esd_controller"}, set(),
    ),
    "commands": (
        {"plc", "dcs_controller", "esd_controller", "control_logic"},
        {"io_channel", "control_valve", "motor"}, {"control_valve", "motor"},
    ),
    "receives_signal_from": (
        {"plc", "dcs_controller", "esd_controller", "io_channel"},
        {"instrument", "transmitter", "analyzer", "flowmeter", "io_channel"},
        {"instrument", "transmitter", "analyzer", "flowmeter"},
    ),
    "sends_signal_to": (
        {"plc", "dcs_controller", "esd_controller", "io_channel"},
        {"hmi", "io_channel", "control_valve"}, {"control_valve"},
    ),
    "implemented_in": (
        {"control_logic"}, {"plc", "dcs_controller", "esd_controller"}, set(),
    ),
    "interlocked_with": (
        {"control_logic", "plc", "dcs_controller", "esd_controller"},
        {"control_logic", "plc", "dcs_controller", "esd_controller"}, set(),
    ),
    "trips": (
        {"esd_controller", "control_logic"},
        {"motor", "control_valve", "plc", "dcs_controller"},
        {"motor", "control_valve"},
    ),
    "initiates": (
        {"plc", "dcs_controller", "esd_controller", "control_logic"},
        {"control_logic"}, set(),
    ),
    "inhibits": (
        {"control_logic", "plc", "dcs_controller", "esd_controller"},
        {"control_logic"}, set(),
    ),
    "participates_in_sequence": (
        set(_OBJECTS["control_automation"]), {"control_logic"}, set(),
    ),
    "monitored_by": (
        {"plc", "dcs_controller", "esd_controller", "io_channel", "control_logic"},
        {"hmi"}, set(),
    ),
    "generates_alarm_for": (
        {"plc", "dcs_controller", "esd_controller", "control_logic"},
        {"hmi", "motor", "control_valve", "instrument", "transmitter"},
        {"motor", "control_valve", "instrument", "transmitter"},
    ),
    "executes_logic_for": (
        {"plc", "dcs_controller", "esd_controller"},
        {"control_logic", "motor", "control_valve"}, {"motor", "control_valve"},
    ),
}
_CONTROL_AUTOMATION_TARGET_FAMILIES = {
    "controlled_by": ("automation",),
    "commands": ("automation", "electrical", "instrumentation"),
    "receives_signal_from": ("automation", "instrumentation"),
    "sends_signal_to": ("automation", "instrumentation"),
    "implemented_in": ("automation",), "interlocked_with": ("automation",),
    "trips": ("automation", "electrical", "instrumentation"),
    "initiates": ("automation",), "inhibits": ("automation",),
    "participates_in_sequence": ("automation",), "monitored_by": ("automation",),
    "generates_alarm_for": ("automation", "electrical", "instrumentation"),
    "executes_logic_for": ("automation", "electrical", "instrumentation"),
}
_CONTROL_AUTOMATION_DELIVERABLE_INPUTS = {
    "control_io_list": (0, 1, 4, 5, 6),
    "control_narrative": (0, 2, 3, 4, 5, 7),
    "cause_effect_matrix": (0, 2, 3, 5, 7),
    "alarm_interlock_schedule": (0, 1, 2, 3, 5, 6, 7),
    "control_system_architecture_diagram": (0, 1, 4, 5, 6),
}
_CONTROL_AUTOMATION_REPRESENTATIONS = {
    "control_io_list": ("spreadsheet",),
    "control_narrative": ("document",),
    "cause_effect_matrix": ("document", "spreadsheet"),
    "alarm_interlock_schedule": ("spreadsheet",),
    "control_system_architecture_diagram": ("cad", "document"),
}

ELECTRICAL_OBJECT_DECLARATIONS = tuple(
    ObjectOperationDeclarationV1(
        f"electrical.object.{object_type}", object_type,
        _ELECTRICAL_PRIMARY_KIND[object_type],
        tuple(f"electrical.{_CONTEXTS['electrical'][index]}.input" for index in _ELECTRICAL_CONTEXT_BY_OBJECT[object_type]),
    )
    for object_type in _OBJECTS["electrical"]
)
ELECTRICAL_RELATIONSHIP_DECLARATIONS = tuple(
    RelationshipOperationDeclarationV1(
        f"electrical.relationship.{relationship_type}", relationship_type,
        frozenset(_ELECTRICAL_RELATIONSHIP_ENDPOINTS[relationship_type][0]),
        frozenset(_ELECTRICAL_RELATIONSHIP_ENDPOINTS[relationship_type][1]),
    )
    for relationship_type in _RELATIONSHIPS["electrical"]
)
INSTRUMENTATION_OBJECT_DECLARATIONS = tuple(
    ObjectOperationDeclarationV1(
        f"instrumentation.object.{object_type}", object_type,
        _INSTRUMENTATION_PRIMARY_KIND[object_type],
        tuple(
            f"instrumentation.{_CONTEXTS['instrumentation'][index]}.input"
            for index in _INSTRUMENTATION_CONTEXT_BY_OBJECT[object_type]
        ),
    )
    for object_type in _OBJECTS["instrumentation"]
)
INSTRUMENTATION_RELATIONSHIP_DECLARATIONS = tuple(
    RelationshipOperationDeclarationV1(
        f"instrumentation.relationship.{relationship_type}", relationship_type,
        frozenset(_INSTRUMENTATION_RELATIONSHIP_ENDPOINTS[relationship_type][0]),
        frozenset(_INSTRUMENTATION_RELATIONSHIP_ENDPOINTS[relationship_type][1]),
        cross_workspace=_INSTRUMENTATION_RELATIONSHIP_ENDPOINTS[relationship_type][2],
        cross_workspace_target_types=(
            frozenset({"io_channel"})
            if _INSTRUMENTATION_RELATIONSHIP_ENDPOINTS[relationship_type][2]
            else frozenset()
        ),
    )
    for relationship_type in _RELATIONSHIPS["instrumentation"]
)
CONTROL_AUTOMATION_OBJECT_DECLARATIONS = tuple(
    ObjectOperationDeclarationV1(
        f"control_automation.object.{object_type}", object_type,
        _CONTROL_AUTOMATION_PRIMARY_KIND[object_type],
        tuple(
            f"control_automation.{_CONTEXTS['control_automation'][index]}.input"
            for index in _CONTROL_AUTOMATION_CONTEXT_BY_OBJECT[object_type]
        ),
    )
    for object_type in _OBJECTS["control_automation"]
)
CONTROL_AUTOMATION_RELATIONSHIP_DECLARATIONS = tuple(
    RelationshipOperationDeclarationV1(
        f"control_automation.relationship.{relationship_type}", relationship_type,
        frozenset(_CONTROL_AUTOMATION_RELATIONSHIP_ENDPOINTS[relationship_type][0]),
        frozenset(_CONTROL_AUTOMATION_RELATIONSHIP_ENDPOINTS[relationship_type][1]),
        direction="bidirectional" if relationship_type == "interlocked_with" else "directed",
        cardinality="many_to_many" if relationship_type in {"interlocked_with", "participates_in_sequence"} else "many_to_one",
        cross_workspace=bool(_CONTROL_AUTOMATION_RELATIONSHIP_ENDPOINTS[relationship_type][2]),
        cross_workspace_target_types=frozenset(_CONTROL_AUTOMATION_RELATIONSHIP_ENDPOINTS[relationship_type][2]),
    )
    for relationship_type in _RELATIONSHIPS["control_automation"]
)


def _context_subject(package_key: str, index: int) -> str:
    if package_key == "electrical" and index in {0, 2}:
        return "workspace"
    if package_key == "control_automation" and index in {0, 4}:
        return "workspace"
    return "engineering_object"


def _rule_specs(package_key: str) -> tuple[RuleSpecV1, ...]:
    schemas = {
        "object_relationship_integrity": ("package.object_relationship_validation.v1", "package.validation_result.v1"),
        "required_input_completeness": ("package.input_completeness.v1", "package.assessment_result.v1"),
        "source_feeder_connectivity": ("package.relationship_completeness.v1", "package.assessment_result.v1"),
        "loop_signal_connectivity": ("package.relationship_completeness.v1", "package.assessment_result.v1"),
        "io_logic_connectivity": ("package.relationship_completeness.v1", "package.assessment_result.v1"),
        "evidence_sufficiency": ("package.evidence_sufficiency.v1", "package.assessment_result.v1"),
        "deliverable_readiness": ("package.deliverable_readiness.v1", "package.validation_result.v1"),
    }
    return tuple(RuleSpecV1(
        f"{package_key}.{name}", f"{package_key}.{name}",
        schemas[name][0], schemas[name][1],
        50 if name == "object_relationship_integrity" else 100,
        16 if name == "object_relationship_integrity" else 32,
    ) for name in _RULES[package_key])


def _vectors(package_key: str) -> tuple[ConformanceEvidenceDeclarationV1, ...]:
    vectors = [item for item in CONFORMANCE_VECTORS_V1 if item.subject_kind == "package_declaration" and item.vector_id.startswith(f"patch_052.{package_key}.")]
    return tuple(ConformanceEvidenceDeclarationV1(
        id=f"{package_key}.conformance.{item.scenario_purpose}", version="1.0.0", owner="PACKAGE", ordinal=index,
        display_name=f"{package_key} {item.scenario_purpose}", vector_id=item.vector_id,
        contract_version="1.0.0", suite_version="1.0.0",
        expected_result_digest=expected_result_digest(item),
        reviewed_source_reference=f"patch_052.{package_key}.{item.scenario_purpose}",
    ) for index, item in enumerate(vectors, 1))


def _contributions(package_key: str) -> PackageContributionsV1:
    rules = _rule_specs(package_key)
    standard_id = f"{package_key}.standards_applicability"
    interface_id, source, target, kind = _INTERFACE[package_key]
    contexts = _CONTEXTS[package_key]
    inputs = tuple(
        EngineeringInputDeclarationV1(
            id=f"{package_key}.{name}.input", version="1.0.0", owner="PACKAGE", ordinal=index,
            display_name=f"{name} input", input_type_id=f"{package_key}.{name}", source_kind="context",
            required=True, max_occurrences=1 if _context_subject(package_key, index - 1) == "workspace" else 64,
        ) for index, name in enumerate(contexts, 1)
    ) + tuple(
        EngineeringInputDeclarationV1(
            id=f"{package_key}.{name}.input", version="1.0.0", owner="PACKAGE", ordinal=index + 5,
            display_name=f"{name} input", input_type_id=f"{package_key}.{name}", source_kind="evidence",
            required=False, max_occurrences=8,
        ) for index, name in enumerate(_EVIDENCE[package_key], 1)
    )
    deliverables = tuple(DeliverableDeclarationV1(
        id=f"{package_key}.deliverable.{name}", version="1.0.0", owner="PACKAGE", ordinal=index,
        display_name=name.replace("_", " ").title(), deliverable_type_id=name,
        required_input_ids=tuple(inputs[position].id for position in (
            _ELECTRICAL_DELIVERABLE_INPUTS[name] if package_key == "electrical"
            else _INSTRUMENTATION_DELIVERABLE_INPUTS[name] if package_key == "instrumentation"
            else _CONTROL_AUTOMATION_DELIVERABLE_INPUTS[name]
        )), output_representation_ids=(
            _ELECTRICAL_REPRESENTATIONS[name] if package_key == "electrical"
            else _INSTRUMENTATION_REPRESENTATIONS[name] if package_key == "instrumentation"
            else _CONTROL_AUTOMATION_REPRESENTATIONS[name]
        ),
        human_acceptance_required=True,
    ) for index, name in enumerate(_DELIVERABLES[package_key], 1))
    vector_rows = _vectors(package_key)
    resource = ResourceDeclarationV1(
        taxonomy_families=1, object_types=len(_OBJECTS[package_key]), relationship_types=len(_RELATIONSHIPS[package_key]),
        context_kinds=5, engineering_inputs=9, deliverables=len(deliverables), evidence_requirements=4,
        deterministic_rule_hooks=5, standards_hooks=1, cross_discipline_interfaces=1, role_requirements=2,
        authorization_requirements=2, migration_compatibility_entries=0, conformance_vectors=len(vector_rows),
        adapter_timeout_class_id="bounded_100ms", adapter_memory_class_id="bounded_4mib",
    )
    return PackageContributionsV1(
        taxonomy_families=(TaxonomyFamilyDeclarationV1(
            id=(f"{package_key}.family.automation" if package_key == "control_automation" else f"{package_key}.family.{package_key}"),
            version="1.0.0", owner="CORE", ordinal=1,
            display_name=f"{package_key} taxonomy", parent_family_id=None,
        ),),
        object_types=tuple(ObjectTypeDeclarationV1(
            id=f"{package_key}.object.{name}", version="1.0.0", owner="PACKAGE",
            ordinal=index, display_name=name.replace("_", " ").title(),
            family_id="automation" if package_key == "control_automation" else package_key,
            lifecycle_id="engineering_object.lifecycle.v1",
            required_context_kind_ids=tuple(
                f"{package_key}.{_CONTEXTS[package_key][position]}"
                for position in (
                    _ELECTRICAL_CONTEXT_BY_OBJECT[name] if package_key == "electrical"
                    else _INSTRUMENTATION_CONTEXT_BY_OBJECT[name] if package_key == "instrumentation"
                    else _CONTROL_AUTOMATION_CONTEXT_BY_OBJECT[name]
                )
            ),
            authority_requirement_ids=("owner.engineering_object.mutate",),
        ) for index, name in enumerate(_OBJECTS[package_key], 1)),
        relationship_types=tuple(RelationshipTypeDeclarationV1(id=f"{package_key}.relationship.{name}", version="1.0.0", owner="PACKAGE", ordinal=index, display_name=name.replace("_", " ").title(), source_object_family_ids=(("automation",) if package_key == "control_automation" else (package_key,)), target_object_family_ids=(
            ("control_automation",) if package_key == "instrumentation" and name == "connected_to_io_channel"
            else ("instrumentation", "control_automation") if package_key == "instrumentation" and name == "provides_feedback_to"
            else _CONTROL_AUTOMATION_TARGET_FAMILIES[name] if package_key == "control_automation"
            else (package_key,)
        ), direction="bidirectional" if name == "interlocked_with" else "directed", cardinality="many_to_many" if name in {"interlocked_with", "participates_in_sequence"} else "many_to_one", lifecycle_id="engineering_relationship.lifecycle.v1") for index, name in enumerate(_RELATIONSHIPS[package_key], 1)),
        context_contributions=tuple(ContextContributionDeclarationV1(id=f"{package_key}.{name}.context", version="1.0.0", owner="PACKAGE", ordinal=index, display_name=f"{name} context", context_kind_id=f"{package_key}.{name}", allowed_subject_kind_ids=(_context_subject(package_key, index - 1),), value_schema_id=f"{package_key}.{name}.v1", required=True) for index, name in enumerate(contexts, 1)),
        engineering_inputs=inputs,
        deliverables=deliverables,
        evidence_requirements=tuple(EvidenceRequirementDeclarationV1(id=f"{package_key}.{name}", version="1.0.0", owner="PACKAGE", ordinal=index, display_name=name.replace("_", " ").title(), evidence_kind_id="human_review" if index == 4 else "engineering_record", minimum_count=1, applicable_operation_id=f"{package_key}.deliverable_issue" if index == 4 else f"{package_key}.evaluate_readiness", human_verification_required=True) for index, name in enumerate(_EVIDENCE[package_key], 1)),
        deterministic_rule_hooks=tuple(DeterministicRuleHookDeclarationV1(id=spec.rule_id, version="1.0.0", owner="PACKAGE", ordinal=index, display_name=spec.rule_id, hook_id=spec.hook_id, hook_version="1.0.0", input_schema_id=spec.input_schema_id, output_schema_id=spec.output_schema_id, max_findings=spec.max_findings, timeout_ms=spec.timeout_ms) for index, spec in enumerate(rules, 1)),
        standards_hooks=(StandardsApplicabilityHookV1(
            hook_id=standard_id, version="1.0.0",
            input_schema_id="package.standards_applicability_input.v1",
            output_schema_id="package.standards_applicability_output.v1",
            max_results=4, timeout_ms=100,
            candidates=(
                StandardsApplicabilityCandidateV1(
                    designation_key=f"{package_key}.design_basis.standard",
                    family_key=package_key, suggested_role="design_basis",
                    rationale_code="package_design_basis_advisory",
                ),
            ),
        ),),
        cross_discipline_interfaces=(InterfaceDeclarationV1(interface_type_id=interface_id, source_discipline_id=source, target_discipline_id=target, dependency_kind=kind, version="1.0.0"),),
        role_requirements=tuple(RoleRequirementDeclarationV1(id=f"{package_key}.role.{operation}", version="1.0.0", owner="PACKAGE", ordinal=index, display_name=f"{operation} role", operation_id=f"{package_key}.{operation}", accepted_human_role_ids=("admin", "engineer"), minimum_authority_predicate_id=f"owner.workspace_{'mutation' if operation == 'mutate' else 'read'}_authorized") for index, operation in enumerate(("mutate", "evaluate"), 1)),
        authorization_requirements=tuple(AuthorizationRequirementDeclarationV1(id=f"{package_key}.authorization.{operation}", version="1.0.0", owner="PACKAGE", ordinal=index, display_name=f"{operation} authorization", operation_id=f"{package_key}.{operation}", source_owner_policy_id=f"owner.workspace_and_{'aggregate_mutation' if operation == 'mutate' else 'sources_read'}", package_policy_id=f"package.executable_bound_{'mutation' if operation == 'mutate' else 'evaluation'}") for index, operation in enumerate(("mutate", "evaluate"), 1)),
        frontend_metadata=FrontendMetadataV1(route_keys=(f"workspace.{package_key}.v1",), navigation_keys=(f"workspace.{package_key}.v1",), component_keys=(f"workspace.{package_key}.v1",), visibility_predicate_id="effective_package_authorized"),
        resource_declaration=resource,
        conformance_evidence=vector_rows,
    )


PACKAGE_CONTRACTS_V1 = tuple(OperationalPackageContractV1(
    package_key, "1.0.0", f"discipline.{package_key}.v1", f"workspace.{package_key}.v1", _rule_specs(package_key)
) for package_key in ("electrical", "instrumentation", "control_automation"))

DESCRIPTORS_V1 = tuple(DisciplinePackageDescriptorV1(
    package_key=contract.package_key, package_version=contract.package_version,
    primary_discipline_id=contract.package_key, core_contract_versions=(1,),
    display_name=_DISPLAY[contract.package_key], entitlement_key=f"discipline.{contract.package_key}",
    adapter_id=contract.adapter_id, contributions=_contributions(contract.package_key),
) for contract in PACKAGE_CONTRACTS_V1)


def package_adapters() -> tuple[StaticDisciplinePackageAdapter, ...]:
    """Return only the reviewed adapters that exactly match source capability IDs."""

    adapters = []
    for descriptor in DESCRIPTORS_V1:
        contributions = descriptor.contributions
        capabilities = frozenset(item.id for item in contributions.deterministic_rule_hooks) | frozenset(item.hook_id for item in contributions.standards_hooks) | frozenset(item.interface_type_id for item in contributions.cross_discipline_interfaces)
        adapters.append(StaticDisciplinePackageAdapter(descriptor.adapter_id, PackageKey(descriptor.package_key), PackageVersion(descriptor.package_version), capabilities))
    return tuple(adapters)


DESCRIPTOR_DIGESTS_V1 = {item.package_key: descriptor_digest(item) for item in DESCRIPTORS_V1}
