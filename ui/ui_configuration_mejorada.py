"""
Ventana de Configuración del Sistema POS - VERSIÓN MEJORADA
Configuraciones generales, impresoras, base de datos, etc.
MEJORES COLORES Y CONTRASTE PARA MEJOR LEGIBILIDAD
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from PIL import Image, ImageTk

class ConfigurationWindow:
    """Ventana principal de configuración con mejor legibilidad"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.config_data = self.load_config()
        self.logo_photo = None  # Inicializar logo_photo
        
        # Crear ventana
        self.window = tk.Toplevel() if parent else tk.Tk()
        self.window.title("🔧 Configuración del Sistema - CajaCentral POS")
        self.window.geometry("900x700")
        self.window.resizable(True, True)
        
        # Configurar estilo con mejor contraste
        self.setup_styles()
        
        # Cargar logo si está disponible
        self.load_logo()
        
        # Crear interfaz
        self.create_interface()
        
        # Centrar ventana
        self.center_window()
    
    def setup_styles(self):
        """Configura estilos con MEJOR CONTRASTE - Azul Rey y Verde Turquesa"""
        self.window.configure(bg='#1e3a8a')  # Azul rey como fondo principal
        
        style = ttk.Style()
        style.configure('Config.TFrame', background='#1e3a8a')
        style.configure('ConfigHeader.TLabel', 
                       font=('Segoe UI', 16, 'bold'),
                       background='#1e3a8a',
                       foreground='#ffffff')  # Blanco sobre azul rey
        style.configure('ConfigSection.TLabel',
                       font=('Segoe UI', 12, 'bold'),
                       background='#ffffff',
                       foreground='#1e3a8a')  # Azul rey sobre blanco
        style.configure('ConfigText.TLabel',
                       font=('Segoe UI', 10),
                       background='#ffffff',
                       foreground='#1f2937')  # Gris muy oscuro legible
        style.configure('Config.TNotebook',
                       background='#1e3a8a',
                       borderwidth=1)
        style.configure('Config.TNotebook.Tab',
                       font=('Segoe UI', 11, 'bold'),
                       padding=[20, 10],
                       foreground='#ffffff',  # Blanco para pestañas
                       background='#0f766e')  # Verde turquesa para pestañas
        style.map('Config.TNotebook.Tab',
                 background=[('selected', '#14b8a6'),  # Verde turquesa más claro cuando seleccionado
                           ('active', '#06d6a0')],    # Verde turquesa brillante cuando hover
                 foreground=[('selected', '#ffffff'),
                           ('active', '#ffffff')])
    
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
        """Crea la interfaz principal con mejor contraste"""
        # Header con logo - Azul rey más intenso
        header_frame = tk.Frame(self.window, bg='#1e40af', height=90)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # Logo y título
        title_frame = tk.Frame(header_frame, bg='#1e40af')
        title_frame.pack(expand=True, fill='both')
        
        if self.logo_photo:
            logo_label = tk.Label(title_frame, image=self.logo_photo, bg='#1e40af')
            logo_label.pack(side='left', padx=20, pady=15)
        
        title_label = tk.Label(
            title_frame,
            text="⚙️ Configuración del Sistema",
            font=('Segoe UI', 20, 'bold'),
            fg='white',  # Blanco sobre azul rey = máximo contraste
            bg='#1e40af'
        )
        title_label.pack(pady=25)
        
        # Notebook para pestañas con mejor estilo
        self.notebook = ttk.Notebook(self.window, style='Config.TNotebook')
        self.notebook.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Pestañas
        self.create_general_tab()
        self.create_printer_tab()
        self.create_database_tab()
        self.create_appearance_tab()
        self.create_backup_tab()
        
        # Footer con botones
        self.create_footer()
    
    def create_general_tab(self):
        """Pestaña General con mejor contraste"""
        general_frame = ttk.Frame(self.notebook, style='Config.TFrame')
        self.notebook.add(general_frame, text="📊 General")
        
        # Marco principal blanco con borde
        main_frame = tk.Frame(general_frame, bg='white', relief='solid', bd=1)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Información de la Empresa
        company_frame = tk.LabelFrame(main_frame, text="🏢 Información de la Empresa", 
                                     bg='white', fg='#000000', font=('Segoe UI', 12, 'bold'),
                                     relief='groove', bd=2)
        company_frame.pack(fill='x', padx=15, pady=10)
        
        # Campos de empresa con mejor contraste
        tk.Label(company_frame, text="Nombre de la Empresa:", bg='white', 
                font=('Segoe UI', 11, 'bold'), fg='#000000').grid(row=0, column=0, sticky='w', padx=15, pady=8)
        self.company_name = tk.Entry(company_frame, width=45, font=('Segoe UI', 11), 
                                   bg='#f8f9fa', fg='#000000', relief='solid', bd=1,
                                   insertbackground='#000000')  # Cursor negro
        self.company_name.grid(row=0, column=1, padx=15, pady=8)
        self.company_name.insert(0, self.config_data.get('company_name', 'CajaCentral POS'))
        
        tk.Label(company_frame, text="RUC/NIT:", bg='white', 
                font=('Segoe UI', 11, 'bold'), fg='#000000').grid(row=1, column=0, sticky='w', padx=15, pady=8)
        self.company_ruc = tk.Entry(company_frame, width=45, font=('Segoe UI', 11), 
                                  bg='#f8f9fa', fg='#000000', relief='solid', bd=1,
                                  insertbackground='#000000')
        self.company_ruc.grid(row=1, column=1, padx=15, pady=8)
        self.company_ruc.insert(0, self.config_data.get('company_ruc', ''))
        
        tk.Label(company_frame, text="Dirección:", bg='white', 
                font=('Segoe UI', 11, 'bold'), fg='#000000').grid(row=2, column=0, sticky='w', padx=15, pady=8)
        self.company_address = tk.Entry(company_frame, width=45, font=('Segoe UI', 11), 
                                      bg='#f8f9fa', fg='#000000', relief='solid', bd=1,
                                      insertbackground='#000000')
        self.company_address.grid(row=2, column=1, padx=15, pady=8)
        self.company_address.insert(0, self.config_data.get('company_address', ''))
        
        tk.Label(company_frame, text="Teléfono:", bg='white', 
                font=('Segoe UI', 11, 'bold'), fg='#000000').grid(row=3, column=0, sticky='w', padx=15, pady=8)
        self.company_phone = tk.Entry(company_frame, width=45, font=('Segoe UI', 11), 
                                    bg='#f8f9fa', fg='#000000', relief='solid', bd=1,
                                    insertbackground='#000000')
        self.company_phone.grid(row=3, column=1, padx=15, pady=8)
        self.company_phone.insert(0, self.config_data.get('company_phone', ''))
        
        # Configuraciones del Sistema
        system_frame = tk.LabelFrame(main_frame, text="⚙️ Configuraciones del Sistema", 
                                   bg='white', fg='#000000', font=('Segoe UI', 12, 'bold'),
                                   relief='groove', bd=2)
        system_frame.pack(fill='x', padx=15, pady=10)
        
        tk.Label(system_frame, text="Moneda:", bg='white', 
                font=('Segoe UI', 11, 'bold'), fg='#000000').grid(row=0, column=0, sticky='w', padx=15, pady=8)
        self.currency = ttk.Combobox(system_frame, values=['CRC', 'USD', 'EUR'], width=15, 
                                   font=('Segoe UI', 11), foreground='#000000')
        self.currency.grid(row=0, column=1, padx=15, pady=8, sticky='w')
        self.currency.set(self.config_data.get('currency', 'CRC'))
        
        tk.Label(system_frame, text="IVA (%):", bg='white', 
                font=('Segoe UI', 11, 'bold'), fg='#000000').grid(row=1, column=0, sticky='w', padx=15, pady=8)
        self.tax_rate = tk.Entry(system_frame, width=10, font=('Segoe UI', 11), 
                               bg='#f8f9fa', fg='#000000', relief='solid', bd=1,
                               insertbackground='#000000')
        self.tax_rate.grid(row=1, column=1, padx=15, pady=8, sticky='w')
        self.tax_rate.insert(0, self.config_data.get('tax_rate', '13'))
        
        # Checkboxes con mejor contraste
        self.auto_backup = tk.BooleanVar(value=self.config_data.get('auto_backup', True))
        tk.Checkbutton(system_frame, text="Respaldo automático diario", variable=self.auto_backup,
                      bg='white', fg='#000000', font=('Segoe UI', 10), 
                      selectcolor='#f8f9fa', activebackground='white',
                      activeforeground='#000000').grid(row=2, column=0, columnspan=2, sticky='w', padx=15, pady=5)
        
        self.print_auto = tk.BooleanVar(value=self.config_data.get('print_auto', True))
        tk.Checkbutton(system_frame, text="Imprimir tickets automáticamente", variable=self.print_auto,
                      bg='white', fg='#000000', font=('Segoe UI', 10),
                      selectcolor='#f8f9fa', activebackground='white',
                      activeforeground='#000000').grid(row=3, column=0, columnspan=2, sticky='w', padx=15, pady=5)
        
        self.sound_enabled = tk.BooleanVar(value=self.config_data.get('sound_enabled', True))
        tk.Checkbutton(system_frame, text="Sonidos del sistema habilitados", variable=self.sound_enabled,
                      bg='white', fg='#000000', font=('Segoe UI', 10),
                      selectcolor='#f8f9fa', activebackground='white',
                      activeforeground='#000000').grid(row=4, column=0, columnspan=2, sticky='w', padx=15, pady=5)
    
    def create_printer_tab(self):
        """Pestaña de Impresoras con mejor contraste"""
        printer_frame = ttk.Frame(self.notebook, style='Config.TFrame')
        self.notebook.add(printer_frame, text="🖨️ Impresoras")
        
        main_frame = tk.Frame(printer_frame, bg='white', relief='solid', bd=1)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        config_frame = tk.LabelFrame(main_frame, text="🖨️ Configuración de Impresión", 
                                   bg='white', fg='#000000', font=('Segoe UI', 12, 'bold'),
                                   relief='groove', bd=2)
        config_frame.pack(fill='x', padx=15, pady=10)
        
        tk.Label(config_frame, text="Impresora para Tickets:", bg='white', 
                font=('Segoe UI', 11, 'bold'), fg='#000000').grid(row=0, column=0, sticky='w', padx=15, pady=8)
        
        printers_frame = tk.Frame(config_frame, bg='white')
        printers_frame.grid(row=0, column=1, padx=15, pady=8, sticky='w')
        
        self.printer_name = ttk.Combobox(printers_frame, width=30, font=('Segoe UI', 10),
                                       foreground='#000000')
        self.printer_name.pack(side='left', padx=(0, 10))
        self.printer_name.set(self.config_data.get('printer_name', 'Impresora predeterminada'))
        
        ttk.Button(printers_frame, text="🔄 Actualizar", 
                  command=self.refresh_printers).pack(side='left')
        
        # Más configuraciones de impresora...
        tk.Label(config_frame, text="Ancho del Papel (chars):", bg='white', 
                font=('Segoe UI', 11, 'bold'), fg='#000000').grid(row=1, column=0, sticky='w', padx=15, pady=8)
        self.paper_width = tk.Entry(config_frame, width=10, font=('Segoe UI', 11), 
                                  bg='#f8f9fa', fg='#000000', relief='solid', bd=1,
                                  insertbackground='#000000')
        self.paper_width.grid(row=1, column=1, padx=15, pady=8, sticky='w')
        self.paper_width.insert(0, self.config_data.get('paper_width', '32'))
    
    def create_database_tab(self):
        """Pestaña de Base de Datos con mejor contraste"""
        db_frame = ttk.Frame(self.notebook, style='Config.TFrame')
        self.notebook.add(db_frame, text="💾 Base de Datos")
        
        main_frame = tk.Frame(db_frame, bg='white', relief='solid', bd=1)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        config_frame = tk.LabelFrame(main_frame, text="💾 Configuración de Base de Datos", 
                                   bg='white', fg='#000000', font=('Segoe UI', 12, 'bold'),
                                   relief='groove', bd=2)
        config_frame.pack(fill='x', padx=15, pady=10)
        
        tk.Label(config_frame, text="Tipo de Base de Datos:", bg='white', 
                font=('Segoe UI', 11, 'bold'), fg='#000000').grid(row=0, column=0, sticky='w', padx=15, pady=8)
        self.db_type = ttk.Combobox(config_frame, values=['SQLite', 'MySQL', 'PostgreSQL'], 
                                  width=20, font=('Segoe UI', 11), foreground='#000000')
        self.db_type.grid(row=0, column=1, padx=15, pady=8, sticky='w')
        self.db_type.set(self.config_data.get('db_type', 'SQLite'))
    
    def create_appearance_tab(self):
        """Pestaña de Apariencia con mejor contraste"""
        appearance_frame = ttk.Frame(self.notebook, style='Config.TFrame')
        self.notebook.add(appearance_frame, text="🎨 Apariencia")
        
        main_frame = tk.Frame(appearance_frame, bg='white', relief='solid', bd=1)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        theme_frame = tk.LabelFrame(main_frame, text="🎨 Configuración de Tema", 
                                  bg='white', fg='#000000', font=('Segoe UI', 12, 'bold'),
                                  relief='groove', bd=2)
        theme_frame.pack(fill='x', padx=15, pady=10)
        
        tk.Label(theme_frame, text="Tema:", bg='white', 
                font=('Segoe UI', 11, 'bold'), fg='#000000').grid(row=0, column=0, sticky='w', padx=15, pady=8)
        self.theme = ttk.Combobox(theme_frame, values=['Claro', 'Oscuro', 'Auto'], 
                                width=15, font=('Segoe UI', 11), foreground='#000000')
        self.theme.grid(row=0, column=1, padx=15, pady=8, sticky='w')
        self.theme.set(self.config_data.get('theme', 'Claro'))
    
    def create_backup_tab(self):
        """Pestaña de Respaldos con mejor contraste"""
        backup_frame = ttk.Frame(self.notebook, style='Config.TFrame')
        self.notebook.add(backup_frame, text="💾 Respaldos")
        
        main_frame = tk.Frame(backup_frame, bg='white', relief='solid', bd=1)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        auto_frame = tk.LabelFrame(main_frame, text="💾 Respaldo Automático", 
                                 bg='white', fg='#000000', font=('Segoe UI', 12, 'bold'),
                                 relief='groove', bd=2)
        auto_frame.pack(fill='x', padx=15, pady=10)
        
        tk.Label(auto_frame, text="Carpeta de respaldos:", bg='white', 
                font=('Segoe UI', 11, 'bold'), fg='#000000').pack(anchor='w', padx=15, pady=(15, 5))
        
        path_frame = tk.Frame(auto_frame, bg='white')
        path_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        self.backup_path = tk.Entry(path_frame, font=('Segoe UI', 11), 
                                  bg='#f8f9fa', fg='#000000', relief='solid', bd=1,
                                  insertbackground='#000000')
        self.backup_path.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.backup_path.insert(0, self.config_data.get('backup_path', './backups'))
        
        ttk.Button(path_frame, text="📁 Examinar", 
                  command=self.select_backup_folder).pack(side='right')
    
    def create_footer(self):
        """Crear footer con botones de acción"""
        footer_frame = tk.Frame(self.window, bg='#ecf0f1', height=60)
        footer_frame.pack(fill='x', side='bottom')
        footer_frame.pack_propagate(False)
        
        button_frame = tk.Frame(footer_frame, bg='#ecf0f1')
        button_frame.pack(pady=15)
        
        # Botones con mejor contraste
        save_btn = tk.Button(button_frame, text="💾 Guardar Configuración", 
                           font=('Segoe UI', 11, 'bold'), bg='#27ae60', fg='white',
                           relief='flat', padx=20, pady=8, cursor='hand2',
                           activebackground='#229954', activeforeground='white',
                           command=self.save_config)
        save_btn.pack(side='left', padx=10)
        
        reset_btn = tk.Button(button_frame, text="🔄 Restablecer", 
                            font=('Segoe UI', 11, 'bold'), bg='#f39c12', fg='white',
                            relief='flat', padx=20, pady=8, cursor='hand2',
                            activebackground='#e67e22', activeforeground='white',
                            command=self.reset_config)
        reset_btn.pack(side='left', padx=10)
        
        cancel_btn = tk.Button(button_frame, text="❌ Cancelar", 
                             font=('Segoe UI', 11, 'bold'), bg='#e74c3c', fg='white',
                             relief='flat', padx=20, pady=8, cursor='hand2',
                             activebackground='#c0392b', activeforeground='white',
                             command=self.close_window)
        cancel_btn.pack(side='left', padx=10)
    
    def refresh_printers(self):
        """Actualiza la lista de impresoras disponibles"""
        try:
            import win32print
            printers = [printer[2] for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)]
            self.printer_name['values'] = printers
            if printers:
                self.printer_name.set(printers[0])
        except ImportError:
            self.printer_name['values'] = ['Impresora predeterminada', 'Sin impresoras detectadas']
    
    def select_backup_folder(self):
        """Selecciona carpeta de respaldos"""
        folder = filedialog.askdirectory(title="Seleccionar Carpeta de Respaldos")
        if folder:
            self.backup_path.delete(0, tk.END)
            self.backup_path.insert(0, folder)
    
    def load_config(self):
        """Carga la configuración desde archivo"""
        try:
            config_file = "config/app_config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error cargando configuración: {e}")
        
        # Configuración por defecto
        return {
            "company_name": "CajaCentral POS",
            "company_ruc": "",
            "company_address": "",
            "company_phone": "",
            "currency": "CRC",
            "tax_rate": "13",
            "auto_backup": True,
            "print_auto": True,
            "sound_enabled": True,
            "printer_name": "Impresora predeterminada",
            "paper_width": "32",
            "db_type": "SQLite",
            "theme": "Claro",
            "backup_path": "./backups"
        }
    
    def save_config(self):
        """Guarda la configuración"""
        try:
            config = {
                "company_name": self.company_name.get(),
                "company_ruc": self.company_ruc.get(),
                "company_address": self.company_address.get(),
                "company_phone": self.company_phone.get(),
                "currency": self.currency.get(),
                "tax_rate": self.tax_rate.get(),
                "auto_backup": self.auto_backup.get(),
                "print_auto": self.print_auto.get(),
                "sound_enabled": self.sound_enabled.get(),
                "printer_name": self.printer_name.get(),
                "paper_width": self.paper_width.get(),
                "db_type": self.db_type.get(),
                "theme": self.theme.get(),
                "backup_path": self.backup_path.get()
            }
            
            # Crear directorio config si no existe
            os.makedirs("config", exist_ok=True)
            
            # Guardar configuración
            with open("config/app_config.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("✅ Éxito", 
                              "Configuración guardada correctamente.\n\n" +
                              "Algunos cambios pueden requerir reiniciar la aplicación.")
            
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error al guardar configuración:\n{e}")
    
    def reset_config(self):
        """Restablece configuración por defecto"""
        if messagebox.askyesno("⚠️ Confirmar", 
                              "¿Estás seguro de restablecer toda la configuración?\n\n" +
                              "Se perderán todos los cambios no guardados."):
            # Recargar valores por defecto
            default_config = self.load_config()
            
            # Actualizar campos
            self.company_name.delete(0, tk.END)
            self.company_name.insert(0, default_config.get('company_name', ''))
            
            self.company_ruc.delete(0, tk.END)
            self.company_ruc.insert(0, default_config.get('company_ruc', ''))
            
            # ... resto de campos
            
            messagebox.showinfo("✅ Restablecido", "Configuración restablecida a valores por defecto.")
    
    def close_window(self):
        """Cierra la ventana"""
        self.window.destroy()
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

# Para prueba independiente
if __name__ == "__main__":
    app = ConfigurationWindow()
    app.window.mainloop()
