import httpx

from app.config import settings
from conftest import login


def test_connection_checks_are_admin_only_and_do_not_contact_missing_services(client, monkeypatch):
    login(client, "qualidade@labquality.local")
    assert client.post("/api/v1/system/connections/model/check").status_code == 403
    login(client)
    def no_network(*args, **kwargs):
        raise AssertionError("No external service should be contacted without configuration")
    monkeypatch.setattr("app.connection_checks._http_check", no_network)
    for service in ("model", "odk", "email"):
        result = client.post(f"/api/v1/system/connections/{service}/check")
        assert result.status_code == 200
        assert result.json()["status"] == "unconfigured"


def test_model_and_odk_checks_validate_auth_without_running_inference_or_import(client, monkeypatch):
    login(client)
    cfg = settings()
    cfg.model_api_key, cfg.model_id, cfg.model_base_url = "secret-for-test", "muse-spark-1.3", "https://api.meta.ai/v1"
    cfg.odk_url, cfg.odk_email, cfg.odk_password = "https://odk.example", "test@example.invalid", "secret-for-test"
    calls = []
    def fake_get(url, **kwargs):
        calls.append(url)
        if url.endswith("/models"):
            assert kwargs["headers"]["Authorization"] == "Bearer secret-for-test"
            return httpx.Response(200, request=httpx.Request("GET", url), json={"data": [{"id": "muse-spark-1.3"}]})
        assert kwargs["auth"] == ("test@example.invalid", "secret-for-test")
        return httpx.Response(200, request=httpx.Request("GET", url), json={"id": 7})
    monkeypatch.setattr("app.connection_checks._http_check", fake_get)
    assert client.post("/api/v1/system/connections/model/check").json()["status"] == "connected"
    assert client.post("/api/v1/system/connections/odk/check").json()["status"] == "connected"
    assert calls == ["https://api.meta.ai/v1/models", "https://odk.example/v1/users/current"]

    def reject(url, **kwargs):
        return httpx.Response(401, request=httpx.Request("GET", url))
    monkeypatch.setattr("app.connection_checks._http_check", reject)
    response = client.post("/api/v1/system/connections/model/check").json()
    assert response["status"] == "failed" and "secret-for-test" not in str(response)


def test_email_check_authenticates_but_sends_no_message(client, monkeypatch):
    login(client)
    cfg = settings()
    cfg.smtp_host, cfg.smtp_from = "smtp.example", "noreply@example.invalid"
    cfg.smtp_username, cfg.smtp_password, cfg.smtp_port, cfg.smtp_starttls = "login", "secret-for-test", 587, True
    calls = []
    class FakeSMTP:
        def __init__(self, host, port, timeout):
            assert (host, port, timeout) == ("smtp.example", 587, 8)
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def ehlo(self): calls.append("ehlo")
        def starttls(self, **kwargs): calls.append("starttls")
        def login(self, username, password):
            assert (username, password) == ("login", "secret-for-test")
            calls.append("login")
        def noop(self): return (250, b"ok")
        def send_message(self, *args): raise AssertionError("Connection check must not send email")
    monkeypatch.setattr("app.connection_checks.smtplib.SMTP", FakeSMTP)
    result = client.post("/api/v1/system/connections/email/check").json()
    assert result["status"] == "connected" and calls == ["ehlo", "starttls", "ehlo", "login"]
    assert "secret-for-test" not in str(result)


def test_partial_smtp_is_not_marked_ready(client):
    login(client)
    cfg = settings()
    cfg.smtp_host = "smtp.example"
    assert client.get("/api/v1/system/status").json()["email_configured"] is False
    assert client.post("/api/v1/system/connections/email/check").json()["status"] == "unconfigured"


def test_smtp_465_uses_implicit_tls_without_delivery(client, monkeypatch):
    login(client)
    cfg = settings()
    cfg.smtp_host, cfg.smtp_from = "smtp.example", "noreply@example.invalid"
    cfg.smtp_username, cfg.smtp_password, cfg.smtp_port = "login", "secret-for-test", 465
    calls = []

    class FakeSMTPSSL:
        def __init__(self, host, port, timeout, context):
            assert (host, port, timeout) == ("smtp.example", 465, 8)
            assert context is not None
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def ehlo(self): calls.append("ehlo")
        def starttls(self, **kwargs): raise AssertionError("Port 465 already uses TLS")
        def login(self, *args): calls.append("login")
        def noop(self): return (250, b"ok")
        def send_message(self, *args): raise AssertionError("Connection check must not send email")

    monkeypatch.setattr("app.connection_checks.smtplib.SMTP_SSL", FakeSMTPSSL)
    assert client.post("/api/v1/system/connections/email/check").json()["status"] == "connected"
    assert calls == ["ehlo", "login"]
