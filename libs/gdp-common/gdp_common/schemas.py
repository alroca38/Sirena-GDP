# SCHEMAS.PY
from __future__ import annotations
 
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any, Literal
 
from pydantic import BaseModel, ConfigDict, Field

from gdp_common.errors import ValidationError
from gdp_common.validators import validatePerson

__all__ = [
    "FIELDS_PERSON", "COLUMNS_PERSON",
    "CreatePerson", "ModifyPerson", "PersonResponse", "PhotoAction",
    "TransactionLogItem", "TransactionLogPage"
]

FIELDS_PERSON = (
    "documentType", "documentId", "firstName", "secondName",
    "lastNames", "birthdate", "genre", "email", "phoneNumber"
)

COLUMNS_PERSON = (
    "documentType, documentId, firstName, secondName, lastNames, "
    "birthdate, genre, email, phoneNumber, (photo IS NOT NULL) AS hasPhoto"
)

_PERSON_ROW_MAP = {k.lower(): k for k in (*FIELDS_PERSON, "hasPhoto")}
_LOG_ROW_MAP = {
    k.lower(): k
    for k in (
        "id", "timestamp", "type", "result",
        "documentType", "documentId", "user", "question", "answer"
    )
}

PhotoAction = Literal["conserve", "replace", "remove"]

def _validateOrLaunch(data: Mapping[str, Any]) -> dict[str, Any]:
    result = validatePerson(data)
    if not result.isValid:
        raise ValidationError.fromValidationResult(result)
    return result.data

# INPUT

class _PersonData(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True, extra="ignore")
    documentType: str | None = Field(
        None, description="Código del tipo de documento: TI (Tarjeta de identidad) o CC (Cédula).",
        examples=["CC"]
    )
    firstName: str | None = Field(
        None, description="Máximo 30 caracteres, sin números.",
        examples=["Pedro"]
    )
    secondName: str | None = Field(
        None, description="Opcional. Máximo 30 caracteres, sin números.",
        examples=["Andrés"]
    )
    lastNames: str | None = Field(
        None, description="Máximo 60 caracteres, sin números.",
        examples=["Pérez Gómez"]
    )
    birthdate: str | None = Field(
        None, description="'YYYY-MM-DD' (calendario) o 'dd-mmm-yyyy' (12-mar-2001).",
        examples=["2001-03-12"]
    )
    genre: str | None = Field(
        None, description="MASCULINO, FEMENINO, NO_BINARIO, PREFIERO_NO_REPORTAR.",
        examples=["MASCULINO"]
    )
    email: str | None = Field(
        None, description="Correo electrónico.",
        examples=["pedro@correo.com"]
    )
    phoneNumber: str | None = Field(
        None, description="Exactamente 10 dígitos.",
        examples=["3001234567"]
    )

class CreatePerson(_PersonData):
    documentId: str | None = Field(
        None, description="Solo dígitos, máximo 10. Es la llave de búsqueda",
        examples=["1045678901"]
    )

    def validateData(self) -> dict[str, Any]:
        return _validateOrLaunch(self.model_dump())

class ModifyPerson(_PersonData):
    removePhoto: bool = Field(
        False, description="Si es 'true' y no se envía una foto nueva, elimina la foto actual."
    )

    def validateData(self, documentId: str) -> dict[str, Any]:
        data = self.model_dump(exclude={"removePhoto"})
        data["documentId"] = documentId
        return _validateOrLaunch(data)

    def photoAction(self, aNewPhoto: bool) -> PhotoAction:
        if aNewPhoto and self.removePhoto:
            raise ValidationError({"photo": "Envíe una foto nueva o pida quitarla, pero no ambas cosas."})
        if aNewPhoto:
            return "replace"
        return "remove" if self.removePhoto else "conserve"

# OUTPUT

class PersonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    documentType: str
    documentId: str
    firstName: str
    secondName: str | None = None
    lastNames: str
    birthdate: date
    genre: str
    email: str
    phoneNumber: str
    hasPhoto: bool = False

    @classmethod
    def fromRow(cls, row: Mapping[str, Any]) -> PersonResponse:
        normalized = {
            _PERSON_ROW_MAP.get(str(k).lower(), str(k)): (
                v.strip() if str(k).lower() == "phonenumber" and isinstance(v, str) else v
            )
            for k, v in dict(row).items()
        }
        return cls.model_validate(normalized)

class TransactionLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    type: str
    result: str
    documentType: str | None = None
    documentId: str | None = None
    user: str | None = None
    question: str | None = None
    answer: str | None = None

    @classmethod
    def fromRow(cls, row: Mapping[str, Any]) -> TransactionLogItem:
        normalized = {
            _LOG_ROW_MAP.get(str(k).lower(), str(k)): v
            for k, v in dict(row).items()
        }
        return cls.model_validate(normalized)

class TransactionLogPage(BaseModel):
    items: list[TransactionLogItem]
    total: int
    page: int
    pageSize: int