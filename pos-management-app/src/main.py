from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config.settings import DATABASE_URI
from config.billing import BillingConfig
from config.email import EmailConfig
from roles.roles import RoleManager
from db.backup import BackupManager
from db.restore import RestoreManager
from audit.movement_audit import MovementAudit
from notifications.email_notifications import EmailNotificationManager

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Initialize configurations
billing_config = BillingConfig()
email_config = EmailConfig()

# Initialize role management
role_manager = RoleManager()

# Initialize backup and restore managers
backup_manager = BackupManager()
restore_manager = RestoreManager()

# Initialize movement auditing
movement_audit = MovementAudit()

# Initialize email notifications
email_notification_manager = EmailNotificationManager()

if __name__ == '__main__':
    app.run(debug=True)