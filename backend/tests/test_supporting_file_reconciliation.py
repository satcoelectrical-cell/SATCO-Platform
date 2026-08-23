from hashlib import sha256
from app.enums.supporting_file import SupportingFileMediaType
from app.models.supporting_file_command import SupportingFileScope
from tests.test_supporting_file_service import PDF_BYTES, mutation_metadata, service
from uuid import uuid4

def test_rejected_scan_keeps_immutable_object_key_and_marks_asset_rejected():
    item=service("unsafe"); scope=SupportingFileScope(uuid4(), 1); reservation=item.reserve_upload(actor_id=1, scope=scope)
    asset=item.finalize_upload(actor_id=1,reservation_id=reservation.id,scope=scope,filename="basis.pdf",media_type=SupportingFileMediaType.PDF,content=PDF_BYTES,expected_digest=sha256(PDF_BYTES).hexdigest(),**mutation_metadata())
    assert asset.lifecycle == "rejected" and asset.storage_key == reservation.storage_key
