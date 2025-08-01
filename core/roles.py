"""
Sistema de Roles y Permisos - Caja Central POS
Gestión avanzada de roles con permisos granulares
"""

import sqlite3
import logging
from enum import Enum, auto
from typing import Dict, Set, List, Optional
from core.database import get_db_cursor

class Role(Enum):
    """Roles disponibles en el sistema"""
    ADMIN = "admin"
    SUB_ADMIN = "sub_admin"
    CASHIER = "cashier"
    SELLER = "seller"

class Permission(Enum):
    """Permisos granulares del sistema"""
    # Reportes y análisis
    VIEW_REPORTS = "view_reports"
    VIEW_SALES_HISTORY = "view_sales_history"
    EXPORT_REPORTS = "export_reports"
    
    # Gestión de usuarios
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    DELETE_USERS = "delete_users"
    
    # Transacciones y ventas
    PROCESS_TRANSACTIONS = "process_transactions"
    VOID_TRANSACTIONS = "void_transactions"
    APPLY_DISCOUNTS = "apply_discounts"
    
    # Inventario
    VIEW_INVENTORY = "view_inventory"
    MANAGE_INVENTORY = "manage_inventory"
    ADD_PRODUCTS = "add_products"
    EDIT_PRODUCTS = "edit_products"
    DELETE_PRODUCTS = "delete_products"
    
    # Configuración del sistema
    VIEW_SETTINGS = "view_settings"
    UPDATE_SETTINGS = "update_settings"
    MANAGE_PRINTERS = "manage_printers"
    
    # Funciones avanzadas
    DATABASE_BACKUP = "database_backup"
    DATABASE_RESTORE = "database_restore"
    MULTISTORE_ACCESS = "multistore_access"
    RESTAURANT_ACCESS = "restaurant_access"
    
    # Facturación
    ELECTRONIC_BILLING = "electronic_billing"
    MANAGE_BILLING_CONFIG = "manage_billing_config"

# Matriz de permisos por rol
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        # Acceso completo a todo
        Permission.VIEW_REPORTS,
        Permission.VIEW_SALES_HISTORY,
        Permission.EXPORT_REPORTS,
        Permission.MANAGE_USERS,
        Permission.VIEW_USERS,
        Permission.CREATE_USERS,
        Permission.DELETE_USERS,
        Permission.PROCESS_TRANSACTIONS,
        Permission.VOID_TRANSACTIONS,
        Permission.APPLY_DISCOUNTS,
        Permission.VIEW_INVENTORY,
        Permission.MANAGE_INVENTORY,
        Permission.ADD_PRODUCTS,
        Permission.EDIT_PRODUCTS,
        Permission.DELETE_PRODUCTS,
        Permission.VIEW_SETTINGS,
        Permission.UPDATE_SETTINGS,
        Permission.MANAGE_PRINTERS,
        Permission.DATABASE_BACKUP,
        Permission.DATABASE_RESTORE,
        Permission.MULTISTORE_ACCESS,
        Permission.RESTAURANT_ACCESS,
        Permission.ELECTRONIC_BILLING,
        Permission.MANAGE_BILLING_CONFIG,
    },
    
    Role.SUB_ADMIN: {
        # Acceso a la mayoría de funciones excepto gestión crítica
        Permission.VIEW_REPORTS,
        Permission.VIEW_SALES_HISTORY,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_USERS,
        Permission.PROCESS_TRANSACTIONS,
        Permission.VOID_TRANSACTIONS,
        Permission.APPLY_DISCOUNTS,
        Permission.VIEW_INVENTORY,
        Permission.MANAGE_INVENTORY,
        Permission.ADD_PRODUCTS,
        Permission.EDIT_PRODUCTS,
        Permission.VIEW_SETTINGS,
        Permission.MULTISTORE_ACCESS,
        Permission.RESTAURANT_ACCESS,
        Permission.ELECTRONIC_BILLING,
    },
    
    Role.CASHIER: {
        # Operaciones de venta y consulta básica
        Permission.PROCESS_TRANSACTIONS,
        Permission.VIEW_INVENTORY,
        Permission.ELECTRONIC_BILLING,
    },
    
    Role.SELLER: {
        # Solo consulta de inventario y ventas básicas
        Permission.VIEW_INVENTORY,
        Permission.PROCESS_TRANSACTIONS,
    },
}

