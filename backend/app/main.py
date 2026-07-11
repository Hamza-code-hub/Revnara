from datetime import UTC, datetime

from fastapi import FastAPI

from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "version": settings.version,
            "time": datetime.now(UTC).isoformat(),
        }

    return app


app = create_app()
