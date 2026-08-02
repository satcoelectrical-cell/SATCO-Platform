from datetime import datetime, timezone
from uuid import uuid4
import pytest
from app.enums import EvidenceLifecycle, EvidenceSourceKind, EvidenceSourceStanding
from app.models.evidence import Evidence
from app.models.evidence_command import CreateEvidence, EvidenceActor, EvidenceMetadata, EvidenceTransitionRejected, TransitionEvidenceLifecycle

def command():
    actor=EvidenceActor(1,uuid4()); meta=EvidenceMetadata(actor,"reason",uuid4(),uuid4(),uuid4())
    return CreateEvidence(meta,actor.organization_id,None,None,EvidenceSourceKind.ENGINEERING_RECORD,"R","1",EvidenceSourceStanding.CURRENT,None,"fact",actor.actor_id)
def test_create_and_transition_increment_once():
    now=datetime.now(timezone.utc); item,_=Evidence.create(command(),now)
    result=item.transition_lifecycle(TransitionEvidenceLifecycle(command().metadata,item.id,1,EvidenceLifecycle.CURRENT),now)
    assert item.version==2 and result.previous_version==1
def test_invalid_transition_rejected():
    now=datetime.now(timezone.utc); item,_=Evidence.create(command(),now)
    with pytest.raises(EvidenceTransitionRejected): item.transition_lifecycle(TransitionEvidenceLifecycle(command().metadata,item.id,1,EvidenceLifecycle.SUPERSEDED),now)
