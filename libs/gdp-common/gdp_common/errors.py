# ERRORS.PY
# 422, 409, 413, 415
from __future__ import annotations

import inspect
import logging
from typing import TYPE_CHECKING, Any, Callable, Mapping

if TYPE_CHECKING:
    from fastapi import FastAPI, Request
    from gdp_common.validators import PhotoError, ValidationResult

log = logging.getLogger("gdp.errors")

__all__ = [
    "GDPError", "InternalError", "ValidationError", "NotAuthenticated",
    "PersonNotFound", "DuplicatedDocument", "PhotoOversized",
    "PhotoFormatNotAllowed", "PhotoError", "RegisterHandlers"
]

# ---------------------
# EXCEPCIONES
# ---------------------

class ErrorGDP(Exception):
    """Clase base para errores de la API"""

    status: int = 500
    title: str = "Error interno del servidor"
    defaultDetails: str = "Ocurrió un error inesperado en el servidor."

    def __init__(
            self,
            details: str | None = None,
            *,
            errors: Mapping[str, str] | None = None,
            headers: Mapping[str, str] | None = None,
    ) -> None:
        self.details = details if details is not None else self.defaultDetails
        self.errors = dict[str, str] = dict(errors or {})
        self.headers = dict[str,str] = dict(headers or {})
        self.registered = False
        super().__init__(self.details)

    @property
    def logResult(self) -> str:
        return "RECHAZADA" if self.status < 500 else "ERROR"

    def toDict(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "status": self.status,
            "title": self.title,
            "details": self.details,
        }
        if self.errors:
            body["errors"] = self.errors
        return body

class InternalError(ErrorGDP):
    """Error interno del servidor (500)"""

class NotAuthenticated(ErrorGDP):
    status = 401
    title = "No autenticado"
    defaultDetails = "No se proporcionó un token de autenticación válido."

    def __init__(self, details: str | None = None) -> None:
        super().__init__(details, headers={"WWW-Authenticate": "Bearer"})

class ValidationError(ErrorGDP):
    status = 422
    title = "Error de validación"
    defaultDetails = "Los datos proporcionados no cumplen con los requisitos de validación."

    def __init__(self, errors: Mapping[str, str], details: str | None = None) -> None:
        if not errors:
            raise ValueError("ValidationError requires at least one error.")
        super().__init__(details, errors=errors)

    @classmethod
    def fromValidationResult(cls, result: ValidationResult) -> ValidationError:
        return cls(result.errors)

class PersonNotFound(ErrorGDP):
    status = 404
    title = "Persona no encontrada"

    def __init__(self, documentId: str) -> None:
        self.documentId = documentId
        super().__init__(f"No se encontró una persona con el documento '{documentId}'.")

class DuplicatedDocument(ErrorGDP):
    status = 409
    title = "Documento duplicado"

    def __init__(self, documentId: str) -> None:
        self.documentId = documentId
        message = f"Ya existe una persona con el documento '{documentId}'."
        super().__init__(message, errors={"documentId": message})

class PhotoOversized(ErrorGDP):
    status = 413
    title = "Foto demasiado grande"

    def __init__(self, message: str) -> None:
        super().__init__(message, errors={"photo": message})

class PhotoFormatNotAllowed(ErrorGDP):
    status = 415
    title = "Formato de foto no permitido"

    def __init__(self, message: str) -> None:
        super().__init__(message, errors={"photo": message})

def ErrorFromPhoto(error: PhotoError) -> ErrorGDP:
    if error.status == PhotoOversized.status:
        return PhotoOversized(error.message)
    if error.status == PhotoFormatNotAllowed.status:
        return PhotoFormatNotAllowed(error.message)
    return ValidationError({"photo": error.message})

# ---------------------
# FASTAPI HANDLERS
# ---------------------
_HTTP_TITLES = {
    400: "Solicitud incorrecta",
    401: "No autenticado",
    403: "Acceso denegado",
    404: "Recurso no encontrado",
    405: "Método no permitido",
    413: "Contenido demasiado grande",
    415: "Tipo de contenido no soportado",
}

_PYDANTIC_MESSAGES = {
    "missing": "El campo es obligatorio.",
    "json_invalid": "El formato JSON de la solicitud es inválido."
}

_FASTAPI_ORIGINS = {"body", "query", "path", "header", "cookie"}

def requestErrors(exc: Any) -> dict[str, str]:
    errors: dict[str, str] = {}
    for e in exc.errors():
        loc = [p for p in e.get("loc", ()) if isinstance(p, str)]
        if loc and loc[0] in _FASTAPI_ORIGINS:
            loc = loc[1:]
        field = loc[-1] if loc else "body"
        errors.setdefault(field, _PYDANTIC_MESSAGES.get(e.get("type", ""), "Valor no válido"))
    return errors

def registerHandlers(
        app: FastAPI,
        *,
        toError: Callable[[Request, ErrorGDP], Any] | None = None
) -> None:
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse
    from starlette.exceptions import HTTPException as StarletteHTTPException

    def respond(err: ErrorGDP) -> JSONResponse:
        return JSONResponse(err.toDict(), status_code=err.status, headers=err.headers)

    async def notify(request: Request, err: ErrorGDP) -> None:
        if toError is None or err.registered:
            return
        try:
            result = toError(request, err)
            if inspect.isawaitable(result):
                await result
        except Exception:
            log.exception("Falló al registrar el rechazo")

    @app.exception_handler(ErrorGDP)
    async def _gdp(request: Request, exc: ErrorGDP) -> JSONResponse:
        await notify(request, exc)
        return respond(exc)

    @app.exception_handler(RequestValidationError)
    async def _request(request: Request, exc: RequestValidationError) -> JSONResponse:
        err = ValidationError(requestErrors(exc) or {"body": "Solicitud no válida"})
        await notify(request, err)
        return respond(err)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Rutas inexistentes (404), método no permitido (405), etc...
        body = {
            "status": exc.status_code,
            "title": _HTTP_TITLES.get(exc.status_code, "Error"),
            "detail": _HTTP_TITLES.get(exc.status_code, "Error")
        }
        return JSONResponse(body, status_code=exc.status_code, headers=getattr(exc, "headers", None))

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception) -> JSONResponse:
        log.exception("Error no controlado en %s %s", request.method, request.url.path)
        err = InternalError()
        await notify(request, err)
        return respond(err)