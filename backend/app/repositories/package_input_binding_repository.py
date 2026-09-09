"""Staging/query repository for immutable package input bindings."""

from sqlalchemy import select

from app.models.package_input_binding import (
    EngineeringContextPackageInputBinding,
    EvidencePackageInputBinding,
)


class PackageInputBindingRepository:
    def __init__(self, session): self.session = session
    def add_context(self, row): self.session.add(row); self.session.flush()
    def add_evidence(self, row): self.session.add(row); self.session.flush()
    def context_exact(self, identity): return self.session.get(EngineeringContextPackageInputBinding, identity)
    def evidence_exact(self, identity): return self.session.get(EvidencePackageInputBinding, identity)

    def context_for_inputs(self, *, project_id, revision, package_key, input_ids):
        return list(self.session.scalars(select(EngineeringContextPackageInputBinding).where(
            EngineeringContextPackageInputBinding.project_id == project_id,
            EngineeringContextPackageInputBinding.project_configuration_revision == revision,
            EngineeringContextPackageInputBinding.package_key == package_key,
            EngineeringContextPackageInputBinding.input_declaration_id.in_(input_ids),
        ).order_by(
            EngineeringContextPackageInputBinding.input_declaration_id,
            EngineeringContextPackageInputBinding.context_subject_reference_id,
            EngineeringContextPackageInputBinding.context_version,
        )))

    def evidence_for_inputs(self, *, project_id, revision, package_key, input_ids, evidence_ids):
        if not evidence_ids: return []
        return list(self.session.scalars(select(EvidencePackageInputBinding).where(
            EvidencePackageInputBinding.project_id == project_id,
            EvidencePackageInputBinding.project_configuration_revision == revision,
            EvidencePackageInputBinding.package_key == package_key,
            EvidencePackageInputBinding.input_declaration_id.in_(input_ids),
            EvidencePackageInputBinding.evidence_id.in_(evidence_ids),
        ).order_by(
            EvidencePackageInputBinding.input_declaration_id,
            EvidencePackageInputBinding.evidence_id,
            EvidencePackageInputBinding.evidence_version,
        )))
