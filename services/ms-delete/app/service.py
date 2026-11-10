# SERVICE.PY - ms-delete
from __future__ import annotations

from gdp_common.db import getSessionFactory
from gdp_common.errors import ValidationError
from gdp_common.log_tx import TransactionType, auditedOperation
from gdp_common.n8n_client import notifyPersonDelete
from gdp_common.schemas import PersonResponse
from gdp_common.validators import validateField

from . import repository


def preloadPerson(documentId: str) -> PersonResponse:
    docClean = (documentId or "").strip()
    err = validateField("documentId", docClean)
    if err:
        raise ValidationError({"documentId": err})

    with getSessionFactory()() as session:
        return repository.getPersonByDocument(session, docClean)


def deletePerson(documentId: str, user: str) -> None:
    docClean = (documentId or "").strip()
    docType: str | None = None
    with auditedOperation(
        TransactionType.DELETE,
        user=user,
        documentId=docClean,
    ) as op:
        err = validateField("documentId", docClean)
        if err:
            raise ValidationError({"documentId": err})

        docType, deletedDocId = repository.deletePersonByDocument(op.session, docClean)
        op.documentType = docType
        op.documentId = deletedDocId

    notifyPersonDelete(docClean, docType)

