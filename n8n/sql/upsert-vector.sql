-- Parámetros n8n: $1 documentId, $2 content, $3 embedding JSON array, $4 documentType.
-- Ejecutar como una sola consulta para reemplazar el vector sin duplicar personas.
WITH removed AS (
    DELETE FROM vector_person
    WHERE metadata ->> 'documentId' = $1
       OR metadata ->> 'numero_documento' = $1
    RETURNING 1
)
INSERT INTO vector_person (content, embedding, metadata)
VALUES (
    $2,
    $3::vector,
    jsonb_build_object(
        'documentId', $1,
        'numero_documento', $1,
        'documentType', $4
    )
);
