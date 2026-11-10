-- 02_types_and_tables.sql
-- Definición de tipos enumerados y tablas según la sección 6 del SDD

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'document_type_enum') THEN
        CREATE TYPE document_type_enum AS ENUM ('TI', 'CC');
        CREATE CAST (text AS document_type_enum) WITH INOUT AS IMPLICIT;
        CREATE CAST (varchar AS document_type_enum) WITH INOUT AS IMPLICIT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'genre_enum') THEN
        CREATE TYPE genre_enum AS ENUM (
            'MASCULINO',
            'FEMENINO',
            'NO_BINARIO',
            'PREFIERO_NO_REPORTAR'
        );
        CREATE CAST (text AS genre_enum) WITH INOUT AS IMPLICIT;
        CREATE CAST (varchar AS genre_enum) WITH INOUT AS IMPLICIT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_type_enum') THEN
        CREATE TYPE transaction_type_enum AS ENUM (
            'CREAR',
            'MODIFICAR',
            'CONSULTAR',
            'BORRAR',
            'CONSULTA_LN',
            'CONSULTA_LOG'
        );
        CREATE CAST (text AS transaction_type_enum) WITH INOUT AS IMPLICIT;
        CREATE CAST (varchar AS transaction_type_enum) WITH INOUT AS IMPLICIT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_result_enum') THEN
        CREATE TYPE transaction_result_enum AS ENUM (
            'EXITO',
            'RECHAZADA',
            'ERROR'
        );
        CREATE CAST (text AS transaction_result_enum) WITH INOUT AS IMPLICIT;
        CREATE CAST (varchar AS transaction_result_enum) WITH INOUT AS IMPLICIT;
    END IF;
END
$$;

-- Entidad principal: PERSON
CREATE TABLE IF NOT EXISTS person (
    id BIGSERIAL PRIMARY KEY,
    documentId VARCHAR(10) NOT NULL UNIQUE,
    documentType document_type_enum NOT NULL,
    firstName VARCHAR(30) NOT NULL,
    secondName VARCHAR(30),
    lastNames VARCHAR(60) NOT NULL,
    birthdate DATE NOT NULL,
    genre genre_enum NOT NULL,
    email VARCHAR(254) NOT NULL,
    phoneNumber CHAR(10) NOT NULL,
    photo BYTEA,
    photoType VARCHAR(32),
    CONSTRAINT chk_person_document_id CHECK (documentId ~ '^[0-9]{1,10}$'),
    CONSTRAINT chk_person_first_name CHECK (char_length(firstName) BETWEEN 1 AND 30 AND firstName !~ '[0-9]'),
    CONSTRAINT chk_person_second_name CHECK (secondName IS NULL OR (char_length(secondName) BETWEEN 1 AND 30 AND secondName !~ '[0-9]')),
    CONSTRAINT chk_person_last_names CHECK (char_length(lastNames) BETWEEN 1 AND 60 AND lastNames !~ '[0-9]'),
    CONSTRAINT chk_person_birthdate CHECK (birthdate >= DATE '1900-01-01' AND birthdate <= CURRENT_DATE),
    CONSTRAINT chk_person_phone CHECK (phoneNumber ~ '^[0-9]{10}$'),
    CONSTRAINT chk_person_photo_size CHECK (photo IS NULL OR octet_length(photo) <= 2097152),
    CONSTRAINT chk_person_photo_type CHECK (photoType IS NULL OR photoType IN ('image/jpeg', 'image/png'))
);

-- Registro de auditoría: LOG_TRANSACTION
CREATE TABLE IF NOT EXISTS log_transaction (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    type transaction_type_enum NOT NULL,
    result transaction_result_enum NOT NULL,
    documentType VARCHAR(64),
    documentId VARCHAR(64),
    "user" VARCHAR(256),
    question TEXT,
    answer TEXT
);

-- Tabla de vectores para RAG: VECTOR_PERSON
CREATE TABLE IF NOT EXISTS vector_person (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

