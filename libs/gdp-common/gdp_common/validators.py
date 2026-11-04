# VALIDATORS.PY
# Validación de campos de entrada (Tipo de documento, Nro. de documento, Primer nombre, etc.)

from __future__ import annotations

import json
import os
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

################################################################
ENV_SPEC = "GDP_VALIDATION_SPEC"
################################################################

_BOGOTA_TZ = timezone(timedelta(hours=-5))

_KNOWN_RULES = {
    "required", "maxLength", "exactLength", "pattern", "enum",
    "dateFormat", "realDate", "noFutureDate", "minDate", "maxSize",
    "realFileType"
}

# Carga de especificaciones de validación desde el archivo JSON

@dataclasss(frozen=True)
class _Spec:
    raw: dict[str, Any]
    patterns: dict[str, re.Pattern[str]]
    months: dict[str, int]

    @property
    def fields(self) -> dict[str, Any]:
        return self.raw["fields"]

def _findRoute(route: str | os.PathLike[str] | None) -> Path:
    candidates = []
    if route:
        candidates.append(Path(route))
    elif os.environ.get(ENV_SPEC):
        candidates.append(Path(os.environ[ENV_SPEC]))
    else:
        candidates.append(Path("/app/shared/validation_spec.json"))
        candidates.append(Path(__file__).resolve().parents[3] / "shared" / "validation_spec.json")
    for c in candidates:
        if c.is_file():
            return c
    raise FileNotFoundError(f"Validation spec file not found in any of the following locations: {candidates}")

@lru_cache(maxsize=None)
def loadSpec(route: str | None = None) -> _Spec:
    raw = json.loads(_findRoute(route).read_text(encoding="utf-8"))

    patterns = {n: re.compile(p) for n, p in raw["patterns"].items()}
    months = {m: i + 1 for i, m in enumerate(raw["abrvMonths"])}

    for name, field in raw["fields"].items():
        for rule in field["rules"]:
            if rule["id"] not in _KNOWN_RULES:
                raise ValueError(f"Unknown validation rule '{rule['id']}' for field '{name}'")
            if rule["id"] == "pattern" and rule["pattern"] not in patterns:
                raise ValueError(f"Unknown pattern '{rule['pattern']}' for field '{name}'")
        for f in field.get("inputFormats", []):
            if f["pattern"] not in patterns:
                raise ValueError(f"Unknown pattern '{f['pattern']}' for input format of field '{name}'")
    return _Spec(raw=raw, patterns=patterns, months=months)

# Utilidades de validación

