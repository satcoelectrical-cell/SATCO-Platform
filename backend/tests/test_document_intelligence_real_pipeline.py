"""Opt-in real Document Intelligence worker qualification.

This test deliberately uses a real PDF parser, local Ollama, and the guarded
disposable PostgreSQL database.  Only the exact-key object store is a test
double.  The synthetic records are retained in the disposable database so a
subsequent Human Review qualification can exercise the same persisted run.
"""

from datetime import datetime, timezone
from io import BytesIO
import json
import os
from types import SimpleNamespace
from urllib.parse import urlparse
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from app.adapters.document_semantic_provider import OllamaDocumentSemanticProvider
from app.adapters.pdf_document_content_extractor import PdfPlumberDocumentContentExtractor
from app.adapters.supporting_file_object_store import (
    InMemoryPrivateSupportingFileObjectStore,
)
from app.core.database import engine
from app.models.customer import Customer
from app.models.document_intelligence import (
    CandidateSourceLocatorLink,
    DocumentCandidateReview,
    DocumentAnalysisPageRecord,
    DocumentAnalysisRun,
    DocumentEngineeringCandidate,
    DocumentFindingRecord,
    DocumentIntelligenceIdempotency,
    DocumentIntelligenceOutbox,
    DocumentPromotionReceipt,
    EvidenceSourceLocatorLink,
    SourceLocatorRecord,
)
from app.models.organization import Organization
from app.models.evidence import Evidence
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.project import Project
from app.models.supporting_file import EvidenceSupportingFileLink, SupportingFileAsset
from app.models.user import User
from app.models.technical_report import (
    TechnicalReportProvenanceRecord,
    TechnicalReportRecord,
)
from app.models.technical_report_command import TechnicalReportActor
from app.services.deterministic_document_interpreter import (
    DeterministicDocumentInterpreter,
)
from app.services.document_analysis_worker import DocumentAnalysisWorker
from app.schemas.document_intelligence import (
    CandidateCorrection,
    CandidateReviewRequest,
    DocumentCorrelationRequest,
    DocumentPromotionRequest,
    DocumentReportDraftRequest,
    EngineeringCandidateValue,
)
from app.repositories.technical_report_unit_of_work import (
    SqlAlchemyTechnicalReportUnitOfWork,
)
from app.services.document_intelligence_service import (
    DocumentIntelligenceConflict,
    DocumentIntelligenceProtectedNotFound,
    DocumentIntelligenceService,
)
from app.services.technical_report_service import TechnicalReportService


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_REAL_DOCUMENT_INTELLIGENCE_PIPELINE") != "1",
    reason="real local Ollama/PostgreSQL qualification is opt-in",
)


def _synthetic_pdf(text: str) -> bytes:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = f"BT /F1 10 Tf 54 720 Td ({escaped}) Tj ET".encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content),
    ]
    payload = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, value in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{number} 0 obj\n".encode())
        payload.extend(value)
        payload.extend(b"\nendobj\n")
    xref = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode())
    payload.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref}\n%%EOF\n"
        ).encode()
    )
    return bytes(payload)


def _assert_isolated_database() -> None:
    parsed = urlparse(os.environ["TEST_DATABASE_URL"])
    assert parsed.hostname in {"127.0.0.1", "localhost"}
    assert parsed.port == 55433
    assert parsed.path == "/satco_platform_patch02022_test"


class _UtcClock:
    @staticmethod
    def now():
        return datetime.now(timezone.utc)