class RoleManager:
    """Gestor de roles y permisos del sistema"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Inicializar tablas de roles y permisos"""
        try:
            with get_db_cursor() as cursor:
                # Tabla de roles
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS roles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        display_name TEXT NOT NULL,
                        description TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabla de permisos
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS permissions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        display_name TEXT NOT NULL,
                        description TEXT,
                        category TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabla de relación rol-permisos
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS role_permissions (
                        role_id INTEGER,
                        permission_id INTEGER,
                        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (role_id, permission_id),
                        FOREIGN KEY (role_id) REFERENCES roles (id),
                        FOREIGN KEY (permission_id) REFERENCES permissions (id)
                    )
                ''')
                
                # Insertar roles base si no existen
                self._insert_default_roles(cursor)
                self._insert_default_permissions(cursor)
                self._assign_default_permissions(cursor)
                
        except Exception as e:
            self.logger.error(f"Error inicializando base de datos de roles: {e}")
    
    def _insert_default_roles(self, cursor):
        """Insertar roles por defecto"""
        default_roles = [
            (Role.ADMIN.value, "Administrador", "Control total del sistema"),
            (Role.SUB_ADMIN.value, "Sub-Administrador", "Gestión operativa"),
            (Role.CASHIER.value, "Cajero", "Operaciones de venta"),
            (Role.SELLER.value, "Vendedor", "Consultas y ventas básicas")
        ]
        
        for role_name, display_name, description in default_roles:
            cursor.execute('''
                INSERT OR IGNORE INTO roles (name, display_name, description) 
                VALUES (?, ?, ?)
            ''', (role_name, display_name, description))
    
    def _insert_default_permissions(self, cursor):
        """Insertar permisos por defecto"""
        permission_data = [
            # Reportes
            (Permission.VIEW_REPORTS.value, "Ver Reportes", "Acceso a reportes del sistema", "reportes"),
            (Permission.VIEW_SALES_HISTORY.value, "Historial Ventas", "Ver historial de ventas", "reportes"),
            (Permission.EXPORT_REPORTS.value, "Exportar Reportes", "Exportar reportes", "reportes"),
            
            # Usuarios
            (Permission.MANAGE_USERS.value, "Gestionar Usuarios", "Crear/editar/eliminar usuarios", "usuarios"),
            (Permission.VIEW_USERS.value, "Ver Usuarios", "Consultar usuarios", "usuarios"),
            
            # Transacciones
            (Permission.PROCESS_TRANSACTIONS.value, "Procesar Ventas", "Realizar transacciones", "ventas"),
            (Permission.VOID_TRANSACTIONS.value, "Anular Ventas", "Cancelar transacciones", "ventas"),
            
            # Inventario
            (Permission.VIEW_INVENTORY.value, "Ver Inventario", "Consultar inventario", "inventario"),
            (Permission.MANAGE_INVENTORY.value, "Gestionar Inventario", "Administrar inventario", "inventario"),
            
            # Configuración
            (Permission.VIEW_SETTINGS.value, "Ver Configuración", "Acceso a configuración", "sistema"),
            (Permission.UPDATE_SETTINGS.value, "Modificar Configuración", "Cambiar configuración", "sistema"),
            
            # Avanzado
            (Permission.MULTISTORE_ACCESS.value, "Multi-Tienda", "Acceso al sistema multi-tienda", "avanzado"),
            (Permission.RESTAURANT_ACCESS.value, "Restaurante", "Acceso al sistema de restaurante", "avanzado"),
        ]
        
        for perm_name, display_name, description, category in permission_data:
            cursor.execute('''
                INSERT OR IGNORE INTO permissions (name, display_name, description, category) 
                VALUES (?, ?, ?, ?)
            ''', (perm_name, display_name, description, category))
    
    def _assign_default_permissions(self, cursor):
        """Asignar permisos por defecto a roles"""
        for role, permissions in ROLE_PERMISSIONS.items():
            role_id = self._get_role_id(cursor, role.value)
            if role_id:
                for permission in permissions:
                    perm_id = self._get_permission_id(cursor, permission.value)
                    if perm_id:
                        cursor.execute('''
                            INSERT OR IGNORE INTO role_permissions (role_id, permission_id) 
                            VALUES (?, ?)
                        ''', (role_id, perm_id))
    
    def _get_role_id(self, cursor, role_name: str) -> Optional[int]:
        """Obtener ID de rol por nombre"""
        cursor.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def _get_permission_id(self, cursor, perm_name: str) -> Optional[int]:
        """Obtener ID de permiso por nombre"""
        cursor.execute("SELECT id FROM permissions WHERE name = ?", (perm_name,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def has_permission(self, user_role: str, permission: Permission) -> bool:
        """Verificar si un rol tiene un permiso específico"""
        try:
            role_enum = Role(user_role)
            return permission in ROLE_PERMISSIONS.get(role_enum, set())
        except ValueError:
            self.logger.warning(f"Rol no válido: {user_role}")
            return False
    
    def get_user_permissions(self, user_role: str) -> Set[Permission]:
        """Obtener todos los permisos de un rol"""
        try:
            role_enum = Role(user_role)
            return ROLE_PERMISSIONS.get(role_enum, set())
        except ValueError:
            self.logger.warning(f"Rol no válido: {user_role}")
            return set()
    
    def get_available_roles(self) -> List[Dict]:
        """Obtener lista de roles disponibles"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute('''
                    SELECT name, display_name, description 
                    FROM roles 
                    WHERE is_active = 1 
                    ORDER BY name
                ''')
                return [
                    {
                        'name': row[0],
                        'display_name': row[1],
                        'description': row[2]
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            self.logger.error(f"Error obteniendo roles: {e}")
            return []
    
    def get_permissions_by_category(self) -> Dict[str, List[Dict]]:
        """Obtener permisos agrupados por categoría"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute('''
                    SELECT name, display_name, description, category 
                    FROM permissions 
                    ORDER BY category, display_name
                ''')
                
                categories = {}
                for row in cursor.fetchall():
                    category = row[3] or 'general'
                    if category not in categories:
                        categories[category] = []
                    
                    categories[category].append({
                        'name': row[0],
                        'display_name': row[1],
                        'description': row[2]
                    })
                
                return categories
        except Exception as e:
            self.logger.error(f"Error obteniendo permisos: {e}")
            return {}

# Instancia global del gestor de roles
role_manager = RoleManager()

# Funciones de compatibilidad con el sistema existente
def tiene_permiso(rol, permiso):
    """Función de compatibilidad para verificar permisos (sistema legacy)"""
    # Mapeo de permisos legacy a nuevos
    legacy_permission_map = {
        "todo": "admin",  # Admin siempre tiene acceso
        "ventas": Permission.PROCESS_TRANSACTIONS,
        "inventario": Permission.MANAGE_INVENTORY,
        "reportes": Permission.VIEW_REPORTS,
        "usuarios": Permission.VIEW_USERS,
        "clientes": Permission.VIEW_USERS,
        "productos": Permission.VIEW_INVENTORY,
        "configuracion_basica": Permission.VIEW_SETTINGS,
        "auditoria": Permission.VIEW_REPORTS,
        "reportes_basicos": Permission.VIEW_SALES_HISTORY,
        "productos_consulta": Permission.VIEW_INVENTORY,
    }
    
    if rol == "admin" or permiso == "todo":
        return True
    
    new_permission = legacy_permission_map.get(permiso)
    if new_permission and isinstance(new_permission, Permission):
        return role_manager.has_permission(rol, new_permission)
    
    return False

def obtener_permisos_rol(rol):
    """Función de compatibilidad para obtener permisos"""
    permissions = role_manager.get_user_permissions(rol)
    return [perm.value for perm in permissions]

def obtener_roles_disponibles():
    """Función de compatibilidad para obtener roles"""
    return ["admin", "sub_admin", "cajero", "vendedor"]

def has_permission(user_role: str, permission: Permission) -> bool:
    """Función de conveniencia para verificar permisos"""
    return role_manager.has_permission(user_role, permission)

def require_permission(permission: Permission):
    """Decorador para requerir permisos específicos"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Implementar lógica de verificación de permisos
            # Por ahora solo devuelve la función
            return func(*args, **kwargs)
        return wrapper
    return decorator
