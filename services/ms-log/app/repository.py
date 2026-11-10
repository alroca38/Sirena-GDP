# REPOSITORY.PY - ms-log
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from gdp_common.schemas import TransactionLogItem, TransactionLogPage


def queryTransactions(
    session: Session,
    *,
    txType: str | None = None,
    result: str | None = None,
    documentType: str | None = None,
    documentId: str | None = None,
    fromDt: datetime | None = None,
    toDt: datetime | None = None,
    page: int = 1,
    pageSize: int = 50,
) -> TransactionLogPage:
    conditions: list[str] = []
    params: dict[str, Any] = {}

    if txType:
        conditions.append("CAST(type AS TEXT) = :txType")
        params["txType"] = txType
    if result:
        conditions.append("CAST(result AS TEXT) = :result")
        params["result"] = result
    if documentType:
        conditions.append("documentType = :documentType")
        params["documentType"] = documentType
    if documentId:
        conditions.append("documentId = :documentId")
        params["documentId"] = documentId
    if fromDt is not None:
        conditions.append("timestamp >= :fromDt")
        params["fromDt"] = fromDt
    if toDt is not None:
        conditions.append("timestamp <= :toDt")
        params["toDt"] = toDt

    whereClause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    countSql = text(f"SELECT COUNT(*) FROM log_transaction {whereClause}")
    total = int(session.execute(countSql, params).scalar_one())

    offset = (page - 1) * pageSize
    params["limit"] = pageSize
    params["offset"] = offset

    selectSql = text(
        f"""
        SELECT id, timestamp, CAST(type AS TEXT) AS type, CAST(result AS TEXT) AS result,
               documentType, documentId, "user", question, answer
        FROM log_transaction
        {whereClause}
        ORDER BY timestamp DESC, id DESC
        LIMIT :limit OFFSET :offset
        """
    )

    rows = session.execute(selectSql, params).mappings().all()
    items = [TransactionLogItem.fromRow(r) for r in rows]

    return TransactionLogPage(
        items=items,
        total=total,
        page=page,
        pageSize=pageSize,
    )

