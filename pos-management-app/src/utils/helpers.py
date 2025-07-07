def validate_email(email):
    import re
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def format_currency(amount):
    return "${:,.2f}".format(amount)

def generate_invoice_number():
    import uuid
    return str(uuid.uuid4())

def log_action(action, user_id):
    from datetime import datetime
    timestamp = datetime.now().isoformat()
    with open('action_log.txt', 'a') as log_file:
        log_file.write(f"{timestamp} - User {user_id}: {action}\n")

def validate_positive_integer(value):
    if isinstance(value, int) and value > 0:
        return True
    return False

def sanitize_input(input_string):
    import html
    return html.escape(input_string)