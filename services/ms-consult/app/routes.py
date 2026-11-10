# ROUTES.PY - ms-consult
from __future__ import annotations

from fastapi import APIRouter, Depends, Path
from fastapi.responses import Response

from gdp_common.auth import getCurrentUser
from gdp_common.schemas import PersonResponse

from . import service

router = APIRouter()


@router.get(
    "/api/consult/health",
    tags=["Health"],
    summary="Estado del microservicio ms-consult (RNF-03)",
)
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ms-consult"}


@router.get(
    "/api/consult/v1/person/{doc}",
    response_model=PersonResponse,
    tags=["Consultar Datos Personales"],
    summary="Consulta de datos personales por número de documento",
)
def consultPersonEndpoint(
    doc: str = Path(..., description="Número de documento a consultar"),
    user: str = Depends(getCurrentUser),
) -> PersonResponse:
    return service.consultPerson(doc, user)


@router.get(
    "/api/consult/v1/person/{doc}/pic",
    tags=["Consultar Datos Personales"],
    summary="Lectura de la fotografía de una persona por número de documento",
    responses={
        200: {
            "content": {"image/jpeg": {}, "image/png": {}},
            "description": "Imagen de la persona en formato JPEG o PNG",
        },
        404: {"description": "Persona o foto no encontrada"},
    },
)
def consultPersonPhotoEndpoint(
    doc: str = Path(..., description="Número de documento de la persona"),
    _user: str = Depends(getCurrentUser),
) -> Response:
    photoBytes, mediaType = service.consultPersonPhoto(doc)
    return Response(content=photoBytes, media_type=mediaType)

