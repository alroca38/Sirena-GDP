-- Fuente para el flujo manual "Reindexar todo".
-- Elimina vectores huérfanos de personas borradas y selecciona los datos indexables (sin correo, teléfono ni foto).
WITH purged AS (
    DELETE FROM vector_person v
    WHERE NOT EXISTS (
        SELECT 1
        FROM person p
        WHERE p.documentId = COALESCE(v.metadata ->> 'documentId', v.metadata ->> 'numero_documento')
    )
    RETURNING 1
)
SELECT
    documentType::text AS "documentType",
    documentId AS "documentId",
    firstName AS "firstName",
    secondName AS "secondName",
    lastNames AS "lastNames",
    birthdate::text AS "birthdate",
    genre::text AS "genre"
FROM person
ORDER BY documentId;