def _process_synthetic_run(
    *, session, objects, organization_id, project_id, workspace_id,
    user_id, filename, text,
):
    payload = _synthetic_pdf(text)
    receipt = objects.put_private(
        key=f"objects/{uuid4().hex}{uuid4().hex}",
        content=BytesIO(payload),
        media_type="application/pdf",
    )
    now = datetime.now(timezone.utc)
    asset = SupportingFileAsset(
        id=uuid4(),
        organization_id=organization_id,
        project_id=project_id,
        workspace_id=workspace_id,
        safe_filename=filename,
        safe_ascii_filename=filename,
        media_type="application/pdf",
        byte_size=receipt.byte_size,
        digest_algorithm="sha256",
        content_digest=receipt.sha256,
        storage_key=receipt.key,
        object_version=receipt.version,
        uploader_id=user_id,
        lifecycle="available",
        version=2,
        uploaded_at=now,
        scan_requested_at=now,
        scanned_at=now,
    )
    session.add(asset)
    session.flush()
    run = DocumentAnalysisRun(
        id=uuid4(),
        organization_id=organization_id,
        project_id=project_id,
        workspace_id=workspace_id,
        supporting_file_asset_id=asset.id,
        source_asset_version=asset.version,
        source_storage_object_version=asset.object_version,
        source_content_digest=asset.content_digest,
        safe_filename=asset.safe_filename,
        media_type=asset.media_type,
        state="queued",
        progress_completed=0,
        customer_message="Analysis queued",
        candidate_count=0,
        unreviewed_count=0,
        limitations=[],
        created_by_id=user_id,
        version=1,
        created_at=now,
        updated_at=now,
    )
    session.add(run)
    session.commit()
    DocumentAnalysisWorker(
        session=session,
        objects=objects,
        extractor=PdfPlumberDocumentContentExtractor(),
        interpreter=DeterministicDocumentInterpreter(),
        semantic_provider=OllamaDocumentSemanticProvider(
            endpoint=os.getenv(
                "DOCUMENT_SEMANTIC_PROVIDER_ENDPOINT",
                "http://127.0.0.1:11434/api/chat",
            ),
            model_id=os.getenv(
                "DOCUMENT_SEMANTIC_PROVIDER_MODEL",
                "satco-qwen3-4b:latest",
            ),
            timeout_seconds=180,
        ),
    ).process(run.id)
    session.expire_all()
    persisted = session.get(DocumentAnalysisRun, run.id)
    assert persisted.state == "requires_review"
    assert persisted.provider_status in {"success", "partial"}
    return persisted.id


