-- 03_indexes.sql
-- Índices para acelerar búsquedas por documento y consultas del log de transacciones

CREATE INDEX IF NOT EXISTS idx_person_document_type_id
    ON person (documentType, documentId);

CREATE INDEX IF NOT EXISTS idx_person_birthdate
    ON person (birthdate);

CREATE INDEX IF NOT EXISTS idx_log_transaction_timestamp
    ON log_transaction (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_log_transaction_type
    ON log_transaction (type);

CREATE INDEX IF NOT EXISTS idx_log_transaction_document
    ON log_transaction (documentType, documentId);

CREATE INDEX IF NOT EXISTS idx_log_transaction_document_id
    ON log_transaction (documentId);

CREATE INDEX IF NOT EXISTS idx_vector_person_doc_id
    ON vector_person ((metadata->>'documentId'));

