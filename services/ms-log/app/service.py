# SERVICE.PY - ms-log
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from gdp_common.errors import ValidationError
from gdp_common.log_tx import TransactionResult, TransactionType, auditedOperation
from gdp_common.schemas import TransactionLogPage
from gdp_common.validators import loadSpec, validateField

from . import repository

_BOGOTA_TZ = timezone(timedelta(hours=-5))
_VALID_TYPES = {t.value for t in TransactionType}
_VALID_RESULTS = {r.value for r in TransactionResult}


def _parseFilterDate(raw: str, *, endOfDay: bool) -> datetime | None:
    text = raw.strip().lower()
    if not text:
        return None

    parsedDate: date | None = None
    spec = loadSpec()

    # 1. YYYY-MM-DD
    if spec.patterns["isoDate"].fullmatch(text):
        try:
            y, m, d = (int(p) for p in text.split("-"))
            parsedDate = date(y, m, d)
        except ValueError:
            return None
    # 2. dd-mmm-yyyy
    elif spec.patterns["textDate"].fullmatch(text):
        try:
            dStr, mStr, yStr = text.split("-")
            parsedDate = date(int(yStr), spec.months[mStr], int(dStr))
        except ValueError:
            return None
    # 3. dd/mm/yyyy
    elif "/" in text and len(text.split("/")) == 3:
        try:
            dStr, mStr, yStr = text.split("/")
            parsedDate = date(int(yStr), int(mStr), int(dStr))
        except ValueError:
            return None
    else:
        # 4. ISO datetime completo
        try:
            dt = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=_BOGOTA_TZ)
            return dt
        except ValueError:
            return None

    t = time(23, 59, 59, 999999) if endOfDay else time(0, 0, 0)
    return datetime.combine(parsedDate, t, tzinfo=_BOGOTA_TZ)


def listTransactions(
    *,
    user: str,
    txType: str | None = None,
    result: str | None = None,
    documentType: str | None = None,
    documentId: str | None = None,
    fromDate: str | None = None,
    toDate: str | None = None,
    page: int = 1,
    pageSize: int = 50,
) -> TransactionLogPage:
    cleanType = (txType or "").strip().upper() or None
    cleanResult = (result or "").strip().upper() or None
    cleanDocType = (documentType or "").strip().upper() or None
    cleanDocId = (documentId or "").strip() or None
    cleanFrom = (fromDate or "").strip() or None
    cleanTo = (toDate or "").strip() or None

    with auditedOperation(
        TransactionType.QUERY_LOG,
        user=user,
        documentType=cleanDocType,
        documentId=cleanDocId,
    ) as op:
        errors: dict[str, str] = {}

        if cleanType and cleanType not in _VALID_TYPES:
            errors["type"] = (
                f"Tipo de transacción inválido. Valores permitidos: {', '.join(sorted(_VALID_TYPES))}."
            )

        if cleanResult and cleanResult not in _VALID_RESULTS:
            errors["result"] = (
                f"Resultado inválido. Valores permitidos: {', '.join(sorted(_VALID_RESULTS))}."
            )

        if cleanDocType:
            docTypeErr = validateField("documentType", cleanDocType)
            if docTypeErr:
                errors["documentType"] = docTypeErr

        if cleanDocId:
            docIdErr = validateField("documentId", cleanDocId)
            if docIdErr:
                errors["documentId"] = docIdErr

        fromDt: datetime | None = None
        toDt: datetime | None = None

        if cleanFrom:
            fromDt = _parseFilterDate(cleanFrom, endOfDay=False)
            if fromDt is None:
                errors["from"] = "Formato de fecha inicial inválido. Use YYYY-MM-DD o dd-mmm-yyyy."

        if cleanTo:
            toDt = _parseFilterDate(cleanTo, endOfDay=True)
            if toDt is None:
                errors["to"] = "Formato de fecha final inválido. Use YYYY-MM-DD o dd-mmm-yyyy."

        if fromDt is not None and toDt is not None and fromDt > toDt:
            errors["from"] = "La fecha inicial ('from') no puede ser posterior a la fecha final ('to')."

        if page < 1:
            errors["page"] = "El número de página debe ser mayor o igual a 1."
        if pageSize < 1 or pageSize > 200:
            errors["pageSize"] = "El tamaño de página debe estar entre 1 y 200."

        if errors:
            raise ValidationError(errors)

        return repository.queryTransactions(
            op.session,
            txType=cleanType,
            result=cleanResult,
            documentType=cleanDocType,
            documentId=cleanDocId,
            fromDt=fromDt,
            toDt=toDt,
            page=page,
            pageSize=pageSize,
        )

