from datetime import datetime, timezone
from uuid import uuid4
import pytest
from app.enums.supporting_file import SupportingFileLifecycle, SupportingFileMediaType
from app.schemas.supporting_file import SupportingFileListResponse, SupportingFileResponse


def response():
    return SupportingFileResponse(id=uuid4(), organization_id=uuid4(), project_id=1, workspace_id=None, safe_filename="basis.pdf", media_type=SupportingFileMediaType.PDF, byte_size=1, content_digest="a" * 64, lifecycle=SupportingFileLifecycle.QUARANTINED, version=1, uploader_id=1, uploaded_at=datetime.now(timezone.utc), scanned_at=None, predecessor_asset_id=None)


def test_list_visible_count_is_closed():
    item = response(); assert SupportingFileListResponse(items=[item], visible_count=1).visible_count == 1
    with pytest.raises(ValueError): SupportingFileListResponse(items=[item], visible_count=0)
