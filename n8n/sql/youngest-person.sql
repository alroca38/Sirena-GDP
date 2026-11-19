-- Consulta fija de solo lectura para preguntas superlativas.
SELECT firstName, secondName, lastNames, documentType, documentId, birthdate
FROM person
ORDER BY birthdate DESC, documentId ASC
LIMIT 1;
