# Flujos n8n

Los archivos JSON de esta carpeta cuentan con identificadores estables (`SirenaPersonSync`, `SirenaReindexAll`, `SirenaChatRag001`) y se enlazan con la credencial PostgreSQL `Sirena PostgreSQL` (`id: SirenaPostgres01`). Al iniciar el contenedor `n8n`, el script `n8n/entrypoint.sh` crea la credencial desde las variables de entorno, importa los tres flujos, activa `Sirena - person-sync` y `Sirena - Chat RAG`, y ejecuta una reindexación inicial (`Sirena - Reindexar todo`).

- `sirena-person-sync.json`: webhook `POST /webhook/person-sync`, embedding incremental con Ollama y upsert/eliminación en `vector_person`.
- `sirena-reindex-all.json`: reindexación manual/inicial desde `person`, limpia vectores huérfanos y excluye datos de contacto y foto.
- `sirena-chat-rag.json`: chat en español, recuperación semántica y consultas fijas de conteo/edad; registra preguntas y respuestas (`EXITO`, `RECHAZADA`, `ERROR`) en `log_transaction`.

Ollama se resuelve por el nombre `ollama` dentro de Compose. Los modelos `bge-m3` y `qwen2.5:3b` se descargan mediante el servicio `ollama-models`.
