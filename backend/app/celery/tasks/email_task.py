from app.celery.celery_app import celery_app
from core.services.email_service import send_email
from core.services.template_service import registration_template


@celery_app.task(name="send_welcome_email")
def send_welcome_email(to: str, name: str, code: str):
    template = registration_template(name, code)
    subject = "Welcome to Our Service!"
    import asyncio

    try:
        asyncio.run(send_email(to, subject, template))
    except Exception as e:
        print(f"Failed to send email to {to}: {str(e)}")
