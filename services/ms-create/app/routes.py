# ROUTES.PY - ms-create
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status

from gdp_common.auth import getCurrentUser
from gdp_common.schemas import CreatePerson, PersonResponse

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
    "/api/create/health",
    tags=["Health"],
    summary="Estado del microservicio ms-create",
)
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ms-create"}


@router.post(
    "/api/create/v1/person",
    response_model=PersonResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Crear Personas"],
    summary="Creación de personas (multipart/form-data, foto opcional)",
)
async def createPersonEndpoint(
    request: Request,
    documentType: str | None = Form(None, description="TI o CC"),
    documentId: str | None = Form(None, description="Número de documento (1-10 dígitos)"),
    firstName: str | None = Form(None, description="Primer nombre (máx. 30 caracteres)"),
    secondName: str | None = Form(None, description="Segundo nombre opcional (máx. 30 caracteres)"),
    lastNames: str | None = Form(None, description="Apellidos (máx. 60 caracteres)"),
    birthdate: str | None = Form(None, description="Fecha de nacimiento (YYYY-MM-DD o dd-mmm-yyyy)"),
    genre: str | None = Form(None, description="MASCULINO, FEMENINO, NO_BINARIO, PREFIERO_NO_REPORTAR"),
    email: str | None = Form(None, description="Correo electrónico"),
    phoneNumber: str | None = Form(None, description="Celular de 10 dígitos"),
    photo: UploadFile | None = File(None, description="Fotografía opcional en formato JPEG o PNG (máx. 2 MiB)"),
    user: str = Depends(getCurrentUser),
) -> PersonResponse:
    contentType = (request.headers.get("content-type") or "").lower()
    if contentType.startswith("application/json"):
        body: dict[str, Any] = await request.json()
        form = CreatePerson.model_validate(body)
        photoBytes = None
    else:
        form = CreatePerson(
            documentType=documentType,
            documentId=documentId,
            firstName=firstName,
            secondName=secondName,
            lastNames=lastNames,
            birthdate=birthdate,
            genre=genre,
            email=email,
            phoneNumber=phoneNumber,
        )
        photoBytes = await _readOptionalPhoto(photo)

    return service.createPerson(form, photoBytes, user)

