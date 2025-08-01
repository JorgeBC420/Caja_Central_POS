"""
Interfaz de usuario para métodos de pago
Maneja configuración y procesamiento de diferentes métodos de pago
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
from typing import Dict, List, Optional

try:
    from modules.payments.payment_methods import PaymentManager
    from modules.payments.multi_payment import MultiPaymentProcessor
except ImportError:
    PaymentManager = None
    MultiPaymentProcessor = None

from ui.ui_helpers import create_styled_frame, format_currency, validate_numeric_input

class PaymentMethodsUI:
    """Interfaz para gestión de métodos de pago"""
    
    def __init__(self, parent_window):
        self.parent = parent_window
        try:
            self.payment_manager = PaymentManager() if PaymentManager else None
        except:
            self.payment_manager = None
        
        # Variables
        self.selected_method = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Frame principal
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(title_frame, text="Métodos de Pago", 
                 font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        # Notebook para diferentes secciones
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestañas
        self.setup_configuration_tab(notebook)
        self.setup_processing_tab(notebook)
        self.setup_reports_tab(notebook)
    
    def setup_configuration_tab(self, notebook):
        """Configura pestaña de configuración de métodos"""
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuración")
        
        # Panel izquierdo - Lista de métodos
        left_panel = create_styled_frame(config_frame, "Métodos de Pago")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Botones de acción
        buttons_frame = ttk.Frame(left_panel)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(buttons_frame, text="Nuevo Método", 
                  command=self.new_payment_method).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Editar", 
                  command=self.edit_payment_method).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Eliminar", 
                  command=self.delete_payment_method).pack(side=tk.LEFT, padx=5)
        
        # Lista de métodos
        self.methods_tree = ttk.Treeview(left_panel, 
                                        columns=('tipo', 'nombre', 'activo', 'comision'), 
                                        show='headings', height=15)
        
        self.methods_tree.heading('tipo', text='Tipo')
        self.methods_tree.heading('nombre', text='Nombre')
        self.methods_tree.heading('activo', text='Activo')
        self.methods_tree.heading('comision', text='Comisión %')
        
        self.methods_tree.column('tipo', width=100)
        self.methods_tree.column('nombre', width=150)
        self.methods_tree.column('activo', width=80)
        self.methods_tree.column('comision', width=100)
        
        scrollbar_methods = ttk.Scrollbar(left_panel, orient=tk.VERTICAL, 
                                         command=self.methods_tree.yview)
        self.methods_tree.configure(yscrollcommand=scrollbar_methods.set)
        
        self.methods_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        scrollbar_methods.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        self.methods_tree.bind('<<TreeviewSelect>>', self.on_method_select)
        
        # Panel derecho - Detalles del método
        self.setup_method_details_panel(config_frame)
        
        # Cargar métodos
        self.load_payment_methods()
    
    def setup_method_details_panel(self, parent):
        """Configura panel de detalles del método"""
        details_frame = create_styled_frame(parent, "Detalles del Método")
        details_frame.pack(side=tk.RIGHT, fill=tk.Y, width=350)
        
        content = ttk.Frame(details_frame)
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Variables del formulario
        self.type_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.active_var = tk.BooleanVar()
        self.commission_var = tk.StringVar(value="0")
        self.min_limit_var = tk.StringVar(value="0")
        self.max_limit_var = tk.StringVar(value="0")
        self.requires_auth_var = tk.BooleanVar()
        
        # Tipo de método
        ttk.Label(content, text="Tipo:").grid(row=0, column=0, sticky=tk.W, pady=5)
        type_combo = ttk.Combobox(content, textvariable=self.type_var, 
                                 values=['efectivo', 'tarjeta_credito', 'tarjeta_debito', 
                                        'transferencia', 'sinpe', 'cheque'], 
                                 state="readonly", width=25)
        type_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Nombre
        ttk.Label(content, text="Nombre:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=self.name_var, width=28).grid(
            row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Activo
        ttk.Checkbutton(content, text="Método activo", 
                       variable=self.active_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Comisión
        ttk.Label(content, text="Comisión (%):").grid(row=3, column=0, sticky=tk.W, pady=5)
        commission_entry = ttk.Entry(content, textvariable=self.commission_var, width=28)
        commission_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Límite mínimo
        ttk.Label(content, text="Límite mínimo:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=self.min_limit_var, width=28).grid(
            row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Límite máximo
        ttk.Label(content, text="Límite máximo:").grid(row=5, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=self.max_limit_var, width=28).grid(
            row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Requiere autorización
        ttk.Checkbutton(content, text="Requiere autorización", 
                       variable=self.requires_auth_var).grid(
                           row=6, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Configuración adicional
        config_frame = ttk.LabelFrame(content, text="Configuración Adicional")
        config_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.config_text = tk.Text(config_frame, height=6, width=35)
        config_scrollbar = ttk.Scrollbar(config_frame, orient=tk.VERTICAL, 
                                        command=self.config_text.yview)
        self.config_text.configure(yscrollcommand=config_scrollbar.set)
        
        self.config_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        config_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Botones de método
        method_buttons = ttk.Frame(content)
        method_buttons.grid(row=8, column=0, columnspan=2, pady=15)
        
        ttk.Button(method_buttons, text="Guardar", 
                  command=self.save_payment_method).pack(side=tk.LEFT, padx=5)
        ttk.Button(method_buttons, text="Limpiar", 
                  command=self.clear_method_form).pack(side=tk.LEFT, padx=5)
        
        content.grid_columnconfigure(1, weight=1)
    
    def setup_processing_tab(self, notebook):
        """Configura pestaña de procesamiento de pagos"""
        processing_frame = ttk.Frame(notebook)
        notebook.add(processing_frame, text="Procesamiento")
        
        # Simulador de pago
        simulator_frame = create_styled_frame(processing_frame, "Simulador de Pago")
        simulator_frame.pack(fill=tk.X, padx=10, pady=10)
        
        sim_content = ttk.Frame(simulator_frame)
        sim_content.pack(fill=tk.X, padx=15, pady=15)
        
        # Variables del simulador
        self.total_amount_var = tk.StringVar(value="10000")
        self.selected_method_var = tk.StringVar()
        
        # Monto a pagar
        ttk.Label(sim_content, text="Monto total:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(sim_content, textvariable=self.total_amount_var, width=15).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Método seleccionado
        ttk.Label(sim_content, text="Método:").grid(row=0, column=2, sticky=tk.W, padx=20, pady=5)
        method_combo = ttk.Combobox(sim_content, textvariable=self.selected_method_var, 
                                   values=['Efectivo', 'Tarjeta Crédito', 'Tarjeta Débito', 'SINPE'],
                                   width=20, state="readonly")
        method_combo.grid(row=0, column=3, sticky=tk.W, pady=5)
        
        # Botón procesar
        ttk.Button(sim_content, text="Simular Pago", 
                  command=self.simulate_payment).grid(row=0, column=4, padx=20, pady=5)
        
        # Área de resultados
        results_frame = create_styled_frame(processing_frame, "Resultados de Simulación")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.results_text = tk.Text(results_frame, height=15, width=80)
        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, 
                                         command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Multipago
        multipay_frame = create_styled_frame(processing_frame, "Pago Múltiple")
        multipay_frame.pack(fill=tk.X, padx=10, pady=10)
        
        multipay_content = ttk.Frame(multipay_frame)
        multipay_content.pack(fill=tk.X, padx=15, pady=15)
        
        ttk.Button(multipay_content, text="Configurar Pago Múltiple", 
                  command=self.open_multipay_config).pack(side=tk.LEFT)
    
    def setup_reports_tab(self, notebook):
        """Configura pestaña de reportes de pago"""
        reports_frame = ttk.Frame(notebook)
        notebook.add(reports_frame, text="Reportes")
        
        # Variables de filtros
        self.date_from_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.date_to_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.filter_method_var = tk.StringVar()
        
        # Filtros
        filters_frame = create_styled_frame(reports_frame, "Filtros de Reporte")
        filters_frame.pack(fill=tk.X, padx=10, pady=10)
        
        filter_content = ttk.Frame(filters_frame)
        filter_content.pack(fill=tk.X, padx=15, pady=15)
        
        # Fecha desde
        ttk.Label(filter_content, text="Desde:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(filter_content, textvariable=self.date_from_var, width=12).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Fecha hasta
        ttk.Label(filter_content, text="Hasta:").grid(row=0, column=2, sticky=tk.W, padx=20, pady=5)
        ttk.Entry(filter_content, textvariable=self.date_to_var, width=12).grid(
            row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Método específico
        ttk.Label(filter_content, text="Método:").grid(row=0, column=4, sticky=tk.W, padx=20, pady=5)
        filter_method_combo = ttk.Combobox(filter_content, textvariable=self.filter_method_var, 
                                          values=['Todos', 'Efectivo', 'Tarjeta Crédito', 'Tarjeta Débito', 'SINPE'],
                                          width=15, state="readonly")
        filter_method_combo.grid(row=0, column=5, sticky=tk.W, padx=5, pady=5)
        
        # Botón generar
        ttk.Button(filter_content, text="Generar Reporte", 
                  command=self.generate_payment_report).grid(row=0, column=6, padx=20, pady=5)
        
        # Tree de reportes
        report_tree_frame = create_styled_frame(reports_frame, "Transacciones de Pago")
        report_tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.report_tree = ttk.Treeview(report_tree_frame, 
                                       columns=('fecha', 'metodo', 'monto', 'comision', 'estado'), 
                                       show='headings', height=12)
        
        self.report_tree.heading('fecha', text='Fecha')
        self.report_tree.heading('metodo', text='Método')
        self.report_tree.heading('monto', text='Monto')
        self.report_tree.heading('comision', text='Comisión')
        self.report_tree.heading('estado', text='Estado')
        
        self.report_tree.column('fecha', width=120)
        self.report_tree.column('metodo', width=150)
        self.report_tree.column('monto', width=100)
        self.report_tree.column('comision', width=100)
        self.report_tree.column('estado', width=100)
        
        report_scrollbar = ttk.Scrollbar(report_tree_frame, orient=tk.VERTICAL, 
                                        command=self.report_tree.yview)
        self.report_tree.configure(yscrollcommand=report_scrollbar.set)
        
        self.report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        report_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
    
    def load_payment_methods(self):
        """Carga los métodos de pago"""
        try:
            # Limpiar tree
            for item in self.methods_tree.get_children():
                self.methods_tree.delete(item)
            
            # Obtener métodos (simulados por ahora)
            methods = [
                {'id': 1, 'tipo': 'efectivo', 'nombre': 'Efectivo', 'activo': True, 'comision': 0.0},
                {'id': 2, 'tipo': 'tarjeta_credito', 'nombre': 'Tarjeta Crédito', 'activo': True, 'comision': 3.5},
                {'id': 3, 'tipo': 'tarjeta_debito', 'nombre': 'Tarjeta Débito', 'activo': True, 'comision': 2.0},
                {'id': 4, 'tipo': 'sinpe', 'nombre': 'SINPE Móvil', 'activo': True, 'comision': 0.0},
                {'id': 5, 'tipo': 'transferencia', 'nombre': 'Transferencia', 'activo': False, 'comision': 0.0}
            ]
            
            for method in methods:
                self.methods_tree.insert('', tk.END, values=(
                    method['tipo'],
                    method['nombre'],
                    'Sí' if method['activo'] else 'No',
                    f"{method['comision']:.1f}%"
                ))
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando métodos de pago: {str(e)}")
    
    def on_method_select(self, event=None):
        """Maneja selección de método"""
        selection = self.methods_tree.selection()
        if not selection:
            return
        
        item = self.methods_tree.item(selection[0])
        values = item['values']
        
        # Cargar datos en formulario
        self.type_var.set(values[0])
        self.name_var.set(values[1])
        self.active_var.set(values[2] == 'Sí')
        commission_str = values[3].replace('%', '')
        self.commission_var.set(commission_str)
        
        # Datos simulados adicionales
        self.min_limit_var.set("100")
        self.max_limit_var.set("1000000")
        self.requires_auth_var.set(values[0] in ['tarjeta_credito', 'tarjeta_debito'])
        
        config_data = {
            'terminal_id': '12345678',
            'merchant_id': 'MERCHANT001',
            'encryption': True
        }
        self.config_text.delete(1.0, tk.END)
        self.config_text.insert(1.0, json.dumps(config_data, indent=2))
    
    def new_payment_method(self):
        """Crea nuevo método de pago"""
        self.clear_method_form()
    
    def edit_payment_method(self):
        """Edita método seleccionado"""
        selection = self.methods_tree.selection()
        if not selection:
            messagebox.showwarning("Selección", "Seleccione un método para editar")
            return
        
        # Los datos ya están cargados por on_method_select
        messagebox.showinfo("Info", "Modifique los datos y presione Guardar")
    
    def delete_payment_method(self):
        """Elimina método seleccionado"""
        selection = self.methods_tree.selection()
        if not selection:
            messagebox.showwarning("Selección", "Seleccione un método para eliminar")
            return
        
        item = self.methods_tree.item(selection[0])
        method_name = item['values'][1]
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar método '{method_name}'?"):
            self.methods_tree.delete(selection[0])
            self.clear_method_form()
    
    def save_payment_method(self):
        """Guarda método de pago"""
        try:
            # Validar datos
            if not self.name_var.get().strip():
                messagebox.showerror("Error", "Ingrese un nombre para el método")
                return
            
            # Aquí se guardaría en la base de datos
            messagebox.showinfo("Éxito", "Método de pago guardado correctamente")
            self.load_payment_methods()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando método: {str(e)}")
    
    def clear_method_form(self):
        """Limpia el formulario"""
        self.type_var.set("")
        self.name_var.set("")
        self.active_var.set(True)
        self.commission_var.set("0")
        self.min_limit_var.set("0")
        self.max_limit_var.set("0")
        self.requires_auth_var.set(False)
        self.config_text.delete(1.0, tk.END)
    
    def simulate_payment(self):
        """Simula procesamiento de pago"""
        try:
            amount = float(self.total_amount_var.get() or 0)
            method = self.selected_method_var.get()
            
            if amount <= 0:
                messagebox.showerror("Error", "Ingrese un monto válido")
                return
            
            if not method:
                messagebox.showerror("Error", "Seleccione un método de pago")
                return
            
            # Simular procesamiento
            self.results_text.delete(1.0, tk.END)
            
            result = f"""
