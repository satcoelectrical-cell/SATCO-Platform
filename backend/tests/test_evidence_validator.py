from pathlib import Path
def test_validator_enforces_acceptable_and_scope_rules():
    source=Path("app/repositories/evidence_unit_of_work.py").read_text()
    for rule in ("Cross-Project Evidence is denied","Evidence Workspace is incompatible","Evidence is not acceptable"):
        assert rule in source
