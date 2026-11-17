# SERVICE.PY - ms-auth
from __future__ import annotations

from typing import Any

from gdp_common import roble


def publicUser(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "userId": profile.get("userId"),
        "email": profile.get("email"),
        "name": profile.get("name"),
    }


def login(email: str, password: str) -> dict[str, Any]:
    tokens = roble.login(email, password)
    profile = roble.me(tokens["accessToken"])
    return {
        "accessToken": tokens["accessToken"],
        "refreshToken": tokens.get("refreshToken"),
        "user": publicUser(profile),
    }


def refresh(refreshToken: str) -> dict[str, Any]:
    tokens = roble.refresh(refreshToken)
    return {
        "accessToken": tokens["accessToken"],
        # Roble hoy no rota el refresh token; si lo hiciera, se propaga el nuevo.
        "refreshToken": tokens.get("refreshToken") or refreshToken,
    }


def logout(accessToken: str) -> None:
    roble.logout(accessToken)
