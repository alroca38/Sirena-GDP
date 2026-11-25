# REPOSITORY.PY - ms-create
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from gdp_common.db import isUniquenessViolation
from gdp_common.errors import DuplicatedDocument
from gdp_common.schemas import COLUMNS_PERSON, PersonResponse

_INSERT_PERSON = text(
    f"""
    INSERT INTO person (
        documentType, documentId, firstName, secondName,
        lastNames, birthdate, genre, email, phoneNumber,
        photo, photoType
    )
    VALUES (
        :documentType, :documentId, :firstName, :secondName,
        :lastNames, :birthdate, :genre, :email, :phoneNumber,
        :photo, :photoType
    )
    RETURNING {COLUMNS_PERSON}
    """
)


def insertPerson(
    session: Session,
    data: dict[str, Any],
    photo: bytes | None = None,
    photoType: str | None = None,
) -> PersonResponse:
    params = {
        "documentType": data["documentType"],
        "documentId": data["documentId"],
        "firstName": data["firstName"],
        "secondName": data.get("secondName"),
        "lastNames": data["lastNames"],
        "birthdate": data["birthdate"],
        "genre": data["genre"],
        "email": data["email"],
        "phoneNumber": data["phoneNumber"],
        "photo": photo,
        "photoType": photoType,
    }
    try:
        row = session.execute(_INSERT_PERSON, params).mappings().one()
    except DBAPIError as exc:
        if isUniquenessViolation(exc):
            raise DuplicatedDocument(str(data["documentId"])) from exc
        raise
    return PersonResponse.fromRow(row)

