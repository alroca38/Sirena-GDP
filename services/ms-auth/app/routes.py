# ROUTES.PY - ms-auth
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field

from gdp_common.auth import extractBearerToken, getCurrentUser
from gdp_common.errors import NotAuthenticated

from . import service

router = APIRouter()


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=1, max_length=256)


class RefreshRequest(BaseModel):
    refreshToken: str = Field(..., min_length=1, max_length=4096)


@router.get("/api/auth/health", tags=["Health"], summary="Estado del microservicio ms-auth")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ms-auth"}


@router.post("/api/auth/v1/login", tags=["Autenticación"], summary="Inicio de sesión con Roble")
def login(body: LoginRequest) -> dict[str, Any]:
    return service.login(body.email.strip(), body.password)


@router.post("/api/auth/v1/refresh", tags=["Autenticación"], summary="Renovación del token de acceso")
def refresh(body: RefreshRequest) -> dict[str, Any]:
    return service.refresh(body.refreshToken)


@router.get("/api/auth/v1/me", tags=["Autenticación"], summary="Usuario de la sesión actual")
def me(request: Request, _user: str = Depends(getCurrentUser)) -> dict[str, Any]:
    return service.publicUser(request.state.claims)


@router.post("/api/auth/v1/logout", status_code=204, tags=["Autenticación"], summary="Cierre de sesión")
def logout(request: Request) -> Response:
    try:
        service.logout(extractBearerToken(request))
    except NotAuthenticated:
        pass  # sin token no hay nada que cerrar en Roble; el cliente limpia su estado
    return Response(status_code=204)
