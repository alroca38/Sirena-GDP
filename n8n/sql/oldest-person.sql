-- Consulta fija de solo lectura para preguntas superlativas (mayor edad).
SELECT firstName, secondName, lastNames, documentType, documentId, birthdate
FROM person
ORDER BY birthdate ASC, documentId ASC
LIMIT 1;
