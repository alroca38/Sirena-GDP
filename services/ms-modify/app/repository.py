# REPOSITORY.PY - ms-modify
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from gdp_common.errors import PersonNotFound
from gdp_common.schemas import COLUMNS_PERSON, PersonResponse, PhotoAction

_SELECT_PERSON = text(
    f"""
    SELECT {COLUMNS_PERSON}
    FROM person
    WHERE documentId = :documentId
    """
)

_UPDATE_CONSERVE_PHOTO = text(
    f"""
    UPDATE person
    SET documentType = :documentType,
        firstName = :firstName,
        secondName = :secondName,
        lastNames = :lastNames,
        birthdate = :birthdate,
        genre = :genre,
        email = :email,
        phoneNumber = :phoneNumber
    WHERE documentId = :documentId
    RETURNING {COLUMNS_PERSON}
    """
)

_UPDATE_WITH_PHOTO = text(
    f"""
    UPDATE person
    SET documentType = :documentType,
        firstName = :firstName,
        secondName = :secondName,
        lastNames = :lastNames,
        birthdate = :birthdate,
        genre = :genre,
        email = :email,
        phoneNumber = :phoneNumber,
        photo = :photo,
        photoType = :photoType
    WHERE documentId = :documentId
    RETURNING {COLUMNS_PERSON}
    """
)


def getPersonByDocument(session: Session, documentId: str) -> PersonResponse:
    row = session.execute(_SELECT_PERSON, {"documentId": documentId}).mappings().first()
    if row is None:
        raise PersonNotFound(documentId)
    return PersonResponse.fromRow(row)


def updatePerson(
    session: Session,
    documentId: str,
    data: dict[str, Any],
    action: PhotoAction,
    photo: bytes | None = None,
    photoType: str | None = None,
) -> PersonResponse:
    params: dict[str, Any] = {
        "documentId": documentId,
        "documentType": data["documentType"],
        "firstName": data["firstName"],
        "secondName": data.get("secondName"),
        "lastNames": data["lastNames"],
        "birthdate": data["birthdate"],
        "genre": data["genre"],
        "email": data["email"],
        "phoneNumber": data["phoneNumber"],
    }

    if action == "conserve":
        row = session.execute(_UPDATE_CONSERVE_PHOTO, params).mappings().first()
    elif action == "replace":
        params["photo"] = photo
        params["photoType"] = photoType
        row = session.execute(_UPDATE_WITH_PHOTO, params).mappings().first()
    else:  # "remove"
        params["photo"] = None
        params["photoType"] = None
        row = session.execute(_UPDATE_WITH_PHOTO, params).mappings().first()

    if row is None:
        raise PersonNotFound(documentId)
    return PersonResponse.fromRow(row)

