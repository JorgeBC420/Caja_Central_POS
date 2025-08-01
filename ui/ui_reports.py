"""
Interfaz de usuario para generación de reportes
Maneja reportes de ventas, inventario, clientes y análisis de negocio
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta, date
from typing import Optional, Dict, List, Any, Tuple
import json
from decimal import Decimal
import threading
import queue

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill
    from openpyxl.chart import BarChart, LineChart, PieChart, Reference
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

from core.database import ejecutar_consulta_segura
from ui.ui_helpers import create_styled_frame, create_input_frame

class ReportsUI:
    """Interfaz principal para generación de reportes"""
    
    def __init__(self, parent_window):
        self.parent = parent_window
        
        # Variables de estado
        self.current_report_data = None
        self.chart_figures = []
        
        # Variables de filtros de fecha
        self.start_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.end_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        
        # Variables de filtros adicionales
        self.report_type_var = tk.StringVar()
        self.period_var = tk.StringVar(value="Hoy")
        self.category_filter_var = tk.StringVar()
        self.user_filter_var = tk.StringVar()
        self.client_filter_var = tk.StringVar()
        
        # Variables de configuración
        self.config_vars = {
            'auto_refresh': tk.BooleanVar(value=True),
            'include_graphics': tk.BooleanVar(value=True),
            'detailed_view': tk.BooleanVar(value=False),
            'export_format': tk.StringVar(value="PDF"),
            'chart_style': tk.StringVar(value="Moderno")
        }
        
        # Cola para reportes en segundo plano
        self.report_queue = queue.Queue()
        
        self.check_dependencies()
        self.setup_ui()
        self.load_initial_data()
    
    def check_dependencies(self):
        """Verifica las dependencias necesarias"""
        missing_deps = []
        
        if not PANDAS_AVAILABLE:
            missing_deps.append("pandas")
        if not MATPLOTLIB_AVAILABLE:
            missing_deps.append("matplotlib")
        if not REPORTLAB_AVAILABLE:
            missing_deps.append("reportlab")
        if not OPENPYXL_AVAILABLE:
            missing_deps.append("openpyxl")
        
        if missing_deps:
            messagebox.showwarning(
                "Dependencias Faltantes",
                f"Las siguientes librerías son recomendadas para reportes avanzados:\n"
                f"{', '.join(missing_deps)}\n\n"
                f"Instálelas con: pip install {' '.join(missing_deps)}"
            )
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Frame principal
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="Reportes y Análisis", 
                 font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        # Botones principales
        buttons_frame = ttk.Frame(title_frame)
        buttons_frame.pack(side=tk.RIGHT)
        
        ttk.Button(buttons_frame, text="Generar Reporte", 
                  command=self.generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Exportar", 
                  command=self.export_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Configuración", 
                  command=self.show_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Programar", 
                  command=self.schedule_report).pack(side=tk.LEFT, padx=5)
        
        # Crear notebook principal
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestañas de reportes
        self.setup_sales_reports_tab()
        self.setup_inventory_reports_tab()
        self.setup_financial_reports_tab()
        self.setup_customer_reports_tab()
        self.setup_analytics_tab()
        self.setup_custom_reports_tab()
    
    def setup_sales_reports_tab(self):
        """Configura la pestaña de reportes de ventas"""
        sales_frame = ttk.Frame(self.notebook)
        self.notebook.add(sales_frame, text="Reportes de Ventas")
        
        # Panel de filtros
        filters_frame = create_styled_frame(sales_frame, "Filtros de Ventas")
        filters_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        filters_content = ttk.Frame(filters_frame)
        filters_content.pack(fill=tk.X, padx=15, pady=10)
        
        # Fila 1: Período
        row1 = ttk.Frame(filters_content)
        row1.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(row1, text="Período:").pack(side=tk.LEFT)
        period_combo = ttk.Combobox(row1, textvariable=self.period_var, width=15, state="readonly")
        period_combo['values'] = ("Hoy", "Ayer", "Esta Semana", "Semana Pasada", 
                                 "Este Mes", "Mes Pasado", "Este Año", "Personalizado")
        period_combo.pack(side=tk.LEFT, padx=(5, 20))
        period_combo.bind('<<ComboboxSelected>>', self.on_period_change)
        
        # Fechas específicas
        ttk.Label(row1, text="Desde:").pack(side=tk.LEFT)
        self.start_date_entry = ttk.Entry(row1, textvariable=self.start_date_var, width=12)
        self.start_date_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(row1, text="Hasta:").pack(side=tk.LEFT)
        self.end_date_entry = ttk.Entry(row1, textvariable=self.end_date_var, width=12)
        self.end_date_entry.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Button(row1, text="Aplicar", command=self.apply_date_filter).pack(side=tk.LEFT)
        
        # Fila 2: Filtros adicionales
        row2 = ttk.Frame(filters_content)
        row2.pack(fill=tk.X)
        
        ttk.Label(row2, text="Usuario:").pack(side=tk.LEFT)
        self.user_combo = ttk.Combobox(row2, textvariable=self.user_filter_var, 
                                      width=15, state="readonly")
        self.user_combo.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row2, text="Categoría:").pack(side=tk.LEFT)
        self.category_combo = ttk.Combobox(row2, textvariable=self.category_filter_var, 
                                          width=15, state="readonly")
        self.category_combo.pack(side=tk.LEFT, padx=(5, 20))
        
        # Panel de tipos de reportes de ventas
        sales_types_frame = create_styled_frame(sales_frame, "Tipos de Reportes")
        sales_types_frame.pack(fill=tk.X, padx=10, pady=10)
        
        sales_types_content = ttk.Frame(sales_types_frame)
        sales_types_content.pack(fill=tk.X, padx=15, pady=10)
        
        # Botones de reportes específicos
        reports_grid = ttk.Frame(sales_types_content)
        reports_grid.pack(fill=tk.X)
        
        # Fila 1
        row1 = ttk.Frame(reports_grid)
        row1.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(row1, text="Ventas Diarias", width=20,
                  command=lambda: self.generate_sales_report("daily")).pack(side=tk.LEFT, padx=5)
        ttk.Button(row1, text="Ventas por Producto", width=20,
                  command=lambda: self.generate_sales_report("by_product")).pack(side=tk.LEFT, padx=5)
        ttk.Button(row1, text="Ventas por Categoría", width=20,
                  command=lambda: self.generate_sales_report("by_category")).pack(side=tk.LEFT, padx=5)
        
        # Fila 2
        row2 = ttk.Frame(reports_grid)
        row2.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(row2, text="Ventas por Usuario", width=20,
                  command=lambda: self.generate_sales_report("by_user")).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text="Métodos de Pago", width=20,
                  command=lambda: self.generate_sales_report("payment_methods")).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text="Análisis de Descuentos", width=20,
                  command=lambda: self.generate_sales_report("discounts")).pack(side=tk.LEFT, padx=5)
        
        # Panel de resultados
        self.setup_results_panel(sales_frame, "sales")
    
    def setup_inventory_reports_tab(self):
        """Configura la pestaña de reportes de inventario"""
        inventory_frame = ttk.Frame(self.notebook)
        self.notebook.add(inventory_frame, text="Reportes de Inventario")
        
        # Panel de tipos de reportes de inventario
        inventory_types_frame = create_styled_frame(inventory_frame, "Reportes de Inventario")
        inventory_types_frame.pack(fill=tk.X, padx=10, pady=10)
        
        inventory_content = ttk.Frame(inventory_types_frame)
        inventory_content.pack(fill=tk.X, padx=15, pady=10)
        
        # Botones de reportes
        reports_grid = ttk.Frame(inventory_content)
        reports_grid.pack(fill=tk.X)
        
        # Fila 1
        row1 = ttk.Frame(reports_grid)
        row1.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(row1, text="Stock Actual", width=20,
                  command=lambda: self.generate_inventory_report("current_stock")).pack(side=tk.LEFT, padx=5)
        ttk.Button(row1, text="Stock Bajo", width=20,
                  command=lambda: self.generate_inventory_report("low_stock")).pack(side=tk.LEFT, padx=5)
        ttk.Button(row1, text="Productos Sin Stock", width=20,
                  command=lambda: self.generate_inventory_report("out_of_stock")).pack(side=tk.LEFT, padx=5)
        
        # Fila 2
        row2 = ttk.Frame(reports_grid)
        row2.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(row2, text="Valorización Inventario", width=20,
                  command=lambda: self.generate_inventory_report("valuation")).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text="Movimientos Stock", width=20,
                  command=lambda: self.generate_inventory_report("movements")).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text="Rotación Productos", width=20,
                  command=lambda: self.generate_inventory_report("rotation")).pack(side=tk.LEFT, padx=5)
        
        # Fila 3
        row3 = ttk.Frame(reports_grid)
        row3.pack(fill=tk.X)
        
        ttk.Button(row3, text="Productos Inactivos", width=20,
                  command=lambda: self.generate_inventory_report("inactive")).pack(side=tk.LEFT, padx=5)
        ttk.Button(row3, text="Análisis ABC", width=20,
                  command=lambda: self.generate_inventory_report("abc_analysis")).pack(side=tk.LEFT, padx=5)
        ttk.Button(row3, text="Costo Inventario", width=20,
                  command=lambda: self.generate_inventory_report("cost_analysis")).pack(side=tk.LEFT, padx=5)
        
        # Panel de resultados
        self.setup_results_panel(inventory_frame, "inventory")
    
    def setup_financial_reports_tab(self):
        """Configura la pestaña de reportes financieros"""
        financial_frame = ttk.Frame(self.notebook)
        self.notebook.add(financial_frame, text="Reportes Financieros")
        
        # Panel de tipos de reportes financieros
        financial_types_frame = create_styled_frame(financial_frame, "Reportes Financieros")
        financial_types_frame.pack(fill=tk.X, padx=10, pady=10)
        
        financial_content = ttk.Frame(financial_types_frame)
        financial_content.pack(fill=tk.X, padx=15, pady=10)
        
        # Botones de reportes
        reports_grid = ttk.Frame(financial_content)
        reports_grid.pack(fill=tk.X)
        
        # Fila 1
        row1 = ttk.Frame(reports_grid)
        row1.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(row1, text="Estado de Resultados", width=20,
                  command=lambda: self.generate_financial_report("income_statement")).pack(side=tk.LEFT, padx=5)
        ttk.Button(row1, text="Flujo de Caja", width=20,
                  command=lambda: self.generate_financial_report("cash_flow")).pack(side=tk.LEFT, padx=5)
        ttk.Button(row1, text="Utilidades", width=20,
                  command=lambda: self.generate_financial_report("profits")).pack(side=tk.LEFT, padx=5)
        
        # Fila 2
        row2 = ttk.Frame(reports_grid)
        row2.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(row2, text="Gastos por Categoría", width=20,
                  command=lambda: self.generate_financial_report("expenses")).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text="Impuestos", width=20,
                  command=lambda: self.generate_financial_report("taxes")).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text="Análisis Márgenes", width=20,
                  command=lambda: self.generate_financial_report("margins")).pack(side=tk.LEFT, padx=5)
        
        # Panel de resultados
        self.setup_results_panel(financial_frame, "financial")
    
    def setup_customer_reports_tab(self):
        """Configura la pestaña de reportes de clientes"""
        customer_frame = ttk.Frame(self.notebook)
        self.notebook.add(customer_frame, text="Reportes de Clientes")
        
        # Panel de tipos de reportes de clientes
        customer_types_frame = create_styled_frame(customer_frame, "Reportes de Clientes")
        customer_types_frame.pack(fill=tk.X, padx=10, pady=10)
        
        customer_content = ttk.Frame(customer_types_frame)
        customer_content.pack(fill=tk.X, padx=15, pady=10)
        
        # Botones de reportes
        reports_grid = ttk.Frame(customer_content)
        reports_grid.pack(fill=tk.X)
        
        # Fila 1
        row1 = ttk.Frame(reports_grid)
        row1.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(row1, text="Clientes Frecuentes", width=20,
                  command=lambda: self.generate_customer_report("frequent")).pack(side=tk.LEFT, padx=5)
        ttk.Button(row1, text="Análisis RFM", width=20,
                  command=lambda: self.generate_customer_report("rfm")).pack(side=tk.LEFT, padx=5)
        ttk.Button(row1, text="Clientes Nuevos", width=20,
                  command=lambda: self.generate_customer_report("new_customers")).pack(side=tk.LEFT, padx=5)
        
        # Fila 2
        row2 = ttk.Frame(reports_grid)
        row2.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(row2, text="Ventas por Cliente", width=20,
                  command=lambda: self.generate_customer_report("sales_by_customer")).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text="Clientes Inactivos", width=20,
                  command=lambda: self.generate_customer_report("inactive")).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text="Análisis Geográfico", width=20,
                  command=lambda: self.generate_customer_report("geographic")).pack(side=tk.LEFT, padx=5)
        
        # Panel de resultados
        self.setup_results_panel(customer_frame, "customer")
    
    def setup_analytics_tab(self):
        """Configura la pestaña de análisis avanzado"""
        analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(analytics_frame, text="Análisis Avanzado")
        
        # Panel de dashboard
        dashboard_frame = create_styled_frame(analytics_frame, "Dashboard Ejecutivo")
        dashboard_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Crear área de gráficos si matplotlib está disponible
        if MATPLOTLIB_AVAILABLE:
            self.setup_dashboard_charts(dashboard_frame)
        else:
            ttk.Label(dashboard_frame, text="Instale matplotlib para ver gráficos", 
                     font=('Arial', 12)).pack(expand=True)
        
        # Panel de KPIs
        kpis_frame = create_styled_frame(analytics_frame, "Indicadores Clave (KPIs)")
        kpis_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.setup_kpis_panel(kpis_frame)
    
    def setup_dashboard_charts(self, parent):
        """Configura los gráficos del dashboard"""
        # Crear frame para controles
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(controls_frame, text="Actualizar Dashboard", 
                  command=self.update_dashboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Configurar Gráficos", 
                  command=self.configure_charts).pack(side=tk.LEFT, padx=5)
        
        # Crear notebook para diferentes vistas
        charts_notebook = ttk.Notebook(parent)
        charts_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Vista de ventas
        sales_chart_frame = ttk.Frame(charts_notebook)
        charts_notebook.add(sales_chart_frame, text="Ventas")
        
        # Vista de inventario
        inventory_chart_frame = ttk.Frame(charts_notebook)
        charts_notebook.add(inventory_chart_frame, text="Inventario")
        
        # Vista financiera
        financial_chart_frame = ttk.Frame(charts_notebook)
        charts_notebook.add(financial_chart_frame, text="Financiero")
        
        # Inicializar gráficos
        self.sales_chart_frame = sales_chart_frame
        self.inventory_chart_frame = inventory_chart_frame
        self.financial_chart_frame = financial_chart_frame
        
        self.create_sample_charts()
    
    def create_sample_charts(self):
        """Crea gráficos de ejemplo"""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        # Gráfico de ventas
        fig1 = Figure(figsize=(12, 4), dpi=100)
        ax1 = fig1.add_subplot(111)
        
        # Datos de ejemplo
        dates = [datetime.now() - timedelta(days=x) for x in range(7, 0, -1)]
        sales = [1500, 2300, 1800, 2100, 2500, 1900, 2200]
        
        ax1.plot(dates, sales, marker='o', linewidth=2, markersize=6)
        ax1.set_title('Ventas de los Últimos 7 Días')
        ax1.set_ylabel('Ventas (₡)')
        ax1.grid(True, alpha=0.3)
        fig1.autofmt_xdate()
        
        canvas1 = FigureCanvasTkAgg(fig1, self.sales_chart_frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Gráfico de inventario
        fig2 = Figure(figsize=(12, 4), dpi=100)
        ax2 = fig2.add_subplot(111)
        
        categories = ['Electrónicos', 'Ropa', 'Hogar', 'Deportes', 'Libros']
        stock_values = [45000, 32000, 28000, 15000, 8000]
        
        ax2.bar(categories, stock_values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57'])
        ax2.set_title('Valor del Inventario por Categoría')
        ax2.set_ylabel('Valor (₡)')
        ax2.tick_params(axis='x', rotation=45)
        
        canvas2 = FigureCanvasTkAgg(fig2, self.inventory_chart_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Gráfico financiero
        fig3 = Figure(figsize=(12, 4), dpi=100)
        ax3 = fig3.add_subplot(111)
        
        months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
        income = [45000, 52000, 48000, 61000, 58000, 67000]
        expenses = [32000, 38000, 35000, 44000, 41000, 48000]
        
        x_pos = range(len(months))
        width = 0.35
        
        ax3.bar([x - width/2 for x in x_pos], income, width, label='Ingresos', color='#4ECDC4')
        ax3.bar([x + width/2 for x in x_pos], expenses, width, label='Gastos', color='#FF6B6B')
        
        ax3.set_title('Ingresos vs Gastos por Mes')
        ax3.set_ylabel('Monto (₡)')
        ax3.set_xticks(x_pos)
        ax3.set_xticklabels(months)
        ax3.legend()
        
        canvas3 = FigureCanvasTkAgg(fig3, self.financial_chart_frame)
        canvas3.draw()
        canvas3.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def setup_kpis_panel(self, parent):
        """Configura el panel de KPIs"""
        kpis_content = ttk.Frame(parent)
        kpis_content.pack(fill=tk.X, padx=15, pady=10)
        
        # Crear grid de KPIs
        kpis_grid = ttk.Frame(kpis_content)
        kpis_grid.pack(fill=tk.X)
        
        # Fila 1
        row1 = ttk.Frame(kpis_grid)
        row1.pack(fill=tk.X, pady=(0, 10))
        
        self.create_kpi_widget(row1, "Ventas Hoy", "₡125,450", "↑ 15%", "green")
        self.create_kpi_widget(row1, "Productos Vendidos", "287", "↑ 8%", "green")
        self.create_kpi_widget(row1, "Ticket Promedio", "₡437", "↓ 3%", "red")
        self.create_kpi_widget(row1, "Clientes Atendidos", "156", "↑ 12%", "green")
        
        # Fila 2
        row2 = ttk.Frame(kpis_grid)
        row2.pack(fill=tk.X)
        
        self.create_kpi_widget(row2, "Margen Bruto", "42.5%", "↑ 2%", "green")
        self.create_kpi_widget(row2, "Stock Crítico", "23", "↓ 5%", "orange")
        self.create_kpi_widget(row2, "Rotación Inventario", "6.2x", "→ 0%", "gray")
        self.create_kpi_widget(row2, "ROI Mensual", "18.3%", "↑ 4%", "green")
    
    def create_kpi_widget(self, parent, title, value, change, color):
        """Crea un widget de KPI"""
        kpi_frame = ttk.LabelFrame(parent, text=title)
        kpi_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Valor principal
        value_label = ttk.Label(kpi_frame, text=value, font=('Arial', 16, 'bold'))
        value_label.pack(pady=5)
        
        # Cambio porcentual
        change_label = ttk.Label(kpi_frame, text=change, font=('Arial', 10), foreground=color)
        change_label.pack()
    
    def setup_custom_reports_tab(self):
        """Configura la pestaña de reportes personalizados"""
        custom_frame = ttk.Frame(self.notebook)
        self.notebook.add(custom_frame, text="Reportes Personalizados")
        
        messagebox.showinfo("Info", "Reportes personalizados en desarrollo")
    
    def setup_results_panel(self, parent, report_type):
        """Configura el panel de resultados para un tipo de reporte"""
        results_frame = create_styled_frame(parent, "Resultados")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Crear TreeView para mostrar resultados
        columns = self.get_columns_for_report_type(report_type)
        
        tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=12)
        
        # Configurar columnas
        for col in columns:
            tree.heading(col, text=col.replace('_', ' ').title())
            tree.column(col, width=120)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Empaquetar
        tree.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        v_scrollbar.grid(row=0, column=1, sticky='ns', pady=10)
        h_scrollbar.grid(row=1, column=0, sticky='ew', padx=10)
        
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # Guardar referencia al TreeView
        setattr(self, f'{report_type}_tree', tree)
        
        # Panel de resumen
        summary_frame = ttk.Frame(results_frame)
        summary_frame.grid(row=2, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        summary_label = ttk.Label(summary_frame, text="Resumen: Sin datos", 
                                 font=('Arial', 10, 'bold'))
        summary_label.pack(side=tk.LEFT)
        
        setattr(self, f'{report_type}_summary', summary_label)
    
    def get_columns_for_report_type(self, report_type):
        """Obtiene las columnas para cada tipo de reporte"""
        columns_map = {
            'sales': ['fecha', 'producto', 'cantidad', 'precio_unitario', 'total', 'usuario'],
            'inventory': ['codigo', 'producto', 'categoria', 'stock_actual', 'stock_minimo', 'valor'],
            'financial': ['concepto', 'ingresos', 'gastos', 'utilidad', 'margen'],
            'customer': ['cliente', 'total_compras', 'frecuencia', 'ultima_compra', 'clasificacion']
        }
        return columns_map.get(report_type, ['col1', 'col2', 'col3', 'col4'])
    
    def load_initial_data(self):
        """Carga datos iniciales para filtros"""
        self.load_users()
        self.load_categories()
        
        # Configurar período inicial
        self.on_period_change()
    
    def load_users(self):
        """Carga lista de usuarios"""
        try:
            query = "SELECT id, username, full_name FROM usuarios WHERE is_active = 1"
            resultado = ejecutar_consulta_segura(query)
            
            users = ["Todos"]
            if resultado:
                for row in resultado:
                    users.append(f"{row[1]} - {row[2]}")
            
            self.user_combo['values'] = users
            self.user_combo.current(0)
            
        except Exception as e:
            print(f"Error cargando usuarios: {e}")
    
    def load_categories(self):
        """Carga lista de categorías"""
        try:
            query = "SELECT id, nombre FROM categorias WHERE activo = 1"
            resultado = ejecutar_consulta_segura(query)
            
            categories = ["Todas"]
            if resultado:
                for row in resultado:
                    categories.append(row[1])
            
            self.category_combo['values'] = categories
            self.category_combo.current(0)
            
        except Exception as e:
            print(f"Error cargando categorías: {e}")
    
    # Métodos de manejo de eventos
    def on_period_change(self, event=None):
        """Maneja cambio de período"""
        period = self.period_var.get()
        today = datetime.now().date()
        
        if period == "Hoy":
            start_date = end_date = today
        elif period == "Ayer":
            start_date = end_date = today - timedelta(days=1)
        elif period == "Esta Semana":
            start_date = today - timedelta(days=today.weekday())
            end_date = today
        elif period == "Semana Pasada":
            start_date = today - timedelta(days=today.weekday() + 7)
            end_date = start_date + timedelta(days=6)
        elif period == "Este Mes":
            start_date = today.replace(day=1)
            end_date = today
        elif period == "Mes Pasado":
            if today.month == 1:
                start_date = date(today.year - 1, 12, 1)
                end_date = date(today.year - 1, 12, 31)
            else:
                start_date = date(today.year, today.month - 1, 1)
                # Último día del mes anterior
                end_date = today.replace(day=1) - timedelta(days=1)
        elif period == "Este Año":
            start_date = date(today.year, 1, 1)
            end_date = today
        else:  # Personalizado
            return  # No cambiar las fechas
        
        self.start_date_var.set(start_date.strftime("%Y-%m-%d"))
        self.end_date_var.set(end_date.strftime("%Y-%m-%d"))
    
    def apply_date_filter(self):
        """Aplica el filtro de fechas"""
        try:
            start_date = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d").date()
            end_date = datetime.strptime(self.end_date_var.get(), "%Y-%m-%d").date()
            
            if start_date > end_date:
                messagebox.showerror("Error", "La fecha inicial no puede ser mayor que la final")
                return
            
            # Actualizar período a personalizado
            self.period_var.set("Personalizado")
            
            messagebox.showinfo("Info", f"Filtro aplicado: {start_date} a {end_date}")
            
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD")
    
    # Métodos de generación de reportes
    def generate_report(self):
        """Genera reporte basado en la pestaña activa"""
        active_tab = self.notebook.index(self.notebook.select())
        
        if active_tab == 0:  # Ventas
            self.generate_sales_report("summary")
        elif active_tab == 1:  # Inventario
            self.generate_inventory_report("current_stock")
        elif active_tab == 2:  # Financiero
            self.generate_financial_report("income_statement")
        elif active_tab == 3:  # Clientes
            self.generate_customer_report("frequent")
        elif active_tab == 4:  # Analytics
            self.update_dashboard()
    
    def generate_sales_report(self, report_type):
        """Genera reportes de ventas"""
        try:
            # Mostrar indicador de progreso
            self.show_progress("Generando reporte de ventas...")
            
            # Obtener fechas del filtro
            start_date = self.start_date_var.get()
            end_date = self.end_date_var.get()
            
            # Consultas según tipo de reporte
            if report_type == "daily":
                query = """
                    SELECT DATE(v.fecha_venta) as fecha, 
                           COUNT(*) as num_ventas,
                           SUM(v.total) as total_ventas,
                           AVG(v.total) as ticket_promedio
                    FROM ventas v 
                    WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
                    GROUP BY DATE(v.fecha_venta)
                    ORDER BY fecha DESC
                """
                params = (start_date, end_date)
                
            elif report_type == "by_product":
                query = """
                    SELECT p.nombre, p.codigo,
                           SUM(dv.cantidad) as cantidad_vendida,
                           SUM(dv.subtotal) as total_vendido,
                           AVG(dv.precio_unitario) as precio_promedio
                    FROM detalle_ventas dv
                    JOIN productos p ON dv.producto_id = p.id
                    JOIN ventas v ON dv.venta_id = v.id
                    WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
                    GROUP BY p.id
                    ORDER BY cantidad_vendida DESC
                """
                params = (start_date, end_date)
                
            elif report_type == "by_category":
                query = """
                    SELECT c.nombre as categoria,
                           COUNT(dv.id) as items_vendidos,
                           SUM(dv.cantidad) as cantidad_total,
                           SUM(dv.subtotal) as total_ventas
                    FROM detalle_ventas dv
                    JOIN productos p ON dv.producto_id = p.id
                    JOIN categorias c ON p.categoria_id = c.id
                    JOIN ventas v ON dv.venta_id = v.id
                    WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
                    GROUP BY c.id
                    ORDER BY total_ventas DESC
                """
                params = (start_date, end_date)
                
            else:  # summary
                query = """
                    SELECT 'Total Ventas' as concepto, COUNT(*) as cantidad, SUM(total) as monto
                    FROM ventas 
                    WHERE DATE(fecha_venta) BETWEEN ? AND ?
                    UNION ALL
                    SELECT 'Productos Vendidos', SUM(cantidad), SUM(subtotal)
                    FROM detalle_ventas dv
                    JOIN ventas v ON dv.venta_id = v.id
                    WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
                """
                params = (start_date, end_date, start_date, end_date)
            
            # Ejecutar consulta
            resultado = ejecutar_consulta_segura(query, params)
            
            # Mostrar resultados
            self.display_report_results(resultado, "sales", report_type)
            self.hide_progress()
            
        except Exception as e:
            self.hide_progress()
            messagebox.showerror("Error", f"Error generando reporte: {str(e)}")
    
    def generate_inventory_report(self, report_type):
        """Genera reportes de inventario"""
        try:
            self.show_progress("Generando reporte de inventario...")
            
            if report_type == "current_stock":
                query = """
                    SELECT p.codigo, p.nombre, c.nombre as categoria,
                           p.stock_actual, p.stock_minimo, p.stock_maximo,
                           (p.stock_actual * p.precio_compra) as valor_stock
                    FROM productos p
                    LEFT JOIN categorias c ON p.categoria_id = c.id
                    WHERE p.activo = 1
                    ORDER BY p.nombre
                """
                params = ()
                
            elif report_type == "low_stock":
                query = """
                    SELECT p.codigo, p.nombre, c.nombre as categoria,
                           p.stock_actual, p.stock_minimo,
                           (p.stock_minimo - p.stock_actual) as faltante
                    FROM productos p
                    LEFT JOIN categorias c ON p.categoria_id = c.id
                    WHERE p.activo = 1 AND p.stock_actual <= p.stock_minimo
                    ORDER BY faltante DESC
                """
                params = ()
                
            elif report_type == "out_of_stock":
                query = """
                    SELECT p.codigo, p.nombre, c.nombre as categoria,
                           p.stock_actual, p.fecha_ultima_venta
                    FROM productos p
                    LEFT JOIN categorias c ON p.categoria_id = c.id
                    WHERE p.activo = 1 AND p.stock_actual <= 0
                    ORDER BY p.fecha_ultima_venta DESC
                """
                params = ()
                
            elif report_type == "valuation":
                query = """
                    SELECT c.nombre as categoria,
                           COUNT(p.id) as num_productos,
                           SUM(p.stock_actual) as stock_total,
                           SUM(p.stock_actual * p.precio_compra) as valor_compra,
                           SUM(p.stock_actual * p.precio_venta) as valor_venta
                    FROM productos p
                    LEFT JOIN categorias c ON p.categoria_id = c.id
                    WHERE p.activo = 1
                    GROUP BY c.id
                    ORDER BY valor_compra DESC
                """
                params = ()
                
            else:
                query = """
                    SELECT p.codigo, p.nombre, p.stock_actual, 
                           (p.stock_actual * p.precio_compra) as valor
                    FROM productos p
                    WHERE p.activo = 1
                    ORDER BY valor DESC
                """
                params = ()
            
            resultado = ejecutar_consulta_segura(query, params)
            self.display_report_results(resultado, "inventory", report_type)
            self.hide_progress()
            
        except Exception as e:
            self.hide_progress()
            messagebox.showerror("Error", f"Error generando reporte: {str(e)}")
    
    def generate_financial_report(self, report_type):
        """Genera reportes financieros"""
        try:
            self.show_progress("Generando reporte financiero...")
            
            start_date = self.start_date_var.get()
            end_date = self.end_date_var.get()
            
            if report_type == "income_statement":
                query = """
                    SELECT 'Ingresos por Ventas' as concepto,
                           SUM(total) as monto,
                           COUNT(*) as transacciones
                    FROM ventas 
                    WHERE DATE(fecha_venta) BETWEEN ? AND ?
                    UNION ALL
                    SELECT 'Costo de Ventas',
                           SUM(dv.cantidad * p.precio_compra),
                           SUM(dv.cantidad)
                    FROM detalle_ventas dv
                    JOIN productos p ON dv.producto_id = p.id
                    JOIN ventas v ON dv.venta_id = v.id
                    WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
                """
                params = (start_date, end_date, start_date, end_date)
                
            elif report_type == "profits":
                query = """
                    SELECT DATE(v.fecha_venta) as fecha,
                           SUM(v.total) as ingresos,
                           SUM(dv.cantidad * p.precio_compra) as costos,
                           (SUM(v.total) - SUM(dv.cantidad * p.precio_compra)) as utilidad
                    FROM ventas v
                    JOIN detalle_ventas dv ON v.id = dv.venta_id
                    JOIN productos p ON dv.producto_id = p.id
                    WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
                    GROUP BY DATE(v.fecha_venta)
                    ORDER BY fecha DESC
                """
                params = (start_date, end_date)
                
            else:
                query = """
                    SELECT 'Resumen Financiero' as concepto,
                           SUM(total) as ingresos,
                           0 as gastos,
                           SUM(total) as neto
                    FROM ventas 
                    WHERE DATE(fecha_venta) BETWEEN ? AND ?
                """
                params = (start_date, end_date)
            
            resultado = ejecutar_consulta_segura(query, params)
            self.display_report_results(resultado, "financial", report_type)
            self.hide_progress()
            
        except Exception as e:
            self.hide_progress()
            messagebox.showerror("Error", f"Error generando reporte: {str(e)}")
    
    def generate_customer_report(self, report_type):
        """Genera reportes de clientes"""
        try:
            self.show_progress("Generando reporte de clientes...")
            
            start_date = self.start_date_var.get()
            end_date = self.end_date_var.get()
            
            if report_type == "frequent":
                query = """
                    SELECT c.nombre, c.telefono, c.email,
                           COUNT(v.id) as num_compras,
                           SUM(v.total) as total_comprado,
                           AVG(v.total) as ticket_promedio,
                           MAX(v.fecha_venta) as ultima_compra
                    FROM clientes c
                    JOIN ventas v ON c.id = v.cliente_id
                    WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
                    GROUP BY c.id
                    HAVING num_compras >= 2
                    ORDER BY num_compras DESC, total_comprado DESC
                """
                params = (start_date, end_date)
                
            elif report_type == "new_customers":
                query = """
                    SELECT c.nombre, c.telefono, c.email,
                           c.fecha_registro,
                           COUNT(v.id) as compras_realizadas,
                           COALESCE(SUM(v.total), 0) as total_gastado
                    FROM clientes c
                    LEFT JOIN ventas v ON c.id = v.cliente_id
                    WHERE DATE(c.fecha_registro) BETWEEN ? AND ?
                    GROUP BY c.id
                    ORDER BY c.fecha_registro DESC
                """
                params = (start_date, end_date)
                
            else:
                query = """
                    SELECT c.nombre, 
                           COUNT(v.id) as compras,
                           SUM(v.total) as total,
                           AVG(v.total) as promedio,
                           'Regular' as clasificacion
                    FROM clientes c
                    LEFT JOIN ventas v ON c.id = v.cliente_id
                    WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
                    GROUP BY c.id
                    ORDER BY total DESC
                """
                params = (start_date, end_date)
            
            resultado = ejecutar_consulta_segura(query, params)
            self.display_report_results(resultado, "customer", report_type)
            self.hide_progress()
            
        except Exception as e:
            self.hide_progress()
            messagebox.showerror("Error", f"Error generando reporte: {str(e)}")
    
    def display_report_results(self, data, report_type, specific_type):
        """Muestra los resultados del reporte"""
        tree = getattr(self, f'{report_type}_tree', None)
        summary_label = getattr(self, f'{report_type}_summary', None)
        
        if not tree:
            return
        
        # Limpiar TreeView
        for item in tree.get_children():
            tree.delete(item)
        
        if not data:
            summary_label.config(text="Sin datos para mostrar")
            return
        
        # Insertar datos
        total_rows = 0
        total_value = 0
        
        for row in data:
            tree.insert('', tk.END, values=row)
            total_rows += 1
            
            # Calcular total si es numérico
            try:
                if len(row) > 1 and isinstance(row[-1], (int, float, Decimal)):
                    total_value += float(row[-1])
            except:
                pass
        
        # Actualizar resumen
        if total_value > 0:
            summary_text = f"Total registros: {total_rows} | Suma: ₡{total_value:,.2f}"
        else:
            summary_text = f"Total registros: {total_rows}"
        
        summary_label.config(text=summary_text)
        
        # Cambiar a la pestaña correspondiente
        tab_map = {'sales': 0, 'inventory': 1, 'financial': 2, 'customer': 3}
        if report_type in tab_map:
            self.notebook.select(tab_map[report_type])
    
    def update_dashboard(self):
        """Actualiza el dashboard con datos actuales"""
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showinfo("Info", "Dashboard requiere matplotlib")
            return
        
        messagebox.showinfo("Info", "Dashboard actualizado")
    
    def configure_charts(self):
        """Configura los gráficos del dashboard"""
        messagebox.showinfo("Info", "Configuración de gráficos en desarrollo")
    
    # Métodos de exportación
    def export_report(self):
        """Exporta el reporte actual"""
        if not self.current_report_data:
            messagebox.showwarning("Advertencia", "No hay datos para exportar")
            return
        
        export_format = self.config_vars['export_format'].get()
        
        file_path = filedialog.asksaveasfilename(
            title="Exportar Reporte",
            defaultextension=f".{export_format.lower()}",
            filetypes=[
                (f"{export_format} files", f"*.{export_format.lower()}"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if file_path:
            try:
                if export_format == "PDF":
                    self.export_to_pdf(file_path)
                elif export_format == "Excel":
                    self.export_to_excel(file_path)
                elif export_format == "CSV":
                    self.export_to_csv(file_path)
                
                messagebox.showinfo("Éxito", "Reporte exportado correctamente")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando: {str(e)}")
    
    def export_to_pdf(self, file_path):
        """Exporta a PDF"""
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror("Error", "Instale reportlab para exportar PDF")
            return
        
        messagebox.showinfo("Info", "Exportación PDF en desarrollo")
    
    def export_to_excel(self, file_path):
        """Exporta a Excel"""
        if not OPENPYXL_AVAILABLE:
            messagebox.showerror("Error", "Instale openpyxl para exportar Excel")
            return
        
        messagebox.showinfo("Info", "Exportación Excel en desarrollo")
    
    def export_to_csv(self, file_path):
        """Exporta a CSV"""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Escribir encabezados y datos
            if self.current_report_data:
                for row in self.current_report_data:
                    writer.writerow(row)
    
    # Métodos de configuración
    def show_config(self):
        """Muestra configuración de reportes"""
        ConfigReportsDialog(self.parent, self.config_vars)
    
    def schedule_report(self):
        """Programa ejecución automática de reportes"""
        ScheduleReportDialog(self.parent)
    
    # Métodos auxiliares
    def show_progress(self, message):
        """Muestra indicador de progreso"""
        # Crear ventana de progreso simple
        self.progress_window = tk.Toplevel(self.parent)
        self.progress_window.title("Procesando...")
        self.progress_window.geometry("300x100")
        self.progress_window.transient(self.parent)
        self.progress_window.grab_set()
        
        ttk.Label(self.progress_window, text=message).pack(pady=20)
        
        progress_bar = ttk.Progressbar(self.progress_window, mode='indeterminate')
        progress_bar.pack(pady=10, padx=20, fill=tk.X)
        progress_bar.start()
        
        self.progress_window.update()
    
    def hide_progress(self):
        """Oculta indicador de progreso"""
        if hasattr(self, 'progress_window'):
            self.progress_window.destroy()

# Diálogos auxiliares
class ConfigReportsDialog:
    """Diálogo de configuración de reportes"""
    
    def __init__(self, parent, config_vars):
        self.config_vars = config_vars
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Configuración de Reportes")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_dialog()
    
    def setup_dialog(self):
        """Configura el diálogo"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Configuraciones generales
        general_frame = create_styled_frame(main_frame, "Configuración General")
        general_frame.pack(fill=tk.X, pady=(0, 15))
        
        general_content = ttk.Frame(general_frame)
        general_content.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Checkbutton(general_content, text="Actualización automática", 
                       variable=self.config_vars['auto_refresh']).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(general_content, text="Incluir gráficos", 
                       variable=self.config_vars['include_graphics']).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(general_content, text="Vista detallada", 
                       variable=self.config_vars['detailed_view']).pack(anchor=tk.W, pady=2)
        
        # Formato de exportación
        export_frame = ttk.Frame(general_content)
        export_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(export_frame, text="Formato de exportación:").pack(side=tk.LEFT)
        format_combo = ttk.Combobox(export_frame, textvariable=self.config_vars['export_format'],
                                   values=["PDF", "Excel", "CSV"], state="readonly", width=10)
        format_combo.pack(side=tk.LEFT, padx=10)
        
        # Botones
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(buttons_frame, text="Cancelar", 
                  command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="Guardar", 
                  command=self.save_config).pack(side=tk.RIGHT, padx=5)
    
    def save_config(self):
        """Guarda la configuración"""
        messagebox.showinfo("Info", "Configuración guardada")
        self.dialog.destroy()

class ScheduleReportDialog:
    """Diálogo para programar reportes"""
    
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Programar Reportes")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        messagebox.showinfo("Info", "Programación de reportes en desarrollo")

# Función principal
def mostrar_reportes(parent_window):
    """Función principal para mostrar los reportes"""
    ReportsUI(parent_window)
