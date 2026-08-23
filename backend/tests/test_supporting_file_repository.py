from datetime import datetime, timezone
from uuid import uuid4
from app.enums.supporting_file import SupportingFileMediaType
from app.models.supporting_file import SupportingFileAsset
from app.models.supporting_file_command import SupportingFileScope


def test_repository_aggregate_constructs_without_session_commit_ownership():
    asset = SupportingFileAsset.quarantine(scope=SupportingFileScope(uuid4(), 1), filename="basis.pdf", media_type=SupportingFileMediaType.PDF, byte_size=1, digest="a" * 64, storage_key="objects/" + "c" * 64, object_version="v1", uploader_id=1, now=datetime.now(timezone.utc))
    assert asset.version == 1 and asset.lifecycle == "quarantined"
