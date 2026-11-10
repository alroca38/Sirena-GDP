# REPOSITORY.PY - ms-delete
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from gdp_common.errors import PersonNotFound
from gdp_common.schemas import COLUMNS_PERSON, PersonResponse

_SELECT_PERSON = text(
    f"""
    SELECT {COLUMNS_PERSON}
    FROM person
    WHERE documentId = :documentId
    """
)

_DELETE_PERSON = text(
    """
    DELETE FROM person
    WHERE documentId = :documentId
    RETURNING documentType, documentId
    """
)


def getPersonByDocument(session: Session, documentId: str) -> PersonResponse:
    row = session.execute(_SELECT_PERSON, {"documentId": documentId}).mappings().first()
    if row is None:
        raise PersonNotFound(documentId)
    return PersonResponse.fromRow(row)


def deletePersonByDocument(session: Session, documentId: str) -> tuple[str, str]:
    row = session.execute(_DELETE_PERSON, {"documentId": documentId}).mappings().first()
    if row is None:
        raise PersonNotFound(documentId)
    rawMap = {str(k).lower(): v for k, v in dict(row).items()}
    return str(rawMap["documenttype"]), str(rawMap["documentid"])