SIMULACIÓN DE PAGO
=====================================
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Método: {method}
Monto: {format_currency(amount)}
Comisión: {format_currency(amount * 0.03)}
Total: {format_currency(amount * 1.03)}

RESULTADO: APROBADO
Código de autorización: {datetime.now().strftime('%Y%m%d%H%M%S')}
Terminal: POS001
Referencia: REF{datetime.now().strftime('%H%M%S')}

Estado de la transacción: EXITOSA
=====================================
"""
            
            self.results_text.insert(1.0, result)
            
        except ValueError:
            messagebox.showerror("Error", "Monto inválido")
        except Exception as e:
            messagebox.showerror("Error", f"Error en simulación: {str(e)}")
    
    def open_multipay_config(self):
        """Abre configuración de pago múltiple"""
        try:
            amount = float(self.total_amount_var.get() or 0)
            MultiPaymentConfigWindow(self.parent, amount)
        except ValueError:
            messagebox.showerror("Error", "Monto inválido para pago múltiple")
    
    def generate_payment_report(self):
        """Genera reporte de pagos"""
        try:
            # Limpiar tree
            for item in self.report_tree.get_children():
                self.report_tree.delete(item)
            
            # Datos simulados
            transactions = [
                ('2024-01-15 10:30', 'Efectivo', 25000, 0, 'Completado'),
                ('2024-01-15 11:45', 'Tarjeta Crédito', 50000, 1750, 'Completado'),
                ('2024-01-15 14:20', 'SINPE Móvil', 15000, 0, 'Completado'),
                ('2024-01-15 16:15', 'Tarjeta Débito', 30000, 600, 'Completado'),
                ('2024-01-15 18:30', 'Efectivo', 12000, 0, 'Completado')
            ]
            
            for trans in transactions:
                self.report_tree.insert('', tk.END, values=(
                    trans[0],
                    trans[1],
                    format_currency(trans[2]),
                    format_currency(trans[3]),
                    trans[4]
                ))
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generando reporte: {str(e)}")

class PaymentMethodsTab(ttk.Frame):
    """Pestaña de métodos de pago para integración en notebook"""
    
    def __init__(self, parent, system):
        super().__init__(parent)
        self.system = system
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de la pestaña"""
        PaymentMethodsUI(self)

