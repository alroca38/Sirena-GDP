# SERVICE.PY - ms-create
from __future__ import annotations

from gdp_common.errors import errorFromPhoto
from gdp_common.log_tx import TransactionType, auditedOperation
from gdp_common.n8n_client import notifyPersonUpsert
from gdp_common.schemas import CreatePerson, PersonResponse
from gdp_common.validators import detectPhotoType, validatePhoto

from . import repository


def createPerson(
    form: CreatePerson,
    photoBytes: bytes | None,
    user: str,
) -> PersonResponse:
    with auditedOperation(
        TransactionType.CREATE,
        user=user,
        documentType=form.documentType,
        documentId=form.documentId,
    ) as op:
        data = form.validateData()
        op.documentType = data["documentType"]
        op.documentId = data["documentId"]

        photoError = validatePhoto(photoBytes)
        if photoError is not None:
            raise errorFromPhoto(photoError)

        photoType = detectPhotoType(photoBytes) if photoBytes is not None else None
        person = repository.insertPerson(op.session, data, photoBytes, photoType)

    notifyPersonUpsert(person)
    return person

