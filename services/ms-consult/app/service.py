# SERVICE.PY - ms-consult
from __future__ import annotations

from gdp_common.db import getSessionFactory
from gdp_common.errors import ValidationError
from gdp_common.log_tx import TransactionType, auditedOperation
from gdp_common.schemas import PersonResponse
from gdp_common.validators import validateField

from . import repository


def consultPerson(documentId: str, user: str) -> PersonResponse:
    docClean = (documentId or "").strip()
    with auditedOperation(
        TransactionType.CONSULT,
        user=user,
        documentId=docClean,
    ) as op:
        err = validateField("documentId", docClean)
        if err:
            raise ValidationError({"documentId": err})

        person = repository.getPersonByDocument(op.session, docClean)
        op.documentType = person.documentType
        op.documentId = person.documentId
        return person


def consultPersonPhoto(documentId: str) -> tuple[bytes, str]:
    docClean = (documentId or "").strip()
    err = validateField("documentId", docClean)
    if err:
        raise ValidationError({"documentId": err})

    with getSessionFactory()() as session:
        return repository.getPersonPhoto(session, docClean)

