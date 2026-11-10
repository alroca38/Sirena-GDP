-- 04_demo_data.sql
-- Datos iniciales de demostración coherentes con el documento de diseño (SDD)

INSERT INTO person (
    documentId, documentType, firstName, secondName, lastNames,
    birthdate, genre, email, phoneNumber, photo, photoType
)
VALUES (
    '1045678901', 'CC', 'Pedro', 'Andrés', 'Pérez Gómez',
    DATE '2001-03-12', 'MASCULINO', 'pedro@correo.com', '3001234567', NULL, NULL
)
ON CONFLICT (documentId) DO NOTHING;

INSERT INTO log_transaction (
    timestamp, type, result, documentType, documentId, "user", question, answer
)
SELECT
    clock_timestamp(), 'CREAR', 'EXITO', 'CC', '1045678901', 'ana.gomez', NULL, NULL
WHERE NOT EXISTS (
    SELECT 1 FROM log_transaction WHERE documentId = '1045678901' AND type = 'CREAR'
);

