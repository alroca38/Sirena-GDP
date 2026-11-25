#!/usr/bin/env bash
# Prueba de humo para habilitar y deshabilitar el microservicio ms-consult (RNF-03)
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"

echo "=== 1. Deshabilitando ms-consult ==="
docker compose stop ms-consult || true
docker compose rm -f ms-consult || true

sleep 2
STATUS_OFF=$(curl -s -o /tmp/consult_off.json -w "%{http_code}" "${BASE_URL}/api/consult/health")
echo "Estado con ms-consult apagado: ${STATUS_OFF}"
cat /tmp/consult_off.json
echo ""

if [ "${STATUS_OFF}" != "503" ]; then
  echo "ERROR: Se esperaba HTTP 503 cuando ms-consult está apagado, se obtuvo ${STATUS_OFF}"
  exit 1
fi

echo "=== 2. Habilitando ms-consult (profile: consult) ==="
docker compose --profile consult up -d ms-consult

echo "Esperando a que ms-consult esté disponible..."
for i in {1..15}; do
  STATUS_ON=$(curl -s -o /tmp/consult_on.json -w "%{http_code}" "${BASE_URL}/api/consult/health" || true)
  if [ "${STATUS_ON}" = "200" ]; then
    break
  fi
  sleep 2
done

echo "Estado con ms-consult encendido: ${STATUS_ON}"
cat /tmp/consult_on.json
echo ""

if [ "${STATUS_ON}" != "200" ]; then
  echo "ERROR: Se esperaba HTTP 200 cuando ms-consult está encendido, se obtuvo ${STATUS_ON}"
  exit 1
fi

echo "=== Prueba de humo RNF-03 completada exitosamente ==="

