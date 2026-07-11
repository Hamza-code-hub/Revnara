import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.auth.jwt import TokenValidationError, verify_jwt
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
