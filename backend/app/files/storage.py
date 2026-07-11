import re
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9_.\-]")


def sanitize_filename(filename: str) -> str:
    """Strips any path component and disallowed characters from a
    user-supplied filename -- defends the tenant-prefixed storage path
    (below) against path traversal (e.g. `../../other-tenant/secret.pdf`)
    regardless of what a client sends as `filename` (BE4.3 security
    testing task: "signed URL replay/path traversal denial").
    """
    # Keep only the last path segment, whichever separator style the
    # client's OS used, before stripping character-level unsafe bits.
    base = filename.replace("\\", "/").rsplit("/", 1)[-1]
    safe = _UNSAFE_FILENAME_CHARS.sub("_", base).strip("._")
    return safe or "file"


def build_tenant_storage_path(tenant_id: uuid.UUID, filename: str) -> str:
    """Every uploaded file's path is prefixed with its tenant id -- the
    backend-side half of tenant isolation for Storage. The Supabase bucket
    policy (DB4.2) is the other half and cannot be exercised without a
    real Supabase project -- see [SupabaseStorageProvider]'s docstring.
    A random UUID prefix on the filename itself additionally makes a
    guessed/replayed path useless without also guessing that UUID.
    """
    safe_filename = sanitize_filename(filename)
    return f"{tenant_id}/{uuid.uuid4()}_{safe_filename}"


@dataclass(frozen=True)
class SignedUpload:
    upload_url: str
    token: str


class StorageProvider(ABC):
    @abstractmethod
    async def create_signed_upload_url(self, *, bucket: str, path: str) -> SignedUpload: ...

    @abstractmethod
    async def download_file(self, *, bucket: str, path: str) -> bytes: ...


class SupabaseStorageProvider(StorageProvider):
    """Calls Supabase Storage's real signed-upload-url REST API
    (`POST /storage/v1/object/upload/sign/{bucket}/{path}`).

    Verified end-to-end (Sprint 4) against a real Supabase project: the
    create-signed-URL call, and a real PUT of file bytes to the resulting
    URL, both succeed. The response's `url` field is relative to the
    Storage API root (`/storage/v1`), not the bare project domain --
    prepending only `base_url` without that segment produces a URL that
    404s with "requested path is invalid", caught by actually performing
    the PUT rather than only asserting the URL was constructed.
    """

    def __init__(self, *, base_url: str, service_role_key: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._service_role_key = service_role_key

    async def create_signed_upload_url(self, *, bucket: str, path: str) -> SignedUpload:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            response = await client.post(
                f"/storage/v1/object/upload/sign/{bucket}/{path}",
                headers={"Authorization": f"Bearer {self._service_role_key}"},
            )
            response.raise_for_status()
            data = response.json()
            return SignedUpload(
                upload_url=f"{self._base_url}/storage/v1{data['url']}", token=data["token"]
            )

    async def download_file(self, *, bucket: str, path: str) -> bytes:
        """Fetches an object's raw bytes via the service-role key (Sprint 5,
        document_worker) -- unlike uploads, downloads for the worker's own
        processing never go through a signed URL, since the worker itself
        holds the service-role credential already."""
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            response = await client.get(
                f"/storage/v1/object/{bucket}/{path}",
                headers={"Authorization": f"Bearer {self._service_role_key}"},
            )
            response.raise_for_status()
            return response.content
