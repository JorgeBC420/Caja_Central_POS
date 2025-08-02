"""
Sistema POS - Caja Registradora Costa Rica
Interfaz Principal Moderna - Versión Independiente
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime
from PIL import Image, ImageTk

class ModernPOSApp:
    """Aplicación POS moderna con diseño estilo Eleventa"""
    
    def __init__(self, user_data=None):
        # Usuario autenticado requerido
        if not user_data:
            messagebox.showerror("Error", "Debe iniciar sesión para usar la aplicación")
            return
            
        self.current_user = user_data
        self.logo_photo = None
        self.sale_items = []
        self.sale_total = 0.0
        
        # Configurar la ventana principal
        self.setup_main_window()
        
        # Configurar estilos
        self.setup_modern_styles()
        
        # Crear interfaz principal
        self.create_main_interface()
        
        # Mostrar mensaje de bienvenida
        self.show_welcome_message()
    
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
    
    def setup_modern_styles(self):
        """Configura estilos modernos para la aplicación"""
        style = ttk.Style()
        
        # Configurar tema base
        try:
            style.theme_use('clam')
        except:
            pass
        
        # Configurar estilos personalizados
        style.configure('Modern.TButton', font=('Segoe UI', 10), padding=(15, 8))
        style.configure('Modern.TNotebook', background='#f8f9fa')
        style.configure('Modern.TNotebook.Tab', font=('Segoe UI', 11), padding=(20, 10))
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_main_interface(self):
        """Crea la interfaz principal moderna"""
        # Header moderno
        self.create_modern_header()
        
        # Área principal con navegación
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
        user_name = self.current_user.get('full_name', 'Usuario')
        
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
        
        # Área de contenido principal - Interfaz de ventas
        self.create_sales_interface(main_frame)
    
    def create_navigation_buttons(self, parent):
        """Crea los botones de navegación principales"""
        nav_content = tk.Frame(parent, bg='#ecf0f1')
        nav_content.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        # Botones principales (estilo Eleventa)
        buttons_config = [
            ("🛒 F1 Ventas", self.show_ventas, '#3498db'),
            ("� Cuentas Simples", self.show_simple_accounts, '#16a085'),
            ("�👥 F2 Clientes", self.show_clientes, '#27ae60'),
            ("📦 F3 Productos", self.show_productos, '#e67e22'),
            ("📊 F4 Inventario", self.show_inventario, '#9b59b6'),
            ("🔍 F5 Buscar", self.show_buscar, '#1abc9c'),
            ("🏪 Multi-Tienda", self.show_multistore, '#8e44ad'),
            ("🍽️ Restaurante", self.show_restaurant, '#e67e22'),
            ("📈 Historial Ventas", self.show_sales_history, '#34495e'),
            ("⚙️ Configuración", self.show_configuracion, '#95a5a6'),
            ("📋 Facturas", self.show_facturas, '#f39c12'),
            ("✂️ Corte", self.show_corte, '#e74c3c'),
            ("📊 Reportes", self.show_reportes, '#2c3e50')
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
    
    def create_sales_interface(self, parent):
        """Crea la interfaz de ventas moderna"""
        # Frame principal de ventas
        sales_frame = tk.Frame(parent, bg='white')
        sales_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Layout principal horizontal
        main_layout = tk.Frame(sales_frame, bg='white')
        main_layout.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel izquierdo - Código de producto y tabla
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
            ("🔢 INS Varios", self.show_varios),
            ("🎯 CTRL+Art Común", self.show_comun),
            ("🔍 F10 Buscar", self.show_buscar),
            ("📏 F11 Mayoreo", self.show_mayoreo),
            ("🗑️ DEL Borrar Art", self.delete_selected_item)
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
        
        # Ejemplo de productos
        self.add_sample_products()
    
    def add_sample_products(self):
        """Agrega productos de ejemplo"""
        sample_products = [
            ('4354535005459', 'PRODUCTO EJEMPLO 1 - Artículo de prueba', '₡15,500.00', '2', '₡31,000.00', '10', '0.000%'),
            ('7890123456789', 'PRODUCTO EJEMPLO 2 - Otro artículo', '₡8,750.25', '1', '₡8,750.25', '5', '5.000%'),
            ('1234567890123', 'PRODUCTO EJEMPLO 3 - Artículo más', '₡25,000.00', '1', '₡25,000.00', '8', '0.000%')
        ]
        
        for product in sample_products:
            item_id = self.sales_tree.insert('', 'end', values=product)
            
        # Actualizar total
        self.update_sale_totals()
    
    def create_sales_totals_panel(self, parent):
        """Crea el panel de totales y acciones"""
        # Información de ticket
        ticket_info = tk.Frame(parent, bg='white')
        ticket_info.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(ticket_info, text="Ticket 1", font=('Segoe UI', 14, 'bold'), 
                bg='white', fg='#2c3e50').pack()
        
        # Productos en la venta
        products_frame = tk.LabelFrame(parent, text="3    Productos en la venta actual", 
                                      font=('Segoe UI', 10), bg='white')
        products_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Totales
        totals_frame = tk.Frame(parent, bg='white')
        totals_frame.pack(fill=tk.X, padx=10, pady=20)
        
        # Total grande
        self.total_label = tk.Label(totals_frame, text="₡64,750.25", 
                                   font=('Segoe UI', 28, 'bold'), fg='#27ae60', bg='white')
        self.total_label.pack()
        
        self.subtotal_label = tk.Label(totals_frame, text="Subtotal: ₡61,662.50", 
                                      font=('Segoe UI', 12), fg='#7f8c8d', bg='white')
        self.subtotal_label.pack()
        
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
            ("📄 Reimprimir Último Ticket", self.reprint_ticket),
            ("💳 Ventas del día o Corte", self.show_corte)
        ]
        
        for text, command in secondary_buttons:
            btn = tk.Button(actions_frame, text=text, command=command,
                           font=('Segoe UI', 10), bg='#3498db', fg='white',
                           relief=tk.FLAT, pady=8)
            btn.pack(fill=tk.X, pady=2)
        
        # Información adicional
        info_frame = tk.Frame(parent, bg='white')
        info_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        date_time = datetime.now().strftime("%d - %b - %Y  %H:%M")
        tk.Label(info_frame, text=date_time, font=('Segoe UI', 9), 
                fg='#7f8c8d', bg='white').pack(side=tk.RIGHT)
    
    def create_status_bar(self):
        """Crea la barra de estado"""
        status_frame = tk.Frame(self.root, bg='#34495e', height=25)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        # Estado de conexión
        tk.Label(status_frame, text="🟢 Sistema Activo", font=('Segoe UI', 9), 
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
        self.root.bind('<Delete>', lambda e: self.delete_selected_item())
        
        # Focus en entrada de código de producto
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
        user_name = self.current_user.get('full_name', 'Usuario')
        messagebox.showinfo("Bienvenido", 
                           f"¡Bienvenido/a {user_name}!\n\nSistema POS iniciado correctamente.\n\n✅ Interfaz moderna activada\n✅ Logo integrado\n✅ Doble clic para editar precios")
    
    # Métodos de navegación
    def show_ventas(self):
        """Muestra la interfaz de ventas"""
        self.product_code_entry.focus_set()
        messagebox.showinfo("Ventas", "Ya está en la pantalla de ventas")
    
    def show_clientes(self):
        """Muestra gestión de clientes"""
        try:
            from ui.ui_customers import CustomersWindow
            CustomersWindow(self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir gestión de clientes:\n{str(e)}")
            print(f"Error clientes: {e}")
            import traceback
            traceback.print_exc()
    
    def show_productos(self):
        """Muestra gestión de productos"""
        try:
            from ui.ui_search_inventory import ProductManagementWindow
            ProductManagementWindow(self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir gestión de productos:\n{str(e)}")
    
    def show_inventario(self):
        """Muestra gestión de inventario"""
        try:
            from ui.ui_search_inventory import InventoryWindow
            InventoryWindow(self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir gestión de inventario:\n{str(e)}")
    
    def show_simple_accounts(self):
        """Muestra el gestor simple de cuentas - Solo abre y cierra"""
        try:
            from ui.ui_simple_sales import SimpleAccountManager
            SimpleAccountManager(self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir gestor de cuentas:\n{str(e)}")
            print(f"Error cuentas simples: {e}")
    
    def show_configuracion(self):
        """Muestra configuración con mejor contraste"""
        try:
            from ui.ui_configuration_mejorada import ConfigurationWindow
            ConfigurationWindow(self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir configuración:\n{str(e)}")
            print(f"Error configuración: {e}")
            import traceback
            traceback.print_exc()
    
    def show_facturas(self):
        """Muestra facturas"""
        try:
            from ui.ui_facturacion_electronica import ElectronicInvoiceWindow
            ElectronicInvoiceWindow(self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir facturación electrónica:\n{str(e)}")
    
    def show_corte(self):
        """Muestra corte de caja"""
        try:
            from ui.ui_cash_close import CashCloseWindow
            CashCloseWindow(self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir corte de caja:\n{str(e)}")
            print(f"Error corte de caja: {e}")
            import traceback
            traceback.print_exc()
    
    def show_reportes(self):
        """Muestra reportes"""
        try:
            from ui.ui_reports import ReportsWindow
            ReportsWindow(self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir reportes:\n{str(e)}")
            print(f"Error reportes: {e}")
            import traceback
            traceback.print_exc()
    
    def show_varios(self):
        """Muestra productos varios"""
        messagebox.showinfo("Función", "Productos Varios")
    
    def show_comun(self):
        """Muestra artículos comunes"""
        messagebox.showinfo("Función", "Artículos Comunes")
    
    def show_buscar(self):
        """Muestra búsqueda de productos"""
        try:
            from ui.ui_search_inventory import ProductSearchWindow
            ProductSearchWindow(self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir búsqueda de productos:\n{str(e)}")
    
    def show_mayoreo(self):
        """Muestra precios de mayoreo"""
        messagebox.showinfo("Función", "Precios de Mayoreo")
    
    def reprint_ticket(self):
        """Reimprimir último ticket"""
        messagebox.showinfo("Función", "Reimprimir Último Ticket")
    
    # Métodos de funcionalidad
    def add_product_to_sale(self):
        """Agrega un producto a la venta"""
        code = self.product_code_entry.get().strip()
        if not code:
            messagebox.showwarning("Código Requerido", 
                                  "⚠️ Ingrese un código de producto\n\nEscriba el código de barras o código del producto y presione ENTER.")
            self.product_code_entry.focus_set()
            return
        
        try:
            # Verificar si el código ya existe en la venta
            existing_item = None
            for item in self.sales_tree.get_children():
                values = self.sales_tree.item(item)['values']
                if values[0] == code:  # Mismo código de barras
                    existing_item = item
                    break
            
            if existing_item:
                # Si existe, incrementar cantidad
                values = list(self.sales_tree.item(existing_item)['values'])
                current_qty = int(values[3])
                new_qty = current_qty + 1
                
                # Recalcular precios
                precio_unitario = float(str(values[2]).replace('₡', '').replace(',', ''))
                nuevo_importe = precio_unitario * new_qty
                
                # Actualizar valores
                values[3] = str(new_qty)  # Cantidad
                values[4] = f"₡{nuevo_importe:,.2f}"  # Importe
                
                self.sales_tree.item(existing_item, values=values)
                
                messagebox.showinfo("✅ Cantidad Actualizada", 
                                   f"Producto existente actualizado:\n\n📦 {values[1]}\n🔢 Nueva cantidad: {new_qty}")
            else:
                # Agregar nuevo producto
                # Simular búsqueda de producto (en producción sería desde base de datos)
                if code.startswith('123'):
                    product_name = f'Producto Premium - Código {code}'
                    price = 25000.00
                elif code.startswith('456'):
                    product_name = f'Producto Estándar - Código {code}'
                    price = 15000.00
                elif code.startswith('789'):
                    product_name = f'Producto Económico - Código {code}'
                    price = 8500.00
                else:
                    product_name = f'Producto Genérico - Código {code}'
                    price = 12000.00
                
                # Crear nuevo producto
                new_product = (
                    code,
                    product_name,
                    f'₡{price:,.2f}',
                    '1',
                    f'₡{price:,.2f}',
                    '15',  # Stock simulado
                    '0.000%'
                )
                
                self.sales_tree.insert('', 'end', values=new_product)
                
                messagebox.showinfo("✅ Producto Agregado", 
                                   f"Nuevo producto agregado a la venta:\n\n📦 {product_name}\n💰 Precio: ₡{price:,.2f}")
            
            # Limpiar entrada y actualizar totales
            self.product_code_entry.delete(0, tk.END)
            self.update_sale_totals()
            self.product_code_entry.focus_set()
            
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error agregando producto: {str(e)}")
            self.product_code_entry.focus_set()
    
    def delete_selected_item(self):
        """Elimina el item seleccionado"""
        selection = self.sales_tree.selection()
        if not selection:
            messagebox.showwarning("Selección", "⚠️ Seleccione un producto para eliminar\n\nHaga clic en un producto de la tabla y luego presione DEL o este botón.")
            return
        
        # Obtener información del producto seleccionado
        item = self.sales_tree.item(selection[0])
        product_name = item['values'][1]
        
        # Confirmar eliminación
        if messagebox.askyesno("Eliminar Producto", 
                               f"¿Está seguro que desea eliminar este producto?\n\n📦 {product_name}\n\n⚠️ Esta acción no se puede deshacer."):
            try:
                # Eliminar el item
                self.sales_tree.delete(selection[0])
                self.update_sale_totals()
                
                # Mensaje de confirmación
                messagebox.showinfo("✅ Producto Eliminado", 
                                   f"El producto ha sido eliminado correctamente:\n\n📦 {product_name}")
                
                # Enfocar entrada de código para continuar
                self.product_code_entry.focus_set()
                
            except Exception as e:
                messagebox.showerror("❌ Error", f"Error eliminando producto: {str(e)}")
    
    def edit_product_price(self, event):
        """Edita el precio de un producto con doble clic"""
        selection = self.sales_tree.selection()
        if not selection:
            return
        
        item = self.sales_tree.item(selection[0])
        values = item['values']
        product_name = values[1]
        current_price_str = str(values[2]).replace('₡', '').replace(',', '')
        try:
            current_price = float(current_price_str)
        except:
            current_price = 0.0
        
        current_quantity = int(values[3])
        
        # Crear ventana de edición estilo Eleventa
        self.show_price_edit_dialog(product_name, current_price, current_quantity, selection[0])
    
    def show_price_edit_dialog(self, product_name, current_price, quantity, item_id):
        """Muestra diálogo para editar precio estilo Eleventa"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Cambiar Precio - Sistema POS")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrar diálogo
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (250)
        y = (dialog.winfo_screenheight() // 2) - (200)
        dialog.geometry(f"500x400+{x}+{y}")
        
        # Configurar estilo moderno
        dialog.configure(bg='#f8f9fa')
        
        # Header azul estilo Eleventa
        header_frame = tk.Frame(dialog, bg='#2c3e50', height=70)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg='#2c3e50')
        header_content.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        tk.Label(header_content, text="💰 Cambiar Precio del Producto", 
                font=('Segoe UI', 16, 'bold'), fg='white', bg='#2c3e50').pack()
        
        # Contenido principal
        main_frame = tk.Frame(dialog, bg='white', padx=30, pady=25)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Información del producto
        product_frame = tk.LabelFrame(main_frame, text="Información del Producto", 
                                     font=('Segoe UI', 10, 'bold'), bg='white', fg='#2c3e50')
        product_frame.pack(fill=tk.X, pady=(0, 20))
        
        product_label = tk.Label(product_frame, text=product_name, 
                                font=('Segoe UI', 11), bg='white', fg='#34495e',
                                wraplength=400, justify=tk.LEFT)
        product_label.pack(anchor=tk.W, padx=10, pady=10)
        
        # Precio actual y cantidad
        current_frame = tk.Frame(main_frame, bg='white')
        current_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Precio actual
        price_current_frame = tk.Frame(current_frame, bg='white')
        price_current_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(price_current_frame, text="Precio Actual:", 
                font=('Segoe UI', 10, 'bold'), bg='white', fg='#2c3e50').pack(anchor=tk.W)
        
        price_display = tk.Label(price_current_frame, text=f"₡{current_price:,.2f}", 
                                font=('Segoe UI', 20, 'bold'), bg='white', fg='#27ae60')
        price_display.pack(anchor=tk.W, pady=(5, 0))
        
        # Cantidad
        qty_frame = tk.Frame(current_frame, bg='white')
        qty_frame.pack(side=tk.RIGHT)
        
        tk.Label(qty_frame, text="Cantidad:", 
                font=('Segoe UI', 10, 'bold'), bg='white', fg='#2c3e50').pack()
        
        tk.Label(qty_frame, text=str(quantity), 
                font=('Segoe UI', 16, 'bold'), bg='white', fg='#3498db').pack(pady=(5, 0))
        
        # Nuevo precio
        new_price_frame = tk.LabelFrame(main_frame, text="Modificar Precio", 
                                       font=('Segoe UI', 10, 'bold'), bg='white', fg='#2c3e50')
        new_price_frame.pack(fill=tk.X, pady=(0, 15))
        
        price_input_frame = tk.Frame(new_price_frame, bg='white')
        price_input_frame.pack(padx=10, pady=15)
        
        tk.Label(price_input_frame, text="Nuevo Precio (₡):", 
                font=('Segoe UI', 11, 'bold'), bg='white', fg='#2c3e50').pack(anchor=tk.W)
        
        price_entry = tk.Entry(price_input_frame, font=('Segoe UI', 18), width=12, 
                              justify='center', relief=tk.FLAT, bd=10,
                              bg='#ecf0f1', fg='#2c3e50')
        price_entry.pack(anchor=tk.W, pady=(8, 10), ipady=8)
        price_entry.insert(0, f"{current_price:.2f}")
        price_entry.select_range(0, tk.END)
        price_entry.focus_set()
        
        # Campo de descuento
        discount_frame = tk.Frame(new_price_frame, bg='white')
        discount_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        tk.Label(discount_frame, text="Descuento (%):", 
                font=('Segoe UI', 10), bg='white', fg='#2c3e50').pack(side=tk.LEFT)
        
        discount_entry = tk.Entry(discount_frame, font=('Segoe UI', 12), width=8, 
                                 justify='center', relief=tk.FLAT, bd=5,
                                 bg='#ecf0f1')
        discount_entry.pack(side=tk.LEFT, padx=(10, 0), ipady=3)
        discount_entry.insert(0, "0.00")
        
        # Botones
        buttons_frame = tk.Frame(main_frame, bg='white')
        buttons_frame.pack(fill=tk.X, pady=(25, 0))
        
        def apply_price_change():
            try:
                new_price = float(price_entry.get())
                discount = float(discount_entry.get())
                
                if new_price <= 0:
                    messagebox.showerror("Error", "El precio debe ser mayor que cero")
                    return
                
                # Aplicar descuento si hay
                final_price = new_price * (1 - discount / 100)
                
                # Calcular nuevo total
                new_total = final_price * quantity
                
                # Actualizar valores en el treeview
                current_values = list(self.sales_tree.item(item_id)['values'])
                current_values[2] = f"₡{final_price:,.2f}"  # Precio
                current_values[4] = f"₡{new_total:,.2f}"    # Importe
                current_values[6] = f"{discount:.3f}%"      # Descuento
                
                self.sales_tree.item(item_id, values=current_values)
                
                # Actualizar totales de venta
                self.update_sale_totals()
                
                dialog.destroy()
                
                # Mensaje de confirmación
                discount_text = f" (Descuento: {discount}%)" if discount > 0 else ""
                messagebox.showinfo("✅ Precio Actualizado", 
                                   f"Precio actualizado correctamente\n\n💰 Nuevo precio: ₡{final_price:,.2f}{discount_text}")
                
            except ValueError:
                messagebox.showerror("❌ Error", "Ingrese valores numéricos válidos")
            except Exception as e:
                messagebox.showerror("❌ Error", f"Error actualizando precio: {str(e)}")
        
        def cancel_edit():
            dialog.destroy()
        
        # Botón principal - Aplicar cambio
        apply_btn = tk.Button(buttons_frame, text="✅ Cambiar Precio", 
                             command=apply_price_change,
                             font=('Segoe UI', 12, 'bold'), bg='#27ae60', fg='white',
                             relief=tk.FLAT, padx=40, pady=15, cursor='hand2')
        apply_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # Botón cancelar
        cancel_btn = tk.Button(buttons_frame, text="❌ Cancelar", 
                              command=cancel_edit,
                              font=('Segoe UI', 12, 'bold'), bg='#e74c3c', fg='white',
                              relief=tk.FLAT, padx=40, pady=15, cursor='hand2')
        cancel_btn.pack(side=tk.LEFT)
        
        # Bind Enter para aplicar cambio
        price_entry.bind('<Return>', lambda e: apply_price_change())
        dialog.bind('<Escape>', lambda e: cancel_edit())
        
        # Efectos hover para botones
        def on_enter_apply(e):
            apply_btn.config(bg='#229954')
        def on_leave_apply(e):
            apply_btn.config(bg='#27ae60')
        
        def on_enter_cancel(e):
            cancel_btn.config(bg='#c0392b')
        def on_leave_cancel(e):
            cancel_btn.config(bg='#e74c3c')
        
        apply_btn.bind('<Enter>', on_enter_apply)
        apply_btn.bind('<Leave>', on_leave_apply)
        cancel_btn.bind('<Enter>', on_enter_cancel)
        cancel_btn.bind('<Leave>', on_leave_cancel)
    
    def update_sale_totals(self):
        """Actualiza los totales de la venta"""
        total = 0.0
        item_count = 0
        
        # Calcular total de todos los items
        for item in self.sales_tree.get_children():
            values = self.sales_tree.item(item)['values']
            try:
                import_str = str(values[4]).replace('₡', '').replace(',', '')
                item_total = float(import_str)
                total += item_total
                item_count += int(values[3])  # cantidad
            except (ValueError, IndexError):
                continue
        
        # Actualizar labels
        if hasattr(self, 'total_label'):
            self.total_label.config(text=f"₡{total:,.2f}")
        
        if hasattr(self, 'subtotal_label'):
            subtotal = total / 1.13  # Simulando IVA
            self.subtotal_label.config(text=f"Subtotal: ₡{subtotal:,.2f}")
        
        # Actualizar contador de productos
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Frame):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, tk.LabelFrame):
                                current_text = grandchild.cget('text')
                                if 'Productos en la venta actual' in current_text:
                                    grandchild.config(text=f"{len(self.sales_tree.get_children())}    Productos en la venta actual")
    
    def process_payment(self):
        """Procesa el pago de la venta"""
        items = self.sales_tree.get_children()
        if not items:
            messagebox.showwarning("Venta Vacía", "No hay productos en la venta")
            return
        
        # Calcular total
        total = 0.0
        productos_venta = []
        
        for item in items:
            values = self.sales_tree.item(item)['values']
            try:
                import_str = str(values[4]).replace('₡', '').replace(',', '')
                item_total = float(import_str)
                total += item_total
                
                # Recopilar datos del producto para facturación
                precio_unitario = float(str(values[2]).replace('₡', '').replace(',', ''))
                cantidad = int(values[3])
                
                productos_venta.append({
                    'codigo': values[0],
                    'descripcion': values[1],
                    'cantidad': cantidad,
                    'precio_unitario': precio_unitario,
                    'total': item_total
                })
                
            except:
                continue
        
        # Mostrar diálogo de opciones de pago
        payment_dialog = tk.Toplevel(self.root)
        payment_dialog.title("💰 Procesar Pago")
        payment_dialog.geometry("600x500")
        payment_dialog.resizable(False, False)
        payment_dialog.transient(self.root)
        payment_dialog.grab_set()
        
        # Centrar diálogo
        payment_dialog.update_idletasks()
        x = (payment_dialog.winfo_screenwidth() // 2) - (300)
        y = (payment_dialog.winfo_screenheight() // 2) - (250)
        payment_dialog.geometry(f"600x500+{x}+{y}")
        
        payment_dialog.configure(bg='#f8f9fa')
        
        # Header
        header_frame = tk.Frame(payment_dialog, bg='#27ae60', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg='#27ae60')
        header_content.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        tk.Label(header_content, text="💰 Procesar Pago", 
                font=('Segoe UI', 18, 'bold'), fg='white', bg='#27ae60').pack(side=tk.LEFT)
        
        tk.Label(header_content, text=f"₡{total:,.2f}", 
                font=('Segoe UI', 24, 'bold'), fg='white', bg='#27ae60').pack(side=tk.RIGHT)
        
        # Contenido principal
        main_frame = tk.Frame(payment_dialog, bg='white', padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Resumen de venta
        summary_frame = tk.LabelFrame(main_frame, text="� Resumen de Venta", 
                                     font=('Segoe UI', 12, 'bold'), bg='white', padx=15, pady=15)
        summary_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(summary_frame, text=f"Productos: {len(productos_venta)}", 
                font=('Segoe UI', 11), bg='white').pack(anchor=tk.W)
        
        subtotal = total / 1.13  # Asumir IVA incluido
        iva = total - subtotal
        
        tk.Label(summary_frame, text=f"Subtotal: ₡{subtotal:,.2f}", 
                font=('Segoe UI', 11), bg='white').pack(anchor=tk.W)
        tk.Label(summary_frame, text=f"IVA (13%): ₡{iva:,.2f}", 
                font=('Segoe UI', 11), bg='white').pack(anchor=tk.W)
        tk.Label(summary_frame, text=f"TOTAL: ₡{total:,.2f}", 
                font=('Segoe UI', 14, 'bold'), fg='#27ae60', bg='white').pack(anchor=tk.W, pady=(5, 0))
        
        # Opciones de pago
        options_frame = tk.LabelFrame(main_frame, text="💳 Opciones de Pago y Facturación", 
                                     font=('Segoe UI', 12, 'bold'), bg='white', padx=15, pady=15)
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Variable para tipo de documento
        doc_type_var = tk.StringVar(value="tiquete")
        
        # Opciones de documento
        tk.Radiobutton(options_frame, text="🧾 Tiquete (sin datos del cliente)", 
                      variable=doc_type_var, value="tiquete",
                      font=('Segoe UI', 11), bg='white', cursor='hand2').pack(anchor=tk.W, pady=2)
        
        tk.Radiobutton(options_frame, text="📄 Factura Electrónica (con datos del cliente)", 
                      variable=doc_type_var, value="factura",
                      font=('Segoe UI', 11), bg='white', cursor='hand2').pack(anchor=tk.W, pady=2)
        
        # Método de pago
        tk.Label(options_frame, text="Método de Pago:", font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor=tk.W, pady=(15, 5))
        
        payment_method_var = tk.StringVar(value="efectivo")
        
        methods_frame = tk.Frame(options_frame, bg='white')
        methods_frame.pack(fill=tk.X)
        
        payment_methods = [
            ("💵 Efectivo", "efectivo"),
            ("💳 Tarjeta", "tarjeta"),
            ("📱 SINPE Móvil", "sinpe"),
            ("🏦 Cheque", "cheque")
        ]
        
        for i, (text, value) in enumerate(payment_methods):
            tk.Radiobutton(methods_frame, text=text, variable=payment_method_var, value=value,
                          font=('Segoe UI', 10), bg='white', cursor='hand2').grid(row=i//2, column=i%2, sticky=tk.W, padx=(0, 20), pady=2)
        
        # Botones de acción
        buttons_frame = tk.Frame(main_frame, bg='white')
        buttons_frame.pack(fill=tk.X, pady=(20, 0))
        
        def process_simple_payment():
            """Procesa pago simple sin facturación electrónica"""
            if messagebox.askyesno("Confirmar Pago", f"¿Procesar pago de ₡{total:,.2f}?"):
                # Limpiar venta
                for item in items:
                    self.sales_tree.delete(item)
                
                self.update_sale_totals()
                payment_dialog.destroy()
                
                method_text = dict(payment_methods)[payment_method_var.get()]
                messagebox.showinfo("✅ Pago Completado", 
                                   f"¡Venta procesada exitosamente!\n\n💰 Total: ₡{total:,.2f}\n💳 Método: {method_text}\n📄 Tiquete impreso")
        
        def process_electronic_invoice():
            """Procesa pago con factura electrónica"""
            try:
                # Importar módulo de facturación
                from ui.ui_facturacion_electronica import mostrar_facturacion_electronica
                
                # Preparar datos de venta
                venta_data = {
                    'total': total,
                    'productos': productos_venta,
                    'metodo_pago': payment_method_var.get()
                }
                
                payment_dialog.destroy()
                
                # Abrir ventana de facturación electrónica
                mostrar_facturacion_electronica(self.root, venta_data)
                
                # Limpiar venta después de facturar
                for item in items:
                    self.sales_tree.delete(item)
                self.update_sale_totals()
                
            except ImportError:
                messagebox.showerror("Error", "Módulo de facturación electrónica no disponible")
            except Exception as e:
                messagebox.showerror("Error", f"Error en facturación: {str(e)}")
        
        def cancel_payment():
            payment_dialog.destroy()
        
        # Botón principal
        main_btn_text = "🧾 Procesar Tiquete" if doc_type_var.get() == "tiquete" else "📄 Generar Factura Electrónica"
        main_command = process_simple_payment if doc_type_var.get() == "tiquete" else process_electronic_invoice
        
        def update_main_button():
            if doc_type_var.get() == "tiquete":
                main_btn.config(text="🧾 Procesar Tiquete", command=process_simple_payment, bg='#3498db')
            else:
                main_btn.config(text="📄 Generar Factura Electrónica", command=process_electronic_invoice, bg='#27ae60')
        
        # Configurar cambio de botón
        for widget in options_frame.winfo_children():
            if isinstance(widget, tk.Radiobutton):
                widget.config(command=update_main_button)
        
        main_btn = tk.Button(buttons_frame, text=main_btn_text, command=main_command,
                            font=('Segoe UI', 14, 'bold'), bg='#3498db', fg='white',
                            relief=tk.FLAT, padx=40, pady=15, cursor='hand2')
        main_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # Botón cancelar
        cancel_btn = tk.Button(buttons_frame, text="❌ Cancelar", command=cancel_payment,
                              font=('Segoe UI', 12), bg='#e74c3c', fg='white',
                              relief=tk.FLAT, padx=30, pady=12, cursor='hand2')
        cancel_btn.pack(side=tk.LEFT)
        
        # Botón ayuda
        help_btn = tk.Button(buttons_frame, text="❓ Ayuda", 
                            command=lambda: messagebox.showinfo("Ayuda", 
                                "🧾 TIQUETE: Documento simple sin datos del cliente\n\n📄 FACTURA ELECTRÓNICA: Documento oficial que cumple con Hacienda, requiere datos del cliente y genera XML + PDF"),
                            font=('Segoe UI', 10), bg='#95a5a6', fg='white',
                            relief=tk.FLAT, padx=20, pady=10, cursor='hand2')
        help_btn.pack(side=tk.RIGHT)
        
        # Configurar botón inicial
        update_main_button()
    
    def show_multistore(self):
        """Abrir sistema multi-tienda"""
        try:
            from ui.ui_multistore import MultiStoreWindow
            MultiStoreWindow(self.root)
        except ImportError as e:
            messagebox.showerror("Error", f"No se pudo cargar el sistema multi-tienda:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error abriendo multi-tienda:\n{str(e)}")
    
    def show_restaurant(self):
        """Abrir sistema de restaurante"""
        try:
            from ui.ui_restaurant import RestaurantWindow
            RestaurantWindow(self.root)
        except ImportError as e:
            messagebox.showerror("Error", f"No se pudo cargar el sistema de restaurante:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error abriendo restaurante:\n{str(e)}")
    
    def show_sales_history(self):
        """Abrir historial de ventas para administradores"""
        try:
            from modules.reports.sales_history import SalesHistoryManager
            from ui.ui_sales_history import SalesHistoryWindow
            
            # Verificar permisos de admin (simulado)
            if self.current_user.get('role_name') == 'Administrador':
                SalesHistoryWindow(self.root)
            else:
                messagebox.showwarning("Permisos", "Solo los administradores pueden acceder al historial de ventas")
        except ImportError as e:
            messagebox.showerror("Error", f"No se pudo cargar el historial de ventas:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error abriendo historial:\n{str(e)}")

    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        if messagebox.askyesno("Salir", "¿Está seguro que desea salir del sistema?"):
            self.root.quit()
    
    def run(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()

def main():
    """Función principal con autenticación segura"""
    try:
        # Importar sistema de login
        from login_secure import authenticate_user
        
        print("🔐 Iniciando sistema de autenticación...")
        
        # Autenticar usuario
        user_data = authenticate_user()
        
        if user_data:
            print(f"✅ Usuario autenticado: {user_data['full_name']} ({user_data['role']})")
            
            # Iniciar aplicación con usuario autenticado
            app = ModernPOSApp(user_data)
            if hasattr(app, 'root'):  # Verificar que se creó correctamente
                app.run()
            else:
                print("❌ Error creando aplicación")
        else:
            print("❌ Autenticación cancelada")
            
    except KeyboardInterrupt:
        print("\n👋 Saliendo...")
    except Exception as e:
        print(f"❌ Error iniciando aplicación: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error Fatal", f"No se pudo iniciar la aplicación:\n{str(e)}")

if __name__ == "__main__":
    main()
