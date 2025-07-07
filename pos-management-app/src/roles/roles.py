from enum import Enum

class Role(Enum):
    ADMIN = "admin"
    SUB_ADMINISTRATOR = "sub_administrator"
    CASHIER = "cashier"
    SELLER = "seller"

class Permissions:
    def __init__(self):
        self.permissions = {
            Role.ADMIN: ["manage_users", "view_reports", "edit_settings", "backup_database", "restore_database"],
            Role.SUB_ADMINISTRATOR: ["manage_users", "view_reports"],
            Role.CASHIER: ["process_sales", "view_sales"],
            Role.SELLER: ["view_products", "process_sales"]
        }

    def get_permissions(self, role):
        return self.permissions.get(role, [])

# Example usage
if __name__ == "__main__":
    permissions = Permissions()
    admin_permissions = permissions.get_permissions(Role.ADMIN)
    print(f"Admin Permissions: {admin_permissions}")