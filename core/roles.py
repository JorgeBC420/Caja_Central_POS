# Definición de roles y permisos
ROLES_PERMISOS = {
    "admin": ["todo"],  # Admin tiene todos los permisos
    "subadmin": [
        "ventas", "inventario", "reportes", "usuarios", "clientes",
        "productos", "configuracion_basica", "auditoria"
    ],
    "cajero": [
        "ventas", "clientes", "reportes_basicos"
    ],
    "vendedor": [
        "ventas", "clientes", "productos_consulta"
    ]
}

def tiene_permiso(rol, permiso):
    """Verifica si un rol tiene un permiso específico"""
    if not rol or not permiso:
        return False
    
    permisos_rol = ROLES_PERMISOS.get(rol, [])
    
    # Admin tiene todo
    if "todo" in permisos_rol:
        return True
    
    # Verificar permiso específico
    return permiso in permisos_rol

def obtener_permisos_rol(rol):
    """Obtiene todos los permisos de un rol"""
    return ROLES_PERMISOS.get(rol, [])

def obtener_roles_disponibles():
    """Obtiene lista de roles disponibles"""
    return list(ROLES_PERMISOS.keys())
