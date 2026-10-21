import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_email(
    to_email: str,
    subject: str,
    body: str,
) -> None:
    if not settings.smtp_host:
        raise RuntimeError("SMTP não está configurado.")

    message = EmailMessage()
    message["From"] = (
        f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    )
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.starttls()

        if settings.smtp_username and settings.smtp_password:
            smtp.login(
                settings.smtp_username,
                settings.smtp_password,
            )

        smtp.send_message(message)