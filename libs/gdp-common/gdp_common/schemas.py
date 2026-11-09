# SCHEMAS.PY
from __future__ import annotations
 
from collections.abc import Mapping
from datetime import date
from typing import Any, Literal
 
from pydantic import BaseModel, ConfigDict, Field

from gdp_common.errors import ValidationError
from gdp_common.validators import validatePerson

__all__ = [
    "FIELDS_PERSON", "COLUMNS_PERSON",
    "CreatePerson", "ModifyPerson", "PersonResponse", "PhotoAction"
]

FIELDS_PERSON = (
    "documentType", "documentId", "firstName", "secondName",
    "lastNames", "birthdate", "genre", "email", "phoneNumber"
)

COLUMNS_PERSON = (
    "documentType, documentId, firstName, secondName, lastNames, "
    "birthdate, genre, email, phoneNumber, (photo IS NOT NULL) AS hasPhoto"
)

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
        return cls.model_validate(dict(row))