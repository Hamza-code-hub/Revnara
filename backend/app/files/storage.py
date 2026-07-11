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


class SupabaseStorageProvider(StorageProvider):
    """Calls Supabase Storage's real signed-upload-url REST API
    (`POST /storage/v1/object/upload/sign/{bucket}/{path}`).

    Not exercised end-to-end anywhere in this codebase -- like Sprint 2's
    Supabase Auth integration, there is no real Supabase project available
    in this environment to verify the HTTP call against (see
    docs/Revnara_Sprint_Development_Plan.md §4 Environment Prerequisites).
    Path construction and metadata handling (the part the backend fully
    controls, [build_tenant_storage_path]/app/files/service.py) are unit
    tested directly; this class's HTTP call is mocked in tests rather than
    asserted against a real response body.
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
                upload_url=f"{self._base_url}{data['url']}", token=data["token"]
            )
