# ROUTES.PY - ms-delete
from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Response, status

from gdp_common.auth import getCurrentUser
from gdp_common.schemas import PersonResponse

from . import service

router = APIRouter()


@router.get(
    "/api/delete/health",
    tags=["Health"],
    summary="Estado del microservicio ms-delete",
)
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ms-delete"}


@router.get(
    "/api/delete/v1/person/{doc}",
    response_model=PersonResponse,
    tags=["Borrar Personas"],
    summary="Precarga de entidad para mostrar a quién se borrará antes de confirmar",
)
def preloadPersonEndpoint(
    doc: str = Path(..., description="Número de documento de la persona a identificar"),
    _user: str = Depends(getCurrentUser),
) -> PersonResponse:
    return service.preloadPerson(doc)


@router.delete(
    "/api/delete/v1/person/{doc}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Borrar Personas"],
    summary="Eliminación confirmada de una persona por número de documento",
)
def deletePersonEndpoint(
    doc: str = Path(..., description="Número de documento de la persona a eliminar"),
    user: str = Depends(getCurrentUser),
) -> Response:
    service.deletePerson(doc, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

