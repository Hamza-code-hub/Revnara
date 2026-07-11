import io

from docx import Document
from pypdf import PdfReader

_PDF_CONTENT_TYPES = {"application/pdf"}
_DOCX_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}


def extract_text(*, content_type: str | None, filename: str, data: bytes) -> str:
    """Extracts plain text from uploaded file bytes (BE5.1). Dispatches on
    `content_type` first, falling back to the filename's extension, since
    Storage doesn't always have a reliable content_type on every object.
    Anything not recognized as PDF/DOCX is treated as plain text.
    """
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if content_type in _PDF_CONTENT_TYPES or extension == "pdf":
        return _extract_pdf_text(data)
    if content_type in _DOCX_CONTENT_TYPES or extension == "docx":
        return _extract_docx_text(data)
    return data.decode("utf-8", errors="replace")


def _extract_pdf_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx_text(data: bytes) -> str:
    document = Document(io.BytesIO(data))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)
