import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import messagebox

class ProductSearchWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("🔍 Buscar Productos - Caja Central POS")
        self.window.geometry("900x600")
        self.window.configure(bg='#f0f0f0')
        self.window.resizable(True, True)
        
        # Centrar ventana
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()
        self.load_products()
        
    def setup_ui(self):
        # Frame principal
        main_frame = tk.Frame(self.window, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(main_frame, 
                              text="🔍 Búsqueda de Productos",
                              font=('Arial', 18, 'bold'),
                              bg='#f0f0f0',
                              fg='#2c3e50')
        title_label.pack(pady=(0, 20))
        
        # Frame de búsqueda
        search_frame = tk.Frame(main_frame, bg='#f0f0f0')
        search_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(search_frame, 
                text="Buscar por:",
                font=('Arial', 12, 'bold'),
                bg='#f0f0f0').pack(side='left', padx=(0, 10))
        
        # Campo de búsqueda
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame,
                                   textvariable=self.search_var,
                                   font=('Arial', 12),
                                   width=40)
        self.search_entry.pack(side='left', padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', self.on_search)
        
        # Botón buscar
        search_btn = tk.Button(search_frame,
                              text="🔍 Buscar",
                              font=('Arial', 11, 'bold'),
                              bg='#3498db',
                              fg='white',
                              relief='flat',
                              padx=20,
                              command=self.search_products)
        search_btn.pack(side='left', padx=(0, 10))
        
        # Botón limpiar
        clear_btn = tk.Button(search_frame,
                             text="🗑️ Limpiar",
                             font=('Arial', 11, 'bold'),
                             bg='#95a5a6',
                             fg='white',
                             relief='flat',
                             padx=20,
                             command=self.clear_search)
        clear_btn.pack(side='left')
        
        # Tabla de productos
        table_frame = tk.Frame(main_frame, bg='#f0f0f0')
        table_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Configurar Treeview
        columns = ('codigo', 'nombre', 'precio', 'stock', 'categoria')
        self.product_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Definir encabezados
        self.product_tree.heading('codigo', text='Código')
        self.product_tree.heading('nombre', text='Nombre del Producto')
        self.product_tree.heading('precio', text='Precio')
        self.product_tree.heading('stock', text='Stock')
        self.product_tree.heading('categoria', text='Categoría')
        
        # Configurar columnas
        self.product_tree.column('codigo', width=100, anchor='center')
        self.product_tree.column('nombre', width=300, anchor='w')
        self.product_tree.column('precio', width=120, anchor='e')
        self.product_tree.column('stock', width=100, anchor='center')
        self.product_tree.column('categoria', width=150, anchor='center')
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.product_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient='horizontal', command=self.product_tree.xview)
        
        self.product_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Empacar tabla y scrollbars
        self.product_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Frame de botones
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill='x')
        
        # Botón seleccionar
        select_btn = tk.Button(button_frame,
                              text="✅ Seleccionar Producto",
                              font=('Arial', 12, 'bold'),
                              bg='#27ae60',
                              fg='white',
                              relief='flat',
                              padx=30,
                              pady=10,
                              command=self.select_product)
        select_btn.pack(side='left', padx=(0, 10))
        
        # Botón cerrar
        close_btn = tk.Button(button_frame,
                             text="❌ Cerrar",
                             font=('Arial', 12, 'bold'),
                             bg='#e74c3c',
                             fg='white',
                             relief='flat',
                             padx=30,
                             pady=10,
                             command=self.close_window)
        close_btn.pack(side='right')
        
        # Doble clic para seleccionar
        self.product_tree.bind('<Double-1>', lambda e: self.select_product())
        
        # Enfocar búsqueda
        self.search_entry.focus_set()
        
    def load_products(self):
        """Cargar productos de ejemplo"""
        # Datos de ejemplo (en producción se cargarían desde la base de datos)
        sample_products = [
            ('12345678', 'Arroz Premium 1kg', '₡2,500.00', '150', 'Básicos'),
            ('12345679', 'Frijoles Negros 500g', '₡1,800.00', '200', 'Básicos'),
            ('12345680', 'Aceite Vegetal 1L', '₡3,200.00', '80', 'Aceites'),
            ('12345681', 'Azúcar Blanca 1kg', '₡1,200.00', '300', 'Básicos'),
            ('12345682', 'Café Molido 250g', '₡4,500.00', '60', 'Bebidas'),
            ('12345683', 'Leche Entera 1L', '₡1,950.00', '120', 'Lácteos'),
            ('12345684', 'Pan Molde Integral', '₡2,800.00', '45', 'Panadería'),
            ('12345685', 'Queso Fresco 250g', '₡3,500.00', '35', 'Lácteos'),
            ('12345686', 'Pollo Entero 1kg', '₡4,200.00', '25', 'Carnes'),
            ('12345687', 'Detergente Líquido 1L', '₡3,800.00', '90', 'Limpieza'),
            ('12345688', 'Papel Higiénico 4 rollos', '₡2,200.00', '180', 'Limpieza'),
            ('12345689', 'Shampoo Anticaspa 400ml', '₡5,200.00', '40', 'Cuidado Personal'),
            ('12345690', 'Jabón de Baño 3 unidades', '₡2,900.00', '75', 'Cuidado Personal'),
            ('12345691', 'Pasta Dental 100ml', '₡3,100.00', '65', 'Cuidado Personal'),
            ('12345692', 'Refresco Cola 2L', '₡1,600.00', '220', 'Bebidas'),
        ]
        
        # Limpiar tabla
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        # Agregar productos
        for product in sample_products:
            self.product_tree.insert('', 'end', values=product)
    
    def on_search(self, event=None):
        """Búsqueda en tiempo real"""
        search_term = self.search_var.get().lower()
        
        # Limpiar tabla
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        # Datos de ejemplo filtrados
        sample_products = [
            ('12345678', 'Arroz Premium 1kg', '₡2,500.00', '150', 'Básicos'),
            ('12345679', 'Frijoles Negros 500g', '₡1,800.00', '200', 'Básicos'),
            ('12345680', 'Aceite Vegetal 1L', '₡3,200.00', '80', 'Aceites'),
            ('12345681', 'Azúcar Blanca 1kg', '₡1,200.00', '300', 'Básicos'),
            ('12345682', 'Café Molido 250g', '₡4,500.00', '60', 'Bebidas'),
            ('12345683', 'Leche Entera 1L', '₡1,950.00', '120', 'Lácteos'),
            ('12345684', 'Pan Molde Integral', '₡2,800.00', '45', 'Panadería'),
            ('12345685', 'Queso Fresco 250g', '₡3,500.00', '35', 'Lácteos'),
            ('12345686', 'Pollo Entero 1kg', '₡4,200.00', '25', 'Carnes'),
            ('12345687', 'Detergente Líquido 1L', '₡3,800.00', '90', 'Limpieza'),
            ('12345688', 'Papel Higiénico 4 rollos', '₡2,200.00', '180', 'Limpieza'),
            ('12345689', 'Shampoo Anticaspa 400ml', '₡5,200.00', '40', 'Cuidado Personal'),
            ('12345690', 'Jabón de Baño 3 unidades', '₡2,900.00', '75', 'Cuidado Personal'),
            ('12345691', 'Pasta Dental 100ml', '₡3,100.00', '65', 'Cuidado Personal'),
            ('12345692', 'Refresco Cola 2L', '₡1,600.00', '220', 'Bebidas'),
        ]
        
        # Filtrar productos
        filtered_products = []
        for product in sample_products:
            if (search_term in product[0].lower() or  # Código
                search_term in product[1].lower() or  # Nombre
                search_term in product[4].lower()):   # Categoría
                filtered_products.append(product)
        
        # Agregar productos filtrados
        for product in filtered_products:
            self.product_tree.insert('', 'end', values=product)
    
    def search_products(self):
        """Ejecutar búsqueda"""
        self.on_search()
    
    def clear_search(self):
        """Limpiar búsqueda"""
        self.search_var.set('')
        self.load_products()
        self.search_entry.focus_set()
    
    def select_product(self):
        """Seleccionar producto y agregarlo a la venta"""
        selected_item = self.product_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selección", "⚠️ Seleccione un producto de la lista")
            return
        
        # Obtener datos del producto seleccionado
        product_data = self.product_tree.item(selected_item[0])['values']
        
        if hasattr(self.parent, 'product_code_entry'):
            # Agregar código al campo de entrada del POS
            self.parent.product_code_entry.delete(0, tk.END)
            self.parent.product_code_entry.insert(0, product_data[0])
            
            # Agregar producto a la venta automáticamente
            if hasattr(self.parent, 'add_product_to_sale'):
                self.parent.add_product_to_sale()
        
        messagebox.showinfo("✅ Producto Seleccionado", 
                           f"Producto agregado a la venta:\n\n"
                           f"📦 {product_data[1]}\n"
                           f"💰 {product_data[2]}")
        
        self.close_window()
    
    def close_window(self):
        """Cerrar ventana"""
        self.window.destroy()


class ProductManagementWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("📦 Gestión de Productos - Caja Central POS")
        self.window.geometry("1200x700")
        self.window.configure(bg='#f0f0f0')
        self.window.resizable(True, True)
        
        # Centrar ventana
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()
        self.load_products()
        
    def setup_ui(self):
        # Frame principal
        main_frame = tk.Frame(self.window, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(main_frame, 
                              text="📦 Gestión de Productos",
                              font=('Arial', 18, 'bold'),
                              bg='#f0f0f0',
                              fg='#2c3e50')
        title_label.pack(pady=(0, 20))
        
        # Frame de herramientas
        tools_frame = tk.Frame(main_frame, bg='#f0f0f0')
        tools_frame.pack(fill='x', pady=(0, 20))
        
        # Botones de acción
        add_btn = tk.Button(tools_frame,
                           text="➕ Nuevo Producto",
                           font=('Arial', 11, 'bold'),
                           bg='#27ae60',
                           fg='white',
                           relief='flat',
                           padx=20,
                           command=self.add_product)
        add_btn.pack(side='left', padx=(0, 10))
        
        edit_btn = tk.Button(tools_frame,
                            text="✏️ Editar",
                            font=('Arial', 11, 'bold'),
                            bg='#f39c12',
                            fg='white',
                            relief='flat',
                            padx=20,
                            command=self.edit_product)
        edit_btn.pack(side='left', padx=(0, 10))
        
        delete_btn = tk.Button(tools_frame,
                              text="🗑️ Eliminar",
                              font=('Arial', 11, 'bold'),
                              bg='#e74c3c',
                              fg='white',
                              relief='flat',
                              padx=20,
                              command=self.delete_product)
        delete_btn.pack(side='left', padx=(0, 10))
        
        # Campo de búsqueda
        tk.Label(tools_frame, 
                text="Buscar:",
                font=('Arial', 11),
                bg='#f0f0f0').pack(side='right', padx=(10, 5))
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(tools_frame,
                               textvariable=self.search_var,
                               font=('Arial', 11),
                               width=30)
        search_entry.pack(side='right')
        search_entry.bind('<KeyRelease>', self.on_search)
        
        # Tabla de productos
        table_frame = tk.Frame(main_frame, bg='#f0f0f0')
        table_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Configurar Treeview
        columns = ('codigo', 'nombre', 'precio_compra', 'precio_venta', 'stock', 'categoria', 'proveedor')
        self.product_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        # Definir encabezados
        self.product_tree.heading('codigo', text='Código')
        self.product_tree.heading('nombre', text='Nombre del Producto')
        self.product_tree.heading('precio_compra', text='Precio Compra')
        self.product_tree.heading('precio_venta', text='Precio Venta')
        self.product_tree.heading('stock', text='Stock')
        self.product_tree.heading('categoria', text='Categoría')
        self.product_tree.heading('proveedor', text='Proveedor')
        
        # Configurar columnas
        self.product_tree.column('codigo', width=100, anchor='center')
        self.product_tree.column('nombre', width=250, anchor='w')
        self.product_tree.column('precio_compra', width=120, anchor='e')
        self.product_tree.column('precio_venta', width=120, anchor='e')
        self.product_tree.column('stock', width=80, anchor='center')
        self.product_tree.column('categoria', width=120, anchor='center')
        self.product_tree.column('proveedor', width=150, anchor='w')
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.product_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient='horizontal', command=self.product_tree.xview)
        
        self.product_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Empacar tabla y scrollbars
        self.product_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Frame de botones
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill='x')
        
        # Botón exportar
        export_btn = tk.Button(button_frame,
                              text="📊 Exportar a Excel",
                              font=('Arial', 11, 'bold'),
                              bg='#2ecc71',
                              fg='white',
                              relief='flat',
                              padx=20,
                              command=self.export_products)
        export_btn.pack(side='left')
        
        # Botón cerrar
        close_btn = tk.Button(button_frame,
                             text="❌ Cerrar",
                             font=('Arial', 12, 'bold'),
                             bg='#95a5a6',
                             fg='white',
                             relief='flat',
                             padx=30,
                             pady=10,
                             command=self.close_window)
        close_btn.pack(side='right')
        
        # Doble clic para editar
        self.product_tree.bind('<Double-1>', lambda e: self.edit_product())
        
    def load_products(self):
        """Cargar productos de ejemplo"""
        # Datos de ejemplo (en producción se cargarían desde la base de datos)
        sample_products = [
            ('12345678', 'Arroz Premium 1kg', '₡2,000.00', '₡2,500.00', '150', 'Básicos', 'Proveedor A'),
            ('12345679', 'Frijoles Negros 500g', '₡1,400.00', '₡1,800.00', '200', 'Básicos', 'Proveedor B'),
            ('12345680', 'Aceite Vegetal 1L', '₡2,500.00', '₡3,200.00', '80', 'Aceites', 'Proveedor C'),
            ('12345681', 'Azúcar Blanca 1kg', '₡900.00', '₡1,200.00', '300', 'Básicos', 'Proveedor A'),
            ('12345682', 'Café Molido 250g', '₡3,500.00', '₡4,500.00', '60', 'Bebidas', 'Proveedor D'),
            ('12345683', 'Leche Entera 1L', '₡1,500.00', '₡1,950.00', '120', 'Lácteos', 'Proveedor E'),
            ('12345684', 'Pan Molde Integral', '₡2,200.00', '₡2,800.00', '45', 'Panadería', 'Proveedor F'),
            ('12345685', 'Queso Fresco 250g', '₡2,800.00', '₡3,500.00', '35', 'Lácteos', 'Proveedor E'),
            ('12345686', 'Pollo Entero 1kg', '₡3,200.00', '₡4,200.00', '25', 'Carnes', 'Proveedor G'),
            ('12345687', 'Detergente Líquido 1L', '₡3,000.00', '₡3,800.00', '90', 'Limpieza', 'Proveedor H'),
            ('12345688', 'Papel Higiénico 4 rollos', '₡1,700.00', '₡2,200.00', '180', 'Limpieza', 'Proveedor H'),
            ('12345689', 'Shampoo Anticaspa 400ml', '₡4,000.00', '₡5,200.00', '40', 'Cuidado Personal', 'Proveedor I'),
            ('12345690', 'Jabón de Baño 3 unidades', '₡2,200.00', '₡2,900.00', '75', 'Cuidado Personal', 'Proveedor I'),
            ('12345691', 'Pasta Dental 100ml', '₡2,400.00', '₡3,100.00', '65', 'Cuidado Personal', 'Proveedor I'),
            ('12345692', 'Refresco Cola 2L', '₡1,200.00', '₡1,600.00', '220', 'Bebidas', 'Proveedor J'),
        ]
        
        # Limpiar tabla
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        # Agregar productos
        for product in sample_products:
            self.product_tree.insert('', 'end', values=product)
    
    def on_search(self, event=None):
        """Búsqueda en tiempo real"""
        search_term = self.search_var.get().lower()
        
        # Limpiar tabla
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        # Datos de ejemplo filtrados
        sample_products = [
            ('12345678', 'Arroz Premium 1kg', '₡2,000.00', '₡2,500.00', '150', 'Básicos', 'Proveedor A'),
            ('12345679', 'Frijoles Negros 500g', '₡1,400.00', '₡1,800.00', '200', 'Básicos', 'Proveedor B'),
            ('12345680', 'Aceite Vegetal 1L', '₡2,500.00', '₡3,200.00', '80', 'Aceites', 'Proveedor C'),
            ('12345681', 'Azúcar Blanca 1kg', '₡900.00', '₡1,200.00', '300', 'Básicos', 'Proveedor A'),
            ('12345682', 'Café Molido 250g', '₡3,500.00', '₡4,500.00', '60', 'Bebidas', 'Proveedor D'),
            ('12345683', 'Leche Entera 1L', '₡1,500.00', '₡1,950.00', '120', 'Lácteos', 'Proveedor E'),
            ('12345684', 'Pan Molde Integral', '₡2,200.00', '₡2,800.00', '45', 'Panadería', 'Proveedor F'),
            ('12345685', 'Queso Fresco 250g', '₡2,800.00', '₡3,500.00', '35', 'Lácteos', 'Proveedor E'),
            ('12345686', 'Pollo Entero 1kg', '₡3,200.00', '₡4,200.00', '25', 'Carnes', 'Proveedor G'),
            ('12345687', 'Detergente Líquido 1L', '₡3,000.00', '₡3,800.00', '90', 'Limpieza', 'Proveedor H'),
            ('12345688', 'Papel Higiénico 4 rollos', '₡1,700.00', '₡2,200.00', '180', 'Limpieza', 'Proveedor H'),
            ('12345689', 'Shampoo Anticaspa 400ml', '₡4,000.00', '₡5,200.00', '40', 'Cuidado Personal', 'Proveedor I'),
            ('12345690', 'Jabón de Baño 3 unidades', '₡2,200.00', '₡2,900.00', '75', 'Cuidado Personal', 'Proveedor I'),
            ('12345691', 'Pasta Dental 100ml', '₡2,400.00', '₡3,100.00', '65', 'Cuidado Personal', 'Proveedor I'),
            ('12345692', 'Refresco Cola 2L', '₡1,200.00', '₡1,600.00', '220', 'Bebidas', 'Proveedor J'),
        ]
        
        # Filtrar productos
        filtered_products = []
        for product in sample_products:
            if (search_term in product[0].lower() or  # Código
                search_term in product[1].lower() or  # Nombre
                search_term in product[5].lower() or  # Categoría
                search_term in product[6].lower()):   # Proveedor
                filtered_products.append(product)
        
        # Agregar productos filtrados
        for product in filtered_products:
            self.product_tree.insert('', 'end', values=product)
    
    def add_product(self):
        """Agregar nuevo producto"""
        messagebox.showinfo("Función", "Agregar Nuevo Producto\n\n(Funcionalidad en desarrollo)")
    
    def edit_product(self):
        """Editar producto seleccionado"""
        selected_item = self.product_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selección", "⚠️ Seleccione un producto para editar")
            return
        
        product_data = self.product_tree.item(selected_item[0])['values']
        messagebox.showinfo("Función", f"Editar Producto: {product_data[1]}\n\n(Funcionalidad en desarrollo)")
    
    def delete_product(self):
        """Eliminar producto seleccionado"""
        selected_item = self.product_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selección", "⚠️ Seleccione un producto para eliminar")
            return
        
        product_data = self.product_tree.item(selected_item[0])['values']
        if messagebox.askyesno("Confirmar", f"¿Eliminar el producto:\n{product_data[1]}?"):
            self.product_tree.delete(selected_item[0])
            messagebox.showinfo("✅ Eliminado", "Producto eliminado correctamente")
    
    def export_products(self):
        """Exportar productos a Excel"""
        messagebox.showinfo("Función", "Exportar a Excel\n\n(Funcionalidad en desarrollo)")
    
    def close_window(self):
        """Cerrar ventana"""
        self.window.destroy()


class InventoryWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("📊 Gestión de Inventario - Caja Central POS")
        self.window.geometry("1300x750")
        self.window.configure(bg='#f0f0f0')
        self.window.resizable(True, True)
        
        # Centrar ventana
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()
        self.load_inventory()
        
    def setup_ui(self):
        # Frame principal
        main_frame = tk.Frame(self.window, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(main_frame, 
                              text="📊 Gestión de Inventario",
                              font=('Arial', 18, 'bold'),
                              bg='#f0f0f0',
                              fg='#2c3e50')
        title_label.pack(pady=(0, 20))
        
        # Frame de estadísticas
        stats_frame = tk.Frame(main_frame, bg='#f0f0f0')
        stats_frame.pack(fill='x', pady=(0, 20))
        
        # Tarjetas de estadísticas
        self.create_stat_card(stats_frame, "Total Productos", "1,247", "#3498db", 0)
        self.create_stat_card(stats_frame, "Valor Inventario", "₡2,850,000", "#27ae60", 1)
        self.create_stat_card(stats_frame, "Stock Bajo", "23", "#e74c3c", 2)
        self.create_stat_card(stats_frame, "Sin Stock", "5", "#f39c12", 3)
        
        # Frame de herramientas
        tools_frame = tk.Frame(main_frame, bg='#f0f0f0')
        tools_frame.pack(fill='x', pady=(0, 20))
        
        # Botones de acción
        adjust_btn = tk.Button(tools_frame,
                              text="📝 Ajuste de Inventario",
                              font=('Arial', 11, 'bold'),
                              bg='#9b59b6',
                              fg='white',
                              relief='flat',
                              padx=20,
                              command=self.inventory_adjustment)
        adjust_btn.pack(side='left', padx=(0, 10))
        
        entry_btn = tk.Button(tools_frame,
                             text="📦 Entrada de Mercancía",
                             font=('Arial', 11, 'bold'),
                             bg='#27ae60',
                             fg='white',
                             relief='flat',
                             padx=20,
                             command=self.merchandise_entry)
        entry_btn.pack(side='left', padx=(0, 10))
        
        kardex_btn = tk.Button(tools_frame,
                              text="📋 Ver Kardex",
                              font=('Arial', 11, 'bold'),
                              bg='#34495e',
                              fg='white',
                              relief='flat',
                              padx=20,
                              command=self.view_kardex)
        kardex_btn.pack(side='left', padx=(0, 10))
        
        # Filtros
        tk.Label(tools_frame, 
                text="Filtrar:",
                font=('Arial', 11),
                bg='#f0f0f0').pack(side='right', padx=(20, 5))
        
        self.filter_var = tk.StringVar(value="Todos")
        filter_combo = ttk.Combobox(tools_frame, 
                                   textvariable=self.filter_var,
                                   values=["Todos", "Stock Bajo", "Sin Stock", "Normal"],
                                   state="readonly",
                                   width=15)
        filter_combo.pack(side='right', padx=(0, 10))
        filter_combo.bind('<<ComboboxSelected>>', self.apply_filter)
        
        # Campo de búsqueda
        tk.Label(tools_frame, 
                text="Buscar:",
                font=('Arial', 11),
                bg='#f0f0f0').pack(side='right', padx=(10, 5))
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(tools_frame,
                               textvariable=self.search_var,
                               font=('Arial', 11),
                               width=25)
        search_entry.pack(side='right')
        search_entry.bind('<KeyRelease>', self.on_search)
        
        # Tabla de inventario
        table_frame = tk.Frame(main_frame, bg='#f0f0f0')
        table_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Configurar Treeview
        columns = ('codigo', 'nombre', 'stock_actual', 'stock_minimo', 'precio_compra', 'precio_venta', 'valor_total', 'estado')
        self.inventory_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        # Definir encabezados
        self.inventory_tree.heading('codigo', text='Código')
        self.inventory_tree.heading('nombre', text='Producto')
        self.inventory_tree.heading('stock_actual', text='Stock Actual')
        self.inventory_tree.heading('stock_minimo', text='Stock Mínimo')
        self.inventory_tree.heading('precio_compra', text='P. Compra')
        self.inventory_tree.heading('precio_venta', text='P. Venta')
        self.inventory_tree.heading('valor_total', text='Valor Total')
        self.inventory_tree.heading('estado', text='Estado')
        
        # Configurar columnas
        self.inventory_tree.column('codigo', width=100, anchor='center')
        self.inventory_tree.column('nombre', width=250, anchor='w')
        self.inventory_tree.column('stock_actual', width=100, anchor='center')
        self.inventory_tree.column('stock_minimo', width=100, anchor='center')
        self.inventory_tree.column('precio_compra', width=110, anchor='e')
        self.inventory_tree.column('precio_venta', width=110, anchor='e')
        self.inventory_tree.column('valor_total', width=120, anchor='e')
        self.inventory_tree.column('estado', width=100, anchor='center')
        
        # Configurar tags para colores
        self.inventory_tree.tag_configure('sin_stock', background='#ffebee')
        self.inventory_tree.tag_configure('stock_bajo', background='#fff3e0')
        self.inventory_tree.tag_configure('normal', background='#e8f5e8')
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.inventory_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient='horizontal', command=self.inventory_tree.xview)
        
        self.inventory_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Empacar tabla y scrollbars
        self.inventory_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Frame de botones
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill='x')
        
        # Botón reporte
        report_btn = tk.Button(button_frame,
                              text="📊 Generar Reporte",
                              font=('Arial', 11, 'bold'),
                              bg='#2ecc71',
                              fg='white',
                              relief='flat',
                              padx=20,
                              command=self.generate_report)
        report_btn.pack(side='left')
        
        # Botón cerrar
        close_btn = tk.Button(button_frame,
                             text="❌ Cerrar",
                             font=('Arial', 12, 'bold'),
                             bg='#95a5a6',
                             fg='white',
                             relief='flat',
                             padx=30,
                             pady=10,
                             command=self.close_window)
        close_btn.pack(side='right')
        
        # Doble clic para ver detalles
        self.inventory_tree.bind('<Double-1>', lambda e: self.view_details())
    
    def create_stat_card(self, parent, title, value, color, column):
        """Crear tarjeta de estadística"""
        card_frame = tk.Frame(parent, bg=color, relief='flat', bd=2)
        card_frame.grid(row=0, column=column, padx=10, pady=5, sticky='ew')
        parent.grid_columnconfigure(column, weight=1)
        
        tk.Label(card_frame, 
                text=title,
                font=('Arial', 10, 'bold'),
                bg=color,
                fg='white').pack(pady=(10, 5))
        
        tk.Label(card_frame, 
                text=value,
                font=('Arial', 16, 'bold'),
                bg=color,
                fg='white').pack(pady=(0, 10))
    
    def load_inventory(self):
        """Cargar inventario de ejemplo"""
        # Datos de ejemplo con diferentes estados de stock
        sample_inventory = [
            ('12345678', 'Arroz Premium 1kg', '150', '20', '₡2,000', '₡2,500', '₡300,000', 'Normal'),
            ('12345679', 'Frijoles Negros 500g', '200', '30', '₡1,400', '₡1,800', '₡280,000', 'Normal'),
            ('12345680', 'Aceite Vegetal 1L', '15', '25', '₡2,500', '₡3,200', '₡37,500', 'Stock Bajo'),
            ('12345681', 'Azúcar Blanca 1kg', '300', '50', '₡900', '₡1,200', '₡270,000', 'Normal'),
            ('12345682', 'Café Molido 250g', '8', '15', '₡3,500', '₡4,500', '₡28,000', 'Stock Bajo'),
            ('12345683', 'Leche Entera 1L', '120', '40', '₡1,500', '₡1,950', '₡180,000', 'Normal'),
            ('12345684', 'Pan Molde Integral', '0', '10', '₡2,200', '₡2,800', '₡0', 'Sin Stock'),
            ('12345685', 'Queso Fresco 250g', '35', '20', '₡2,800', '₡3,500', '₡98,000', 'Normal'),
            ('12345686', 'Pollo Entero 1kg', '5', '15', '₡3,200', '₡4,200', '₡16,000', 'Stock Bajo'),
            ('12345687', 'Detergente Líquido 1L', '90', '25', '₡3,000', '₡3,800', '₡270,000', 'Normal'),
            ('12345688', 'Papel Higiénico 4 rollos', '180', '50', '₡1,700', '₡2,200', '₡306,000', 'Normal'),
            ('12345689', 'Shampoo Anticaspa 400ml', '3', '10', '₡4,000', '₡5,200', '₡12,000', 'Stock Bajo'),
            ('12345690', 'Jabón de Baño 3 unidades', '75', '30', '₡2,200', '₡2,900', '₡165,000', 'Normal'),
            ('12345691', 'Pasta Dental 100ml', '0', '20', '₡2,400', '₡3,100', '₡0', 'Sin Stock'),
            ('12345692', 'Refresco Cola 2L', '220', '80', '₡1,200', '₡1,600', '₡264,000', 'Normal'),
        ]
        
        # Limpiar tabla
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # Agregar productos con tags según el estado
        for product in sample_inventory:
            estado = product[7]
            if estado == 'Sin Stock':
                tag = 'sin_stock'
            elif estado == 'Stock Bajo':
                tag = 'stock_bajo'
            else:
                tag = 'normal'
            
            self.inventory_tree.insert('', 'end', values=product, tags=(tag,))
    
    def on_search(self, event=None):
        """Búsqueda en tiempo real"""
        search_term = self.search_var.get().lower()
        
        # Datos de ejemplo filtrados
        sample_inventory = [
            ('12345678', 'Arroz Premium 1kg', '150', '20', '₡2,000', '₡2,500', '₡300,000', 'Normal'),
            ('12345679', 'Frijoles Negros 500g', '200', '30', '₡1,400', '₡1,800', '₡280,000', 'Normal'),
            ('12345680', 'Aceite Vegetal 1L', '15', '25', '₡2,500', '₡3,200', '₡37,500', 'Stock Bajo'),
            ('12345681', 'Azúcar Blanca 1kg', '300', '50', '₡900', '₡1,200', '₡270,000', 'Normal'),
            ('12345682', 'Café Molido 250g', '8', '15', '₡3,500', '₡4,500', '₡28,000', 'Stock Bajo'),
            ('12345683', 'Leche Entera 1L', '120', '40', '₡1,500', '₡1,950', '₡180,000', 'Normal'),
            ('12345684', 'Pan Molde Integral', '0', '10', '₡2,200', '₡2,800', '₡0', 'Sin Stock'),
            ('12345685', 'Queso Fresco 250g', '35', '20', '₡2,800', '₡3,500', '₡98,000', 'Normal'),
            ('12345686', 'Pollo Entero 1kg', '5', '15', '₡3,200', '₡4,200', '₡16,000', 'Stock Bajo'),
            ('12345687', 'Detergente Líquido 1L', '90', '25', '₡3,000', '₡3,800', '₡270,000', 'Normal'),
            ('12345688', 'Papel Higiénico 4 rollos', '180', '50', '₡1,700', '₡2,200', '₡306,000', 'Normal'),
            ('12345689', 'Shampoo Anticaspa 400ml', '3', '10', '₡4,000', '₡5,200', '₡12,000', 'Stock Bajo'),
            ('12345690', 'Jabón de Baño 3 unidades', '75', '30', '₡2,200', '₡2,900', '₡165,000', 'Normal'),
            ('12345691', 'Pasta Dental 100ml', '0', '20', '₡2,400', '₡3,100', '₡0', 'Sin Stock'),
            ('12345692', 'Refresco Cola 2L', '220', '80', '₡1,200', '₡1,600', '₡264,000', 'Normal'),
        ]
        
        # Limpiar tabla
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # Filtrar productos
        filtered_products = []
        for product in sample_inventory:
            if (search_term in product[0].lower() or  # Código
                search_term in product[1].lower()):   # Nombre
                filtered_products.append(product)
        
        # Agregar productos filtrados con tags
        for product in filtered_products:
            estado = product[7]
            if estado == 'Sin Stock':
                tag = 'sin_stock'
            elif estado == 'Stock Bajo':
                tag = 'stock_bajo'
            else:
                tag = 'normal'
            
            self.inventory_tree.insert('', 'end', values=product, tags=(tag,))
    
    def apply_filter(self, event=None):
        """Aplicar filtro por estado"""
        filter_value = self.filter_var.get()
        
        # Datos de ejemplo
        sample_inventory = [
            ('12345678', 'Arroz Premium 1kg', '150', '20', '₡2,000', '₡2,500', '₡300,000', 'Normal'),
            ('12345679', 'Frijoles Negros 500g', '200', '30', '₡1,400', '₡1,800', '₡280,000', 'Normal'),
            ('12345680', 'Aceite Vegetal 1L', '15', '25', '₡2,500', '₡3,200', '₡37,500', 'Stock Bajo'),
            ('12345681', 'Azúcar Blanca 1kg', '300', '50', '₡900', '₡1,200', '₡270,000', 'Normal'),
            ('12345682', 'Café Molido 250g', '8', '15', '₡3,500', '₡4,500', '₡28,000', 'Stock Bajo'),
            ('12345683', 'Leche Entera 1L', '120', '40', '₡1,500', '₡1,950', '₡180,000', 'Normal'),
            ('12345684', 'Pan Molde Integral', '0', '10', '₡2,200', '₡2,800', '₡0', 'Sin Stock'),
            ('12345685', 'Queso Fresco 250g', '35', '20', '₡2,800', '₡3,500', '₡98,000', 'Normal'),
            ('12345686', 'Pollo Entero 1kg', '5', '15', '₡3,200', '₡4,200', '₡16,000', 'Stock Bajo'),
            ('12345687', 'Detergente Líquido 1L', '90', '25', '₡3,000', '₡3,800', '₡270,000', 'Normal'),
            ('12345688', 'Papel Higiénico 4 rollos', '180', '50', '₡1,700', '₡2,200', '₡306,000', 'Normal'),
            ('12345689', 'Shampoo Anticaspa 400ml', '3', '10', '₡4,000', '₡5,200', '₡12,000', 'Stock Bajo'),
            ('12345690', 'Jabón de Baño 3 unidades', '75', '30', '₡2,200', '₡2,900', '₡165,000', 'Normal'),
            ('12345691', 'Pasta Dental 100ml', '0', '20', '₡2,400', '₡3,100', '₡0', 'Sin Stock'),
            ('12345692', 'Refresco Cola 2L', '220', '80', '₡1,200', '₡1,600', '₡264,000', 'Normal'),
        ]
        
        # Limpiar tabla
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # Filtrar según selección
        filtered_products = []
        if filter_value == "Todos":
            filtered_products = sample_inventory
        else:
            for product in sample_inventory:
                if product[7] == filter_value:
                    filtered_products.append(product)
        
        # Agregar productos filtrados con tags
        for product in filtered_products:
            estado = product[7]
            if estado == 'Sin Stock':
                tag = 'sin_stock'
            elif estado == 'Stock Bajo':
                tag = 'stock_bajo'
            else:
                tag = 'normal'
            
            self.inventory_tree.insert('', 'end', values=product, tags=(tag,))
    
    def inventory_adjustment(self):
        """Ajuste de inventario"""
        messagebox.showinfo("Función", "Ajuste de Inventario\n\n(Funcionalidad en desarrollo)")
    
    def merchandise_entry(self):
        """Entrada de mercancía"""
        messagebox.showinfo("Función", "Entrada de Mercancía\n\n(Funcionalidad en desarrollo)")
    
    def view_kardex(self):
        """Ver kardex"""
        messagebox.showinfo("Función", "Ver Kardex\n\n(Funcionalidad en desarrollo)")
    
    def view_details(self):
        """Ver detalles del producto"""
        selected_item = self.inventory_tree.selection()
        if not selected_item:
            return
        
        product_data = self.inventory_tree.item(selected_item[0])['values']
        messagebox.showinfo("Detalles", f"Detalles del producto:\n{product_data[1]}\n\n(Vista detallada en desarrollo)")
    
    def generate_report(self):
        """Generar reporte de inventario"""
        messagebox.showinfo("Función", "Generar Reporte de Inventario\n\n(Funcionalidad en desarrollo)")
    
    def close_window(self):
        """Cerrar ventana"""
        self.window.destroy()
