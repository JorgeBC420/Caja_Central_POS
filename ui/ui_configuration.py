"""
Ventana de Configuración del Sistema POS
Configuraciones generales, impresoras, base de datos, etc.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from PIL import Image, ImageTk

class ConfigurationWindow:
    """Ventana principal de configuración"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.config_data = self.load_config()
        self.logo_photo = None  # Inicializar logo_photo
        
        # Crear ventana
        self.window = tk.Toplevel() if parent else tk.Tk()
        self.window.title("Configuración del Sistema - CajaCentral POS")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        
        # Configurar estilo
        self.setup_styles()
        
        # Cargar logo si está disponible
        self.load_logo()
        
        # Crear interfaz
        self.create_interface()
        
        # Centrar ventana
        self.center_window()
    
    def setup_styles(self):
        """Configura estilos para la ventana"""
        self.window.configure(bg='#f8f9fa')
        
        style = ttk.Style()
        style.configure('Config.TFrame', background='#f8f9fa')
        style.configure('ConfigHeader.TLabel', 
                       font=('Segoe UI', 16, 'bold'),
                       background='#f8f9fa',
                       foreground='#2c3e50')
        style.configure('ConfigSection.TLabel',
                       font=('Segoe UI', 12, 'bold'),
                       background='white',
                       foreground='#1a1a1a')  # Texto más oscuro y legible
    
    def load_logo(self):
        """Carga el logo si está disponible"""
        try:
            from core.brand_manager import get_brand_manager
            brand_manager = get_brand_manager()
            logo = brand_manager.get_logo("small")
            if logo:
                self.logo_photo = ImageTk.PhotoImage(logo)
            else:
                self.logo_photo = None
        except:
            self.logo_photo = None
    
    def create_interface(self):
        """Crea la interfaz principal"""
        # Header con logo
        header_frame = tk.Frame(self.window, bg='#3498db', height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # Logo y título
        title_frame = tk.Frame(header_frame, bg='#3498db')
        title_frame.pack(expand=True, fill='both')
        
        if self.logo_photo:
            logo_label = tk.Label(title_frame, image=self.logo_photo, bg='#3498db')
            logo_label.pack(side='left', padx=20, pady=10)
        
        title_label = tk.Label(
            title_frame,
            text="Configuración del Sistema",
            font=('Segoe UI', 18, 'bold'),
            fg='white',
            bg='#3498db'
        )
        title_label.pack(pady=20)
        
        # Notebook para pestañas
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Pestañas
        self.create_general_tab(notebook)
        self.create_printer_tab(notebook)
        self.create_database_tab(notebook)
        self.create_appearance_tab(notebook)
        self.create_backup_tab(notebook)
        
        # Botones de acción
        self.create_action_buttons()
    
    def create_general_tab(self, notebook):
        """Crea la pestaña de configuración general"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="⚙️ General")
        
        # Información de la empresa
        company_frame = tk.LabelFrame(frame, text="Información de la Empresa", 
                                     font=('Segoe UI', 10, 'bold'), bg='white')
        company_frame.pack(fill='x', padx=10, pady=10)
        
        # Campos de empresa
        tk.Label(company_frame, text="Nombre de la Empresa:", bg='white', 
                font=('Segoe UI', 10, 'bold'), fg='#2c3e50').grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.company_name = tk.Entry(company_frame, width=40, font=('Segoe UI', 11), 
                                   bg='white', fg='#2c3e50', relief='solid', bd=1)
        self.company_name.grid(row=0, column=1, padx=10, pady=5)
        self.company_name.insert(0, self.config_data.get('company_name', 'CajaCentral POS'))
        
        tk.Label(company_frame, text="RUC/NIT:", bg='white', 
                font=('Segoe UI', 10, 'bold'), fg='#2c3e50').grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.company_ruc = tk.Entry(company_frame, width=40, font=('Segoe UI', 11), 
                                  bg='white', fg='#2c3e50', relief='solid', bd=1)
        self.company_ruc.grid(row=1, column=1, padx=10, pady=5)
        self.company_ruc.insert(0, self.config_data.get('company_ruc', ''))
        
        tk.Label(company_frame, text="Dirección:", bg='white', 
                font=('Segoe UI', 10, 'bold'), fg='#2c3e50').grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.company_address = tk.Entry(company_frame, width=40, font=('Segoe UI', 11), 
                                      bg='white', fg='#2c3e50', relief='solid', bd=1)
        self.company_address.grid(row=2, column=1, padx=10, pady=5)
        self.company_address.insert(0, self.config_data.get('company_address', ''))
        
        tk.Label(company_frame, text="Teléfono:", bg='white', 
                font=('Segoe UI', 10, 'bold'), fg='#2c3e50').grid(row=3, column=0, sticky='w', padx=10, pady=5)
        self.company_phone = tk.Entry(company_frame, width=40, font=('Segoe UI', 11), 
                                    bg='white', fg='#2c3e50', relief='solid', bd=1)
        self.company_phone.grid(row=3, column=1, padx=10, pady=5)
        self.company_phone.insert(0, self.config_data.get('company_phone', ''))
        
        # Configuraciones del sistema
        system_frame = tk.LabelFrame(frame, text="Configuraciones del Sistema", 
                                   font=('Segoe UI', 10, 'bold'), bg='white')
        system_frame.pack(fill='x', padx=10, pady=10)
        
        # Moneda
        tk.Label(system_frame, text="Moneda:", bg='white').grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.currency = ttk.Combobox(system_frame, values=['CRC', 'USD', 'EUR'], width=37)
        self.currency.grid(row=0, column=1, padx=10, pady=5)
        self.currency.set(self.config_data.get('currency', 'CRC'))
        
        # IVA
        tk.Label(system_frame, text="IVA (%):", bg='white').grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.tax_rate = tk.Entry(system_frame, width=40, font=('Segoe UI', 10))
        self.tax_rate.grid(row=1, column=1, padx=10, pady=5)
        self.tax_rate.insert(0, self.config_data.get('tax_rate', '13'))
        
        # Opciones
        options_frame = tk.Frame(system_frame, bg='white')
        options_frame.grid(row=2, column=0, columnspan=2, sticky='w', padx=10, pady=10)
        
        self.auto_print = tk.BooleanVar(value=self.config_data.get('auto_print', True))
        tk.Checkbutton(options_frame, text="Imprimir automáticamente tickets", 
                      variable=self.auto_print, bg='white').pack(anchor='w')
        
        self.confirm_delete = tk.BooleanVar(value=self.config_data.get('confirm_delete', True))
        tk.Checkbutton(options_frame, text="Confirmar antes de eliminar", 
                      variable=self.confirm_delete, bg='white').pack(anchor='w')
        
        self.show_welcome = tk.BooleanVar(value=self.config_data.get('show_welcome', True))
        tk.Checkbutton(options_frame, text="Mostrar mensaje de bienvenida", 
                      variable=self.show_welcome, bg='white').pack(anchor='w')
    
    def create_printer_tab(self, notebook):
        """Crea la pestaña de configuración de impresoras"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🖨️ Impresoras")
        
        printer_frame = tk.LabelFrame(frame, text="Configuración de Impresoras", 
                                    font=('Segoe UI', 10, 'bold'), bg='white')
        printer_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Lista de impresoras
        tk.Label(printer_frame, text="Impresora para Tickets:", bg='white').grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.ticket_printer = ttk.Combobox(printer_frame, width=37)
        self.ticket_printer.grid(row=0, column=1, padx=10, pady=5)
        
        # Botón para detectar impresoras
        detect_btn = tk.Button(printer_frame, text="Detectar Impresoras", 
                             command=self.detect_printers, bg='#3498db', fg='white')
        detect_btn.grid(row=0, column=2, padx=10, pady=5)
        
        # Configuraciones de tickets
        tk.Label(printer_frame, text="Ancho del Papel (chars):", bg='white').grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.paper_width = tk.Entry(printer_frame, width=40, font=('Segoe UI', 10))
        self.paper_width.grid(row=1, column=1, padx=10, pady=5)
        self.paper_width.insert(0, self.config_data.get('paper_width', '40'))
        
        # Opciones de impresión
        print_options_frame = tk.Frame(printer_frame, bg='white')
        print_options_frame.grid(row=2, column=0, columnspan=3, sticky='w', padx=10, pady=10)
        
        self.print_logo = tk.BooleanVar(value=self.config_data.get('print_logo', True))
        tk.Checkbutton(print_options_frame, text="Imprimir logo en tickets", 
                      variable=self.print_logo, bg='white').pack(anchor='w')
        
        self.print_footer = tk.BooleanVar(value=self.config_data.get('print_footer', True))
        tk.Checkbutton(print_options_frame, text="Imprimir pie de página personalizado", 
                      variable=self.print_footer, bg='white').pack(anchor='w')
        
        # Pie de página personalizado
        tk.Label(printer_frame, text="Pie de Página:", bg='white').grid(row=3, column=0, sticky='nw', padx=10, pady=5)
        self.footer_text = tk.Text(printer_frame, width=30, height=3, font=('Segoe UI', 9))
        self.footer_text.grid(row=3, column=1, padx=10, pady=5)
        self.footer_text.insert('1.0', self.config_data.get('footer_text', '¡Gracias por su compra!\\nVuelva pronto'))
        
        # Botón de prueba
        test_btn = tk.Button(printer_frame, text="Imprimir Prueba", 
                           command=self.test_print, bg='#27ae60', fg='white')
        test_btn.grid(row=4, column=1, padx=10, pady=10)
    
    def create_database_tab(self, notebook):
        """Crea la pestaña de configuración de base de datos"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🗄️ Base de Datos")
        
        db_frame = tk.LabelFrame(frame, text="Configuración de Base de Datos", 
                               font=('Segoe UI', 10, 'bold'), bg='white')
        db_frame.pack(fill='x', padx=10, pady=10)
        
        # Información de la BD
        tk.Label(db_frame, text="Tipo de Base de Datos:", bg='white').grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.db_type = ttk.Combobox(db_frame, values=['SQLite', 'MySQL', 'PostgreSQL'], width=37)
        self.db_type.grid(row=0, column=1, padx=10, pady=5)
        self.db_type.set(self.config_data.get('db_type', 'SQLite'))
        
        tk.Label(db_frame, text="Archivo/Host:", bg='white').grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.db_path = tk.Entry(db_frame, width=40, font=('Segoe UI', 10))
        self.db_path.grid(row=1, column=1, padx=10, pady=5)
        self.db_path.insert(0, self.config_data.get('db_path', 'caja_registradora_pos_cr.db'))
        
        # Botón para seleccionar archivo
        browse_btn = tk.Button(db_frame, text="...", command=self.browse_database, width=3)
        browse_btn.grid(row=1, column=2, padx=5, pady=5)
        
        # Estado de la conexión
        status_frame = tk.Frame(db_frame, bg='white')
        status_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        # Botones de acción
        action_frame = tk.Frame(db_frame, bg='white')
        action_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        tk.Button(action_frame, text="Probar Conexión", command=self.test_database, 
                 bg='#3498db', fg='white').pack(side='left', padx=5)
        tk.Button(action_frame, text="Crear Backup", command=self.create_backup, 
                 bg='#f39c12', fg='white').pack(side='left', padx=5)
        tk.Button(action_frame, text="Restaurar Backup", command=self.restore_backup, 
                 bg='#e74c3c', fg='white').pack(side='left', padx=5)
    
    def create_appearance_tab(self, notebook):
        """Crea la pestaña de apariencia"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🎨 Apariencia")
        
        theme_frame = tk.LabelFrame(frame, text="Tema y Colores", 
                                  font=('Segoe UI', 10, 'bold'), bg='white')
        theme_frame.pack(fill='x', padx=10, pady=10)
        
        # Tema
        tk.Label(theme_frame, text="Tema:", bg='white').grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.theme = ttk.Combobox(theme_frame, values=['Moderno', 'Clásico', 'Oscuro'], width=37)
        self.theme.grid(row=0, column=1, padx=10, pady=5)
        self.theme.set(self.config_data.get('theme', 'Moderno'))
        
        # Colores
        tk.Label(theme_frame, text="Color Principal:", bg='white').grid(row=1, column=0, sticky='w', padx=10, pady=5)
        color_frame = tk.Frame(theme_frame, bg='white')
        color_frame.grid(row=1, column=1, sticky='w', padx=10, pady=5)
        
        self.primary_color = tk.Entry(color_frame, width=30, font=('Segoe UI', 10))
        self.primary_color.pack(side='left')
        self.primary_color.insert(0, self.config_data.get('primary_color', '#3498db'))
        
        color_btn = tk.Button(color_frame, text="🎨", command=self.choose_color, width=3)
        color_btn.pack(side='left', padx=5)
        
        # Logo personalizado
        logo_frame = tk.LabelFrame(frame, text="Logo Personalizado", 
                                 font=('Segoe UI', 10, 'bold'), bg='white')
        logo_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(logo_frame, text="Logo Actual:", bg='white').grid(row=0, column=0, sticky='w', padx=10, pady=5)
        
        # Mostrar logo actual si existe
        if self.logo_photo:
            logo_display = tk.Label(logo_frame, image=self.logo_photo, bg='white')
            logo_display.grid(row=0, column=1, padx=10, pady=5)
        else:
            tk.Label(logo_frame, text="Sin logo configurado", bg='white', fg='gray').grid(row=0, column=1, padx=10, pady=5)
        
        tk.Button(logo_frame, text="Cambiar Logo", command=self.change_logo, 
                 bg='#9b59b6', fg='white').grid(row=1, column=1, padx=10, pady=5)
    
    def create_backup_tab(self, notebook):
        """Crea la pestaña de respaldos"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="💾 Respaldos")
        
        backup_frame = tk.LabelFrame(frame, text="Gestión de Respaldos", 
                                   font=('Segoe UI', 10, 'bold'), bg='white')
        backup_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Configuración automática
        auto_frame = tk.Frame(backup_frame, bg='white')
        auto_frame.pack(fill='x', padx=10, pady=10)
        
        self.auto_backup = tk.BooleanVar(value=self.config_data.get('auto_backup', False))
        tk.Checkbutton(auto_frame, text="Respaldo automático diario", 
                      variable=self.auto_backup, bg='white').pack(anchor='w')
        
        tk.Label(auto_frame, text="Carpeta de respaldos:", bg='white').pack(anchor='w', pady=(10, 5))
        backup_path_frame = tk.Frame(auto_frame, bg='white')
        backup_path_frame.pack(fill='x')
        
        self.backup_path = tk.Entry(backup_path_frame, font=('Segoe UI', 10))
        self.backup_path.pack(side='left', fill='x', expand=True)
        self.backup_path.insert(0, self.config_data.get('backup_path', './backups'))
        
        tk.Button(backup_path_frame, text="...", command=self.browse_backup_folder, width=3).pack(side='right')
        
        # Acciones manuales
        manual_frame = tk.Frame(backup_frame, bg='white')
        manual_frame.pack(fill='x', padx=10, pady=20)
        
        tk.Button(manual_frame, text="Crear Respaldo Ahora", command=self.manual_backup, 
                 bg='#27ae60', fg='white', width=20).pack(side='left', padx=5)
        tk.Button(manual_frame, text="Restaurar desde Archivo", command=self.restore_from_file, 
                 bg='#e67e22', fg='white', width=20).pack(side='left', padx=5)
        
        # Lista de respaldos existentes
        list_frame = tk.LabelFrame(backup_frame, text="Respaldos Existentes", bg='white')
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Crear lista con scrollbar
        listbox_frame = tk.Frame(list_frame, bg='white')
        listbox_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.backup_listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set)
        self.backup_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.backup_listbox.yview)
        
        # Cargar lista de respaldos
        self.refresh_backup_list()
    
    def create_action_buttons(self):
        """Crea los botones de acción principales"""
        button_frame = tk.Frame(self.window, bg='#f8f9fa')
        button_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Button(button_frame, text="💾 Guardar Configuración", 
                 command=self.save_config, bg='#27ae60', fg='white', 
                 font=('Segoe UI', 10, 'bold'), width=20).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="🔄 Restablecer", 
                 command=self.reset_config, bg='#f39c12', fg='white', 
                 font=('Segoe UI', 10), width=15).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="❌ Cancelar", 
                 command=self.window.destroy, bg='#e74c3c', fg='white', 
                 font=('Segoe UI', 10), width=15).pack(side='right', padx=5)
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def load_config(self):
        """Carga la configuración desde archivo"""
        config_file = "config/app.ini"
        json_config_file = "config/app_config.json"
        
        default_config = {
            'company_name': 'CajaCentral POS',
            'company_ruc': '',
            'company_address': '',
            'company_phone': '',
            'currency': 'CRC',
            'tax_rate': '13',
            'auto_print': True,
            'confirm_delete': True,
            'show_welcome': True,
            'ticket_printer': '',
            'paper_width': '40',
            'print_logo': True,
            'print_footer': True,
            'footer_text': '¡Gracias por su compra!\\nVuelva pronto',
            'db_type': 'SQLite',
            'db_path': 'caja_registradora_pos_cr.db',
            'theme': 'Moderno',
            'primary_color': '#3498db',
            'auto_backup': False,
            'backup_path': './backups'
        }
        
        try:
            # Intentar cargar archivo JSON primero
            if os.path.exists(json_config_file):
                with open(json_config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                # Combinar con defaults para campos faltantes
                for key, value in default_config.items():
                    if key not in config_data:
                        config_data[key] = value
                return config_data
            else:
                return default_config
        except Exception as e:
            print(f"Error cargando configuración: {e}")
            return default_config
    
    def save_config(self):
        """Guarda la configuración"""
        try:
            config_data = {
                'company_name': self.company_name.get(),
                'company_ruc': self.company_ruc.get(),
                'company_address': self.company_address.get(),
                'company_phone': self.company_phone.get(),
                'currency': self.currency.get(),
                'tax_rate': self.tax_rate.get(),
                'auto_print': self.auto_print.get(),
                'confirm_delete': self.confirm_delete.get(),
                'show_welcome': self.show_welcome.get(),
                'ticket_printer': self.ticket_printer.get(),
                'paper_width': self.paper_width.get(),
                'print_logo': self.print_logo.get(),
                'print_footer': self.print_footer.get(),
                'footer_text': self.footer_text.get('1.0', 'end-1c'),
                'db_type': self.db_type.get(),
                'db_path': self.db_path.get(),
                'theme': self.theme.get(),
                'primary_color': self.primary_color.get(),
                'auto_backup': self.auto_backup.get(),
                'backup_path': self.backup_path.get()
            }
            
            # Crear directorio config si no existe
            os.makedirs('config', exist_ok=True)
            
            # Guardar configuración en formato JSON
            with open('config/app_config.json', 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Éxito", "Configuración guardada correctamente")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando configuración:\\n{str(e)}")
    
    def reset_config(self):
        """Restablece la configuración por defecto"""
        if messagebox.askyesno("Confirmar", "¿Está seguro de restablecer toda la configuración?"):
            # Recargar ventana con valores por defecto
            self.window.destroy()
            ConfigurationWindow(self.parent)
    
    def detect_printers(self):
        """Detecta impresoras disponibles"""
        try:
            import win32print
            printers = [printer[2] for printer in win32print.EnumPrinters(2)]
            self.ticket_printer['values'] = printers
            if printers:
                messagebox.showinfo("Impresoras Detectadas", f"Se encontraron {len(printers)} impresoras")
            else:
                messagebox.showwarning("Sin Impresoras", "No se encontraron impresoras")
        except ImportError:
            messagebox.showwarning("Error", "Función no disponible en este sistema")
        except Exception as e:
            messagebox.showerror("Error", f"Error detectando impresoras:\\n{str(e)}")
    
    def test_print(self):
        """Imprime un ticket de prueba"""
        messagebox.showinfo("Prueba de Impresión", "Funcionalidad de prueba - Próximamente")
    
    def test_database(self):
        """Prueba la conexión a la base de datos"""
        try:
            from core.database import DatabaseManager
            db = DatabaseManager()
            if db.test_connection():
                messagebox.showinfo("Conexión Exitosa", "Base de datos conectada correctamente")
            else:
                messagebox.showerror("Error de Conexión", "No se pudo conectar a la base de datos")
        except Exception as e:
            messagebox.showerror("Error", f"Error probando conexión:\\n{str(e)}")
    
    def browse_database(self):
        """Permite seleccionar archivo de base de datos"""
        filename = filedialog.askopenfilename(
            title="Seleccionar Base de Datos",
            filetypes=[("SQLite", "*.db"), ("Todos", "*.*")]
        )
        if filename:
            self.db_path.delete(0, tk.END)
            self.db_path.insert(0, filename)
    
    def browse_backup_folder(self):
        """Permite seleccionar carpeta de respaldos"""
        folder = filedialog.askdirectory(title="Seleccionar Carpeta de Respaldos")
        if folder:
            self.backup_path.delete(0, tk.END)
            self.backup_path.insert(0, folder)
    
    def choose_color(self):
        """Permite elegir color personalizado"""
        try:
            from tkinter import colorchooser
            color = colorchooser.askcolor(title="Elegir Color Principal")
            if color[1]:
                self.primary_color.delete(0, tk.END)
                self.primary_color.insert(0, color[1])
        except:
            messagebox.showwarning("Color", "Selector de color no disponible")
    
    def change_logo(self):
        """Permite cambiar el logo"""
        filename = filedialog.askopenfilename(
            title="Seleccionar Logo",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp"), ("Todos", "*.*")]
        )
        if filename:
            try:
                # Copiar logo a assets
                import shutil
                os.makedirs('assets', exist_ok=True)
                shutil.copy2(filename, 'assets/logo_custom.png')
                messagebox.showinfo("Logo", "Logo actualizado correctamente")
                
                # Recargar logo
                self.load_logo()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error actualizando logo:\\n{str(e)}")
    
    def create_backup(self):
        """Crea un respaldo de la base de datos"""
        messagebox.showinfo("Backup", "Funcionalidad de respaldo - Próximamente")
    
    def restore_backup(self):
        """Restaura un respaldo"""
        messagebox.showinfo("Restaurar", "Funcionalidad de restauración - Próximamente")
    
    def manual_backup(self):
        """Crea un respaldo manual"""
        try:
            import shutil
            from datetime import datetime
            
            # Crear directorio de respaldos
            backup_dir = self.backup_path.get()
            os.makedirs(backup_dir, exist_ok=True)
            
            # Nombre del respaldo con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.db"
            backup_full_path = os.path.join(backup_dir, backup_name)
            
            # Copiar base de datos
            db_path = self.db_path.get()
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_full_path)
                messagebox.showinfo("Respaldo Creado", f"Respaldo creado:\\n{backup_name}")
                self.refresh_backup_list()
            else:
                messagebox.showerror("Error", "Base de datos no encontrada")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error creando respaldo:\\n{str(e)}")
    
    def restore_from_file(self):
        """Restaura desde un archivo seleccionado"""
        filename = filedialog.askopenfilename(
            title="Seleccionar Archivo de Respaldo",
            filetypes=[("Base de Datos", "*.db"), ("Todos", "*.*")]
        )
        if filename:
            if messagebox.askyesno("Confirmar Restauración", 
                                  "¿Está seguro? Esta acción reemplazará la base de datos actual"):
                try:
                    import shutil
                    db_path = self.db_path.get()
                    
                    # Crear respaldo de seguridad antes de restaurar
                    backup_current = f"{db_path}.backup_before_restore"
                    shutil.copy2(db_path, backup_current)
                    
                    # Restaurar
                    shutil.copy2(filename, db_path)
                    messagebox.showinfo("Restauración Completa", "Base de datos restaurada correctamente")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Error restaurando:\\n{str(e)}")
    
    def refresh_backup_list(self):
        """Actualiza la lista de respaldos"""
        try:
            backup_dir = self.backup_path.get()
            if os.path.exists(backup_dir):
                backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
                backups.sort(reverse=True)  # Más recientes primero
                
                self.backup_listbox.delete(0, tk.END)
                for backup in backups:
                    self.backup_listbox.insert(tk.END, backup)
        except:
            pass  # Silenciar errores de directorio
    
    def run(self):
        """Ejecuta la ventana de configuración"""
        self.window.mainloop()

if __name__ == "__main__":
    config_window = ConfigurationWindow()
    config_window.run()
