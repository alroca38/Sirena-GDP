-- Parámetros n8n: $1 embedding de la pregunta como array JSON, $2 cantidad máxima.
SELECT content, metadata
FROM vector_person
WHERE embedding IS NOT NULL
ORDER BY embedding <=> $1::vector
LIMIT $2;