class PaymentWindow(tk.Toplevel):
    """Ventana de procesamiento de pago"""
    
    def __init__(self, parent, total_amount, payment_processor=None, currency_manager=None):
        super().__init__(parent)
        self.total_amount = float(total_amount or 0)
        self.payment_processor = payment_processor
        self.currency_manager = currency_manager
        
        self.title("Procesar Pago")
        self.geometry("500x400")
        self.transient(parent)
        self.grab_set()
        
        self.result = None
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
        
        ttk.Label(summary_content, text=f"Total a pagar: {format_currency(self.total_amount)}", 
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
            change = received - self.total_amount
            
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
            
            if received < self.total_amount and self.payment_method.get() == "efectivo":
                messagebox.showerror("Error", "El monto recibido es insuficiente")
                return
            
            # Datos del pago
            self.result = [{
                'type': self.payment_method.get(),
                'amount': self.total_amount,
                'received': received,
                'change': max(0, received - self.total_amount)
            }]
            
            messagebox.showinfo("Éxito", "Pago procesado correctamente")
            self.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Ingrese un monto válido")
        except Exception as e:
            messagebox.showerror("Error", f"Error procesando pago: {str(e)}")

class MultiPaymentConfigWindow(tk.Toplevel):
    """Ventana de configuración de pago múltiple"""
    
    def __init__(self, parent, total_amount):
        super().__init__(parent)
        self.total_amount = float(total_amount or 0)
        self.title("Configurar Pago Múltiple")
        self.geometry("600x500")
        self.transient(parent)
        self.grab_set()
        
        self.payments = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Variables
        self.method_var = tk.StringVar()
        self.amount_var = tk.StringVar()
        
        # Título y total
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(title_frame, text="Configurar Pago Múltiple", 
                 font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
        ttk.Label(title_frame, text=f"Total: {format_currency(self.total_amount)}", 
                 font=('Arial', 12, 'bold')).pack(side=tk.RIGHT)
        
        # Agregar pago
        add_frame = create_styled_frame(main_frame, "Agregar Pago")
        add_frame.pack(fill=tk.X, pady=(0, 15))
        
        add_content = ttk.Frame(add_frame)
        add_content.pack(fill=tk.X, padx=15, pady=15)
        
        ttk.Label(add_content, text="Método:").grid(row=0, column=0, sticky=tk.W, pady=5)
        method_combo = ttk.Combobox(add_content, textvariable=self.method_var, 
                                   values=['Efectivo', 'Tarjeta Crédito', 'Tarjeta Débito', 'SINPE'], 
                                   state="readonly", width=20)
        method_combo.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(add_content, text="Monto:").grid(row=0, column=2, sticky=tk.W, padx=20, pady=5)
        ttk.Entry(add_content, textvariable=self.amount_var, width=15).grid(
            row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        ttk.Button(add_content, text="Agregar", 
                  command=self.add_payment).grid(row=0, column=4, padx=20, pady=5)
        
        # Lista de pagos
        payments_frame = create_styled_frame(main_frame, "Pagos Configurados")
        payments_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.payments_tree = ttk.Treeview(payments_frame, 
                                         columns=('metodo', 'monto'), 
                                         show='headings', height=8)
        
        self.payments_tree.heading('metodo', text='Método')
        self.payments_tree.heading('monto', text='Monto')
        
        self.payments_tree.column('metodo', width=200)
        self.payments_tree.column('monto', width=150)
        
        payments_scrollbar = ttk.Scrollbar(payments_frame, orient=tk.VERTICAL, 
                                          command=self.payments_tree.yview)
        self.payments_tree.configure(yscrollcommand=payments_scrollbar.set)
        
        self.payments_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        payments_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Resumen
        summary_frame = ttk.Frame(main_frame)
        summary_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.total_payments_label = ttk.Label(summary_frame, text="Total pagos: ₡0.00", 
                                             font=('Arial', 12, 'bold'))
        self.total_payments_label.pack(side=tk.LEFT)
        
        self.remaining_label = ttk.Label(summary_frame, text=f"Restante: {format_currency(self.total_amount)}", 
                                        font=('Arial', 12, 'bold'))
        self.remaining_label.pack(side=tk.RIGHT)
        
        # Botones
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="Cancelar", 
                  command=self.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="Procesar Pagos", 
                  command=self.process_payments).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="Eliminar Seleccionado", 
                  command=self.remove_payment).pack(side=tk.LEFT, padx=5)
    
    def add_payment(self):
        """Agrega un pago a la lista"""
        try:
            method = self.method_var.get()
            amount = float(self.amount_var.get() or 0)
            
            if not method:
                messagebox.showerror("Error", "Seleccione un método de pago")
                return
            
            if amount <= 0:
                messagebox.showerror("Error", "Ingrese un monto válido")
                return
            
            total_current = sum(p['amount'] for p in self.payments)
            if total_current + amount > self.total_amount:
                messagebox.showerror("Error", "El monto excede el total a pagar")
                return
            
            # Agregar pago
            payment = {'method': method, 'amount': amount}
            self.payments.append(payment)
            
            # Agregar a tree
            self.payments_tree.insert('', tk.END, values=(method, format_currency(amount)))
            
            # Limpiar campos
            self.method_var.set("")
            self.amount_var.set("")
            
            # Actualizar resumen
            self.update_summary()
            
        except ValueError:
            messagebox.showerror("Error", "Monto inválido")
        except Exception as e:
            messagebox.showerror("Error", f"Error agregando pago: {str(e)}")
    
    def remove_payment(self):
        """Elimina el pago seleccionado"""
        selection = self.payments_tree.selection()
        if not selection:
            messagebox.showwarning("Selección", "Seleccione un pago para eliminar")
            return
        
        # Obtener índice
        index = self.payments_tree.index(selection[0])
        
        # Eliminar de lista y tree
        del self.payments[index]
        self.payments_tree.delete(selection[0])
        
        # Actualizar resumen
        self.update_summary()
    
    def update_summary(self):
        """Actualiza el resumen de pagos"""
        total_payments = sum(p['amount'] for p in self.payments)
        remaining = self.total_amount - total_payments
        
        self.total_payments_label.config(text=f"Total pagos: {format_currency(total_payments)}")
        self.remaining_label.config(text=f"Restante: {format_currency(remaining)}")
        
        if remaining < 0:
            self.remaining_label.config(foreground='red')
        elif remaining == 0:
            self.remaining_label.config(foreground='green')
        else:
            self.remaining_label.config(foreground='orange')
    
    def process_payments(self):
        """Procesa los pagos múltiples"""
        if not self.payments:
            messagebox.showwarning("Sin Pagos", "Agregue al menos un método de pago")
            return
        
        total_payments = sum(p['amount'] for p in self.payments)
        if total_payments != self.total_amount:
            messagebox.showerror("Error", "El total de pagos debe coincidir con el monto a pagar")
            return
        
        messagebox.showinfo("Éxito", "Pagos múltiples procesados correctamente")
        self.destroy()

# Funciones de utilidad para compatibilidad con el sistema existente
def finalizar_venta_ui(self, event=None):
    """Finaliza la venta actual"""
    # 1. Validar que haya productos en la venta
    if not hasattr(self, 'sistema') or not hasattr(self.sistema, 'venta_actual'):
        messagebox.showwarning("Error", "No hay sistema de ventas inicializado")
        return False
        
    if not self.sistema.venta_actual.get('items', []):
        messagebox.showwarning("Sin productos", "Agrega productos antes de finalizar la venta.")
        return False

    # 2. Calcular el total y abrir la ventana de pagos
    try:
        total = self.sistema.calcular_total_venta_actual()
    except:
        total = sum(item.get('total', 0) for item in self.sistema.venta_actual.get('items', []))
    
    win = PaymentWindow(self, total)
    self.wait_window(win)

    # 3. Procesar los pagos si existen
    if not hasattr(win, "result") or not win.result:
        messagebox.showwarning("Sin pagos", "No se registraron pagos para esta venta.")
        return False

    return True

def mostrar_forma_de_pago_ui(self, pagos):
    """Muestra la forma de pago en la interfaz"""
    return_str = "Forma de pago:\n"
    for pago in pagos:
        return_str += f"- {pago.get('type', 'N/A')}: ₡{pago.get('amount', 0):,.2f}\n"
    
    if hasattr(self, 'etiqueta_pago'):
        self.etiqueta_pago.config(text=return_str)
    return return_str

def mostrar_cambio_ui(self, cambio):
    """Muestra el cambio en la interfaz"""
    if cambio > 0:
        cambio_text = f"Cambio: ₡{cambio:,.2f}"
    else:
        cambio_text = ""
    
    if hasattr(self, 'etiqueta_cambio'):
        self.etiqueta_cambio.config(text=cambio_text)
    return cambio_text

def get_total_venta_ui(self):
    """Obtiene el total de la venta actual"""
    try:
        if hasattr(self, 'sistema'):
            return self.sistema.calcular_total_venta_actual()
        else:
            return 0.0
    except:
        return 0.0

# Función principal
def mostrar_metodos_pago(parent_window):
    """Función principal para mostrar métodos de pago"""
    PaymentMethodsUI(parent_window)
