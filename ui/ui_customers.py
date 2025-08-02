"""
Ventana de Gestión de Clientes - Sistema POS
Registro, búsqueda y edición de clientes
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from PIL import Image, ImageTk

class CustomersWindow:
    """Ventana de gestión de clientes"""
    
    def __init__(self, parent=None):
        self.parent = parent
        
        # Crear ventana
        self.window = tk.Toplevel() if parent else tk.Tk()
        self.window.title("Gestión de Clientes - CajaCentral POS")
        self.window.geometry("900x600")
        self.window.resizable(True, True)
        
        # Configurar estilo
        self.window.configure(bg='#f8f9fa')
        
        # Datos simulados de clientes
        self.customers_data = [
            {"id": 1, "name": "Juan Pérez", "phone": "8888-8888", "email": "juan@email.com", "address": "San José", "purchases": 15},
            {"id": 2, "name": "María González", "phone": "7777-7777", "email": "maria@email.com", "address": "Cartago", "purchases": 8},
            {"id": 3, "name": "Carlos Rodríguez", "phone": "6666-6666", "email": "carlos@email.com", "address": "Alajuela", "purchases": 23},
            {"id": 4, "name": "Ana López", "phone": "5555-5555", "email": "ana@email.com", "address": "Heredia", "purchases": 12},
        ]
        
        # Crear interfaz
        self.create_interface()
        
        # Centrar ventana
        self.center_window()
        
        # Cargar datos
        self.load_customers()
    
    def create_interface(self):
        """Crea la interfaz principal"""
        # Header
        header_frame = tk.Frame(self.window, bg='#9b59b6', height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # Título
        title_frame = tk.Frame(header_frame, bg='#9b59b6')
        title_frame.pack(expand=True, fill='both')
        
        title_label = tk.Label(
            title_frame,
            text="👥 Gestión de Clientes",
            font=('Segoe UI', 18, 'bold'),
            fg='white',
            bg='#9b59b6'
        )
        title_label.pack(pady=20)
        
        # Toolbar
        toolbar_frame = tk.Frame(self.window, bg='#ecf0f1')
        toolbar_frame.pack(fill='x', padx=10, pady=5)
        
        # Búsqueda
        search_frame = tk.Frame(toolbar_frame, bg='#ecf0f1')
        search_frame.pack(side='left', fill='x', expand=True)
        
        tk.Label(search_frame, text="🔍 Buscar:", 
                font=('Segoe UI', 10), bg='#ecf0f1').pack(side='left', padx=5)
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                              font=('Segoe UI', 10), width=30)
        search_entry.pack(side='left', padx=5)
        search_entry.bind('<KeyRelease>', self.filter_customers)
        
        # Botones
        buttons_frame = tk.Frame(toolbar_frame, bg='#ecf0f1')
        buttons_frame.pack(side='right')
        
        tk.Button(buttons_frame, text="➕ Nuevo Cliente", 
                 command=self.new_customer, bg='#27ae60', fg='white', 
                 font=('Segoe UI', 10)).pack(side='left', padx=5)
        
        tk.Button(buttons_frame, text="✏️ Editar", 
                 command=self.edit_customer, bg='#3498db', fg='white', 
                 font=('Segoe UI', 10)).pack(side='left', padx=5)
        
        tk.Button(buttons_frame, text="🗑️ Eliminar", 
                 command=self.delete_customer, bg='#e74c3c', fg='white', 
                 font=('Segoe UI', 10)).pack(side='left', padx=5)
        
        # Lista de clientes
        list_frame = tk.Frame(self.window, bg='white')
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Crear Treeview
        columns = ("ID", "Nombre", "Teléfono", "Email", "Dirección", "Compras")
        self.customers_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # Configurar columnas
        self.customers_tree.heading("ID", text="ID")
        self.customers_tree.heading("Nombre", text="Nombre")
        self.customers_tree.heading("Teléfono", text="Teléfono")
        self.customers_tree.heading("Email", text="Email")
        self.customers_tree.heading("Dirección", text="Dirección")
        self.customers_tree.heading("Compras", text="Compras")
        
        # Ancho de columnas
        self.customers_tree.column("ID", width=50)
        self.customers_tree.column("Nombre", width=150)
        self.customers_tree.column("Teléfono", width=100)
        self.customers_tree.column("Email", width=150)
        self.customers_tree.column("Dirección", width=120)
        self.customers_tree.column("Compras", width=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.customers_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient="horizontal", command=self.customers_tree.xview)
        self.customers_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview y scrollbars
        self.customers_tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Bind doble click
        self.customers_tree.bind("<Double-1>", lambda e: self.edit_customer())
        
        # Estadísticas
        stats_frame = tk.Frame(self.window, bg='#34495e')
        stats_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.stats_label = tk.Label(stats_frame, text="", 
                                  font=('Segoe UI', 10), fg='white', bg='#34495e')
        self.stats_label.pack(pady=10)
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def load_customers(self):
        """Carga los clientes en la lista"""
        # Limpiar lista actual
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        
        # Agregar clientes
        for customer in self.customers_data:
            self.customers_tree.insert("", "end", values=(
                customer["id"],
                customer["name"],
                customer["phone"],
                customer["email"],
                customer["address"],
                customer["purchases"]
            ))
        
        # Actualizar estadísticas
        self.update_stats()
    
    def filter_customers(self, event=None):
        """Filtra clientes según búsqueda"""
        search_term = self.search_var.get().lower()
        
        # Limpiar lista
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        
        # Filtrar y mostrar
        filtered_customers = []
        for customer in self.customers_data:
            if (search_term in customer["name"].lower() or 
                search_term in customer["phone"] or 
                search_term in customer["email"].lower()):
                
                self.customers_tree.insert("", "end", values=(
                    customer["id"],
                    customer["name"],
                    customer["phone"],
                    customer["email"],
                    customer["address"],
                    customer["purchases"]
                ))
                filtered_customers.append(customer)
        
        # Actualizar estadísticas con filtro
        total_customers = len(filtered_customers)
        total_purchases = sum(c["purchases"] for c in filtered_customers)
        self.stats_label.config(text=f"📊 Mostrando {total_customers} clientes | Total compras: {total_purchases}")
    
    def update_stats(self):
        """Actualiza las estadísticas"""
        total_customers = len(self.customers_data)
        total_purchases = sum(c["purchases"] for c in self.customers_data)
        avg_purchases = total_purchases / total_customers if total_customers > 0 else 0
        
        self.stats_label.config(
            text=f"📊 Total clientes: {total_customers} | Total compras: {total_purchases} | Promedio: {avg_purchases:.1f} compras/cliente"
        )
    
    def new_customer(self):
        """Crea un nuevo cliente"""
        self.customer_form_window(is_edit=False)
    
    def edit_customer(self):
        """Edita el cliente seleccionado"""
        selection = self.customers_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un cliente para editar")
            return
        
        # Obtener datos del cliente seleccionado
        item = self.customers_tree.item(selection[0])
        customer_id = item['values'][0]
        
        # Buscar cliente en los datos
        customer = next((c for c in self.customers_data if c["id"] == customer_id), None)
        if customer:
            self.customer_form_window(is_edit=True, customer_data=customer)
    
    def delete_customer(self):
        """Elimina el cliente seleccionado"""
        selection = self.customers_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un cliente para eliminar")
            return
        
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este cliente?"):
            # Obtener ID del cliente
            item = self.customers_tree.item(selection[0])
            customer_id = item['values'][0]
            
            # Eliminar de los datos
            self.customers_data = [c for c in self.customers_data if c["id"] != customer_id]
            
            # Recargar lista
            self.load_customers()
            
            messagebox.showinfo("Éxito", "Cliente eliminado correctamente")
    
    def customer_form_window(self, is_edit=False, customer_data=None):
        """Ventana de formulario para cliente"""
        # Crear ventana
        form_window = tk.Toplevel(self.window)
        form_window.title("Editar Cliente" if is_edit else "Nuevo Cliente")
        form_window.geometry("400x500")
        form_window.resizable(False, False)
        form_window.configure(bg='white')
        
        # Centrar ventana
        form_window.transient(self.window)
        form_window.grab_set()
        
        # Header
        header_frame = tk.Frame(form_window, bg='#9b59b6', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        title = "✏️ Editar Cliente" if is_edit else "➕ Nuevo Cliente"
        tk.Label(header_frame, text=title, font=('Segoe UI', 14, 'bold'), 
                fg='white', bg='#9b59b6').pack(pady=15)
        
        # Formulario
        form_frame = tk.Frame(form_window, bg='white')
        form_frame.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Variables del formulario
        name_var = tk.StringVar()
        phone_var = tk.StringVar()
        email_var = tk.StringVar()
        address_var = tk.StringVar()
        
        # Llenar datos si es edición
        if is_edit and customer_data:
            name_var.set(customer_data["name"])
            phone_var.set(customer_data["phone"])
            email_var.set(customer_data["email"])
            address_var.set(customer_data["address"])
        
        # Campos del formulario
        tk.Label(form_frame, text="Nombre Completo:", font=('Segoe UI', 10, 'bold'), 
                bg='white').pack(anchor='w', pady=(0, 5))
        name_entry = tk.Entry(form_frame, textvariable=name_var, font=('Segoe UI', 10))
        name_entry.pack(fill='x', pady=(0, 15), ipady=5)
        name_entry.focus()
        
        tk.Label(form_frame, text="Teléfono:", font=('Segoe UI', 10, 'bold'), 
                bg='white').pack(anchor='w', pady=(0, 5))
        phone_entry = tk.Entry(form_frame, textvariable=phone_var, font=('Segoe UI', 10))
        phone_entry.pack(fill='x', pady=(0, 15), ipady=5)
        
        tk.Label(form_frame, text="Email:", font=('Segoe UI', 10, 'bold'), 
                bg='white').pack(anchor='w', pady=(0, 5))
        email_entry = tk.Entry(form_frame, textvariable=email_var, font=('Segoe UI', 10))
        email_entry.pack(fill='x', pady=(0, 15), ipady=5)
        
        tk.Label(form_frame, text="Dirección:", font=('Segoe UI', 10, 'bold'), 
                bg='white').pack(anchor='w', pady=(0, 5))
        address_entry = tk.Entry(form_frame, textvariable=address_var, font=('Segoe UI', 10))
        address_entry.pack(fill='x', pady=(0, 30), ipady=5)
        
        # Botones
        buttons_frame = tk.Frame(form_frame, bg='white')
        buttons_frame.pack(fill='x', pady=20)
        
        def save_customer():
            """Guarda el cliente"""
            if not name_var.get().strip():
                messagebox.showerror("Error", "El nombre es requerido")
                return
            
            customer_info = {
                "name": name_var.get().strip(),
                "phone": phone_var.get().strip(),
                "email": email_var.get().strip(),
                "address": address_var.get().strip()
            }
            
            if is_edit and customer_data:
                # Actualizar cliente existente
                for customer in self.customers_data:
                    if customer["id"] == customer_data["id"]:
                        customer.update(customer_info)
                        break
                messagebox.showinfo("Éxito", "Cliente actualizado correctamente")
            else:
                # Crear nuevo cliente
                new_id = max([c["id"] for c in self.customers_data]) + 1 if self.customers_data else 1
                customer_info.update({"id": new_id, "purchases": 0})
                self.customers_data.append(customer_info)
                messagebox.showinfo("Éxito", "Cliente creado correctamente")
            
            # Recargar lista y cerrar ventana
            self.load_customers()
            form_window.destroy()
        
        tk.Button(buttons_frame, text="💾 Guardar", command=save_customer, 
                 bg='#27ae60', fg='white', font=('Segoe UI', 10, 'bold'), 
                 width=12).pack(side='left', padx=5)
        
        tk.Button(buttons_frame, text="❌ Cancelar", command=form_window.destroy, 
                 bg='#e74c3c', fg='white', font=('Segoe UI', 10), 
                 width=12).pack(side='right', padx=5)
        
        # Bind Enter para guardar
        form_window.bind('<Return>', lambda e: save_customer())
        form_window.bind('<Escape>', lambda e: form_window.destroy())
    
    def run(self):
        """Ejecuta la ventana"""
        self.window.mainloop()

if __name__ == "__main__":
    customers_window = CustomersWindow()
    customers_window.run()
