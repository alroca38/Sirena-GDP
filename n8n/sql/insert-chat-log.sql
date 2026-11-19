-- Parámetros n8n: $1 resultado (EXITO/ERROR), $2 sesión, $3 pregunta, $4 respuesta.
INSERT INTO log_transaction
    (timestamp, type, result, "user", question, answer)
VALUES
    (clock_timestamp(), 'CONSULTA_LN', $1, $2, $3, $4);
