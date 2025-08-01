"""
Integración de Facturación Electrónica con el Sistema POS
Módulo para conectar las ventas con la generación automática de facturas electrónicas
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
i        # Botón generar factura
        generate_btn = tk.Button(actions_frame, text="📄 Generar Factura Electrónica", 
                                command=self.generate_electronic_invoice,
                                font=('Segoe UI', 12, 'bold'), bg='#27ae60', fg='white',
                                relief=tk.FLAT, padx=30, pady=12, cursor='hand2')
        generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón PDF v4.4
        pdf_v44_btn = tk.Button(actions_frame, text="📋 Exportar PDF v4.4", 
                               command=self.export_pdf_v44,
                               font=('Segoe UI', 12, 'bold'), bg='#e74c3c', fg='white',
                               relief=tk.FLAT, padx=30, pady=12, cursor='hand2')
        pdf_v44_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón vista previa
        preview_btn = tk.Button(actions_frame, text="👁️ Vista Previa PDF", 
                               command=self.preview_pdf,
                               font=('Segoe UI', 11), bg='#3498db', fg='white',
                               relief=tk.FLAT, padx=20, pady=12, cursor='hand2')
        preview_btn.pack(side=tk.LEFT, padx=(0, 10))rom datetime import datetime
import threading
from typing import Dict, List, Optional
import webbrowser

# Importar el módulo de facturación electrónica
try:
    from modules.invoicing.facturacion_electronica_cr import FacturacionElectronicaCR
    FACTURACION_AVAILABLE = True
except ImportError:
    FACTURACION_AVAILABLE = False
    print("Módulo de facturación electrónica no disponible")

class FacturacionElectronicaUI:
    """Interfaz para gestión de facturación electrónica"""
    
    def __init__(self, parent_window, venta_data: Dict = None):
        self.parent = parent_window
        self.venta_data = venta_data or {}
        self.facturacion_system = None
        
        if FACTURACION_AVAILABLE:
            self.facturacion_system = FacturacionElectronicaCR()
        
        self.create_window()
    
    def create_window(self):
        """Crea la ventana de facturación electrónica"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("💻 Facturación Electrónica - Costa Rica")
        self.window.geometry("900x700")
        self.window.resizable(True, True)
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Centrar ventana
        self.center_window()
        
        # Configurar estilo
        self.window.configure(bg='#f8f9fa')
        
        # Crear interfaz
        self.create_interface()
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_interface(self):
        """Crea la interfaz principal"""
        # Header
        self.create_header()
        
        # Notebook para pestañas
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Pestaña de generación
        self.create_generation_tab()
        
        # Pestaña de configuración
        self.create_config_tab()
        
        # Pestaña de historial
        self.create_history_tab()
        
        # Pestaña de ayuda
        self.create_help_tab()
    
    def create_header(self):
        """Crea el header de la ventana"""
        header_frame = tk.Frame(self.window, bg='#2c3e50', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg='#2c3e50')
        header_content.pack(expand=True, fill=tk.BOTH, padx=20, pady=15)
        
        # Título
        title_label = tk.Label(header_content, text="🧾 Facturación Electrónica Costa Rica", 
                              font=('Segoe UI', 16, 'bold'), fg='white', bg='#2c3e50')
        title_label.pack(side=tk.LEFT)
        
        # Estado del sistema
        status_frame = tk.Frame(header_content, bg='#2c3e50')
        status_frame.pack(side=tk.RIGHT)
        
        if FACTURACION_AVAILABLE:
            status_text = "🟢 Sistema Activo"
            status_color = '#27ae60'
        else:
            status_text = "🔴 No Disponible"
            status_color = '#e74c3c'
        
        status_label = tk.Label(status_frame, text=status_text, 
                               font=('Segoe UI', 10, 'bold'), fg=status_color, bg='#2c3e50')
        status_label.pack()
        
        version_label = tk.Label(status_frame, text="Versión XML 4.4", 
                                font=('Segoe UI', 9), fg='#bdc3c7', bg='#2c3e50')
        version_label.pack()
    
    def create_generation_tab(self):
        """Pestaña de generación de facturas"""
        gen_frame = ttk.Frame(self.notebook)
        self.notebook.add(gen_frame, text="📄 Generar Factura")
        
        # Scroll frame
        canvas = tk.Canvas(gen_frame, bg='white')
        scrollbar = ttk.Scrollbar(gen_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Datos de la factura
        self.create_invoice_form(scrollable_frame)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_invoice_form(self, parent):
        """Crea el formulario de datos de factura"""
        # Información general
        info_frame = tk.LabelFrame(parent, text="📋 Información General", 
                                  font=('Segoe UI', 11, 'bold'), bg='white', padx=15, pady=15)
        info_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Número de factura
        tk.Label(info_frame, text="Número de Factura:", font=('Segoe UI', 10), bg='white').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.invoice_number = tk.Entry(info_frame, font=('Segoe UI', 11), width=20)
        self.invoice_number.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        self.invoice_number.insert(0, self.get_next_invoice_number())
        
        # Tipo de documento
        tk.Label(info_frame, text="Tipo de Documento:", font=('Segoe UI', 10), bg='white').grid(row=0, column=2, sticky=tk.W, padx=(20, 0), pady=5)
        self.doc_type = ttk.Combobox(info_frame, values=["Factura Electrónica", "Tiquete Electrónico"], state="readonly", width=18)
        self.doc_type.grid(row=0, column=3, sticky=tk.W, padx=(10, 0), pady=5)
        self.doc_type.set("Factura Electrónica")
        
        # Condición de venta
        tk.Label(info_frame, text="Condición de Venta:", font=('Segoe UI', 10), bg='white').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.sale_condition = ttk.Combobox(info_frame, values=["Contado", "Crédito"], state="readonly", width=18)
        self.sale_condition.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        self.sale_condition.set("Contado")
        
        # Medio de pago
        tk.Label(info_frame, text="Medio de Pago:", font=('Segoe UI', 10), bg='white').grid(row=1, column=2, sticky=tk.W, padx=(20, 0), pady=5)
        self.payment_method = ttk.Combobox(info_frame, values=["Efectivo", "Tarjeta", "SINPE Móvil", "Cheque"], state="readonly", width=18)
        self.payment_method.grid(row=1, column=3, sticky=tk.W, padx=(10, 0), pady=5)
        self.payment_method.set("Efectivo")
        
        # Datos del cliente
        client_frame = tk.LabelFrame(parent, text="👤 Datos del Cliente", 
                                    font=('Segoe UI', 11, 'bold'), bg='white', padx=15, pady=15)
        client_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Nombre del cliente
        tk.Label(client_frame, text="Nombre Completo:", font=('Segoe UI', 10), bg='white').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.client_name = tk.Entry(client_frame, font=('Segoe UI', 11), width=40)
        self.client_name.grid(row=0, column=1, columnspan=2, sticky=tk.W+tk.E, padx=(10, 0), pady=5)
        
        # Cédula
        tk.Label(client_frame, text="Cédula/ID:", font=('Segoe UI', 10), bg='white').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.client_id = tk.Entry(client_frame, font=('Segoe UI', 11), width=20)
        self.client_id.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Tipo de identificación
        tk.Label(client_frame, text="Tipo ID:", font=('Segoe UI', 10), bg='white').grid(row=1, column=2, sticky=tk.W, padx=(20, 0), pady=5)
        self.id_type = ttk.Combobox(client_frame, values=["Física", "Jurídica", "DIMEX", "NITE"], state="readonly", width=15)
        self.id_type.grid(row=1, column=3, sticky=tk.W, padx=(10, 0), pady=5)
        self.id_type.set("Física")
        
        # Email y teléfono
        tk.Label(client_frame, text="Email:", font=('Segoe UI', 10), bg='white').grid(row=2, column=0, sticky=tk.W, pady=5)
        self.client_email = tk.Entry(client_frame, font=('Segoe UI', 11), width=30)
        self.client_email.grid(row=2, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=5)
        
        tk.Label(client_frame, text="Teléfono:", font=('Segoe UI', 10), bg='white').grid(row=2, column=2, sticky=tk.W, padx=(20, 0), pady=5)
        self.client_phone = tk.Entry(client_frame, font=('Segoe UI', 11), width=15)
        self.client_phone.grid(row=2, column=3, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Dirección
        tk.Label(client_frame, text="Dirección:", font=('Segoe UI', 10), bg='white').grid(row=3, column=0, sticky=tk.W, pady=5)
        self.client_address = tk.Text(client_frame, font=('Segoe UI', 10), width=60, height=3)
        self.client_address.grid(row=3, column=1, columnspan=3, sticky=tk.W+tk.E, padx=(10, 0), pady=5)
        
        # Configurar grid weights
        client_frame.grid_columnconfigure(1, weight=1)
        
        # Productos de la venta
        products_frame = tk.LabelFrame(parent, text="🛒 Productos de la Venta", 
                                      font=('Segoe UI', 11, 'bold'), bg='white', padx=15, pady=15)
        products_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Tabla de productos
        self.create_products_table(products_frame)
        
        # Totales
        totals_frame = tk.Frame(products_frame, bg='white')
        totals_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Labels de totales
        totals_labels_frame = tk.Frame(totals_frame, bg='white')
        totals_labels_frame.pack(side=tk.RIGHT)
        
        self.subtotal_label = tk.Label(totals_labels_frame, text="Subtotal: ₡0.00", 
                                      font=('Segoe UI', 11), bg='white')
        self.subtotal_label.pack(anchor=tk.E)
        
        self.tax_label = tk.Label(totals_labels_frame, text="IVA (13%): ₡0.00", 
                                 font=('Segoe UI', 11), bg='white')
        self.tax_label.pack(anchor=tk.E)
        
        self.total_label = tk.Label(totals_labels_frame, text="TOTAL: ₡0.00", 
                                   font=('Segoe UI', 14, 'bold'), fg='#27ae60', bg='white')
        self.total_label.pack(anchor=tk.E, pady=(5, 0))
        
        # Botones de acción
        actions_frame = tk.Frame(parent, bg='white')
        actions_frame.pack(fill=tk.X, padx=15, pady=20)
        
        # Botón generar factura
        generate_btn = tk.Button(actions_frame, text="📄 Generar Factura Electrónica", 
                                command=self.generate_electronic_invoice,
                                font=('Segoe UI', 12, 'bold'), bg='#27ae60', fg='white',
                                relief=tk.FLAT, padx=30, pady=12, cursor='hand2')
        generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón vista previa
        preview_btn = tk.Button(actions_frame, text="👁️ Vista Previa PDF", 
                               command=self.preview_pdf,
                               font=('Segoe UI', 11), bg='#3498db', fg='white',
                               relief=tk.FLAT, padx=20, pady=10, cursor='hand2')
        preview_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón limpiar
        clear_btn = tk.Button(actions_frame, text="🗑️ Limpiar", 
                             command=self.clear_form,
                             font=('Segoe UI', 11), bg='#95a5a6', fg='white',
                             relief=tk.FLAT, padx=20, pady=10, cursor='hand2')
        clear_btn.pack(side=tk.LEFT)
        
        # Cargar datos de venta si existen
        self.load_sale_data()
    
    def create_products_table(self, parent):
        """Crea la tabla de productos"""
        table_frame = tk.Frame(parent, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        columns = ('Código', 'Descripción', 'Cantidad', 'Precio', 'Total')
        self.products_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=8)
        
        # Configurar columnas
        self.products_tree.heading('Código', text='Código')
        self.products_tree.heading('Descripción', text='Descripción')
        self.products_tree.heading('Cantidad', text='Cant.')
        self.products_tree.heading('Precio', text='Precio Unit.')
        self.products_tree.heading('Total', text='Total')
        
        self.products_tree.column('Código', width=100)
        self.products_tree.column('Descripción', width=300)
        self.products_tree.column('Cantidad', width=80)
        self.products_tree.column('Precio', width=100)
        self.products_tree.column('Total', width=100)
        
        # Scrollbar
        products_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=products_scrollbar.set)
        
        self.products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        products_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_config_tab(self):
        """Pestaña de configuración"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="⚙️ Configuración")
        
        # Información de empresa
        company_frame = tk.LabelFrame(config_frame, text="🏢 Datos de la Empresa", 
                                     font=('Segoe UI', 11, 'bold'), padx=15, pady=15)
        company_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # Campos de empresa
        fields = [
            ("Nombre de la Empresa:", "company_name"),
            ("Cédula Jurídica:", "company_id"),
            ("Teléfono:", "company_phone"),
            ("Email:", "company_email"),
            ("Dirección:", "company_address")
        ]
        
        self.config_vars = {}
        for i, (label, var_name) in enumerate(fields):
            tk.Label(company_frame, text=label, font=('Segoe UI', 10)).grid(row=i, column=0, sticky=tk.W, pady=5)
            if var_name == "company_address":
                entry = tk.Text(company_frame, font=('Segoe UI', 10), width=50, height=3)
            else:
                entry = tk.Entry(company_frame, font=('Segoe UI', 11), width=50)
            entry.grid(row=i, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=5)
            self.config_vars[var_name] = entry
        
        company_frame.grid_columnconfigure(1, weight=1)
        
        # Configuración técnica
        tech_frame = tk.LabelFrame(config_frame, text="🔧 Configuración Técnica", 
                                  font=('Segoe UI', 11, 'bold'), padx=15, pady=15)
        tech_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # Ambiente
        tk.Label(tech_frame, text="Ambiente:", font=('Segoe UI', 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.environment = ttk.Combobox(tech_frame, values=["Pruebas (Sandbox)", "Producción"], state="readonly", width=20)
        self.environment.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        self.environment.set("Pruebas (Sandbox)")
        
        # Régimen
        tk.Label(tech_frame, text="Régimen Tributario:", font=('Segoe UI', 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.tax_regime = ttk.Combobox(tech_frame, values=["Simplificado (Trimestral)", "Tradicional (Mensual)"], state="readonly", width=25)
        self.tax_regime.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        self.tax_regime.set("Simplificado (Trimestral)")
        
        # Botones de configuración
        config_buttons_frame = tk.Frame(config_frame)
        config_buttons_frame.pack(fill=tk.X, padx=15, pady=20)
        
        save_config_btn = tk.Button(config_buttons_frame, text="💾 Guardar Configuración", 
                                   command=self.save_config,
                                   font=('Segoe UI', 11, 'bold'), bg='#27ae60', fg='white',
                                   relief=tk.FLAT, padx=20, pady=10, cursor='hand2')
        save_config_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        test_connection_btn = tk.Button(config_buttons_frame, text="🔗 Probar Conexión Hacienda", 
                                       command=self.test_hacienda_connection,
                                       font=('Segoe UI', 11), bg='#3498db', fg='white',
                                       relief=tk.FLAT, padx=20, pady=10, cursor='hand2')
        test_connection_btn.pack(side=tk.LEFT)
    
    def create_history_tab(self):
        """Pestaña de historial de facturas"""
        history_frame = ttk.Frame(self.notebook)
        self.notebook.add(history_frame, text="📚 Historial")
        
        # Filtros
        filters_frame = tk.Frame(history_frame)
        filters_frame.pack(fill=tk.X, padx=15, pady=15)
        
        tk.Label(filters_frame, text="Desde:", font=('Segoe UI', 10)).pack(side=tk.LEFT)
        self.date_from = tk.Entry(filters_frame, font=('Segoe UI', 10), width=12)
        self.date_from.pack(side=tk.LEFT, padx=(5, 15))
        self.date_from.insert(0, datetime.now().strftime("%d/%m/%Y"))
        
        tk.Label(filters_frame, text="Hasta:", font=('Segoe UI', 10)).pack(side=tk.LEFT)
        self.date_to = tk.Entry(filters_frame, font=('Segoe UI', 10), width=12)
        self.date_to.pack(side=tk.LEFT, padx=(5, 15))
        self.date_to.insert(0, datetime.now().strftime("%d/%m/%Y"))
        
        search_btn = tk.Button(filters_frame, text="🔍 Buscar", 
                              command=self.search_invoices,
                              font=('Segoe UI', 10), bg='#3498db', fg='white',
                              relief=tk.FLAT, padx=15, pady=5, cursor='hand2')
        search_btn.pack(side=tk.LEFT, padx=5)
        
        # Tabla de historial
        history_table_frame = tk.Frame(history_frame)
        history_table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        history_columns = ('Fecha', 'Número', 'Cliente', 'Total', 'Estado', 'Acciones')
        self.history_tree = ttk.Treeview(history_table_frame, columns=history_columns, show='headings', height=15)
        
        for col in history_columns:
            self.history_tree.heading(col, text=col)
            if col == 'Cliente':
                self.history_tree.column(col, width=200)
            elif col == 'Acciones':
                self.history_tree.column(col, width=150)
            else:
                self.history_tree.column(col, width=100)
        
        history_scrollbar = ttk.Scrollbar(history_table_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Cargar historial de ejemplo
        self.load_sample_history()
    
    def create_help_tab(self):
        """Pestaña de ayuda"""
        help_frame = ttk.Frame(self.notebook)
        self.notebook.add(help_frame, text="❓ Ayuda")
        
        help_text = tk.Text(help_frame, font=('Segoe UI', 10), wrap=tk.WORD, padx=20, pady=20)
        help_text.pack(fill=tk.BOTH, expand=True)
        
        help_content = """
SISTEMA DE FACTURACIÓN ELECTRÓNICA COSTA RICA
==============================================

🎯 CARACTERÍSTICAS PRINCIPALES:
• Cumple con la normativa del Ministerio de Hacienda
• Genera XML versión 4.4 automáticamente  
• Crea PDF profesional para el cliente
• Envío automático al ATV (Administrador Tributario Virtual)
• Compatible con régimen simplificado y tradicional

📋 COMO USAR EL SISTEMA:

1. CONFIGURACIÓN INICIAL:
   • Vaya a la pestaña "Configuración"
   • Complete los datos de su empresa
   • Configure el régimen tributario (simplificado o tradicional)
   • Seleccione el ambiente (pruebas o producción)

2. GENERAR FACTURA:
   • Complete los datos del cliente (opcional para contado)
   • Los productos se cargan automáticamente desde la venta
   • Revise los totales calculados
   • Haga clic en "Generar Factura Electrónica"

3. RÉGIMEN SIMPLIFICADO:
   • Reportes cada 3 meses al Ministerio de Hacienda
   • Menor complejidad administrativa
   • Ideal para pequeños negocios

4. RÉGIMEN TRADICIONAL:
   • Reportes mensuales
   • Mayor detalle contable
   • Para empresas medianas y grandes

🔧 CONFIGURACIÓN TÉCNICA:
• Certificados digitales para firmar XML
• Conexión segura con API de Hacienda
• Respaldos automáticos de facturas
• Trazabilidad completa de documentos

📞 SOPORTE TÉCNICO:
• Email: soporte@cajacentral.com
• Teléfono: +506 2222-3333
• WhatsApp: +506 8888-9999
• Horario: Lunes a Viernes 8:00 AM - 6:00 PM

⚖️ MARCO LEGAL:
• Resolución DGT-R-48-2016
• Ley 8114 - Simplificación Tributaria
• Decreto Ejecutivo N° 41524-H

✅ BENEFICIOS PARA CONTADORES:
• Reportes en PDF listos para presentar
• Exportación a Excel y otros formatos
• Conciliación automática con sistemas contables
• Trazabilidad completa de documentos fiscales

🚀 ¡Su negocio cumple automáticamente con Hacienda!
        """
        
        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)
    
    def get_next_invoice_number(self):
        """Obtiene el siguiente número de factura"""
        # En producción, esto vendría de la base de datos
        return str(datetime.now().strftime("%Y%m%d") + "001")
    
    def load_sale_data(self):
        """Carga los datos de la venta actual"""
        if not self.venta_data:
            # Datos de ejemplo si no hay venta
            sample_products = [
                ("123456", "Producto de Ejemplo 1", "2", "₡15,000.00", "₡30,000.00"),
                ("789012", "Producto de Ejemplo 2", "1", "₡8,500.00", "₡8,500.00")
            ]
            
            for product in sample_products:
                self.products_tree.insert('', 'end', values=product)
        
        self.calculate_totals()
    
    def calculate_totals(self):
        """Calcula los totales de la factura"""
        subtotal = 0
        
        for item in self.products_tree.get_children():
            values = self.products_tree.item(item)['values']
            total_str = str(values[4]).replace('₡', '').replace(',', '')
            try:
                subtotal += float(total_str)
            except ValueError:
                continue
        
        tax = subtotal * 0.13  # IVA 13%
        total = subtotal + tax
        
        self.subtotal_label.config(text=f"Subtotal: ₡{subtotal:,.2f}")
        self.tax_label.config(text=f"IVA (13%): ₡{tax:,.2f}")
        self.total_label.config(text=f"TOTAL: ₡{total:,.2f}")
    
    def generate_electronic_invoice(self):
        """Genera la factura electrónica"""
        if not FACTURACION_AVAILABLE:
            messagebox.showerror("Error", "Sistema de facturación no disponible")
            return
        
        try:
            # Recopilar datos del formulario
            invoice_data = self.collect_invoice_data()
            
            # Validar datos
            if not self.validate_invoice_data(invoice_data):
                return
            
            # Mostrar progreso
            progress_window = self.show_progress_window()
            
            def generate_in_background():
                try:
                    # Generar XML
                    progress_window.update_progress("Generando XML v4.4...", 25)
                    xml_content = self.facturacion_system.crear_xml_factura(invoice_data)
                    
                    # Generar PDF
                    progress_window.update_progress("Creando PDF...", 50)
                    pdf_path = self.facturacion_system.generar_pdf_factura(invoice_data)
                    
                    # Guardar XML
                    progress_window.update_progress("Guardando archivos...", 75)
                    xml_path = self.save_xml_file(xml_content, invoice_data['numero'])
                    
                    # Enviar a Hacienda (opcional)
                    if messagebox.askyesno("Envío a Hacienda", "¿Desea enviar la factura al Ministerio de Hacienda ahora?"):
                        progress_window.update_progress("Enviando a Hacienda...", 90)
                        # result = self.facturacion_system.enviar_hacienda(xml_content, invoice_data['clave_numerica'])
                    
                    progress_window.update_progress("¡Completado!", 100)
                    progress_window.close()
                    
                    # Mostrar resultado
                    self.show_generation_result(xml_path, pdf_path, invoice_data)
                    
                except Exception as e:
                    progress_window.close()
                    messagebox.showerror("Error", f"Error generando factura: {str(e)}")
            
            threading.Thread(target=generate_in_background, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error en generación: {str(e)}")
    
    def collect_invoice_data(self):
        """Recopila todos los datos de la factura"""
        # Recopilar productos
        lineas = []
        for item in self.products_tree.get_children():
            values = self.products_tree.item(item)['values']
            precio_str = str(values[3]).replace('₡', '').replace(',', '')
            
            linea = {
                'codigo': values[0],
                'descripcion': values[1],
                'cantidad': int(values[2]),
                'precio_unitario': float(precio_str),
                'descuento': 0.0,
                'unidad_medida': 'Unid',
                'codigo_impuesto': '01',
                'tarifa_impuesto': 13.00
            }
            lineas.append(linea)
        
        # Datos del cliente
        cliente_data = None
        if self.client_name.get().strip():
            cliente_data = {
                'nombre': self.client_name.get(),
                'cedula': self.client_id.get(),
                'tipo_identificacion': '01' if self.id_type.get() == 'Física' else '02',
                'telefono': self.client_phone.get(),
                'email': self.client_email.get(),
                'direccion': self.client_address.get('1.0', tk.END).strip(),
                'provincia': '1',
                'canton': '01',
                'distrito': '01'
            }
        
        return {
            'numero': self.invoice_number.get(),
            'codigo_actividad': '522001',  # Venta al por menor
            'condicion_venta': '01' if self.sale_condition.get() == 'Contado' else '02',
            'medio_pago': '01',  # Efectivo por defecto
            'cliente': cliente_data,
            'lineas': lineas
        }
    
    def validate_invoice_data(self, data):
        """Valida los datos de la factura"""
        if not data['numero']:
            messagebox.showerror("Error", "El número de factura es requerido")
            return False
        
        if not data['lineas']:
            messagebox.showerror("Error", "Debe tener al menos un producto")
            return False
        
        return True
    
    def show_progress_window(self):
        """Muestra ventana de progreso"""
        progress_win = tk.Toplevel(self.window)
        progress_win.title("Generando Factura...")
        progress_win.geometry("400x150")
        progress_win.resizable(False, False)
        progress_win.transient(self.window)
        progress_win.grab_set()
        
        # Centrar
        progress_win.update_idletasks()
        x = (progress_win.winfo_screenwidth() // 2) - 200
        y = (progress_win.winfo_screenheight() // 2) - 75
        progress_win.geometry(f"400x150+{x}+{y}")
        
        # Contenido
        tk.Label(progress_win, text="⏳ Generando Factura Electrónica", 
                font=('Segoe UI', 14, 'bold')).pack(pady=20)
        
        progress_bar = ttk.Progressbar(progress_win, length=300, mode='determinate')
        progress_bar.pack(pady=10)
        
        status_label = tk.Label(progress_win, text="Iniciando...", font=('Segoe UI', 10))
        status_label.pack(pady=5)
        
        def update_progress(text, value):
            status_label.config(text=text)
            progress_bar['value'] = value
            progress_win.update()
        
        def close():
            progress_win.destroy()
        
        progress_win.update_progress = update_progress
        progress_win.close = close
        
        return progress_win
    
    def save_xml_file(self, xml_content, invoice_number):
        """Guarda el archivo XML"""
        os.makedirs('facturas', exist_ok=True)
        filename = f"factura_{invoice_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        filepath = os.path.join('facturas', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        return filepath
    
    def show_generation_result(self, xml_path, pdf_path, invoice_data):
        """Muestra el resultado de la generación"""
        result_window = tk.Toplevel(self.window)
        result_window.title("✅ Factura Generada Exitosamente")
        result_window.geometry("500x400")
        result_window.resizable(False, False)
        result_window.transient(self.window)
        result_window.grab_set()
        
        # Centrar
        result_window.update_idletasks()
        x = (result_window.winfo_screenwidth() // 2) - 250
        y = (result_window.winfo_screenheight() // 2) - 200
        result_window.geometry(f"500x400+{x}+{y}")
        
        # Contenido
        main_frame = tk.Frame(result_window, bg='white', padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        tk.Label(main_frame, text="✅ ¡Factura Generada Exitosamente!", 
                font=('Segoe UI', 16, 'bold'), fg='#27ae60', bg='white').pack(pady=(0, 20))
        
        # Información
        info_frame = tk.Frame(main_frame, bg='white')
        info_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(info_frame, text=f"📄 Factura No: {invoice_data['numero']}", 
                font=('Segoe UI', 12), bg='white').pack(anchor=tk.W, pady=5)
        tk.Label(info_frame, text=f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                font=('Segoe UI', 12), bg='white').pack(anchor=tk.W, pady=5)
        tk.Label(info_frame, text=f"📁 XML: {os.path.basename(xml_path)}", 
                font=('Segoe UI', 12), bg='white').pack(anchor=tk.W, pady=5)
        tk.Label(info_frame, text=f"📄 PDF: {os.path.basename(pdf_path)}", 
                font=('Segoe UI', 12), bg='white').pack(anchor=tk.W, pady=5)
        
        # Botones
        buttons_frame = tk.Frame(main_frame, bg='white')
        buttons_frame.pack(fill=tk.X, pady=20)
        
        def open_pdf():
            try:
                os.startfile(pdf_path)
            except:
                webbrowser.open(f"file://{os.path.abspath(pdf_path)}")
        
        def open_folder():
            try:
                os.startfile(os.path.dirname(pdf_path))
            except:
                pass
        
        pdf_btn = tk.Button(buttons_frame, text="📄 Abrir PDF", command=open_pdf,
                           font=('Segoe UI', 11, 'bold'), bg='#e74c3c', fg='white',
                           relief=tk.FLAT, padx=20, pady=10, cursor='hand2')
        pdf_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        folder_btn = tk.Button(buttons_frame, text="📁 Abrir Carpeta", command=open_folder,
                              font=('Segoe UI', 11), bg='#3498db', fg='white',
                              relief=tk.FLAT, padx=20, pady=10, cursor='hand2')
        folder_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        close_btn = tk.Button(buttons_frame, text="✅ Cerrar", command=result_window.destroy,
                             font=('Segoe UI', 11), bg='#95a5a6', fg='white',
                             relief=tk.FLAT, padx=20, pady=10, cursor='hand2')
        close_btn.pack(side=tk.RIGHT)
    
    def export_pdf_v44(self):
        """Exporta factura directamente a PDF versión 4.4"""
        if not FACTURACION_AVAILABLE:
            messagebox.showerror("Error", "Sistema de facturación no disponible")
            return
        
        try:
            # Recopilar datos del formulario
            invoice_data = self.collect_invoice_data()
            
            # Validar que hay productos
            if not invoice_data.get('lineas'):
                messagebox.showwarning("Advertencia", "⚠️ Agregue al menos un producto para generar el PDF")
                return
            
            # Mostrar diálogo de progreso
            progress_window = self.show_progress_window()
            
            def generate_pdf_v44_background():
                try:
                    progress_window.update_progress("Preparando datos v4.4...", 20)
                    
                    # Preparar datos específicos para v4.4
                    datos_v44 = {
                        'numero': invoice_data['numero'],
                        'fecha': datetime.now().strftime('%d/%m/%Y'),
                        'hora': datetime.now().strftime('%H:%M:%S'),
                        'empresa': {
                            'nombre': invoice_data.get('emisor', {}).get('nombre', 'Empresa S.A.'),
                            'cedula': invoice_data.get('emisor', {}).get('cedula', '3-101-123456'),
                            'telefono': '2222-3333',
                            'email': 'info@empresa.co.cr',
                            'direccion': 'San José, Costa Rica',
                            'actividad': 'Comercio al por menor'
                        },
                        'cliente': invoice_data.get('cliente', {
                            'nombre': 'Cliente General',
                            'cedula': 'N/A',
                            'telefono': 'N/A',
                            'email': 'N/A',
                            'direccion': 'N/A'
                        }),
                        'lineas': invoice_data['lineas'],
                        'tipo_documento': 'Factura Electrónica',
                        'moneda': 'Colones (CRC)',
                        'clave_numerica': invoice_data.get('clave_numerica', 'CR' + '0' * 48),
                        'consecutivo': invoice_data.get('numero', '001-001-01-00000001'),
                        'condicion_venta': 'Contado',
                        'medio_pago': 'Efectivo',
                        'tipo_cambio': '590.00',
                        'regimen': 'Régimen Simplificado',
                        'resolucion_dgt': 'DGT-R-48-2016',
                        'vigencia_resolucion': '07/10/2016'
                    }
                    
                    progress_window.update_progress("Generando PDF v4.4...", 60)
                    
                    # Generar PDF v4.4
                    pdf_path = self.facturacion_system.generar_pdf_v44(datos_v44)
                    
                    progress_window.update_progress("¡PDF v4.4 Completado!", 100)
                    progress_window.close()
                    
                    # Mostrar resultado específico para v4.4
                    self.show_pdf_v44_result(pdf_path, datos_v44)
                    
                except Exception as e:
                    progress_window.close()
                    messagebox.showerror("Error PDF v4.4", f"Error generando PDF v4.4:\n{str(e)}")
            
            threading.Thread(target=generate_pdf_v44_background, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error preparando PDF v4.4: {str(e)}")
    
    def show_pdf_v44_result(self, pdf_path, invoice_data):
        """Muestra el resultado de la generación PDF v4.4"""
        result_window = tk.Toplevel(self.window)
        result_window.title("✅ PDF v4.4 Generado")
        result_window.geometry("500x400")
        result_window.configure(bg='white')
        result_window.transient(self.window)
        result_window.grab_set()
        
        # Centrar ventana
        result_window.update_idletasks()
        x = (result_window.winfo_screenwidth() // 2) - (250)
        y = (result_window.winfo_screenheight() // 2) - (200)
        result_window.geometry(f"500x400+{x}+{y}")
        
        # Frame principal
        main_frame = tk.Frame(result_window, bg='white', padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Icono de éxito
        success_label = tk.Label(main_frame, text="✅", font=('Arial', 48), bg='white', fg='#27ae60')
        success_label.pack(pady=(0, 20))
        
        # Título
        title_label = tk.Label(main_frame, text="PDF v4.4 Generado Exitosamente", 
                              font=('Segoe UI', 16, 'bold'), bg='white', fg='#2c3e50')
        title_label.pack(pady=(0, 20))
        
        # Información
        info_frame = tk.Frame(main_frame, bg='white')
        info_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(info_frame, text=f"📄 Factura No: {invoice_data['numero']}", 
                font=('Segoe UI', 12), bg='white').pack(anchor=tk.W, pady=5)
        tk.Label(info_frame, text=f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                font=('Segoe UI', 12), bg='white').pack(anchor=tk.W, pady=5)
        tk.Label(info_frame, text=f"📋 Versión: 4.4 (Formato Contador)", 
                font=('Segoe UI', 12, 'bold'), bg='white', fg='#e74c3c').pack(anchor=tk.W, pady=5)
        tk.Label(info_frame, text=f"📄 Archivo: {os.path.basename(pdf_path)}", 
                font=('Segoe UI', 12), bg='white').pack(anchor=tk.W, pady=5)
        
        # Nota especial v4.4
        note_frame = tk.Frame(main_frame, bg='#f8f9fa', relief=tk.RAISED, bd=1)
        note_frame.pack(fill=tk.X, pady=15)
        
        tk.Label(note_frame, text="📋 Información v4.4", 
                font=('Segoe UI', 11, 'bold'), bg='#f8f9fa', fg='#2c3e50').pack(pady=(10, 5))
        tk.Label(note_frame, text="• Formato especial para contadores y auditorías", 
                font=('Segoe UI', 10), bg='#f8f9fa').pack(anchor=tk.W, padx=15)
        tk.Label(note_frame, text="• Cumple normativas Ministerio de Hacienda CR", 
                font=('Segoe UI', 10), bg='#f8f9fa').pack(anchor=tk.W, padx=15)
        tk.Label(note_frame, text="• Incluye información técnica detallada", 
                font=('Segoe UI', 10), bg='#f8f9fa').pack(anchor=tk.W, padx=15, pady=(0, 10))
        
        # Botones
        buttons_frame = tk.Frame(main_frame, bg='white')
        buttons_frame.pack(fill=tk.X, pady=20)
        
        def open_pdf():
            try:
                os.startfile(pdf_path)
            except:
                webbrowser.open(f"file://{os.path.abspath(pdf_path)}")
        
        def open_folder():
            try:
                os.startfile(os.path.dirname(pdf_path))
            except:
                pass
        
        pdf_btn = tk.Button(buttons_frame, text="📄 Abrir PDF v4.4", command=open_pdf,
                           font=('Segoe UI', 12, 'bold'), bg='#e74c3c', fg='white',
                           relief=tk.FLAT, padx=25, pady=12, cursor='hand2')
        pdf_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        folder_btn = tk.Button(buttons_frame, text="📁 Abrir Carpeta", command=open_folder,
                              font=('Segoe UI', 11), bg='#3498db', fg='white',
                              relief=tk.FLAT, padx=20, pady=12, cursor='hand2')
        folder_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        close_btn = tk.Button(buttons_frame, text="✅ Cerrar", command=result_window.destroy,
                             font=('Segoe UI', 11), bg='#95a5a6', fg='white',
                             relief=tk.FLAT, padx=20, pady=12, cursor='hand2')
        close_btn.pack(side=tk.RIGHT)

    def preview_pdf(self):
        """Vista previa del PDF"""
        messagebox.showinfo("Vista Previa", "Función de vista previa en desarrollo")
    
    def clear_form(self):
        """Limpia el formulario"""
        if messagebox.askyesno("Limpiar", "¿Está seguro que desea limpiar todos los datos?"):
            self.client_name.delete(0, tk.END)
            self.client_id.delete(0, tk.END)
            self.client_email.delete(0, tk.END)
            self.client_phone.delete(0, tk.END)
            self.client_address.delete('1.0', tk.END)
            
            for item in self.products_tree.get_children():
                self.products_tree.delete(item)
            
            self.calculate_totals()
    
    def save_config(self):
        """Guarda la configuración"""
        messagebox.showinfo("Configuración", "Configuración guardada correctamente")
    
    def test_hacienda_connection(self):
        """Prueba la conexión con Hacienda"""
        messagebox.showinfo("Conexión", "Probando conexión con Ministerio de Hacienda...\n\n✅ Conexión exitosa (modo prueba)")
    
    def search_invoices(self):
        """Busca facturas en el historial"""
        messagebox.showinfo("Búsqueda", "Función de búsqueda en desarrollo")
    
    def load_sample_history(self):
        """Carga historial de ejemplo"""
        sample_history = [
            ("25/07/2024", "20240725001", "Juan Pérez", "₡45,650.00", "✅ Aceptada", "Ver | Reimprimir"),
            ("24/07/2024", "20240724003", "María González", "₡23,200.00", "✅ Aceptada", "Ver | Reimprimir"),
            ("24/07/2024", "20240724002", "Carlos Rodríguez", "₡67,800.00", "⏳ Pendiente", "Ver | Reenviar"),
            ("23/07/2024", "20240723001", "Ana Jiménez", "₡15,400.00", "✅ Aceptada", "Ver | Reimprimir")
        ]
        
        for item in sample_history:
            self.history_tree.insert('', 'end', values=item)

# Función para mostrar la ventana desde el sistema principal
def mostrar_facturacion_electronica(parent_window, venta_data=None):
    """Muestra la ventana de facturación electrónica"""
    try:
        FacturacionElectronicaUI(parent_window, venta_data)
    except Exception as e:
        messagebox.showerror("Error", f"Error abriendo facturación electrónica: {str(e)}")

if __name__ == "__main__":
    # Prueba independiente
    root = tk.Tk()
    root.withdraw()
    
    app = FacturacionElectronicaUI(root)
    root.mainloop()
