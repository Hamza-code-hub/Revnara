import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from app.auth.jwt import TokenValidationError, verify_jwt
from app.config import get_settings
from tests.conftest import TEST_JWT_SECRET, make_token


def test_valid_token_is_accepted() -> None:
    user_id = uuid.uuid4()
    token = make_token(user_id=user_id, email="user@example.com")

    claims = verify_jwt(token)

    assert claims.user_id == user_id
    assert claims.email == "user@example.com"


def test_expired_token_is_rejected() -> None:
    payload = {
        "sub": str(uuid.uuid4()),
        "aud": "authenticated",
        "exp": datetime.now(UTC) - timedelta(hours=1),
    }
    token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")

    with pytest.raises(TokenValidationError):
        verify_jwt(token)


def test_tampered_signature_is_rejected() -> None:
    token = make_token()
    tampered = token[:-4] + ("AAAA" if token[-4:] != "AAAA" else "BBBB")

    with pytest.raises(TokenValidationError):
        verify_jwt(tampered)


def test_wrong_secret_is_rejected() -> None:
    payload = {"sub": str(uuid.uuid4()), "aud": "authenticated"}
    token = jwt.encode(payload, "a-completely-different-secret-value", algorithm="HS256")

    with pytest.raises(TokenValidationError):
        verify_jwt(token)


def test_missing_token_is_rejected() -> None:
    with pytest.raises(TokenValidationError):
        verify_jwt("")


def test_wrong_audience_is_rejected() -> None:
    payload = {"sub": str(uuid.uuid4()), "aud": "some-other-audience"}
    token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")

    with pytest.raises(TokenValidationError):
        verify_jwt(token)


def test_missing_subject_is_rejected() -> None:
    payload = {"aud": "authenticated"}
    token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")

    with pytest.raises(TokenValidationError):
        verify_jwt(token)


def test_non_uuid_subject_is_rejected() -> None:
    payload = {"sub": "not-a-uuid", "aud": "authenticated"}
    token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")

    with pytest.raises(TokenValidationError):
        verify_jwt(token)


class _FakeSigningKey:
    def __init__(self, key: object) -> None:
        self.key = key


class _FakeJWKClient:
    def __init__(self, key: object) -> None:
        self._key = key

    def get_signing_key_from_jwt(self, token: str) -> _FakeSigningKey:
        return _FakeSigningKey(self._key)


def _make_es256_token(*, user_id: uuid.UUID | None = None, email: str | None = "user@example.com"):
    """Real Supabase projects sign with an asymmetric key served over JWKS
    (Project Settings -> API -> JWT Keys, confirmed Sprint 4) -- this
    generates a throwaway EC keypair to sign a token the same way, without
    needing a real network-reachable JWKS endpoint in tests. Returns
    (token, public_key) so the caller can wire the public key into a fake
    JWKS client."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    payload = {"sub": str(user_id or uuid.uuid4()), "email": email, "aud": "authenticated"}
    token = jwt.encode(payload, private_key, algorithm="ES256")
    return token, private_key.public_key()


def test_valid_es256_token_is_accepted_via_jwks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    get_settings.cache_clear()

    user_id = uuid.uuid4()
    token, public_key = _make_es256_token(user_id=user_id)
    monkeypatch.setattr("app.auth.jwt._jwks_client", lambda url: _FakeJWKClient(public_key))

    claims = verify_jwt(token)

    assert claims.user_id == user_id
    assert claims.email == "user@example.com"

    get_settings.cache_clear()


def test_es256_token_rejected_when_signed_by_a_different_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    get_settings.cache_clear()

    token, _real_public_key = _make_es256_token()
    wrong_public_key = ec.generate_private_key(ec.SECP256R1()).public_key()
    monkeypatch.setattr("app.auth.jwt._jwks_client", lambda url: _FakeJWKClient(wrong_public_key))

    with pytest.raises(TokenValidationError):
        verify_jwt(token)

    get_settings.cache_clear()


def test_es256_token_rejected_when_supabase_url_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPABASE_URL", "")
    get_settings.cache_clear()

    token, _ = _make_es256_token()

    with pytest.raises(TokenValidationError):
        verify_jwt(token)

    get_settings.cache_clear()
