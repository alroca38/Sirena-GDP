-- Parámetro n8n: $1 documentId.
DELETE FROM vector_person
WHERE metadata ->> 'documentId' = $1
   OR metadata ->> 'numero_documento' = $1;
