from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.email import SMTP_CONFIG

def send_email(subject, body, to_email):
    msg = MIMEMultipart()
    msg['From'] = SMTP_CONFIG['FROM_EMAIL']
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with SMTP(SMTP_CONFIG['HOST'], SMTP_CONFIG['PORT']) as server:
            server.starttls()
            server.login(SMTP_CONFIG['USERNAME'], SMTP_CONFIG['PASSWORD'])
            server.send_message(msg)
            print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def notify_user_of_event(event_type, user_email):
    subject = f"Notification: {event_type}"
    body = f"Dear User,\n\nThis is to inform you about the following event: {event_type}.\n\nBest Regards,\nYour Application Team"
    send_email(subject, body, user_email)