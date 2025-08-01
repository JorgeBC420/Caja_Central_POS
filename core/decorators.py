from functools import wraps
from tkinter import messagebox
from datetime import datetime

def login_required(func):
    """Decorador que requiere que el usuario esté logueado"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'sistema') or not self.sistema.usuario_actual:
            messagebox.showerror("Error", "Debe iniciar sesión para acceder a esta función.")
            return None
        return func(self, *args, **kwargs)
    return wrapper

def admin_required(func):
    """Decorador que requiere permisos de administrador"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'sistema') or not self.sistema.usuario_actual:
            messagebox.showerror("Error", "Debe iniciar sesión.")
            return None
        
        usuario_rol = getattr(self.sistema.usuario_actual, 'rol', '')
        if usuario_rol not in ['admin', 'subadmin']:
            messagebox.showerror("Error", "No tiene permisos de administrador.")
            return None
        
        return func(self, *args, **kwargs)
    return wrapper

def permission_required(permission):
    """Decorador que requiere un permiso específico"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, 'sistema') or not self.sistema.usuario_actual:
                messagebox.showerror("Error", "Debe iniciar sesión.")
                return None
            
            # Importar aquí para evitar imports circulares
            from core.roles import tiene_permiso
            usuario_rol = getattr(self.sistema.usuario_actual, 'rol', '')
            
            if not tiene_permiso(usuario_rol, permission):
                messagebox.showerror("Error", f"No tiene permisos para: {permission}")
                return None
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

def log_action(action_name):
    """Decorador que registra la acción en auditoría"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            resultado = func(self, *args, **kwargs)
            
            # Registrar en auditoría si existe el sistema
            if hasattr(self, 'sistema') and self.sistema.usuario_actual:
                try:
                    evento = {
                        'usuario': self.sistema.usuario_actual.username,
                        'accion': action_name,
                        'descripcion': f"Acción ejecutada: {func.__name__}",
                        'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    self.sistema.db.insertar_auditoria(evento)
                except Exception as e:
                    print(f"Error registrando auditoría: {e}")
            
            return resultado
        return wrapper
    return decorator