def test_real_worker_postgresql_ollama_persists_and_retrieves():
    _assert_isolated_database()
    now = datetime.now(timezone.utc)
    unique = uuid4().hex
    # The shared test harness assigns newly inserted users to this fixed,
    # test-only organization in an ``after_insert`` listener.
    organization_id = UUID("02810000-0000-4000-8000-000000000001")
    payload = _synthetic_pdf(
        "SATCO SYNTHETIC ENGINEERING TEST. P&ID states the fail position of "
        "XV-101 is Fail Closed (FC). Control Narrative states the fail position "
        "of XV-101 is Fail Open (FO). This intentional discrepancy requires "
        "Human engineering review; AI output is advisory and must not approve "
        "or promote any engineering decision."
    )
    objects = InMemoryPrivateSupportingFileObjectStore()
    receipt = objects.put_private(
        key=f"objects/{unique}{uuid4().hex}",
        content=BytesIO(payload),
        media_type="application/pdf",
    )

    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as session:
        organization = session.get(Organization, organization_id)
        if organization is None:
            organization = Organization(
                id=organization_id,
                name="SATCO synthetic P0 qualification",
                slug="satco-p0-qualification",
                is_active=True,
            )
            session.add(organization)
            session.flush()
        user = User(
            email=f"p0-{unique}@example.invalid",
            username=f"p0_{unique}",
            hashed_password="not-a-login-account",
            full_name="Synthetic P0 Engineer",
            role="engineer",
            is_active=True,
        )
        customer = Customer(
            organization_id=organization_id,
            name="Synthetic Petrochemical Customer",
            company="Synthetic Test Data Only",
        )
        session.add_all((user, customer))
        session.flush()
        project = Project(
            organization_id=organization_id,
            project_code=f"SAT-PRJ-2026-{int(unique[:8], 16):010d}",
            name="Synthetic XV-101 Golden Workflow",
            description="Disposable qualification data; not a real project.",
            customer_id=customer.id,
            status="in_progress",
            priority="medium",
            owner_id=user.id,
            primary_assignee_id=user.id,
            progress=0,
            created_at=now,
        )
        session.add(project)
        session.flush()
        asset = SupportingFileAsset(
            id=uuid4(),
            organization_id=organization_id,
            project_id=project.id,
            workspace_id=None,
            safe_filename="synthetic-xv-101-discrepancy.pdf",
            safe_ascii_filename="synthetic-xv-101-discrepancy.pdf",
            media_type="application/pdf",
            byte_size=receipt.byte_size,
            digest_algorithm="sha256",
            content_digest=receipt.sha256,
            storage_key=receipt.key,
            object_version=receipt.version,
            uploader_id=user.id,
            lifecycle="available",
            version=2,
            uploaded_at=now,
            scan_requested_at=now,
            scanned_at=now,
        )
        # These persistence models intentionally expose identifier-only links,
        # so make the source parent durable before inserting the analysis FK.
        session.add(asset)
        session.flush()
        run = DocumentAnalysisRun(
            id=uuid4(),
            organization_id=organization_id,
            project_id=project.id,
            workspace_id=None,
            supporting_file_asset_id=asset.id,
            source_asset_version=asset.version,
            source_storage_object_version=asset.object_version,
            source_content_digest=asset.content_digest,
            safe_filename=asset.safe_filename,
            media_type=asset.media_type,
            state="queued",
            progress_completed=0,
            customer_message="Analysis queued",
            candidate_count=0,
            unreviewed_count=0,
            limitations=[],
            created_by_id=user.id,
            version=1,
            created_at=now,
            updated_at=now,
        )
        session.add(run)
        session.commit()
        run_id = run.id

        DocumentAnalysisWorker(
            session=session,
            objects=objects,
            extractor=PdfPlumberDocumentContentExtractor(),
            interpreter=DeterministicDocumentInterpreter(),
            semantic_provider=OllamaDocumentSemanticProvider(
                endpoint=os.getenv(
                    "DOCUMENT_SEMANTIC_PROVIDER_ENDPOINT",
                    "http://127.0.0.1:11434/api/chat",
                ),
                model_id=os.getenv(
                    "DOCUMENT_SEMANTIC_PROVIDER_MODEL",
                    "satco-qwen3-4b:latest",
                ),
                timeout_seconds=180,
            ),
        ).process(run_id)

    # A fresh SQLAlchemy session proves that the worker committed durable rows
    # to the isolated PostgreSQL database rather than leaving ORM-only state.
    with Session() as verification:
        persisted_run = verification.get(DocumentAnalysisRun, run_id)
        pages = verification.query(DocumentAnalysisPageRecord).filter_by(
            analysis_run_id=run_id
        ).all()
        candidates = verification.query(DocumentEngineeringCandidate).filter_by(
            analysis_run_id=run_id
        ).order_by(DocumentEngineeringCandidate.ordinal).all()
        candidate_ids = tuple(candidate.id for candidate in candidates)
        links = verification.query(CandidateSourceLocatorLink).filter(
            CandidateSourceLocatorLink.candidate_id.in_(candidate_ids)
        ).all()
        locator_ids = tuple(link.source_locator_id for link in links)
        locators = verification.query(SourceLocatorRecord).filter(
            SourceLocatorRecord.id.in_(locator_ids)
        ).all()

        assert persisted_run is not None
        assert persisted_run.state == "requires_review"
        assert persisted_run.provider_status in {"success", "partial"}
        assert persisted_run.page_count == len(pages) == 1
        assert persisted_run.candidate_count == len(candidates) >= 2
        assert persisted_run.unreviewed_count == len(candidates)
        assert len(links) >= len(candidates)
        assert {locator.id for locator in locators} == set(locator_ids)
        assert all(locator.content_digest == receipt.sha256 for locator in locators)
        assert all(locator.page_index == 0 for locator in locators)

        provider_candidate_ids = {
            link.candidate_id
            for link in links
            if any(
                locator.id == link.source_locator_id
                and locator.extraction_method == "provider"
                for locator in locators
            )
        }
        provider_candidates = [
            candidate
            for candidate in candidates
            if candidate.id in provider_candidate_ids
        ]
        assert provider_candidates
        assert any(
            candidate.kind == "discrepancy"
            and "xv-101" in " ".join(
                filter(
                    None,
                    (
                        candidate.subject_key,
                        candidate.subject_label,
                        candidate.raw_value,
                        candidate.normalized_value,
                    ),
                )
            ).lower()
            for candidate in provider_candidates
        )

        print(
            json.dumps(
                {
                    "analysis_run_id": str(run_id),
                    "state": persisted_run.state,
                    "provider_status": persisted_run.provider_status,
                    "page_count": len(pages),
                    "candidate_count": len(candidates),
                    "provider_candidate_count": len(provider_candidates),
                    "source_locator_count": len(locators),
                    "candidate_locator_link_count": len(links),
                    "object_store": "in-memory test double",
                },
                sort_keys=True,
            )
        )


