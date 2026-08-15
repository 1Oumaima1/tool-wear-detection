import logging
import smtplib
from email.mime.text import MIMEText

from app.config import settings
from app.models.settings import PlatformSettings

logger = logging.getLogger("email_service")


def _build_message(alert_data: dict, smtp_from: str, smtp_to: str) -> MIMEText:
    body = f"""
ALERTE — Outil de coupe dégradé détecté

Machine ID     : {alert_data['machine_id']}
Machine        : {alert_data['machine_name']}
Tool ID        : {alert_data['tool_id']}
Identifiant    : {alert_data['tool_identifier']}
Prédiction     : {alert_data['predicted_class'].upper()}
Confiance      : {alert_data['confidence']*100:.1f}%
Date           : {alert_data['date']}
Heure          : {alert_data['time']}

Recommandation :
{alert_data['recommendation']}

--
Agatronic Industrial AI Monitoring Platform (alerte automatique)
"""
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = f"[ALERTE OUTIL] {alert_data['tool_identifier']} — {alert_data['predicted_class'].upper()}"
    msg["From"] = smtp_from
    msg["To"] = smtp_to
    return msg


def send_alert_email(alert_data: dict, platform_settings: PlatformSettings | None) -> bool:

    host = (platform_settings.smtp_host if platform_settings and platform_settings.smtp_host else settings.SMTP_HOST)
    port = (platform_settings.smtp_port if platform_settings and platform_settings.smtp_port else settings.SMTP_PORT)
    user = (platform_settings.smtp_user if platform_settings and platform_settings.smtp_user else settings.SMTP_USER)
    password = (platform_settings.smtp_password if platform_settings and platform_settings.smtp_password else settings.SMTP_PASSWORD)
    to_addr = (platform_settings.alert_email_to if platform_settings and platform_settings.alert_email_to else settings.ALERT_EMAIL_TO)

    if not user or not password or not to_addr:
        logger.warning("SMTP non configuré (user/password/destinataire manquant) — email non envoyé.")
        return False

    msg = _build_message(alert_data, smtp_from=settings.ALERT_EMAIL_FROM, smtp_to=to_addr)

    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            server.login(user, password)
            server.sendmail(settings.ALERT_EMAIL_FROM, [to_addr], msg.as_string())
        logger.info("Email d'alerte envoyé à %s pour l'outil %s", to_addr, alert_data["tool_identifier"])
        return True
    except Exception:
        logger.exception("Échec de l'envoi de l'email d'alerte")
        return False
