import os
from jinja2 import Environment, FileSystemLoader, select_autoescape
from aiosmtplib import send
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from fastapi import BackgroundTasks, HTTPException
from enums.error_messages import EErrorMessages

# Load environment variables from .env file
load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")

# Initialize Jinja2 environment
template_env = Environment(
    loader=FileSystemLoader(os.path.join(os.getcwd(), "app/templates")),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_template(template_name: str, context: dict) -> str:
    """
    Renders an email template with the provided context.

    Args:
        template_name (str): The name of the template file.
        context (dict): A dictionary containing the context variables for the template.

    Returns:
        str: The rendered template as a string.
    """
    template = template_env.get_template(template_name)
    return template.render(context)


async def send_email(to_email: str, subject: str, template_name: str, context: dict):
    """
    Sends an email with the provided subject and template.

    Args:
        to_email (str): The recipient's email address.
        subject (str): The subject of the email.
        template_name (str): The name of the template file.
        context (dict): A dictionary containing the context variables for the template.

    Raises:
        HTTPException: If there is an error sending the email.
    """
    try:
        html_content = render_template(template_name, context)

        message = MIMEMultipart()
        message["From"] = EMAIL_FROM
        message["To"] = to_email
        message["Subject"] = subject

        message.attach(MIMEText(html_content, "html"))
        await send(
            message,
            hostname=EMAIL_HOST,
            port=EMAIL_PORT,
            username=EMAIL_ACCOUNT,
            password=EMAIL_PASSWORD,
            start_tls=False,
        )

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=EErrorMessages.SYSTEM_ERROR.value)


def send_email_background(
    background_tasks: BackgroundTasks,
    to_email: str,
    subject: str,
    template_name: str,
    context: dict,
):
    """
    Adds a task to send an email in the background.

    Args:
        background_tasks (BackgroundTasks): FastAPI BackgroundTasks instance to add the task.
        to_email (str): The recipient's email address.
        subject (str): The subject of the email.
        template_name (str): The name of the template file.
        context (dict): A dictionary containing the context variables for the template.
    """
    background_tasks.add_task(send_email, to_email, subject, template_name, context)
