# CONFIG.PY
# Lectura de variables de entorno
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

__all__ = ["Settings", "getSettings", "clearSettingsCache"]


def _firstEnv(*names: str, default: str | None = None) -> str | None:
    for name in names:
        val = os.environ.get(name)
        if val is not None and val.strip() != "":
            return val.strip()
    return default


@dataclass(frozen=True)
class Settings:
    dbUrl: str
    jwksUrl: str | None = None
    issuer: str | None = None
    audience: str | None = None
    publicKey: str | None = None
    jwtSecret: str | None = None
    robleVerifyUrl: str | None = None
    algorithms: tuple[str, ...] = ("RS256", "HS256", "ES256")
    n8nWebhookUrl: str = "http://n8n:5678/webhook/person-sync"
    n8nTimeoutSeconds: float = 3.0


@lru_cache(maxsize=1)
def getSettings() -> Settings:
    dbUrl = _firstEnv("DB_URL")
    if not dbUrl:
        pgUser = _firstEnv("POSTGRES_USER", default="postgres")
        pgPass = _firstEnv("POSTGRES_PASSWORD", default="postgres")
        pgHost = _firstEnv("POSTGRES_HOST", default="postgres")
        pgPort = _firstEnv("POSTGRES_PORT", default="5432")
        pgDb = _firstEnv("POSTGRES_DB", default="sirena")
        dbUrl = f"postgresql+psycopg://{pgUser}:{pgPass}@{pgHost}:{pgPort}/{pgDb}"

    jwksUrl = _firstEnv("ROBLE_JWKS_URL", "SSO_JWKS_URL", "JWKS_URL")
    issuer = _firstEnv("ROBLE_ISSUER", "SSO_ISSUER", "JWT_ISSUER")
    audience = _firstEnv("ROBLE_AUDIENCE", "SSO_AUDIENCE", "JWT_AUDIENCE")
    publicKey = _firstEnv("ROBLE_PUBLIC_KEY", "SSO_PUBLIC_KEY", "JWT_PUBLIC_KEY")
    jwtSecret = _firstEnv("ROBLE_JWT_SECRET", "SSO_JWT_SECRET", "JWT_SECRET")

    robleVerifyUrl = _firstEnv("ROBLE_VERIFY_URL")
    if not robleVerifyUrl:
        authBase = _firstEnv("ROBLE_AUTH_URL")
        contract = _firstEnv("ROBLE_CONTRACT", "ROBLE_DB_NAME", "ROBLE_PROJECT_ID")
        if authBase and contract:
            robleVerifyUrl = f"{authBase.rstrip('/')}/{contract.strip('/')}/verify-token"

    rawAlgs = _firstEnv("ROBLE_ALGORITHMS", "JWT_ALGORITHMS")
    algorithms = (
        tuple(a.strip() for a in rawAlgs.split(",") if a.strip())
        if rawAlgs
        else ("RS256", "HS256", "ES256")
    )

    n8nWebhookUrl = (
        _firstEnv("N8N_WEBHOOK_URL", default="http://n8n:5678/webhook/person-sync")
        or "http://n8n:5678/webhook/person-sync"
    )
    try:
        n8nTimeout = float(_firstEnv("N8N_TIMEOUT_SECONDS", default="3.0") or "3.0")
    except ValueError:
        n8nTimeout = 3.0

    return Settings(
        dbUrl=dbUrl,
        jwksUrl=jwksUrl,
        issuer=issuer,
        audience=audience,
        publicKey=publicKey,
        jwtSecret=jwtSecret,
        robleVerifyUrl=robleVerifyUrl,
        algorithms=algorithms,
        n8nWebhookUrl=n8nWebhookUrl,
        n8nTimeoutSeconds=n8nTimeout,
    )


def clearSettingsCache() -> None:
    getSettings.cache_clear()
