"""Read-only connection checks. No model inference, ODK import, or email delivery."""

import smtplib
import socket
import ssl
from urllib.parse import urlparse

import httpx

from .config import settings


def _http_check(url: str, *, headers: dict | None = None, auth=None) -> httpx.Response:
    response = httpx.get(url, headers=headers, auth=auth, timeout=8, follow_redirects=False)
    return response


def check_connection(service: str) -> dict[str, str]:
    cfg = settings()
    if service == "model":
        if not cfg.model_api_key:
            return {"status": "unconfigured", "message": "Defina LQ_MODEL_API_KEY no .env e reinicie a API."}
        base = cfg.model_base_url.rstrip("/")
        parsed = urlparse(base)
        if parsed.scheme != "https" or not parsed.hostname:
            return {"status": "failed", "message": "LQ_MODEL_BASE_URL deve usar HTTPS."}
        try:
            response = _http_check(base + "/models", headers={"Authorization": "Bearer " + cfg.model_api_key})
            if response.status_code in (401, 403):
                return {"status": "failed", "message": "Chave Meta recusada ou sem permissão para consultar modelos."}
            if response.status_code != 200:
                return {"status": "failed", "message": f"Meta Model API respondeu HTTP {response.status_code}."}
            payload = response.json()
            models = payload.get("data", []) if isinstance(payload, dict) else None
            if not isinstance(models, list):
                return {"status": "failed", "message": "A lista de modelos Meta veio num formato inesperado."}
            if not any(isinstance(model, dict) and model.get("id") == cfg.model_id for model in models):
                return {"status": "failed", "message": "Chave aceite, mas o modelo configurado não consta da lista disponível."}
            return {"status": "connected", "message": "Chave aceite e modelo disponível. Faça uma análise para validar a inferência e os créditos."}
        except (httpx.HTTPError, ValueError):
            return {"status": "failed", "message": "Não foi possível consultar a Meta Model API."}

    if service == "odk":
        if not (cfg.odk_url and cfg.odk_email and cfg.odk_password):
            return {"status": "unconfigured", "message": "Defina LQ_ODK_URL, LQ_ODK_EMAIL e LQ_ODK_PASSWORD no .env e reinicie a API."}
        base = cfg.odk_url.rstrip("/")
        parsed = urlparse(base)
        if parsed.scheme != "https" or not parsed.hostname:
            return {"status": "failed", "message": "LQ_ODK_URL deve usar HTTPS."}
        try:
            response = _http_check(base + "/v1/users/current", auth=(cfg.odk_email, cfg.odk_password))
            if response.status_code == 401:
                return {"status": "failed", "message": "ODK respondeu HTTP 401: confirme o email e a palavra-passe do utilizador Web; SSO pode impedir Basic Auth."}
            if response.status_code == 403:
                return {"status": "failed", "message": "ODK respondeu HTTP 403: a conta autenticou, mas não tem permissão para esta operação."}
            if 300 <= response.status_code < 400:
                return {"status": "failed", "message": "ODK redireccionou o pedido. Confirme a URL base HTTPS, sem /v1 e sem página de login."}
            if response.status_code == 404:
                return {"status": "failed", "message": "ODK respondeu HTTP 404: confirme a URL base do ODK Central, sem /v1."}
            if response.status_code != 200:
                return {"status": "failed", "message": f"ODK Central respondeu HTTP {response.status_code}."}
            payload = response.json()
            if not isinstance(payload, dict) or not payload.get("id"):
                return {"status": "failed", "message": "A resposta de autenticação ODK veio num formato inesperado."}
            return {"status": "connected", "message": "Autenticação ODK aceite. Projecto, formulário e mapeamento ainda precisam de validação."}
        except (httpx.HTTPError, ValueError):
            return {"status": "failed", "message": "Não foi possível autenticar no ODK Central."}

    if service == "email":
        if not cfg.smtp_configured:
            return {"status": "unconfigured", "message": "Defina LQ_SMTP_HOST, LQ_SMTP_FROM, LQ_SMTP_USERNAME e LQ_SMTP_PASSWORD no .env e reinicie a API."}
        phase = "a ligação TCP"
        try:
            context = ssl.create_default_context()
            if cfg.smtp_port == 465:
                smtp = smtplib.SMTP_SSL(cfg.smtp_host, cfg.smtp_port, timeout=8, context=context)
            else:
                smtp = smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=8)
            with smtp:
                phase = "a saudação SMTP"
                smtp.ehlo()
                if cfg.smtp_starttls and cfg.smtp_port != 465:
                    phase = "o STARTTLS"
                    smtp.starttls(context=context)
                    phase = "a saudação após TLS"
                    smtp.ehlo()
                phase = "a autenticação"
                smtp.login(cfg.smtp_username, cfg.smtp_password)
                phase = "a confirmação da sessão"
                code, _ = smtp.noop()
                if code != 250:
                    return {"status": "failed", "message": "Servidor SMTP não confirmou a ligação autenticada."}
            return {"status": "connected", "message": "Ligação e autenticação SMTP verificadas. Nenhum email foi enviado."}
        except smtplib.SMTPAuthenticationError as exc:
            return {"status": "failed", "message": f"SMTP recusou as credenciais (código {exc.smtp_code}). Verifique o utilizador e a chave ou palavra-passe SMTP activa."}
        except smtplib.SMTPNotSupportedError:
            return {"status": "failed", "message": "O servidor SMTP não suporta STARTTLS ou o método de autenticação solicitado. Confira a porta e o tipo de TLS."}
        except smtplib.SMTPResponseException as exc:
            return {"status": "failed", "message": f"Servidor SMTP recusou a operação (código {exc.smtp_code}). Confirme a porta, TLS e permissões da conta."}
        except ssl.SSLError:
            return {"status": "failed", "message": "Falhou a negociação TLS com o servidor SMTP. Confira a porta, TLS e o certificado."}
        except (TimeoutError, socket.timeout):
            return {"status": "failed", "message": "A ligação SMTP expirou. Confira o endereço, a porta e a conectividade."}
        except socket.gaierror:
            return {"status": "failed", "message": "O endereço do servidor SMTP não foi encontrado. Confira LQ_SMTP_HOST."}
        except smtplib.SMTPServerDisconnected:
            return {"status": "failed", "message": f"A ligação SMTP foi interrompida durante {phase}. Confira a porta, TLS e a rede."}
        except (smtplib.SMTPException, OSError):
            return {"status": "failed", "message": f"Falha de ligação SMTP durante {phase}. Confira o endereço, a porta e a rede."}

    raise ValueError("Serviço desconhecido.")
