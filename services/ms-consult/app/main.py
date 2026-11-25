# MAIN.PY - ms-consult
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from gdp_common.auth import tryGetCurrentUser
from gdp_common.errors import ErrorGDP, NotAuthenticated, registerHandlers
from gdp_common.log_tx import TransactionResult, TransactionType, registerLogIndependent

from .routes import router

app = FastAPI(
    title="Sirena GDP - ms-consult",
    description="Microservicio de consulta de datos personales (RF-04, RNF-03)",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/api/consult/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _onUnhandledError(request: Request, err: ErrorGDP) -> None:
    if isinstance(err, NotAuthenticated):
        return
    path = request.url.path
    if not path.startswith("/api/consult/v1/person/") or path.endswith("/pic"):
        return
    docId = request.path_params.get("doc")
    user = tryGetCurrentUser(request)
    registerLogIndependent(
        TransactionType.CONSULT,
        TransactionResult(err.logResult),
        documentId=docId,
        user=user,
    )


registerHandlers(app, toError=_onUnhandledError)
app.include_router(router)


@app.get("/api/consult/openapi.json", include_in_schema=False)
def openapiAlias() -> dict[str, Any]:
    return app.openapi()

