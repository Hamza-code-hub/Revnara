import uuid

from app.files.storage import build_tenant_storage_path, sanitize_filename


def test_sanitize_filename_keeps_a_plain_name_unchanged() -> None:
    assert sanitize_filename("proposal.pdf") == "proposal.pdf"


def test_sanitize_filename_strips_path_traversal_segments() -> None:
    """BE4.3 security testing task: a client-supplied filename must never
    be able to escape the tenant-prefixed storage path -- only the final
    path segment survives, so `../../other-tenant/secret.pdf` collapses
    to just `secret.pdf`."""
    assert sanitize_filename("../../other-tenant/secret.pdf") == "secret.pdf"


def test_sanitize_filename_strips_windows_style_path_traversal() -> None:
    assert sanitize_filename("..\\..\\windows\\secret.pdf") == "secret.pdf"


def test_sanitize_filename_strips_disallowed_characters() -> None:
    assert sanitize_filename("weird name!@#.pdf") == "weird_name___.pdf"


def test_sanitize_filename_falls_back_to_a_default_for_an_empty_result() -> None:
    assert sanitize_filename("...") == "file"


def test_build_tenant_storage_path_is_prefixed_by_the_tenant_id() -> None:
    tenant_id = uuid.uuid4()
    path = build_tenant_storage_path(tenant_id, "proposal.pdf")
    assert path.startswith(f"{tenant_id}/")
    assert path.endswith("_proposal.pdf")


def test_build_tenant_storage_path_ignores_traversal_in_the_filename() -> None:
    """Even if a malicious filename is passed straight through, the
    resulting path can never resolve outside this tenant_id's own
    prefix."""
    tenant_id = uuid.uuid4()
    other_tenant_id = uuid.uuid4()
    path = build_tenant_storage_path(tenant_id, f"../{other_tenant_id}/secret.pdf")
    assert path.startswith(f"{tenant_id}/")
    assert str(other_tenant_id) not in path


def test_build_tenant_storage_path_is_unique_per_call() -> None:
    tenant_id = uuid.uuid4()
    first = build_tenant_storage_path(tenant_id, "proposal.pdf")
    second = build_tenant_storage_path(tenant_id, "proposal.pdf")
    assert first != second
