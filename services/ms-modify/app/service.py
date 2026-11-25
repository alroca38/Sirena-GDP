# SERVICE.PY - ms-modify
from __future__ import annotations

from gdp_common.db import getSessionFactory
from gdp_common.errors import ValidationError, errorFromPhoto
from gdp_common.log_tx import TransactionType, auditedOperation
from gdp_common.n8n_client import notifyPersonUpsert
from gdp_common.schemas import ModifyPerson, PersonResponse
from gdp_common.validators import detectPhotoType, validateField, validatePhoto

from . import repository


def preloadPerson(documentId: str) -> PersonResponse:
    docClean = (documentId or "").strip()
    err = validateField("documentId", docClean)
    if err:
        raise ValidationError({"documentId": err})

    with getSessionFactory()() as session:
        return repository.getPersonByDocument(session, docClean)


def modifyPerson(
    documentId: str,
    form: ModifyPerson,
    photoBytes: bytes | None,
    user: str,
) -> PersonResponse:
    docClean = (documentId or "").strip()
    with auditedOperation(
        TransactionType.MODIFY,
        user=user,
        documentType=form.documentType,
        documentId=docClean,
    ) as op:
        data = form.validateData(docClean)
        op.documentType = data["documentType"]
        op.documentId = data["documentId"]

        action = form.photoAction(photoBytes is not None)
        photoType: str | None = None
        if action == "replace":
            photoError = validatePhoto(photoBytes)
            if photoError is not None:
                raise errorFromPhoto(photoError)
            photoType = detectPhotoType(photoBytes) if photoBytes is not None else None

        person = repository.updatePerson(
            op.session,
            data["documentId"],
            data,
            action,
            photoBytes,
            photoType,
        )

    notifyPersonUpsert(person)
    return person

