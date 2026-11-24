# n8n en Sirena

Sirena utiliza n8n para mantener el índice vectorial de personas y ofrecer consultas en lenguaje natural. Los servicios `ms-create`, `ms-modify` y `ms-delete` notifican `POST /webhook/person-sync` después de confirmar los cambios en PostgreSQL. El contenido preparado para indexar omite correo, teléfono y foto.

## Estructura

- `contracts/person-sync.schema.json`: contrato del evento que envían los microservicios.
- `sql/`: consultas SQL acotadas para indexación, reindexación, recuperación y auditoría.
- `workflows/`: exportaciones n8n sin credenciales.

## Operación

Compose publica n8n en el puerto `5678` y conserva sus datos en `n8ndata`. Configura una clave estable `N8N_ENCRYPTION_KEY` en `.env`; n8n la utiliza para cifrar las credenciales almacenadas. No la cambies mientras necesites acceder a las credenciales existentes.

Compose ejecuta Ollama sin publicar su puerto al host y conserva modelos en `ollamadata`. El servicio descarga `qwen2.5:3b` para chat y `bge-m3` para embeddings antes de iniciar n8n. Ambos modelos son multilingües; `bge-m3` entrega vectores de 1024 dimensiones. El modelo de chat requiere aproximadamente 2 GB de memoria de almacenamiento; Ollama necesita memoria adicional al ejecutar los modelos.

En las credenciales PostgreSQL de n8n usa host `postgres`, puerto `5432`, y la base/usuario/clave del entorno local. El usuario debe leer `person`, leer y escribir `vector_person`, e insertar en `log_transaction`.

## Flujos

### Sincronización

El webhook `POST /webhook/person-sync` acepta los eventos `upsert` y `delete` definidos en `contracts/person-sync.schema.json`. El evento `upsert` genera un embedding del campo `content` y reemplaza el vector existente por `documentId`; `delete` elimina el vector por documento. Usa consultas parametrizadas de `sql/`.

### Reindexación

El flujo manual consulta `sql/reindex-source.sql`, crea el mismo texto que `buildPersonIndexContent` en `libs/gdp-common/gdp_common/n8n_client.py` y actualiza los vectores con el mismo modelo de embeddings de sincronización y búsqueda.

### Chat RAG

El chat usa similitud vectorial para consultas descriptivas y SQL predefinido de solo lectura para conteos y superlativos. El modelo responde únicamente con datos recuperados, en español; si el contexto no basta, indica que no dispone de esa información. El texto recuperado se trata como dato, no como instrucción. Cada pregunta y respuesta se registra como `CONSULTA_LN`.

No se conecta el chat al SSO Roble ni a la SPA en esta integración. La identidad auditada es el identificador de sesión de n8n y no equivale a una identidad verificada. Mantén la interfaz n8n limitada a usuarios autorizados.

## Datos y modelos

El proveedor y modelo de chat/embeddings se configuran como credenciales n8n, nunca en los archivos exportados. El mismo modelo de embeddings debe usarse para indexar y consultar. `vector_person.embedding` no fija dimensión; define cualquier índice vectorial después de seleccionar el modelo. Cambiar el modelo obliga a reindexar.

Los microservicios tratan la sincronización como mejor esfuerzo: el CRUD ya confirmado no se revierte si n8n falla y no hay reintento automático. El flujo manual de reindexación permite reconstruir el índice desde `person`.
