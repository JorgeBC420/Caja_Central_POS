"""
Interfaz principal del sistema POS - Caja Registradora Costa Rica
Versión moderna con diseño profesional similar a Eleventa
"""

import tkinter as tk
from tkinter import ttk, messagebox, Menu
import sys
import os
from datetime import datetime
import threading
from typing import Optional, Dict, Any
from PIL import Image, ImageTk

# Agregar el directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar módulos de UI
try:
    from ui.ui_login import LoginUI, mostrar_login
    from ui.ui_clients import mostrar_gestion_clientes
    from ui.ui_inventory import mostrar_gestion_inventario
    from ui.ui_kardex import mostrar_kardex
    from ui.ui_lector_barras import mostrar_lector_barras
    from ui.ui_productos import mostrar_gestion_productos
    from ui.ui_reports import mostrar_reportes
    from ui.ui_sale import SaleUI
    from ui.ui_payment import PaymentMethodsUI
    from ui.ui_users import mostrar_gestion_usuarios
    from ui.ui_apartados import mostrar_apartados
    from ui.ui_helpers import create_styled_frame, format_currency
    UI_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Advertencia: Algunos módulos UI no están disponibles: {e}")
    UI_MODULES_AVAILABLE = False

# Importar módulos del core
try:
    from core.database import ejecutar_consulta_segura, verificar_conexion_db
    from core.roles import RoleManager
    from core.licencia import LicenseManager
    from core.config import ConfigManager
    CORE_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Advertencia: Módulos del core no disponibles: {e}")
    CORE_MODULES_AVAILABLE = False

