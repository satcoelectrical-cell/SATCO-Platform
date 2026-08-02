"""Closed PATCH-026 EngineeringRelationship vocabulary."""

from enum import StrEnum


class RelationshipFamily(StrEnum):
    """Approved Version 1 relationship semantic namespaces."""

    STRUCTURAL = "structural"
    PHYSICAL = "physical"
    ELECTRICAL = "electrical"
    INSTRUMENTATION = "instrumentation"
    AUTOMATION = "automation"
    DEPENDENCY = "dependency"


class RelationshipType(StrEnum):
    """Approved Version 1 type tokens, interpreted only with a family."""

    PART_OF = "part_of"
    BELONGS_TO_SYSTEM = "belongs_to_system"
    BELONGS_TO_SUBSYSTEM = "belongs_to_subsystem"
    BELONGS_TO_PACKAGE = "belongs_to_package"
    GROUPED_WITH = "grouped_with"
    INSTALLED_IN = "installed_in"
    LOCATED_IN = "located_in"
    CONNECTED_TO = "connected_to"
    MOUNTED_ON = "mounted_on"
    CONNECTED_THROUGH = "connected_through"
    MECHANICALLY_COUPLED_TO = "mechanically_coupled_to"
    TERMINATED_AT = "terminated_at"
    ROUTED_THROUGH = "routed_through"
    SHARES_ENCLOSURE_WITH = "shares_enclosure_with"
    POWERED_BY = "powered_by"
    PROTECTED_BY = "protected_by"
    ISOLATED_BY = "isolated_by"
    EARTHED_THROUGH = "earthed_through"
    CONNECTED_TO_BUSBAR = "connected_to_busbar"
    CONTROLLED_BY_FEEDER = "controlled_by_feeder"
    BACKED_UP_BY_UPS = "backed_up_by_ups"
    MEASURES = "measures"
    TRANSMITS_TO = "transmits_to"
    RECEIVES_PROCESS_INPUT_FROM = "receives_process_input_from"
    CONNECTED_TO_LOOP = "connected_to_loop"
    CONNECTED_TO_IO_CHANNEL = "connected_to_io_channel"
    ACTUATES = "actuates"
    POSITIONED_BY = "positioned_by"
    MONITORED_BY = "monitored_by"
    PROVIDES_FEEDBACK_TO = "provides_feedback_to"
    COMPENSATED_BY = "compensated_by"
    CALIBRATED_AGAINST = "calibrated_against"
    CONTROLLED_BY = "controlled_by"
    COMMANDS = "commands"
    RECEIVES_SIGNAL_FROM = "receives_signal_from"
    SENDS_SIGNAL_TO = "sends_signal_to"
    IMPLEMENTED_IN = "implemented_in"
    INTERLOCKED_WITH = "interlocked_with"
    TRIPS = "trips"
    INITIATES = "initiates"
    INHIBITS = "inhibits"
    PARTICIPATES_IN_SEQUENCE = "participates_in_sequence"
    GENERATES_ALARM_FOR = "generates_alarm_for"
    EXECUTES_LOGIC_FOR = "executes_logic_for"
    DEPENDS_ON = "depends_on"
    AFFECTS = "affects"
    ENABLES = "enables"
    PREVENTS = "prevents"
    CONSTRAINS = "constrains"
    REPLACES = "replaces"
    SUPERSEDES = "supersedes"
    DERIVED_FROM = "derived_from"


class RelationshipLifecycle(StrEnum):
    """Approved complete lifecycle for governed relationships."""

    PROPOSED = "proposed"
    CURRENT = "current"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"
    REJECTED = "rejected"


RELATIONSHIP_TYPES_BY_FAMILY: dict[
    RelationshipFamily, frozenset[RelationshipType]
] = {
    RelationshipFamily.STRUCTURAL: frozenset(
        RelationshipType(value) for value in (
            "part_of", "belongs_to_system", "belongs_to_subsystem",
            "belongs_to_package", "grouped_with", "installed_in",
            "located_in",
        )
    ),
    RelationshipFamily.PHYSICAL: frozenset(
        RelationshipType(value) for value in (
            "connected_to", "mounted_on", "connected_through",
            "mechanically_coupled_to", "terminated_at", "routed_through",
            "shares_enclosure_with",
        )
    ),
    RelationshipFamily.ELECTRICAL: frozenset(
        RelationshipType(value) for value in (
            "powered_by", "protected_by", "isolated_by", "earthed_through",
            "connected_to_busbar", "controlled_by_feeder", "backed_up_by_ups",
        )
    ),
    RelationshipFamily.INSTRUMENTATION: frozenset(
        RelationshipType(value) for value in (
            "measures", "transmits_to", "receives_process_input_from",
            "connected_to_loop", "connected_to_io_channel", "actuates",
            "positioned_by", "monitored_by", "provides_feedback_to",
            "compensated_by", "calibrated_against",
        )
    ),
    RelationshipFamily.AUTOMATION: frozenset(
        RelationshipType(value) for value in (
            "controlled_by", "commands", "receives_signal_from",
            "sends_signal_to", "implemented_in", "interlocked_with", "trips",
            "initiates", "inhibits", "participates_in_sequence",
            "monitored_by", "generates_alarm_for", "executes_logic_for",
        )
    ),
    RelationshipFamily.DEPENDENCY: frozenset(
        RelationshipType(value) for value in (
            "depends_on", "affects", "enables", "prevents", "constrains",
            "replaces", "supersedes", "derived_from",
        )
    ),
}


ACYCLIC_RELATIONSHIP_PAIRS = frozenset(
    (family, RelationshipType(value))
    for family, values in {
        RelationshipFamily.STRUCTURAL: (
            "part_of", "belongs_to_system", "belongs_to_subsystem",
            "belongs_to_package", "installed_in", "located_in",
        ),
        RelationshipFamily.ELECTRICAL: (
            "powered_by", "protected_by", "isolated_by", "earthed_through",
            "controlled_by_feeder", "backed_up_by_ups",
        ),
        RelationshipFamily.AUTOMATION: ("implemented_in",),
        RelationshipFamily.DEPENDENCY: (
            "depends_on", "enables", "prevents", "constrains", "replaces",
            "supersedes", "derived_from",
        ),
    }.items()
    for value in values
)


CROSS_WORKSPACE_RELATIONSHIP_FAMILIES = frozenset(
    {
        RelationshipFamily.PHYSICAL,
        RelationshipFamily.ELECTRICAL,
        RelationshipFamily.INSTRUMENTATION,
        RelationshipFamily.AUTOMATION,
        RelationshipFamily.DEPENDENCY,
    }
)


def validate_relationship_pair(
    family: RelationshipFamily,
    relationship_type: RelationshipType,
) -> None:
    """Reject a type outside its explicitly supplied family namespace."""

    if relationship_type not in RELATIONSHIP_TYPES_BY_FAMILY[family]:
        raise ValueError(
            f"{relationship_type.value} is not valid for {family.value}"
        )
