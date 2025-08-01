"""
Interfaz de usuario para login y gestión de sesiones
Maneja autenticación, roles y permisos de usuarios
"""

import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import json

from core.database import ejecutar_consulta_segura
from core.roles import RoleManager
from ui.ui_helpers import create_styled_frame

class LoginUI:
    """Interfaz principal de login"""
    
    def __init__(self, parent_window=None, callback_function=None):
        self.parent = parent_window
        self.callback_function = callback_function
        self.role_manager = RoleManager()
        
        # Variables de estado
        self.current_user = None
        self.session_token = None
        self.login_attempts = 0
        self.max_attempts = 3
        self.lockout_time = 300  # 5 minutos en segundos
        
        # Variables de interfaz
        self.setup_variables()
        
        # Crear ventana de login
        self.create_login_window()
        
        # Cargar configuración
        self.load_config()
    
    def setup_variables(self):
        """Configura las variables de la interfaz"""
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.remember_var = tk.BooleanVar()
        self.auto_login_var = tk.BooleanVar()
        
        # Variables de configuración
        self.config_vars = {
            'session_timeout': tk.IntVar(value=60),  # minutos
            'password_policy': tk.BooleanVar(value=True),
            'two_factor_enabled': tk.BooleanVar(value=False),
            'auto_logout_idle': tk.IntVar(value=30),  # minutos
            'log_attempts': tk.BooleanVar(value=True)
        }
    
    def create_login_window(self):
        """Crea la ventana principal de login"""
        if self.parent:
            self.window = tk.Toplevel(self.parent)
        else:
            self.window = tk.Tk()
        
        self.window.title("Sistema POS - Iniciar Sesión")
        self.window.geometry("450x600")
        self.window.resizable(False, False)
        
        # Centrar ventana
        self.center_window()
        
        # Configurar estilos
        self.setup_styles()
        
        # Crear contenido
        self.setup_ui()
        
        # Configurar eventos
        self.setup_events()
        
        # Aplicar configuración guardada
        self.apply_saved_config()
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_styles(self):
        """Configura los estilos de la interfaz"""
        style = ttk.Style()
        
        # Configurar tema
        try:
            style.theme_use('clam')
        except:
            pass
        
        # Estilos personalizados
        style.configure('Title.TLabel', font=('Arial', 18, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 12))
        style.configure('Login.TButton', font=('Arial', 12, 'bold'))
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Logo y título
        self.setup_header(main_frame)
        
        # Formulario de login
        self.setup_login_form(main_frame)
        
        # Opciones adicionales
        self.setup_options(main_frame)
        
        # Botones de acción
        self.setup_buttons(main_frame)
        
        # Estado del sistema
        self.setup_status(main_frame)
    
    def setup_header(self, parent):
        """Configura el encabezado con logo y título"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        # Logo placeholder
        logo_frame = ttk.Frame(header_frame, relief=tk.RAISED, borderwidth=2)
        logo_frame.pack(pady=(0, 15))
        
        ttk.Label(logo_frame, text="🏪", font=('Arial', 48)).pack(padx=20, pady=10)
        
        # Título
        ttk.Label(header_frame, text="Sistema POS", 
                 style='Title.TLabel').pack()
        ttk.Label(header_frame, text="Caja Registradora Costa Rica", 
                 style='Subtitle.TLabel').pack()
        
        # *** CREDENCIALES DE ACCESO ***
        credentials_frame = ttk.LabelFrame(header_frame, text="🔐 Credenciales de Acceso", padding=15)
        credentials_frame.pack(fill=tk.X, pady=15)
        
        ttk.Label(credentials_frame, text="USUARIOS DISPONIBLES:", 
                 font=('Arial', 10, 'bold'), foreground='darkblue').pack()
        
        # Admin
        admin_frame = ttk.Frame(credentials_frame)
        admin_frame.pack(fill=tk.X, pady=2)
        ttk.Label(admin_frame, text="👑 Administrador:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        ttk.Label(admin_frame, text="Usuario: admin | Contraseña: admin123", 
                 font=('Arial', 9), foreground='darkgreen').pack(side=tk.LEFT, padx=10)
        
        # Cajero
        cajero_frame = ttk.Frame(credentials_frame)
        cajero_frame.pack(fill=tk.X, pady=2)
        ttk.Label(cajero_frame, text="💰 Cajero:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        ttk.Label(cajero_frame, text="Usuario: cajero | Contraseña: cajero123", 
                 font=('Arial', 9), foreground='darkgreen').pack(side=tk.LEFT, padx=10)
        
        # Vendedor
        vendedor_frame = ttk.Frame(credentials_frame)
        vendedor_frame.pack(fill=tk.X, pady=2)
        ttk.Label(vendedor_frame, text="🛒 Vendedor:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        ttk.Label(vendedor_frame, text="Usuario: vendedor | Contraseña: vendedor123", 
                 font=('Arial', 9), foreground='darkgreen').pack(side=tk.LEFT, padx=10)
        
        # Línea separadora
        ttk.Separator(header_frame, orient='horizontal').pack(fill=tk.X, pady=15)
    
    def setup_login_form(self, parent):
        """Configura el formulario de login"""
        form_frame = create_styled_frame(parent, "Iniciar Sesión")
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        form_content = ttk.Frame(form_frame)
        form_content.pack(fill=tk.X, padx=20, pady=15)
        
        # Usuario
        user_frame = ttk.Frame(form_content)
        user_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(user_frame, text="Usuario:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.username_entry = ttk.Entry(user_frame, textvariable=self.username_var, 
                                       font=('Arial', 12), width=25)
        self.username_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Botones de acceso rápido
        quick_access_frame = ttk.Frame(user_frame)
        quick_access_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(quick_access_frame, text="Admin", width=8,
                  command=lambda: self.quick_login('admin', 'admin123')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(quick_access_frame, text="Cajero", width=8,
                  command=lambda: self.quick_login('cajero', 'cajero123')).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_access_frame, text="Vendedor", width=8,
                  command=lambda: self.quick_login('vendedor', 'vendedor123')).pack(side=tk.LEFT, padx=5)
        
        # Contraseña
        pass_frame = ttk.Frame(form_content)
        pass_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(pass_frame, text="Contraseña:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        pass_input_frame = ttk.Frame(pass_frame)
        pass_input_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.password_entry = ttk.Entry(pass_input_frame, textvariable=self.password_var, 
                                       show="*", font=('Arial', 12))
        self.password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Botón mostrar/ocultar contraseña
        self.show_password_var = tk.BooleanVar()
        self.show_pass_btn = ttk.Checkbutton(pass_input_frame, text="👁", 
                                           variable=self.show_password_var,
                                           command=self.toggle_password_visibility)
        self.show_pass_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Información de intentos
        self.attempts_label = ttk.Label(form_content, text="", 
                                       foreground='red', font=('Arial', 9))
        self.attempts_label.pack(anchor=tk.W)
    
    def setup_options(self, parent):
        """Configura las opciones adicionales"""
        options_frame = ttk.Frame(parent)
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Checkboxes
        ttk.Checkbutton(options_frame, text="Recordar usuario", 
                       variable=self.remember_var).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(options_frame, text="Inicio automático", 
                       variable=self.auto_login_var).pack(anchor=tk.W, pady=2)
        
        # Enlaces
        links_frame = ttk.Frame(options_frame)
        links_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.forgot_link = ttk.Label(links_frame, text="¿Olvidó su contraseña?", 
                                    foreground='blue', cursor='hand2', 
                                    font=('Arial', 9, 'underline'))
        self.forgot_link.pack(side=tk.LEFT)
        self.forgot_link.bind('<Button-1>', self.forgot_password)
        
        self.register_link = ttk.Label(links_frame, text="Crear nueva cuenta", 
                                      foreground='blue', cursor='hand2', 
                                      font=('Arial', 9, 'underline'))
        self.register_link.pack(side=tk.RIGHT)
        self.register_link.bind('<Button-1>', self.register_user)
    
    def setup_buttons(self, parent):
        """Configura los botones de acción"""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Botón principal de login
        self.login_button = ttk.Button(buttons_frame, text="Iniciar Sesión", 
                                      style='Login.TButton', command=self.login)
        self.login_button.pack(fill=tk.X, pady=(0, 10))
        
        # Botones secundarios
        secondary_frame = ttk.Frame(buttons_frame)
        secondary_frame.pack(fill=tk.X)
        
        # Configuración
        ttk.Button(secondary_frame, text="Configuración", 
                  command=self.show_config).pack(side=tk.LEFT, padx=(0, 5))
        
        # Modo invitado
        ttk.Button(secondary_frame, text="Modo Invitado", 
                  command=self.guest_mode).pack(side=tk.LEFT, padx=5)
        
        # Ayuda
        ttk.Button(secondary_frame, text="Ayuda", 
                  command=self.show_help).pack(side=tk.RIGHT)
        
        # Salir
        ttk.Button(secondary_frame, text="Salir", 
                  command=self.quit_application).pack(side=tk.RIGHT, padx=(0, 5))
    
    def setup_status(self, parent):
        """Configura el panel de estado"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X)
        
        # Separador
        ttk.Separator(status_frame, orient='horizontal').pack(fill=tk.X, pady=(0, 10))
        
        # Estado del sistema
        system_status_frame = ttk.Frame(status_frame)
        system_status_frame.pack(fill=tk.X)
        
        ttk.Label(system_status_frame, text="Estado del Sistema:", 
                 font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        
        self.system_status_label = ttk.Label(system_status_frame, text="Listo", 
                                            foreground='green', font=('Arial', 9))
        self.system_status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Información de base de datos
        db_status_frame = ttk.Frame(status_frame)
        db_status_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(db_status_frame, text="Base de Datos:", 
                 font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        
        self.db_status_label = ttk.Label(db_status_frame, text="Conectada", 
                                        foreground='green', font=('Arial', 9))
        self.db_status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Fecha y hora
        datetime_frame = ttk.Frame(status_frame)
        datetime_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.datetime_label = ttk.Label(datetime_frame, text="", 
                                       font=('Arial', 8), foreground='gray')
        self.datetime_label.pack(side=tk.RIGHT)
        
        # Actualizar fecha y hora
        self.update_datetime()
    
    def setup_events(self):
        """Configura los eventos de la interfaz"""
        # Enter para login
        self.window.bind('<Return>', lambda e: self.login())
        
        # Escape para salir
        self.window.bind('<Escape>', lambda e: self.quit_application())
        
        # Focus inicial
        self.username_entry.focus()
        
        # Eventos de ventana
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def toggle_password_visibility(self):
        """Alterna la visibilidad de la contraseña"""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")
    
    def update_datetime(self):
        """Actualiza la fecha y hora"""
        now = datetime.now()
        self.datetime_label.config(text=now.strftime("%d/%m/%Y %H:%M:%S"))
        self.window.after(1000, self.update_datetime)
    
    def login(self):
        """Procesa el login del usuario"""
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        # Validaciones básicas
        if not username or not password:
            messagebox.showerror("Error", "Complete todos los campos")
            return
        
        # Verificar intentos de login
        if self.is_account_locked():
            messagebox.showerror("Cuenta Bloqueada", 
                               f"Demasiados intentos fallidos. Intente en {self.lockout_time // 60} minutos.")
            return
        
        try:
            # Verificar credenciales
            user_data = self.authenticate_user(username, password)
            
            if user_data:
                # Login exitoso
                self.login_attempts = 0
                self.current_user = user_data
                self.session_token = self.generate_session_token()
                
                # Registrar login
                self.log_login_attempt(username, True)
                
                # Guardar configuración si está marcado
                if self.remember_var.get():
                    self.save_user_config()
                
                # Mostrar bienvenida
                self.show_welcome_message()
                
                # Ejecutar callback si existe
                if self.callback_function:
                    self.callback_function(user_data)
                
                # Cerrar ventana de login
                self.window.destroy()
            else:
                # Login fallido
                self.login_attempts += 1
                self.log_login_attempt(username, False)
                
                remaining = self.max_attempts - self.login_attempts
                if remaining > 0:
                    self.attempts_label.config(text=f"Credenciales incorrectas. Intentos restantes: {remaining}")
                    messagebox.showerror("Error", "Usuario o contraseña incorrectos")
                else:
                    self.attempts_label.config(text="Cuenta bloqueada temporalmente")
                    messagebox.showerror("Cuenta Bloqueada", 
                                       f"Demasiados intentos fallidos. Cuenta bloqueada por {self.lockout_time // 60} minutos.")
                
                # Limpiar contraseña
                self.password_var.set("")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error durante el login: {str(e)}")
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Autentica las credenciales del usuario"""
        
        # *** CREDENCIALES POR DEFECTO ***
        default_users = {
            'admin': {
                'password': 'admin123',
                'full_name': 'Administrador',
                'email': 'admin@cajapos.com',
                'role': 'Administrador',
                'permissions': {
                    'ventas': True, 'inventario': True, 'clientes': True,
                    'reportes': True, 'usuarios': True, 'configuracion': True
                }
            },
            'cajero': {
                'password': 'cajero123',
                'full_name': 'Cajero Principal',
                'email': 'cajero@cajapos.com',
                'role': 'Cajero',
                'permissions': {
                    'ventas': True, 'inventario': False, 'clientes': True,
                    'reportes': False, 'usuarios': False, 'configuracion': False
                }
            },
            'vendedor': {
                'password': 'vendedor123',
                'full_name': 'Vendedor',
                'email': 'vendedor@cajapos.com',
                'role': 'Vendedor',
                'permissions': {
                    'ventas': True, 'inventario': True, 'clientes': True,
                    'reportes': True, 'usuarios': False, 'configuracion': False
                }
            }
        }
        
        # Verificar credenciales por defecto primero
        if username in default_users and default_users[username]['password'] == password:
            user_data = {
                'id': hash(username) % 10000,  # ID único basado en username
                'username': username,
                'email': default_users[username]['email'],
                'full_name': default_users[username]['full_name'],
                'role_id': 1 if username == 'admin' else 2,
                'is_active': True,
                'last_login': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat(),
                'role_name': default_users[username]['role'],
                'permissions': default_users[username]['permissions']
            }
            return user_data
        
        # Si no es usuario por defecto, buscar en base de datos
        try:
            # Hash de la contraseña
            password_hash = self.hash_password(password)
            
            # Buscar usuario en la base de datos
            query = """
                SELECT u.id, u.username, u.email, u.full_name, u.role_id, u.is_active,
                       u.password_hash, u.last_login, u.created_at,
                       r.name as role_name, r.permissions
                FROM usuarios u
                LEFT JOIN roles r ON u.role_id = r.id
                WHERE u.username = ? AND u.is_active = 1
            """
            
            resultado = ejecutar_consulta_segura(query, (username,))
            
            if resultado and len(resultado) > 0:
                user_record = resultado[0]
                
                # Verificar contraseña
                if self.verify_password(password, user_record[6]):  # password_hash
                    # Actualizar último login
                    self.update_last_login(user_record[0])
                    
                    # Preparar datos del usuario
                    user_data = {
                        'id': user_record[0],
                        'username': user_record[1],
                        'email': user_record[2],
                        'full_name': user_record[3],
                        'role_id': user_record[4],
                        'is_active': user_record[5],
                        'last_login': user_record[7],
                        'created_at': user_record[8],
                        'role_name': user_record[9],
                        'permissions': json.loads(user_record[10]) if user_record[10] else {}
                    }
                    
                    return user_data
            
            return None
            
        except Exception as e:
            print(f"Error en autenticación: {e}")
            return None
    
    def hash_password(self, password: str) -> str:
        """Genera hash seguro de la contraseña"""
        # Usar salt único por contraseña
        salt = secrets.token_hex(16)
        # Combinar contraseña y salt
        combined = f"{password}{salt}"
        # Generar hash
        hash_obj = hashlib.sha256(combined.encode())
        return f"{salt}:{hash_obj.hexdigest()}"
    
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verifica la contraseña contra el hash almacenado"""
        try:
            if ':' not in stored_hash:
                # Hash antiguo sin salt (compatibilidad)
                return hashlib.sha256(password.encode()).hexdigest() == stored_hash
            
            salt, hash_part = stored_hash.split(':', 1)
            combined = f"{password}{salt}"
            computed_hash = hashlib.sha256(combined.encode()).hexdigest()
            return computed_hash == hash_part
            
        except Exception:
            return False
    
    def generate_session_token(self) -> str:
        """Genera token de sesión único"""
        return secrets.token_urlsafe(32)
    
    def update_last_login(self, user_id: int):
        """Actualiza la fecha del último login"""
        try:
            query = "UPDATE usuarios SET last_login = ? WHERE id = ?"
            ejecutar_consulta_segura(query, (datetime.now().isoformat(), user_id))
        except Exception as e:
            print(f"Error actualizando último login: {e}")
    
    def log_login_attempt(self, username: str, success: bool):
        """Registra intento de login"""
        if not self.config_vars['log_attempts'].get():
            return
        
        try:
            query = """
                INSERT INTO login_attempts (username, success, ip_address, user_agent, attempt_time)
                VALUES (?, ?, ?, ?, ?)
            """
            
            # Obtener información adicional si está disponible
            ip_address = "127.0.0.1"  # Placeholder para IP local
            user_agent = "POS Desktop App"
            
            ejecutar_consulta_segura(query, (
                username, success, ip_address, user_agent, datetime.now().isoformat()
            ))
            
        except Exception as e:
            print(f"Error registrando intento de login: {e}")
    
    def is_account_locked(self) -> bool:
        """Verifica si la cuenta está bloqueada"""
        return self.login_attempts >= self.max_attempts
    
    def show_welcome_message(self):
        """Muestra mensaje de bienvenida"""
        if self.current_user:
            welcome_msg = f"¡Bienvenido/a {self.current_user['full_name']}!\n"
            welcome_msg += f"Rol: {self.current_user['role_name']}\n"
            welcome_msg += f"Último acceso: {self.current_user['last_login'] or 'Primer acceso'}"
            
            messagebox.showinfo("Bienvenido", welcome_msg)
    
    def forgot_password(self, event=None):
        """Maneja recuperación de contraseña"""
        ForgotPasswordDialog(self.window)
    
    def register_user(self, event=None):
        """Maneja registro de nuevo usuario"""
        RegisterUserDialog(self.window)
    
    def guest_mode(self):
        """Inicia modo invitado con permisos limitados"""
        guest_user = {
            'id': 0,
            'username': 'invitado',
            'email': '',
            'full_name': 'Usuario Invitado',
            'role_id': 0,
            'is_active': True,
            'role_name': 'Invitado',
            'permissions': {'read_only': True}
        }
        
        if messagebox.askyesno("Modo Invitado", 
                              "¿Desea iniciar en modo invitado?\n"
                              "Tendrá acceso limitado de solo lectura."):
            self.current_user = guest_user
            self.session_token = self.generate_session_token()
            
            if self.callback_function:
                self.callback_function(guest_user)
            
            self.window.destroy()
    
    def show_config(self):
        """Muestra configuración del sistema"""
        ConfigDialog(self.window, self.config_vars)
    
    def quick_login(self, username: str, password: str):
        """Login rápido con credenciales predefinidas"""
        self.username_var.set(username)
        self.password_var.set(password)
        # Ejecutar login automáticamente
        self.login()
    
    def show_help(self):
        """Muestra ayuda del sistema"""
        HelpDialog(self.window)
    
    def load_config(self):
        """Carga configuración guardada"""
        try:
            # Aquí se cargaría desde archivo de configuración
            pass
        except Exception as e:
            print(f"Error cargando configuración: {e}")
    
    def save_user_config(self):
        """Guarda configuración del usuario"""
        try:
            if self.remember_var.get():
                # Guardar usuario (no contraseña)
                config = {
                    'username': self.username_var.get(),
                    'auto_login': self.auto_login_var.get()
                }
                # Aquí se guardaría en archivo de configuración
        except Exception as e:
            print(f"Error guardando configuración: {e}")
    
    def apply_saved_config(self):
        """Aplica configuración guardada"""
        try:
            # Aquí se aplicaría configuración guardada
            pass
        except Exception as e:
            print(f"Error aplicando configuración: {e}")
    
    def quit_application(self):
        """Cierra la aplicación"""
        if messagebox.askyesno("Salir", "¿Está seguro que desea salir?"):
            self.window.quit()
    
    def on_closing(self):
        """Maneja cierre de ventana"""
        self.quit_application()

# Diálogos auxiliares
class ForgotPasswordDialog:
    """Diálogo para recuperación de contraseña"""
    
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Recuperar Contraseña")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        messagebox.showinfo("Info", "Función de recuperación en desarrollo")

class RegisterUserDialog:
    """Diálogo para registro de nuevo usuario"""
    
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Registrar Usuario")
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        messagebox.showinfo("Info", "Función de registro en desarrollo")

class ConfigDialog:
    """Diálogo de configuración del sistema"""
    
    def __init__(self, parent, config_vars):
        self.config_vars = config_vars
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Configuración del Sistema")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        messagebox.showinfo("Info", "Configuración avanzada en desarrollo")

class HelpDialog:
    """Diálogo de ayuda del sistema"""
    
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Ayuda del Sistema")
        self.dialog.geometry("700x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_help_content()
    
    def setup_help_content(self):
        """Configura el contenido de ayuda"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        ttk.Label(main_frame, text="Ayuda del Sistema POS", 
                 font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        # Notebook para diferentes secciones
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña de login
        login_frame = ttk.Frame(notebook)
        notebook.add(login_frame, text="Inicio de Sesión")
        
        login_text = tk.Text(login_frame, wrap=tk.WORD, font=('Arial', 10))
        login_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        login_content = """
Ayuda para Inicio de Sesión:

1. Ingrese su nombre de usuario y contraseña
2. Marque "Recordar usuario" para guardar el nombre de usuario
3. Use "Modo Invitado" para acceso limitado sin autenticación
4. Contacte al administrador si olvida su contraseña

Solución de Problemas:
- Si no puede iniciar sesión, verifique sus credenciales
- Después de 3 intentos fallidos, la cuenta se bloquea temporalmente
- Asegúrese de que la base de datos esté conectada
        """
        
        login_text.insert(tk.END, login_content)
        login_text.config(state=tk.DISABLED)
        
        # Pestaña de seguridad
        security_frame = ttk.Frame(notebook)
        notebook.add(security_frame, text="Seguridad")
        
        security_text = tk.Text(security_frame, wrap=tk.WORD, font=('Arial', 10))
        security_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        security_content = """
Políticas de Seguridad:

1. Use contraseñas seguras (mínimo 8 caracteres)
2. No comparta sus credenciales
3. Cierre sesión al terminar de usar el sistema
4. Las sesiones expiran automáticamente por inactividad

Roles y Permisos:
- Administrador: Acceso completo al sistema
- Gerente: Gestión de ventas e inventario
- Cajero: Solo operaciones de venta
- Invitado: Solo lectura limitada
        """
        
        security_text.insert(tk.END, security_content)
        security_text.config(state=tk.DISABLED)
        
        # Botón cerrar
        ttk.Button(main_frame, text="Cerrar", 
                  command=self.dialog.destroy).pack(pady=10)

class SessionManager:
    """Gestor de sesiones de usuario"""
    
    def __init__(self):
        self.active_sessions = {}
        self.session_timeout = 3600  # 1 hora en segundos
    
    def create_session(self, user_id: int, session_token: str):
        """Crea una nueva sesión"""
        self.active_sessions[session_token] = {
            'user_id': user_id,
            'created_at': datetime.now(),
            'last_activity': datetime.now()
        }
    
    def validate_session(self, session_token: str) -> bool:
        """Valida si una sesión es válida"""
        if session_token not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_token]
        elapsed = (datetime.now() - session['last_activity']).total_seconds()
        
        if elapsed > self.session_timeout:
            self.destroy_session(session_token)
            return False
        
        # Actualizar última actividad
        session['last_activity'] = datetime.now()
        return True
    
    def destroy_session(self, session_token: str):
        """Destruye una sesión"""
        if session_token in self.active_sessions:
            del self.active_sessions[session_token]
    
    def cleanup_expired_sessions(self):
        """Limpia sesiones expiradas"""
        current_time = datetime.now()
        expired_tokens = []
        
        for token, session in self.active_sessions.items():
            elapsed = (current_time - session['last_activity']).total_seconds()
            if elapsed > self.session_timeout:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            self.destroy_session(token)

# Función principal
def mostrar_login(callback_function=None):
    """Función principal para mostrar la ventana de login"""
    return LoginUI(callback_function=callback_function)
