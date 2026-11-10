# AUTH.PY
# Validación de JWT
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

import httpx
import jwt
from fastapi import Request

from gdp_common.config import getSettings
from gdp_common.errors import NotAuthenticated

log = logging.getLogger("gdp.auth")

__all__ = [
    "extractBearerToken",
    "verifyToken",
    "extractUserFromClaims",
    "getCurrentUser",
    "tryGetCurrentUser",
]


@lru_cache(maxsize=4)
def _getJwksClient(jwksUrl: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(jwksUrl, cache_keys=True)


def extractBearerToken(request: Request) -> str:
    authHeader = request.headers.get("Authorization") or request.headers.get("authorization")
    if authHeader:
        parts = authHeader.strip().split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
            raise NotAuthenticated("El encabezado Authorization debe tener el formato 'Bearer <token>'.")
        return parts[1].strip()

    queryToken = request.query_params.get("token")
    if queryToken and queryToken.strip():
        return queryToken.strip()

    raise NotAuthenticated("No se proporcionó un token de autenticación válido.")


def extractUserFromClaims(claims: dict[str, Any]) -> str:
    for key in ("preferred_username", "username", "name", "email", "sub"):
        val = claims.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()

    nestedUser = claims.get("user")
    if isinstance(nestedUser, dict):
        for key in ("username", "name", "email", "id"):
            val = nestedUser.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()

    return "usuario"


def verifyToken(token: str) -> dict[str, Any]:
    if not token or token.count(".") != 2:
        raise NotAuthenticated("El token de acceso tiene un formato inválido.")

    parts = token.split(".")
    if any(not p for p in parts):
        raise NotAuthenticated("El token de acceso está incompleto.")

    settings = getSettings()
    decodeKwargs: dict[str, Any] = {
        "algorithms": list(settings.algorithms),
        "options": {
            "require": ["exp"],
            "verify_exp": True,
            "verify_iss": bool(settings.issuer),
            "verify_aud": bool(settings.audience),
        },
    }
    if settings.issuer:
        decodeKwargs["issuer"] = settings.issuer
    if settings.audience:
        decodeKwargs["audience"] = settings.audience

    try:
        if settings.jwksUrl:
            signingKey = _getJwksClient(settings.jwksUrl).get_signing_key_from_jwt(token).key
            claims = jwt.decode(token, signingKey, **decodeKwargs)
        elif settings.publicKey:
            key = settings.publicKey.replace("\\n", "\n")
            claims = jwt.decode(token, key, **decodeKwargs)
        elif settings.jwtSecret:
            claims = jwt.decode(token, settings.jwtSecret, **decodeKwargs)
        elif settings.robleVerifyUrl:
            resp = httpx.get(
                settings.robleVerifyUrl,
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0,
            )
            if resp.status_code != 200:
                raise NotAuthenticated("El token de acceso fue rechazado por el proveedor SSO (Roble).")
            header = jwt.get_unverified_header(token)
            if not header.get("alg") or str(header.get("alg")).lower() == "none":
                raise NotAuthenticated("Algoritmo de token no permitido.")
            claims = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "require": ["exp"],
                    "verify_exp": True,
                    "verify_iss": bool(settings.issuer),
                    "verify_aud": bool(settings.audience),
                },
                issuer=settings.issuer,
                audience=settings.audience,
            )
        else:
            header = jwt.get_unverified_header(token)
            alg = str(header.get("alg", ""))
            if not alg or alg.lower() == "none":
                raise NotAuthenticated("Algoritmo de token no permitido.")
            claims = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "require": ["exp"],
                    "verify_exp": True,
                    "verify_iss": bool(settings.issuer),
                    "verify_aud": bool(settings.audience),
                },
                issuer=settings.issuer,
                audience=settings.audience,
            )
    except NotAuthenticated:
        raise
    except jwt.ExpiredSignatureError as exc:
        raise NotAuthenticated("El token de acceso ha expirado.") from exc
    except jwt.InvalidIssuerError as exc:
        raise NotAuthenticated("El emisor del token no es válido.") from exc
    except jwt.InvalidAudienceError as exc:
        raise NotAuthenticated("La audiencia del token no es válida.") from exc
    except (jwt.PyJWTError, httpx.HTTPError, ValueError) as exc:
        raise NotAuthenticated("El token de acceso no es válido.") from exc

    if not isinstance(claims, dict):
        raise NotAuthenticated("El contenido del token no es válido.")

    return claims


def getCurrentUser(request: Request) -> str:
    token = extractBearerToken(request)
    claims = verifyToken(token)
    user = extractUserFromClaims(claims)
    request.state.user = user
    request.state.claims = claims
    return user


def tryGetCurrentUser(request: Request) -> str | None:
    existing = getattr(request.state, "user", None)
    if isinstance(existing, str) and existing:
        return existing
    try:
        return getCurrentUser(request)
    except Exception:
        return None
