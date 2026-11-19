-- Fuente para el flujo manual "Reindexar todo". No selecciona correo, teléfono ni foto.
SELECT
    documentType,
    documentId,
    firstName,
    secondName,
    lastNames,
    birthdate::text AS birthdate,
    genre::text AS genre
FROM person
ORDER BY documentId;
