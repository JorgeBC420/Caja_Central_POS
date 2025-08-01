"""
Interfaz de usuario para gestión de clientes
Maneja registro, consulta, edición y eliminar clientes
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
from typing import Optional, Dict, List, Any
import re

from modules.clients.client_manager import ClientManager
from ui.ui_helpers import create_styled_frame, create_input_frame, show_loading_dialog
from core.database import ejecutar_consulta_segura

class ClientsUI:
    """Interfaz principal para gestión de clientes"""
    
    def __init__(self, parent_window):
        self.parent = parent_window
        self.client_manager = ClientManager()
        self.current_client = None
        
        # Variables de filtros
        self.filter_vars = {
            'nombre': tk.StringVar(),
            'tipo': tk.StringVar(),
            'estado': tk.StringVar()
        }
        
        self.setup_ui()
        self.load_clients()
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="Gestión de Clientes", 
                 font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        # Botones principales
        buttons_frame = ttk.Frame(title_frame)
        buttons_frame.pack(side=tk.RIGHT)
        
        ttk.Button(buttons_frame, text="Nuevo Cliente", 
                  command=self.show_client_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Importar", 
                  command=self.import_clients).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Exportar", 
                  command=self.export_clients).pack(side=tk.LEFT, padx=5)
        
        # Frame de filtros
        self.setup_filters_frame()
        
        # Frame principal con lista y detalles
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Lista de clientes (lado izquierdo)
        self.setup_clients_list(content_frame)
        
        # Panel de detalles (lado derecho)
        self.setup_details_panel(content_frame)
    
    def setup_filters_frame(self):
        """Configura el frame de filtros"""
        filters_frame = create_styled_frame(self.main_frame, "Filtros")
        filters_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Primera fila de filtros
        filter_row1 = ttk.Frame(filters_frame)
        filter_row1.pack(fill=tk.X, padx=10, pady=5)
        
        # Buscar por nombre
        ttk.Label(filter_row1, text="Buscar:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(filter_row1, textvariable=self.filter_vars['nombre'])
        search_entry.pack(side=tk.LEFT, padx=(5, 20))
        search_entry.bind('<KeyRelease>', lambda e: self.apply_filters())
        
        # Filtro por tipo
        ttk.Label(filter_row1, text="Tipo:").pack(side=tk.LEFT)
        tipo_combo = ttk.Combobox(filter_row1, textvariable=self.filter_vars['tipo'],
                                 values=['', 'PERSONA_FISICA', 'PERSONA_JURIDICA', 'EXTRANJERO'])
        tipo_combo.pack(side=tk.LEFT, padx=(5, 20))
        tipo_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_filters())
        
        # Filtro por estado  
        ttk.Label(filter_row1, text="Estado:").pack(side=tk.LEFT)
        estado_combo = ttk.Combobox(filter_row1, textvariable=self.filter_vars['estado'],
                                   values=['', 'ACTIVO', 'INACTIVO'])
        estado_combo.pack(side=tk.LEFT, padx=(5, 20))
        estado_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_filters())
        
        # Botón limpiar filtros
        ttk.Button(filter_row1, text="Limpiar", 
                  command=self.clear_filters).pack(side=tk.RIGHT)
    
    def setup_clients_list(self, parent):
        """Configura la lista de clientes"""
        list_frame = ttk.Frame(parent)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Título de la lista
        ttk.Label(list_frame, text="Lista de Clientes", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # Treeview para clientes
        columns = ('id', 'identificacion', 'nombre', 'tipo', 'telefono', 'estado')
        self.clients_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Configurar columnas
        self.clients_tree.heading('id', text='ID')
        self.clients_tree.heading('identificacion', text='Identificación')
        self.clients_tree.heading('nombre', text='Nombre')
        self.clients_tree.heading('tipo', text='Tipo')
        self.clients_tree.heading('telefono', text='Teléfono')
        self.clients_tree.heading('estado', text='Estado')
        
        # Anchos de columnas
        self.clients_tree.column('id', width=50)
        self.clients_tree.column('identificacion', width=120)
        self.clients_tree.column('nombre', width=200)
        self.clients_tree.column('tipo', width=100)
        self.clients_tree.column('telefono', width=100)
        self.clients_tree.column('estado', width=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.clients_tree.yview)
        self.clients_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview y scrollbar
        self.clients_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind eventos
        self.clients_tree.bind('<<TreeviewSelect>>', self.on_client_select)
        self.clients_tree.bind('<Double-1>', self.edit_client)
        
        # Menú contextual
        self.setup_context_menu()
    
    def setup_details_panel(self, parent):
        """Configura el panel de detalles del cliente"""
        details_frame = ttk.Frame(parent)
        details_frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        
        # Título
        ttk.Label(details_frame, text="Detalles del Cliente", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # Notebook para organizar información
        self.details_notebook = ttk.Notebook(details_frame)
        self.details_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña información básica
        self.setup_basic_info_tab()
        
        # Pestaña historial de compras
        self.setup_purchase_history_tab()
        
        # Pestaña apartados
        self.setup_apartados_tab()
        
        # Frame de acciones
        actions_frame = ttk.Frame(details_frame)
        actions_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(actions_frame, text="Editar", 
                  command=self.edit_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Eliminar", 
                  command=self.delete_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Estado Cuenta", 
                  command=self.show_account_status).pack(side=tk.LEFT, padx=5)
    
    def setup_basic_info_tab(self):
        """Configura la pestaña de información básica"""
        basic_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(basic_frame, text="Información Básica")
        
        # Variables para mostrar información
        self.info_vars = {
            'identificacion': tk.StringVar(),
            'nombre': tk.StringVar(),
            'tipo_identificacion': tk.StringVar(),
            'telefono': tk.StringVar(),
            'email': tk.StringVar(),
            'direccion': tk.StringVar(),
            'fecha_registro': tk.StringVar(),
            'estado': tk.StringVar(),
            'limite_credito': tk.StringVar(),
            'saldo_pendiente': tk.StringVar()
        }
        
        # Campos de información (solo lectura)
        row = 0
        for field, var in self.info_vars.items():
            ttk.Label(basic_frame, text=f"{field.replace('_', ' ').title()}:").grid(
                row=row, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(basic_frame, textvariable=var, background='white', 
                     relief=tk.SUNKEN).grid(row=row, column=1, sticky=tk.EW, padx=5, pady=2)
            row += 1
        
        basic_frame.columnconfigure(1, weight=1)
    
    def setup_purchase_history_tab(self):
        """Configura la pestaña de historial de compras"""
        history_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(history_frame, text="Historial Compras")
        
        # Treeview para historial
        history_columns = ('fecha', 'factura', 'total', 'estado', 'metodo_pago')
        self.history_tree = ttk.Treeview(history_frame, columns=history_columns, 
                                        show='headings', height=10)
        
        # Configurar columnas
        self.history_tree.heading('fecha', text='Fecha')
        self.history_tree.heading('factura', text='Factura')
        self.history_tree.heading('total', text='Total')
        self.history_tree.heading('estado', text='Estado')
        self.history_tree.heading('metodo_pago', text='Método Pago')
        
        # Scrollbar para historial
        history_scroll = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, 
                                      command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scroll.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_apartados_tab(self):
        """Configura la pestaña de apartados"""
        apartados_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(apartados_frame, text="Apartados")
        
        # Treeview para apartados
        apartados_columns = ('fecha', 'producto', 'cantidad', 'abonado', 'pendiente', 'estado')
        self.apartados_tree = ttk.Treeview(apartados_frame, columns=apartados_columns, 
                                          show='headings', height=10)
        
        # Configurar columnas
        self.apartados_tree.heading('fecha', text='Fecha')
        self.apartados_tree.heading('producto', text='Producto')
        self.apartados_tree.heading('cantidad', text='Cantidad')
        self.apartados_tree.heading('abonado', text='Abonado')
        self.apartados_tree.heading('pendiente', text='Pendiente')
        self.apartados_tree.heading('estado', text='Estado')
        
        # Scrollbar para apartados
        apartados_scroll = ttk.Scrollbar(apartados_frame, orient=tk.VERTICAL, 
                                        command=self.apartados_tree.yview)
        self.apartados_tree.configure(yscrollcommand=apartados_scroll.set)
        
        self.apartados_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        apartados_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_context_menu(self):
        """Configura el menú contextual para la lista de clientes"""
        self.context_menu = tk.Menu(self.main_frame, tearoff=0)
        self.context_menu.add_command(label="Ver Detalles", command=self.view_client_details)
        self.context_menu.add_command(label="Editar", command=self.edit_client)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Nueva Venta", command=self.new_sale_for_client)
        self.context_menu.add_command(label="Nuevo Apartado", command=self.new_apartado_for_client)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Estado de Cuenta", command=self.show_account_status)
        self.context_menu.add_command(label="Eliminar", command=self.delete_client)
        
        self.clients_tree.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """Muestra el menú contextual"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def load_clients(self):
        """Carga la lista de clientes"""
        try:
            # Limpiar lista actual
            for item in self.clients_tree.get_children():
                self.clients_tree.delete(item)
            
            # Obtener clientes del manager
            clients = self.client_manager.listar_clientes()
            
            for client in clients:
                self.clients_tree.insert('', tk.END, values=(
                    client.get('id', ''),
                    client.get('identificacion', ''),
                    client.get('nombre_completo', ''),
                    client.get('tipo_identificacion', ''),
                    client.get('telefono', ''),
                    client.get('estado', '')
                ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando clientes: {str(e)}")
    
    def apply_filters(self):
        """Aplica los filtros a la lista de clientes"""
        try:
            # Obtener valores de filtros
            nombre_filter = self.filter_vars['nombre'].get().strip()
            tipo_filter = self.filter_vars['tipo'].get()
            estado_filter = self.filter_vars['estado'].get()
            
            # Construir filtros
            filters = {}
            if nombre_filter:
                filters['nombre'] = nombre_filter
            if tipo_filter:
                filters['tipo_identificacion'] = tipo_filter
            if estado_filter:
                filters['estado'] = estado_filter
            
            # Limpiar lista
            for item in self.clients_tree.get_children():
                self.clients_tree.delete(item)
            
            # Aplicar filtros
            clients = self.client_manager.buscar_clientes(filters)
            
            for client in clients:
                self.clients_tree.insert('', tk.END, values=(
                    client.get('id', ''),
                    client.get('identificacion', ''),
                    client.get('nombre_completo', ''),
                    client.get('tipo_identificacion', ''),
                    client.get('telefono', ''),
                    client.get('estado', '')
                ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Error aplicando filtros: {str(e)}")
    
    def clear_filters(self):
        """Limpia todos los filtros"""
        for var in self.filter_vars.values():
            var.set('')
        self.load_clients()
    
    def on_client_select(self, event):
        """Maneja la selección de un cliente"""
        selection = self.clients_tree.selection()
        if selection:
            item = self.clients_tree.item(selection[0])
            client_id = item['values'][0]
            self.load_client_details(client_id)
    
    def load_client_details(self, client_id):
        """Carga los detalles de un cliente"""
        try:
            # Obtener información del cliente
            client = self.client_manager.obtener_cliente(client_id)
            if not client:
                return
            
            self.current_client = client
            
            # Actualizar campos de información básica
            self.info_vars['identificacion'].set(client.get('identificacion', ''))
            self.info_vars['nombre'].set(client.get('nombre_completo', ''))
            self.info_vars['tipo_identificacion'].set(client.get('tipo_identificacion', ''))
            self.info_vars['telefono'].set(client.get('telefono', ''))
            self.info_vars['email'].set(client.get('email', ''))
            self.info_vars['direccion'].set(client.get('direccion', ''))
            self.info_vars['fecha_registro'].set(client.get('fecha_registro', ''))
            self.info_vars['estado'].set(client.get('estado', ''))
            self.info_vars['limite_credito'].set(f"₡{client.get('limite_credito', 0):,.2f}")
            self.info_vars['saldo_pendiente'].set(f"₡{client.get('saldo_pendiente', 0):,.2f}")
            
            # Cargar historial de compras
            self.load_purchase_history(client_id)
            
            # Cargar apartados
            self.load_apartados(client_id)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando detalles: {str(e)}")
    
    def load_purchase_history(self, client_id):
        """Carga el historial de compras del cliente"""
        try:
            # Limpiar historial actual
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            
            # Obtener historial
            historial = self.client_manager.obtener_historial_compras(client_id)
            
            for compra in historial:
                self.history_tree.insert('', tk.END, values=(
                    compra.get('fecha_venta', ''),
                    compra.get('numero_factura', ''),
                    f"₡{compra.get('total', 0):,.2f}",
                    compra.get('estado', ''),
                    compra.get('metodo_pago', '')
                ))
                
        except Exception as e:
            self.logger.error(f"Error cargando historial: {e}")
    
    def load_apartados(self, client_id):
        """Carga los apartados del cliente"""
        try:
            # Limpiar apartados actuales
            for item in self.apartados_tree.get_children():
                self.apartados_tree.delete(item)
            
            # Obtener apartados
            apartados = self.client_manager.obtener_apartados_cliente(client_id)
            
            for apartado in apartados:
                self.apartados_tree.insert('', tk.END, values=(
                    apartado.get('fecha_apartado', ''),
                    apartado.get('producto_nombre', ''),
                    apartado.get('cantidad', ''),
                    f"₡{apartado.get('monto_abonado', 0):,.2f}",
                    f"₡{apartado.get('monto_pendiente', 0):,.2f}",
                    apartado.get('estado', '')
                ))
                
        except Exception as e:
            self.logger.error(f"Error cargando apartados: {e}")
    
    def show_client_form(self, client_data=None):
        """Muestra el formulario de cliente"""
        ClientFormDialog(self.parent, self.client_manager, client_data, self.on_client_saved)
    
    def edit_client(self):
        """Edita el cliente seleccionado"""
        if not self.current_client:
            messagebox.showwarning("Advertencia", "Seleccione un cliente para editar")
            return
        
        self.show_client_form(self.current_client)
    
    def delete_client(self):
        """Elimina el cliente seleccionado"""
        if not self.current_client:
            messagebox.showwarning("Advertencia", "Seleccione un cliente para eliminar")
            return
        
        # Confirmar eliminación
        if messagebox.askyesno("Confirmar", 
                              f"¿Está seguro de eliminar el cliente {self.current_client.get('nombre_completo')}?"):
            try:
                success = self.client_manager.eliminar_cliente(self.current_client['id'])
                if success:
                    messagebox.showinfo("Éxito", "Cliente eliminado correctamente")
                    self.load_clients()
                    self.clear_client_details()
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el cliente")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error eliminando cliente: {str(e)}")
    
    def view_client_details(self):
        """Muestra los detalles completos del cliente"""
        if not self.current_client:
            messagebox.showwarning("Advertencia", "Seleccione un cliente")
            return
        
        # Cambiar a la pestaña de información básica
        self.details_notebook.select(0)
    
    def new_sale_for_client(self):
        """Inicia una nueva venta para el cliente seleccionado"""
        if not self.current_client:
            messagebox.showwarning("Advertencia", "Seleccione un cliente")
            return
        
        # Aquí integrar con el módulo de ventas
        messagebox.showinfo("Info", "Funcionalidad de venta en desarrollo")
    
    def new_apartado_for_client(self):
        """Crea un nuevo apartado para el cliente seleccionado"""
        if not self.current_client:
            messagebox.showwarning("Advertencia", "Seleccione un cliente")
            return
        
        # Aquí integrar con el módulo de apartados
        messagebox.showinfo("Info", "Funcionalidad de apartado en desarrollo")
    
    def show_account_status(self):
        """Muestra el estado de cuenta del cliente"""
        if not self.current_client:
            messagebox.showwarning("Advertencia", "Seleccione un cliente")
            return
        
        AccountStatusDialog(self.parent, self.client_manager, self.current_client['id'])
    
    def import_clients(self):
        """Importa clientes desde archivo"""
        file_path = filedialog.askopenfilename(
            title="Importar Clientes",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )
        
        if file_path:
            try:
                result = self.client_manager.importar_clientes(file_path)
                messagebox.showinfo("Éxito", 
                                   f"Importados {result['importados']} clientes\n"
                                   f"Errores: {result['errores']}")
                self.load_clients()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error importando: {str(e)}")
    
    def export_clients(self):
        """Exporta clientes a archivo"""
        file_path = filedialog.asksaveasfilename(
            title="Exportar Clientes",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")]
        )
        
        if file_path:
            try:
                self.client_manager.exportar_clientes(file_path)
                messagebox.showinfo("Éxito", "Clientes exportados correctamente")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error exportando: {str(e)}")
    
    def on_client_saved(self):
        """Callback cuando se guarda un cliente"""
        self.load_clients()
        messagebox.showinfo("Éxito", "Cliente guardado correctamente")
    
    def clear_client_details(self):
        """Limpia los detalles del cliente"""
        self.current_client = None
        for var in self.info_vars.values():
            var.set('')
        
        # Limpiar historial
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Limpiar apartados
        for item in self.apartados_tree.get_children():
            self.apartados_tree.delete(item)

class ClientFormDialog:
    """Diálogo para crear/editar clientes"""
    
    def __init__(self, parent, client_manager, client_data=None, callback=None):
        self.parent = parent
        self.client_manager = client_manager
        self.client_data = client_data
        self.callback = callback
        
        self.setup_dialog()
        self.setup_form()
        
        if client_data:
            self.load_client_data()
    
    def setup_dialog(self):
        """Configura el diálogo"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Nuevo Cliente" if not self.client_data else "Editar Cliente")
        self.dialog.geometry("600x700")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Centrar ventana
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (700 // 2)
        self.dialog.geometry(f"600x700+{x}+{y}")
    
    def setup_form(self):
        """Configura el formulario"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Variables del formulario
        self.form_vars = {
            'tipo_identificacion': tk.StringVar(value='CEDULA_FISICA'),
            'identificacion': tk.StringVar(),
            'nombre': tk.StringVar(),
            'apellido1': tk.StringVar(),
            'apellido2': tk.StringVar(),
            'nombre_comercial': tk.StringVar(),
            'telefono': tk.StringVar(),
            'email': tk.StringVar(),
            'direccion': tk.StringVar(),
            'provincia': tk.StringVar(),
            'canton': tk.StringVar(),
            'distrito': tk.StringVar(),
            'limite_credito': tk.DoubleVar(),
            'descuento_habitual': tk.DoubleVar(),
            'estado': tk.StringVar(value='ACTIVO'),
            'notas': tk.StringVar()
        }
        
        # Notebook para organizar campos
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña información básica
        self.setup_basic_tab(notebook)
        
        # Pestaña dirección
        self.setup_address_tab(notebook)
        
        # Pestaña configuración
        self.setup_config_tab(notebook)
        
        # Frame de botones
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(buttons_frame, text="Cancelar", 
                  command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="Guardar", 
                  command=self.save_client).pack(side=tk.RIGHT, padx=5)
    
    def setup_basic_tab(self, notebook):
        """Configura la pestaña de información básica"""
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="Información Básica")
        
        # Tipo de identificación
        ttk.Label(basic_frame, text="Tipo Identificación *:").grid(row=0, column=0, sticky=tk.W, pady=5)
        tipo_combo = ttk.Combobox(basic_frame, textvariable=self.form_vars['tipo_identificacion'],
                                 values=['CEDULA_FISICA', 'CEDULA_JURIDICA', 'DIMEX', 'NITE', 'PASAPORTE'])
        tipo_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Identificación
        ttk.Label(basic_frame, text="Identificación *:").grid(row=1, column=0, sticky=tk.W, pady=5)
        id_entry = ttk.Entry(basic_frame, textvariable=self.form_vars['identificacion'])
        id_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Nombre
        ttk.Label(basic_frame, text="Nombre *:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(basic_frame, textvariable=self.form_vars['nombre']).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Primer apellido
        ttk.Label(basic_frame, text="Primer Apellido:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(basic_frame, textvariable=self.form_vars['apellido1']).grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Segundo apellido
        ttk.Label(basic_frame, text="Segundo Apellido:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Entry(basic_frame, textvariable=self.form_vars['apellido2']).grid(row=4, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Nombre comercial
        ttk.Label(basic_frame, text="Nombre Comercial:").grid(row=5, column=0, sticky=tk.W, pady=5)
        ttk.Entry(basic_frame, textvariable=self.form_vars['nombre_comercial']).grid(row=5, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Teléfono
        ttk.Label(basic_frame, text="Teléfono:").grid(row=6, column=0, sticky=tk.W, pady=5)
        ttk.Entry(basic_frame, textvariable=self.form_vars['telefono']).grid(row=6, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Email
        ttk.Label(basic_frame, text="Email:").grid(row=7, column=0, sticky=tk.W, pady=5)
        ttk.Entry(basic_frame, textvariable=self.form_vars['email']).grid(row=7, column=1, sticky=tk.EW, padx=5, pady=5)
        
        basic_frame.columnconfigure(1, weight=1)
    
    def setup_address_tab(self, notebook):
        """Configura la pestaña de dirección"""
        address_frame = ttk.Frame(notebook)
        notebook.add(address_frame, text="Dirección")
        
        # Dirección exacta
        ttk.Label(address_frame, text="Dirección Exacta:").grid(row=0, column=0, sticky=tk.NW, pady=5)
        address_text = tk.Text(address_frame, height=3, width=40)
        address_text.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        # Bind text widget to StringVar
        address_text.bind('<KeyRelease>', lambda e: self.form_vars['direccion'].set(address_text.get(1.0, tk.END).strip()))
        
        # Provincia
        ttk.Label(address_frame, text="Provincia:").grid(row=1, column=0, sticky=tk.W, pady=5)
        provincia_combo = ttk.Combobox(address_frame, textvariable=self.form_vars['provincia'],
                                      values=['San José', 'Alajuela', 'Cartago', 'Heredia', 'Guanacaste', 'Puntarenas', 'Limón'])
        provincia_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Cantón
        ttk.Label(address_frame, text="Cantón:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(address_frame, textvariable=self.form_vars['canton']).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Distrito
        ttk.Label(address_frame, text="Distrito:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(address_frame, textvariable=self.form_vars['distrito']).grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        
        address_frame.columnconfigure(1, weight=1)
    
    def setup_config_tab(self, notebook):
        """Configura la pestaña de configuración"""
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuración")
        
        # Límite de crédito
        ttk.Label(config_frame, text="Límite de Crédito:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.form_vars['limite_credito']).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Descuento habitual
        ttk.Label(config_frame, text="Descuento Habitual (%):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.form_vars['descuento_habitual']).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Estado
        ttk.Label(config_frame, text="Estado:").grid(row=2, column=0, sticky=tk.W, pady=5)
        estado_combo = ttk.Combobox(config_frame, textvariable=self.form_vars['estado'],
                                   values=['ACTIVO', 'INACTIVO'])
        estado_combo.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Notas
        ttk.Label(config_frame, text="Notas:").grid(row=3, column=0, sticky=tk.NW, pady=5)
        notes_text = tk.Text(config_frame, height=4, width=40)
        notes_text.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        notes_text.bind('<KeyRelease>', lambda e: self.form_vars['notas'].set(notes_text.get(1.0, tk.END).strip()))
        
        config_frame.columnconfigure(1, weight=1)
    
    def load_client_data(self):
        """Carga los datos del cliente en el formulario"""
        if not self.client_data:
            return
        
        # Cargar datos en las variables
        for field, var in self.form_vars.items():
            value = self.client_data.get(field, '')
            if isinstance(var, tk.DoubleVar):
                var.set(float(value) if value else 0.0)
            else:
                var.set(value)
    
    def validate_form(self) -> tuple[bool, str]:
        """Valida el formulario"""
        # Campos requeridos
        if not self.form_vars['identificacion'].get().strip():
            return False, "La identificación es requerida"
        
        if not self.form_vars['nombre'].get().strip():
            return False, "El nombre es requerido"
        
        # Validar email si se proporciona
        email = self.form_vars['email'].get().strip()
        if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return False, "Email inválido"
        
        return True, ""
    
    def save_client(self):
        """Guarda el cliente"""
        # Validar formulario
        is_valid, error_msg = self.validate_form()
        if not is_valid:
            messagebox.showerror("Error", error_msg)
            return
        
        try:
            # Preparar datos
            client_data = {}
            for field, var in self.form_vars.items():
                if isinstance(var, tk.DoubleVar):
                    client_data[field] = var.get()
                else:
                    client_data[field] = var.get().strip()
            
            # Crear nombre completo
            nombre_completo = client_data['nombre']
            if client_data.get('apellido1'):
                nombre_completo += f" {client_data['apellido1']}"
            if client_data.get('apellido2'):
                nombre_completo += f" {client_data['apellido2']}"
            
            client_data['nombre_completo'] = nombre_completo
            
            # Guardar o actualizar
            if self.client_data:
                # Actualizar cliente existente
                client_data['id'] = self.client_data['id']
                success = self.client_manager.actualizar_cliente(client_data['id'], client_data)
            else:
                # Crear nuevo cliente
                success = self.client_manager.crear_cliente(client_data)
            
            if success:
                if self.callback:
                    self.callback()
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "No se pudo guardar el cliente")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando cliente: {str(e)}")

class AccountStatusDialog:
    """Diálogo para mostrar estado de cuenta del cliente"""
    
    def __init__(self, parent, client_manager, client_id):
        self.parent = parent
        self.client_manager = client_manager
        self.client_id = client_id
        
        self.setup_dialog()
        self.load_account_status()
    
    def setup_dialog(self):
        """Configura el diálogo"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Estado de Cuenta")
        self.dialog.geometry("800x600")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
    
    def load_account_status(self):
        """Carga el estado de cuenta"""
        try:
            estado = self.client_manager.obtener_estado_cuenta(self.client_id)
            
            # Mostrar información del estado de cuenta
            info_frame = ttk.Frame(self.dialog)
            info_frame.pack(fill=tk.X, padx=20, pady=20)
            
            ttk.Label(info_frame, text=f"Cliente: {estado.get('nombre_cliente', '')}", 
                     font=('Arial', 12, 'bold')).pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Saldo Pendiente: ₡{estado.get('saldo_pendiente', 0):,.2f}", 
                     font=('Arial', 10)).pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Límite de Crédito: ₡{estado.get('limite_credito', 0):,.2f}", 
                     font=('Arial', 10)).pack(anchor=tk.W)
            
            # Lista de transacciones pendientes
            tree_frame = ttk.Frame(self.dialog)
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
            
            columns = ('fecha', 'tipo', 'descripcion', 'monto', 'saldo')
            tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
            
            tree.heading('fecha', text='Fecha')
            tree.heading('tipo', text='Tipo')
            tree.heading('descripcion', text='Descripción')
            tree.heading('monto', text='Monto')
            tree.heading('saldo', text='Saldo')
            
            for transaccion in estado.get('transacciones', []):
                tree.insert('', tk.END, values=(
                    transaccion.get('fecha', ''),
                    transaccion.get('tipo', ''),
                    transaccion.get('descripcion', ''),
                    f"₡{transaccion.get('monto', 0):,.2f}",
                    f"₡{transaccion.get('saldo', 0):,.2f}"
                ))
            
            tree.pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando estado de cuenta: {str(e)}")

# Función principal para usar desde la aplicación principal
def mostrar_gestion_clientes(parent_window):
    """Función principal para mostrar la gestión de clientes"""
    ClientsUI(parent_window)
