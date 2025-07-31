from pydantic import BaseModel
from typing import List, Optional

class EmailConfig(BaseModel):
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    use_tls: bool
    use_ssl: bool

class EmailTemplates(BaseModel):
    welcome_email: str
    password_reset: str
    order_confirmation: str

class EmailSettings(BaseModel):
    config: EmailConfig
    templates: EmailTemplates

def get_email_settings() -> EmailSettings:
    return EmailSettings(
        config=EmailConfig(
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="your_email@example.com",
            password="your_password",
            use_tls=True,
            use_ssl=False
        ),
        templates=EmailTemplates(
            welcome_email="Welcome to our service, {name}!",
            password_reset="Click here to reset your password: {reset_link}",
            order_confirmation="Thank you for your order, {order_id}!"
        )
    )