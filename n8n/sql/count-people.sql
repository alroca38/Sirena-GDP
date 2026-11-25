-- Consulta fija de solo lectura para preguntas de conteo.
SELECT count(*)::integer AS total_personas
FROM person;
