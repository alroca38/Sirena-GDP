# MAIN.PY - ms-auth
from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from gdp_common.errors import registerHandlers

from .routes import router

# Sin CORS: el navegador solo llega a este servicio por el Nginx del frontend (mismo origen).
app = FastAPI(
    title="Sirena GDP - ms-auth",
    description="Inicio y cierre de sesión con Roble (RF-01)",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/api/auth/docs",
)

registerHandlers(app)
app.include_router(router)


@app.get("/api/auth/openapi.json", include_in_schema=False)
def openapiAlias() -> dict[str, Any]:
    return app.openapi()
