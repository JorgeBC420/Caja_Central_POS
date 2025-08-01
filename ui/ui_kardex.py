"""
Interfaz de usuario para Kardex de inventario
Maneja el registro detallado de movimientos de productos con control de costos
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Any
import threading

from modules.inventory.kardex import KardexManager
from modules.inventory.product import ProductManager
from ui.ui_helpers import create_styled_frame, create_input_frame, show_loading_dialog
from core.database import ejecutar_consulta_segura

class KardexUI:
    """Interfaz principal para gestión de Kardex"""
    
    def __init__(self, parent_window):
        self.parent = parent_window
        self.kardex_manager = KardexManager()
        self.product_manager = ProductManager()
        self.current_product = None
        self.current_period = None
        
        # Variables de filtros
        self.filter_vars = {
            'producto': tk.StringVar(),
            'fecha_desde': tk.StringVar(value=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')),
            'fecha_hasta': tk.StringVar(value=datetime.now().strftime('%Y-%m-%d')),
            'tipo_movimiento': tk.StringVar(),
            'usuario': tk.StringVar()
        }
        
        self.setup_ui()
        self.load_initial_data()
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título y botones principales
        self.setup_header()
        
        # Frame de filtros
        self.setup_filters_frame()
        
        # Notebook principal
        self.setup_main_notebook()
    
    def setup_header(self):
        """Configura el encabezado con título y botones"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Título
        ttk.Label(header_frame, text="Kardex de Inventario", 
                 font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        # Botones principales
        buttons_frame = ttk.Frame(header_frame)
        buttons_frame.pack(side=tk.RIGHT)
        
        ttk.Button(buttons_frame, text="Nuevo Movimiento", 
                  command=self.show_movement_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cerrar Período", 
                  command=self.close_period).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Reporte Kardex", 
                  command=self.generate_kardex_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Exportar", 
                  command=self.export_kardex).pack(side=tk.LEFT, padx=5)
    
    def setup_filters_frame(self):
        """Configura el frame de filtros"""
        filters_frame = create_styled_frame(self.main_frame, "Filtros de Búsqueda")
        filters_frame.pack(fill=tk.X, pady=(0, 10))
        
        filter_content = ttk.Frame(filters_frame)
        filter_content.pack(fill=tk.X, padx=10, pady=5)
        
        # Primera fila de filtros
        filter_row1 = ttk.Frame(filter_content)
        filter_row1.pack(fill=tk.X, pady=2)
        
        # Producto
        ttk.Label(filter_row1, text="Producto:").pack(side=tk.LEFT)
        self.product_combo = ttk.Combobox(filter_row1, textvariable=self.filter_vars['producto'], 
                                         width=25, state="readonly")
        self.product_combo.pack(side=tk.LEFT, padx=(5, 15))
        self.product_combo.bind('<<ComboboxSelected>>', self.on_product_selected)
        
        # Fecha desde
        ttk.Label(filter_row1, text="Desde:").pack(side=tk.LEFT)
        ttk.Entry(filter_row1, textvariable=self.filter_vars['fecha_desde'], 
                 width=12).pack(side=tk.LEFT, padx=(5, 15))
        
        # Fecha hasta
        ttk.Label(filter_row1, text="Hasta:").pack(side=tk.LEFT)
        ttk.Entry(filter_row1, textvariable=self.filter_vars['fecha_hasta'], 
                 width=12).pack(side=tk.LEFT, padx=(5, 15))
        
        # Segunda fila de filtros
        filter_row2 = ttk.Frame(filter_content)
        filter_row2.pack(fill=tk.X, pady=2)
        
        # Tipo de movimiento
        ttk.Label(filter_row2, text="Tipo:").pack(side=tk.LEFT)
        tipo_combo = ttk.Combobox(filter_row2, textvariable=self.filter_vars['tipo_movimiento'],
                                 width=15, values=['', 'ENTRADA', 'SALIDA', 'AJUSTE', 'VENTA', 
                                                  'COMPRA', 'DEVOLUCION', 'TRASLADO'])
        tipo_combo.pack(side=tk.LEFT, padx=(5, 15))
        
        # Usuario
        ttk.Label(filter_row2, text="Usuario:").pack(side=tk.LEFT)
        self.user_combo = ttk.Combobox(filter_row2, textvariable=self.filter_vars['usuario'], 
                                      width=15, state="readonly")
        self.user_combo.pack(side=tk.LEFT, padx=(5, 15))
        
        # Botones de acción
        ttk.Button(filter_row2, text="Buscar", 
                  command=self.apply_filters).pack(side=tk.LEFT, padx=10)
        ttk.Button(filter_row2, text="Limpiar", 
                  command=self.clear_filters).pack(side=tk.LEFT, padx=5)
    
    def setup_main_notebook(self):
        """Configura el notebook principal"""
        self.main_notebook = ttk.Notebook(self.main_frame)
        self.main_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña kardex por producto
        self.setup_product_kardex_tab()
        
        # Pestaña resumen de movimientos
        self.setup_movements_summary_tab()
        
        # Pestaña análisis de costos
        self.setup_cost_analysis_tab()
        
        # Pestaña períodos cerrados
        self.setup_closed_periods_tab()
    
    def setup_product_kardex_tab(self):
        """Configura la pestaña de kardex por producto"""
        kardex_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(kardex_frame, text="Kardex por Producto")
        
        # Frame principal dividido
        main_content = ttk.Frame(kardex_frame)
        main_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel de información del producto (arriba)
        self.setup_product_info_panel(main_content)
        
        # Panel de movimientos kardex (abajo)
        self.setup_kardex_movements_panel(main_content)
    
    def setup_product_info_panel(self, parent):
        """Configura el panel de información del producto"""
        info_frame = create_styled_frame(parent, "Información del Producto")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_content = ttk.Frame(info_frame)
        info_content.pack(fill=tk.X, padx=10, pady=5)
        
        # Variables para información del producto
        self.product_info_vars = {
            'codigo': tk.StringVar(),
            'nombre': tk.StringVar(),
            'categoria': tk.StringVar(),
            'unidad_medida': tk.StringVar(),
            'stock_actual': tk.StringVar(),
            'costo_promedio': tk.StringVar(),
            'valor_inventario': tk.StringVar(),
            'ultimo_costo': tk.StringVar()
        }
        
        # Primera fila de información
        info_row1 = ttk.Frame(info_content)
        info_row1.pack(fill=tk.X, pady=2)
        
        for i, (field, var) in enumerate(list(self.product_info_vars.items())[:4]):
            ttk.Label(info_row1, text=f"{field.replace('_', ' ').title()}:").grid(
                row=0, column=i*2, sticky=tk.W, padx=5)
            ttk.Label(info_row1, textvariable=var, background='white', 
                     relief=tk.SUNKEN, width=15).grid(
                         row=0, column=i*2+1, sticky=tk.EW, padx=5)
        
        # Segunda fila de información
        info_row2 = ttk.Frame(info_content)
        info_row2.pack(fill=tk.X, pady=2)
        
        for i, (field, var) in enumerate(list(self.product_info_vars.items())[4:]):
            ttk.Label(info_row2, text=f"{field.replace('_', ' ').title()}:").grid(
                row=0, column=i*2, sticky=tk.W, padx=5)
            ttk.Label(info_row2, textvariable=var, background='white', 
                     relief=tk.SUNKEN, width=15).grid(
                         row=0, column=i*2+1, sticky=tk.EW, padx=5)
        
        # Configurar expansión de columnas
        for i in range(8):
            info_row1.columnconfigure(i, weight=1)
            info_row2.columnconfigure(i, weight=1)
    
    def setup_kardex_movements_panel(self, parent):
        """Configura el panel de movimientos kardex"""
        movements_frame = create_styled_frame(parent, "Movimientos Kardex")
        movements_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview para movimientos kardex
        columns = ('fecha', 'documento', 'tipo', 'entradas_cant', 'entradas_costo', 
                  'salidas_cant', 'salidas_costo', 'saldo_cant', 'saldo_costo', 
                  'costo_unitario', 'observaciones')
        
        self.kardex_tree = ttk.Treeview(movements_frame, columns=columns, 
                                       show='headings', height=15)
        
        # Configurar encabezados
        headers = {
            'fecha': 'Fecha',
            'documento': 'Documento',
            'tipo': 'Tipo',
            'entradas_cant': 'Ent. Cant.',
            'entradas_costo': 'Ent. Costo',
            'salidas_cant': 'Sal. Cant.',
            'salidas_costo': 'Sal. Costo',
            'saldo_cant': 'Saldo Cant.',
            'saldo_costo': 'Saldo Costo',
            'costo_unitario': 'Costo Unit.',
            'observaciones': 'Observaciones'
        }
        
        for col, header in headers.items():
            self.kardex_tree.heading(col, text=header)
        
        # Configurar anchos de columnas
        column_widths = {
            'fecha': 100,
            'documento': 120,
            'tipo': 100,
            'entradas_cant': 80,
            'entradas_costo': 100,
            'salidas_cant': 80,
            'salidas_costo': 100,
            'saldo_cant': 80,
            'saldo_costo': 100,
            'costo_unitario': 100,
            'observaciones': 200
        }
        
        for col, width in column_widths.items():
            self.kardex_tree.column(col, width=width)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(movements_frame, orient=tk.VERTICAL, 
                                   command=self.kardex_tree.yview)
        h_scrollbar = ttk.Scrollbar(movements_frame, orient=tk.HORIZONTAL, 
                                   command=self.kardex_tree.xview)
        
        self.kardex_tree.configure(yscrollcommand=v_scrollbar.set, 
                                  xscrollcommand=h_scrollbar.set)
        
        # Pack elementos
        self.kardex_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X, padx=10)
        
        # Bind eventos
        self.kardex_tree.bind('<Double-1>', self.view_movement_details)
    
    def setup_movements_summary_tab(self):
        """Configura la pestaña de resumen de movimientos"""
        summary_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(summary_frame, text="Resumen Movimientos")
        
        # Frame de estadísticas (arriba)
        stats_frame = create_styled_frame(summary_frame, "Estadísticas del Período")
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        stats_content = ttk.Frame(stats_frame)
        stats_content.pack(fill=tk.X, padx=10, pady=5)
        
        # Variables para estadísticas
        self.stats_vars = {
            'total_entradas': tk.StringVar(value="0"),
            'total_salidas': tk.StringVar(value="0"),
            'valor_entradas': tk.StringVar(value="₡0.00"),
            'valor_salidas': tk.StringVar(value="₡0.00"),
            'productos_movidos': tk.StringVar(value="0"),
            'movimientos_registrados': tk.StringVar(value="0")
        }
        
        # Mostrar estadísticas en dos filas
        stats_row1 = ttk.Frame(stats_content)
        stats_row1.pack(fill=tk.X, pady=2)
        
        stats_row2 = ttk.Frame(stats_content)
        stats_row2.pack(fill=tk.X, pady=2)
        
        # Primera fila de estadísticas
        for i, (field, var) in enumerate(list(self.stats_vars.items())[:3]):
            ttk.Label(stats_row1, text=f"{field.replace('_', ' ').title()}:").grid(
                row=0, column=i*2, sticky=tk.W, padx=10)
            ttk.Label(stats_row1, textvariable=var, font=('Arial', 10, 'bold'), 
                     foreground='blue').grid(row=0, column=i*2+1, sticky=tk.W, padx=10)
        
        # Segunda fila de estadísticas
        for i, (field, var) in enumerate(list(self.stats_vars.items())[3:]):
            ttk.Label(stats_row2, text=f"{field.replace('_', ' ').title()}:").grid(
                row=0, column=i*2, sticky=tk.W, padx=10)
            ttk.Label(stats_row2, textvariable=var, font=('Arial', 10, 'bold'), 
                     foreground='blue').grid(row=0, column=i*2+1, sticky=tk.W, padx=10)
        
        # Lista de movimientos resumen
        summary_list_frame = ttk.Frame(summary_frame)
        summary_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        summary_columns = ('fecha', 'producto', 'tipo', 'cantidad', 'costo_unitario', 
                          'costo_total', 'usuario', 'documento')
        
        self.summary_tree = ttk.Treeview(summary_list_frame, columns=summary_columns, 
                                        show='headings', height=12)
        
        # Configurar encabezados resumen
        summary_headers = {
            'fecha': 'Fecha',
            'producto': 'Producto',
            'tipo': 'Tipo',
            'cantidad': 'Cantidad',
            'costo_unitario': 'Costo Unit.',
            'costo_total': 'Costo Total',
            'usuario': 'Usuario',
            'documento': 'Documento'
        }
        
        for col, header in summary_headers.items():
            self.summary_tree.heading(col, text=header)
            self.summary_tree.column(col, width=120)
        
        # Scrollbar para resumen
        summary_scroll = ttk.Scrollbar(summary_list_frame, orient=tk.VERTICAL, 
                                      command=self.summary_tree.yview)
        self.summary_tree.configure(yscrollcommand=summary_scroll.set)
        
        self.summary_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        summary_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_cost_analysis_tab(self):
        """Configura la pestaña de análisis de costos"""
        analysis_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(analysis_frame, text="Análisis de Costos")
        
        # Panel de configuración de análisis
        config_frame = create_styled_frame(analysis_frame, "Configuración de Análisis")
        config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        config_content = ttk.Frame(config_frame)
        config_content.pack(fill=tk.X, padx=10, pady=5)
        
        # Opciones de análisis
        ttk.Label(config_content, text="Método de Costeo:").pack(side=tk.LEFT)
        self.costing_method = tk.StringVar(value="PROMEDIO")
        method_combo = ttk.Combobox(config_content, textvariable=self.costing_method,
                                   values=["PROMEDIO", "FIFO", "LIFO", "ULTIMO_COSTO"])
        method_combo.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(config_content, text="Agrupar por:").pack(side=tk.LEFT, padx=(20, 0))
        self.group_by = tk.StringVar(value="PRODUCTO")
        group_combo = ttk.Combobox(config_content, textvariable=self.group_by,
                                  values=["PRODUCTO", "CATEGORIA", "PROVEEDOR"])
        group_combo.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(config_content, text="Generar Análisis", 
                  command=self.generate_cost_analysis).pack(side=tk.RIGHT, padx=10)
        
        # Resultado del análisis
        result_frame = ttk.Frame(analysis_frame)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        analysis_columns = ('item', 'stock_inicial', 'entradas', 'salidas', 'stock_final',
                           'costo_inicial', 'costo_entradas', 'costo_salidas', 'costo_final',
                           'variacion_costo', 'rotacion')
        
        self.analysis_tree = ttk.Treeview(result_frame, columns=analysis_columns, 
                                         show='headings', height=15)
        
        # Configurar encabezados análisis
        analysis_headers = {
            'item': 'Item',
            'stock_inicial': 'Stock Ini.',
            'entradas': 'Entradas',
            'salidas': 'Salidas',
            'stock_final': 'Stock Fin.',
            'costo_inicial': 'Costo Ini.',
            'costo_entradas': 'Costo Ent.',
            'costo_salidas': 'Costo Sal.',
            'costo_final': 'Costo Fin.',
            'variacion_costo': 'Var. Costo',
            'rotacion': 'Rotación'
        }
        
        for col, header in analysis_headers.items():
            self.analysis_tree.heading(col, text=header)
            self.analysis_tree.column(col, width=100)
        
        # Scrollbar para análisis
        analysis_scroll = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, 
                                       command=self.analysis_tree.yview)
        self.analysis_tree.configure(yscrollcommand=analysis_scroll.set)
        
        self.analysis_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        analysis_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_closed_periods_tab(self):
        """Configura la pestaña de períodos cerrados"""
        periods_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(periods_frame, text="Períodos Cerrados")
        
        # Botones de acción
        actions_frame = ttk.Frame(periods_frame)
        actions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(actions_frame, text="Nuevo Cierre", 
                  command=self.show_period_close_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Ver Detalle", 
                  command=self.view_period_detail).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Reabrir Período", 
                  command=self.reopen_period).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Exportar Período", 
                  command=self.export_period).pack(side=tk.LEFT, padx=5)
        
        # Lista de períodos cerrados
        periods_list_frame = ttk.Frame(periods_frame)
        periods_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        periods_columns = ('periodo', 'fecha_cierre', 'productos', 'movimientos', 
                          'valor_inventario', 'usuario', 'estado')
        
        self.periods_tree = ttk.Treeview(periods_list_frame, columns=periods_columns, 
                                        show='headings', height=15)
        
        # Configurar encabezados períodos
        periods_headers = {
            'periodo': 'Período',
            'fecha_cierre': 'Fecha Cierre',
            'productos': 'Productos',
            'movimientos': 'Movimientos',
            'valor_inventario': 'Valor Inventario',
            'usuario': 'Usuario',
            'estado': 'Estado'
        }
        
        for col, header in periods_headers.items():
            self.periods_tree.heading(col, text=header)
            self.periods_tree.column(col, width=150)
        
        # Scrollbar para períodos
        periods_scroll = ttk.Scrollbar(periods_list_frame, orient=tk.VERTICAL, 
                                      command=self.periods_tree.yview)
        self.periods_tree.configure(yscrollcommand=periods_scroll.set)
        
        self.periods_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        periods_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind eventos
        self.periods_tree.bind('<<TreeviewSelect>>', self.on_period_select)
        
        # Cargar períodos cerrados
        self.load_closed_periods()
    
    def load_initial_data(self):
        """Carga datos iniciales"""
        try:
            # Cargar productos para el combo
            products = self.product_manager.listar_productos()
            product_list = [f"{p.get('codigo', '')} - {p.get('nombre', '')}" for p in products]
            self.product_combo['values'] = product_list
            
            # Cargar usuarios para el combo
            users = self.kardex_manager.obtener_usuarios_movimientos()
            self.user_combo['values'] = users
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando datos iniciales: {str(e)}")
    
    def on_product_selected(self, event=None):
        """Maneja la selección de producto"""
        selected = self.filter_vars['producto'].get()
        if selected:
            # Extraer código del producto
            codigo = selected.split(' - ')[0]
            self.load_product_kardex(codigo)
    
    def load_product_kardex(self, product_code):
        """Carga el kardex de un producto específico"""
        try:
            # Obtener información del producto
            product = self.product_manager.obtener_producto_por_codigo(product_code)
            if not product:
                return
            
            self.current_product = product
            
            # Actualizar información del producto
            self.product_info_vars['codigo'].set(product.get('codigo', ''))
            self.product_info_vars['nombre'].set(product.get('nombre', ''))
            self.product_info_vars['categoria'].set(product.get('categoria', ''))
            self.product_info_vars['unidad_medida'].set(product.get('unidad_medida', ''))
            self.product_info_vars['stock_actual'].set(f"{product.get('stock_actual', 0)}")
            
            # Calcular costos
            costo_promedio = self.kardex_manager.calcular_costo_promedio(product['id'])
            valor_inventario = product.get('stock_actual', 0) * costo_promedio
            ultimo_costo = self.kardex_manager.obtener_ultimo_costo(product['id'])
            
            self.product_info_vars['costo_promedio'].set(f"₡{costo_promedio:,.2f}")
            self.product_info_vars['valor_inventario'].set(f"₡{valor_inventario:,.2f}")
            self.product_info_vars['ultimo_costo'].set(f"₡{ultimo_costo:,.2f}")
            
            # Cargar movimientos kardex
            self.load_kardex_movements(product['id'])
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando kardex: {str(e)}")
    
    def load_kardex_movements(self, product_id):
        """Carga los movimientos kardex del producto"""
        try:
            # Limpiar árbol actual
            for item in self.kardex_tree.get_children():
                self.kardex_tree.delete(item)
            
            # Obtener fechas de filtro
            fecha_desde = self.filter_vars['fecha_desde'].get()
            fecha_hasta = self.filter_vars['fecha_hasta'].get()
            
            # Obtener movimientos kardex
            movements = self.kardex_manager.obtener_kardex_producto(
                product_id, fecha_desde, fecha_hasta
            )
            
            # Llenar el árbol con los movimientos
            for movement in movements:
                values = (
                    movement.get('fecha_movimiento', ''),
                    movement.get('numero_documento', ''),
                    movement.get('tipo_movimiento', ''),
                    movement.get('cantidad_entrada', '') or '',
                    f"₡{movement.get('costo_entrada', 0):,.2f}" if movement.get('costo_entrada') else '',
                    movement.get('cantidad_salida', '') or '',
                    f"₡{movement.get('costo_salida', 0):,.2f}" if movement.get('costo_salida') else '',
                    movement.get('saldo_cantidad', 0),
                    f"₡{movement.get('saldo_costo', 0):,.2f}",
                    f"₡{movement.get('costo_unitario', 0):,.2f}",
                    movement.get('observaciones', '')
                )
                
                self.kardex_tree.insert('', tk.END, values=values)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando movimientos: {str(e)}")
    
    def apply_filters(self):
        """Aplica los filtros de búsqueda"""
        try:
            # Si hay un producto seleccionado, cargar su kardex
            selected_product = self.filter_vars['producto'].get()
            if selected_product:
                codigo = selected_product.split(' - ')[0]
                self.load_product_kardex(codigo)
            
            # Cargar resumen de movimientos con filtros
            self.load_movements_summary()
            
            # Actualizar estadísticas
            self.update_statistics()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error aplicando filtros: {str(e)}")
    
    def clear_filters(self):
        """Limpia todos los filtros"""
        for key, var in self.filter_vars.items():
            if key in ['fecha_desde', 'fecha_hasta']:
                continue  # Mantener fechas
            var.set('')
        
        # Limpiar datos mostrados
        for item in self.kardex_tree.get_children():
            self.kardex_tree.delete(item)
        
        # Limpiar información del producto
        for var in self.product_info_vars.values():
            var.set('')
        
        self.current_product = None
    
    def load_movements_summary(self):
        """Carga el resumen de movimientos"""
        try:
            # Limpiar árbol de resumen
            for item in self.summary_tree.get_children():
                self.summary_tree.delete(item)
            
            # Obtener filtros
            filters = {
                'fecha_desde': self.filter_vars['fecha_desde'].get(),
                'fecha_hasta': self.filter_vars['fecha_hasta'].get(),
                'tipo_movimiento': self.filter_vars['tipo_movimiento'].get() or None,
                'usuario': self.filter_vars['usuario'].get() or None
            }
            
            # Obtener movimientos
            movements = self.kardex_manager.obtener_resumen_movimientos(filters)
            
            for movement in movements:
                values = (
                    movement.get('fecha_movimiento', ''),
                    movement.get('producto_nombre', ''),
                    movement.get('tipo_movimiento', ''),
                    movement.get('cantidad', 0),
                    f"₡{movement.get('costo_unitario', 0):,.2f}",
                    f"₡{movement.get('costo_total', 0):,.2f}",
                    movement.get('usuario', ''),
                    movement.get('numero_documento', '')
                )
                
                self.summary_tree.insert('', tk.END, values=values)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando resumen: {str(e)}")
    
    def update_statistics(self):
        """Actualiza las estadísticas del período"""
        try:
            # Obtener filtros
            filters = {
                'fecha_desde': self.filter_vars['fecha_desde'].get(),
                'fecha_hasta': self.filter_vars['fecha_hasta'].get(),
                'tipo_movimiento': self.filter_vars['tipo_movimiento'].get() or None
            }
            
            # Obtener estadísticas
            stats = self.kardex_manager.obtener_estadisticas_periodo(filters)
            
            # Actualizar variables
            self.stats_vars['total_entradas'].set(f"{stats.get('total_entradas', 0):,}")
            self.stats_vars['total_salidas'].set(f"{stats.get('total_salidas', 0):,}")
            self.stats_vars['valor_entradas'].set(f"₡{stats.get('valor_entradas', 0):,.2f}")
            self.stats_vars['valor_salidas'].set(f"₡{stats.get('valor_salidas', 0):,.2f}")
            self.stats_vars['productos_movidos'].set(f"{stats.get('productos_movidos', 0)}")
            self.stats_vars['movimientos_registrados'].set(f"{stats.get('movimientos_registrados', 0)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error actualizando estadísticas: {str(e)}")
    
    def generate_cost_analysis(self):
        """Genera el análisis de costos"""
        try:
            # Limpiar árbol de análisis
            for item in self.analysis_tree.get_children():
                self.analysis_tree.delete(item)
            
            # Obtener parámetros de análisis
            method = self.costing_method.get()
            group_by = self.group_by.get()
            
            filters = {
                'fecha_desde': self.filter_vars['fecha_desde'].get(),
                'fecha_hasta': self.filter_vars['fecha_hasta'].get()
            }
            
            # Generar análisis
            analysis = self.kardex_manager.generar_analisis_costos(method, group_by, filters)
            
            for item in analysis:
                values = (
                    item.get('item_name', ''),
                    item.get('stock_inicial', 0),
                    item.get('entradas', 0),
                    item.get('salidas', 0),
                    item.get('stock_final', 0),
                    f"₡{item.get('costo_inicial', 0):,.2f}",
                    f"₡{item.get('costo_entradas', 0):,.2f}",
                    f"₡{item.get('costo_salidas', 0):,.2f}",
                    f"₡{item.get('costo_final', 0):,.2f}",
                    f"{item.get('variacion_costo', 0):,.2f}%",
                    f"{item.get('rotacion', 0):,.2f}"
                )
                
                self.analysis_tree.insert('', tk.END, values=values)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error generando análisis: {str(e)}")
    
    def load_closed_periods(self):
        """Carga los períodos cerrados"""
        try:
            # Limpiar árbol de períodos
            for item in self.periods_tree.get_children():
                self.periods_tree.delete(item)
            
            # Obtener períodos cerrados
            periods = self.kardex_manager.obtener_periodos_cerrados()
            
            for period in periods:
                values = (
                    period.get('nombre_periodo', ''),
                    period.get('fecha_cierre', ''),
                    period.get('total_productos', 0),
                    period.get('total_movimientos', 0),
                    f"₡{period.get('valor_inventario', 0):,.2f}",
                    period.get('usuario_cierre', ''),
                    period.get('estado', '')
                )
                
                self.periods_tree.insert('', tk.END, values=values)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando períodos: {str(e)}")
    
    def on_period_select(self, event):
        """Maneja la selección de período"""
        selection = self.periods_tree.selection()
        if selection:
            item = self.periods_tree.item(selection[0])
            self.current_period = item['values'][0]  # Nombre del período
    
    def show_movement_form(self):
        """Muestra el formulario para nuevo movimiento"""
        KardexMovementDialog(self.parent, self.kardex_manager, self.on_movement_saved)
    
    def close_period(self):
        """Cierra un período contable"""
        PeriodCloseDialog(self.parent, self.kardex_manager, self.on_period_closed)
    
    def show_period_close_dialog(self):
        """Muestra el diálogo de cierre de período"""
        self.close_period()
    
    def view_period_detail(self):
        """Ver detalles del período seleccionado"""
        if not self.current_period:
            messagebox.showwarning("Advertencia", "Seleccione un período")
            return
        
        PeriodDetailDialog(self.parent, self.kardex_manager, self.current_period)
    
    def reopen_period(self):
        """Reabre un período cerrado"""
        if not self.current_period:
            messagebox.showwarning("Advertencia", "Seleccione un período")
            return
        
        if messagebox.askyesno("Confirmar", 
                              f"¿Está seguro de reabrir el período {self.current_period}?\n"
                              "Esta acción permitirá nuevas modificaciones."):
            try:
                success = self.kardex_manager.reabrir_periodo(self.current_period)
                if success:
                    messagebox.showinfo("Éxito", "Período reabierto correctamente")
                    self.load_closed_periods()
                else:
                    messagebox.showerror("Error", "No se pudo reabrir el período")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error reabriendo período: {str(e)}")
    
    def export_period(self):
        """Exporta un período cerrado"""
        if not self.current_period:
            messagebox.showwarning("Advertencia", "Seleccione un período")
            return
        
        file_path = filedialog.asksaveasfilename(
            title=f"Exportar Período {self.current_period}",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")]
        )
        
        if file_path:
            try:
                self.kardex_manager.exportar_periodo(self.current_period, file_path)
                messagebox.showinfo("Éxito", "Período exportado correctamente")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando: {str(e)}")
    
    def generate_kardex_report(self):
        """Genera reporte de kardex"""
        KardexReportDialog(self.parent, self.kardex_manager)
    
    def export_kardex(self):
        """Exporta kardex actual"""
        if not self.current_product:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Exportar Kardex",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")]
        )
        
        if file_path:
            try:
                filters = {
                    'producto_id': self.current_product['id'],
                    'fecha_desde': self.filter_vars['fecha_desde'].get(),
                    'fecha_hasta': self.filter_vars['fecha_hasta'].get()
                }
                
                self.kardex_manager.exportar_kardex(filters, file_path)
                messagebox.showinfo("Éxito", "Kardex exportado correctamente")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando: {str(e)}")
    
    def view_movement_details(self, event):
        """Ver detalles de un movimiento"""
        selection = self.kardex_tree.selection()
        if selection:
            item = self.kardex_tree.item(selection[0])
            # Implementar diálogo de detalles del movimiento
            messagebox.showinfo("Info", "Detalles del movimiento en desarrollo")
    
    def on_movement_saved(self):
        """Callback cuando se guarda un movimiento"""
        if self.current_product:
            self.load_product_kardex(self.current_product['codigo'])
        self.load_movements_summary()
        self.update_statistics()
    
    def on_period_closed(self):
        """Callback cuando se cierra un período"""
        self.load_closed_periods()

# Diálogos adicionales (versiones simplificadas para completar el módulo)
class KardexMovementDialog:
    """Diálogo para registrar movimientos de kardex"""
    
    def __init__(self, parent, kardex_manager, callback=None):
        messagebox.showinfo("Info", "Formulario de movimiento kardex en desarrollo")

class PeriodCloseDialog:
    """Diálogo para cierre de período"""
    
    def __init__(self, parent, kardex_manager, callback=None):
        messagebox.showinfo("Info", "Cierre de período en desarrollo")

class PeriodDetailDialog:
    """Diálogo para detalles de período"""
    
    def __init__(self, parent, kardex_manager, period_name):
        messagebox.showinfo("Info", f"Detalles del período {period_name} en desarrollo")

class KardexReportDialog:
    """Diálogo para reportes de kardex"""
    
    def __init__(self, parent, kardex_manager):
        messagebox.showinfo("Info", "Generador de reportes kardex en desarrollo")

# Función principal
def mostrar_kardex(parent_window):
    """Función principal para mostrar el kardex"""
    KardexUI(parent_window)
