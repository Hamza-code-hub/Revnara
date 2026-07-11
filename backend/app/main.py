from datetime import UTC, datetime

from fastapi import FastAPI

from app.company.router import router as company_router
from app.config import get_settings
from app.files.router import router as files_router
from app.organizations.invitations import router as members_router
from app.organizations.router import router as organizations_router
from app.tenancy.rate_limit import TenantRateLimitMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    app.add_middleware(TenantRateLimitMiddleware)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "version": settings.version,
            "time": datetime.now(UTC).isoformat(),
        }

    app.include_router(organizations_router)
    app.include_router(members_router)
    app.include_router(company_router)
    app.include_router(files_router)

    return app


app = create_app()
