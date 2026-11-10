# MAIN.PY - ms-modify
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from gdp_common.auth import tryGetCurrentUser
from gdp_common.errors import ErrorGDP, NotAuthenticated, registerHandlers
from gdp_common.log_tx import TransactionResult, TransactionType, registerLogIndependent

from .routes import router

app = FastAPI(
    title="Sirena GDP - ms-modify",
    description="Microservicio de modificación de datos personales (RF-03)",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/api/modify/docs",
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
    # Solo la operación PUT /api/modify/v1/person/{doc} genera registro propio de auditoría
    if request.method.upper() != "PUT" or not request.url.path.startswith("/api/modify/v1/person/"):
        return
    docId = request.path_params.get("doc")
    user = tryGetCurrentUser(request)
    registerLogIndependent(
        TransactionType.MODIFY,
        TransactionResult(err.logResult),
        documentId=docId,
        user=user,
    )


registerHandlers(app, toError=_onUnhandledError)
app.include_router(router)


@app.get("/api/modify/openapi.json", include_in_schema=False)
def openapiAlias() -> dict[str, Any]:
    return app.openapi()

