from datetime import datetime, timezone
from uuid import uuid4
import pytest
from app.enums.supporting_file import SupportingFileLifecycle, SupportingFileMediaType
from app.exceptions.supporting_file import SupportingFileInvalidTransition, SupportingFileVersionConflict
from app.models.supporting_file import SupportingFileAsset
from app.models.supporting_file_command import SupportingFileScope


def asset():
    now = datetime.now(timezone.utc)
    return SupportingFileAsset.quarantine(scope=SupportingFileScope(uuid4(), 1, None), filename="basis.pdf", media_type=SupportingFileMediaType.PDF, byte_size=20, digest="a" * 64, storage_key="objects/" + "b" * 64, object_version="v1", uploader_id=1, now=now)


def test_closed_lifecycle_and_immutable_identity():
    item = asset(); item.mark_available(1, datetime.now(timezone.utc)); assert item.lifecycle == SupportingFileLifecycle.AVAILABLE
    item.withdraw(2, 1, datetime.now(timezone.utc), "withdrawn"); assert item.lifecycle == SupportingFileLifecycle.WITHDRAWN
    with pytest.raises(SupportingFileInvalidTransition): item.mark_available(3, datetime.now(timezone.utc))
    with pytest.raises(SupportingFileVersionConflict): item.withdraw(2, 1, datetime.now(timezone.utc), "again")
