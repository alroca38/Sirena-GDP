# LOG_TX.PY
from __future__ import annotations
 
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any
 
from sqlalchemy import text
from sqlalchemy.orm import Session
 
from gdp_common.db import getSessionFactory
from gdp_common.errors import ErrorGDP, InternalError

log = logging.getLogger("gdp.log_tx")

__all__ = [
    "TransactionType", "TransactionResult", "Operation",
    "registerLog", "registerLogIndependent", "auditedOperation"
]

class TransactionType(str, Enum):
    CREATE = "CREAR"
    MODIFY = "MODIFICAR"
    CONSULT = "CONSULTAR"
    DELETE = "BORRAR"
    QUERY_LN = "CONSULTA_LN"
    QUERY_LOG = "CONSULTA_LOG"

class TransactionResult(str, Enum):
    SUCCESS = "EXITO"
    REJECTED = "RECHAZADO"
    ERROR = "ERROR"

_MAX_DOCUMENT = 64
_MAX_USER = 256
_MAX_TEXT = 10_000

_INSERT = text(
    """
    INSERT INTO log_transaction
        (timestamp, type, result, documentType, documentId,
         user, question, answer)
    VALUES
        (clock_timestamp(), :type, :result, :documentType, :documentId,
         :user, :question, :answer)
    RETURNING id
    """
)

def _clean(value: Any, max: int) -> str | None:
    if value is None:
        return None
    text = str(value).replace("\x00", "")
    text = text.encode("utf-8", "replace").decode("utf-8")
    return text[:max]

def registerLog(
    session: Session,
    type: TransactionType | str,
    result: TransactionResult | str,
    *,
    documentType: str | None = None,
    documentId: str | None = None,
    user: str | None = None,
    question: str | None = None,
    answer: str | None = None
) -> int:
    row = session.execute(
        _INSERT,
        {
            "type": TransactionType(type).value,
            "result": TransactionResult(result).value,
            "documentType": _clean(documentType, _MAX_DOCUMENT),
            "documentId": _clean(documentId, _MAX_DOCUMENT),
            "user": _clean(user, _MAX_USER),
            "question": _clean(question, _MAX_TEXT),
            "answer": _clean(answer, _MAX_TEXT)
        }
    ).scalar_one()
    return int(row)

def registerLogIndependent(
    type: TransactionType | str,
    result: TransactionResult | str,
    **fields: Any
) -> int | None:
    try:
        with getSessionFactory()() as session:
            id_ = registerLog(session, type, result, **fields)
            session.commit()
            return id_
    except Exception:
        log.exception("No se pudo escribir el registro de log (%s / %s)", type, result)
        return None

@dataclass
class Operation:
    session: Session
    type: TransactionType
    user: str | None = None
    documentType: str | None = None
    documentId: str | None = None
    question: str | None = None
    answer: str | None = None

    def _fields(self) -> dict[str, Any]:
        return {
            "documentType": self.documentType,
            "documentId": self.documentId,
            "user": self.user,
            "question": self.question,
            "answer": self.answer
        }

def _revert(session: Session) -> None:
    try:
        session.rollback()
    except Exception:
        log.exception("Falló el rollback de la transacción")

@contextmanager
def auditedOperation(
    type: TransactionType | str,
    *,
    user: str | None = None,
    documentType: str | None = None,
    documentId: str | None = None,
    question: str | None = None,
    answer: str | None = None
) -> Iterator[Operation]:
    type = TransactionType(type)
    session = getSessionFactory()()
    op = Operation(
        session=session,
        type=type,
        user=user,
        documentType=documentType,
        documentId=documentId,
        question=question,
        answer=answer
    )
    try:
        yield op
        registerLog(session, op.type, TransactionResult.SUCCESS, **op._fields())
        session.commit()
    except ErrorGDP as exc:
        _revert(session)
        id_ = registerLogIndependent(
            op.type, TransactionResult(exc.logResult), **op._fields()
        )
        exc.registered = id_ is not None
        raise
    except Exception as exc:
        _revert(session)
        log.exception("Error inesperado en la operación %s", op.type.value)
        id_ = registerLogIndependent(op.type, TransactionResult.ERROR, **op._fields())
        internal = InternalError()
        internal.registered = id_ is not None
        raise internal from exc
    except BaseException:
        _revert(session)
        raise
    finally:
        session.close()