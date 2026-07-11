import uuid

from pydantic import BaseModel, ConfigDict

from app.files.models import FileStatus


class SignedUploadRequest(BaseModel):
    filename: str
    content_type: str | None = None
    linked_entity_type: str | None = None
    linked_entity_id: uuid.UUID | None = None


class SignedUploadResponse(BaseModel):
    file_id: uuid.UUID
    upload_url: str
    token: str
    storage_path: str


class FileConfirmRequest(BaseModel):
    size_bytes: int | None = None


class FileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bucket: str
    storage_path: str
    original_filename: str
    content_type: str | None
    size_bytes: int | None
    status: FileStatus
    linked_entity_type: str | None
    linked_entity_id: uuid.UUID | None
