# Flujos n8n

Los archivos JSON de esta carpeta son exportaciones para importar desde el editor n8n. Los workflows se importan inactivos y requieren enlazar la credencial PostgreSQL `Sirena PostgreSQL` antes de activarlos.

- `sirena-person-sync.json`: webhook `POST /webhook/person-sync`, embedding incremental con Ollama y upsert/eliminación en `vector_person`.
- `sirena-reindex-all.json`: reindexación manual desde `person`, excluye datos de contacto y foto.
- `sirena-chat-rag.json`: chat en español, recuperación semántica y consultas fijas de conteo/edad; registra preguntas y respuestas en `log_transaction`.

Ollama se resuelve por el nombre `ollama` dentro de Compose. Los modelos `bge-m3` y `qwen2.5:3b` se descargan mediante el servicio `ollama-models`. La guía operativa fuera del repositorio contiene los pasos para importar, asignar credenciales, validar y activar.
