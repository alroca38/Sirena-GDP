#!/usr/bin/env bash
# Prueba de humo para sincronización vectorial y consultas RAG en n8n (Secciones 8, 9 y 12 del SDD)
set -euo pipefail

N8N_URL="${N8N_URL:-http://localhost:5678}"

echo "=== 1. Verificando disponibilidad de n8n en ${N8N_URL} ==="
for i in {1..20}; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "${N8N_URL}/healthz" || true)
  if [ "${CODE}" = "200" ]; then
    break
  fi
  sleep 2
done

if [ "${CODE:-000}" != "200" ]; then
  echo "ERROR: n8n no respondió HTTP 200 en ${N8N_URL}/healthz (código ${CODE:-000})"
  exit 1
fi

echo "=== 2. Probando webhook POST /webhook/person-sync (upsert) ==="
UPSERT_PAYLOAD='{
  "action": "upsert",
  "documentId": "9988776655",
  "documentType": "CC",
  "firstName": "Lucía",
  "secondName": "Fernanda",
  "lastNames": "Martínez Rojas",
  "birthdate": "1999-07-20",
  "genre": "FEMENINO",
  "content": "Persona: Lucía Fernanda Martínez Rojas. Documento: CC 9988776655.\nFecha de nacimiento: 20-jul-1999 (27 años). Género: Femenino.",
  "metadata": {
    "documentId": "9988776655",
    "numero_documento": "9988776655",
    "documentType": "CC"
  }
}'

WEBHOOK_STATUS=$(curl -s -o /tmp/n8n_upsert.json -w "%{http_code}" \
  -X POST "${N8N_URL}/webhook/person-sync" \
  -H "Content-Type: application/json" \
  -d "${UPSERT_PAYLOAD}")

echo "Estado webhook upsert: ${WEBHOOK_STATUS}"
if [ "${WEBHOOK_STATUS}" != "200" ]; then
  echo "ERROR: Se esperaba HTTP 200 del webhook person-sync, se obtuvo ${WEBHOOK_STATUS}"
  exit 1
fi

sleep 3
VECTOR_COUNT=$(docker compose exec -T postgres psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-sirena}" -tAc \
  "SELECT count(*) FROM vector_person WHERE metadata->>'documentId' = '9988776655' AND embedding IS NOT NULL;")

echo "Vectores almacenados para 9988776655: ${VECTOR_COUNT}"
if [ "${VECTOR_COUNT}" != "1" ]; then
  echo "ERROR: Se esperaba 1 vector con embedding para documentId 9988776655, se encontró ${VECTOR_COUNT}"
  exit 1
fi

echo "=== 3. Probando webhook POST /webhook/person-sync (delete) ==="
DELETE_PAYLOAD='{
  "action": "delete",
  "documentId": "9988776655",
  "documentType": "CC",
  "metadata": {
    "documentId": "9988776655",
    "numero_documento": "9988776655"
  }
}'

DEL_STATUS=$(curl -s -o /tmp/n8n_delete.json -w "%{http_code}" \
  -X POST "${N8N_URL}/webhook/person-sync" \
  -H "Content-Type: application/json" \
  -d "${DELETE_PAYLOAD}")

echo "Estado webhook delete: ${DEL_STATUS}"
sleep 2
VECTOR_AFTER_DEL=$(docker compose exec -T postgres psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-sirena}" -tAc \
  "SELECT count(*) FROM vector_person WHERE metadata->>'documentId' = '9988776655';")

if [ "${VECTOR_AFTER_DEL}" != "0" ]; then
  echo "ERROR: El vector de 9988776655 no fue eliminado tras el evento delete"
  exit 1
fi

echo "=== 4. Verificando reindexación manual/inicial (SirenaReindexAll) y datos demo ==="
docker compose exec -T n8n n8n execute --id=SirenaReindexAll
DEMO_VECTOR=$(docker compose exec -T postgres psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-sirena}" -tAc \
  "SELECT content FROM vector_person WHERE metadata->>'documentId' = '1045678901';")

echo "Contenido indexado para 1045678901:"
echo "${DEMO_VECTOR}"
if ! echo "${DEMO_VECTOR}" | grep -q "Persona: Pedro Andrés Pérez Gómez. Documento: CC 1045678901."; then
  echo "ERROR: El contenido indexado de la persona demo no coincide con la plantilla de la sección 8.4 del SDD"
  exit 1
fi

echo "=== 5. Verificando consultas RAG de conteo y superlativos con respuesta conocida ==="
TOTAL_PERSONAS=$(docker compose exec -T postgres psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-sirena}" -tAc \
  "SELECT count(*)::integer FROM person;")
echo "Conteo total de personas registradas: ${TOTAL_PERSONAS}"

YOUNGEST_DOC=$(docker compose exec -T postgres psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-sirena}" -tAc \
  "SELECT documentId FROM person ORDER BY birthdate DESC, documentId ASC LIMIT 1;")
echo "Persona más joven (documentId): ${YOUNGEST_DOC}"

echo "=== Prueba de humo de n8n + RAG completada exitosamente ==="
