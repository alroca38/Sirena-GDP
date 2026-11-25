#!/bin/sh
set -eu

if [ -f /home/node/.n8n/config ]; then
  EXISTING_KEY=$(node -e "try{const c=require('/home/node/.n8n/config');if(c.encryptionKey)process.stdout.write(String(c.encryptionKey));}catch(e){}" 2>/dev/null || true)
  if [ -n "$EXISTING_KEY" ] && [ "${N8N_ENCRYPTION_KEY:-}" != "$EXISTING_KEY" ]; then
    echo "[sirena-n8n] Sincronizando N8N_ENCRYPTION_KEY con la clave existente en /home/node/.n8n/config..."
    export N8N_ENCRYPTION_KEY="$EXISTING_KEY"
  fi
fi

if [ "${N8N_AUTO_PROVISION:-true}" = "true" ]; then
  CRED_FILE="/tmp/sirena-postgres-cred.json"
  cat > "$CRED_FILE" <<EOF
[
  {
    "id": "SirenaPostgres01",
    "name": "Sirena PostgreSQL",
    "type": "postgres",
    "data": {
      "host": "${POSTGRES_HOST:-postgres}",
      "database": "${POSTGRES_DB:-sirena}",
      "user": "${POSTGRES_USER:-postgres}",
      "password": "${POSTGRES_PASSWORD:-postgres}",
      "port": ${POSTGRES_PORT:-5432},
      "ssl": "disable"
    }
  }
]
EOF

  echo "[sirena-n8n] Importando credencial PostgreSQL..."
  n8n import:credentials --input="$CRED_FILE"
  rm -f "$CRED_FILE"

  echo "[sirena-n8n] Importando flujos de trabajo..."
  n8n import:workflow --separate --input=/opt/sirena-n8n/workflows

  echo "[sirena-n8n] Activando flujos webhook y chat RAG..."
  n8n update:workflow --id=SirenaPersonSync --active=true
  n8n update:workflow --id=SirenaChatRag001 --active=true

  echo "[sirena-n8n] Ejecutando indexación inicial (SirenaReindexAll)..."
  n8n execute --id=SirenaReindexAll || echo "[sirena-n8n] Advertencia: la reindexación inicial no pudo completarse en el arranque."
fi

exec n8n start
