"""
Interfaz de usuario para gestión de inventario
Maneja productos, stock, movimientos y alertas de inventario
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
from typing import Optional, Dict, List, Any
import threading

from modules.inventory.inventory import InventoryManager
from modules.inventory.product import ProductManager
from ui.ui_helpers import create_styled_frame, create_input_frame, show_loading_dialog
from core.database import ejecutar_consulta_segura

class InventoryUI:
    """Interfaz principal para gestión de inventario"""
    
    def __init__(self, parent_window):
        self.parent = parent_window
        self.inventory_manager = InventoryManager()
        self.product_manager = ProductManager()
        self.current_product = None
        
        # Variables de filtros
        self.filter_vars = {
            'codigo': tk.StringVar(),
            'nombre': tk.StringVar(),
            'categoria': tk.StringVar(),
            'estado': tk.StringVar(),
            'stock_bajo': tk.BooleanVar()
        }
        
        self.setup_ui()
        self.load_products()
        self.start_auto_refresh()
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título y botones principales
        self.setup_header()
        
        # Frame de filtros y alertas
        self.setup_filters_and_alerts()
        
        # Notebook principal
        self.setup_main_notebook()
    
    def setup_header(self):
        """Configura el encabezado con título y botones"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Título
        ttk.Label(header_frame, text="Gestión de Inventario", 
                 font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        # Botones principales
        buttons_frame = ttk.Frame(header_frame)
        buttons_frame.pack(side=tk.RIGHT)
        
        ttk.Button(buttons_frame, text="Nuevo Producto", 
                  command=self.show_product_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Ajuste Inventario", 
                  command=self.show_adjustment_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Importar", 
                  command=self.import_inventory).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Exportar", 
                  command=self.export_inventory).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Reportes", 
                  command=self.show_reports).pack(side=tk.LEFT, padx=5)
    
    def setup_filters_and_alerts(self):
        """Configura filtros y panel de alertas"""
        filter_alert_frame = ttk.Frame(self.main_frame)
        filter_alert_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Frame de filtros (lado izquierdo)
        filters_frame = create_styled_frame(filter_alert_frame, "Filtros")
        filters_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        filter_content = ttk.Frame(filters_frame)
        filter_content.pack(fill=tk.X, padx=10, pady=5)
        
        # Fila 1 de filtros
        filter_row1 = ttk.Frame(filter_content)
        filter_row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(filter_row1, text="Código:").pack(side=tk.LEFT)
        code_entry = ttk.Entry(filter_row1, textvariable=self.filter_vars['codigo'], width=15)
        code_entry.pack(side=tk.LEFT, padx=(5, 15))
        code_entry.bind('<KeyRelease>', lambda e: self.apply_filters())
        
        ttk.Label(filter_row1, text="Nombre:").pack(side=tk.LEFT)
        name_entry = ttk.Entry(filter_row1, textvariable=self.filter_vars['nombre'], width=20)
        name_entry.pack(side=tk.LEFT, padx=(5, 15))
        name_entry.bind('<KeyRelease>', lambda e: self.apply_filters())
        
        # Fila 2 de filtros
        filter_row2 = ttk.Frame(filter_content)
        filter_row2.pack(fill=tk.X, pady=2)
        
        ttk.Label(filter_row2, text="Categoría:").pack(side=tk.LEFT)
        categoria_combo = ttk.Combobox(filter_row2, textvariable=self.filter_vars['categoria'], 
                                      width=15, values=self.get_categories())
        categoria_combo.pack(side=tk.LEFT, padx=(5, 15))
        categoria_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_filters())
        
        ttk.Label(filter_row2, text="Estado:").pack(side=tk.LEFT)
        estado_combo = ttk.Combobox(filter_row2, textvariable=self.filter_vars['estado'],
                                   width=15, values=['', 'ACTIVO', 'INACTIVO', 'DESCONTINUADO'])
        estado_combo.pack(side=tk.LEFT, padx=(5, 15))
        estado_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_filters())
        
        stock_check = ttk.Checkbutton(filter_row2, text="Solo stock bajo",
                                     variable=self.filter_vars['stock_bajo'],
                                     command=self.apply_filters)
        stock_check.pack(side=tk.LEFT, padx=(5, 15))
        
        ttk.Button(filter_row2, text="Limpiar", 
                  command=self.clear_filters).pack(side=tk.RIGHT)
        
        # Panel de alertas (lado derecho)
        self.setup_alerts_panel(filter_alert_frame)
    
    def setup_alerts_panel(self, parent):
        """Configura el panel de alertas"""
        alerts_frame = create_styled_frame(parent, "Alertas")
        alerts_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.alerts_text = tk.Text(alerts_frame, height=4, width=40, 
                                  font=('Arial', 9), state=tk.DISABLED)
        self.alerts_text.pack(padx=10, pady=5)
        
        # Cargar alertas iniciales
        self.update_alerts()
    
    def setup_main_notebook(self):
        """Configura el notebook principal"""
        self.main_notebook = ttk.Notebook(self.main_frame)
        self.main_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña lista de productos
        self.setup_products_tab()
        
        # Pestaña movimientos
        self.setup_movements_tab()
        
        # Pestaña stock crítico
        self.setup_critical_stock_tab()
    
    def setup_products_tab(self):
        """Configura la pestaña de productos"""
        products_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(products_frame, text="Productos")
        
        # Frame principal con lista y detalles
        content_frame = ttk.Frame(products_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Lista de productos (lado izquierdo)
        list_frame = ttk.Frame(content_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        ttk.Label(list_frame, text="Lista de Productos", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # Treeview para productos
        columns = ('codigo', 'nombre', 'categoria', 'precio', 'stock', 'minimo', 'estado')
        self.products_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=20)
        
        # Configurar columnas
        self.products_tree.heading('codigo', text='Código')
        self.products_tree.heading('nombre', text='Nombre')
        self.products_tree.heading('categoria', text='Categoría')
        self.products_tree.heading('precio', text='Precio')
        self.products_tree.heading('stock', text='Stock')
        self.products_tree.heading('minimo', text='Mínimo')
        self.products_tree.heading('estado', text='Estado')
        
        # Anchos de columnas
        self.products_tree.column('codigo', width=100)
        self.products_tree.column('nombre', width=200)
        self.products_tree.column('categoria', width=120)
        self.products_tree.column('precio', width=100)
        self.products_tree.column('stock', width=80)
        self.products_tree.column('minimo', width=80)
        self.products_tree.column('estado', width=100)
        
        # Scrollbar
        products_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, 
                                       command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=products_scroll.set)
        
        self.products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        products_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind eventos
        self.products_tree.bind('<<TreeviewSelect>>', self.on_product_select)
        self.products_tree.bind('<Double-1>', self.edit_product)
        
        # Panel de detalles (lado derecho)
        self.setup_product_details(content_frame)
        
        # Menú contextual
        self.setup_products_context_menu()
    
    def setup_product_details(self, parent):
        """Configura el panel de detalles del producto"""
        details_frame = ttk.Frame(parent)
        details_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        ttk.Label(details_frame, text="Detalles del Producto", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # Información básica
        info_frame = create_styled_frame(details_frame, "Información")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Variables para mostrar información
        self.product_info_vars = {
            'codigo': tk.StringVar(),
            'nombre': tk.StringVar(),
            'descripcion': tk.StringVar(),
            'categoria': tk.StringVar(),
            'precio_venta': tk.StringVar(),
            'precio_costo': tk.StringVar(),
            'stock_actual': tk.StringVar(),
            'stock_minimo': tk.StringVar(),
            'stock_maximo': tk.StringVar(),
            'ubicacion': tk.StringVar(),
            'proveedor': tk.StringVar(),
            'estado': tk.StringVar()
        }
        
        row = 0
        for field, var in self.product_info_vars.items():
            ttk.Label(info_frame, text=f"{field.replace('_', ' ').title()}:").grid(
                row=row, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(info_frame, textvariable=var, background='white', 
                     relief=tk.SUNKEN, width=20).grid(row=row, column=1, sticky=tk.EW, padx=5, pady=2)
            row += 1
        
        info_frame.columnconfigure(1, weight=1)
        
        # Imagen del producto
        image_frame = create_styled_frame(details_frame, "Imagen")
        image_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.product_image_label = ttk.Label(image_frame, text="Sin imagen", 
                                            background='lightgray', width=25, anchor=tk.CENTER)
        self.product_image_label.pack(padx=10, pady=10)
        
        # Acciones
        actions_frame = ttk.Frame(details_frame)
        actions_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(actions_frame, text="Editar", 
                  command=self.edit_product).pack(fill=tk.X, pady=2)
        ttk.Button(actions_frame, text="Movimiento", 
                  command=self.show_product_movement).pack(fill=tk.X, pady=2)
        ttk.Button(actions_frame, text="Historial", 
                  command=self.show_product_history).pack(fill=tk.X, pady=2)
        ttk.Button(actions_frame, text="Eliminar", 
                  command=self.delete_product).pack(fill=tk.X, pady=2)
    
    def setup_movements_tab(self):
        """Configura la pestaña de movimientos"""
        movements_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(movements_frame, text="Movimientos")
        
        # Frame de filtros de movimientos
        mov_filters_frame = ttk.Frame(movements_frame)
        mov_filters_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(mov_filters_frame, text="Desde:").pack(side=tk.LEFT)
        self.date_from = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ttk.Entry(mov_filters_frame, textvariable=self.date_from, width=12).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(mov_filters_frame, text="Hasta:").pack(side=tk.LEFT, padx=(10, 0))
        self.date_to = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ttk.Entry(mov_filters_frame, textvariable=self.date_to, width=12).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(mov_filters_frame, text="Tipo:").pack(side=tk.LEFT, padx=(10, 0))
        self.movement_type = tk.StringVar()
        type_combo = ttk.Combobox(mov_filters_frame, textvariable=self.movement_type,
                                 values=['', 'ENTRADA', 'SALIDA', 'AJUSTE', 'VENTA', 'DEVOLUCION'])
        type_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(mov_filters_frame, text="Filtrar", 
                  command=self.load_movements).pack(side=tk.LEFT, padx=10)
        
        # Lista de movimientos
        movements_list_frame = ttk.Frame(movements_frame)
        movements_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        mov_columns = ('fecha', 'producto', 'tipo', 'cantidad', 'motivo', 'usuario', 'referencia')
        self.movements_tree = ttk.Treeview(movements_list_frame, columns=mov_columns, 
                                          show='headings', height=15)
        
        # Configurar columnas de movimientos
        self.movements_tree.heading('fecha', text='Fecha')
        self.movements_tree.heading('producto', text='Producto')
        self.movements_tree.heading('tipo', text='Tipo')
        self.movements_tree.heading('cantidad', text='Cantidad')
        self.movements_tree.heading('motivo', text='Motivo')
        self.movements_tree.heading('usuario', text='Usuario')
        self.movements_tree.heading('referencia', text='Referencia')
        
        # Scrollbar para movimientos
        movements_scroll = ttk.Scrollbar(movements_list_frame, orient=tk.VERTICAL, 
                                        command=self.movements_tree.yview)
        self.movements_tree.configure(yscrollcommand=movements_scroll.set)
        
        self.movements_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        movements_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_critical_stock_tab(self):
        """Configura la pestaña de stock crítico"""
        critical_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(critical_frame, text="Stock Crítico")
        
        # Botones de acción
        actions_frame = ttk.Frame(critical_frame)
        actions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(actions_frame, text="Actualizar", 
                  command=self.load_critical_stock).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Generar Orden", 
                  command=self.generate_purchase_order).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Exportar Lista", 
                  command=self.export_critical_stock).pack(side=tk.LEFT, padx=5)
        
        # Lista de productos con stock crítico
        critical_list_frame = ttk.Frame(critical_frame)
        critical_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        critical_columns = ('codigo', 'nombre', 'stock_actual', 'stock_minimo', 
                           'faltante', 'categoria', 'proveedor')
        self.critical_tree = ttk.Treeview(critical_list_frame, columns=critical_columns, 
                                         show='headings', height=15)
        
        # Configurar columnas críticas
        self.critical_tree.heading('codigo', text='Código')
        self.critical_tree.heading('nombre', text='Nombre')
        self.critical_tree.heading('stock_actual', text='Stock Actual')
        self.critical_tree.heading('stock_minimo', text='Stock Mínimo')
        self.critical_tree.heading('faltante', text='Faltante')
        self.critical_tree.heading('categoria', text='Categoría')
        self.critical_tree.heading('proveedor', text='Proveedor')
        
        # Scrollbar para críticos
        critical_scroll = ttk.Scrollbar(critical_list_frame, orient=tk.VERTICAL, 
                                       command=self.critical_tree.yview)
        self.critical_tree.configure(yscrollcommand=critical_scroll.set)
        
        self.critical_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        critical_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Cargar datos iniciales
        self.load_critical_stock()
    
    def setup_products_context_menu(self):
        """Configura el menú contextual para productos"""
        self.context_menu = tk.Menu(self.main_frame, tearoff=0)
        self.context_menu.add_command(label="Ver Detalles", command=self.view_product_details)
        self.context_menu.add_command(label="Editar", command=self.edit_product)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Entrada de Stock", command=self.stock_entry)
        self.context_menu.add_command(label="Salida de Stock", command=self.stock_exit)
        self.context_menu.add_command(label="Ajuste de Inventario", command=self.stock_adjustment)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Historial Movimientos", command=self.show_product_history)
        self.context_menu.add_command(label="Eliminar", command=self.delete_product)
        
        self.products_tree.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """Muestra el menú contextual"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def get_categories(self) -> List[str]:
        """Obtiene las categorías disponibles"""
        try:
            return self.product_manager.obtener_categorias()
        except Exception:
            return ['Alimentación', 'Bebidas', 'Limpieza', 'Cuidado Personal', 'Otros']
    
    def load_products(self):
        """Carga la lista de productos"""
        try:
            # Limpiar lista actual
            for item in self.products_tree.get_children():
                self.products_tree.delete(item)
            
            # Obtener productos
            products = self.inventory_manager.listar_productos()
            
            for product in products:
                # Determinar color según stock
                stock = product.get('stock_actual', 0)
                minimo = product.get('stock_minimo', 0)
                
                values = (
                    product.get('codigo', ''),
                    product.get('nombre', ''),
                    product.get('categoria', ''),
                    f"₡{product.get('precio_venta', 0):,.2f}",
                    stock,
                    minimo,
                    product.get('estado', '')
                )
                
                item = self.products_tree.insert('', tk.END, values=values)
                
                # Colorear según stock
                if stock <= 0:
                    self.products_tree.item(item, tags=('sin_stock',))
                elif stock <= minimo:
                    self.products_tree.item(item, tags=('stock_bajo',))
                else:
                    self.products_tree.item(item, tags=('stock_ok',))
            
            # Configurar colores
            self.products_tree.tag_configure('sin_stock', background='#ffebee')
            self.products_tree.tag_configure('stock_bajo', background='#fff3e0')
            self.products_tree.tag_configure('stock_ok', background='#e8f5e8')
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando productos: {str(e)}")
    
    def apply_filters(self):
        """Aplica los filtros a la lista de productos"""
        try:
            # Construir filtros
            filters = {}
            
            if self.filter_vars['codigo'].get().strip():
                filters['codigo'] = self.filter_vars['codigo'].get().strip()
            if self.filter_vars['nombre'].get().strip():
                filters['nombre'] = self.filter_vars['nombre'].get().strip()
            if self.filter_vars['categoria'].get():
                filters['categoria'] = self.filter_vars['categoria'].get()
            if self.filter_vars['estado'].get():
                filters['estado'] = self.filter_vars['estado'].get()
            if self.filter_vars['stock_bajo'].get():
                filters['stock_bajo'] = True
            
            # Limpiar lista
            for item in self.products_tree.get_children():
                self.products_tree.delete(item)
            
            # Aplicar filtros
            products = self.inventory_manager.buscar_productos(filters)
            
            for product in products:
                stock = product.get('stock_actual', 0)
                minimo = product.get('stock_minimo', 0)
                
                values = (
                    product.get('codigo', ''),
                    product.get('nombre', ''),
                    product.get('categoria', ''),
                    f"₡{product.get('precio_venta', 0):,.2f}",
                    stock,
                    minimo,
                    product.get('estado', '')
                )
                
                item = self.products_tree.insert('', tk.END, values=values)
                
                # Aplicar colores
                if stock <= 0:
                    self.products_tree.item(item, tags=('sin_stock',))
                elif stock <= minimo:
                    self.products_tree.item(item, tags=('stock_bajo',))
                else:
                    self.products_tree.item(item, tags=('stock_ok',))
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error aplicando filtros: {str(e)}")
    
    def clear_filters(self):
        """Limpia todos los filtros"""
        for var in self.filter_vars.values():
            if isinstance(var, tk.BooleanVar):
                var.set(False)
            else:
                var.set('')
        self.load_products()
    
    def on_product_select(self, event):
        """Maneja la selección de un producto"""
        selection = self.products_tree.selection()
        if selection:
            item = self.products_tree.item(selection[0])
            product_code = item['values'][0]
            self.load_product_details(product_code)
    
    def load_product_details(self, product_code):
        """Carga los detalles de un producto"""
        try:
            product = self.product_manager.obtener_producto_por_codigo(product_code)
            if not product:
                return
            
            self.current_product = product
            
            # Actualizar campos de información
            self.product_info_vars['codigo'].set(product.get('codigo', ''))
            self.product_info_vars['nombre'].set(product.get('nombre', ''))
            self.product_info_vars['descripcion'].set(product.get('descripcion', ''))
            self.product_info_vars['categoria'].set(product.get('categoria', ''))
            self.product_info_vars['precio_venta'].set(f"₡{product.get('precio_venta', 0):,.2f}")
            self.product_info_vars['precio_costo'].set(f"₡{product.get('precio_costo', 0):,.2f}")
            self.product_info_vars['stock_actual'].set(f"{product.get('stock_actual', 0)}")
            self.product_info_vars['stock_minimo'].set(f"{product.get('stock_minimo', 0)}")
            self.product_info_vars['stock_maximo'].set(f"{product.get('stock_maximo', 0)}")
            self.product_info_vars['ubicacion'].set(product.get('ubicacion', ''))
            self.product_info_vars['proveedor'].set(product.get('proveedor_principal', ''))
            self.product_info_vars['estado'].set(product.get('estado', ''))
            
            # TODO: Cargar imagen del producto si existe
            self.product_image_label.config(text="Sin imagen")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando detalles: {str(e)}")
    
    def update_alerts(self):
        """Actualiza el panel de alertas"""
        try:
            self.alerts_text.config(state=tk.NORMAL)
            self.alerts_text.delete(1.0, tk.END)
            
            # Obtener alertas
            alerts = self.inventory_manager.obtener_alertas_inventario()
            
            if alerts:
                alert_text = ""
                for alert in alerts[:5]:  # Mostrar solo las primeras 5
                    alert_text += f"• {alert['mensaje']}\n"
                
                if len(alerts) > 5:
                    alert_text += f"... y {len(alerts) - 5} más"
                
                self.alerts_text.insert(tk.END, alert_text)
            else:
                self.alerts_text.insert(tk.END, "Sin alertas activas")
            
            self.alerts_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.alerts_text.config(state=tk.NORMAL)
            self.alerts_text.delete(1.0, tk.END)
            self.alerts_text.insert(tk.END, "Error cargando alertas")
            self.alerts_text.config(state=tk.DISABLED)
    
    def load_movements(self):
        """Carga los movimientos de inventario"""
        try:
            # Limpiar lista actual
            for item in self.movements_tree.get_children():
                self.movements_tree.delete(item)
            
            # Obtener filtros
            date_from = self.date_from.get()
            date_to = self.date_to.get()
            movement_type = self.movement_type.get()
            
            # Obtener movimientos
            movements = self.inventory_manager.obtener_movimientos(
                fecha_desde=date_from,
                fecha_hasta=date_to,
                tipo=movement_type if movement_type else None
            )
            
            for movement in movements:
                self.movements_tree.insert('', tk.END, values=(
                    movement.get('fecha_movimiento', ''),
                    movement.get('producto_nombre', ''),
                    movement.get('tipo_movimiento', ''),
                    movement.get('cantidad', ''),
                    movement.get('motivo', ''),
                    movement.get('usuario', ''),
                    movement.get('referencia', '')
                ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando movimientos: {str(e)}")
    
    def load_critical_stock(self):
        """Carga productos con stock crítico"""
        try:
            # Limpiar lista actual
            for item in self.critical_tree.get_children():
                self.critical_tree.delete(item)
            
            # Obtener productos críticos
            critical_products = self.inventory_manager.obtener_stock_critico()
            
            for product in critical_products:
                faltante = product.get('stock_minimo', 0) - product.get('stock_actual', 0)
                
                self.critical_tree.insert('', tk.END, values=(
                    product.get('codigo', ''),
                    product.get('nombre', ''),
                    product.get('stock_actual', 0),
                    product.get('stock_minimo', 0),
                    max(0, faltante),
                    product.get('categoria', ''),
                    product.get('proveedor_principal', '')
                ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando stock crítico: {str(e)}")
    
    def show_product_form(self, product_data=None):
        """Muestra el formulario de producto"""
        ProductFormDialog(self.parent, self.product_manager, product_data, self.on_product_saved)
    
    def edit_product(self):
        """Edita el producto seleccionado"""
        if not self.current_product:
            messagebox.showwarning("Advertencia", "Seleccione un producto para editar")
            return
        
        self.show_product_form(self.current_product)
    
    def delete_product(self):
        """Elimina el producto seleccionado"""
        if not self.current_product:
            messagebox.showwarning("Advertencia", "Seleccione un producto para eliminar")
            return
        
        if messagebox.askyesno("Confirmar", 
                              f"¿Está seguro de eliminar el producto {self.current_product.get('nombre')}?"):
            try:
                success = self.product_manager.eliminar_producto(self.current_product['id'])
                if success:
                    messagebox.showinfo("Éxito", "Producto eliminado correctamente")
                    self.load_products()
                    self.clear_product_details()
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el producto")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error eliminando producto: {str(e)}")
    
    def show_adjustment_form(self):
        """Muestra el formulario de ajuste de inventario"""
        AdjustmentDialog(self.parent, self.inventory_manager, self.on_adjustment_saved)
    
    def show_product_movement(self):
        """Muestra movimientos del producto seleccionado"""
        if not self.current_product:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return
        
        MovementDialog(self.parent, self.inventory_manager, self.current_product, self.on_movement_saved)
    
    def show_product_history(self):
        """Muestra el historial del producto"""
        if not self.current_product:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return
        
        ProductHistoryDialog(self.parent, self.inventory_manager, self.current_product['id'])
    
    def stock_entry(self):
        """Entrada de stock para el producto seleccionado"""
        if not self.current_product:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return
        
        StockMovementDialog(self.parent, self.inventory_manager, 
                           self.current_product, "ENTRADA", self.on_movement_saved)
    
    def stock_exit(self):
        """Salida de stock para el producto seleccionado"""
        if not self.current_product:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return
        
        StockMovementDialog(self.parent, self.inventory_manager, 
                           self.current_product, "SALIDA", self.on_movement_saved)
    
    def stock_adjustment(self):
        """Ajuste de stock para el producto seleccionado"""
        if not self.current_product:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return
        
        StockMovementDialog(self.parent, self.inventory_manager, 
                           self.current_product, "AJUSTE", self.on_movement_saved)
    
    def view_product_details(self):
        """Ver detalles del producto"""
        if not self.current_product:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return
        
        # Focus en el panel de detalles
        pass
    
    def import_inventory(self):
        """Importa inventario desde archivo"""
        file_path = filedialog.askopenfilename(
            title="Importar Inventario",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )
        
        if file_path:
            try:
                result = self.inventory_manager.importar_inventario(file_path)
                messagebox.showinfo("Éxito", 
                                   f"Importados {result['importados']} productos\n"
                                   f"Errores: {result['errores']}")
                self.load_products()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error importando: {str(e)}")
    
    def export_inventory(self):
        """Exporta inventario a archivo"""
        file_path = filedialog.asksaveasfilename(
            title="Exportar Inventario",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")]
        )
        
        if file_path:
            try:
                self.inventory_manager.exportar_inventario(file_path)
                messagebox.showinfo("Éxito", "Inventario exportado correctamente")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando: {str(e)}")
    
    def export_critical_stock(self):
        """Exporta lista de stock crítico"""
        file_path = filedialog.asksaveasfilename(
            title="Exportar Stock Crítico",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")]
        )
        
        if file_path:
            try:
                self.inventory_manager.exportar_stock_critico(file_path)
                messagebox.showinfo("Éxito", "Stock crítico exportado correctamente")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando: {str(e)}")
    
    def generate_purchase_order(self):
        """Genera orden de compra para productos críticos"""
        try:
            # Obtener productos críticos
            critical_products = self.inventory_manager.obtener_stock_critico()
            
            if not critical_products:
                messagebox.showinfo("Info", "No hay productos con stock crítico")
                return
            
            PurchaseOrderDialog(self.parent, critical_products)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generando orden: {str(e)}")
    
    def show_reports(self):
        """Muestra reportes de inventario"""
        InventoryReportsDialog(self.parent, self.inventory_manager)
    
    def on_product_saved(self):
        """Callback cuando se guarda un producto"""
        self.load_products()
        self.update_alerts()
    
    def on_adjustment_saved(self):
        """Callback cuando se guarda un ajuste"""
        self.load_products()
        self.load_movements()
        self.update_alerts()
    
    def on_movement_saved(self):
        """Callback cuando se guarda un movimiento"""
        self.load_products()
        self.load_movements()
        self.update_alerts()
        if self.current_product:
            self.load_product_details(self.current_product['codigo'])
    
    def clear_product_details(self):
        """Limpia los detalles del producto"""
        self.current_product = None
        for var in self.product_info_vars.values():
            var.set('')
        self.product_image_label.config(text="Sin imagen")
    
    def start_auto_refresh(self):
        """Inicia actualización automática de alertas"""
        def refresh_alerts():
            self.update_alerts()
            # Programar próxima actualización en 30 segundos
            self.parent.after(30000, refresh_alerts)
        
        # Iniciar primer refresh
        self.parent.after(1000, refresh_alerts)

class ProductFormDialog:
    """Diálogo para crear/editar productos"""
    
    def __init__(self, parent, product_manager, product_data=None, callback=None):
        self.parent = parent
        self.product_manager = product_manager
        self.product_data = product_data
        self.callback = callback
        
        self.setup_dialog()
        self.setup_form()
        
        if product_data:
            self.load_product_data()
    
    def setup_dialog(self):
        """Configura el diálogo"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Nuevo Producto" if not self.product_data else "Editar Producto")
        self.dialog.geometry("700x800")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Centrar ventana
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (800 // 2)
        self.dialog.geometry(f"700x800+{x}+{y}")
    
    def setup_form(self):
        """Configura el formulario"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Variables del formulario
        self.form_vars = {
            'codigo': tk.StringVar(),
            'codigo_barras': tk.StringVar(),
            'nombre': tk.StringVar(),
            'descripcion': tk.StringVar(),
            'categoria': tk.StringVar(),
            'precio_costo': tk.DoubleVar(),
            'precio_venta': tk.DoubleVar(),
            'margen_ganancia': tk.DoubleVar(),
            'stock_actual': tk.IntVar(),
            'stock_minimo': tk.IntVar(),
            'stock_maximo': tk.IntVar(),
            'ubicacion': tk.StringVar(),
            'proveedor_principal': tk.StringVar(),
            'aplica_iva': tk.BooleanVar(value=True),
            'estado': tk.StringVar(value='ACTIVO'),
            'unidad_medida': tk.StringVar(value='UNIDAD'),
            'peso': tk.DoubleVar(),
            'notas': tk.StringVar()
        }
        
        # Notebook para organizar campos
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña información básica
        self.setup_basic_tab(notebook)
        
        # Pestaña precios y costos
        self.setup_prices_tab(notebook)
        
        # Pestaña inventario
        self.setup_inventory_tab(notebook)
        
        # Pestaña configuración
        self.setup_config_tab(notebook)
        
        # Frame de botones
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(buttons_frame, text="Cancelar", 
                  command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="Guardar", 
                  command=self.save_product).pack(side=tk.RIGHT, padx=5)
    
    def setup_basic_tab(self, notebook):
        """Configura la pestaña de información básica"""
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="Información Básica")
        
        # Código del producto
        ttk.Label(basic_frame, text="Código *:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(basic_frame, textvariable=self.form_vars['codigo']).grid(
            row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Código de barras
        ttk.Label(basic_frame, text="Código de Barras:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(basic_frame, textvariable=self.form_vars['codigo_barras']).grid(
            row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Nombre
        ttk.Label(basic_frame, text="Nombre *:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(basic_frame, textvariable=self.form_vars['nombre']).grid(
            row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Descripción
        ttk.Label(basic_frame, text="Descripción:").grid(row=3, column=0, sticky=tk.NW, pady=5)
        desc_text = tk.Text(basic_frame, height=3, width=40)
        desc_text.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        desc_text.bind('<KeyRelease>', 
                      lambda e: self.form_vars['descripcion'].set(desc_text.get(1.0, tk.END).strip()))
        
        # Categoría
        ttk.Label(basic_frame, text="Categoría *:").grid(row=4, column=0, sticky=tk.W, pady=5)
        categoria_combo = ttk.Combobox(basic_frame, textvariable=self.form_vars['categoria'],
                                      values=['Alimentación', 'Bebidas', 'Limpieza', 
                                             'Cuidado Personal', 'Electrónicos', 'Otros'])
        categoria_combo.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Unidad de medida
        ttk.Label(basic_frame, text="Unidad de Medida:").grid(row=5, column=0, sticky=tk.W, pady=5)
        unidad_combo = ttk.Combobox(basic_frame, textvariable=self.form_vars['unidad_medida'],
                                   values=['UNIDAD', 'KILOGRAMO', 'GRAMO', 'LITRO', 'MILILITRO'])
        unidad_combo.grid(row=5, column=1, sticky=tk.EW, padx=5, pady=5)
        
        basic_frame.columnconfigure(1, weight=1)
    
    def setup_prices_tab(self, notebook):
        """Configura la pestaña de precios"""
        prices_frame = ttk.Frame(notebook)
        notebook.add(prices_frame, text="Precios")
        
        # Precio de costo
        ttk.Label(prices_frame, text="Precio de Costo:").grid(row=0, column=0, sticky=tk.W, pady=5)
        cost_entry = ttk.Entry(prices_frame, textvariable=self.form_vars['precio_costo'])
        cost_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        cost_entry.bind('<KeyRelease>', self.calculate_margin)
        
        # Precio de venta
        ttk.Label(prices_frame, text="Precio de Venta *:").grid(row=1, column=0, sticky=tk.W, pady=5)
        sale_entry = ttk.Entry(prices_frame, textvariable=self.form_vars['precio_venta'])
        sale_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        sale_entry.bind('<KeyRelease>', self.calculate_margin)
        
        # Margen de ganancia (calculado)
        ttk.Label(prices_frame, text="Margen de Ganancia (%):").grid(
            row=2, column=0, sticky=tk.W, pady=5)
        ttk.Label(prices_frame, textvariable=self.form_vars['margen_ganancia'], 
                 background='lightgray').grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Aplica IVA
        ttk.Checkbutton(prices_frame, text="Aplica IVA", 
                       variable=self.form_vars['aplica_iva']).grid(
                           row=3, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        prices_frame.columnconfigure(1, weight=1)
    
    def setup_inventory_tab(self, notebook):
        """Configura la pestaña de inventario"""
        inventory_frame = ttk.Frame(notebook)
        notebook.add(inventory_frame, text="Inventario")
        
        # Stock actual
        ttk.Label(inventory_frame, text="Stock Actual:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(inventory_frame, textvariable=self.form_vars['stock_actual']).grid(
            row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Stock mínimo
        ttk.Label(inventory_frame, text="Stock Mínimo:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(inventory_frame, textvariable=self.form_vars['stock_minimo']).grid(
            row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Stock máximo
        ttk.Label(inventory_frame, text="Stock Máximo:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(inventory_frame, textvariable=self.form_vars['stock_maximo']).grid(
            row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Ubicación
        ttk.Label(inventory_frame, text="Ubicación:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(inventory_frame, textvariable=self.form_vars['ubicacion']).grid(
            row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Proveedor principal
        ttk.Label(inventory_frame, text="Proveedor Principal:").grid(
            row=4, column=0, sticky=tk.W, pady=5)
        ttk.Entry(inventory_frame, textvariable=self.form_vars['proveedor_principal']).grid(
            row=4, column=1, sticky=tk.EW, padx=5, pady=5)
        
        inventory_frame.columnconfigure(1, weight=1)
    
    def setup_config_tab(self, notebook):
        """Configura la pestaña de configuración"""
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuración")
        
        # Estado
        ttk.Label(config_frame, text="Estado:").grid(row=0, column=0, sticky=tk.W, pady=5)
        estado_combo = ttk.Combobox(config_frame, textvariable=self.form_vars['estado'],
                                   values=['ACTIVO', 'INACTIVO', 'DESCONTINUADO'])
        estado_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Peso
        ttk.Label(config_frame, text="Peso (kg):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.form_vars['peso']).grid(
            row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Notas
        ttk.Label(config_frame, text="Notas:").grid(row=2, column=0, sticky=tk.NW, pady=5)
        notes_text = tk.Text(config_frame, height=4, width=40)
        notes_text.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        notes_text.bind('<KeyRelease>', 
                       lambda e: self.form_vars['notas'].set(notes_text.get(1.0, tk.END).strip()))
        
        config_frame.columnconfigure(1, weight=1)
    
    def calculate_margin(self, event=None):
        """Calcula el margen de ganancia"""
        try:
            costo = self.form_vars['precio_costo'].get()
            venta = self.form_vars['precio_venta'].get()
            
            if costo > 0 and venta > 0:
                margen = ((venta - costo) / costo) * 100
                self.form_vars['margen_ganancia'].set(round(margen, 2))
            else:
                self.form_vars['margen_ganancia'].set(0)
                
        except Exception:
            self.form_vars['margen_ganancia'].set(0)
    
    def load_product_data(self):
        """Carga los datos del producto en el formulario"""
        if not self.product_data:
            return
        
        for field, var in self.form_vars.items():
            value = self.product_data.get(field, '')
            if isinstance(var, (tk.DoubleVar, tk.IntVar)):
                var.set(float(value) if value else 0)
            elif isinstance(var, tk.BooleanVar):
                var.set(bool(value))
            else:
                var.set(value)
    
    def validate_form(self) -> tuple[bool, str]:
        """Valida el formulario"""
        if not self.form_vars['codigo'].get().strip():
            return False, "El código es requerido"
        
        if not self.form_vars['nombre'].get().strip():
            return False, "El nombre es requerido"
        
        if not self.form_vars['categoria'].get().strip():
            return False, "La categoría es requerida"
        
        if self.form_vars['precio_venta'].get() <= 0:
            return False, "El precio de venta debe ser mayor a 0"
        
        return True, ""
    
    def save_product(self):
        """Guarda el producto"""
        is_valid, error_msg = self.validate_form()
        if not is_valid:
            messagebox.showerror("Error", error_msg)
            return
        
        try:
            # Preparar datos
            product_data = {}
            for field, var in self.form_vars.items():
                if isinstance(var, (tk.DoubleVar, tk.IntVar)):
                    product_data[field] = var.get()
                elif isinstance(var, tk.BooleanVar):
                    product_data[field] = var.get()
                else:
                    product_data[field] = var.get().strip()
            
            # Guardar o actualizar
            if self.product_data:
                product_data['id'] = self.product_data['id']
                success = self.product_manager.actualizar_producto(product_data['id'], product_data)
            else:
                success = self.product_manager.crear_producto(product_data)
            
            if success:
                if self.callback:
                    self.callback()
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "No se pudo guardar el producto")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando producto: {str(e)}")

# Diálogos adicionales (versiones simplificadas)
class MovementDialog:
    """Diálogo para registrar movimientos de inventario"""
    
    def __init__(self, parent, inventory_manager, product, callback=None):
        self.parent = parent
        self.inventory_manager = inventory_manager
        self.product = product
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Movimiento - {product.get('nombre', '')}")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Implementar formulario de movimiento
        messagebox.showinfo("Info", "Formulario de movimiento en desarrollo")

class AdjustmentDialog:
    """Diálogo para ajustes de inventario"""
    
    def __init__(self, parent, inventory_manager, callback=None):
        messagebox.showinfo("Info", "Formulario de ajuste en desarrollo")

class StockMovementDialog:
    """Diálogo para movimientos de stock específicos"""
    
    def __init__(self, parent, inventory_manager, product, movement_type, callback=None):
        messagebox.showinfo("Info", f"Formulario de {movement_type} en desarrollo")

class ProductHistoryDialog:
    """Diálogo para historial del producto"""
    
    def __init__(self, parent, inventory_manager, product_id):
        messagebox.showinfo("Info", "Historial de producto en desarrollo")

class PurchaseOrderDialog:
    """Diálogo para generar orden de compra"""
    
    def __init__(self, parent, critical_products):
        messagebox.showinfo("Info", "Generador de orden de compra en desarrollo")

class InventoryReportsDialog:
    """Diálogo para reportes de inventario"""
    
    def __init__(self, parent, inventory_manager):
        messagebox.showinfo("Info", "Reportes de inventario en desarrollo")

# Función principal
def mostrar_gestion_inventario(parent_window):
    """Función principal para mostrar la gestión de inventario"""
    InventoryUI(parent_window)
