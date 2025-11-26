from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from fastapi import HTTPException

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "vadik505050@gmail.com"
SMTP_PASSWORD = "hlfxcdkncihyqxkn"


async def send_email(to: str, subject: str, body: str):
    message = MIMEMultipart()
    message["From"] = SMTP_USER
    message["To"] = to
    message["Subject"] = subject

    message.attach(MIMEText(body, "html"))

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
