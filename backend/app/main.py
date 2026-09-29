from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.command import router as command_router
from app.api.control import router as control_router
from app.api.errors import error_body, json_error, violation_details
from app.api.forecast import router as forecast_router
from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.api.schedule import router as schedule_router
from app.api.unit_operations import router as unit_operations_router
from app.config import settings
from app.services.scheduling import DomainViolationError, NotFoundError


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="BBP scheduling and closed-loop control API",
    )

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
        return json_error(404, "not_found", str(exc))

    @app.exception_handler(DomainViolationError)
    async def domain_violation_handler(
        _request: Request, exc: DomainViolationError
    ) -> JSONResponse:
        return json_error(
            409,
            "conflict",
            str(exc),
            violation_details(exc.violations),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = []
        for err in exc.errors():
            item = dict(err)
            ctx = item.get("ctx")
            if isinstance(ctx, dict) and "error" in ctx:
                ctx = {**ctx, "error": str(ctx["error"])}
                item["ctx"] = ctx
            details.append(item)
        return JSONResponse(
            status_code=422,
            content=error_body(
                "validation_error",
                "Request validation failed",
                details=details,
            ),
        )

    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(schedule_router, prefix=settings.api_prefix)
    app.include_router(unit_operations_router, prefix=settings.api_prefix)
    app.include_router(control_router, prefix=settings.api_prefix)
    app.include_router(forecast_router, prefix=settings.api_prefix)
    app.include_router(ingest_router)  # POST /ingest at root (assignment contract)
    app.include_router(command_router)  # POST /command at root (assignment contract)
    return app


app = create_app()