def test_real_persisted_candidates_require_authorized_human_review():
    _assert_isolated_database()
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as session:
        run = session.query(DocumentAnalysisRun).filter_by(
            safe_filename="synthetic-xv-101-discrepancy.pdf",
            provider_status="success",
            state="requires_review",
        ).order_by(DocumentAnalysisRun.created_at.desc()).first()
        assert run is not None, "Stage A must persist a reviewable successful run"
        project = session.get(Project, run.project_id)
        engineer = session.get(User, project.owner_id)
        assert engineer is not None and engineer.role == "engineer"

        service = DocumentIntelligenceService(session)
        with pytest.raises(DocumentIntelligenceProtectedNotFound):
            service.list_candidates(
                project_id=run.project_id,
                run_id=run.id,
                user=SimpleNamespace(id=-1, is_active=True, role="engineer"),
                organization_id=run.organization_id,
            )

        visible = service.list_candidates(
            project_id=run.project_id,
            run_id=run.id,
            user=engineer,
            organization_id=run.organization_id,
        )
        assert visible.total == run.candidate_count == 2
        assert visible.unreviewed_count == 2
        assert all(item.locators for item in visible.items)
        assert all(
            locator.page_index == 0
            and locator.content_digest == run.source_content_digest
            for item in visible.items
            for locator in item.locators
        )
        discrepancy = next(
            item for item in visible.items if item.kind.value == "discrepancy"
        )
        accepted_target = next(
            item for item in visible.items if item.candidate_id != discrepancy.candidate_id
        )
        assert discrepancy.proposed_canonical_target == "none"

        accept_key = uuid4()
        accept_request = CandidateReviewRequest(
            expected_version=accepted_target.version,
            action="accept",
            rationale="Authorized synthetic qualification acceptance.",
        )
        accepted = service.review_candidate(
            project_id=run.project_id,
            run_id=run.id,
            candidate_id=accepted_target.candidate_id,
            data=accept_request,
            user=engineer,
            organization_id=run.organization_id,
            idempotency_id=accept_key,
            correlation_id=uuid4(),
        )
        assert accepted.review_state.value == "accepted"

        review_count = session.query(DocumentCandidateReview).filter_by(
            candidate_id=accepted_target.candidate_id
        ).count()
        outbox_count = session.query(DocumentIntelligenceOutbox).filter_by(
            aggregate_id=run.id,
            event_type="DocumentCandidateReviewed",
        ).count()
        replayed = service.review_candidate(
            project_id=run.project_id,
            run_id=run.id,
            candidate_id=accepted_target.candidate_id,
            data=accept_request,
            user=engineer,
            organization_id=run.organization_id,
            idempotency_id=accept_key,
            correlation_id=uuid4(),
        )
        assert replayed.candidate_id == accepted.candidate_id
        assert replayed.version == accepted.version
        assert session.query(DocumentCandidateReview).filter_by(
            candidate_id=accepted_target.candidate_id
        ).count() == review_count
        assert session.query(DocumentIntelligenceOutbox).filter_by(
            aggregate_id=run.id,
            event_type="DocumentCandidateReviewed",
        ).count() == outbox_count

        with pytest.raises(DocumentIntelligenceConflict):
            service.review_candidate(
                project_id=run.project_id,
                run_id=run.id,
                candidate_id=accepted_target.candidate_id,
                data=CandidateReviewRequest(
                    expected_version=accepted_target.version,
                    action="reject",
                    rationale="Conflicting reuse must fail.",
                ),
                user=engineer,
                organization_id=run.organization_id,
                idempotency_id=accept_key,
                correlation_id=uuid4(),
            )

        with pytest.raises(DocumentIntelligenceConflict):
            service.review_candidate(
                project_id=run.project_id,
                run_id=run.id,
                candidate_id=discrepancy.candidate_id,
                data=CandidateReviewRequest(
                    expected_version=discrepancy.version + 99,
                    action="reject",
                    rationale="Stale version must fail.",
                ),
                user=engineer,
                organization_id=run.organization_id,
                idempotency_id=uuid4(),
                correlation_id=uuid4(),
            )

        rejected = service.review_candidate(
            project_id=run.project_id,
            run_id=run.id,
            candidate_id=discrepancy.candidate_id,
            data=CandidateReviewRequest(
                expected_version=discrepancy.version,
                action="reject",
                rationale="Synthetic discrepancy rejected by authorized engineer.",
            ),
            user=engineer,
            organization_id=run.organization_id,
            idempotency_id=uuid4(),
            correlation_id=uuid4(),
        )
        assert rejected.review_state.value == "rejected"
        candidate_ids = tuple(item.candidate_id for item in visible.items)
        run_id = run.id

    with Session() as verification:
        persisted_run = verification.get(DocumentAnalysisRun, run_id)
        reviews = verification.query(DocumentCandidateReview).filter(
            DocumentCandidateReview.candidate_id.in_(candidate_ids)
        ).order_by(DocumentCandidateReview.occurred_at).all()
        idempotency = verification.query(DocumentIntelligenceIdempotency).filter_by(
            aggregate_id=run_id,
            operation="review_candidate",
        ).all()
        review_events = verification.query(DocumentIntelligenceOutbox).filter_by(
            aggregate_id=run_id,
            event_type="DocumentCandidateReviewed",
        ).all()
        promotions = verification.query(DocumentPromotionReceipt).filter(
            DocumentPromotionReceipt.candidate_id.in_(candidate_ids)
        ).all()

        assert persisted_run.state == "completed"
        assert persisted_run.unreviewed_count == 0
        assert {review.action for review in reviews} == {"accept", "reject"}
        assert all(review.rationale for review in reviews)
        assert len(idempotency) == 2
        assert len(review_events) == 2
        assert promotions == []
        print(
            json.dumps(
                {
                    "analysis_run_id": str(run_id),
                    "authorized_candidate_count": len(candidate_ids),
                    "human_review_actions": sorted(
                        review.action for review in reviews
                    ),
                    "review_audit_count": len(reviews),
                    "review_outbox_count": len(review_events),
                    "idempotency_record_count": len(idempotency),
                    "automatic_promotion_count": len(promotions),
                    "final_state": persisted_run.state,
                },
                sort_keys=True,
            )
        )


