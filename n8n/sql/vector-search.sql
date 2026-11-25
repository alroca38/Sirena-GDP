-- Parámetros n8n:
-- $1 embedding de la pregunta como array JSON
-- $2 filtro opcional de género ('Femenino', 'Masculino', 'No binario', 'Prefiero no reportar' o NULL)
-- $3 filtro opcional de tipo de documento ('CC', 'TI' o NULL)
-- $4 filtro opcional de número de documento (o NULL)
-- $5 cantidad máxima de registros a recuperar
SELECT content, metadata
FROM vector_person
WHERE embedding IS NOT NULL
  AND ($2::text IS NULL OR content ILIKE ('%Género: ' || $2::text || '.%'))
  AND ($3::text IS NULL OR metadata ->> 'documentType' = $3::text)
  AND ($4::text IS NULL OR metadata ->> 'documentId' = $4::text)
ORDER BY embedding <=> $1::vector
LIMIT $5::integer;
