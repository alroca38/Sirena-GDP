# ROBLE.PY
# Cliente mínimo de los endpoints de autenticación de Roble.
#
# Replica los mismos endpoints que usa el paquete oficial `roble`
# (https://github.com/openlabun/python_roble_package):
#   POST {base}/auth/{contract}/login
#   GET  {base}/auth/{contract}/me
#   POST {base}/auth/{contract}/refresh-token
#   POST {base}/auth/{contract}/logout
#

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

import httpx
import jwt

from gdp_common.config import getSettings
from gdp_common.errors import (
    AuthProviderUnavailable,
    DuplicatedUser,
    InternalError,
    NotAuthenticated,
    UserRegistrationRejected,
)

log = logging.getLogger("gdp.roble")

__all__ = ["login", "refresh", "me", "registerUser", "logout", "getHttpClient"]


@lru_cache(maxsize=1)
def getHttpClient() -> httpx.Client:
    return httpx.Client(timeout=getSettings().authTimeoutSeconds)


def _authUrl() -> str:
    settings = getSettings()
    if not settings.robleContractId:
        log.error("ROBLE_CONTRACT_ID no está configurado.")
        raise InternalError("La autenticación con Roble no está configurada en el servidor.")
    return f"{settings.robleBaseUrl}/auth/{settings.robleContractId}"


def _call(
    method: str,
    endpoint: str,
    *,
    body: dict[str, Any] | None = None,
    token: str | None = None,
) -> tuple[int, Any]:
    """Ejecuta la petición. Devuelve (status, json) para 2xx y 4xx.

    Los fallos de red y las respuestas 5xx se convierten en AuthProviderUnavailable:
    no significan que el token sea inválido, sino que no se pudo comprobar.
    """
    url = f"{_authUrl()}/{endpoint}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = getHttpClient().request(method, url, json=body, headers=headers)
    except httpx.HTTPError as exc:
        log.warning("Roble no respondió en %s: %s", endpoint, exc)
        raise AuthProviderUnavailable() from exc

    if resp.status_code >= 500:
        # Roble responde 500 en /auth cuando el contract_id no existe.
        log.error("Roble respondió %s en %s (¿ROBLE_CONTRACT_ID correcto?)", resp.status_code, endpoint)
        raise AuthProviderUnavailable()

    try:
        data = resp.json() if resp.content else None
    except ValueError:
        data = None
    return resp.status_code, data


def login(email: str, password: str) -> dict[str, Any]:
    status, data = _call("POST", "login", body={"email": email, "password": password})
    if status >= 400:
        raise NotAuthenticated("Correo o contraseña incorrectos.")
    if not isinstance(data, dict) or not data.get("accessToken"):
        log.error("Respuesta inesperada de /login: %r", data)
        raise AuthProviderUnavailable()
    return data


def refresh(refreshToken: str) -> dict[str, Any]:
    status, data = _call("POST", "refresh-token", body={"refreshToken": refreshToken})
    if status >= 400:
        raise NotAuthenticated("La sesión expiró. Inicie sesión de nuevo.")
    if not isinstance(data, dict) or not data.get("accessToken"):
        log.error("Respuesta inesperada de /refresh-token: %r", data)
        raise AuthProviderUnavailable()
    return data


def me(accessToken: str) -> dict[str, Any]:
    status, data = _call("GET", "me", token=accessToken)
    if status >= 400:
        raise NotAuthenticated("El token de acceso no es válido o ha expirado.")
    if not isinstance(data, dict):
        log.error("Respuesta inesperada de /me: %r", data)
        raise AuthProviderUnavailable()
    if not data.get("role"):
        try:
            tokenClaims = jwt.decode(accessToken, options={"verify_signature": False})
            role = tokenClaims.get("role") or tokenClaims.get("roles")
            if role:
                data["role"] = role
        except Exception:  # noqa: BLE001
            pass
    return data


def registerUser(email: str, password: str, name: str) -> dict[str, str]:
    """Crea una cuenta activa en Roble sin iniciar sesión como esa cuenta."""
    status, data = _call(
        "POST",
        "signup-direct",
        body={"email": email, "password": password, "name": name},
    )
    message = ""
    if isinstance(data, dict):
        message = " ".join(str(data.get(key, "")) for key in ("detail", "message", "error")).lower()
    if status == 409 or (status == 400 and any(word in message for word in ("already exists", "already registered", "duplicate", "ya existe", "ya registrado"))):
        raise DuplicatedUser()
    if status >= 400:
        raise UserRegistrationRejected()
    # No devolver la respuesta íntegra: Roble puede incluir tokens u otros datos.
    return {"email": email, "name": name}


def logout(accessToken: str) -> None:
    """Cierre de sesión en Roble. Es de mejor esfuerzo: nunca lanza."""
    try:
        _call("POST", "logout", token=accessToken)
    except Exception:  # noqa: BLE001
        log.info("No se pudo cerrar la sesión en Roble; se descarta localmente.")
