"""
Sistema de Login Seguro - CajaCentral POS
Con tu logo personalizado integrado
"""

import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
import json
import os
from datetime import datetime
from PIL import Image, ImageTk

class SecureLogin:
    """Sistema de login seguro con branding personalizado"""
    
    def __init__(self, callback_function=None):
        self.callback_function = callback_function
        self.login_attempts = 0
        self.max_attempts = 3
        self.current_user = None
        
        # Usuarios por defecto (deberías moverlos a base de datos)
        self.users = {
            "admin": {
                "password": self.hash_password("admin123"),
                "full_name": "Administrador",
                "role": "admin",
                "permissions": "all"
            },
            "cajero": {
                "password": self.hash_password("cajero123"),
                "full_name": "Cajero Principal", 
                "role": "cashier",
                "permissions": "sales,reports"
            },
            "gerente": {
                "password": self.hash_password("gerente123"),
                "full_name": "Gerente",
                "role": "manager", 
                "permissions": "all"
            }
        }
        
        self.create_login_window()
    
    def hash_password(self, password: str) -> str:
        """Genera hash seguro de contraseña"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def load_logo(self):
        """Carga tu logo personalizado"""
        try:
            from core.brand_manager import get_brand_manager
            brand_manager = get_brand_manager()
            
            # Obtener logo mediano para login
            logo_data = brand_manager.get_logo("medium")
            if logo_data:
                # Redimensionar para login
                img = logo_data.resize((150, 150), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
            
        except Exception as e:
            print(f"⚠️ No se pudo cargar logo: {e}")
        
        return None
    
    def create_login_window(self):
        """Crea la ventana de login con tu branding"""
        self.root = tk.Tk()
        self.root.title("CajaCentral POS - Iniciar Sesión")
        self.root.geometry("450x600")
        self.root.resizable(False, False)
        
        # Centrar ventana
        self.center_window()
        
        # Configurar estilo
        self.root.configure(bg='#2c3e50')
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Logo
        logo_frame = tk.Frame(main_frame, bg='#2c3e50')
        logo_frame.pack(pady=(20, 30))
        
        logo_photo = self.load_logo()
        if logo_photo:
            logo_label = tk.Label(logo_frame, image=logo_photo, bg='#2c3e50')
            logo_label.image = logo_photo  # Mantener referencia
            logo_label.pack()
        
        # Título
        title_label = tk.Label(
            main_frame,
            text="CajaCentral POS",
            font=('Segoe UI', 24, 'bold'),
            fg='white',
            bg='#2c3e50'
        )
        title_label.pack(pady=(0, 10))
        
        subtitle_label = tk.Label(
            main_frame,
            text="Sistema de Punto de Venta",
            font=('Segoe UI', 12),
            fg='#bdc3c7',
            bg='#2c3e50'
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Frame del formulario
        form_frame = tk.Frame(main_frame, bg='#34495e', relief='raised', bd=1)
        form_frame.pack(fill='x', pady=20)
        
        # Padding interno
        inner_frame = tk.Frame(form_frame, bg='#34495e')
        inner_frame.pack(fill='x', padx=30, pady=30)
        
        # Campo Usuario
        tk.Label(
            inner_frame,
            text="Usuario:",
            font=('Segoe UI', 11, 'bold'),
            fg='white',
            bg='#34495e'
        ).pack(anchor='w', pady=(0, 5))
        
        self.username_var = tk.StringVar()
        username_entry = tk.Entry(
            inner_frame,
            textvariable=self.username_var,
            font=('Segoe UI', 12),
            relief='flat',
            bd=10,
            bg='#ecf0f1',
            fg='#2c3e50'
        )
        username_entry.pack(fill='x', pady=(0, 15), ipady=8)
        username_entry.focus()
        
        # Campo Contraseña
        tk.Label(
            inner_frame,
            text="Contraseña:",
            font=('Segoe UI', 11, 'bold'),
            fg='white',
            bg='#34495e'
        ).pack(anchor='w', pady=(0, 5))
        
        self.password_var = tk.StringVar()
        password_entry = tk.Entry(
            inner_frame,
            textvariable=self.password_var,
            font=('Segoe UI', 12),
            show='*',
            relief='flat',
            bd=10,
            bg='#ecf0f1',
            fg='#2c3e50'
        )
        password_entry.pack(fill='x', pady=(0, 25), ipady=8)
        
        # Botón Login
        login_btn = tk.Button(
            inner_frame,
            text="INICIAR SESIÓN",
            font=('Segoe UI', 12, 'bold'),
            bg='#3498db',
            fg='white',
            relief='flat',
            bd=0,
            cursor='hand2',
            command=self.attempt_login
        )
        login_btn.pack(fill='x', ipady=12)
        
        # Efecto hover
        def on_enter(e):
            login_btn.configure(bg='#2980b9')
        
        def on_leave(e):
            login_btn.configure(bg='#3498db')
        
        login_btn.bind("<Enter>", on_enter)
        login_btn.bind("<Leave>", on_leave)
        
        # Bind Enter key
        self.root.bind('<Return>', lambda e: self.attempt_login())
        
        # Información de usuarios demo
        info_frame = tk.Frame(main_frame, bg='#2c3e50')
        info_frame.pack(pady=(20, 0))
        
        info_label = tk.Label(
            info_frame,
            text="👤 Usuarios de prueba:",
            font=('Segoe UI', 10, 'bold'),
            fg='#bdc3c7',
            bg='#2c3e50'
        )
        info_label.pack()
        
        users_info = tk.Label(
            info_frame,
            text="admin/admin123 • cajero/cajero123 • gerente/gerente123",
            font=('Segoe UI', 9),
            fg='#95a5a6',
            bg='#2c3e50'
        )
        users_info.pack(pady=(5, 0))
        
        # Label de intentos
        self.attempts_label = tk.Label(
            main_frame,
            text="",
            font=('Segoe UI', 9),
            fg='#e74c3c',
            bg='#2c3e50'
        )
        self.attempts_label.pack(pady=(10, 0))
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def attempt_login(self):
        """Intenta hacer login"""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Por favor ingrese usuario y contraseña")
            return
        
        # Verificar usuario
        if username in self.users:
            user_data = self.users[username]
            password_hash = self.hash_password(password)
            
            if password_hash == user_data["password"]:
                # Login exitoso
                self.current_user = {
                    "username": username,
                    "full_name": user_data["full_name"],
                    "role": user_data["role"],
                    "permissions": user_data["permissions"],
                    "login_time": datetime.now().isoformat()
                }
                
                self.login_success()
                return
        
        # Login fallido
        self.login_attempts += 1
        remaining = self.max_attempts - self.login_attempts
        
        if remaining > 0:
            self.attempts_label.configure(
                text=f"❌ Usuario o contraseña incorrectos. Intentos restantes: {remaining}"
            )
            self.password_var.set("")  # Limpiar contraseña
        else:
            messagebox.showerror(
                "Acceso Bloqueado", 
                f"Se agotaron los intentos de login.\\nReinicie la aplicación para intentar nuevamente."
            )
            self.root.quit()
    
    def login_success(self):
        """Maneja login exitoso"""
        # Guardar sesión
        self.save_session()
        
        # Mostrar mensaje de bienvenida
        messagebox.showinfo(
            "Bienvenido",
            f"¡Hola {self.current_user['full_name']}!\\n"
            f"Rol: {self.current_user['role']}\\n"
            f"Sesión iniciada correctamente"
        )
        
        # Cerrar ventana de login
        self.root.destroy()
        
        # Ejecutar callback si está definido
        if self.callback_function:
            self.callback_function(self.current_user)
    
    def save_session(self):
        """Guarda la sesión actual"""
        try:
            session_data = {
                "user": self.current_user,
                "timestamp": datetime.now().isoformat()
            }
            
            with open("data/current_session.json", "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ No se pudo guardar sesión: {e}")
    
    def run(self):
        """Ejecuta la ventana de login"""
        self.root.mainloop()
        return self.current_user

def authenticate_user(callback_function=None):
    """Función principal para autenticar usuario"""
    
    # Verificar si hay una sesión activa
    try:
        if os.path.exists("data/current_session.json"):
            with open("data/current_session.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                
            # Verificar si la sesión es reciente (menos de 24 horas)
            session_time = datetime.fromisoformat(session_data["timestamp"])
            time_diff = datetime.now() - session_time
            
            if time_diff.total_seconds() < 86400:  # 24 horas
                print(f"✅ Sesión activa: {session_data['user']['full_name']}")
                return session_data["user"]
    
    except Exception as e:
        print(f"⚠️ Error verificando sesión: {e}")
    
    # No hay sesión válida, mostrar login
    login = SecureLogin(callback_function)
    return login.run()

if __name__ == "__main__":
    def main_app(user_data):
        print(f"🚀 Iniciando aplicación principal para: {user_data['full_name']}")
        # Aquí iría tu aplicación principal
        
    result = authenticate_user(main_app)
    if result:
        print(f"✅ Usuario autenticado: {result['full_name']}")
    else:
        print("❌ Autenticación cancelada")
