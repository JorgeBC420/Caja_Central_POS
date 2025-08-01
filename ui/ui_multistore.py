"""
Interfaz de Usuario para Sistema Multi-Tienda
Ventana principal para gestión de múltiples sucursales e inventario conectado
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime, timedelta
import json
from modules.multistore.store_manager import MultiStoreManager
from modules.reports.sales_history import SalesHistoryManager

class MultiStoreWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("🏪 Gestión Multi-Tienda - Caja Central POS")
        self.window.geometry("1400x800")
        self.window.configure(bg='#f0f0f0')
        self.window.resizable(True, True)
        
        # Managers
        self.store_manager = MultiStoreManager()
        self.sales_manager = SalesHistoryManager()
        
        # Centrar ventana
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()
        self.load_data()
        
        # Auto-actualizar cada 30 segundos
        self.auto_refresh()
    
    def setup_ui(self):
        """Crear interfaz de usuario"""
        # Header
        self.create_header()
        
        # Notebook para pestañas
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Pestañas
        self.create_dashboard_tab()
        self.create_inventory_tab()
        self.create_transfers_tab()
        self.create_sales_history_tab()
        self.create_stores_config_tab()
    
    def create_header(self):
        """Crear header de la ventana"""
        header_frame = tk.Frame(self.window, bg='#2c3e50', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg='#2c3e50')
        header_content.pack(expand=True, fill=tk.BOTH, padx=20, pady=15)
        
        # Título
        title_label = tk.Label(header_content, text="🏪 Sistema Multi-Tienda", 
                              font=('Segoe UI', 18, 'bold'), fg='white', bg='#2c3e50')
        title_label.pack(side=tk.LEFT)
        
        # Estado de sincronización
        self.sync_status = tk.Label(header_content, text="🔄 Sincronizando...", 
                                   font=('Segoe UI', 12), fg='#f39c12', bg='#2c3e50')
        self.sync_status.pack(side=tk.RIGHT, padx=(0, 20))
        
        # Botón cerrar
        close_btn = tk.Button(header_content, text="❌", font=('Arial', 14),
                             bg='#e74c3c', fg='white', relief=tk.FLAT,
                             command=self.close_window, cursor='hand2')
        close_btn.pack(side=tk.RIGHT)
    
    def create_dashboard_tab(self):
        """Crear pestaña de dashboard"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="📊 Dashboard")
        
        # Frame principal con scroll
        canvas = tk.Canvas(dashboard_frame, bg='white')
        scrollbar = ttk.Scrollbar(dashboard_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Tarjetas de resumen
        self.create_summary_cards(scrollable_frame)
        
        # Gráficos de rendimiento por tienda
        self.create_store_performance_section(scrollable_frame)
        
        # Alertas de stock
        self.create_stock_alerts_section(scrollable_frame)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
    
    def create_summary_cards(self, parent):
        """Crear tarjetas de resumen"""
        cards_frame = tk.Frame(parent, bg='white')
        cards_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Título
        tk.Label(cards_frame, text="📈 Resumen General", 
                font=('Segoe UI', 16, 'bold'), bg='white').pack(anchor=tk.W, pady=(0, 15))
        
        # Container de tarjetas
        cards_container = tk.Frame(cards_frame, bg='white')
        cards_container.pack(fill=tk.X)
        
        # Configurar grid
        for i in range(4):
            cards_container.grid_columnconfigure(i, weight=1)
        
        # Tarjetas
        self.create_summary_card(cards_container, "🏪 Tiendas Activas", "3", "#3498db", 0)
        self.create_summary_card(cards_container, "📦 Productos Totales", "1,247", "#27ae60", 1)
        self.create_summary_card(cards_container, "⚠️ Stock Bajo", "23", "#e74c3c", 2)
        self.create_summary_card(cards_container, "🔄 Transferencias Pendientes", "5", "#f39c12", 3)
    
    def create_summary_card(self, parent, title, value, color, column):
        """Crear tarjeta de resumen individual"""
        card_frame = tk.Frame(parent, bg=color, relief='flat', bd=2)
        card_frame.grid(row=0, column=column, padx=10, pady=5, sticky='ew')
        
        tk.Label(card_frame, text=title, font=('Segoe UI', 11, 'bold'),
                bg=color, fg='white').pack(pady=(15, 5))
        
        tk.Label(card_frame, text=value, font=('Segoe UI', 20, 'bold'),
                bg=color, fg='white').pack(pady=(0, 15))
    
    def create_store_performance_section(self, parent):
        """Crear sección de rendimiento por tienda"""
        perf_frame = tk.Frame(parent, bg='white')
        perf_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(perf_frame, text="🏪 Rendimiento por Tienda", 
                font=('Segoe UI', 16, 'bold'), bg='white').pack(anchor=tk.W, pady=(0, 15))
        
        # Tabla de rendimiento
        columns = ('tienda', 'ventas_hoy', 'ingresos', 'productos_vendidos', 'stock_disponible')
        self.performance_tree = ttk.Treeview(perf_frame, columns=columns, show='headings', height=8)
        
        # Definir encabezados
        self.performance_tree.heading('tienda', text='Tienda')
        self.performance_tree.heading('ventas_hoy', text='Ventas Hoy')
        self.performance_tree.heading('ingresos', text='Ingresos')
        self.performance_tree.heading('productos_vendidos', text='Productos Vendidos')
        self.performance_tree.heading('stock_disponible', text='Stock Disponible')
        
        # Configurar columnas
        self.performance_tree.column('tienda', width=200, anchor='w')
        self.performance_tree.column('ventas_hoy', width=100, anchor='center')
        self.performance_tree.column('ingresos', width=120, anchor='e')
        self.performance_tree.column('productos_vendidos', width=150, anchor='center')
        self.performance_tree.column('stock_disponible', width=120, anchor='center')
        
        # Scrollbar para la tabla
        perf_scrollbar = ttk.Scrollbar(perf_frame, orient='vertical', command=self.performance_tree.yview)
        self.performance_tree.configure(yscrollcommand=perf_scrollbar.set)
        
        self.performance_tree.pack(side='left', fill='both', expand=True)
        perf_scrollbar.pack(side='right', fill='y')
    
    def create_stock_alerts_section(self, parent):
        """Crear sección de alertas de stock"""
        alerts_frame = tk.Frame(parent, bg='white')
        alerts_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(alerts_frame, text="⚠️ Alertas de Stock Crítico", 
                font=('Segoe UI', 16, 'bold'), bg='white', fg='#e74c3c').pack(anchor=tk.W, pady=(0, 15))
        
        # Lista de alertas
        self.alerts_listbox = tk.Listbox(alerts_frame, height=6, font=('Segoe UI', 10))
        alerts_scrollbar = ttk.Scrollbar(alerts_frame, orient='vertical', command=self.alerts_listbox.yview)
        self.alerts_listbox.configure(yscrollcommand=alerts_scrollbar.set)
        
        self.alerts_listbox.pack(side='left', fill='both', expand=True)
        alerts_scrollbar.pack(side='right', fill='y')
    
    def create_inventory_tab(self):
        """Crear pestaña de inventario consolidado"""
        inventory_frame = ttk.Frame(self.notebook)
        self.notebook.add(inventory_frame, text="📦 Inventario Consolidado")
        
        # Herramientas
        tools_frame = tk.Frame(inventory_frame, bg='white')
        tools_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(tools_frame, text="Buscar producto:", font=('Segoe UI', 11), bg='white').pack(side=tk.LEFT)
        
        self.search_product_var = tk.StringVar()
        search_entry = tk.Entry(tools_frame, textvariable=self.search_product_var, 
                               font=('Segoe UI', 11), width=30)
        search_entry.pack(side=tk.LEFT, padx=(10, 0))
        search_entry.bind('<KeyRelease>', self.search_consolidated_inventory)
        
        search_btn = tk.Button(tools_frame, text="🔍 Buscar", 
                              font=('Segoe UI', 10, 'bold'), bg='#3498db', fg='white',
                              relief=tk.FLAT, padx=15, command=self.search_consolidated_inventory)
        search_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Tabla de inventario consolidado
        table_frame = tk.Frame(inventory_frame, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        columns = ('producto', 'codigo', 'total_stock', 'tienda_principal', 'sucursal_2', 'sucursal_3', 'precio')
        self.inventory_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        # Definir encabezados
        headers = {
            'producto': 'Producto',
            'codigo': 'Código',
            'total_stock': 'Stock Total',
            'tienda_principal': 'Tienda Principal',
            'sucursal_2': 'Sucursal Norte',
            'sucursal_3': 'Sucursal Sur',
            'precio': 'Precio'
        }
        
        for col, header in headers.items():
            self.inventory_tree.heading(col, text=header)
        
        # Configurar columnas
        self.inventory_tree.column('producto', width=250, anchor='w')
        self.inventory_tree.column('codigo', width=100, anchor='center')
        self.inventory_tree.column('total_stock', width=100, anchor='center')
        self.inventory_tree.column('tienda_principal', width=120, anchor='center')
        self.inventory_tree.column('sucursal_2', width=120, anchor='center')
        self.inventory_tree.column('sucursal_3', width=120, anchor='center')
        self.inventory_tree.column('precio', width=100, anchor='e')
        
        # Scrollbars
        inventory_v_scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.inventory_tree.yview)
        inventory_h_scroll = ttk.Scrollbar(table_frame, orient='horizontal', command=self.inventory_tree.xview)
        self.inventory_tree.configure(yscrollcommand=inventory_v_scroll.set, xscrollcommand=inventory_h_scroll.set)
        
        self.inventory_tree.grid(row=0, column=0, sticky='nsew')
        inventory_v_scroll.grid(row=0, column=1, sticky='ns')
        inventory_h_scroll.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
    
    def create_transfers_tab(self):
        """Crear pestaña de transferencias"""
        transfers_frame = ttk.Frame(self.notebook)
        self.notebook.add(transfers_frame, text="🔄 Transferencias")
        
        # Botones de acción
        actions_frame = tk.Frame(transfers_frame, bg='white')
        actions_frame.pack(fill=tk.X, padx=15, pady=10)
        
        new_transfer_btn = tk.Button(actions_frame, text="➕ Nueva Transferencia",
                                    font=('Segoe UI', 11, 'bold'), bg='#27ae60', fg='white',
                                    relief=tk.FLAT, padx=20, pady=8,
                                    command=self.new_transfer_dialog)
        new_transfer_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        refresh_btn = tk.Button(actions_frame, text="🔄 Actualizar",
                               font=('Segoe UI', 11), bg='#3498db', fg='white',
                               relief=tk.FLAT, padx=20, pady=8,
                               command=self.refresh_transfers)
        refresh_btn.pack(side=tk.LEFT)
        
        # Tabla de transferencias
        table_frame = tk.Frame(transfers_frame, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        columns = ('id', 'producto', 'cantidad', 'origen', 'destino', 'estado', 'fecha', 'solicitante')
        self.transfers_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=18)
        
        # Definir encabezados
        headers = {
            'id': 'ID',
            'producto': 'Producto',
            'cantidad': 'Cantidad',
            'origen': 'Origen',
            'destino': 'Destino',
            'estado': 'Estado',
            'fecha': 'Fecha',
            'solicitante': 'Solicitante'
        }
        
        for col, header in headers.items():
            self.transfers_tree.heading(col, text=header)
        
        # Configurar columnas
        self.transfers_tree.column('id', width=80, anchor='center')
        self.transfers_tree.column('producto', width=200, anchor='w')
        self.transfers_tree.column('cantidad', width=80, anchor='center')
        self.transfers_tree.column('origen', width=120, anchor='center')
        self.transfers_tree.column('destino', width=120, anchor='center')
        self.transfers_tree.column('estado', width=100, anchor='center')
        self.transfers_tree.column('fecha', width=120, anchor='center')
        self.transfers_tree.column('solicitante', width=120, anchor='center')
        
        # Scrollbar
        transfers_scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.transfers_tree.yview)
        self.transfers_tree.configure(yscrollcommand=transfers_scrollbar.set)
        
        self.transfers_tree.pack(side='left', fill='both', expand=True)
        transfers_scrollbar.pack(side='right', fill='y')
        
        # Botones de acción en transferencias
        transfer_actions = tk.Frame(transfers_frame, bg='white')
        transfer_actions.pack(fill=tk.X, padx=15, pady=10)
        
        approve_btn = tk.Button(transfer_actions, text="✅ Aprobar",
                               font=('Segoe UI', 10, 'bold'), bg='#27ae60', fg='white',
                               relief=tk.FLAT, padx=15, command=self.approve_transfer)
        approve_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_btn = tk.Button(transfer_actions, text="❌ Cancelar",
                              font=('Segoe UI', 10), bg='#e74c3c', fg='white',
                              relief=tk.FLAT, padx=15, command=self.cancel_transfer)
        cancel_btn.pack(side=tk.LEFT)
    
    def create_sales_history_tab(self):
        """Crear pestaña de historial de ventas"""
        history_frame = ttk.Frame(self.notebook)
        self.notebook.add(history_frame, text="📊 Historial de Ventas")
        
        # Filtros
        filters_frame = tk.Frame(history_frame, bg='white')
        filters_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(filters_frame, text="Período:", font=('Segoe UI', 11), bg='white').pack(side=tk.LEFT)
        
        self.period_var = tk.StringVar(value="30 días")
        period_combo = ttk.Combobox(filters_frame, textvariable=self.period_var,
                                   values=["Hoy", "7 días", "30 días", "90 días"], 
                                   state="readonly", width=15)
        period_combo.pack(side=tk.LEFT, padx=(10, 20))
        
        tk.Label(filters_frame, text="Tienda:", font=('Segoe UI', 11), bg='white').pack(side=tk.LEFT)
        
        self.store_filter_var = tk.StringVar(value="Todas")
        store_combo = ttk.Combobox(filters_frame, textvariable=self.store_filter_var,
                                  values=["Todas", "Principal", "Norte", "Sur"], 
                                  state="readonly", width=15)
        store_combo.pack(side=tk.LEFT, padx=(10, 20))
        
        update_btn = tk.Button(filters_frame, text="🔄 Actualizar",
                              font=('Segoe UI', 10, 'bold'), bg='#3498db', fg='white',
                              relief=tk.FLAT, padx=15, command=self.update_sales_history)
        update_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        export_btn = tk.Button(filters_frame, text="📊 Exportar Excel",
                              font=('Segoe UI', 10), bg='#27ae60', fg='white',
                              relief=tk.FLAT, padx=15, command=self.export_sales_history)
        export_btn.pack(side=tk.RIGHT)
        
        # Estadísticas rápidas
        stats_frame = tk.Frame(history_frame, bg='#f8f9fa', relief=tk.RAISED, bd=1)
        stats_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        stats_container = tk.Frame(stats_frame, bg='#f8f9fa')
        stats_container.pack(fill=tk.X, padx=20, pady=15)
        
        # Configurar grid para estadísticas
        for i in range(4):
            stats_container.grid_columnconfigure(i, weight=1)
        
        self.create_stat_display(stats_container, "💰 Ingresos Totales", "₡0", 0)
        self.create_stat_display(stats_container, "🛒 Transacciones", "0", 1)
        self.create_stat_display(stats_container, "📦 Items Vendidos", "0", 2)
        self.create_stat_display(stats_container, "💳 Ticket Promedio", "₡0", 3)
        
        # Tabla de historial
        table_frame = tk.Frame(history_frame, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        columns = ('fecha', 'tienda', 'cajero', 'cliente', 'total', 'items', 'metodo_pago')
        self.history_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Definir encabezados
        headers = {
            'fecha': 'Fecha/Hora',
            'tienda': 'Tienda',
            'cajero': 'Cajero',
            'cliente': 'Cliente',
            'total': 'Total',
            'items': 'Items',
            'metodo_pago': 'Método Pago'
        }
        
        for col, header in headers.items():
            self.history_tree.heading(col, text=header)
        
        # Configurar columnas
        self.history_tree.column('fecha', width=130, anchor='center')
        self.history_tree.column('tienda', width=120, anchor='center')
        self.history_tree.column('cajero', width=120, anchor='w')
        self.history_tree.column('cliente', width=150, anchor='w')
        self.history_tree.column('total', width=100, anchor='e')
        self.history_tree.column('items', width=60, anchor='center')
        self.history_tree.column('metodo_pago', width=100, anchor='center')
        
        # Scrollbar
        history_scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        
        self.history_tree.pack(side='left', fill='both', expand=True)
        history_scrollbar.pack(side='right', fill='y')
    
    def create_stat_display(self, parent, label, value, column):
        """Crear display de estadística"""
        stat_frame = tk.Frame(parent, bg='#f8f9fa')
        stat_frame.grid(row=0, column=column, padx=10, sticky='ew')
        
        tk.Label(stat_frame, text=label, font=('Segoe UI', 10), 
                bg='#f8f9fa', fg='#6c757d').pack()
        
        setattr(self, f'stat_{column}', tk.Label(stat_frame, text=value, 
                                                font=('Segoe UI', 14, 'bold'), 
                                                bg='#f8f9fa', fg='#2c3e50'))
        getattr(self, f'stat_{column}').pack()
    
    def create_stores_config_tab(self):
        """Crear pestaña de configuración de tiendas"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="⚙️ Configuración")
        
        tk.Label(config_frame, text="Configuración de Tiendas", 
                font=('Segoe UI', 16, 'bold')).pack(pady=20)
        
        # Botones de configuración
        buttons_frame = tk.Frame(config_frame)
        buttons_frame.pack(pady=20)
        
        add_store_btn = tk.Button(buttons_frame, text="➕ Agregar Tienda",
                                 font=('Segoe UI', 12, 'bold'), bg='#27ae60', fg='white',
                                 relief=tk.FLAT, padx=30, pady=15,
                                 command=self.add_store_dialog)
        add_store_btn.pack(side=tk.LEFT, padx=10)
        
        sync_config_btn = tk.Button(buttons_frame, text="🔄 Configurar Sincronización",
                                   font=('Segoe UI', 12), bg='#3498db', fg='white',
                                   relief=tk.FLAT, padx=30, pady=15,
                                   command=self.sync_config_dialog)
        sync_config_btn.pack(side=tk.LEFT, padx=10)
    
    def load_data(self):
        """Cargar datos iniciales"""
        def load_in_background():
            try:
                # Cargar datos de ejemplo
                self.load_performance_data()
                self.load_inventory_data()
                self.load_transfers_data()
                self.load_sales_history_data()
                
                # Actualizar estado de sincronización
                self.sync_status.config(text="✅ Sincronizado", fg='#27ae60')
                
            except Exception as e:
                self.sync_status.config(text="❌ Error", fg='#e74c3c')
                print(f"Error cargando datos: {e}")
        
        threading.Thread(target=load_in_background, daemon=True).start()
    
    def load_performance_data(self):
        """Cargar datos de rendimiento"""
        # Datos de ejemplo
        sample_data = [
            ("Tienda Principal", 45, "₡187,500", 128, 856),
            ("Sucursal Norte", 32, "₡134,200", 89, 643),
            ("Sucursal Sur", 28, "₡112,800", 76, 521),
        ]
        
        # Limpiar tabla
        for item in self.performance_tree.get_children():
            self.performance_tree.delete(item)
        
        # Agregar datos
        for data in sample_data:
            self.performance_tree.insert('', 'end', values=data)
    
    def load_inventory_data(self):
        """Cargar datos de inventario consolidado"""
        # Datos de ejemplo
        sample_inventory = [
            ("Arroz Premium 1kg", "12345678", 450, 150, 200, 100, "₡2,500"),
            ("Frijoles Negros 500g", "12345679", 380, 200, 120, 60, "₡1,800"),
            ("Aceite Vegetal 1L", "12345680", 95, 15, 50, 30, "₡3,200"),
            ("Azúcar Blanca 1kg", "12345681", 720, 300, 250, 170, "₡1,200"),
            ("Café Molido 250g", "12345682", 88, 8, 45, 35, "₡4,500"),
        ]
        
        # Limpiar tabla
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # Agregar datos
        for data in sample_inventory:
            self.inventory_tree.insert('', 'end', values=data)
    
    def load_transfers_data(self):
        """Cargar datos de transferencias"""
        # Datos de ejemplo
        sample_transfers = [
            ("TR001", "Arroz Premium 1kg", 50, "Principal", "Norte", "Pendiente", "01/08/2025", "Admin"),
            ("TR002", "Aceite Vegetal 1L", 25, "Norte", "Sur", "En Tránsito", "31/07/2025", "María G."),
            ("TR003", "Café Molido 250g", 15, "Sur", "Principal", "Completado", "30/07/2025", "Carlos R."),
        ]
        
        # Limpiar tabla
        for item in self.transfers_tree.get_children():
            self.transfers_tree.delete(item)
        
        # Agregar datos
        for data in sample_transfers:
            self.transfers_tree.insert('', 'end', values=data)
    
    def load_sales_history_data(self):
        """Cargar historial de ventas"""
        # Actualizar estadísticas
        self.stat_0.config(text="₡434,500")
        self.stat_1.config(text="105")
        self.stat_2.config(text="293")
        self.stat_3.config(text="₡4,138")
        
        # Datos de ejemplo
        sample_sales = [
            ("01/08/2025 14:30", "Principal", "María González", "Cliente General", "₡15,750", "8", "Efectivo"),
            ("01/08/2025 14:15", "Norte", "Carlos Ruiz", "Ana Pérez", "₡23,400", "12", "Tarjeta"),
            ("01/08/2025 14:00", "Sur", "Lucia Mora", "Cliente General", "₡8,900", "5", "Efectivo"),
            ("01/08/2025 13:45", "Principal", "María González", "José Rodríguez", "₡45,200", "18", "Transferencia"),
        ]
        
        # Limpiar tabla
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Agregar datos
        for data in sample_sales:
            self.history_tree.insert('', 'end', values=data)
    
    def search_consolidated_inventory(self, event=None):
        """Buscar en inventario consolidado"""
        search_term = self.search_product_var.get().lower()
        # Implementar búsqueda real aquí
        messagebox.showinfo("Búsqueda", f"Buscando: {search_term}")
    
    def new_transfer_dialog(self):
        """Diálogo para nueva transferencia"""
        messagebox.showinfo("Nueva Transferencia", "Diálogo de nueva transferencia en desarrollo")
    
    def refresh_transfers(self):
        """Actualizar transferencias"""
        self.load_transfers_data()
        messagebox.showinfo("✅ Actualizado", "Transferencias actualizadas")
    
    def approve_transfer(self):
        """Aprobar transferencia seleccionada"""
        selected = self.transfers_tree.selection()
        if not selected:
            messagebox.showwarning("Selección", "Seleccione una transferencia para aprobar")
            return
        
        messagebox.showinfo("✅ Aprobado", "Transferencia aprobada exitosamente")
    
    def cancel_transfer(self):
        """Cancelar transferencia seleccionada"""
        selected = self.transfers_tree.selection()
        if not selected:
            messagebox.showwarning("Selección", "Seleccione una transferencia para cancelar")
            return
        
        if messagebox.askyesno("Confirmar", "¿Está seguro de cancelar esta transferencia?"):
            messagebox.showinfo("❌ Cancelado", "Transferencia cancelada")
    
    def update_sales_history(self):
        """Actualizar historial de ventas"""
        self.load_sales_history_data()
    
    def export_sales_history(self):
        """Exportar historial a Excel"""
        messagebox.showinfo("📊 Exportar", "Exportando historial de ventas a Excel...")
    
    def add_store_dialog(self):
        """Diálogo para agregar nueva tienda"""
        messagebox.showinfo("Agregar Tienda", "Diálogo de nueva tienda en desarrollo")
    
    def sync_config_dialog(self):
        """Diálogo de configuración de sincronización"""
        messagebox.showinfo("Configuración", "Configuración de sincronización en desarrollo")
    
    def auto_refresh(self):
        """Auto-actualizar datos cada 30 segundos"""
        def refresh():
            try:
                # Simular actualización
                self.sync_status.config(text="🔄 Actualizando...", fg='#f39c12')
                self.window.after(2000, lambda: self.sync_status.config(text="✅ Sincronizado", fg='#27ae60'))
            except:
                pass
            
            # Programar próxima actualización
            self.window.after(30000, self.auto_refresh)
        
        self.window.after(1000, refresh)
    
    def close_window(self):
        """Cerrar ventana"""
        self.store_manager.stop_sync()  # Detener sincronización
        self.window.destroy()
