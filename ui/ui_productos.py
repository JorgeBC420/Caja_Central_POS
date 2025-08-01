"""
Interfaz de usuario para gestión de productos
Maneja CRUD de productos, categorías, precios y características
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import Optional, Dict, List, Any
import csv
import json
from decimal import Decimal

from modules.inventory.product import ProductManager
from ui.ui_helpers import create_styled_frame, create_input_frame
from core.database import ejecutar_consulta_segura

class ProductsUI:
    """Interfaz principal para gestión de productos"""
    
    def __init__(self, parent_window):
        self.parent = parent_window
        self.product_manager = ProductManager()
        
        # Variables de estado
        self.current_product = None
        self.products_list = []
        self.categories_list = []
        self.filtered_products = []
        
        # Variables de búsqueda y filtros
        self.search_var = tk.StringVar()
        self.category_filter_var = tk.StringVar()
        self.status_filter_var = tk.StringVar()
        self.stock_filter_var = tk.StringVar()
        
        # Variables del formulario
        self.setup_form_variables()
        
        # Configurar interfaz
        self.setup_ui()
        
        # Cargar datos iniciales
        self.load_initial_data()
        
        # Configurar eventos
        self.setup_events()
    
    def setup_form_variables(self):
        """Configura las variables del formulario"""
        self.form_vars = {
            'id': tk.StringVar(),
            'codigo': tk.StringVar(),
            'codigo_barras': tk.StringVar(),
            'nombre': tk.StringVar(),
            'descripcion': tk.StringVar(),
            'categoria_id': tk.StringVar(),
            'marca': tk.StringVar(),
            'modelo': tk.StringVar(),
            'unidad_medida': tk.StringVar(),
            'precio_compra': tk.StringVar(),
            'precio_venta': tk.StringVar(),
            'precio_mayoreo': tk.StringVar(),
            'stock_minimo': tk.StringVar(),
            'stock_maximo': tk.StringVar(),
            'stock_actual': tk.StringVar(),
            'ubicacion': tk.StringVar(),
            'proveedor': tk.StringVar(),
            'iva_incluido': tk.BooleanVar(),
            'activo': tk.BooleanVar(value=True),
            'peso': tk.StringVar(),
            'dimensiones': tk.StringVar(),
            'color': tk.StringVar(),
            'talla': tk.StringVar(),
            'garantia_meses': tk.StringVar(),
            'imagen_url': tk.StringVar(),
            'notas': tk.StringVar()
        }
        
        # Variables de configuración
        self.config_vars = {
            'auto_codigo': tk.BooleanVar(value=True),
            'validar_stock': tk.BooleanVar(value=True),
            'precio_automatico': tk.BooleanVar(),
            'margen_utilidad': tk.StringVar(value="30"),
            'alertas_stock': tk.BooleanVar(value=True)
        }
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Frame principal
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="Gestión de Productos", 
                 font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        # Botones principales
        buttons_frame = ttk.Frame(title_frame)
        buttons_frame.pack(side=tk.RIGHT)
        
        ttk.Button(buttons_frame, text="Nuevo Producto", 
                  command=self.new_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Importar", 
                  command=self.import_products).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Exportar", 
                  command=self.export_products).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Configuración", 
                  command=self.show_config).pack(side=tk.LEFT, padx=5)
        
        # Crear notebook principal
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña de lista de productos
        self.setup_products_list_tab()
        
        # Pestaña de formulario de producto
        self.setup_product_form_tab()
        
        # Pestaña de categorías
        self.setup_categories_tab()
        
        # Pestaña de reportes
        self.setup_reports_tab()
        
        # Pestaña de configuración
        self.setup_config_tab()
    
    def setup_products_list_tab(self):
        """Configura la pestaña de lista de productos"""
        list_frame = ttk.Frame(self.notebook)
        self.notebook.add(list_frame, text="Lista de Productos")
        
        # Panel de búsqueda y filtros
        search_frame = create_styled_frame(list_frame, "Búsqueda y Filtros")
        search_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        search_content = ttk.Frame(search_frame)
        search_content.pack(fill=tk.X, padx=15, pady=10)
        
        # Fila 1: Búsqueda general
        search_row1 = ttk.Frame(search_content)
        search_row1.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_row1, text="Búsqueda:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_row1, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Button(search_row1, text="Buscar", 
                  command=self.search_products).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_row1, text="Limpiar", 
                  command=self.clear_search).pack(side=tk.LEFT, padx=5)
        
        # Fila 2: Filtros
        search_row2 = ttk.Frame(search_content)
        search_row2.pack(fill=tk.X)
        
        # Filtro por categoría
        ttk.Label(search_row2, text="Categoría:").pack(side=tk.LEFT)
        self.category_combo = ttk.Combobox(search_row2, textvariable=self.category_filter_var, 
                                          width=15, state="readonly")
        self.category_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        # Filtro por estado
        ttk.Label(search_row2, text="Estado:").pack(side=tk.LEFT)
        status_combo = ttk.Combobox(search_row2, textvariable=self.status_filter_var, 
                                   width=12, state="readonly")
        status_combo['values'] = ("Todos", "Activo", "Inactivo")
        status_combo.current(0)
        status_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        # Filtro por stock
        ttk.Label(search_row2, text="Stock:").pack(side=tk.LEFT)
        stock_combo = ttk.Combobox(search_row2, textvariable=self.stock_filter_var, 
                                  width=15, state="readonly")
        stock_combo['values'] = ("Todos", "Stock Normal", "Stock Bajo", "Sin Stock", "Sobre Stock")
        stock_combo.current(0)
        stock_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Button(search_row2, text="Filtrar", 
                  command=self.apply_filters).pack(side=tk.LEFT, padx=(10, 0))
        
        # Lista de productos
        products_frame = create_styled_frame(list_frame, "Productos")
        products_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configurar TreeView
        columns = ('codigo', 'codigo_barras', 'nombre', 'categoria', 'precio_venta', 
                  'stock_actual', 'stock_minimo', 'estado')
        
        self.products_tree = ttk.Treeview(products_frame, columns=columns, show='headings', height=15)
        
        # Configurar columnas
        self.products_tree.heading('codigo', text='Código')
        self.products_tree.heading('codigo_barras', text='Código Barras')
        self.products_tree.heading('nombre', text='Nombre')
        self.products_tree.heading('categoria', text='Categoría')
        self.products_tree.heading('precio_venta', text='Precio Venta')
        self.products_tree.heading('stock_actual', text='Stock')
        self.products_tree.heading('stock_minimo', text='Min.')
        self.products_tree.heading('estado', text='Estado')
        
        # Anchos de columnas
        self.products_tree.column('codigo', width=80)
        self.products_tree.column('codigo_barras', width=120)
        self.products_tree.column('nombre', width=200)
        self.products_tree.column('categoria', width=120)
        self.products_tree.column('precio_venta', width=100)
        self.products_tree.column('stock_actual', width=80)
        self.products_tree.column('stock_minimo', width=60)
        self.products_tree.column('estado', width=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(products_frame, orient=tk.VERTICAL, command=self.products_tree.yview)
        h_scrollbar = ttk.Scrollbar(products_frame, orient=tk.HORIZONTAL, command=self.products_tree.xview)
        self.products_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Empaquetar TreeView y scrollbars
        self.products_tree.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        v_scrollbar.grid(row=0, column=1, sticky='ns', pady=10)
        h_scrollbar.grid(row=1, column=0, sticky='ew', padx=10)
        
        products_frame.grid_rowconfigure(0, weight=1)
        products_frame.grid_columnconfigure(0, weight=1)
        
        # Panel de acciones
        actions_frame = ttk.Frame(list_frame)
        actions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(actions_frame, text="Ver Detalles", 
                  command=self.view_product_details).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Editar", 
                  command=self.edit_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Eliminar", 
                  command=self.delete_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Duplicar", 
                  command=self.duplicate_product).pack(side=tk.LEFT, padx=5)
        
        # Separador
        ttk.Separator(actions_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(actions_frame, text="Movimiento Stock", 
                  command=self.stock_movement).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Historial", 
                  command=self.product_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Etiquetas", 
                  command=self.print_labels).pack(side=tk.LEFT, padx=5)
        
        # Información de totales
        totals_frame = ttk.Frame(actions_frame)
        totals_frame.pack(side=tk.RIGHT)
        
        self.totals_label = ttk.Label(totals_frame, text="Total productos: 0", 
                                     font=('Arial', 10, 'bold'))
        self.totals_label.pack()
    
    def setup_product_form_tab(self):
        """Configura la pestaña del formulario de producto"""
        form_frame = ttk.Frame(self.notebook)
        self.notebook.add(form_frame, text="Formulario de Producto")
        
        # Crear canvas con scrollbar para el formulario
        canvas = tk.Canvas(form_frame)
        scrollbar = ttk.Scrollbar(form_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Contenido del formulario
        content_frame = ttk.Frame(scrollable_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título del formulario
        form_title_frame = ttk.Frame(content_frame)
        form_title_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.form_title_label = ttk.Label(form_title_frame, text="Nuevo Producto", 
                                         font=('Arial', 14, 'bold'))
        self.form_title_label.pack(side=tk.LEFT)
        
        # Botones del formulario
        form_buttons_frame = ttk.Frame(form_title_frame)
        form_buttons_frame.pack(side=tk.RIGHT)
        
        ttk.Button(form_buttons_frame, text="Guardar", 
                  command=self.save_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(form_buttons_frame, text="Limpiar", 
                  command=self.clear_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(form_buttons_frame, text="Cancelar", 
                  command=self.cancel_form).pack(side=tk.LEFT, padx=5)
        
        # Sección 1: Información básica
        basic_frame = create_styled_frame(content_frame, "Información Básica")
        basic_frame.pack(fill=tk.X, pady=(0, 15))
        
        basic_content = ttk.Frame(basic_frame)
        basic_content.pack(fill=tk.X, padx=15, pady=10)
        
        # Fila 1
        row1 = ttk.Frame(basic_content)
        row1.pack(fill=tk.X, pady=(0, 10))
        
        # ID (solo lectura)
        col1 = ttk.Frame(row1)
        col1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(col1, text="ID:").pack(anchor=tk.W)
        id_entry = ttk.Entry(col1, textvariable=self.form_vars['id'], state='readonly', width=20)
        id_entry.pack(fill=tk.X, pady=(2, 0))
        
        # Código
        col2 = ttk.Frame(row1)
        col2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        ttk.Label(col2, text="Código *:").pack(anchor=tk.W)
        codigo_entry = ttk.Entry(col2, textvariable=self.form_vars['codigo'], width=20)
        codigo_entry.pack(fill=tk.X, pady=(2, 0))
        
        # Código de barras
        col3 = ttk.Frame(row1)
        col3.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        ttk.Label(col3, text="Código de Barras:").pack(anchor=tk.W)
        barcode_frame = ttk.Frame(col3)
        barcode_frame.pack(fill=tk.X, pady=(2, 0))
        ttk.Entry(barcode_frame, textvariable=self.form_vars['codigo_barras']).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(barcode_frame, text="📷", width=3, 
                  command=self.scan_barcode).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Fila 2
        row2 = ttk.Frame(basic_content)
        row2.pack(fill=tk.X, pady=(0, 10))
        
        # Nombre
        col1 = ttk.Frame(row2)
        col1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(col1, text="Nombre *:").pack(anchor=tk.W)
        ttk.Entry(col1, textvariable=self.form_vars['nombre'], width=30).pack(fill=tk.X, pady=(2, 0))
        
        # Categoría
        col2 = ttk.Frame(row2)
        col2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        ttk.Label(col2, text="Categoría:").pack(anchor=tk.W)
        self.category_form_combo = ttk.Combobox(col2, textvariable=self.form_vars['categoria_id'], 
                                               width=20, state="readonly")
        self.category_form_combo.pack(fill=tk.X, pady=(2, 0))
        
        # Fila 3 - Descripción
        row3 = ttk.Frame(basic_content)
        row3.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(row3, text="Descripción:").pack(anchor=tk.W)
        desc_text = tk.Text(row3, height=3, wrap=tk.WORD)
        desc_text.pack(fill=tk.X, pady=(2, 0))
        # Vincular texto con variable
        desc_text.bind('<KeyRelease>', lambda e: self.form_vars['descripcion'].set(desc_text.get('1.0', tk.END).strip()))
        
        # Sección 2: Detalles del producto
        details_frame = create_styled_frame(content_frame, "Detalles del Producto")
        details_frame.pack(fill=tk.X, pady=(0, 15))
        
        details_content = ttk.Frame(details_frame)
        details_content.pack(fill=tk.X, padx=15, pady=10)
        
        # Fila 1
        details_row1 = ttk.Frame(details_content)
        details_row1.pack(fill=tk.X, pady=(0, 10))
        
        # Marca
        col1 = ttk.Frame(details_row1)
        col1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(col1, text="Marca:").pack(anchor=tk.W)
        ttk.Entry(col1, textvariable=self.form_vars['marca']).pack(fill=tk.X, pady=(2, 0))
        
        # Modelo
        col2 = ttk.Frame(details_row1)
        col2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        ttk.Label(col2, text="Modelo:").pack(anchor=tk.W)
        ttk.Entry(col2, textvariable=self.form_vars['modelo']).pack(fill=tk.X, pady=(2, 0))
        
        # Unidad de medida
        col3 = ttk.Frame(details_row1)
        col3.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        ttk.Label(col3, text="Unidad:").pack(anchor=tk.W)
        unidad_combo = ttk.Combobox(col3, textvariable=self.form_vars['unidad_medida'], 
                                   values=("Unidad", "Kg", "Lt", "m", "m²", "m³", "Caja", "Paquete"))
        unidad_combo.pack(fill=tk.X, pady=(2, 0))
        
        # Fila 2 - Características físicas
        details_row2 = ttk.Frame(details_content)
        details_row2.pack(fill=tk.X, pady=(0, 10))
        
        # Peso
        col1 = ttk.Frame(details_row2)
        col1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(col1, text="Peso (kg):").pack(anchor=tk.W)
        ttk.Entry(col1, textvariable=self.form_vars['peso']).pack(fill=tk.X, pady=(2, 0))
        
        # Dimensiones
        col2 = ttk.Frame(details_row2)
        col2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        ttk.Label(col2, text="Dimensiones (LxAxA):").pack(anchor=tk.W)
        ttk.Entry(col2, textvariable=self.form_vars['dimensiones']).pack(fill=tk.X, pady=(2, 0))
        
        # Color
        col3 = ttk.Frame(details_row2)
        col3.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        ttk.Label(col3, text="Color:").pack(anchor=tk.W)
        ttk.Entry(col3, textvariable=self.form_vars['color']).pack(fill=tk.X, pady=(2, 0))
        
        # Fila 3
        details_row3 = ttk.Frame(details_content)
        details_row3.pack(fill=tk.X, pady=(0, 10))
        
        # Talla
        col1 = ttk.Frame(details_row3)
        col1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(col1, text="Talla:").pack(anchor=tk.W)
        ttk.Entry(col1, textvariable=self.form_vars['talla']).pack(fill=tk.X, pady=(2, 0))
        
        # Garantía
        col2 = ttk.Frame(details_row3)
        col2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        ttk.Label(col2, text="Garantía (meses):").pack(anchor=tk.W)
        ttk.Entry(col2, textvariable=self.form_vars['garantia_meses']).pack(fill=tk.X, pady=(2, 0))
        
        # Proveedor
        col3 = ttk.Frame(details_row3)
        col3.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        ttk.Label(col3, text="Proveedor:").pack(anchor=tk.W)
        ttk.Entry(col3, textvariable=self.form_vars['proveedor']).pack(fill=tk.X, pady=(2, 0))
        
        # Sección 3: Precios
        prices_frame = create_styled_frame(content_frame, "Precios")
        prices_frame.pack(fill=tk.X, pady=(0, 15))
        
        prices_content = ttk.Frame(prices_frame)
        prices_content.pack(fill=tk.X, padx=15, pady=10)
        
        # Fila 1
        prices_row1 = ttk.Frame(prices_content)
        prices_row1.pack(fill=tk.X, pady=(0, 10))
        
        # Precio de compra
        col1 = ttk.Frame(prices_row1)
        col1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(col1, text="Precio Compra:").pack(anchor=tk.W)
        ttk.Entry(col1, textvariable=self.form_vars['precio_compra']).pack(fill=tk.X, pady=(2, 0))
        
        # Precio de venta
        col2 = ttk.Frame(prices_row1)
        col2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        ttk.Label(col2, text="Precio Venta *:").pack(anchor=tk.W)
        precio_venta_frame = ttk.Frame(col2)
        precio_venta_frame.pack(fill=tk.X, pady=(2, 0))
        ttk.Entry(precio_venta_frame, textvariable=self.form_vars['precio_venta']).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(precio_venta_frame, text="Auto", width=5, 
                  command=self.calculate_sale_price).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Precio mayoreo
        col3 = ttk.Frame(prices_row1)
        col3.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        ttk.Label(col3, text="Precio Mayoreo:").pack(anchor=tk.W)
        ttk.Entry(col3, textvariable=self.form_vars['precio_mayoreo']).pack(fill=tk.X, pady=(2, 0))
        
        # Fila 2 - Opciones de precio
        prices_row2 = ttk.Frame(prices_content)
        prices_row2.pack(fill=tk.X)
        
        ttk.Checkbutton(prices_row2, text="IVA incluido en precio", 
                       variable=self.form_vars['iva_incluido']).pack(side=tk.LEFT)
        
        # Margen de utilidad
        margin_frame = ttk.Frame(prices_row2)
        margin_frame.pack(side=tk.RIGHT)
        ttk.Label(margin_frame, text="Margen %:").pack(side=tk.LEFT)
        ttk.Entry(margin_frame, textvariable=self.config_vars['margen_utilidad'], 
                 width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        # Sección 4: Inventario
        inventory_frame = create_styled_frame(content_frame, "Inventario")
        inventory_frame.pack(fill=tk.X, pady=(0, 15))
        
        inventory_content = ttk.Frame(inventory_frame)
        inventory_content.pack(fill=tk.X, padx=15, pady=10)
        
        # Fila 1
        inventory_row1 = ttk.Frame(inventory_content)
        inventory_row1.pack(fill=tk.X, pady=(0, 10))
        
        # Stock actual
        col1 = ttk.Frame(inventory_row1)
        col1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(col1, text="Stock Actual:").pack(anchor=tk.W)
        ttk.Entry(col1, textvariable=self.form_vars['stock_actual']).pack(fill=tk.X, pady=(2, 0))
        
        # Stock mínimo
        col2 = ttk.Frame(inventory_row1)
        col2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        ttk.Label(col2, text="Stock Mínimo:").pack(anchor=tk.W)
        ttk.Entry(col2, textvariable=self.form_vars['stock_minimo']).pack(fill=tk.X, pady=(2, 0))
        
        # Stock máximo
        col3 = ttk.Frame(inventory_row1)
        col3.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        ttk.Label(col3, text="Stock Máximo:").pack(anchor=tk.W)
        ttk.Entry(col3, textvariable=self.form_vars['stock_maximo']).pack(fill=tk.X, pady=(2, 0))
        
        # Fila 2
        inventory_row2 = ttk.Frame(inventory_content)
        inventory_row2.pack(fill=tk.X)
        
        # Ubicación
        col1 = ttk.Frame(inventory_row2)
        col1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(col1, text="Ubicación:").pack(anchor=tk.W)
        ttk.Entry(col1, textvariable=self.form_vars['ubicacion']).pack(fill=tk.X, pady=(2, 0))
        
        # Estado
        col2 = ttk.Frame(inventory_row2)
        col2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        ttk.Checkbutton(col2, text="Producto Activo", 
                       variable=self.form_vars['activo']).pack(anchor=tk.W, pady=10)
        
        # Sección 5: Imagen y notas
        extras_frame = create_styled_frame(content_frame, "Imagen y Notas")
        extras_frame.pack(fill=tk.X, pady=(0, 15))
        
        extras_content = ttk.Frame(extras_frame)
        extras_content.pack(fill=tk.X, padx=15, pady=10)
        
        # Imagen
        image_row = ttk.Frame(extras_content)
        image_row.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(image_row, text="Imagen URL:").pack(anchor=tk.W)
        image_frame = ttk.Frame(image_row)
        image_frame.pack(fill=tk.X, pady=(2, 0))
        ttk.Entry(image_frame, textvariable=self.form_vars['imagen_url']).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(image_frame, text="Examinar", 
                  command=self.browse_image).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Vista previa de imagen
        self.image_preview_label = ttk.Label(image_row, text="Sin imagen", 
                                           background='lightgray', width=20, 
                                           anchor=tk.CENTER)
        self.image_preview_label.pack(pady=5)
        
        # Notas
        notes_row = ttk.Frame(extras_content)
        notes_row.pack(fill=tk.X)
        
        ttk.Label(notes_row, text="Notas:").pack(anchor=tk.W)
        self.notes_text = tk.Text(notes_row, height=4, wrap=tk.WORD)
        self.notes_text.pack(fill=tk.X, pady=(2, 0))
        self.notes_text.bind('<KeyRelease>', lambda e: self.form_vars['notas'].set(self.notes_text.get('1.0', tk.END).strip()))
        
        # Vincular scroll del mouse al canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def setup_categories_tab(self):
        """Configura la pestaña de categorías"""
        categories_frame = ttk.Frame(self.notebook)
        self.notebook.add(categories_frame, text="Categorías")
        
        messagebox.showinfo("Info", "Gestión de categorías en desarrollo")
    
    def setup_reports_tab(self):
        """Configura la pestaña de reportes"""
        reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(reports_frame, text="Reportes")
        
        messagebox.showinfo("Info", "Reportes de productos en desarrollo")
    
    def setup_config_tab(self):
        """Configura la pestaña de configuración"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="Configuración")
        
        config_content = ttk.Frame(config_frame)
        config_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Configuraciones generales
        general_frame = create_styled_frame(config_content, "Configuración General")
        general_frame.pack(fill=tk.X, pady=(0, 15))
        
        general_content = ttk.Frame(general_frame)
        general_content.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Checkbutton(general_content, text="Generar código automáticamente", 
                       variable=self.config_vars['auto_codigo']).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(general_content, text="Validar stock al vender", 
                       variable=self.config_vars['validar_stock']).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(general_content, text="Calcular precio automáticamente", 
                       variable=self.config_vars['precio_automatico']).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(general_content, text="Alertas de stock bajo", 
                       variable=self.config_vars['alertas_stock']).pack(anchor=tk.W, pady=2)
        
        # Margen de utilidad por defecto
        margin_frame = ttk.Frame(general_content)
        margin_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(margin_frame, text="Margen de utilidad por defecto (%):").pack(side=tk.LEFT)
        ttk.Entry(margin_frame, textvariable=self.config_vars['margen_utilidad'], 
                 width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Botones de configuración
        config_buttons_frame = ttk.Frame(config_content)
        config_buttons_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(config_buttons_frame, text="Guardar Configuración", 
                  command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_buttons_frame, text="Restaurar Valores", 
                  command=self.restore_config).pack(side=tk.LEFT, padx=5)
    
    def setup_events(self):
        """Configura los eventos de la interfaz"""
        # Eventos del TreeView
        self.products_tree.bind('<Double-1>', self.on_product_double_click)
        self.products_tree.bind('<ButtonRelease-1>', self.on_product_select)
        
        # Eventos de búsqueda
        self.search_var.trace('w', self.on_search_change)
        self.category_filter_var.trace('w', self.on_filter_change)
        self.status_filter_var.trace('w', self.on_filter_change)
        self.stock_filter_var.trace('w', self.on_filter_change)
        
        # Eventos del formulario
        self.form_vars['precio_compra'].trace('w', self.on_price_change)
        self.form_vars['codigo'].trace('w', self.on_code_change)
    
    def load_initial_data(self):
        """Carga los datos iniciales"""
        self.load_categories()
        self.load_products()
    
    def load_categories(self):
        """Carga las categorías disponibles"""
        try:
            query = "SELECT id, nombre FROM categorias WHERE activo = 1 ORDER BY nombre"
            resultado = ejecutar_consulta_segura(query)
            
            self.categories_list = []
            category_values = ["Seleccionar..."]
            
            if resultado:
                for row in resultado:
                    category_data = {'id': row[0], 'nombre': row[1]}
                    self.categories_list.append(category_data)
                    category_values.append(f"{row[0]} - {row[1]}")
            
            # Actualizar comboboxes
            self.category_combo['values'] = category_values
            self.category_form_combo['values'] = category_values
            
            if category_values:
                self.category_combo.current(0)
                self.category_form_combo.current(0)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando categorías: {str(e)}")
    
    def load_products(self):
        """Carga la lista de productos"""
        try:
            query = """
                SELECT p.id, p.codigo, p.codigo_barras, p.nombre, c.nombre as categoria,
                       p.precio_venta, p.stock_actual, p.stock_minimo, p.activo
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                ORDER BY p.nombre
            """
            
            resultado = ejecutar_consulta_segura(query)
            
            # Limpiar TreeView
            for item in self.products_tree.get_children():
                self.products_tree.delete(item)
            
            self.products_list = []
            
            if resultado:
                for row in resultado:
                    product_data = {
                        'id': row[0],
                        'codigo': row[1],
                        'codigo_barras': row[2] or '',
                        'nombre': row[3],
                        'categoria': row[4] or 'Sin categoría',
                        'precio_venta': row[5],
                        'stock_actual': row[6],
                        'stock_minimo': row[7],
                        'activo': row[8]
                    }
                    
                    self.products_list.append(product_data)
                    
                    # Estado del producto
                    estado = "Activo" if product_data['activo'] else "Inactivo"
                    
                    # Insertar en TreeView
                    self.products_tree.insert('', tk.END, values=(
                        product_data['codigo'],
                        product_data['codigo_barras'],
                        product_data['nombre'],
                        product_data['categoria'],
                        f"₡{product_data['precio_venta']:,.2f}",
                        product_data['stock_actual'],
                        product_data['stock_minimo'],
                        estado
                    ))
            
            # Actualizar totales
            self.update_totals()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando productos: {str(e)}")
    
    def update_totals(self):
        """Actualiza la información de totales"""
        total_products = len(self.products_list)
        active_products = len([p for p in self.products_list if p['activo']])
        
        self.totals_label.config(text=f"Total: {total_products} | Activos: {active_products}")
    
    # Métodos de búsqueda y filtros
    def search_products(self):
        """Busca productos por texto"""
        search_text = self.search_var.get().lower()
        
        if not search_text:
            self.load_products()
            return
        
        # Filtrar productos
        filtered = []
        for product in self.products_list:
            if (search_text in product['nombre'].lower() or
                search_text in product['codigo'].lower() or
                search_text in product['codigo_barras'].lower()):
                filtered.append(product)
        
        self.display_filtered_products(filtered)
    
    def clear_search(self):
        """Limpia la búsqueda"""
        self.search_var.set("")
        self.category_filter_var.set("Todos")
        self.status_filter_var.set("Todos")
        self.stock_filter_var.set("Todos")
        self.load_products()
    
    def apply_filters(self):
        """Aplica los filtros seleccionados"""
        filtered = list(self.products_list)
        
        # Filtro por categoría
        category_filter = self.category_filter_var.get()
        if category_filter and category_filter != "Todos":
            category_name = category_filter.split(" - ")[-1]
            filtered = [p for p in filtered if p['categoria'] == category_name]
        
        # Filtro por estado
        status_filter = self.status_filter_var.get()
        if status_filter == "Activo":
            filtered = [p for p in filtered if p['activo']]
        elif status_filter == "Inactivo":
            filtered = [p for p in filtered if not p['activo']]
        
        # Filtro por stock
        stock_filter = self.stock_filter_var.get()
        if stock_filter == "Stock Bajo":
            filtered = [p for p in filtered if p['stock_actual'] <= p['stock_minimo']]
        elif stock_filter == "Sin Stock":
            filtered = [p for p in filtered if p['stock_actual'] <= 0]
        elif stock_filter == "Sobre Stock":
            filtered = [p for p in filtered if p['stock_actual'] > p['stock_minimo'] * 2]
        
        self.display_filtered_products(filtered)
    
    def display_filtered_products(self, products):
        """Muestra productos filtrados"""
        # Limpiar TreeView
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        for product in products:
            estado = "Activo" if product['activo'] else "Inactivo"
            
            self.products_tree.insert('', tk.END, values=(
                product['codigo'],
                product['codigo_barras'],
                product['nombre'],
                product['categoria'],
                f"₡{product['precio_venta']:,.2f}",
                product['stock_actual'],
                product['stock_minimo'],
                estado
            ))
    
    def on_search_change(self, *args):
        """Maneja cambios en el campo de búsqueda"""
        # Búsqueda automática después de 500ms de inactividad
        if hasattr(self, 'search_timer'):
            self.parent.after_cancel(self.search_timer)
        self.search_timer = self.parent.after(500, self.search_products)
    
    def on_filter_change(self, *args):
        """Maneja cambios en los filtros"""
        self.apply_filters()
    
    # Métodos del formulario
    def new_product(self):
        """Crea un nuevo producto"""
        self.clear_form()
        self.form_title_label.config(text="Nuevo Producto")
        self.notebook.select(1)  # Cambiar a pestaña de formulario
        
        # Generar código automático si está habilitado
        if self.config_vars['auto_codigo'].get():
            self.generate_product_code()
    
    def edit_product(self):
        """Edita el producto seleccionado"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un producto para editar")
            return
        
        # Obtener datos del producto seleccionado
        item = self.products_tree.item(selection[0])
        codigo = item['values'][0]
        
        # Buscar producto completo
        try:
            product = self.product_manager.obtener_por_codigo(codigo)
            if product:
                self.load_product_to_form(product)
                self.form_title_label.config(text=f"Editar Producto - {product['nombre']}")
                self.notebook.select(1)  # Cambiar a pestaña de formulario
            else:
                messagebox.showerror("Error", "No se pudo cargar el producto")
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando producto: {str(e)}")
    
    def load_product_to_form(self, product):
        """Carga un producto al formulario"""
        # Limpiar formulario primero
        self.clear_form()
        
        # Cargar datos
        for key, var in self.form_vars.items():
            if key in product and product[key] is not None:
                if isinstance(var, tk.BooleanVar):
                    var.set(bool(product[key]))
                else:
                    var.set(str(product[key]))
        
        # Cargar descripción y notas en los Text widgets
        if 'descripcion' in product and product['descripcion']:
            # Aquí cargarías en el Text widget de descripción
            pass
        
        if 'notas' in product and product['notas']:
            self.notes_text.delete('1.0', tk.END)
            self.notes_text.insert('1.0', product['notas'])
    
    def save_product(self):
        """Guarda el producto actual"""
        try:
            # Validar campos requeridos
            if not self.form_vars['nombre'].get().strip():
                messagebox.showerror("Error", "El nombre del producto es requerido")
                return
            
            if not self.form_vars['codigo'].get().strip():
                messagebox.showerror("Error", "El código del producto es requerido")
                return
            
            if not self.form_vars['precio_venta'].get():
                messagebox.showerror("Error", "El precio de venta es requerido")
                return
            
            # Preparar datos del producto
            product_data = {}
            for key, var in self.form_vars.items():
                if key == 'id' and not var.get():
                    continue  # Skip empty ID for new products
                
                value = var.get()
                if isinstance(var, tk.BooleanVar):
                    product_data[key] = value
                elif value:  # Only include non-empty values
                    product_data[key] = value
            
            # Obtener descripción y notas de los Text widgets
            # product_data['descripcion'] = descripción del Text widget
            product_data['notas'] = self.notes_text.get('1.0', tk.END).strip()
            
            # Validar precios
            try:
                if product_data.get('precio_venta'):
                    float(product_data['precio_venta'])
                if product_data.get('precio_compra'):
                    float(product_data['precio_compra'])
                if product_data.get('precio_mayoreo'):
                    float(product_data['precio_mayoreo'])
            except ValueError:
                messagebox.showerror("Error", "Los precios deben ser números válidos")
                return
            
            # Guardar producto
            if product_data.get('id'):
                # Actualizar producto existente
                resultado = self.product_manager.actualizar(product_data['id'], product_data)
                if resultado:
                    messagebox.showinfo("Éxito", "Producto actualizado correctamente")
                else:
                    messagebox.showerror("Error", "No se pudo actualizar el producto")
            else:
                # Crear nuevo producto
                resultado = self.product_manager.crear(product_data)
                if resultado:
                    messagebox.showinfo("Éxito", "Producto creado correctamente")
                    self.form_vars['id'].set(str(resultado))
                else:
                    messagebox.showerror("Error", "No se pudo crear el producto")
            
            # Recargar lista de productos
            self.load_products()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando producto: {str(e)}")
    
    def clear_form(self):
        """Limpia el formulario"""
        for var in self.form_vars.values():
            if isinstance(var, tk.BooleanVar):
                var.set(False)
            else:
                var.set("")
        
        # Limpiar Text widgets
        self.notes_text.delete('1.0', tk.END)
        
        # Valores por defecto
        self.form_vars['activo'].set(True)
        self.form_vars['unidad_medida'].set("Unidad")
        
        # Limpiar imagen
        self.image_preview_label.config(text="Sin imagen")
    
    def cancel_form(self):
        """Cancela la edición del formulario"""
        if messagebox.askyesno("Cancelar", "¿Desea cancelar los cambios?"):
            self.clear_form()
            self.notebook.select(0)  # Volver a la lista de productos
    
    # Métodos auxiliares
    def generate_product_code(self):
        """Genera código automático para el producto"""
        try:
            # Buscar el último código usado
            query = "SELECT MAX(CAST(codigo AS INTEGER)) FROM productos WHERE codigo REGEXP '^[0-9]+$'"
            resultado = ejecutar_consulta_segura(query)
            
            if resultado and resultado[0][0]:
                next_code = int(resultado[0][0]) + 1
            else:
                next_code = 1
            
            self.form_vars['codigo'].set(str(next_code).zfill(6))  # Código con ceros a la izquierda
            
        except Exception as e:
            print(f"Error generando código: {e}")
            self.form_vars['codigo'].set("000001")
    
    def calculate_sale_price(self):
        """Calcula precio de venta basado en precio de compra y margen"""
        try:
            precio_compra = float(self.form_vars['precio_compra'].get() or 0)
            margen = float(self.config_vars['margen_utilidad'].get() or 30)
            
            if precio_compra > 0:
                precio_venta = precio_compra * (1 + margen / 100)
                self.form_vars['precio_venta'].set(f"{precio_venta:.2f}")
            
        except ValueError:
            messagebox.showerror("Error", "Ingrese valores numéricos válidos")
    
    def scan_barcode(self):
        """Abre el lector de códigos de barras"""
        messagebox.showinfo("Info", "Integración con lector de códigos en desarrollo")
    
    def browse_image(self):
        """Examina archivo de imagen"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar Imagen",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if file_path:
            self.form_vars['imagen_url'].set(file_path)
            self.image_preview_label.config(text="Imagen seleccionada")
            # TODO: Mostrar vista previa de la imagen
    
    # Eventos del formulario
    def on_price_change(self, *args):
        """Maneja cambios en el precio de compra"""
        if self.config_vars['precio_automatico'].get():
            self.calculate_sale_price()
    
    def on_code_change(self, *args):
        """Maneja cambios en el código del producto"""
        # Validar que el código no exista
        pass
    
    # Eventos de la lista
    def on_product_double_click(self, event):
        """Maneja doble clic en producto"""
        self.edit_product()
    
    def on_product_select(self, event):
        """Maneja selección de producto"""
        selection = self.products_tree.selection()
        if selection:
            # Habilitar botones de acción
            pass
    
    # Métodos de acciones
    def view_product_details(self):
        """Ver detalles del producto seleccionado"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return
        
        messagebox.showinfo("Info", "Vista de detalles en desarrollo")
    
    def delete_product(self):
        """Elimina el producto seleccionado"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un producto para eliminar")
            return
        
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este producto?"):
            item = self.products_tree.item(selection[0])
            codigo = item['values'][0]
            
            try:
                resultado = self.product_manager.eliminar(codigo)
                if resultado:
                    messagebox.showinfo("Éxito", "Producto eliminado correctamente")
                    self.load_products()
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el producto")
            except Exception as e:
                messagebox.showerror("Error", f"Error eliminando producto: {str(e)}")
    
    def duplicate_product(self):
        """Duplica el producto seleccionado"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un producto para duplicar")
            return
        
        messagebox.showinfo("Info", "Función de duplicar en desarrollo")
    
    def stock_movement(self):
        """Movimiento de stock del producto seleccionado"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return
        
        messagebox.showinfo("Info", "Movimiento de stock en desarrollo")
    
    def product_history(self):
        """Historial del producto seleccionado"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return
        
        messagebox.showinfo("Info", "Historial de producto en desarrollo")
    
    def print_labels(self):
        """Imprime etiquetas del producto seleccionado"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return
        
        messagebox.showinfo("Info", "Impresión de etiquetas en desarrollo")
    
    # Métodos de importación/exportación
    def import_products(self):
        """Importa productos desde archivo"""
        file_path = filedialog.askopenfilename(
            title="Importar Productos",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if file_path:
            messagebox.showinfo("Info", "Importación de productos en desarrollo")
    
    def export_products(self):
        """Exporta productos a archivo"""
        file_path = filedialog.asksaveasfilename(
            title="Exportar Productos",
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    
                    # Encabezados
                    writer.writerow(['Código', 'Código Barras', 'Nombre', 'Categoría', 
                                   'Precio Venta', 'Stock Actual', 'Stock Mínimo', 'Estado'])
                    
                    # Datos
                    for product in self.products_list:
                        writer.writerow([
                            product['codigo'],
                            product['codigo_barras'],
                            product['nombre'],
                            product['categoria'],
                            product['precio_venta'],
                            product['stock_actual'],
                            product['stock_minimo'],
                            'Activo' if product['activo'] else 'Inactivo'
                        ])
                
                messagebox.showinfo("Éxito", "Productos exportados correctamente")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando: {str(e)}")
    
    # Configuración
    def show_config(self):
        """Muestra configuración de productos"""
        self.notebook.select(4)  # Cambiar a pestaña de configuración
    
    def save_config(self):
        """Guarda la configuración"""
        messagebox.showinfo("Info", "Configuración guardada")
    
    def restore_config(self):
        """Restaura configuración por defecto"""
        if messagebox.askyesno("Confirmar", "¿Restaurar configuración por defecto?"):
            self.config_vars['auto_codigo'].set(True)
            self.config_vars['validar_stock'].set(True)
            self.config_vars['precio_automatico'].set(False)
            self.config_vars['margen_utilidad'].set("30")
            self.config_vars['alertas_stock'].set(True)

# Función principal
def mostrar_gestion_productos(parent_window):
    """Función principal para mostrar la gestión de productos"""
    ProductsUI(parent_window)
