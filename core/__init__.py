# Core module - Sistema POS
"""
Módulo core del sistema POS que contiene:
- DatabaseManager: Gestión de base de datos
- SistemaCaja: Lógica principal del sistema
- Decoradores: Autenticación y autorización
- Roles: Sistema de permisos
- Config: Configuración del sistema
"""

__all__ = [
    'DatabaseManager',
    'SistemaCaja', 
    'ConfigManager',
    'cargar_config_tienda'
]
