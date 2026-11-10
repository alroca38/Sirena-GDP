# N8N_CLIENT.PY
# Llamada al webhook de n8n
from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

import httpx

from gdp_common.config import getSettings
from gdp_common.schemas import PersonResponse

log = logging.getLogger("gdp.n8n_client")

__all__ = [
    "formatDateUi",
    "calculateAge",
    "buildPersonIndexContent",
    "notifyPersonUpsert",
    "notifyPersonDelete",
]

_BOGOTA_TZ = timezone(timedelta(hours=-5))

_ABRV_MONTHS = (
    "ene", "feb", "mar", "abr", "may", "jun",
    "jul", "ago", "sep", "oct", "nov", "dic"
)

_GENRE_LABELS = {
    "MASCULINO": "Masculino",
    "FEMENINO": "Femenino",
    "NO_BINARIO": "No binario",
    "PREFIERO_NO_REPORTAR": "Prefiero no reportar",
}


def _toDate(value: date | str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def formatDateUi(value: date | str) -> str:
    d = _toDate(value)
    monthName = _ABRV_MONTHS[d.month - 1]
    return f"{d.day:02d}-{monthName}-{d.year:04d}"


def calculateAge(birthdate: date | str, today: date | None = None) -> int:
    b = _toDate(birthdate)
    t = today or datetime.now(_BOGOTA_TZ).date()
    age = t.year - b.year - ((t.month, t.day) < (b.month, b.day))
    return max(0, age)


def buildPersonIndexContent(person: PersonResponse | Mapping[str, Any]) -> str:
    data = person.model_dump() if isinstance(person, PersonResponse) else dict(person)
    parts = [
        str(data.get("firstName") or "").strip(),
        str(data.get("secondName") or "").strip(),
        str(data.get("lastNames") or "").strip(),
    ]
    fullName = " ".join(p for p in parts if p)
    docType = str(data.get("documentType") or "").strip()
    docId = str(data.get("documentId") or "").strip()
    bdate = data.get("birthdate")
    bdateUi = formatDateUi(bdate) if bdate else ""
    age = calculateAge(bdate) if bdate else 0
    genreCode = str(data.get("genre") or "").strip()
    genreLabel = _GENRE_LABELS.get(genreCode, genreCode)

    return (
        f"Persona: {fullName}. Documento: {docType} {docId}.\n"
        f"Fecha de nacimiento: {bdateUi} ({age} años). Género: {genreLabel}."
    )


def _postWebhook(payload: dict[str, Any]) -> bool:
    settings = getSettings()
    url = settings.n8nWebhookUrl
    if not url:
        return False
    try:
        response = httpx.post(url, json=payload, timeout=settings.n8nTimeoutSeconds)
        if response.status_code >= 400:
            log.warning(
                "Webhook person-sync respondió con estado %s: %s",
                response.status_code,
                response.text[:200],
            )
            return False
        return True
    except Exception:
        log.warning("No fue posible notificar al webhook person-sync de n8n (%s)", url, exc_info=True)
        return False


def notifyPersonUpsert(person: PersonResponse | Mapping[str, Any]) -> bool:
    data = person.model_dump() if isinstance(person, PersonResponse) else dict(person)
    bdate = data.get("birthdate")
    bdateIso = _toDate(bdate).isoformat() if bdate else None
    content = buildPersonIndexContent(data)
    docId = str(data.get("documentId") or "")
    docType = str(data.get("documentType") or "")

    payload: dict[str, Any] = {
        "action": "upsert",
        "documentId": docId,
        "documentType": docType,
        "firstName": data.get("firstName"),
        "secondName": data.get("secondName"),
        "lastNames": data.get("lastNames"),
        "birthdate": bdateIso,
        "genre": data.get("genre"),
        "content": content,
        "metadata": {
            "documentId": docId,
            "numero_documento": docId,
            "documentType": docType,
        },
    }
    return _postWebhook(payload)


def notifyPersonDelete(documentId: str, documentType: str | None = None) -> bool:
    payload: dict[str, Any] = {
        "action": "delete",
        "documentId": documentId,
        "documentType": documentType,
        "metadata": {
            "documentId": documentId,
            "numero_documento": documentId,
        },
    }
    return _postWebhook(payload)
