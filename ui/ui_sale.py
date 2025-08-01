"""
Interfaz de usuario para ventas y punto de venta
Maneja el proceso completo de venta desde productos hasta pago
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, Dict, List, Any
from decimal import Decimal

from core.calculadora_caja import CalculadoraCaja
from modules.inventory.product import ProductManager
from ui.ui_helpers import create_styled_frame, format_currency

class SaleUI:
    """Interfaz principal de ventas/POS"""
    
    def __init__(self, parent_window):
        self.parent = parent_window
        self.product_manager = ProductManager()
        
        # Variables de venta
        self.current_sale = {
            'items': [],
            'subtotal': 0.0,
            'tax': 0.0,
            'discount': 0.0,
            'total': 0.0,
            'customer_id': None
        }
        
        # Variables de UI
        self.search_var = tk.StringVar()
        self.customer_var = tk.StringVar()
        self.discount_var = tk.StringVar(value="0")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Frame principal
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="Punto de Venta", 
                 font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        # Botones principales
        buttons_frame = ttk.Frame(title_frame)
        buttons_frame.pack(side=tk.RIGHT)
        
        ttk.Button(buttons_frame, text="Nueva Venta", 
                  command=self.new_sale).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Buscar Producto", 
                  command=self.search_product).pack(side=tk.LEFT, padx=5)
        
        # Área principal dividida
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Panel izquierdo - Productos
        self.setup_product_panel(content_frame)
        
        # Panel derecho - Venta actual
        self.setup_sale_panel(content_frame)
    
    def setup_product_panel(self, parent):
        """Configura el panel de productos"""
        product_frame = create_styled_frame(parent, "Productos")
        product_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Búsqueda
        search_frame = ttk.Frame(product_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="Buscar:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        search_entry.bind('<KeyRelease>', self.on_search_change)
        
        # Lista de productos
        self.products_tree = ttk.Treeview(product_frame, 
                                         columns=('codigo', 'nombre', 'precio', 'stock'), 
                                         show='headings', height=15)
        
        self.products_tree.heading('codigo', text='Código')
        self.products_tree.heading('nombre', text='Nombre')
        self.products_tree.heading('precio', text='Precio')
        self.products_tree.heading('stock', text='Stock')
        
        self.products_tree.column('codigo', width=100)
        self.products_tree.column('nombre', width=200)
        self.products_tree.column('precio', width=100)
        self.products_tree.column('stock', width=80)
        
        scrollbar = ttk.Scrollbar(product_frame, orient=tk.VERTICAL, command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=scrollbar.set)
        
        self.products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Bind doble clic
        self.products_tree.bind('<Double-1>', self.add_product_to_sale)
        
        # Cargar productos
        self.load_products()
    
    def setup_sale_panel(self, parent):
        """Configura el panel de venta"""
        sale_frame = create_styled_frame(parent, "Venta Actual")
        sale_frame.pack(side=tk.RIGHT, fill=tk.Y, width=400)
        
        # Cliente
        customer_frame = ttk.Frame(sale_frame)
        customer_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(customer_frame, text="Cliente:").pack(side=tk.LEFT)
        customer_combo = ttk.Combobox(customer_frame, textvariable=self.customer_var, 
                                     width=25, state="readonly")
        customer_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Items de venta
        items_frame = ttk.LabelFrame(sale_frame, text="Items")
        items_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.items_tree = ttk.Treeview(items_frame, 
                                      columns=('producto', 'cantidad', 'precio', 'total'), 
                                      show='headings', height=12)
        
        self.items_tree.heading('producto', text='Producto')
        self.items_tree.heading('cantidad', text='Cant.')
        self.items_tree.heading('precio', text='Precio')
        self.items_tree.heading('total', text='Total')
        
        self.items_tree.column('producto', width=180)
        self.items_tree.column('cantidad', width=60)
        self.items_tree.column('precio', width=80)
        self.items_tree.column('total', width=80)
        
        items_scrollbar = ttk.Scrollbar(items_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=items_scrollbar.set)
        
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        items_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Bind doble clic para editar precio
        self.items_tree.bind('<Double-1>', self.edit_item_price)
        
        # Bind para eliminar items
        self.items_tree.bind('<Delete>', self.remove_item)
        
        # Totales
        totals_frame = ttk.LabelFrame(sale_frame, text="Totales")
        totals_frame.pack(fill=tk.X, padx=10, pady=5)
        
        totals_content = ttk.Frame(totals_frame)
        totals_content.pack(fill=tk.X, padx=10, pady=10)
        
        # Subtotal
        ttk.Label(totals_content, text="Subtotal:").grid(row=0, column=0, sticky=tk.W)
        self.subtotal_label = ttk.Label(totals_content, text="₡0.00", font=('Arial', 10, 'bold'))
        self.subtotal_label.grid(row=0, column=1, sticky=tk.E)
        
        # Descuento
        ttk.Label(totals_content, text="Descuento:").grid(row=1, column=0, sticky=tk.W)
        discount_entry = ttk.Entry(totals_content, textvariable=self.discount_var, width=10)
        discount_entry.grid(row=1, column=1, sticky=tk.E)
        discount_entry.bind('<KeyRelease>', self.calculate_totals)
        
        # IVA
        ttk.Label(totals_content, text="IVA (13%):").grid(row=2, column=0, sticky=tk.W)
        self.tax_label = ttk.Label(totals_content, text="₡0.00")
        self.tax_label.grid(row=2, column=1, sticky=tk.E)
        
        # Total
        ttk.Label(totals_content, text="TOTAL:", font=('Arial', 12, 'bold')).grid(row=3, column=0, sticky=tk.W)
        self.total_label = ttk.Label(totals_content, text="₡0.00", 
                                    font=('Arial', 14, 'bold'), foreground='blue')
        self.total_label.grid(row=3, column=1, sticky=tk.E)
        
        totals_content.grid_columnconfigure(1, weight=1)
        
        # Botones de acción
        actions_frame = ttk.Frame(sale_frame)
        actions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(actions_frame, text="Procesar Pago", 
                  command=self.process_payment).pack(fill=tk.X, pady=2)
        ttk.Button(actions_frame, text="Guardar Apartado", 
                  command=self.save_layaway).pack(fill=tk.X, pady=2)
        ttk.Button(actions_frame, text="Cancelar Venta", 
                  command=self.cancel_sale).pack(fill=tk.X, pady=2)
    
    def load_products(self):
        """Carga la lista de productos"""
        try:
            # Limpiar tree
            for item in self.products_tree.get_children():
                self.products_tree.delete(item)
            
            # Obtener productos activos
            products = self.product_manager.obtener_todos_activos()
            
            for product in products:
                self.products_tree.insert('', tk.END, values=(
                    product.get('codigo', ''),
                    product.get('nombre', ''),
                    format_currency(product.get('precio_venta', 0)),
                    product.get('stock_actual', 0)
                ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando productos: {str(e)}")
    
    def on_search_change(self, event=None):
        """Maneja cambios en la búsqueda"""
        search_text = self.search_var.get().lower()
        
        # Limpiar tree
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        if not search_text:
            self.load_products()
            return
        
        try:
            # Buscar productos
            products = self.product_manager.buscar(search_text)
            
            for product in products:
                if (search_text in product.get('nombre', '').lower() or 
                    search_text in product.get('codigo', '').lower()):
                    
                    self.products_tree.insert('', tk.END, values=(
                        product.get('codigo', ''),
                        product.get('nombre', ''),
                        format_currency(product.get('precio_venta', 0)),
                        product.get('stock_actual', 0)
                    ))
        except Exception as e:
            print(f"Error en búsqueda: {e}")
    
    def add_product_to_sale(self, event=None):
        """Agrega producto a la venta"""
        selection = self.products_tree.selection()
        if not selection:
            return
        
        item = self.products_tree.item(selection[0])
        codigo = item['values'][0]
        nombre = item['values'][1]
        precio_str = item['values'][2].replace('₡', '').replace(',', '')
        stock = int(item['values'][3])
        
        if stock <= 0:
            messagebox.showwarning("Sin Stock", f"El producto {nombre} no tiene stock disponible")
            return
        
        try:
            precio = float(precio_str)
        except ValueError:
            messagebox.showerror("Error", "Error en el precio del producto")
            return
        
        # Verificar si ya está en la venta
        for item in self.current_sale['items']:
            if item['codigo'] == codigo:
                # Incrementar cantidad
                item['cantidad'] += 1
                item['total'] = item['cantidad'] * item['precio']
                break
        else:
            # Agregar nuevo item
            self.current_sale['items'].append({
                'codigo': codigo,
                'nombre': nombre,
                'cantidad': 1,
                'precio': precio,
                'total': precio
            })
        
        self.update_sale_display()
    
    def remove_item(self, event=None):
        """Elimina item de la venta"""
        selection = self.items_tree.selection()
        if not selection:
            return
        
        # Obtener índice del item
        item_index = self.items_tree.index(selection[0])
        
        # Eliminar del current_sale
        if 0 <= item_index < len(self.current_sale['items']):
            del self.current_sale['items'][item_index]
        
        self.update_sale_display()
    
    def update_sale_display(self):
        """Actualiza la visualización de la venta"""
        # Limpiar tree de items
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        
        # Mostrar items actuales
        for item in self.current_sale['items']:
            self.items_tree.insert('', tk.END, values=(
                item['nombre'],
                item['cantidad'],
                format_currency(item['precio']),
                format_currency(item['total'])
            ))
        
        # Calcular totales
        self.calculate_totals()
    
    def calculate_totals(self, event=None):
        """Calcula los totales de la venta"""
        try:
            # Calcular subtotal
            subtotal = sum(item['total'] for item in self.current_sale['items'])
            
            # Aplicar descuento
            discount_percent = float(self.discount_var.get() or 0)
            discount_amount = subtotal * (discount_percent / 100)
            
            # Calcular subtotal después del descuento
            subtotal_after_discount = subtotal - discount_amount
            
            # Calcular IVA (13%)
            tax = subtotal_after_discount * 0.13
            
            # Total final
            total = subtotal_after_discount + tax
            
            # Actualizar variables
            self.current_sale['subtotal'] = subtotal
            self.current_sale['discount'] = discount_amount
            self.current_sale['tax'] = tax
            self.current_sale['total'] = total
            
            # Actualizar labels
            self.subtotal_label.config(text=format_currency(subtotal))
            self.tax_label.config(text=format_currency(tax))
            self.total_label.config(text=format_currency(total))
            
        except ValueError:
            # Error en descuento
            self.discount_var.set("0")
    
    def new_sale(self):
        """Inicia una nueva venta"""
        if self.current_sale['items']:
            if not messagebox.askyesno("Nueva Venta", "¿Desea cancelar la venta actual?"):
                return
        
        # Reiniciar venta
        self.current_sale = {
            'items': [],
            'subtotal': 0.0,
            'tax': 0.0,
            'discount': 0.0,
            'total': 0.0,
            'customer_id': None
        }
        
        self.customer_var.set("")
        self.discount_var.set("0")
        self.update_sale_display()
    
    def process_payment(self):
        """Procesa el pago de la venta"""
        if not self.current_sale['items']:
            messagebox.showwarning("Venta Vacía", "Agregue productos a la venta")
            return
        
        # Abrir ventana de pago
        PaymentWindow(self.parent, self.current_sale, self.on_payment_complete)
    
    def on_payment_complete(self, payment_data):
        """Maneja completación del pago"""
        try:
            # Aquí se procesaría el pago y se guardaría la venta
            messagebox.showinfo("Venta Procesada", "Venta completada exitosamente")
            self.new_sale()
        except Exception as e:
            messagebox.showerror("Error", f"Error procesando pago: {str(e)}")
    
    def save_layaway(self):
        """Guarda como apartado"""
        if not self.current_sale['items']:
            messagebox.showwarning("Venta Vacía", "Agregue productos para apartar")
            return
        
        messagebox.showinfo("Info", "Función de apartados en desarrollo")
    
    def cancel_sale(self):
        """Cancela la venta actual"""
        if self.current_sale['items']:
            if messagebox.askyesno("Cancelar Venta", "¿Está seguro de cancelar la venta?"):
                self.new_sale()
    
    def search_product(self):
        """Abre búsqueda avanzada de productos"""
        messagebox.showinfo("Info", "Búsqueda avanzada en desarrollo")

class SaleTab(ttk.Frame):
    """Pestaña de venta para integración en notebook"""
    
    def __init__(self, parent, system):
        super().__init__(parent)
        self.system = system
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de la pestaña"""
        SaleUI(self)