def test_real_human_controlled_promotion_persists_proposed_evidence():
    _assert_isolated_database()
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as session:
        run = session.query(DocumentAnalysisRun).filter_by(
            safe_filename="synthetic-xv-101-discrepancy.pdf",
            provider_status="success",
            state="completed",
        ).order_by(DocumentAnalysisRun.created_at.desc()).first()
        assert run is not None, "Stage B must complete the persisted Stage A run"
        project = session.get(Project, run.project_id)
        engineer = session.get(User, project.owner_id)
        candidate = session.query(DocumentEngineeringCandidate).filter_by(
            analysis_run_id=run.id,
            review_state="accepted",
        ).first()
        assert candidate is not None
        assert session.query(DocumentPromotionReceipt).filter_by(
            candidate_id=candidate.id,
            candidate_version=candidate.version,
        ).first() is None

        service = DocumentIntelligenceService(session)
        promotion_key = uuid4()
        request = DocumentPromotionRequest(
            expected_candidate_version=candidate.version,
            include_engineering_context=False,
            rationale="Authorized evidence-only synthetic qualification promotion.",
        )
        promoted = service.promote_candidate(
            project_id=run.project_id,
            run_id=run.id,
            candidate_id=candidate.id,
            data=request,
            user=engineer,
            organization_id=run.organization_id,
            idempotency_id=promotion_key,
            correlation_id=uuid4(),
        )
        replayed = service.promote_candidate(
            project_id=run.project_id,
            run_id=run.id,
            candidate_id=candidate.id,
            data=request,
            user=engineer,
            organization_id=run.organization_id,
            idempotency_id=promotion_key,
            correlation_id=uuid4(),
        )
        assert replayed.promotion_receipt_id == promoted.promotion_receipt_id
        assert replayed.evidence_id == promoted.evidence_id
        assert promoted.engineering_context_id is None
        evidence_id = promoted.evidence_id
        receipt_id = promoted.promotion_receipt_id
        candidate_id = candidate.id
        run_id = run.id

    with Session() as verification:
        evidence = verification.get(Evidence, evidence_id)
        receipt = verification.get(DocumentPromotionReceipt, receipt_id)
        file_links = verification.query(EvidenceSupportingFileLink).filter_by(
            evidence_id=evidence_id
        ).all()
        locator_links = verification.query(EvidenceSourceLocatorLink).filter_by(
            evidence_id=evidence_id
        ).all()
        promotion_events = verification.query(DocumentIntelligenceOutbox).filter_by(
            aggregate_id=run_id,
            event_type="DocumentCandidatePromoted",
        ).all()
        promotion_keys = verification.query(DocumentIntelligenceIdempotency).filter_by(
            aggregate_id=run_id,
            operation="promote_candidate",
        ).all()

        assert evidence is not None and evidence.lifecycle == "proposed"
        assert receipt.candidate_id == candidate_id
        assert receipt.evidence_id == evidence_id
        assert len(file_links) == 1
        assert len(locator_links) >= 1
        assert len(promotion_events) == 1
        assert len(promotion_keys) == 1
        print(
            json.dumps(
                {
                    "analysis_run_id": str(run_id),
                    "candidate_id": str(candidate_id),
                    "promotion_receipt_id": str(receipt_id),
                    "evidence_id": str(evidence_id),
                    "evidence_lifecycle": evidence.lifecycle,
                    "supporting_file_link_count": len(file_links),
                    "source_locator_link_count": len(locator_links),
                    "engineering_context_id": None,
                },
                sort_keys=True,
            )
        )


