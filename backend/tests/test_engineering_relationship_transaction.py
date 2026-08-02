from unittest.mock import MagicMock
from datetime import datetime, timezone
from uuid import uuid4
import pytest
from sqlalchemy.orm import sessionmaker

from app.enums import RelationshipFamily, RelationshipType
from app.exceptions.engineering_relationship import (
    EngineeringRelationshipProtectedNotFound,
    EngineeringRelationshipVersionConflict,
)
from app.models.audit_log import AuditLog
from app.models.engineering_object import EngineeringObject
from app.models.engineering_relationship_command import (
    AuthenticatedRelationshipActor, EngineeringRelationshipIdempotency,
    EngineeringRelationshipOutbox, RelationshipAuthorizationContext,
)
from app.models.evidence import Evidence
from app.models.organization import Organization
from app.repositories.engineering_relationship_unit_of_work import (
    SqlAlchemyRelationshipAuthorizationPolicy,
    SqlAlchemyRelationshipValidator,
    SqlAlchemyEngineeringRelationshipUnitOfWork,
    UtcRelationshipClock,
)
from app.repositories.engineering_relationship_repository import (
    SqlAlchemyEngineeringRelationshipRepository,
)
from app.schemas.engineering_relationship import (
    EngineeringRelationshipCreate,
    SubmitEngineeringRelationshipForReviewRequest,
)
from app.services.engineering_relationship_service import EngineeringRelationshipService


def test_unit_of_work_commits_and_rolls_back_one_shared_session():
    session = MagicMock()
    uow = SqlAlchemyEngineeringRelationshipUnitOfWork(lambda: session)
    with uow as entered:
        assert entered.engineering_relationships.session is session
        assert entered.audit.session is session
        assert entered.domain_events.session is session
        assert entered.idempotency.session is session
        entered.commit()
    session.commit.assert_called_once()

    session.reset_mock()
    with pytest.raises(RuntimeError):
        with SqlAlchemyEngineeringRelationshipUnitOfWork(lambda: session):
            raise RuntimeError("force rollback")
    session.rollback.assert_called_once()


def test_create_persists_relationship_audit_outbox_and_idempotency_atomically(
    db_session, relationship_domain,
):
    domain = relationship_domain
    actor_user = domain["actors"]["consumer"]
    project = domain["project"]
    workspace = domain["consumer_workspace"]
    organization = Organization()
    db_session.add(organization)
    db_session.flush()
    now = datetime.now(timezone.utc)
    source = EngineeringObject(
        id=uuid4(), organization_id=organization.id,
        customer_id=project.customer_id, project_id=project.id,
        workspace_id=workspace.id, family="electrical",
        discipline="electrical", object_type="motor", subtype=None,
        lifecycle="active", authority_standing="approved", version=1,
        creator_id=actor_user.id, steward_id=actor_user.id,
        created_at=now, updated_at=now,
    )
    target = EngineeringObject(
        id=uuid4(), organization_id=organization.id,
        customer_id=project.customer_id, project_id=project.id,
        workspace_id=workspace.id, family="electrical",
        discipline="electrical", object_type="transformer", subtype=None,
        lifecycle="active", authority_standing="approved", version=1,
        creator_id=actor_user.id, steward_id=actor_user.id,
        created_at=now, updated_at=now,
    )
    evidence = Evidence(
        id=uuid4(), organization_id=organization.id, project_id=project.id,
        workspace_id=workspace.id, lifecycle="current",
        source_kind="engineering_record", source_reference="ENG-001",
        source_revision="A", source_standing="current",
        supported_fact="Approved relationship basis", creator_id=actor_user.id,
        version=1, created_at=now, updated_at=now,
    )
    db_session.add_all([source, target, evidence])
    db_session.commit()
    factory = sessionmaker(
        bind=db_session.get_bind(), expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    repository = SqlAlchemyEngineeringRelationshipRepository(db_session)
    service = EngineeringRelationshipService(
        uow_factory=lambda: SqlAlchemyEngineeringRelationshipUnitOfWork(factory),
        authorization=SqlAlchemyRelationshipAuthorizationPolicy(db_session),
        validator=SqlAlchemyRelationshipValidator(db_session, repository),
        clock=UtcRelationshipClock(),
    )
    actor = AuthenticatedRelationshipActor(actor_user.id, organization.id)
    data = EngineeringRelationshipCreate(
        source_object_id=source.id, target_object_id=target.id,
        relationship_family=RelationshipFamily.ELECTRICAL,
        relationship_type=RelationshipType.POWERED_BY,
        evidence_references=[evidence.id], rationale="Approved engineering basis",
    )
    idempotency_id = uuid4()
    result = service.create(
        data=data, actor=actor,
        context=RelationshipAuthorizationContext("CreateEngineeringRelationship", {}),
        correlation_id=uuid4(), idempotency_id=idempotency_id,
    )
    assert result.version == 1
    db_session.expire_all()
    assert db_session.query(AuditLog).filter_by(
        entity="ENGINEERING_RELATIONSHIP", entity_uuid=result.id
    ).count() == 1
    assert db_session.query(EngineeringRelationshipOutbox).filter_by(
        aggregate_id=result.id
    ).count() == 1
    with pytest.raises(EngineeringRelationshipVersionConflict):
        service.submit_for_review(
            result.id,
            SubmitEngineeringRelationshipForReviewRequest(
                relationship_family="electrical",
                relationship_type="powered_by", expected_version=99,
                rationale="Stale command", evidence_references=[evidence.id],
            ), actor,
            RelationshipAuthorizationContext("SubmitEngineeringRelationshipForReview", {}),
            uuid4(), uuid4(),
        )
    with pytest.raises(EngineeringRelationshipProtectedNotFound):
        service.get(
            uuid4(), actor,
            RelationshipAuthorizationContext("ReadEngineeringRelationship", {}),
        )
    assert db_session.query(EngineeringRelationshipIdempotency).filter_by(
        aggregate_id=result.id, status="completed"
    ).count() == 1
    replay = service.create(
        data=data, actor=actor,
        context=RelationshipAuthorizationContext("CreateEngineeringRelationship", {}),
        correlation_id=uuid4(), idempotency_id=idempotency_id,
    )
    assert replay.id == result.id
    assert db_session.query(EngineeringRelationshipOutbox).filter_by(
        aggregate_id=result.id
    ).count() == 1