def _toText(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        value = value.isoformat()
    if not isinstance(value, str):
        value = str(value)
    return unicodedata.normalize("NFC", value)

def _normalize(text: str, operations: list[str]) -> str:
    for op in operations:
        if op == "trim":
            text = text.strip()
        elif op == "collapseSpaces":
            text = re.sub(r" +", " ", text)
        elif op == "lowercase":
            text = text.lower()
    return text

def _message(rule: Mapping[str, Any], field: Mapping[str, Any]) -> str:
    return(
        rule["message"]
        .replace("{value}", str(rule.get("value", "")))
        .replace("{tag}", field["tag"])
    )

def _parseDate(spec: _Spec, field: Mapping[str, Any], text: str) -> tuple[str, date | None]:
    for fmt in field["inputFormats"]:
        if not spec.patterns[fmt["pattern"]].fullmatch(text):
            continue
        try:
            if fmt["id"] == "calendar":
                year, month, day = (int(p) for p in text.split("-"))
            else:
                d, m, a = text.split("-")
                year, month, day = int(a), spec.months[m], int(d)
            return "ok", date(year, month, day)
        except ValueError:
            return "real", None
    return "format", None

# Validación de campos individuales

def _evaluateField(spec: _Spec, name: str, value: Any, today: date) -> tuple[Any, str | None]:
    """
    Normaliza y valida un campo.
    Devuelve el valor normalizado y un mensaje de error (o None si es válido).
    """
    field = spec.fields[name]
    text = _normalize(_toText(value), field.get("normalization", []))

    if text == "":
        for rule in field["rules"]:
            if rule["id"] == "required":
                return None, _message(rule, field)
        return None, None

    date: date | None = None
    dateStatus = ""
    for rule in field["rules"]:
        rid = rule["id"]
        fail = False

        if rid == "required":
            pass
        elif rid == "maxLength":
            fail = len(text) > rule["value"]
        elif rid == "exactLength":
            fail = len(text) != rule["value"]
        elif rid == "pattern":
            fail = spec.patterns[rule["pattern"]].fullmatch(text) is None
        elif rid == "enum":
            fail = text not in {v["code"] for v in field["values"]}
        elif rid in ("dateFormat", "realDate", "noFutureDate", "minDate"):
            if not dateStatus:
                dateStatus, date = _parseDate(spec, field, text)
            if rid == "dateFormat":
                fail = dateStatus == "format"
            elif rid == "realDate":
                fail = dateStatus == "real"
            elif dateStatus != "ok":
                fail = True
            elif rid == "noFutureDate":
                fail = date > today
            else:
                fail = date < date.fromisoformat(rule["value"])

        if fail:
            return text, _message(rule, field)

    return (date if field["type"] == "date" else text), None

def _todayBogota() -> date:
    return datetime.now(_BOGOTA_TZ).date()

@dataclass(frozen=True)
class ValidationResult:
    data: dict[str, Any] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def isValid(self) -> bool:
        return not self.errors

def validatePerson(data: Mapping[str, Any], today: date | None = None, specRoute: str | None = None) -> ValidationResult:
    """
    Valida los campos de una persona según la especificación de validación.
    Devuelve un objeto ValidationResult con los datos normalizados y los errores encontrados.
    """
    spec = loadSpec(specRoute)
    today = today or _todayBogota()

    normalized_data: dict[str, Any] = {}
    errors: dict[str, str] = {}

    for name in spec.fields.items():
        if field["type"] == "file":
            continue  # Skip file fields for now
        value, error = _evaluateField(spec, name, data.get(name), today)
        if error:
            errors[name] = error
        else:
            normalized_data[name] = value

    return ValidationResult(data=normalized_data, errors=errors)

def validateField(name: str, value: Any, today: date | None = None, specRoute: str | None = None) -> str | None:
    """
    Valida un campo individual según la especificación de validación.
    Devuelve el valor normalizado y un mensaje de error (o None si es válido).
    """
    spec = loadSpec(specRoute)
    return _evaluateField(spec, name, value, today or _todayBogota())[1]

# Validación de archivos

@dataclass(frozen=True)
class PhotoError:
    status: int
    message: str

def detectPhotoType(content: bytes, *, specRoute: str | None = None) -> str | None:
    """
    Detecta el tipo de archivo de una foto a partir de su contenido.
    """
    for type in loadSpec(specRoute).fields["photo"]["typesAllowed"]:
        for signature in type["signature"]:
            if content.startswith(bytes.fromhex(signature)):
                return type["mime"]
    return None

def validatePhoto(content: bytes | None, *, specRoute: str | None = None) -> PhotoError | None:
    """
    Valida el contenido de una foto según la especificación de validación.
    Devuelve un objeto PhotoError si hay un error, o None si es válido.
    """
    if content is None:
        return None
    spec = loadSpec(specRoute)
    field = spec.fields["photo"]
    http = spec.raw["httpErrors"]

    for rule in field["rules"]:
        if rule["id"] == "maxSize" and len(content) > rule["value"]:
            return PhotoError(http["oversizedPhoto"], _message(rule, field))
        if rule["id"] == "realFileType" and detectPhotoType(content, specRoute=specRoute) is None:
            return PhotoError(http["invalidPhoto"], _message(rule, field))
    return None