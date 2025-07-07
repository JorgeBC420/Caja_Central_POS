from enum import Enum, auto

class Role(Enum):
    ADMIN = auto()
    SUB_ADMIN = auto()
    CASHIER = auto()
    SELLER = auto()

class Permission(Enum):
    VIEW_REPORTS = auto()
    MANAGE_USERS = auto()
    PROCESS_TRANSACTIONS = auto()
    VIEW_INVENTORY = auto()
    MANAGE_INVENTORY = auto()
    VIEW_SETTINGS = auto()
    UPDATE_SETTINGS = auto()

role_permissions = {
    Role.ADMIN: {
        Permission.VIEW_REPORTS,
        Permission.MANAGE_USERS,
        Permission.PROCESS_TRANSACTIONS,
        Permission.VIEW_INVENTORY,
        Permission.MANAGE_INVENTORY,
        Permission.VIEW_SETTINGS,
        Permission.UPDATE_SETTINGS,
    },
    Role.SUB_ADMIN: {
        Permission.VIEW_REPORTS,
        Permission.PROCESS_TRANSACTIONS,
        Permission.VIEW_INVENTORY,
        Permission.MANAGE_INVENTORY,
        Permission.VIEW_SETTINGS,
    },
    Role.CASHIER: {
        Permission.PROCESS_TRANSACTIONS,
        Permission.VIEW_INVENTORY,
    },
    Role.SELLER: {
        Permission.VIEW_INVENTORY,
    },
}

def has_permission(role, permission):
    return permission in role_permissions.get(role, set())