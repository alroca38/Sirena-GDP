from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

from gdp_common.n8n_client import (
    buildPersonIndexContent,
    calculateAge,
    formatDateUi,
    notifyPersonDelete,
    notifyPersonUpsert,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
N8N_DIR = ROOT_DIR / "n8n"
WORKFLOWS_DIR = N8N_DIR / "workflows"


def test_build_person_index_content_matches_sdd_section_8_4() -> None:
    person = {
        "documentId": "1243568790",
        "documentType": "CC",
        "firstName": "Pedro",
        "secondName": "Andrés",
        "lastNames": "Pérez Gómez",
        "birthdate": date(2001, 3, 12),
        "genre": "MASCULINO",
        "email": "pedro@correo.com",
        "phoneNumber": "3001234567",
    }
    assert formatDateUi(person["birthdate"]) == "12-mar-2001"
    assert calculateAge(person["birthdate"], today=date(2026, 3, 12)) == 25

    with patch("gdp_common.n8n_client.calculateAge", return_value=25):
        content = buildPersonIndexContent(person)

    expected = (
        "Persona: Pedro Andrés Pérez Gómez. Documento: CC 1243568790.\n"
        "Fecha de nacimiento: 12-mar-2001 (25 años). Género: Masculino."
    )
    assert content == expected
    assert "pedro@correo.com" not in content
    assert "3001234567" not in content


def test_notify_person_upsert_and_delete_payload_contract() -> None:
    captured: list[dict] = []

    def fake_post(payload: dict) -> bool:
        captured.append(payload)
        return True

    person = {
        "documentId": "1045678901",
        "documentType": "CC",
        "firstName": "Pedro",
        "secondName": "Andrés",
        "lastNames": "Pérez Gómez",
        "birthdate": date(2001, 3, 12),
        "genre": "MASCULINO",
    }

    with patch("gdp_common.n8n_client._postWebhook", side_effect=fake_post):
        assert notifyPersonUpsert(person) is True
        assert notifyPersonDelete("1045678901", "CC") is True

    upsert_payload, delete_payload = captured
    assert upsert_payload["action"] == "upsert"
    assert upsert_payload["documentId"] == "1045678901"
    assert upsert_payload["documentType"] == "CC"
    assert upsert_payload["metadata"] == {
        "documentId": "1045678901",
        "numero_documento": "1045678901",
        "documentType": "CC",
    }
    assert "Persona: Pedro Andrés Pérez Gómez." in upsert_payload["content"]

    assert delete_payload == {
        "action": "delete",
        "documentId": "1045678901",
        "documentType": "CC",
        "metadata": {
            "documentId": "1045678901",
            "numero_documento": "1045678901",
        },
    }


def test_n8n_workflows_structure_and_connections() -> None:
    expected_workflows = {
        "sirena-person-sync.json": "SirenaPersonSync",
        "sirena-reindex-all.json": "SirenaReindexAll",
        "sirena-chat-rag.json": "SirenaChatRag001",
    }

    for filename, expected_id in expected_workflows.items():
        path = WORKFLOWS_DIR / filename
        assert path.exists(), f"Falta el workflow {filename}"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("id") == expected_id

        nodes = data.get("nodes", [])
        node_names = {n["name"] for n in nodes}
        assert len(node_names) == len(nodes), f"Nombres de nodos duplicados en {filename}"

        for node in nodes:
            if node.get("type") == "n8n-nodes-base.postgres":
                cred = node.get("credentials", {}).get("postgres", {})
                assert cred.get("id") == "SirenaPostgres01"
                assert cred.get("name") == "Sirena PostgreSQL"

        for src, targets in data.get("connections", {}).items():
            assert src in node_names, f"Conexión desde nodo inexistente '{src}' en {filename}"
            for branch in targets.get("main", []):
                for link in branch:
                    assert link["node"] in node_names, (
                        f"Conexión hacia nodo inexistente '{link['node']}' en {filename}"
                    )
