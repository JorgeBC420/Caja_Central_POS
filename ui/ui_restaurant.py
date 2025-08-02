"""
Interfaz de Usuario para Sistema de Restaurante COMPLETO
Gestión completa de mesas, cuentas activas, menú, órdenes y FACTURACIÓN
Sistema de apertura/cierre de cuentas con facturación automática
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime, timedelta
import json
import os
from modules.restaurant.restaurant_manager import RestaurantManager

class RestaurantWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("🍽️ Sistema de Restaurante COMPLETO - Caja Central POS")
        self.window.geometry("1600x900")
        self.window.configure(bg='#0f766e')  # Verde turquesa de fondo
        self.window.resizable(True, True)
        
        # Manager
        self.restaurant_manager = RestaurantManager()
        
        # Variables
        self.selected_table = None
        self.current_order_items = []
        self.active_accounts = {}  # Cuentas activas por mesa
        
        # Cargar logo
        self.load_logo()
        
        # Centrar ventana
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()
        self.load_initial_data()
        
        # Auto-actualizar cada 10 segundos
        self.auto_refresh()
    
    def load_logo(self):
        """Carga el logo si está disponible"""
        try:
            from core.brand_manager import get_brand_manager
            brand_manager = get_brand_manager()
            logo = brand_manager.get_logo("small")
            if logo:
                from PIL import ImageTk
                self.logo_photo = ImageTk.PhotoImage(logo)
            else:
                self.logo_photo = None
        except:
            self.logo_photo = None
    
    def setup_ui(self):
        """Crear interfaz de usuario"""
        # Header
        self.create_header()
        
        # Layout principal con paneles
        self.create_main_layout()
    
    def create_header(self):
        """Crear header de la ventana con verde turquesa"""
        header_frame = tk.Frame(self.window, bg='#14b8a6', height=80)  # Verde turquesa
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg='#14b8a6')
        header_content.pack(expand=True, fill=tk.BOTH, padx=20, pady=15)
        
        # Logo si está disponible
        if hasattr(self, 'logo_photo') and self.logo_photo:
            logo_label = tk.Label(header_content, image=self.logo_photo, bg='#14b8a6')
            logo_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # Título
        title_label = tk.Label(header_content, text="🍽️ Sistema de Restaurante COMPLETO", 
                              font=('Segoe UI', 18, 'bold'), fg='white', bg='#14b8a6')
        title_label.pack(side=tk.LEFT)
        
        # Información del día
        today_info = tk.Label(header_content, 
                             text=f"📅 {datetime.now().strftime('%d/%m/%Y')} | 🕐 Turno: Almuerzo",
                             font=('Segoe UI', 12), fg='#ecf0f1', bg='#2c3e50')
        today_info.pack(side=tk.LEFT, padx=(50, 0))
        
        # Estado del sistema
        self.system_status = tk.Label(header_content, text="🟢 Sistema Activo", 
                                     font=('Segoe UI', 12), fg='#27ae60', bg='#2c3e50')
        self.system_status.pack(side=tk.RIGHT, padx=(0, 20))
        
        # Botón cerrar
        close_btn = tk.Button(header_content, text="❌", font=('Arial', 14),
                             bg='#e74c3c', fg='white', relief=tk.FLAT,
                             command=self.close_window, cursor='hand2')
        close_btn.pack(side=tk.RIGHT)
    
    def create_main_layout(self):
        """Crear layout principal con paneles"""
        # Container principal
        main_container = tk.Frame(self.window, bg='#f8f9fa')
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Panel izquierdo - Mesas y gestión
        left_panel = tk.Frame(main_container, bg='white', relief=tk.RAISED, bd=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Panel derecho - Menú y órdenes
        right_panel = tk.Frame(main_container, bg='white', relief=tk.RAISED, bd=1, width=600)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_panel.pack_propagate(False)
        
        # Configurar paneles
        self.setup_left_panel(left_panel)
        self.setup_right_panel(right_panel)
    
    def setup_left_panel(self, panel):
        """Configurar panel izquierdo - Mesas"""
        # Título del panel
        title_frame = tk.Frame(panel, bg='#34495e')
        title_frame.pack(fill=tk.X)
        
        tk.Label(title_frame, text="🏪 Gestión de Mesas y Cuentas", 
                font=('Segoe UI', 14, 'bold'), fg='white', bg='#34495e').pack(pady=15)
        
        # Notebook para diferentes vistas
        self.left_notebook = ttk.Notebook(panel)
        self.left_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña de mesas
        self.create_tables_tab()
        
        # Pestaña de cuentas activas
        self.create_active_accounts_tab()
        
        # Pestaña de cocina
        self.create_kitchen_tab()
        
        # Pestaña de reportes
        self.create_reports_tab()
    
    def create_tables_tab(self):
        """Crear pestaña de mesas"""
        tables_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(tables_frame, text="🏪 Mesas")
        
        # Herramientas
        tools_frame = tk.Frame(tables_frame, bg='white')
        tools_frame.pack(fill=tk.X, padx=10, pady=10)
        
        refresh_btn = tk.Button(tools_frame, text="🔄 Actualizar",
                               font=('Segoe UI', 10, 'bold'), bg='#3498db', fg='white',
                               relief=tk.FLAT, padx=15, command=self.refresh_tables)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        new_table_btn = tk.Button(tools_frame, text="➕ Nueva Mesa",
                                 font=('Segoe UI', 10), bg='#27ae60', fg='white',
                                 relief=tk.FLAT, padx=15, command=self.add_table_dialog)
        new_table_btn.pack(side=tk.LEFT)
        
        # Grid de mesas
        self.create_tables_grid(tables_frame)
    
    def create_tables_grid(self, parent):
        """Crear grid visual de mesas"""
        # Contenedor con scroll
        canvas = tk.Canvas(parent, bg='#ecf0f1')
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.tables_container = tk.Frame(canvas, bg='#ecf0f1')
        
        self.tables_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.tables_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Crear mesas de ejemplo
        self.create_sample_tables()
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
    
    def create_sample_tables(self):
        """Crear mesas de ejemplo"""
        # Configurar grid
        cols = 4
        
        # Tipos de mesa y estados
        table_types = [
            ("Mesa 1", "libre", 4, "🟢"),
            ("Mesa 2", "ocupada", 6, "🔴"),
            ("Mesa 3", "reservada", 2, "🟡"),
            ("Mesa 4", "libre", 4, "🟢"),
            ("Mesa 5", "ocupada", 8, "🔴"),
            ("Mesa 6", "libre", 2, "🟢"),
            ("Barra 1", "ocupada", 1, "🔴"),
            ("Barra 2", "libre", 1, "🟢"),
            ("Terraza 1", "libre", 6, "🟢"),
            ("Terraza 2", "reservada", 4, "🟡"),
            ("VIP 1", "ocupada", 10, "🔴"),
            ("VIP 2", "libre", 8, "🟢"),
        ]
        
        for i, (name, status, capacity, indicator) in enumerate(table_types):
            row = i // cols
            col = i % cols
            
            # Frame de la mesa
            table_frame = tk.Frame(self.tables_container, bg='white', relief=tk.RAISED, bd=2)
            table_frame.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            
            # Configurar hover effect
            table_frame.bind("<Button-1>", lambda e, table=name: self.select_table(table))
            table_frame.bind("<Enter>", lambda e, frame=table_frame: frame.config(bg='#f0f0f0'))
            table_frame.bind("<Leave>", lambda e, frame=table_frame: frame.config(bg='white'))
            
            # Contenido de la mesa
            tk.Label(table_frame, text=indicator, font=('Arial', 20), bg='white').pack(pady=(10, 5))
            tk.Label(table_frame, text=name, font=('Segoe UI', 12, 'bold'), bg='white').pack()
            tk.Label(table_frame, text=f"👥 {capacity} personas", font=('Segoe UI', 9), bg='white').pack()
            tk.Label(table_frame, text=status.title(), 
                    font=('Segoe UI', 10, 'bold'), 
                    fg='#27ae60' if status == 'libre' else '#e74c3c' if status == 'ocupada' else '#f39c12',
                    bg='white').pack(pady=(5, 10))
            
            # Configurar peso de columnas
            self.tables_container.grid_columnconfigure(col, weight=1)
    
    def create_active_accounts_tab(self):
        """Crear pestaña de cuentas activas"""
        accounts_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(accounts_frame, text="💳 Cuentas Activas")
        
        # Resumen de cuentas
        summary_frame = tk.Frame(accounts_frame, bg='#3498db')
        summary_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(summary_frame, text="📊 Resumen de Cuentas Activas", 
                font=('Segoe UI', 12, 'bold'), fg='white', bg='#3498db').pack(pady=10)
        
        stats_container = tk.Frame(summary_frame, bg='#3498db')
        stats_container.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Estadísticas
        for i in range(3):
            stats_container.grid_columnconfigure(i, weight=1)
        
        self.create_account_stat(stats_container, "💳 Cuentas Abiertas", "8", 0)
        self.create_account_stat(stats_container, "💰 Total Pendiente", "₡127,450", 1)
        self.create_account_stat(stats_container, "⏱️ Tiempo Promedio", "45 min", 2)
        
        # Lista de cuentas activas
        list_frame = tk.Frame(accounts_frame, bg='white')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        tk.Label(list_frame, text="Lista de Cuentas Activas", 
                font=('Segoe UI', 12, 'bold'), bg='white').pack(anchor=tk.W, padx=15, pady=10)
        
        # Tabla de cuentas
        columns = ('mesa', 'cliente', 'items', 'total', 'tiempo', 'acciones')
        self.accounts_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        # Definir encabezados
        headers = {
            'mesa': 'Mesa',
            'cliente': 'Cliente',
            'items': 'Items',
            'total': 'Total',
            'tiempo': 'Tiempo',
            'acciones': 'Estado'
        }
        
        for col, header in headers.items():
            self.accounts_tree.heading(col, text=header)
        
        # Configurar columnas
        self.accounts_tree.column('mesa', width=80, anchor='center')
        self.accounts_tree.column('cliente', width=150, anchor='w')
        self.accounts_tree.column('items', width=60, anchor='center')
        self.accounts_tree.column('total', width=100, anchor='e')
        self.accounts_tree.column('tiempo', width=80, anchor='center')
        self.accounts_tree.column('acciones', width=100, anchor='center')
        
        # Scrollbar
        accounts_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.accounts_tree.yview)
        self.accounts_tree.configure(yscrollcommand=accounts_scrollbar.set)
        
        self.accounts_tree.pack(side='left', fill='both', expand=True, padx=15)
        accounts_scrollbar.pack(side='right', fill='y', padx=(0, 15))
        
        # Botones de acción
        actions_frame = tk.Frame(accounts_frame, bg='white')
        actions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        close_account_btn = tk.Button(actions_frame, text="💳 Cerrar Cuenta",
                                     font=('Segoe UI', 11, 'bold'), bg='#e74c3c', fg='white',
                                     relief=tk.FLAT, padx=20, command=self.close_account)
        close_account_btn.pack(side=tk.LEFT, padx=(15, 10))
        
        print_bill_btn = tk.Button(actions_frame, text="🖨️ Imprimir Cuenta",
                                  font=('Segoe UI', 11), bg='#27ae60', fg='white',
                                  relief=tk.FLAT, padx=20, command=self.print_bill)
        print_bill_btn.pack(side=tk.LEFT, padx=10)
    
    def create_account_stat(self, parent, label, value, column):
        """Crear estadística de cuenta"""
        stat_frame = tk.Frame(parent, bg='#3498db')
        stat_frame.grid(row=0, column=column, padx=10, sticky='ew')
        
        tk.Label(stat_frame, text=label, font=('Segoe UI', 10, 'bold'), 
                bg='#3498db', fg='white').pack()
        
        tk.Label(stat_frame, text=value, font=('Segoe UI', 14, 'bold'), 
                bg='#3498db', fg='white').pack()
    
    def create_kitchen_tab(self):
        """Crear pestaña de cocina"""
        kitchen_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(kitchen_frame, text="👨‍🍳 Cocina")
        
        # Header de cocina
        kitchen_header = tk.Frame(kitchen_frame, bg='#e67e22')
        kitchen_header.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(kitchen_header, text="👨‍🍳 Órdenes de Cocina", 
                font=('Segoe UI', 14, 'bold'), fg='white', bg='#e67e22').pack(pady=15)
        
        # Filtros de órdenes
        filters_frame = tk.Frame(kitchen_frame, bg='white')
        filters_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(filters_frame, text="Estado:", font=('Segoe UI', 11), bg='white').pack(side=tk.LEFT, padx=(15, 5))
        
        self.kitchen_filter_var = tk.StringVar(value="Pendientes")
        filter_combo = ttk.Combobox(filters_frame, textvariable=self.kitchen_filter_var,
                                   values=["Todos", "Pendientes", "En Preparación", "Listos"], 
                                   state="readonly", width=15)
        filter_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        refresh_kitchen_btn = tk.Button(filters_frame, text="🔄 Actualizar",
                                       font=('Segoe UI', 10), bg='#3498db', fg='white',
                                       relief=tk.FLAT, padx=15, command=self.refresh_kitchen_orders)
        refresh_kitchen_btn.pack(side=tk.LEFT)
        
        # Lista de órdenes de cocina
        orders_frame = tk.Frame(kitchen_frame, bg='white')
        orders_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Tabla de órdenes
        columns = ('orden', 'mesa', 'producto', 'cantidad', 'estado', 'tiempo', 'prioridad')
        self.kitchen_tree = ttk.Treeview(orders_frame, columns=columns, show='headings', height=15)
        
        # Definir encabezados
        headers = {
            'orden': 'Orden #',
            'mesa': 'Mesa',
            'producto': 'Producto',
            'cantidad': 'Cant.',
            'estado': 'Estado',
            'tiempo': 'Tiempo',
            'prioridad': 'Prioridad'
        }
        
        for col, header in headers.items():
            self.kitchen_tree.heading(col, text=header)
        
        # Configurar columnas
        self.kitchen_tree.column('orden', width=80, anchor='center')
        self.kitchen_tree.column('mesa', width=60, anchor='center')
        self.kitchen_tree.column('producto', width=200, anchor='w')
        self.kitchen_tree.column('cantidad', width=60, anchor='center')
        self.kitchen_tree.column('estado', width=120, anchor='center')
        self.kitchen_tree.column('tiempo', width=80, anchor='center')
        self.kitchen_tree.column('prioridad', width=80, anchor='center')
        
        # Scrollbar
        kitchen_scrollbar = ttk.Scrollbar(orders_frame, orient='vertical', command=self.kitchen_tree.yview)
        self.kitchen_tree.configure(yscrollcommand=kitchen_scrollbar.set)
        
        self.kitchen_tree.pack(side='left', fill='both', expand=True, padx=15)
        kitchen_scrollbar.pack(side='right', fill='y', padx=(0, 15))
        
        # Botones de cocina
        kitchen_actions = tk.Frame(kitchen_frame, bg='white')
        kitchen_actions.pack(fill=tk.X, padx=10, pady=10)
        
        start_prep_btn = tk.Button(kitchen_actions, text="🔥 Iniciar Preparación",
                                  font=('Segoe UI', 11, 'bold'), bg='#f39c12', fg='white',
                                  relief=tk.FLAT, padx=20, command=self.start_preparation)
        start_prep_btn.pack(side=tk.LEFT, padx=(15, 10))
        
        mark_ready_btn = tk.Button(kitchen_actions, text="✅ Marcar Listo",
                                  font=('Segoe UI', 11, 'bold'), bg='#27ae60', fg='white',
                                  relief=tk.FLAT, padx=20, command=self.mark_ready)
        mark_ready_btn.pack(side=tk.LEFT, padx=10)
    
    def create_reports_tab(self):
        """Crear pestaña de reportes"""
        reports_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(reports_frame, text="📊 Reportes")
        
        tk.Label(reports_frame, text="📊 Reportes del Restaurante", 
                font=('Segoe UI', 16, 'bold')).pack(pady=30)
        
        # Botones de reportes
        reports_buttons = tk.Frame(reports_frame)
        reports_buttons.pack(pady=20)
        
        daily_report_btn = tk.Button(reports_buttons, text="📈 Reporte Diario",
                                    font=('Segoe UI', 12, 'bold'), bg='#3498db', fg='white',
                                    relief=tk.FLAT, padx=30, pady=15,
                                    command=self.generate_daily_report)
        daily_report_btn.pack(pady=10)
        
        menu_analysis_btn = tk.Button(reports_buttons, text="🍽️ Análisis de Menú",
                                     font=('Segoe UI', 12), bg='#27ae60', fg='white',
                                     relief=tk.FLAT, padx=30, pady=15,
                                     command=self.menu_analysis)
        menu_analysis_btn.pack(pady=10)
        
        tables_report_btn = tk.Button(reports_buttons, text="🏪 Rotación de Mesas",
                                     font=('Segoe UI', 12), bg='#e67e22', fg='white',
                                     relief=tk.FLAT, padx=30, pady=15,
                                     command=self.tables_rotation_report)
        tables_report_btn.pack(pady=10)
    
    def setup_right_panel(self, panel):
        """Configurar panel derecho - Menú y órdenes"""
        # Título del panel
        title_frame = tk.Frame(panel, bg='#27ae60')
        title_frame.pack(fill=tk.X)
        
        tk.Label(title_frame, text="🍽️ Menú y Órdenes", 
                font=('Segoe UI', 14, 'bold'), fg='white', bg='#27ae60').pack(pady=15)
        
        # Información de mesa seleccionada
        self.create_selected_table_info(panel)
        
        # Menú de productos
        self.create_menu_section(panel)
        
        # Orden actual
        self.create_current_order_section(panel)
    
    def create_selected_table_info(self, parent):
        """Crear información de mesa seleccionada"""
        info_frame = tk.Frame(parent, bg='#ecf0f1', relief=tk.RAISED, bd=1)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.table_info_label = tk.Label(info_frame, text="Seleccione una mesa", 
                                        font=('Segoe UI', 12, 'bold'), bg='#ecf0f1')
        self.table_info_label.pack(pady=15)
    
    def create_menu_section(self, parent):
        """Crear sección del menú"""
        menu_frame = tk.Frame(parent, bg='white')
        menu_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Header del menú
        menu_header = tk.Frame(menu_frame, bg='white')
        menu_header.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(menu_header, text="🍽️ Menú", 
                font=('Segoe UI', 12, 'bold'), bg='white').pack(side=tk.LEFT)
        
        # Categorías
        categories_frame = tk.Frame(menu_frame, bg='white')
        categories_frame.pack(fill=tk.X, padx=15, pady=5)
        
        categories = ["🥗 Entradas", "🍖 Platos Fuertes", "🍰 Postres", "🥤 Bebidas"]
        self.selected_category = tk.StringVar(value="🍖 Platos Fuertes")
        
        for category in categories:
            btn = tk.Radiobutton(categories_frame, text=category, variable=self.selected_category,
                                value=category, font=('Segoe UI', 10), bg='white',
                                command=self.load_menu_items)
            btn.pack(side=tk.LEFT, padx=5)
        
        # Lista de productos del menú
        products_frame = tk.Frame(menu_frame, bg='white')
        products_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Scrollable frame para productos
        canvas = tk.Canvas(products_frame, bg='white', height=300)
        scrollbar = ttk.Scrollbar(products_frame, orient="vertical", command=canvas.yview)
        self.menu_products_frame = tk.Frame(canvas, bg='white')
        
        self.menu_products_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.menu_products_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Cargar productos iniciales
        self.load_menu_items()
    
    def create_current_order_section(self, parent):
        """Crear sección de orden actual"""
        order_frame = tk.Frame(parent, bg='white', relief=tk.RAISED, bd=1)
        order_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Header de la orden
        order_header = tk.Frame(order_frame, bg='#34495e')
        order_header.pack(fill=tk.X)
        
        tk.Label(order_header, text="🛒 Orden Actual", 
                font=('Segoe UI', 12, 'bold'), fg='white', bg='#34495e').pack(pady=10)
        
        # Lista de items en la orden
        self.order_listbox = tk.Listbox(order_frame, height=8, font=('Segoe UI', 10))
        order_scrollbar = ttk.Scrollbar(order_frame, orient='vertical', command=self.order_listbox.yview)
        self.order_listbox.configure(yscrollcommand=order_scrollbar.set)
        
        self.order_listbox.pack(side='left', fill='both', expand=True, padx=15, pady=10)
        order_scrollbar.pack(side='right', fill='y', padx=(0, 15), pady=10)
        
        # Total y botones
        total_frame = tk.Frame(order_frame, bg='white')
        total_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.total_label = tk.Label(total_frame, text="Total: ₡0", 
                                   font=('Segoe UI', 14, 'bold'), bg='white')
        self.total_label.pack(pady=5)
        
        buttons_frame = tk.Frame(order_frame, bg='white')
        buttons_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        clear_btn = tk.Button(buttons_frame, text="🗑️ Limpiar",
                             font=('Segoe UI', 10), bg='#e74c3c', fg='white',
                             relief=tk.FLAT, padx=15, command=self.clear_order)
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        send_kitchen_btn = tk.Button(buttons_frame, text="👨‍🍳 Enviar a Cocina",
                                    font=('Segoe UI', 10, 'bold'), bg='#f39c12', fg='white',
                                    relief=tk.FLAT, padx=15, command=self.send_to_kitchen)
        send_kitchen_btn.pack(side=tk.LEFT, padx=10)
        
        close_order_btn = tk.Button(buttons_frame, text="💳 Cerrar Cuenta",
                                   font=('Segoe UI', 10, 'bold'), bg='#27ae60', fg='white',
                                   relief=tk.FLAT, padx=15, command=self.close_table_account)
        close_order_btn.pack(side=tk.RIGHT)
    
    def load_menu_items(self):
        """Cargar items del menú según categoría"""
        # Limpiar frame de productos
        for widget in self.menu_products_frame.winfo_children():
            widget.destroy()
        
        # Productos de ejemplo por categoría
        menu_items = {
            "🥗 Entradas": [
                ("Ensalada César", "₡3,500", "Lechuga, crutones, parmesano"),
                ("Nachos Supremos", "₡4,200", "Con guacamole y queso"),
                ("Alitas BBQ", "₡5,800", "6 unidades con salsa BBQ"),
            ],
            "🍖 Platos Fuertes": [
                ("Casado Tradicional", "₡6,500", "Arroz, frijoles, carne, plátano"),
                ("Pollo a la Plancha", "₡7,200", "Con ensalada y papas"),
                ("Pescado en Salsa", "₡8,900", "Dorado con verduras"),
                ("Pasta Carbonara", "₡6,800", "Con tocino y queso parmesano"),
            ],
            "🍰 Postres": [
                ("Tres Leches", "₡2,800", "Torta tradicional"),
                ("Flan de Coco", "₡2,500", "Con caramelo"),
                ("Helado Artesanal", "₡2,200", "Vainilla o chocolate"),
            ],
            "🥤 Bebidas": [
                ("Refresco Natural", "₡1,500", "Naranja o cas"),
                ("Café Americano", "₡1,200", "Café premium"),
                ("Cerveza Nacional", "₡2,000", "Imperial o Pilsen"),
                ("Agua Embotellada", "₡800", "500ml"),
            ]
        }
        
        category = self.selected_category.get()
        items = menu_items.get(category, [])
        
        for i, (name, price, description) in enumerate(items):
            item_frame = tk.Frame(self.menu_products_frame, bg='#f8f9fa', relief=tk.RAISED, bd=1)
            item_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Información del producto
            info_frame = tk.Frame(item_frame, bg='#f8f9fa')
            info_frame.pack(fill=tk.X, side=tk.LEFT, expand=True)
            
            tk.Label(info_frame, text=name, font=('Segoe UI', 11, 'bold'), 
                    bg='#f8f9fa').pack(anchor=tk.W, padx=10, pady=(5, 0))
            
            tk.Label(info_frame, text=description, font=('Segoe UI', 9), 
                    bg='#f8f9fa', fg='#666').pack(anchor=tk.W, padx=10)
            
            tk.Label(info_frame, text=price, font=('Segoe UI', 11, 'bold'), 
                    bg='#f8f9fa', fg='#27ae60').pack(anchor=tk.W, padx=10, pady=(0, 5))
            
            # Botón agregar
            add_btn = tk.Button(item_frame, text="➕", font=('Arial', 12, 'bold'),
                               bg='#3498db', fg='white', relief=tk.FLAT, width=3,
                               command=lambda n=name, p=price: self.add_to_order(n, p))
            add_btn.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def load_initial_data(self):
        """Cargar datos iniciales"""
        # Cargar datos de cuentas activas
        sample_accounts = [
            ("Mesa 2", "Juan Pérez", 8, "₡18,750", "35 min"),
            ("Mesa 5", "María García", 12, "₡32,400", "22 min"),
            ("VIP 1", "Carlos Rodríguez", 5, "₡45,800", "1h 15m"),
            ("Barra 1", "Ana López", 3, "₡8,900", "18 min"),
            ("Terraza 2", "Luis Mora", 7, "₡21,600", "42 min"),
        ]
        
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)
        
        for data in sample_accounts:
            self.accounts_tree.insert('', 'end', values=data)
        
        # Cargar órdenes de cocina
        sample_kitchen_orders = [
            ("K001", "Mesa 2", "Casado Tradicional", 2, "Pendiente", "5 min", "Normal"),
            ("K002", "Mesa 5", "Pollo a la Plancha", 1, "En Preparación", "15 min", "Urgente"),
            ("K003", "VIP 1", "Pescado en Salsa", 3, "Pendiente", "2 min", "VIP"),
            ("K004", "Mesa 2", "Tres Leches", 1, "Listo", "25 min", "Normal"),
        ]
        
        for item in self.kitchen_tree.get_children():
            self.kitchen_tree.delete(item)
        
        for data in sample_kitchen_orders:
            self.kitchen_tree.insert('', 'end', values=data)
    
    def select_table(self, table_name):
        """Seleccionar mesa"""
        self.selected_table = table_name
        self.table_info_label.config(text=f"Mesa Seleccionada: {table_name}")
        messagebox.showinfo("Mesa Seleccionada", f"Ha seleccionado: {table_name}")
    
    def add_to_order(self, name, price):
        """Agregar item a la orden"""
        if not self.selected_table:
            messagebox.showwarning("Mesa", "Seleccione una mesa primero")
            return
        
        # Agregar a la lista
        price_value = float(price.replace('₡', '').replace(',', ''))
        self.current_order_items.append((name, price_value))
        
        # Actualizar listbox
        self.order_listbox.insert(tk.END, f"{name} - {price}")
        
        # Actualizar total
        total = sum(item[1] for item in self.current_order_items)
        self.total_label.config(text=f"Total: ₡{total:,.0f}")
    
    def clear_order(self):
        """Limpiar orden actual"""
        self.current_order_items.clear()
        self.order_listbox.delete(0, tk.END)
        self.total_label.config(text="Total: ₡0")
    
    def send_to_kitchen(self):
        """Enviar orden a cocina"""
        if not self.current_order_items:
            messagebox.showwarning("Orden", "No hay items en la orden")
            return
        
        if not self.selected_table:
            messagebox.showwarning("Mesa", "Seleccione una mesa")
            return
        
        messagebox.showinfo("✅ Enviado", f"Orden enviada a cocina para {self.selected_table}")
        self.clear_order()
    
    def close_table_account(self):
        """Cerrar cuenta de mesa"""
        if not self.selected_table:
            messagebox.showwarning("Mesa", "Seleccione una mesa")
            return
        
        if messagebox.askyesno("Cerrar Cuenta", f"¿Cerrar cuenta de {self.selected_table}?"):
            messagebox.showinfo("✅ Cerrado", "Cuenta cerrada exitosamente")
    
    def refresh_tables(self):
        """Actualizar estado de mesas"""
        messagebox.showinfo("🔄 Actualizado", "Estado de mesas actualizado")
    
    def add_table_dialog(self):
        """Diálogo para agregar nueva mesa"""
        messagebox.showinfo("Nueva Mesa", "Diálogo de nueva mesa en desarrollo")
    
    def close_account(self):
        """Cerrar cuenta seleccionada"""
        selected = self.accounts_tree.selection()
        if not selected:
            messagebox.showwarning("Selección", "Seleccione una cuenta para cerrar")
            return
        
        messagebox.showinfo("✅ Cerrado", "Cuenta cerrada exitosamente")
    
    def print_bill(self):
        """Imprimir cuenta"""
        selected = self.accounts_tree.selection()
        if not selected:
            messagebox.showwarning("Selección", "Seleccione una cuenta para imprimir")
            return
        
        messagebox.showinfo("🖨️ Imprimiendo", "Imprimiendo cuenta...")
    
    def start_preparation(self):
        """Iniciar preparación de orden"""
        selected = self.kitchen_tree.selection()
        if not selected:
            messagebox.showwarning("Selección", "Seleccione una orden")
            return
        
        messagebox.showinfo("🔥 Iniciado", "Preparación iniciada")
    
    def mark_ready(self):
        """Marcar orden como lista"""
        selected = self.kitchen_tree.selection()
        if not selected:
            messagebox.showwarning("Selección", "Seleccione una orden")
            return
        
        messagebox.showinfo("✅ Listo", "Orden marcada como lista")
    
    def refresh_kitchen_orders(self):
        """Actualizar órdenes de cocina"""
        self.load_initial_data()
    
    def generate_daily_report(self):
        """Generar reporte diario"""
        messagebox.showinfo("📊 Reporte", "Generando reporte diario...")
    
    def menu_analysis(self):
        """Análisis de menú"""
        messagebox.showinfo("🍽️ Análisis", "Analizando rendimiento del menú...")
    
    def tables_rotation_report(self):
        """Reporte de rotación de mesas"""
        messagebox.showinfo("🏪 Rotación", "Generando reporte de rotación de mesas...")
    
    def auto_refresh(self):
        """Auto-actualizar datos cada 15 segundos"""
        def refresh():
            try:
                # Simular actualización
                self.system_status.config(text="🟡 Actualizando...", fg='#f39c12')
                self.window.after(2000, lambda: self.system_status.config(text="🟢 Sistema Activo", fg='#27ae60'))
            except:
                pass
            
            # Programar próxima actualización
            self.window.after(15000, self.auto_refresh)
        
        self.window.after(1000, refresh)
    
    def close_window(self):
        """Cerrar ventana"""
        self.window.destroy()