class MainApplication:
    """Aplicación principal del Sistema POS"""
    
    def __init__(self):
        self.current_user = None
        self.session_token = None
        self.logo_photo = None
        
        # Configurar la ventana principal
        self.setup_main_window()
        
        # Configurar estilos
        self.setup_modern_styles()
        
        # Mostrar login
        self.show_login()
    
    def setup_main_window(self):
        """Configura la ventana principal"""
        self.root = tk.Tk()
        self.root.title("Sistema POS - Caja Central Costa Rica")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        
        # Centrar ventana
        self.center_window()
        
        # Configurar cierre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configurar color de fondo
        self.root.configure(bg='#f8f9fa')
        
        # Ocultar inicialmente
        self.root.withdraw()
    
    def setup_modern_styles(self):
        """Configura estilos modernos para la aplicación"""
        style = ttk.Style()
        
        # Configurar tema base
        try:
            style.theme_use('clam')
        except:
            pass
        
        # Colores del tema moderno
        colors = {
            'primary': '#2c3e50',      # Azul oscuro
            'secondary': '#3498db',    # Azul
            'success': '#27ae60',      # Verde
            'warning': '#f39c12',      # Naranja
            'danger': '#e74c3c',       # Rojo
            'light': '#ecf0f1',        # Gris claro
            'dark': '#34495e',         # Gris oscuro
            'white': '#ffffff',
            'background': '#f8f9fa'
        }
        
        # Configurar estilos personalizados
        style.configure('Modern.TLabel', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), foreground=colors['primary'])
        style.configure('Subtitle.TLabel', font=('Segoe UI', 12), foreground=colors['dark'])
        style.configure('Header.TLabel', font=('Segoe UI', 14, 'bold'), foreground='white')
        
        # Botones modernos
        style.configure('Modern.TButton', font=('Segoe UI', 10), padding=(15, 8))
        style.configure('Primary.TButton', font=('Segoe UI', 10, 'bold'), 
                       background=colors['primary'], foreground='white')
        style.configure('Success.TButton', font=('Segoe UI', 10, 'bold'),
                       background=colors['success'], foreground='white')
        style.configure('Warning.TButton', font=('Segoe UI', 10, 'bold'),
                       background=colors['warning'], foreground='white')
        
        # Notebook moderno
        style.configure('Modern.TNotebook', background=colors['background'])
        style.configure('Modern.TNotebook.Tab', font=('Segoe UI', 11), padding=(20, 10))
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def show_login(self):
        """Muestra la ventana de login"""
        try:
            if UI_MODULES_AVAILABLE:
                login_ui = LoginUI(callback_function=self.on_login_success)
            else:
                self.create_basic_login()
        except Exception as e:
            messagebox.showerror("Error", f"Error mostrando login: {str(e)}")
            self.create_basic_login()
    
    def create_basic_login(self):
        """Crea un login básico si no están disponibles los módulos UI"""
        # Implementación de login básico
        login_window = tk.Toplevel()
        login_window.title("Sistema POS - Login")
        login_window.geometry("400x300")
        login_window.resizable(False, False)
        login_window.transient(self.root)
        login_window.grab_set()
        
        # Simular login exitoso para demo
        user_data = {
            'id': 1,
            'username': 'admin',
            'full_name': 'Administrador',
            'role_name': 'Administrador',
            'permissions': {'all': True}
        }
        
        login_window.destroy()
        self.on_login_success(user_data)
    
    def on_login_success(self, user_data):
        """Maneja el login exitoso"""
        self.current_user = user_data
        
        # Mostrar ventana principal
        self.root.deiconify()
        
        # Crear interfaz principal
        self.create_main_interface()
        
        # Mostrar mensaje de bienvenida
        self.show_welcome_message()
    
    def create_main_interface(self):
        """Crea la interfaz principal moderna"""
        # Limpiar ventana
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Header moderno
        self.create_modern_header()
        
        # Área principal con pestañas
        self.create_main_content()
        
        # Barra de estado
        self.create_status_bar()
        
        # Configurar atajos de teclado
        self.setup_keyboard_shortcuts()
    
    def create_modern_header(self):
        """Crea el header moderno estilo Eleventa"""
        # Frame principal del header
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=100)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)
        
        # Frame interno para contenido
        header_content = tk.Frame(header_frame, bg='#2c3e50')
        header_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # Logo y título (lado izquierdo)
        logo_frame = tk.Frame(header_content, bg='#2c3e50')
        logo_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Cargar logo
        self.load_logo(logo_frame)
        
        # Información del sistema
        info_frame = tk.Frame(logo_frame, bg='#2c3e50')
        info_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(15, 0))
        
        # Título principal
        title_label = tk.Label(info_frame, text="SISTEMA POS", 
                              font=('Segoe UI', 18, 'bold'), fg='white', bg='#2c3e50')
        title_label.pack(anchor=tk.W)
        
        # Subtítulo con URL
        subtitle_label = tk.Label(info_frame, text="PUNTO DE VENTA", 
                                 font=('Segoe UI', 10), fg='#bdc3c7', bg='#2c3e50')
        subtitle_label.pack(anchor=tk.W)
        
        url_label = tk.Label(info_frame, text="www.cajacentral.com", 
                            font=('Segoe UI', 9), fg='#95a5a6', bg='#2c3e50')
        url_label.pack(anchor=tk.W)
        
        # Información de usuario (lado derecho)
        user_frame = tk.Frame(header_content, bg='#2c3e50')
        user_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Usuario actual
        user_name = self.current_user.get('full_name', 'Usuario') if self.current_user else 'Usuario'
        user_role = self.current_user.get('role_name', 'Sin rol') if self.current_user else 'Sin rol'
        
        user_info = tk.Label(user_frame, text=f"Le atiende:", 
                            font=('Segoe UI', 9), fg='#bdc3c7', bg='#2c3e50')
        user_info.pack(anchor=tk.E)
        
        user_name_label = tk.Label(user_frame, text=user_name, 
                                  font=('Segoe UI', 12, 'bold'), fg='white', bg='#2c3e50')
        user_name_label.pack(anchor=tk.E)
        
        # Fecha y hora
        self.datetime_label = tk.Label(user_frame, text="", 
                                      font=('Segoe UI', 10), fg='#ecf0f1', bg='#2c3e50')
        self.datetime_label.pack(anchor=tk.E, pady=(5, 0))
        
        # Actualizar fecha/hora
        self.update_datetime()
    
    def load_logo(self, parent):
        """Carga el logo del sistema"""
        try:
            logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'logo.png')
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((70, 70), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label = tk.Label(parent, image=self.logo_photo, bg='#2c3e50')
                logo_label.pack(side=tk.LEFT)
            else:
                # Logo placeholder
                logo_label = tk.Label(parent, text="🏪", font=('Arial', 48), 
                                    fg='white', bg='#2c3e50')
                logo_label.pack(side=tk.LEFT)
        except Exception as e:
            print(f"Error cargando logo: {e}")
            # Logo placeholder en caso de error
            logo_label = tk.Label(parent, text="🏪", font=('Arial', 48), 
                                fg='white', bg='#2c3e50')
            logo_label.pack(side=tk.LEFT)
    
    def create_main_content(self):
        """Crea el contenido principal con navegación moderna"""
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#f8f9fa')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Barra de navegación horizontal (estilo Eleventa)
        nav_frame = tk.Frame(main_frame, bg='#ecf0f1', height=60)
        nav_frame.pack(fill=tk.X, padx=0, pady=0)
        nav_frame.pack_propagate(False)
        
        # Botones de navegación principales
        self.create_navigation_buttons(nav_frame)
        
        # Área de contenido con notebook
        content_frame = tk.Frame(main_frame, bg='#ffffff')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Notebook principal
        self.main_notebook = ttk.Notebook(content_frame, style='Modern.TNotebook')
        self.main_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Crear pestañas principales
        self.create_main_tabs()
    
    def create_navigation_buttons(self, parent):
        """Crea los botones de navegación principales"""
        nav_content = tk.Frame(parent, bg='#ecf0f1')
        nav_content.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        # Botones principales (estilo Eleventa)
        buttons_config = [
            ("🛒 F1 Ventas", self.show_ventas, '#3498db'),
            ("👥 F2 Clientes", self.show_clientes, '#27ae60'),
            ("📦 F3 Productos", self.show_productos, '#e67e22'),
            ("📊 F4 Inventario", self.show_inventario, '#9b59b6'),
            ("⚙️ Configuración", self.show_configuracion, '#95a5a6'),
            ("📋 Facturas", self.show_facturas, '#f39c12'),
            ("✂️ Corte", self.show_corte, '#e74c3c'),
            ("📈 Reportes", self.show_reportes, '#2c3e50')
        ]
        
        for i, (text, command, color) in enumerate(buttons_config):
            btn = tk.Button(nav_content, text=text, command=command,
                           font=('Segoe UI', 10, 'bold'), fg='white', bg=color,
                           relief=tk.FLAT, bd=0, padx=15, pady=8,
                           cursor='hand2')
            btn.pack(side=tk.LEFT, padx=5, pady=5)
            
            # Efectos hover
            self.add_hover_effect(btn, color)
    
    def add_hover_effect(self, button, original_color):
        """Agrega efecto hover a los botones"""
        def on_enter(e):
            button.config(bg=self.darken_color(original_color))
        
        def on_leave(e):
            button.config(bg=original_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    def darken_color(self, color):
        """Oscurece un color para el efecto hover"""
        color_map = {
            '#3498db': '#2980b9',
            '#27ae60': '#229954',
            '#e67e22': '#d35400',
            '#9b59b6': '#8e44ad',
            '#95a5a6': '#7f8c8d',
            '#f39c12': '#e67e22',
            '#e74c3c': '#c0392b',
            '#2c3e50': '#1a252f'
        }
        return color_map.get(color, color)
    
    def create_main_tabs(self):
        """Crea las pestañas principales del sistema"""
        # Pestaña de Ventas (principal)
        self.create_ventas_tab()
        
        # Pestaña de Dashboard
        self.create_dashboard_tab()
        
        # Seleccionar pestaña de ventas por defecto
        self.main_notebook.select(0)
    
    def create_ventas_tab(self):
        """Crea la pestaña de ventas principal"""
        ventas_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(ventas_frame, text="🛒 VENTA - Ticket 1")
        
        # Crear interfaz de ventas moderna
        try:
            # Usar el módulo de ventas si está disponible
            sale_ui = SaleUI(ventas_frame)
        except Exception as e:
            print(f"Error creando interfaz de ventas: {e}")
            # Interfaz de ventas básica
            self.create_basic_sales_interface(ventas_frame)
    
    def create_basic_sales_interface(self, parent):
        """Crea una interfaz de ventas básica"""
        # Layout principal horizontal
        main_layout = tk.Frame(parent, bg='white')
        main_layout.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel izquierdo - Código de producto
        left_panel = tk.Frame(main_layout, bg='white')
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Código del producto
        code_frame = tk.Frame(left_panel, bg='white')
        code_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(code_frame, text="Código del Producto:", 
                font=('Segoe UI', 11), bg='white').pack(side=tk.LEFT)
        
        self.product_code_entry = tk.Entry(code_frame, font=('Segoe UI', 12), width=20)
        self.product_code_entry.pack(side=tk.LEFT, padx=(10, 10))
        
        # Botón Agregar Producto
        add_btn = tk.Button(code_frame, text="✓ ENTER - Agregar Producto",
                           font=('Segoe UI', 10, 'bold'), bg='#27ae60', fg='white',
                           relief=tk.FLAT, padx=15, pady=5,
                           command=self.add_product_to_sale)
        add_btn.pack(side=tk.LEFT, padx=5)
        
        # Botones de funciones rápidas
        functions_frame = tk.Frame(left_panel, bg='white')
        functions_frame.pack(fill=tk.X, pady=10)
        
        function_buttons = [
            ("🔢 INS Varios", None),
            ("🎯 CTRL+Art Común", None),
            ("🔍 F10 Buscar", None),
            ("📏 F11 Mayoreo", None),
            ("📥 F7 Entradas", None),
            ("📤 F8 Salidas", None),
            ("🗑️ DEL Borrar Art", None)
        ]
        
        for text, command in function_buttons:
            btn = tk.Button(functions_frame, text=text, command=command,
                           font=('Segoe UI', 9), bg='#ecf0f1', fg='#2c3e50',
                           relief=tk.FLAT, padx=10, pady=3, cursor='hand2')
            btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Tabla de productos en venta
        self.create_sales_table(left_panel)
        
        # Panel derecho - Totales y acciones
        right_panel = tk.Frame(main_layout, bg='white', width=350)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)
        
        self.create_sales_totals_panel(right_panel)
    
    def create_sales_table(self, parent):
        """Crea la tabla de productos en venta"""
        # Frame para la tabla
        table_frame = tk.Frame(parent, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Treeview para mostrar productos
        columns = ('Código de Barras', 'Descripción del Producto', 'Precio Venta', 
                  'Cant.', 'Importe', 'Existencia', 'Descuento')
        
        self.sales_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Configurar columnas
        column_widths = {'Código de Barras': 120, 'Descripción del Producto': 300, 
                        'Precio Venta': 80, 'Cant.': 50, 'Importe': 80, 
                        'Existencia': 80, 'Descuento': 80}
        
        for col in columns:
            self.sales_tree.heading(col, text=col)
            self.sales_tree.column(col, width=column_widths.get(col, 100), minwidth=50)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.sales_tree.yview)
        self.sales_tree.configure(yscrollcommand=scrollbar.set)
        
        self.sales_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind para doble clic (editar precio)
        self.sales_tree.bind('<Double-1>', self.edit_product_price)
        
        # Ejemplo de producto
        self.sales_tree.insert('', 'end', values=(
            '4354535005459', 'DOUBLE DONG GELLY 450 MM ...', '₡30,087.69', '1', 
            '₡30,087.69', '5', '0.000%'
        ))
    
    def create_sales_totals_panel(self, parent):
        """Crea el panel de totales y acciones"""
        # Información de ticket
        ticket_info = tk.Frame(parent, bg='white')
        ticket_info.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(ticket_info, text="Ticket 2", font=('Segoe UI', 14, 'bold'), 
                bg='white', fg='#2c3e50').pack()
        
        # Productos en la venta
        products_frame = tk.LabelFrame(parent, text="1    Productos en la venta actual", 
                                      font=('Segoe UI', 10), bg='white')
        products_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Totales
        totals_frame = tk.Frame(parent, bg='white')
        totals_frame.pack(fill=tk.X, padx=10, pady=20)
        
        # Total grande
        total_label = tk.Label(totals_frame, text="₡33,999.10", 
                              font=('Segoe UI', 28, 'bold'), fg='#27ae60', bg='white')
        total_label.pack()
        
        subtotal_label = tk.Label(totals_frame, text="Subtotal: ₡30,087.69", 
                                 font=('Segoe UI', 12), fg='#7f8c8d', bg='white')
        subtotal_label.pack()
        
        # Botones de acción
        actions_frame = tk.Frame(parent, bg='white')
        actions_frame.pack(fill=tk.X, padx=10, pady=20)
        
        # Botón principal - Cobrar
        cobrar_btn = tk.Button(actions_frame, text="💰 F12 - Cobrar", 
                              font=('Segoe UI', 14, 'bold'), bg='#27ae60', fg='white',
                              relief=tk.FLAT, pady=15, command=self.process_payment)
        cobrar_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Botones secundarios
        secondary_buttons = [
            ("📄 Reimprimir Último Ticket", None),
            ("💳 Ventas del día o Corte", None)
        ]
        
        for text, command in secondary_buttons:
            btn = tk.Button(actions_frame, text=text, command=command,
                           font=('Segoe UI', 10), bg='#3498db', fg='white',
                           relief=tk.FLAT, pady=8)
            btn.pack(fill=tk.X, pady=2)
        
        # Información adicional
        info_frame = tk.Frame(parent, bg='white')
        info_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        date_time = datetime.now().strftime("%d - %b - %Y  %H:%M am")
        tk.Label(info_frame, text=date_time, font=('Segoe UI', 9), 
                fg='#7f8c8d', bg='white').pack(side=tk.RIGHT)
    
    def create_dashboard_tab(self):
        """Crea la pestaña de dashboard"""
        dashboard_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(dashboard_frame, text="📊 Dashboard")
        
        # Título del dashboard
        title_frame = tk.Frame(dashboard_frame, bg='white')
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(title_frame, text="Dashboard - Resumen Ejecutivo", 
                font=('Segoe UI', 18, 'bold'), fg='#2c3e50', bg='white').pack()
        
        # Panel de métricas
        metrics_frame = tk.Frame(dashboard_frame, bg='white')
        metrics_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Crear tarjetas de métricas
        metrics_data = [
            ("Ventas Hoy", "₡125,450.00", "#27ae60"),
            ("Transacciones", "45", "#3498db"), 
            ("Productos Vendidos", "127", "#e67e22"),
            ("Ticket Promedio", "₡2,787.78", "#9b59b6")
        ]
        
        for title, value, color in metrics_data:
            self.create_metric_card(metrics_frame, title, value, color)
    
    def create_metric_card(self, parent, title, value, color):
        """Crea una tarjeta de métrica"""
        card = tk.Frame(parent, bg='white', relief=tk.RAISED, bd=1)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(card, text=title, font=('Segoe UI', 10), 
                fg='#7f8c8d', bg='white').pack(pady=(10, 5))
        tk.Label(card, text=value, font=('Segoe UI', 16, 'bold'), 
                fg=color, bg='white').pack(pady=(0, 10))
    
    def create_status_bar(self):
        """Crea la barra de estado"""
        status_frame = tk.Frame(self.root, bg='#34495e', height=25)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        # Estado de conexión
        tk.Label(status_frame, text="🟢 Conectado", font=('Segoe UI', 9), 
                fg='white', bg='#34495e').pack(side=tk.LEFT, padx=10)
        
        # Información adicional
        tk.Label(status_frame, text=f"Usuario: {self.current_user.get('username', 'N/A')}", 
                font=('Segoe UI', 9), fg='white', bg='#34495e').pack(side=tk.RIGHT, padx=10)
    
    def setup_keyboard_shortcuts(self):
        """Configura los atajos de teclado"""
        self.root.bind('<F1>', lambda e: self.show_ventas())
        self.root.bind('<F2>', lambda e: self.show_clientes())
        self.root.bind('<F3>', lambda e: self.show_productos())
        self.root.bind('<F4>', lambda e: self.show_inventario())
        self.root.bind('<F12>', lambda e: self.process_payment())
        self.root.bind('<Control-q>', lambda e: self.on_closing())
        
        # Focus en entrada de código de producto
        if hasattr(self, 'product_code_entry'):
            self.product_code_entry.focus_set()
            self.product_code_entry.bind('<Return>', lambda e: self.add_product_to_sale())
    
    def update_datetime(self):
        """Actualiza la fecha y hora en el header"""
        try:
            now = datetime.now()
            formatted_time = now.strftime("%d/%m/%Y %H:%M:%S")
            if hasattr(self, 'datetime_label'):
                self.datetime_label.config(text=formatted_time)
            self.root.after(1000, self.update_datetime)
        except:
            pass
    
    def show_welcome_message(self):
        """Muestra mensaje de bienvenida"""
        user_name = self.current_user.get('full_name', 'Usuario') if self.current_user else 'Usuario'
        messagebox.showinfo("Bienvenido", f"¡Bienvenido/a {user_name}!\n\nSistema POS iniciado correctamente.")
    
    # Métodos de navegación
    def show_ventas(self):
        """Muestra la pestaña de ventas"""
        self.main_notebook.select(0)
        if hasattr(self, 'product_code_entry'):
            self.product_code_entry.focus_set()
    
    def show_clientes(self):
        """Muestra gestión de clientes"""
        try:
            mostrar_gestion_clientes(self.root)
        except:
            messagebox.showinfo("Módulo", "Gestión de Clientes")
    
    def show_productos(self):
        """Muestra gestión de productos"""
        try:
            mostrar_gestion_productos(self.root)
        except:
            messagebox.showinfo("Módulo", "Gestión de Productos")
    
    def show_inventario(self):
        """Muestra gestión de inventario"""
        try:
            mostrar_gestion_inventario(self.root)
        except:
            messagebox.showinfo("Módulo", "Gestión de Inventario")
    
    def show_configuracion(self):
        """Muestra configuración"""
        messagebox.showinfo("Módulo", "Configuración del Sistema")
    
    def show_facturas(self):
        """Muestra facturas"""
        messagebox.showinfo("Módulo", "Gestión de Facturas")
    
    def show_corte(self):
        """Muestra corte de caja"""
        messagebox.showinfo("Módulo", "Corte de Caja")
    
    def show_reportes(self):
        """Muestra reportes"""
        try:
            mostrar_reportes(self.root)
        except:
            messagebox.showinfo("Módulo", "Reportes del Sistema")
    
    # Métodos de funcionalidad
    def add_product_to_sale(self):
        """Agrega un producto a la venta"""
        code = self.product_code_entry.get().strip()
        if code:
            # Aquí iría la lógica para buscar el producto y agregarlo
            messagebox.showinfo("Producto", f"Agregando producto con código: {code}")
            self.product_code_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Código", "Ingrese un código de producto")
    
    def edit_product_price(self, event):
        """Edita el precio de un producto con doble clic"""
        selection = self.sales_tree.selection()
        if selection:
            item = self.sales_tree.item(selection[0])
            product_name = item['values'][1]  # Descripción del producto
            current_price = item['values'][2]  # Precio actual
            
            # Ventana de edición de precio
            self.show_price_edit_dialog(product_name, current_price, selection[0])
    
    def show_price_edit_dialog(self, product_name, current_price, item_id):
        """Muestra diálogo para editar precio"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Precio")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrar diálogo
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (200)
        y = (dialog.winfo_screenheight() // 2) - (150)
        dialog.geometry(f"400x300+{x}+{y}")
        
        # Contenido del diálogo
        main_frame = tk.Frame(dialog, bg='white', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        tk.Label(main_frame, text="Cambiar Precio", font=('Segoe UI', 14, 'bold'), 
                bg='white', fg='#2c3e50').pack(pady=(0, 20))
        
        # Información del producto
        tk.Label(main_frame, text=f"Producto: {product_name[:50]}...", 
                font=('Segoe UI', 10), bg='white').pack(pady=5)
        
        # Precio actual
        tk.Label(main_frame, text=f"Precio Normal: {current_price}", 
                font=('Segoe UI', 12, 'bold'), bg='white', fg='#27ae60').pack(pady=(10, 5))
        
        # Entrada de nuevo precio
        tk.Label(main_frame, text="Nuevo Precio:", font=('Segoe UI', 10), bg='white').pack(pady=(20, 5))
        
        price_entry = tk.Entry(main_frame, font=('Segoe UI', 14), width=15, justify='center')
        price_entry.pack(pady=5)
        price_entry.focus_set()
        
        # Campo de descuento
        tk.Label(main_frame, text="Descuento:", font=('Segoe UI', 10), bg='white').pack(pady=(10, 5))
        
        discount_entry = tk.Entry(main_frame, font=('Segoe UI', 12), width=10, justify='center')
        discount_entry.pack(pady=5)
        discount_entry.insert(0, "0.000")
        
        # Botones
        buttons_frame = tk.Frame(main_frame, bg='white')
        buttons_frame.pack(pady=20)
        
        def apply_price_change():
            try:
                new_price = float(price_entry.get().replace('₡', '').replace(',', ''))
                discount = float(discount_entry.get())
                
                # Actualizar el item en la tabla
                current_values = list(self.sales_tree.item(item_id)['values'])
                current_values[2] = f"₡{new_price:,.2f}"  # Nuevo precio
                current_values[4] = f"₡{new_price:,.2f}"  # Nuevo importe (asumiendo cantidad 1)
                current_values[6] = f"{discount:.3f}%"    # Descuento
                
                self.sales_tree.item(item_id, values=current_values)
                
                dialog.destroy()
                messagebox.showinfo("Precio Actualizado", "El precio ha sido actualizado correctamente")
                
            except ValueError:
                messagebox.showerror("Error", "Ingrese un precio válido")
        
        def cancel_change():
            dialog.destroy()
        
        # Botones
        tk.Button(buttons_frame, text="✓ Cambiar precio", command=apply_price_change,
                 font=('Segoe UI', 10, 'bold'), bg='#27ae60', fg='white', 
                 relief=tk.FLAT, padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(buttons_frame, text="✗ Cancelar", command=cancel_change,
                 font=('Segoe UI', 10, 'bold'), bg='#e74c3c', fg='white', 
                 relief=tk.FLAT, padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key
        price_entry.bind('<Return>', lambda e: apply_price_change())
    
    def process_payment(self):
        """Procesa el pago de la venta"""
        try:
            # Abrir interfaz de pago
            payment_window = tk.Toplevel(self.root)
            payment_window.title("Procesar Pago")
            payment_window.geometry("600x500")
            payment_window.transient(self.root)
            payment_window.grab_set()
            
            # Crear interfaz de pago
            PaymentMethodsUI(payment_window)
            
        except Exception as e:
            print(f"Error en proceso de pago: {e}")
            messagebox.showinfo("Pago", "Procesando pago de ₡33,999.10")
    
    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        if messagebox.askyesno("Salir", "¿Está seguro que desea salir del sistema?"):
            self.root.quit()
    
    def run(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()

def main():
    """Función principal"""
    try:
        app = MainApplication()
        app.run()
    except Exception as e:
        print(f"Error iniciando aplicación: {e}")
        messagebox.showerror("Error Fatal", f"No se pudo iniciar la aplicación:\n{str(e)}")

if __name__ == "__main__":
    main()
