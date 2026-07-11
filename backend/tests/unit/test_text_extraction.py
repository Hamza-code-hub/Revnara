import io

from docx import Document

from app.rag.text_extraction import extract_text


def _build_minimal_pdf(text: str) -> bytes:
    """Hand-builds a real, structurally valid minimal PDF (proper xref
    table with correct byte offsets -- pypdf's reader rejects a PDF
    without one, confirmed by actually trying) containing a single page
    with `text` drawn on it. No external PDF-writing library is a
    dependency here; this is the smallest real PDF pypdf can parse."""
    objects = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>"
        b"/MediaBox[0 0 200 200]/Contents 5 0 R>>",
        b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
    ]
    stream_content = f"BT /F1 24 Tf 10 100 Td ({text}) Tj ET".encode()
    objects.append(
        b"<</Length " + str(len(stream_content)).encode() + b">>\nstream\n"
        + stream_content + b"\nendstream"
    )

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj".encode() + obj + b"endobj\n")
    xref_offset = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n".encode())
    out.write(b"0000000000 65535 f \n")
    for offset in offsets:
        out.write(f"{offset:010d} 00000 n \n".encode())
    out.write(b"trailer\n<</Size " + str(len(objects) + 1).encode() + b"/Root 1 0 R>>\n")
    out.write(b"startxref\n" + str(xref_offset).encode() + b"\n%%EOF")
    return out.getvalue()


def _build_minimal_docx(paragraphs: list[str]) -> bytes:
    document = Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_plain_text_is_decoded_directly() -> None:
    text = extract_text(
        content_type="text/plain", filename="notes.txt", data=b"hello world"
    )
    assert text == "hello world"


def test_unknown_content_type_falls_back_to_plain_text() -> None:
    text = extract_text(content_type=None, filename="notes", data=b"raw bytes here")
    assert text == "raw bytes here"


def test_pdf_is_extracted_by_content_type() -> None:
    data = _build_minimal_pdf("Hello PDF")
    text = extract_text(content_type="application/pdf", filename="upload.bin", data=data)
    assert "Hello PDF" in text


def test_pdf_is_extracted_by_extension_when_content_type_is_missing() -> None:
    data = _build_minimal_pdf("Hello PDF")
    text = extract_text(content_type=None, filename="proposal.pdf", data=data)
    assert "Hello PDF" in text


def test_docx_is_extracted_by_content_type() -> None:
    data = _build_minimal_docx(["First paragraph.", "Second paragraph."])
    text = extract_text(
        content_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        filename="upload.bin",
        data=data,
    )
    assert "First paragraph." in text
    assert "Second paragraph." in text


def test_docx_is_extracted_by_extension_when_content_type_is_missing() -> None:
    data = _build_minimal_docx(["Only paragraph."])
    text = extract_text(content_type=None, filename="case-study.docx", data=data)
    assert "Only paragraph." in text
