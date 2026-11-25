-- Parámetros n8n: $1 resultado (EXITO/RECHAZADA/ERROR), $2 sesión, $3 pregunta, $4 respuesta.
-- La sesión es identificador de auditoría, no identidad verificada de Roble.
INSERT INTO log_transaction
    (timestamp, type, result, "user", question, answer)
VALUES
    (clock_timestamp(), 'CONSULTA_LN', $1, $2, $3, $4);
