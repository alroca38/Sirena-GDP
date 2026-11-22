# ROUTES.PY - ms-auth
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, Field, field_validator

from gdp_common.auth import extractBearerToken, getCurrentAdmin, getCurrentUser
from gdp_common.errors import NotAuthenticated

from . import service

router = APIRouter()


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=1, max_length=256)


class RefreshRequest(BaseModel):
    refreshToken: str = Field(..., min_length=1, max_length=4096)


class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: str = Field(..., min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validatePasswordPolicy(cls, password: str) -> str:
        valid = (
            len(password) >= 8
            and any("A" <= char <= "Z" for char in password)
            and any("a" <= char <= "z" for char in password)
            and any(char in "0123456789" for char in password)
            and any(char in "!@#$_.-" for char in password)
        )
        if not valid:
            raise ValueError("La contraseña no cumple la política de seguridad.")
        return password


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


@router.post(
    "/api/auth/v1/users",
    status_code=status.HTTP_201_CREATED,
    tags=["Administración"],
    summary="Crear cuenta de usuario en Roble (solo admin)",
)
def createUser(body: CreateUserRequest, _admin: str = Depends(getCurrentAdmin)) -> dict[str, str]:
    return service.createUser(body.name.strip(), body.email.strip().lower(), body.password)


@router.post("/api/auth/v1/logout", status_code=204, tags=["Autenticación"], summary="Cierre de sesión")
def logout(request: Request) -> Response:
    try:
        service.logout(extractBearerToken(request))
    except NotAuthenticated:
        pass  # sin token no hay nada que cerrar en Roble; el cliente limpia su estado
    return Response(status_code=204)
