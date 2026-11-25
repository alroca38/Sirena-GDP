-- Consulta fija de solo lectura para preguntas superlativas (menor edad / más joven).
SELECT
    concat_ws(' ', firstName, secondName, lastNames) AS "nombreCompleto",
    firstName AS "firstName",
    secondName AS "secondName",
    lastNames AS "lastNames",
    documentType::text AS "documentType",
    documentId AS "documentId",
    birthdate::text AS "birthdate",
    EXTRACT(YEAR FROM age((now() AT TIME ZONE 'America/Bogota')::date, birthdate))::integer AS "edadAnos",
    genre::text AS "genre"
FROM person
ORDER BY birthdate DESC, documentId ASC
LIMIT 1;
