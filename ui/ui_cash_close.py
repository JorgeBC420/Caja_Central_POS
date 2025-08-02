"""
Ventana de Corte de Caja - Sistema POS
Cierre de caja diario con conteo de efectivo y cuadre
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from PIL import Image, ImageTk

class CashCloseWindow:
    """Ventana para el corte/cierre de caja"""
    
    def __init__(self, parent=None):
        self.parent = parent
        
        # Crear ventana
        self.window = tk.Toplevel() if parent else tk.Tk()
        self.window.title("Corte de Caja - CajaCentral POS")
        self.window.geometry("600x700")
        self.window.resizable(False, False)
        
        # Configurar estilo
        self.window.configure(bg='#2c3e50')
        
        # Variables para cálculos
        self.setup_variables()
        
        # Crear interfaz
        self.create_interface()
        
        # Centrar ventana
        self.center_window()
        
        # Cargar datos del día
        self.load_daily_data()
    
    def setup_variables(self):
        """Configura las variables para cálculos"""
        # Variables de entrada (billetes y monedas)
        self.bills_50000 = tk.IntVar()
        self.bills_20000 = tk.IntVar()
        self.bills_10000 = tk.IntVar()
        self.bills_5000 = tk.IntVar()
        self.bills_2000 = tk.IntVar()
        self.bills_1000 = tk.IntVar()
        
        self.coins_500 = tk.IntVar()
        self.coins_100 = tk.IntVar()
        self.coins_50 = tk.IntVar()
        self.coins_25 = tk.IntVar()
        self.coins_10 = tk.IntVar()
        self.coins_5 = tk.IntVar()
        
        # Variables calculadas
        self.total_counted = tk.DoubleVar()
        self.expected_cash = tk.DoubleVar()
        self.difference = tk.DoubleVar()
        
        # Datos del día
        self.opening_balance = 50000.00  # Saldo inicial
        self.cash_sales = 0.00
        self.card_sales = 0.00
        self.expenses = 0.00
        
    def create_interface(self):
        """Crea la interfaz principal"""
        # Header
        header_frame = tk.Frame(self.window, bg='#34495e', height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # Logo y título
        title_frame = tk.Frame(header_frame, bg='#34495e')
        title_frame.pack(expand=True, fill='both')
        
        title_label = tk.Label(
            title_frame,
            text="💰 Corte de Caja",
            font=('Segoe UI', 18, 'bold'),
            fg='white',
            bg='#34495e'
        )
        title_label.pack(pady=20)
        
        # Fecha actual
        date_label = tk.Label(
            title_frame,
            text=datetime.now().strftime("Fecha: %d/%m/%Y - %H:%M"),
            font=('Segoe UI', 10),
            fg='#bdc3c7',
            bg='#34495e'
        )
        date_label.pack()
        
        # Contenido principal
        main_frame = tk.Frame(self.window, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Crear notebook para pestañas
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)
        
        # Pestaña 1: Conteo de efectivo
        self.create_cash_count_tab(notebook)
        
        # Pestaña 2: Resumen del día
        self.create_daily_summary_tab(notebook)
        
        # Pestaña 3: Cuadre final
        self.create_final_balance_tab(notebook)
        
        # Botones de acción
        self.create_action_buttons(main_frame)
    
    def create_cash_count_tab(self, notebook):
        """Crea la pestaña de conteo de efectivo"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="💵 Conteo de Efectivo")
        
        # Frame principal con scroll
        canvas = tk.Canvas(frame, bg='white')
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Título
        tk.Label(scrollable_frame, text="Conteo Manual de Efectivo", 
                font=('Segoe UI', 14, 'bold'), bg='white').pack(pady=10)
        
        # Billetes
        bills_frame = tk.LabelFrame(scrollable_frame, text="Billetes", 
                                  font=('Segoe UI', 12, 'bold'), bg='white')
        bills_frame.pack(fill='x', padx=20, pady=10)
        
        bills_data = [
            ("50,000", self.bills_50000, 50000),
            ("20,000", self.bills_20000, 20000),
            ("10,000", self.bills_10000, 10000),
            ("5,000", self.bills_5000, 5000),
            ("2,000", self.bills_2000, 2000),
            ("1,000", self.bills_1000, 1000),
        ]
        
        for i, (denomination, var, value) in enumerate(bills_data):
            row_frame = tk.Frame(bills_frame, bg='white')
            row_frame.pack(fill='x', padx=10, pady=5)
            
            tk.Label(row_frame, text=f"₡{denomination}:", 
                    font=('Segoe UI', 10), bg='white', width=15, anchor='w').pack(side='left')
            
            spinbox = tk.Spinbox(row_frame, from_=0, to=999, textvariable=var, 
                               width=10, font=('Segoe UI', 10))
            spinbox.pack(side='left', padx=10)
            
            # Label para mostrar subtotal
            subtotal_label = tk.Label(row_frame, text="₡0", 
                                    font=('Segoe UI', 10), bg='white', width=15, anchor='e')
            subtotal_label.pack(side='right')
            
            # Bind para actualizar subtotal
            var.trace('w', lambda *args, lbl=subtotal_label, v=var, val=value: 
                     lbl.config(text=f"₡{v.get() * val:,}"))
        
        # Monedas
        coins_frame = tk.LabelFrame(scrollable_frame, text="Monedas", 
                                  font=('Segoe UI', 12, 'bold'), bg='white')
        coins_frame.pack(fill='x', padx=20, pady=10)
        
        coins_data = [
            ("500", self.coins_500, 500),
            ("100", self.coins_100, 100),
            ("50", self.coins_50, 50),
            ("25", self.coins_25, 25),
            ("10", self.coins_10, 10),
            ("5", self.coins_5, 5),
        ]
        
        for i, (denomination, var, value) in enumerate(coins_data):
            row_frame = tk.Frame(coins_frame, bg='white')
            row_frame.pack(fill='x', padx=10, pady=5)
            
            tk.Label(row_frame, text=f"₡{denomination}:", 
                    font=('Segoe UI', 10), bg='white', width=15, anchor='w').pack(side='left')
            
            spinbox = tk.Spinbox(row_frame, from_=0, to=999, textvariable=var, 
                               width=10, font=('Segoe UI', 10))
            spinbox.pack(side='left', padx=10)
            
            # Label para mostrar subtotal
            subtotal_label = tk.Label(row_frame, text="₡0", 
                                    font=('Segoe UI', 10), bg='white', width=15, anchor='e')
            subtotal_label.pack(side='right')
            
            # Bind para actualizar subtotal
            var.trace('w', lambda *args, lbl=subtotal_label, v=var, val=value: 
                     lbl.config(text=f"₡{v.get() * val:,}"))
        
        # Total contado
        total_frame = tk.Frame(scrollable_frame, bg='#3498db')
        total_frame.pack(fill='x', padx=20, pady=20)
        
        tk.Label(total_frame, text="TOTAL CONTADO:", 
                font=('Segoe UI', 14, 'bold'), fg='white', bg='#3498db').pack(side='left', padx=20, pady=15)
        
        self.total_label = tk.Label(total_frame, text="₡0", 
                                  font=('Segoe UI', 16, 'bold'), fg='white', bg='#3498db')
        self.total_label.pack(side='right', padx=20, pady=15)
        
        # Botón para calcular
        tk.Button(scrollable_frame, text="🧮 Calcular Total", 
                 command=self.calculate_total, bg='#27ae60', fg='white', 
                 font=('Segoe UI', 12, 'bold')).pack(pady=20)
    
    def create_daily_summary_tab(self, notebook):
        """Crea la pestaña de resumen del día"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="📊 Resumen del Día")
        
        # Frame con fondo blanco
        content_frame = tk.Frame(frame, bg='white')
        content_frame.pack(fill='both', expand=True)
        
        # Título
        tk.Label(content_frame, text="Resumen de Operaciones", 
                font=('Segoe UI', 16, 'bold'), bg='white').pack(pady=20)
        
        # Información del día
        info_frame = tk.Frame(content_frame, bg='white')
        info_frame.pack(fill='both', expand=True, padx=40, pady=20)
        
        # Crear campos de información
        self.create_info_row(info_frame, "Saldo Inicial:", f"₡{self.opening_balance:,.2f}")
        self.create_info_row(info_frame, "Ventas en Efectivo:", f"₡{self.cash_sales:,.2f}")
        self.create_info_row(info_frame, "Ventas con Tarjeta:", f"₡{self.card_sales:,.2f}")
        self.create_info_row(info_frame, "Total Ventas:", f"₡{self.cash_sales + self.card_sales:,.2f}")
        self.create_info_row(info_frame, "Gastos:", f"₡{self.expenses:,.2f}")
        
        # Línea separadora
        separator = tk.Frame(info_frame, height=2, bg='#bdc3c7')
        separator.pack(fill='x', pady=20)
        
        # Efectivo esperado
        expected = self.opening_balance + self.cash_sales - self.expenses
        self.create_info_row(info_frame, "Efectivo Esperado:", f"₡{expected:,.2f}", bold=True)
        
        # Botón para actualizar datos
        tk.Button(content_frame, text="🔄 Actualizar Datos", 
                 command=self.load_daily_data, bg='#3498db', fg='white', 
                 font=('Segoe UI', 10)).pack(pady=20)
    
    def create_final_balance_tab(self, notebook):
        """Crea la pestaña de cuadre final"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="⚖️ Cuadre Final")
        
        content_frame = tk.Frame(frame, bg='white')
        content_frame.pack(fill='both', expand=True)
        
        # Título
        tk.Label(content_frame, text="Cuadre de Caja", 
                font=('Segoe UI', 16, 'bold'), bg='white').pack(pady=20)
        
        # Frame para el cuadre
        balance_frame = tk.Frame(content_frame, bg='white')
        balance_frame.pack(fill='both', expand=True, padx=40)
        
        # Labels que se actualizarán
        self.expected_label = tk.Label(balance_frame, text="Efectivo Esperado: ₡0", 
                                     font=('Segoe UI', 12), bg='white')
        self.expected_label.pack(pady=10)
        
        self.counted_label = tk.Label(balance_frame, text="Efectivo Contado: ₡0", 
                                    font=('Segoe UI', 12), bg='white')
        self.counted_label.pack(pady=10)
        
        # Línea separadora
        separator = tk.Frame(balance_frame, height=2, bg='#bdc3c7')
        separator.pack(fill='x', pady=20)
        
        # Diferencia
        self.difference_label = tk.Label(balance_frame, text="Diferencia: ₡0", 
                                       font=('Segoe UI', 14, 'bold'), bg='white')
        self.difference_label.pack(pady=10)
        
        # Status
        self.status_label = tk.Label(balance_frame, text="", 
                                   font=('Segoe UI', 12, 'bold'), bg='white')
        self.status_label.pack(pady=20)
        
        # Campo para observaciones
        obs_frame = tk.LabelFrame(content_frame, text="Observaciones", 
                                font=('Segoe UI', 10, 'bold'), bg='white')
        obs_frame.pack(fill='x', padx=40, pady=20)
        
        self.observations_text = tk.Text(obs_frame, height=4, font=('Segoe UI', 10))
        self.observations_text.pack(fill='x', padx=10, pady=10)
    
    def create_info_row(self, parent, label, value, bold=False):
        """Crea una fila de información"""
        row_frame = tk.Frame(parent, bg='white')
        row_frame.pack(fill='x', pady=5)
        
        font_style = ('Segoe UI', 12, 'bold') if bold else ('Segoe UI', 12)
        
        tk.Label(row_frame, text=label, font=font_style, 
                bg='white', width=20, anchor='w').pack(side='left')
        tk.Label(row_frame, text=value, font=font_style, 
                bg='white', anchor='e').pack(side='right')
    
    def create_action_buttons(self, parent):
        """Crea los botones de acción"""
        button_frame = tk.Frame(parent, bg='#2c3e50')
        button_frame.pack(fill='x', pady=20)
        
        tk.Button(button_frame, text="💾 Guardar Corte", 
                 command=self.save_cash_close, bg='#27ae60', fg='white', 
                 font=('Segoe UI', 12, 'bold'), width=15).pack(side='left', padx=10)
        
        tk.Button(button_frame, text="🖨️ Imprimir Reporte", 
                 command=self.print_report, bg='#3498db', fg='white', 
                 font=('Segoe UI', 12), width=15).pack(side='left', padx=10)
        
        tk.Button(button_frame, text="❌ Cancelar", 
                 command=self.window.destroy, bg='#e74c3c', fg='white', 
                 font=('Segoe UI', 12), width=15).pack(side='right', padx=10)
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def load_daily_data(self):
        """Carga los datos del día desde la base de datos"""
        # Aquí conectarías con tu base de datos real
        # Por ahora usamos datos simulados
        
        self.opening_balance = 50000.00
        self.cash_sales = 95000.00
        self.card_sales = 50000.00
        self.expenses = 5000.00
        
        # Actualizar labels si existen
        try:
            expected = self.opening_balance + self.cash_sales - self.expenses
            self.expected_label.config(text=f"Efectivo Esperado: ₡{expected:,.2f}")
            self.expected_cash.set(expected)
        except:
            pass
    
    def calculate_total(self):
        """Calcula el total de efectivo contado"""
        total = 0
        
        # Sumar billetes
        total += self.bills_50000.get() * 50000
        total += self.bills_20000.get() * 20000
        total += self.bills_10000.get() * 10000
        total += self.bills_5000.get() * 5000
        total += self.bills_2000.get() * 2000
        total += self.bills_1000.get() * 1000
        
        # Sumar monedas
        total += self.coins_500.get() * 500
        total += self.coins_100.get() * 100
        total += self.coins_50.get() * 50
        total += self.coins_25.get() * 25
        total += self.coins_10.get() * 10
        total += self.coins_5.get() * 5
        
        # Actualizar variables
        self.total_counted.set(total)
        self.total_label.config(text=f"₡{total:,.2f}")
        
        # Actualizar cuadre
        self.update_balance()
    
    def update_balance(self):
        """Actualiza el cuadre final"""
        expected = self.opening_balance + self.cash_sales - self.expenses
        counted = self.total_counted.get()
        difference = counted - expected
        
        # Actualizar labels
        self.expected_label.config(text=f"Efectivo Esperado: ₡{expected:,.2f}")
        self.counted_label.config(text=f"Efectivo Contado: ₡{counted:,.2f}")
        self.difference_label.config(text=f"Diferencia: ₡{difference:,.2f}")
        
        # Status según diferencia
        if abs(difference) <= 100:  # Tolerancia de ₡100
            self.status_label.config(text="✅ CAJA CUADRADA", fg='#27ae60')
        elif difference > 0:
            self.status_label.config(text="📈 SOBRANTE EN CAJA", fg='#f39c12')
        else:
            self.status_label.config(text="📉 FALTANTE EN CAJA", fg='#e74c3c')
    
    def save_cash_close(self):
        """Guarda el corte de caja"""
        if self.total_counted.get() == 0:
            messagebox.showwarning("Advertencia", "Debe realizar el conteo de efectivo primero")
            return
        
        if messagebox.askyesno("Confirmar", "¿Está seguro de guardar este corte de caja?\nEsta acción no se puede deshacer."):
            try:
                # Aquí guardarías en la base de datos
                cash_close_data = {
                    "date": datetime.now().isoformat(),
                    "opening_balance": self.opening_balance,
                    "cash_sales": self.cash_sales,
                    "card_sales": self.card_sales,
                    "expenses": self.expenses,
                    "expected_cash": self.opening_balance + self.cash_sales - self.expenses,
                    "counted_cash": self.total_counted.get(),
                    "difference": self.total_counted.get() - (self.opening_balance + self.cash_sales - self.expenses),
                    "observations": self.observations_text.get('1.0', 'end-1c'),
                    "bills_count": {
                        "50000": self.bills_50000.get(),
                        "20000": self.bills_20000.get(),
                        "10000": self.bills_10000.get(),
                        "5000": self.bills_5000.get(),
                        "2000": self.bills_2000.get(),
                        "1000": self.bills_1000.get(),
                    },
                    "coins_count": {
                        "500": self.coins_500.get(),
                        "100": self.coins_100.get(),
                        "50": self.coins_50.get(),
                        "25": self.coins_25.get(),
                        "10": self.coins_10.get(),
                        "5": self.coins_5.get(),
                    }
                }
                
                messagebox.showinfo("Éxito", "Corte de caja guardado correctamente")
                self.window.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error guardando corte de caja:\n{str(e)}")
    
    def print_report(self):
        """Imprime el reporte de corte de caja"""
        messagebox.showinfo("Imprimir", "Funcionalidad de impresión - Próximamente")
    
    def run(self):
        """Ejecuta la ventana"""
        self.window.mainloop()

if __name__ == "__main__":
    cash_close = CashCloseWindow()
    cash_close.run()