class PaymentWindow(tk.Toplevel):
    """Ventana de procesamiento de pago"""
    
    def __init__(self, parent, sale_data, callback):
        super().__init__(parent)
        self.sale_data = sale_data
        self.callback = callback
        self.title("Procesar Pago")
        self.geometry("500x400")
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de pago"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Resumen de venta
        summary_frame = create_styled_frame(main_frame, "Resumen de Venta")
        summary_frame.pack(fill=tk.X, pady=(0, 15))
        
        summary_content = ttk.Frame(summary_frame)
        summary_content.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(summary_content, text=f"Total a pagar: {format_currency(self.sale_data['total'])}", 
                 font=('Arial', 14, 'bold')).pack()
        
        # Métodos de pago
        payment_frame = create_styled_frame(main_frame, "Método de Pago")
        payment_frame.pack(fill=tk.X, pady=(0, 15))
        
        payment_content = ttk.Frame(payment_frame)
        payment_content.pack(fill=tk.X, padx=10, pady=10)
        
        self.payment_method = tk.StringVar(value="efectivo")
        
        ttk.Radiobutton(payment_content, text="Efectivo", 
                       variable=self.payment_method, value="efectivo").pack(anchor=tk.W)
        ttk.Radiobutton(payment_content, text="Tarjeta", 
                       variable=self.payment_method, value="tarjeta").pack(anchor=tk.W)
        ttk.Radiobutton(payment_content, text="Transferencia", 
                       variable=self.payment_method, value="transferencia").pack(anchor=tk.W)
        
        # Monto recibido
        amount_frame = ttk.Frame(payment_content)
        amount_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(amount_frame, text="Monto recibido:").pack(side=tk.LEFT)
        self.amount_received = tk.StringVar()
        amount_entry = ttk.Entry(amount_frame, textvariable=self.amount_received)
        amount_entry.pack(side=tk.RIGHT, padx=5)
        amount_entry.bind('<KeyRelease>', self.calculate_change)
        
        # Cambio
        self.change_label = ttk.Label(payment_content, text="Cambio: ₡0.00", 
                                     font=('Arial', 12, 'bold'))
        self.change_label.pack()
        
        # Botones
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(buttons_frame, text="Cancelar", 
                  command=self.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="Procesar Pago", 
                  command=self.process_payment).pack(side=tk.RIGHT, padx=5)
    
    def calculate_change(self, event=None):
        """Calcula el cambio"""
        try:
            received = float(self.amount_received.get() or 0)
            total = self.sale_data['total']
            change = received - total
            
            if change >= 0:
                self.change_label.config(text=f"Cambio: {format_currency(change)}", 
                                       foreground='green')
            else:
                self.change_label.config(text=f"Falta: {format_currency(abs(change))}", 
                                       foreground='red')
        except ValueError:
            self.change_label.config(text="Cambio: ₡0.00", foreground='black')
    
    def process_payment(self):
        """Procesa el pago"""
        try:
            received = float(self.amount_received.get() or 0)
            total = self.sale_data['total']
            
            if received < total and self.payment_method.get() == "efectivo":
                messagebox.showerror("Error", "El monto recibido es insuficiente")
                return
            
            # Datos del pago
            payment_data = {
                'method': self.payment_method.get(),
                'amount_received': received,
                'change': max(0, received - total),
                'sale_data': self.sale_data
            }
            
            # Llamar callback
            self.callback(payment_data)
            self.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Ingrese un monto válido")
        except Exception as e:
            messagebox.showerror("Error", f"Error procesando pago: {str(e)}")
    
    def edit_item_price(self, event):
        """Edita el precio de un item con doble clic"""
        selection = self.items_tree.selection()
        if not selection:
            return
        
        item = self.items_tree.item(selection[0])
        values = item['values']
        product_name = values[0]
        current_price = float(str(values[2]).replace('₡', '').replace(',', ''))
        current_quantity = int(values[1])
        
        # Crear ventana de edición
        edit_window = tk.Toplevel(self.parent)
        edit_window.title("Editar Precio - Estilo Eleventa")
        edit_window.geometry("450x350")
        edit_window.resizable(False, False)
        edit_window.transient(self.parent)
        edit_window.grab_set()
        
        # Centrar ventana
        edit_window.update_idletasks()
        x = (edit_window.winfo_screenwidth() // 2) - (225)
        y = (edit_window.winfo_screenheight() // 2) - (175)
        edit_window.geometry(f"450x350+{x}+{y}")
        
        # Configurar estilo moderno
        edit_window.configure(bg='#f8f9fa')
        
        # Header azul estilo Eleventa
        header_frame = tk.Frame(edit_window, bg='#2c3e50', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg='#2c3e50')
        header_content.pack(expand=True, fill=tk.BOTH, padx=20, pady=15)
        
        tk.Label(header_content, text="Cambiar Precio", 
                font=('Segoe UI', 16, 'bold'), fg='white', bg='#2c3e50').pack()
        
        # Contenido principal
        main_frame = tk.Frame(edit_window, bg='white', padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Información del producto
        product_frame = tk.Frame(main_frame, bg='white')
        product_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(product_frame, text="Producto:", 
                font=('Segoe UI', 10, 'bold'), bg='white', fg='#2c3e50').pack(anchor=tk.W)
        
        product_label = tk.Label(product_frame, text=product_name, 
                                font=('Segoe UI', 11), bg='white', fg='#34495e',
                                wraplength=350, justify=tk.LEFT)
        product_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Precio actual
        current_frame = tk.Frame(main_frame, bg='white')
        current_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(current_frame, text="Precio Actual:", 
                font=('Segoe UI', 10, 'bold'), bg='white', fg='#2c3e50').pack(anchor=tk.W)
        
        price_display = tk.Label(current_frame, text=f"₡{current_price:,.2f}", 
                                font=('Segoe UI', 18, 'bold'), bg='white', fg='#27ae60')
        price_display.pack(anchor=tk.W, pady=(5, 0))
        
        # Nuevo precio
        new_price_frame = tk.Frame(main_frame, bg='white')
        new_price_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(new_price_frame, text="Nuevo Precio:", 
                font=('Segoe UI', 10, 'bold'), bg='white', fg='#2c3e50').pack(anchor=tk.W)
        
        price_entry = tk.Entry(new_price_frame, font=('Segoe UI', 16), width=15, 
                              justify='center', relief=tk.FLAT, bd=5)
        price_entry.pack(anchor=tk.W, pady=(5, 0), ipady=8)
        price_entry.insert(0, f"{current_price:.2f}")
        price_entry.select_range(0, tk.END)
        price_entry.focus_set()
        
        # Descuento
        discount_frame = tk.Frame(main_frame, bg='white')
        discount_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(discount_frame, text="Descuento (%):", 
                font=('Segoe UI', 10, 'bold'), bg='white', fg='#2c3e50').pack(anchor=tk.W)
        
        discount_entry = tk.Entry(discount_frame, font=('Segoe UI', 12), width=10, 
                                 justify='center', relief=tk.FLAT, bd=5)
        discount_entry.pack(anchor=tk.W, pady=(5, 0), ipady=5)
        discount_entry.insert(0, "0.00")
        
        # Botones
        buttons_frame = tk.Frame(main_frame, bg='white')
        buttons_frame.pack(fill=tk.X, pady=(20, 0))
        
        def apply_price_change():
            try:
                new_price = float(price_entry.get())
                discount = float(discount_entry.get())
                
                if new_price <= 0:
                    messagebox.showerror("Error", "El precio debe ser mayor que cero")
                    return
                
                # Aplicar descuento si hay
                final_price = new_price * (1 - discount / 100)
                
                # Actualizar el item en la venta
                new_total = final_price * current_quantity
                
                # Actualizar valores en el treeview
                updated_values = (product_name, current_quantity, f"₡{final_price:,.2f}", f"₡{new_total:,.2f}")
                self.items_tree.item(selection[0], values=updated_values)
                
                # Actualizar total de venta
                self.update_sale_totals()
                
                edit_window.destroy()
                messagebox.showinfo("Precio Actualizado", 
                                   f"Precio actualizado a ₡{final_price:,.2f}")
                
            except ValueError:
                messagebox.showerror("Error", "Ingrese valores numéricos válidos")
            except Exception as e:
                messagebox.showerror("Error", f"Error actualizando precio: {str(e)}")
        
        def cancel_edit():
            edit_window.destroy()
        
        # Botón principal - Aplicar cambio
        apply_btn = tk.Button(buttons_frame, text="✓ Cambiar Precio", 
                             command=apply_price_change,
                             font=('Segoe UI', 12, 'bold'), bg='#27ae60', fg='white',
                             relief=tk.FLAT, padx=30, pady=12, cursor='hand2')
        apply_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón cancelar
        cancel_btn = tk.Button(buttons_frame, text="✗ Cancelar", 
                              command=cancel_edit,
                              font=('Segoe UI', 12, 'bold'), bg='#e74c3c', fg='white',
                              relief=tk.FLAT, padx=30, pady=12, cursor='hand2')
        cancel_btn.pack(side=tk.LEFT)
        
        # Bind Enter para aplicar cambio
        price_entry.bind('<Return>', lambda e: apply_price_change())
        edit_window.bind('<Escape>', lambda e: cancel_edit())
        
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

# Función principal
def mostrar_punto_venta(parent_window):
    """Función principal para mostrar el punto de venta"""
    SaleUI(parent_window)