def test_real_full_golden_workflow_creates_preliminary_report_draft():
    _assert_isolated_database()
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    organization_id = UUID("02810000-0000-4000-8000-000000000001")
    unique = uuid4().hex
    objects = InMemoryPrivateSupportingFileObjectStore()

    with Session() as session:
        organization = session.get(Organization, organization_id)
        assert organization is not None and organization.is_active
        engineer = User(
            email=f"golden-{unique}@example.invalid",
            username=f"golden_{unique}",
            hashed_password="not-a-login-account",
            full_name="Synthetic Bidboland RO Engineer",
            role="engineer",
            is_active=True,
        )
        customer = Customer(
            organization_id=organization_id,
            name="Synthetic Bidboland RO Customer",
            company="Synthetic Test Data Only",
        )
        session.add_all((engineer, customer))
        session.flush()
        project = Project(
            organization_id=organization_id,
            project_code=f"SAT-PRJ-2026-{int(unique[:8], 16):010d}",
            name="Synthetic Bidboland RO Golden Workflow",
            description=(
                "Disposable benchmark only; original Bidboland RO documents "
                "are not read or modified."
            ),
            customer_id=customer.id,
            status="in_progress",
            priority="high",
            owner_id=engineer.id,
            primary_assignee_id=engineer.id,
            progress=0,
            created_at=datetime.now(timezone.utc),
        )
        session.add(project)
        session.flush()
        workspace = EngineeringWorkspace(
            project_id=project.id,
            discipline="instrumentation",
            description="Synthetic RO instrumentation benchmark workspace",
            status="active",
            owner_id=engineer.id,
            primary_assignee_id=engineer.id,
            created_by_id=engineer.id,
            version=1,
        )
        session.add(workspace)
        session.flush()

        primary_run_id = _process_synthetic_run(
            session=session,
            objects=objects,
            organization_id=organization_id,
            project_id=project.id,
            workspace_id=workspace.id,
            user_id=engineer.id,
            filename="synthetic-bidboland-ro-design-basis.pdf",
            text=(
                "SATCO SYNTHETIC BIDBOLAND RO BENCHMARK. Design pressure for "
                "RO feed vessel V-101 is explicitly TBD (to be determined). "
                "P&ID states XV-101 fail position is Fail Closed, while the "
                "Control Narrative states XV-101 fail position is Fail Open. "
                "All output requires Human engineering review."
            ),
        )
        secondary_run_id = _process_synthetic_run(
            session=session,
            objects=objects,
            organization_id=organization_id,
            project_id=project.id,
            workspace_id=workspace.id,
            user_id=engineer.id,
            filename="synthetic-bidboland-ro-control-note.pdf",
            text=(
                "SATCO SYNTHETIC BIDBOLAND RO CONTROL NOTE. Pump P-101 stops "
                "on confirmed low suction pressure. This advisory source is "
                "synthetic and requires Human engineering review."
            ),
        )

        service = DocumentIntelligenceService(session)
        primary = service.list_candidates(
            project_id=project.id,
            run_id=primary_run_id,
            user=engineer,
            organization_id=organization_id,
        )
        secondary = service.list_candidates(
            project_id=project.id,
            run_id=secondary_run_id,
            user=engineer,
            organization_id=organization_id,
        )
        missing = next(
            (
                item for item in primary.items
                if "pressure" in " ".join(
                    filter(None, (item.subject_key, item.subject_label, item.value.raw_value))
                ).lower()
                and "tbd" in item.value.raw_value.lower()
            ),
            None,
        )
        assert missing is not None, "Ollama must extract the explicit TBD pressure"
        assert all(
            any(
                locator.extraction_method == "provider"
                for item in candidate_page.items
                for locator in item.locators
            )
            for candidate_page in (primary, secondary)
        )

        corrected = service.review_candidate(
            project_id=project.id,
            run_id=primary_run_id,
            candidate_id=missing.candidate_id,
            data=CandidateReviewRequest(
                expected_version=missing.version,
                action="correct",
                rationale=(
                    "Authorized engineer normalizes the explicit source placeholder "
                    "without supplying a design value."
                ),
                correction=CandidateCorrection(
                    subject_key="v_101_design_pressure",
                    subject_label="V-101 design pressure",
                    value=EngineeringCandidateValue(
                        raw_value="TBD",
                        normalized_value="TBD",
                        numeric_value=None,
                        unit=None,
                        quantity_type="pressure",
                        condition="Design basis",
                    ),
                    uncertainty="Responsible engineer must determine the design pressure.",
                ),
            ),
            user=engineer,
            organization_id=organization_id,
            idempotency_id=uuid4(),
            correlation_id=uuid4(),
        )
        assert corrected.review_state.value == "corrected"

        for run_id, candidate_page in (
            (primary_run_id, primary),
            (secondary_run_id, secondary),
        ):
            for candidate in candidate_page.items:
                if candidate.candidate_id == missing.candidate_id:
                    continue
                service.review_candidate(
                    project_id=project.id,
                    run_id=run_id,
                    candidate_id=candidate.candidate_id,
                    data=CandidateReviewRequest(
                        expected_version=candidate.version,
                        action="reject",
                        rationale="Out of scope for this bounded synthetic qualification.",
                    ),
                    user=engineer,
                    organization_id=organization_id,
                    idempotency_id=uuid4(),
                    correlation_id=uuid4(),
                )

        promoted = service.promote_candidate(
            project_id=project.id,
            run_id=primary_run_id,
            candidate_id=missing.candidate_id,
            data=DocumentPromotionRequest(
                expected_candidate_version=corrected.version,
                include_engineering_context=False,
                rationale=(
                    "Record the Human-reviewed missing-information assertion as "
                    "proposed Evidence; do not create an engineering value."
                ),
            ),
            user=engineer,
            organization_id=organization_id,
            idempotency_id=uuid4(),
            correlation_id=uuid4(),
        )
        correlation = service.correlate_documents(
            project_id=project.id,
            data=DocumentCorrelationRequest(
                analysis_run_ids=(primary_run_id, secondary_run_id),
                rationale="Evaluate only Human-reviewed candidates with P0 rules.",
            ),
            user=engineer,
            organization_id=organization_id,
            idempotency_id=uuid4(),
            correlation_id=uuid4(),
        )
        assert len(correlation.findings) == 1
        finding = correlation.findings[0]
        correlation_summary = correlation.correlations[0].summary
        assert finding.kind.value == "missing_information"
        assert finding.evidence

        report_factory = sessionmaker(bind=engine, expire_on_commit=False)
        report_service = TechnicalReportService(
            lambda: SqlAlchemyTechnicalReportUnitOfWork(report_factory),
            _UtcClock(),
        )
        report = service.create_document_report_draft(
            project_id=project.id,
            data=DocumentReportDraftRequest(
                workspace_id=workspace.id,
                finding_ids=(finding.finding_id,),
                purpose="engineering_analysis",
                rationale=(
                    "Create a preliminary, traceable draft for responsible "
                    "engineering disposition."
                ),
            ),
            user=engineer,
            organization_id=organization_id,
            idempotency_id=uuid4(),
            correlation_id=uuid4(),
            report_service=report_service,
            report_actor=TechnicalReportActor(engineer.id, organization_id),
        )
        assert report.lifecycle == "draft"
        assert report.preliminary is True
        project_id = project.id
        workspace_id = workspace.id
        engineer_id = engineer.id

    with Session() as verification:
        primary_run = verification.get(DocumentAnalysisRun, primary_run_id)
        secondary_run = verification.get(DocumentAnalysisRun, secondary_run_id)
        evidence = verification.get(Evidence, promoted.evidence_id)
        finding_row = verification.get(DocumentFindingRecord, finding.finding_id)
        report_row = verification.get(TechnicalReportRecord, report.report_id)
        provenance = verification.query(TechnicalReportProvenanceRecord).filter_by(
            technical_report_id=report.report_id
        ).all()

        assert primary_run.state == secondary_run.state == "completed"
        assert evidence.lifecycle == "proposed"
        assert finding_row.state == "open"
        assert report_row.lifecycle == "draft"
        assert report_row.is_preliminary is True
        assert report_row.accepted_snapshot is None
        assert report_row.accepted_snapshot_digest is None
        assert report_row.accepted_by_id is None
        assert report_row.accepted_at is None
        assert report_row.workspace_id == workspace_id
        assert report_row.project_id == project_id
        assert report_row.owner_id == engineer_id
        assert correlation_summary in report_row.draft_content
        assert len(provenance) == 1
        assert provenance[0].report_local_source_id == finding.finding_id
        assert correlation_summary in (
            provenance[0].minimal_historical_representation[
                "minimal_representation"
            ]
        )
        assert provenance[0].integrity_digest
        print(
            json.dumps(
                {
                    "project_id": project_id,
                    "workspace_id": workspace_id,
                    "analysis_run_count": 2,
                    "provider_statuses": sorted((
                        primary_run.provider_status,
                        secondary_run.provider_status,
                    )),
                    "human_reviewed_missing_candidate_id": str(missing.candidate_id),
                    "promoted_evidence_id": str(promoted.evidence_id),
                    "finding_id": str(finding.finding_id),
                    "finding_state": finding_row.state,
                    "technical_report_id": str(report.report_id),
                    "report_lifecycle": report_row.lifecycle,
                    "report_preliminary": report_row.is_preliminary,
                    "report_provenance_count": len(provenance),
                    "object_store": "in-memory test double",
                },
                sort_keys=True,
            )
        )
