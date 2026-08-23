"""Private S3-compatible exact-key Supporting File object adapter."""
from hashlib import sha256
from io import BytesIO
from uuid import uuid4

from app.models.supporting_file_command import MAX_FILE_BYTES, bounded_stream_identity, opaque_storage_key
from app.ports.supporting_file import SupportingFileObjectReceipt, SupportingFileObjectStore


def new_opaque_object_key() -> str:
    """Random immutable domain-unrelated key; lifecycle never changes it."""
    return f"objects/{uuid4().hex}{uuid4().hex}"


class InMemoryPrivateSupportingFileObjectStore(SupportingFileObjectStore):
    """Test double, deliberately not selected by production composition."""
    def __init__(self): self._objects: dict[tuple[str, str], bytes] = {}
    def put_private(self, *, key: str, content, media_type: str) -> SupportingFileObjectReceipt:
        key = opaque_storage_key(key); payload = content.read(MAX_FILE_BYTES + 1)
        if len(payload) > MAX_FILE_BYTES: raise ValueError("supporting file exceeds accepted size")
        version = uuid4().hex; self._objects[(key, version)] = payload
        return SupportingFileObjectReceipt(key, version, len(payload), sha256(payload).hexdigest())
    def head_exact(self, key: str, version: str) -> SupportingFileObjectReceipt | None:
        payload = self._objects.get((opaque_storage_key(key), version))
        return None if payload is None else SupportingFileObjectReceipt(key, version, len(payload), sha256(payload).hexdigest())
    def open_exact(self, key: str, version: str) -> BytesIO: return BytesIO(self._objects[(opaque_storage_key(key), version)])
    def delete_exact(self, key: str, version: str) -> None: self._objects.pop((opaque_storage_key(key), version), None)


class S3PrivateSupportingFileObjectStore(SupportingFileObjectStore):
    """S3-compatible exact-key client using a separately mounted data-plane principal.

    The client deliberately exposes no bucket enumeration or pre-signed/public
    URL API. Bucket policy/IAM remains PATCH-042 operational authority.
    """
    def __init__(self, *, endpoint_url: str, bucket: str, region: str, access_key: str, secret_key: str):
        if not endpoint_url.startswith("https://") or not bucket or not region or not access_key or not secret_key:
            raise ValueError("supporting-file object store is not configured")
        import boto3
        self.bucket = bucket
        self.client = boto3.client("s3", endpoint_url=endpoint_url, region_name=region,
                                  aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    def put_private(self, *, key: str, content, media_type: str) -> SupportingFileObjectReceipt:
        key = opaque_storage_key(key); byte_size, digest = bounded_stream_identity(content)
        response = self.client.put_object(Bucket=self.bucket, Key=key, Body=content,
                                          ContentType=media_type, Metadata={"sha256": digest},
                                          ChecksumAlgorithm="SHA256", IfNoneMatch="*")
        return SupportingFileObjectReceipt(key, str(response.get("VersionId") or response.get("ETag", "")).strip('"'), byte_size, digest)

    def head_exact(self, key: str, version: str) -> SupportingFileObjectReceipt | None:
        key = opaque_storage_key(key)
        try:
            result = self.client.head_object(Bucket=self.bucket, Key=key, VersionId=version)
        except self.client.exceptions.NoSuchKey:
            return None
        digest = result.get("Metadata", {}).get("sha256")
        if not digest: return None
        return SupportingFileObjectReceipt(key, version, int(result["ContentLength"]), digest)

    def open_exact(self, key: str, version: str):
        key = opaque_storage_key(key)
        return self.client.get_object(Bucket=self.bucket, Key=key, VersionId=version)["Body"]

    def delete_exact(self, key: str, version: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=opaque_storage_key(key), VersionId=version)
