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
    robleBaseUrl: str = "https://roble-api.test-openlab.uninorte.edu.co"
    robleContractId: str | None = None
    authCacheTtlSeconds: float = 30.0
    authTimeoutSeconds: float = 5.0
    n8nWebhookUrl: str = "http://n8n:5678/webhook/person-sync"
    n8nTimeoutSeconds: float = 3.0


def _floatEnv(name: str, default: float) -> float:
    try:
        return float(_firstEnv(name, default=str(default)) or default)
    except ValueError:
        return default


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

    robleBaseUrl = (
        _firstEnv("ROBLE_BASE_URL", default=Settings.robleBaseUrl) or Settings.robleBaseUrl
    ).rstrip("/")
    robleContractId = _firstEnv("ROBLE_CONTRACT_ID")

    n8nWebhookUrl = (
        _firstEnv("N8N_WEBHOOK_URL", default="http://n8n:5678/webhook/person-sync")
        or "http://n8n:5678/webhook/person-sync"
    )

    return Settings(
        dbUrl=dbUrl,
        robleBaseUrl=robleBaseUrl,
        robleContractId=robleContractId,
        authCacheTtlSeconds=_floatEnv("AUTH_CACHE_TTL_SECONDS", 30.0),
        authTimeoutSeconds=_floatEnv("ROBLE_TIMEOUT_SECONDS", 5.0),
        n8nWebhookUrl=n8nWebhookUrl,
        n8nTimeoutSeconds=_floatEnv("N8N_TIMEOUT_SECONDS", 3.0),
    )


def clearSettingsCache() -> None:
    getSettings.cache_clear()
