import os
import shutil
from datetime import datetime

class DatabaseBackup:
    def __init__(self, db_path, backup_dir):
        self.db_path = db_path
        self.backup_dir = backup_dir

    def create_backup(self):
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

        backup_file = os.path.join(self.backup_dir, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        shutil.copy2(self.db_path, backup_file)
        return backup_file

    def list_backups(self):
        return [f for f in os.listdir(self.backup_dir) if f.endswith('.db')]

    def delete_backup(self, backup_file):
        backup_path = os.path.join(self.backup_dir, backup_file)
        if os.path.exists(backup_path):
            os.remove(backup_path)
            return True
        return False

    def restore_backup(self, backup_file):
        backup_path = os.path.join(self.backup_dir, backup_file)
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, self.db_path)
            return True
        return False