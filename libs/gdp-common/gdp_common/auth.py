# AUTH.PY
# Validación de tokens de acceso emitidos por Roble.
#
# Un token es válido si Roble lo acepta en GET /auth/{contract}/me. El resultado
# se guarda en memoria durante AUTH_CACHE_TTL_SECONDS (por defecto 30 s, y nunca
# más allá del `exp` del token) para no consultar a Roble en cada petición.
# Consecuencia: tras un logout, un token ya cacheado puede seguir valiendo hasta
# 30 s en los otros servicios.
from __future__ import annotations

import hashlib
import logging
import threading
import time
from typing import Any

import jwt
from fastapi import Request

from gdp_common import roble
from gdp_common.config import getSettings
from gdp_common.errors import AccessDenied, NotAuthenticated

log = logging.getLogger("gdp.auth")

__all__ = [
    "extractBearerToken",
    "verifyToken",
    "extractUserFromClaims",
    "getCurrentUser",
    "tryGetCurrentUser",
]

_MAX_TOKEN_LENGTH = 4096
_MAX_CACHE_ENTRIES = 1024

_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_cacheLock = threading.Lock()


def extractBearerToken(request: Request) -> str:
    authHeader = request.headers.get("Authorization")
    if not authHeader:
        raise NotAuthenticated("No se proporcionó un token de autenticación válido.")
    parts = authHeader.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise NotAuthenticated("El encabezado Authorization debe tener el formato 'Bearer <token>'.")
    return parts[1].strip()


def _tokenExpiry(token: str) -> float | None:
    """`exp` del token (solo lectura, sin validar firma: la validez la decide Roble)."""
    try:
        exp = jwt.decode(token, options={"verify_signature": False}).get("exp")
        return float(exp) if exp is not None else None
    except Exception:  # noqa: BLE001
        return None


def _cacheGet(key: str) -> dict[str, Any] | None:
    with _cacheLock:
        entry = _cache.get(key)
        if entry is None:
            return None
        if entry[0] <= time.monotonic():
            _cache.pop(key, None)
            return None
        return entry[1]


def _cachePut(key: str, profile: dict[str, Any], ttl: float) -> None:
    if ttl <= 0:
        return
    now = time.monotonic()
    with _cacheLock:
        if len(_cache) >= _MAX_CACHE_ENTRIES:
            for k in [k for k, (until, _) in _cache.items() if until <= now]:
                _cache.pop(k, None)
            if len(_cache) >= _MAX_CACHE_ENTRIES:
                _cache.clear()
        _cache[key] = (now + ttl, profile)


def clearCache() -> None:
    with _cacheLock:
        _cache.clear()


def verifyToken(token: str) -> dict[str, Any]:
    """Valida el token contra Roble y devuelve el perfil del usuario (`/me`)."""
    if not token or len(token) > _MAX_TOKEN_LENGTH or any(c.isspace() for c in token):
        raise NotAuthenticated("El token de acceso tiene un formato inválido.")

    exp = _tokenExpiry(token)
    if exp is not None and exp <= time.time():
        raise NotAuthenticated("El token de acceso ha expirado.")

    key = hashlib.sha256(token.encode()).hexdigest()
    cached = _cacheGet(key)
    if cached is not None:
        return cached

    profile = roble.me(token)
    ttl = getSettings().authCacheTtlSeconds
    if exp is not None:
        ttl = min(ttl, exp - time.time())
    _cachePut(key, profile, ttl)
    return profile


def extractUserFromClaims(profile: dict[str, Any]) -> str:
    """Identificador del usuario para el log: correo, o nombre, o userId."""
    for key in ("email", "name", "userId", "id"):
        val = profile.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return "usuario"


def getCurrentUser(request: Request) -> str:
    token = extractBearerToken(request)
    profile = verifyToken(token)
    user = extractUserFromClaims(profile)
    request.state.user = user
    request.state.claims = profile
    return user


def getCurrentAdmin(request: Request) -> str:
    """Valida la sesión con Roble y exige su rol admin en el servidor."""
    user = getCurrentUser(request)
    role = request.state.claims.get("role")
    roles = role if isinstance(role, list) else [role]
    if not any(isinstance(value, str) and value.strip().lower() == "admin" for value in roles):
        raise AccessDenied()
    return user


def tryGetCurrentUser(request: Request) -> str | None:
    existing = getattr(request.state, "user", None)
    if isinstance(existing, str) and existing:
        return existing
    try:
        return getCurrentUser(request)
    except Exception:  # noqa: BLE001
        return None
