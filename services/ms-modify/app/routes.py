# ROUTES.PY - ms-modify
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, Path, Request, UploadFile

from gdp_common.auth import getCurrentUser
from gdp_common.schemas import ModifyPerson, PersonResponse

from . import service

router = APIRouter()


async def _readOptionalPhoto(photo: UploadFile | None) -> bytes | None:
    if photo is None:
        return None
    content = await photo.read()
    if not content and not (photo.filename or "").strip():
        return None
    return content


@router.get(
    "/api/modify/health",
    tags=["Health"],
    summary="Estado del microservicio ms-modify",
)
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ms-modify"}


@router.get(
    "/api/modify/v1/person/{doc}",
    response_model=PersonResponse,
    tags=["Modificar Datos Personales"],
    summary="Precarga del formulario de modificación sin depender de ms-consult",
)
def preloadPersonEndpoint(
    doc: str = Path(..., description="Número de documento de la persona a modificar"),
    _user: str = Depends(getCurrentUser),
) -> PersonResponse:
    return service.preloadPerson(doc)


@router.put(
    "/api/modify/v1/person/{doc}",
    response_model=PersonResponse,
    tags=["Modificar Datos Personales"],
    summary="Actualización de datos personales y foto (reemplazar, conservar o quitar)",
)
async def modifyPersonEndpoint(
    request: Request,
    doc: str = Path(..., description="Número de documento de la persona (no editable)"),
    documentType: str | None = Form(None, description="TI o CC"),
    firstName: str | None = Form(None, description="Primer nombre (máx. 30 caracteres)"),
    secondName: str | None = Form(None, description="Segundo nombre opcional (máx. 30 caracteres)"),
    lastNames: str | None = Form(None, description="Apellidos (máx. 60 caracteres)"),
    birthdate: str | None = Form(None, description="Fecha de nacimiento (YYYY-MM-DD o dd-mmm-yyyy)"),
    genre: str | None = Form(None, description="MASCULINO, FEMENINO, NO_BINARIO, PREFIERO_NO_REPORTAR"),
    email: str | None = Form(None, description="Correo electrónico"),
    phoneNumber: str | None = Form(None, description="Celular de 10 dígitos"),
    removePhoto: bool = Form(False, description="Si es true y no se envía foto nueva, elimina la foto actual"),
    photo: UploadFile | None = File(None, description="Nueva foto opcional en formato JPEG o PNG (máx. 2 MiB)"),
    user: str = Depends(getCurrentUser),
) -> PersonResponse:
    contentType = (request.headers.get("content-type") or "").lower()
    if contentType.startswith("application/json"):
        body: dict[str, Any] = await request.json()
        form = ModifyPerson.model_validate(body)
        photoBytes = None
    else:
        form = ModifyPerson(
            documentType=documentType,
            firstName=firstName,
            secondName=secondName,
            lastNames=lastNames,
            birthdate=birthdate,
            genre=genre,
            email=email,
            phoneNumber=phoneNumber,
            removePhoto=removePhoto,
        )
        photoBytes = await _readOptionalPhoto(photo)

    return service.modifyPerson(doc, form, photoBytes, user)

