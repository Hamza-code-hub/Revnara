from app.main import create_app


def test_app_boots_without_exceptions() -> None:
    app = create_app()

    assert app is not None
    assert any(route.path == "/health" for route in app.routes)
