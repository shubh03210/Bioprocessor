"""Shared API error envelope helpers."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from app.domain.scheduling_rules import Violation


def error_body(code: str, message: str, details: list[Any] | None = None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
        }
    }


def violation_details(violations: list[Violation]) -> list[dict]:
    return [
        {
            "rule_id": v.rule_id,
            "message": v.message,
            "operation_ids": list(v.operation_ids),
        }
        for v in violations
    ]


def http_error(
    status_code: int,
    code: str,
    message: str,
    details: list[Any] | None = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=error_body(code, message, details),
    )


def json_error(
    status_code: int,
    code: str,
    message: str,
    details: list[Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=error_body(code, message, details),
    )
