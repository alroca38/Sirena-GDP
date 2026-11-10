# MAIN.PY - ms-create
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from gdp_common.auth import tryGetCurrentUser
from gdp_common.errors import ErrorGDP, NotAuthenticated, registerHandlers
from gdp_common.log_tx import TransactionResult, TransactionType, registerLogIndependent

from .routes import router

app = FastAPI(
    title="Sirena GDP - ms-create",
    description="Microservicio de creación de personas (RF-02)",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/api/create/docs",
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
    if not request.url.path.startswith("/api/create/v1/person"):
        return
    user = tryGetCurrentUser(request)
    registerLogIndependent(
        TransactionType.CREATE,
        TransactionResult(err.logResult),
        user=user,
    )


registerHandlers(app, toError=_onUnhandledError)
app.include_router(router)


@app.get("/api/create/openapi.json", include_in_schema=False)
def openapiAlias() -> dict[str, Any]:
    return app.openapi()

