# ROUTES.PY - ms-log
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from gdp_common.auth import getCurrentUser
from gdp_common.schemas import TransactionLogPage

from . import service

router = APIRouter()


@router.get(
    "/api/log/health",
    tags=["Health"],
    summary="Estado del microservicio ms-log",
)
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ms-log"}


@router.get(
    "/api/log/v1/transactions",
    response_model=TransactionLogPage,
    tags=["Consultar Log"],
    summary="Consulta del log de transacciones con filtros combinables y paginación (RF-07)",
)
def getTransactionsEndpoint(
    type: str | None = Query(
        None,
        description="Tipo de transacción: CREAR, MODIFICAR, CONSULTAR, BORRAR, CONSULTA_LN, CONSULTA_LOG",
    ),
    result: str | None = Query(
        None,
        description="Resultado de la transacción: EXITO, RECHAZADA, ERROR",
    ),
    documentType: str | None = Query(
        None,
        description="Tipo de documento: TI o CC",
    ),
    documentId: str | None = Query(
        None,
        description="Número de documento (1-10 dígitos)",
    ),
    fromDate: str | None = Query(
        None,
        alias="from",
        description="Fecha inicial de transacción en hora de Bogotá (YYYY-MM-DD o dd-mmm-yyyy)",
    ),
    toDate: str | None = Query(
        None,
        alias="to",
        description="Fecha final de transacción en hora de Bogotá (YYYY-MM-DD o dd-mmm-yyyy)",
    ),
    page: int = Query(1, description="Página actual (>= 1)"),
    pageSize: int = Query(50, description="Registros por página (1-200)"),
    user: str = Depends(getCurrentUser),
) -> TransactionLogPage:
    return service.listTransactions(
        user=user,
        txType=type,
        result=result,
        documentType=documentType,
        documentId=documentId,
        fromDate=fromDate,
        toDate=toDate,
        page=page,
        pageSize=pageSize,
    )

