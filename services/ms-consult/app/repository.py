# REPOSITORY.PY - ms-consult
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from gdp_common.errors import ErrorGDP, PersonNotFound
from gdp_common.schemas import COLUMNS_PERSON, PersonResponse

_SELECT_PERSON = text(
    f"""
    SELECT {COLUMNS_PERSON}
    FROM person
    WHERE documentId = :documentId
    """
)

_SELECT_PHOTO = text(
    """
    SELECT photo, photoType
    FROM person
    WHERE documentId = :documentId
    """
)


class PhotoNotFound(ErrorGDP):
    status = 404
    title = "Foto no encontrada"

    def __init__(self, documentId: str) -> None:
        super().__init__(f"La persona con documento '{documentId}' no tiene foto registrada.")


def getPersonByDocument(session: Session, documentId: str) -> PersonResponse:
    row = session.execute(_SELECT_PERSON, {"documentId": documentId}).mappings().first()
    if row is None:
        raise PersonNotFound(documentId)
    return PersonResponse.fromRow(row)


def getPersonPhoto(session: Session, documentId: str) -> tuple[bytes, str]:
    row = session.execute(_SELECT_PHOTO, {"documentId": documentId}).mappings().first()
    if row is None:
        raise PersonNotFound(documentId)
    rawMap = {str(k).lower(): v for k, v in dict(row).items()}
    photo = rawMap.get("photo")
    if photo is None:
        raise PhotoNotFound(documentId)
    photoType = str(rawMap.get("phototype") or "image/jpeg")
    return bytes(photo), photoType

