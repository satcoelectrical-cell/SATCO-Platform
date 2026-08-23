from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import uuid4
import pytest
from app.enums.supporting_file import SupportingFileMediaType
from app.exceptions.supporting_file import SupportingFileProtectedNotFound, SupportingFileValidationError
from app.models.supporting_file_command import SupportingFileScope
from tests.test_supporting_file_service import PDF_BYTES, mutation_metadata, scope, service

def test_cross_organization_reservation_cannot_be_finalized():
    item=service(); source=SupportingFileScope(uuid4(), 1); other=SupportingFileScope(uuid4(), 1)
    reservation=item.reserve_upload(actor_id=1, scope=source)
    with pytest.raises(SupportingFileProtectedNotFound):
        item.finalize_upload(actor_id=1,reservation_id=reservation.id,scope=other,filename="basis.pdf",media_type=SupportingFileMediaType.PDF,content=PDF_BYTES,expected_digest=sha256(PDF_BYTES).hexdigest(),**mutation_metadata())


def test_continuation_is_canonical_authenticated_context_bound_and_expiring():
    item=service(); scoped=scope(); now=datetime.now(timezone.utc)
    for offset in range(3):
        reservation=item.reserve_upload(actor_id=1,scope=scoped,now=now-timedelta(seconds=offset))
        content=PDF_BYTES+str(offset).encode()
        item.finalize_upload(actor_id=1,reservation_id=reservation.id,scope=scoped,filename="basis.pdf",media_type=SupportingFileMediaType.PDF,content=content,expected_digest=sha256(content).hexdigest(),now=now-timedelta(seconds=offset),**mutation_metadata())
    first, token=item.list_metadata(actor_id=1,scope=scoped,lifecycle=None,limit=1,continuation=None,now=now)
    assert len(first)==1 and token
    second,_=item.list_metadata(actor_id=1,scope=scoped,lifecycle=None,limit=1,continuation=token,now=now)
    assert second and second[0].id != first[0].id
    for invalid_actor, invalid_scope, invalid_token, invalid_now in (
        (2,scoped,token,now),
        (1,SupportingFileScope(uuid4(),scoped.project_id),token,now),
        (1,scoped,token[:-1]+("A" if token[-1]!="A" else "B"),now),
        (1,scoped,token,now+timedelta(minutes=16)),
    ):
        with pytest.raises((SupportingFileProtectedNotFound,SupportingFileValidationError)):
            item.list_metadata(actor_id=invalid_actor,scope=invalid_scope,lifecycle=None,limit=1,continuation=invalid_token,now=invalid_now)
