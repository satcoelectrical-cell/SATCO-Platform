from io import BytesIO
from app.adapters.supporting_file_object_store import InMemoryPrivateSupportingFileObjectStore, new_opaque_object_key

def test_exact_key_store_has_no_list_or_public_url_and_binds_digest():
    store=InMemoryPrivateSupportingFileObjectStore(); key=new_opaque_object_key(); receipt=store.put_private(key=key,content=BytesIO(b"basis"),media_type="application/pdf")
    assert receipt.key == key and receipt.byte_size == 5 and store.head_exact(key, receipt.version) == receipt
    assert not hasattr(store, "list") and not hasattr(store, "public_url")
