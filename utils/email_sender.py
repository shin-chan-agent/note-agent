import os
import smtplib

from email.mime.text import MIMEText
from email.header import Header


def send_email(
    subject,
    body,
):
    """
    SMTPを利用してメールを送信する。
    """

    smtp_server = os.environ["SMTP_SERVER"]
    smtp_port = int(os.environ["SMTP_PORT"])
    smtp_user = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    sender_email = os.environ["SENDER_EMAIL"]
    recipient_email = os.environ["RECIPIENT_EMAIL"]

    message = MIMEText(
        body,
        "plain",
        "utf-8",
    )

    message["Subject"] = Header(
        subject,
        "utf-8",
    )

    message["From"] = sender_email
    message["To"] = recipient_email

    with smtplib.SMTP(
        smtp_server,
        smtp_port,
        timeout=30,
    ) as server:

        server.starttls()

        server.login(
            smtp_user,
            smtp_password,
        )

        server.send_message(message)