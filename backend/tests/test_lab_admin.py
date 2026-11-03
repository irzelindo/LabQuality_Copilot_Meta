from sqlalchemy import select

from app.database import session_factory
from app.models import Assessment, AuditEvent, Laboratory, User
from conftest import login


def test_lab_deactivation_preserves_assessments_and_reactivation_restores_access(client):
    login(client)
    lab = next(l for l in client.get("/api/v1/laboratories").json() if l["code"] == "SUL")
    assessment = client.get("/api/v1/assessments", params={"laboratory_id": lab["id"]}).json()["items"][0]
    edited = client.patch(f"/api/v1/laboratories/{lab['id']}", json={"name": "Laboratório Sul actualizado", "region": "Maputo"})
    assert edited.status_code == 200 and edited.json()["code"] == "SUL"
    assert client.post(f"/api/v1/laboratories/{lab['id']}/status", json={"active": False, "reason": "Suspenso para revisão."}).status_code == 200
    assert lab["id"] not in {l["id"] for l in client.get("/api/v1/laboratories").json()}
    assert client.get(f"/api/v1/assessments/{assessment['id']}").status_code == 404
    inactive = client.get("/api/v1/laboratories?include_inactive=true").json()
    assert next(l for l in inactive if l["id"] == lab["id"])["active"] is False
    with session_factory()() as db:
        assert db.scalar(select(Assessment).where(Assessment.id == assessment["id"])) is not None
    assert client.request("DELETE", f"/api/v1/laboratories/{lab['id']}", json={"reason": "Eliminar laboratório."}).status_code == 409
    assert client.post(f"/api/v1/laboratories/{lab['id']}/status", json={"active": True, "reason": "Revisão concluída."}).status_code == 200
    assert client.get(f"/api/v1/assessments/{assessment['id']}").status_code == 200
    assert any(l["id"] == lab["id"] for l in client.get("/api/v1/laboratories").json())


def test_only_admin_can_manage_own_organization_labs_and_delete_empty_lab(client):
    login(client)
    new = client.post("/api/v1/laboratories", json={"code": "EMPTY", "name": "Temporário"}).json()
    assert client.post("/api/v1/laboratories", json={"code": "EMPTY", "name": "Outro"}).status_code == 409
    user = next(u for u in client.get("/api/v1/users").json() if u["role"] == "quality")
    grant = client.patch(f"/api/v1/users/{user['id']}/access", json={
        "role": "quality", "active": True, "laboratory_ids": user["laboratory_ids"] + [new["id"]]})
    assert grant.status_code == 200
    assert client.request("DELETE", f"/api/v1/laboratories/{new['id']}", json={"reason": "Cadastro em duplicado."}).status_code == 409
    client.patch(f"/api/v1/users/{user['id']}/access", json={
        "role": "quality", "active": True, "laboratory_ids": user["laboratory_ids"]})
    login(client, user["email"])
    assert client.get("/api/v1/laboratories?include_inactive=true").status_code == 403
    assert client.patch(f"/api/v1/laboratories/{new['id']}", json={"name": "Novo", "region": ""}).status_code == 403
    assert client.post(f"/api/v1/laboratories/{new['id']}/status", json={"active": False, "reason": "Motivo válido."}).status_code == 403
    assert client.request("DELETE", f"/api/v1/laboratories/{new['id']}", json={"reason": "Motivo válido."}).status_code == 403
    login(client)
    assert client.request("DELETE", f"/api/v1/laboratories/{new['id']}", json={"reason": "Cadastro em duplicado."}).status_code == 200
    assert client.get("/api/v1/laboratories?include_inactive=true").json() and new["id"] not in {
        l["id"] for l in client.get("/api/v1/laboratories?include_inactive=true").json()}
    with session_factory()() as db:
        assert db.get(Laboratory, new["id"]) is None
        assert db.scalar(select(AuditEvent).where(AuditEvent.entity_id == new["id"],
                                                  AuditEvent.operation == "laboratory.deleted")) is not None


def test_user_identity_and_access_edit_and_inactive_assignment(client):
    login(client)
    quality = next(u for u in client.get("/api/v1/users").json() if u["role"] == "quality")
    assert client.post("/api/v1/users", json={"name": "Duplicado", "email": quality["email"],
        "password": "Password-local-test-only!", "role": "quality", "laboratory_ids": []}).status_code == 409
    lab_id = quality["laboratory_ids"][0]
    edit = {"name": "Responsável Sul", "email": "responsavel@example.org", "role": "quality",
            "active": True, "laboratory_ids": [lab_id]}
    assert client.patch(f"/api/v1/users/{quality['id']}/access", json=edit).status_code == 200
    assert client.post("/api/v1/auth/login", json={"email": edit["email"], "password": "Local-demo-test-2026!"}).status_code == 200
    login(client)
    assert client.patch(f"/api/v1/users/{quality['id']}/access", json={**edit, "email": "admin@labquality.local"}).status_code == 409
    client.post(f"/api/v1/laboratories/{lab_id}/status", json={"active": False, "reason": "Laboratório suspenso."})
    assert client.patch(f"/api/v1/users/{quality['id']}/access", json=edit).status_code == 200
    another = next(l for l in client.get("/api/v1/laboratories").json() if l["code"] == "CENTRO")
    assert client.patch(f"/api/v1/users/{quality['id']}/access", json={**edit,
        "laboratory_ids": [lab_id, another["id"]]}).status_code == 200
    client.post(f"/api/v1/laboratories/{another['id']}/status", json={
        "active": False, "reason": "Outro laboratório suspenso."})
    second = next(u for u in client.get("/api/v1/users").json() if u["role"] == "manager")
    assert another["id"] not in second["laboratory_ids"]
    assert client.patch(f"/api/v1/users/{second['id']}/access", json={
        "role": "manager", "active": True,
        "laboratory_ids": second["laboratory_ids"] + [another["id"]]}).status_code == 404
    assert client.get("/api/v1/users").json() and next(u for u in client.get("/api/v1/users").json()
        if u["id"] == quality["id"])["name"] == edit["name"]


def test_cannot_manage_foreign_laboratory(client):
    login(client)
    with session_factory()() as db:
        from app.models import Organization
        other = Organization(name="Outra organização")
        db.add(other)
        db.flush()
        foreign = Laboratory(organization_id=other.id, code="FOREIGN", name="Laboratório externo")
        db.add(foreign)
        db.commit()
        foreign_id = foreign.id
    assert foreign_id not in {lab["id"] for lab in client.get("/api/v1/laboratories?include_inactive=true").json()}
    assert client.patch(f"/api/v1/laboratories/{foreign_id}", json={"name": "Alterado", "region": ""}).status_code == 404
    assert client.post(f"/api/v1/laboratories/{foreign_id}/status", json={"active": False, "reason": "Motivo válido."}).status_code == 404
    assert client.request("DELETE", f"/api/v1/laboratories/{foreign_id}", json={"reason": "Motivo válido."}).status_code == 404
