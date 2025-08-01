"""
Interfaz de Usuario para Historial de Ventas
Ventana especializada para administradores con análisis y reportes
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from datetime import datetime, timedelta
import json
from modules.reports.sales_history import SalesHistoryManager

class SalesHistoryWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("📊 Historial de Ventas - Admin - Caja Central POS")
        self.window.geometry("1500x850")
        self.window.configure(bg='#f8f9fa')
        self.window.resizable(True, True)
        
        # Manager
        self.sales_manager = SalesHistoryManager()
        
        # Variables
        self.chart_canvas = None
        
        # Centrar ventana
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()
        self.load_initial_data()
        
        # Auto-actualizar cada 60 segundos
        self.auto_refresh()
    
    def setup_ui(self):
        """Crear interfaz de usuario"""
        # Header
        self.create_header()
        
        # Contenido principal con pestañas
        self.create_main_content()
    
    def create_header(self):
        """Crear header de la ventana"""
        header_frame = tk.Frame(self.window, bg='#2c3e50', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg='#2c3e50')
        header_content.pack(expand=True, fill=tk.BOTH, padx=20, pady=15)
        
        # Título
        title_label = tk.Label(header_content, text="📊 Historial de Ventas - Panel Administrativo", 
                              font=('Segoe UI', 18, 'bold'), fg='white', bg='#2c3e50')
        title_label.pack(side=tk.LEFT)
        
        # Fecha y hora actual
        datetime_label = tk.Label(header_content, 
                                 text=f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                                 font=('Segoe UI', 12), fg='#ecf0f1', bg='#2c3e50')
        datetime_label.pack(side=tk.LEFT, padx=(50, 0))
        
        # Estado de actualización
        self.update_status = tk.Label(header_content, text="✅ Actualizado", 
                                     font=('Segoe UI', 12), fg='#27ae60', bg='#2c3e50')
        self.update_status.pack(side=tk.RIGHT, padx=(0, 20))
        
        # Botón cerrar
        close_btn = tk.Button(header_content, text="❌", font=('Arial', 14),
                             bg='#e74c3c', fg='white', relief=tk.FLAT,
                             command=self.close_window, cursor='hand2')
        close_btn.pack(side=tk.RIGHT)
    
    def create_main_content(self):
        """Crear contenido principal con pestañas"""
        # Notebook principal
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Pestañas
        self.create_dashboard_tab()
        self.create_detailed_history_tab()
        self.create_analytics_tab()
        self.create_cashier_performance_tab()
        self.create_export_tab()
    
    def create_dashboard_tab(self):
        """Crear pestaña de dashboard"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="📊 Dashboard")
        
        # Filtros rápidos
        self.create_quick_filters(dashboard_frame)
        
        # Métricas principales
        self.create_main_metrics(dashboard_frame)
        
        # Gráfico de ventas por hora
        self.create_hourly_chart(dashboard_frame)
        
        # Resumen de productos más vendidos
        self.create_top_products_summary(dashboard_frame)
    
    def create_quick_filters(self, parent):
        """Crear filtros rápidos"""
        filters_frame = tk.Frame(parent, bg='white', relief=tk.RAISED, bd=1)
        filters_frame.pack(fill=tk.X, padx=10, pady=10)
        
        filters_content = tk.Frame(filters_frame, bg='white')
        filters_content.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Label(filters_content, text="📅 Período:", font=('Segoe UI', 11, 'bold'), 
                bg='white').pack(side=tk.LEFT)
        
        self.period_var = tk.StringVar(value="Hoy")
        period_combo = ttk.Combobox(filters_content, textvariable=self.period_var,
                                   values=["Hoy", "Ayer", "Esta Semana", "Este Mes", "Personalizado"], 
                                   state="readonly", width=15)
        period_combo.pack(side=tk.LEFT, padx=(10, 30))
        period_combo.bind('<<ComboboxSelected>>', self.on_period_change)
        
        tk.Label(filters_content, text="🏪 Cajero:", font=('Segoe UI', 11, 'bold'), 
                bg='white').pack(side=tk.LEFT)
        
        self.cashier_var = tk.StringVar(value="Todos")
        cashier_combo = ttk.Combobox(filters_content, textvariable=self.cashier_var,
                                    values=["Todos", "María González", "Carlos Ruiz", "Ana López"], 
                                    state="readonly", width=15)
        cashier_combo.pack(side=tk.LEFT, padx=(10, 30))
        cashier_combo.bind('<<ComboboxSelected>>', self.on_cashier_change)
        
        # Botones de acción
        refresh_btn = tk.Button(filters_content, text="🔄 Actualizar",
                               font=('Segoe UI', 10, 'bold'), bg='#3498db', fg='white',
                               relief=tk.FLAT, padx=20, command=self.refresh_data)
        refresh_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        export_btn = tk.Button(filters_content, text="📊 Exportar",
                              font=('Segoe UI', 10), bg='#27ae60', fg='white',
                              relief=tk.FLAT, padx=20, command=self.quick_export)
        export_btn.pack(side=tk.RIGHT, padx=10)
    
    def create_main_metrics(self, parent):
        """Crear métricas principales"""
        metrics_frame = tk.Frame(parent, bg='white')
        metrics_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Título
        title_frame = tk.Frame(metrics_frame, bg='#34495e')
        title_frame.pack(fill=tk.X)
        
        tk.Label(title_frame, text="📈 Métricas del Período Seleccionado", 
                font=('Segoe UI', 14, 'bold'), fg='white', bg='#34495e').pack(pady=15)
        
        # Container de métricas
        metrics_container = tk.Frame(metrics_frame, bg='white')
        metrics_container.pack(fill=tk.X, padx=20, pady=20)
        
        # Configurar grid
        for i in range(5):
            metrics_container.grid_columnconfigure(i, weight=1)
        
        # Métricas
        self.create_metric_card(metrics_container, "💰 Ingresos Totales", "₡0", "#27ae60", 0)
        self.create_metric_card(metrics_container, "🛒 Total Transacciones", "0", "#3498db", 1)
        self.create_metric_card(metrics_container, "📦 Items Vendidos", "0", "#e67e22", 2)
        self.create_metric_card(metrics_container, "💳 Ticket Promedio", "₡0", "#9b59b6", 3)
        self.create_metric_card(metrics_container, "📊 Transacciones/Hora", "0", "#1abc9c", 4)
    
    def create_metric_card(self, parent, title, value, color, column):
        """Crear tarjeta de métrica"""
        card_frame = tk.Frame(parent, bg=color, relief='flat', bd=2)
        card_frame.grid(row=0, column=column, padx=10, pady=5, sticky='ew')
        
        tk.Label(card_frame, text=title, font=('Segoe UI', 10, 'bold'),
                bg=color, fg='white', wraplength=120).pack(pady=(15, 5))
        
        metric_label = tk.Label(card_frame, text=value, font=('Segoe UI', 18, 'bold'),
                               bg=color, fg='white')
        metric_label.pack(pady=(0, 15))
        
        # Guardar referencia para actualizar
        setattr(self, f'metric_{column}', metric_label)
    
    def create_hourly_chart(self, parent):
        """Crear gráfico de ventas por hora"""
        chart_frame = tk.Frame(parent, bg='white', relief=tk.RAISED, bd=1)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Título del gráfico
        chart_title = tk.Frame(chart_frame, bg='#2c3e50')
        chart_title.pack(fill=tk.X)
        
        tk.Label(chart_title, text="📈 Ventas por Hora del Día", 
                font=('Segoe UI', 12, 'bold'), fg='white', bg='#2c3e50').pack(pady=10)
        
        # Área del gráfico (simulado con barras)
        self.chart_area = tk.Frame(chart_frame, bg='white', height=200)
        self.chart_area.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.chart_area.pack_propagate(False)
        
        # Crear gráfico simulado
        self.create_simulated_chart()
    
    def create_simulated_chart(self):
        """Crear gráfico simulado con barras"""
        # Limpiar área
        for widget in self.chart_area.winfo_children():
            widget.destroy()
        
        # Datos simulados de ventas por hora
        hourly_data = [
            ("8:00", 15000), ("9:00", 22000), ("10:00", 35000), ("11:00", 45000),
            ("12:00", 68000), ("13:00", 52000), ("14:00", 38000), ("15:00", 42000),
            ("16:00", 31000), ("17:00", 28000), ("18:00", 25000), ("19:00", 18000)
        ]
        
        max_value = max(data[1] for data in hourly_data)
        
        # Container para las barras
        bars_container = tk.Frame(self.chart_area, bg='white')
        bars_container.pack(expand=True, fill=tk.BOTH, pady=20)
        
        # Crear barras
        for i, (hour, value) in enumerate(hourly_data):
            bar_frame = tk.Frame(bars_container, bg='white')
            bar_frame.pack(side=tk.LEFT, fill=tk.Y, expand=True, padx=2)
            
            # Calcular altura de la barra
            bar_height = int((value / max_value) * 120)
            
            # Espaciador superior
            spacer = tk.Frame(bar_frame, bg='white', height=120-bar_height)
            spacer.pack(fill=tk.X)
            
            # Barra
            bar = tk.Frame(bar_frame, bg='#3498db', height=bar_height)
            bar.pack(fill=tk.X)
            
            # Valor
            tk.Label(bar_frame, text=f"₡{value//1000}k", font=('Segoe UI', 8), 
                    bg='white').pack()
            
            # Hora
            tk.Label(bar_frame, text=hour, font=('Segoe UI', 8, 'bold'), 
                    bg='white').pack()
    
    def create_top_products_summary(self, parent):
        """Crear resumen de productos más vendidos"""
        products_frame = tk.Frame(parent, bg='white', relief=tk.RAISED, bd=1)
        products_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Título
        title_frame = tk.Frame(products_frame, bg='#e67e22')
        title_frame.pack(fill=tk.X)
        
        tk.Label(title_frame, text="🏆 Top 5 Productos Más Vendidos", 
                font=('Segoe UI', 12, 'bold'), fg='white', bg='#e67e22').pack(pady=10)
        
        # Lista de productos
        products_container = tk.Frame(products_frame, bg='white')
        products_container.pack(fill=tk.X, padx=20, pady=15)
        
        # Datos simulados
        top_products = [
            ("🍚 Arroz Premium 1kg", 145, "₡362,500"),
            ("🥤 Coca Cola 600ml", 98, "₡147,000"),
            ("🍞 Pan Integral", 87, "₡104,400"),
            ("🥛 Leche Dos Pinos 1L", 76, "₡83,600"),
            ("🧀 Queso Turrialba 500g", 65, "₡195,000")
        ]
        
        for i, (product, quantity, revenue) in enumerate(top_products):
            product_frame = tk.Frame(products_container, bg='#f8f9fa', relief=tk.RAISED, bd=1)
            product_frame.pack(fill=tk.X, pady=2)
            
            # Ranking
            rank_label = tk.Label(product_frame, text=f"#{i+1}", 
                                 font=('Segoe UI', 12, 'bold'), bg='#f8f9fa', 
                                 fg='#2c3e50', width=3)
            rank_label.pack(side=tk.LEFT, padx=10, pady=5)
            
            # Producto
            product_label = tk.Label(product_frame, text=product, 
                                    font=('Segoe UI', 11), bg='#f8f9fa', anchor='w')
            product_label.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)
            
            # Cantidad
            qty_label = tk.Label(product_frame, text=f"{quantity} und.", 
                                font=('Segoe UI', 10), bg='#f8f9fa', fg='#7f8c8d')
            qty_label.pack(side=tk.RIGHT, padx=10, pady=5)
            
            # Ingresos
            revenue_label = tk.Label(product_frame, text=revenue, 
                                    font=('Segoe UI', 11, 'bold'), bg='#f8f9fa', 
                                    fg='#27ae60')
            revenue_label.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def create_detailed_history_tab(self):
        """Crear pestaña de historial detallado"""
        history_frame = ttk.Frame(self.notebook)
        self.notebook.add(history_frame, text="📋 Historial Detallado")
        
        # Filtros avanzados
        filters_frame = tk.Frame(history_frame, bg='white', relief=tk.RAISED, bd=1)
        filters_frame.pack(fill=tk.X, padx=10, pady=10)
        
        filters_content = tk.Frame(filters_frame, bg='white')
        filters_content.pack(fill=tk.X, padx=20, pady=15)
        
        # Búsqueda
        tk.Label(filters_content, text="🔍 Buscar:", font=('Segoe UI', 11), 
                bg='white').pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(filters_content, textvariable=self.search_var, 
                               font=('Segoe UI', 11), width=25)
        search_entry.pack(side=tk.LEFT, padx=(10, 20))
        search_entry.bind('<KeyRelease>', self.on_search_change)
        
        # Método de pago
        tk.Label(filters_content, text="💳 Método:", font=('Segoe UI', 11), 
                bg='white').pack(side=tk.LEFT)
        
        self.payment_filter_var = tk.StringVar(value="Todos")
        payment_combo = ttk.Combobox(filters_content, textvariable=self.payment_filter_var,
                                    values=["Todos", "Efectivo", "Tarjeta", "Transferencia"], 
                                    state="readonly", width=12)
        payment_combo.pack(side=tk.LEFT, padx=(10, 20))
        
        # Tabla de historial detallado
        table_frame = tk.Frame(history_frame, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        columns = ('fecha', 'factura', 'cajero', 'cliente', 'items', 'subtotal', 'impuestos', 'total', 'metodo_pago', 'estado')
        self.detailed_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=18)
        
        # Definir encabezados
        headers = {
            'fecha': 'Fecha/Hora',
            'factura': 'Factura #',
            'cajero': 'Cajero',
            'cliente': 'Cliente',
            'items': 'Items',
            'subtotal': 'Subtotal',
            'impuestos': 'Impuestos',
            'total': 'Total',
            'metodo_pago': 'Método Pago',
            'estado': 'Estado'
        }
        
        for col, header in headers.items():
            self.detailed_tree.heading(col, text=header)
        
        # Configurar columnas
        column_widths = {
            'fecha': 130, 'factura': 100, 'cajero': 120, 'cliente': 150, 'items': 60,
            'subtotal': 100, 'impuestos': 100, 'total': 100, 'metodo_pago': 100, 'estado': 80
        }
        
        for col, width in column_widths.items():
            self.detailed_tree.column(col, width=width, anchor='center' if col in ['items', 'estado'] else 'w')
        
        # Scrollbars
        detailed_v_scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.detailed_tree.yview)
        detailed_h_scroll = ttk.Scrollbar(table_frame, orient='horizontal', command=self.detailed_tree.xview)
        self.detailed_tree.configure(yscrollcommand=detailed_v_scroll.set, xscrollcommand=detailed_h_scroll.set)
        
        self.detailed_tree.grid(row=0, column=0, sticky='nsew')
        detailed_v_scroll.grid(row=0, column=1, sticky='ns')
        detailed_h_scroll.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Doble click para ver detalles
        self.detailed_tree.bind('<Double-1>', self.show_sale_details)
    
    def create_analytics_tab(self):
        """Crear pestaña de análisis"""
        analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(analytics_frame, text="📊 Análisis")
        
        tk.Label(analytics_frame, text="📊 Análisis Avanzado de Ventas", 
                font=('Segoe UI', 16, 'bold')).pack(pady=30)
        
        # Botones de análisis
        analysis_buttons = tk.Frame(analytics_frame)
        analysis_buttons.pack(pady=20)
        
        trend_btn = tk.Button(analysis_buttons, text="📈 Análisis de Tendencias",
                             font=('Segoe UI', 12, 'bold'), bg='#3498db', fg='white',
                             relief=tk.FLAT, padx=30, pady=15,
                             command=self.show_trend_analysis)
        trend_btn.pack(pady=10)
        
        seasonal_btn = tk.Button(analysis_buttons, text="🌟 Análisis Estacional",
                                font=('Segoe UI', 12), bg='#e67e22', fg='white',
                                relief=tk.FLAT, padx=30, pady=15,
                                command=self.show_seasonal_analysis)
        seasonal_btn.pack(pady=10)
        
        forecast_btn = tk.Button(analysis_buttons, text="🔮 Proyección de Ventas",
                                font=('Segoe UI', 12), bg='#9b59b6', fg='white',
                                relief=tk.FLAT, padx=30, pady=15,
                                command=self.show_forecast)
        forecast_btn.pack(pady=10)
    
    def create_cashier_performance_tab(self):
        """Crear pestaña de rendimiento de cajeros"""
        performance_frame = ttk.Frame(self.notebook)
        self.notebook.add(performance_frame, text="👥 Rendimiento Cajeros")
        
        # Resumen de rendimiento
        summary_frame = tk.Frame(performance_frame, bg='#3498db')
        summary_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(summary_frame, text="👥 Rendimiento de Cajeros - Período Actual", 
                font=('Segoe UI', 14, 'bold'), fg='white', bg='#3498db').pack(pady=15)
        
        # Tabla de rendimiento
        table_frame = tk.Frame(performance_frame, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        columns = ('cajero', 'transacciones', 'ingresos', 'ticket_promedio', 'items_promedio', 'tiempo_promedio', 'eficiencia')
        self.performance_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Definir encabezados
        headers = {
            'cajero': 'Cajero',
            'transacciones': 'Transacciones',
            'ingresos': 'Ingresos',
            'ticket_promedio': 'Ticket Promedio',
            'items_promedio': 'Items Promedio',
            'tiempo_promedio': 'Tiempo Promedio',
            'eficiencia': 'Eficiencia'
        }
        
        for col, header in headers.items():
            self.performance_tree.heading(col, text=header)
        
        # Configurar columnas
        perf_widths = {
            'cajero': 150, 'transacciones': 120, 'ingresos': 120, 
            'ticket_promedio': 120, 'items_promedio': 120, 
            'tiempo_promedio': 120, 'eficiencia': 100
        }
        
        for col, width in perf_widths.items():
            self.performance_tree.column(col, width=width, anchor='w' if col == 'cajero' else 'center')
        
        # Scrollbar
        perf_scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.performance_tree.yview)
        self.performance_tree.configure(yscrollcommand=perf_scrollbar.set)
        
        self.performance_tree.pack(side='left', fill='both', expand=True, padx=15)
        perf_scrollbar.pack(side='right', fill='y', padx=(0, 15))
    
    def create_export_tab(self):
        """Crear pestaña de exportación"""
        export_frame = ttk.Frame(self.notebook)
        self.notebook.add(export_frame, text="📤 Exportar")
        
        tk.Label(export_frame, text="📤 Exportar Datos de Ventas", 
                font=('Segoe UI', 16, 'bold')).pack(pady=30)
        
        # Opciones de exportación
        export_options = tk.Frame(export_frame)
        export_options.pack(pady=20)
        
        excel_btn = tk.Button(export_options, text="📊 Exportar a Excel",
                             font=('Segoe UI', 12, 'bold'), bg='#27ae60', fg='white',
                             relief=tk.FLAT, padx=40, pady=20,
                             command=self.export_to_excel)
        excel_btn.pack(pady=10)
        
        pdf_btn = tk.Button(export_options, text="📄 Exportar a PDF",
                           font=('Segoe UI', 12), bg='#e74c3c', fg='white',
                           relief=tk.FLAT, padx=40, pady=20,
                           command=self.export_to_pdf)
        pdf_btn.pack(pady=10)
        
        csv_btn = tk.Button(export_options, text="📋 Exportar a CSV",
                           font=('Segoe UI', 12), bg='#f39c12', fg='white',
                           relief=tk.FLAT, padx=40, pady=20,
                           command=self.export_to_csv)
        csv_btn.pack(pady=10)
    
    def load_initial_data(self):
        """Cargar datos iniciales"""
        def load_in_background():
            try:
                # Simular carga de datos
                self.update_status.config(text="🔄 Cargando...", fg='#f39c12')
                
                # Actualizar métricas
                self.update_main_metrics()
                
                # Cargar historial detallado
                self.load_detailed_history()
                
                # Cargar rendimiento de cajeros
                self.load_cashier_performance()
                
                self.update_status.config(text="✅ Actualizado", fg='#27ae60')
                
            except Exception as e:
                self.update_status.config(text="❌ Error", fg='#e74c3c')
                print(f"Error cargando datos: {e}")
        
        threading.Thread(target=load_in_background, daemon=True).start()
    
    def update_main_metrics(self):
        """Actualizar métricas principales"""
        # Datos simulados basados en el período seleccionado
        metrics_data = {
            "Hoy": ("₡427,350", "87", "245", "₡4,912", "12.4"),
            "Ayer": ("₡398,200", "82", "231", "₡4,856", "11.7"),
            "Esta Semana": ("₡2,847,600", "574", "1,683", "₡4,962", "13.2"),
            "Este Mes": ("₡12,384,750", "2,456", "7,234", "₡5,043", "14.1")
        }
        
        period = self.period_var.get()
        data = metrics_data.get(period, metrics_data["Hoy"])
        
        for i, value in enumerate(data):
            if hasattr(self, f'metric_{i}'):
                getattr(self, f'metric_{i}').config(text=value)
    
    def load_detailed_history(self):
        """Cargar historial detallado"""
        # Datos simulados
        sample_data = [
            ("01/08/2025 14:30", "F0001234", "María González", "Cliente General", "8", "₡13,500", "₡1,755", "₡15,255", "Efectivo", "Completado"),
            ("01/08/2025 14:15", "F0001235", "Carlos Ruiz", "Ana Pérez", "12", "₡21,200", "₡2,756", "₡23,956", "Tarjeta", "Completado"),
            ("01/08/2025 14:00", "F0001236", "María González", "Luis Mora", "5", "₡7,800", "₡1,014", "₡8,814", "Efectivo", "Completado"),
            ("01/08/2025 13:45", "F0001237", "Ana López", "José Rodríguez", "18", "₡38,500", "₡5,005", "₡43,505", "Transferencia", "Completado"),
            ("01/08/2025 13:30", "F0001238", "Carlos Ruiz", "María García", "3", "₡4,200", "₡546", "₡4,746", "Tarjeta", "Completado"),
        ]
        
        # Limpiar tabla
        for item in self.detailed_tree.get_children():
            self.detailed_tree.delete(item)
        
        # Agregar datos
        for data in sample_data:
            self.detailed_tree.insert('', 'end', values=data)
    
    def load_cashier_performance(self):
        """Cargar rendimiento de cajeros"""
        # Datos simulados
        performance_data = [
            ("María González", 45, "₡187,500", "₡4,167", "5.2", "3.2 min", "94%"),
            ("Carlos Ruiz", 32, "₡134,200", "₡4,194", "4.8", "3.8 min", "89%"),
            ("Ana López", 28, "₡112,800", "₡4,029", "4.3", "4.1 min", "85%"),
        ]
        
        # Limpiar tabla
        for item in self.performance_tree.get_children():
            self.performance_tree.delete(item)
        
        # Agregar datos
        for data in performance_data:
            self.performance_tree.insert('', 'end', values=data)
    
    def on_period_change(self, event=None):
        """Manejar cambio de período"""
        self.update_main_metrics()
        self.create_simulated_chart()
    
    def on_cashier_change(self, event=None):
        """Manejar cambio de cajero"""
        # Filtrar datos por cajero
        pass
    
    def on_search_change(self, event=None):
        """Manejar cambio en búsqueda"""
        search_term = self.search_var.get().lower()
        # Implementar filtrado en tiempo real
        pass
    
    def refresh_data(self):
        """Actualizar todos los datos"""
        self.load_initial_data()
    
    def quick_export(self):
        """Exportación rápida"""
        self.export_to_excel()
    
    def show_sale_details(self, event):
        """Mostrar detalles de venta seleccionada"""
        selected = self.detailed_tree.selection()
        if selected:
            messagebox.showinfo("Detalles de Venta", "Mostrando detalles de la venta seleccionada...")
    
    def show_trend_analysis(self):
        """Mostrar análisis de tendencias"""
        messagebox.showinfo("📈 Tendencias", "Generando análisis de tendencias de ventas...")
    
    def show_seasonal_analysis(self):
        """Mostrar análisis estacional"""
        messagebox.showinfo("🌟 Estacional", "Analizando patrones estacionales...")
    
    def show_forecast(self):
        """Mostrar proyección de ventas"""
        messagebox.showinfo("🔮 Proyección", "Generando proyección de ventas...")
    
    def export_to_excel(self):
        """Exportar a Excel"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Guardar reporte de ventas"
            )
            
            if filename:
                # Simular exportación
                messagebox.showinfo("✅ Exportado", f"Datos exportados exitosamente a:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")
    
    def export_to_pdf(self):
        """Exportar a PDF"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Guardar reporte PDF"
            )
            
            if filename:
                messagebox.showinfo("✅ Exportado", f"Reporte PDF generado:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")
    
    def export_to_csv(self):
        """Exportar a CSV"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Guardar datos CSV"
            )
            
            if filename:
                messagebox.showinfo("✅ Exportado", f"Datos CSV guardados:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")
    
    def auto_refresh(self):
        """Auto-actualizar datos cada 60 segundos"""
        def refresh():
            try:
                # Solo actualizar si la ventana sigue abierta
                if self.window.winfo_exists():
                    self.update_main_metrics()
                    self.window.after(60000, self.auto_refresh)
            except:
                pass
        
        self.window.after(60000, refresh)
    
    def close_window(self):
        """Cerrar ventana"""
        self.window.destroy()
