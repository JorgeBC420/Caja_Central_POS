"""
Sistema de Ventas Simple - Solo Apertura y Cierre de Cuentas
Lógica básica para control de cuentas activas sin procesar productos complejos
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import os

class SimpleAccountManager:
    """Gestor simple de cuentas - Solo abre y cierra"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.active_accounts = {}  # ID cuenta: datos
        self.account_counter = 1
        
        # Crear ventana
        self.window = tk.Toplevel() if parent else tk.Tk()
        self.window.title("💰 Gestor Simple de Cuentas - CajaCentral POS")
        self.window.geometry("900x600")
        self.window.configure(bg='#1e3a8a')  # Azul rey de fondo
        self.window.resizable(True, True)
        
        # Cargar logo
        self.load_logo()
        
        # Crear interfaz
        self.create_interface()
        
        # Cargar cuentas existentes
        self.load_accounts()
        
        # Centrar ventana
        self.center_window()
    
    def load_logo(self):
        """Carga el logo si está disponible"""
        try:
            from core.brand_manager import get_brand_manager
            brand_manager = get_brand_manager()
            logo = brand_manager.get_logo("small")
            if logo:
                from PIL import ImageTk
                self.logo_photo = ImageTk.PhotoImage(logo)
            else:
                self.logo_photo = None
        except:
            self.logo_photo = None
    
    def create_interface(self):
        """Crea la interfaz principal"""
        # Header
        header_frame = tk.Frame(self.window, bg='#1e40af', height=80)  # Azul rey intenso
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        title_frame = tk.Frame(header_frame, bg='#1e40af')
        title_frame.pack(expand=True, fill='both')
        
        if self.logo_photo:
            logo_label = tk.Label(title_frame, image=self.logo_photo, bg='#1e40af')
            logo_label.pack(side='left', padx=20, pady=10)
        
        title_label = tk.Label(
            title_frame,
            text="💰 Gestor Simple de Cuentas",
            font=('Segoe UI', 18, 'bold'),
            fg='white',
            bg='#1e40af'
        )
        title_label.pack(pady=20)
        
        # Contenedor principal
        main_frame = tk.Frame(self.window, bg='white', relief='solid', bd=1)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Panel de acciones
        self.create_actions_panel(main_frame)
        
        # Panel de cuentas activas
        self.create_accounts_panel(main_frame)
        
        # Footer con estadísticas
        self.create_footer()
    
    def create_actions_panel(self, parent):
        """Panel de acciones principales"""
        actions_frame = tk.LabelFrame(parent, text="⚡ Acciones Rápidas", 
                                    bg='white', fg='#2c3e50', font=('Segoe UI', 14, 'bold'),
                                    relief='groove', bd=2)
        actions_frame.pack(fill='x', padx=10, pady=10)
        
        buttons_frame = tk.Frame(actions_frame, bg='white')
        buttons_frame.pack(fill='x', padx=20, pady=20)
        
        # Botón abrir nueva cuenta
        open_btn = tk.Button(
            buttons_frame,
            text="🆕 ABRIR NUEVA CUENTA",
            font=('Segoe UI', 14, 'bold'),
            bg='#27ae60',
            fg='white',
            relief='flat',
            padx=30,
            pady=15,
            cursor='hand2',
            activebackground='#229954',
            activeforeground='white',
            command=self.open_new_account
        )
        open_btn.pack(side='left', padx=10)
        
        # Botón cerrar cuenta
        close_btn = tk.Button(
            buttons_frame,
            text="💳 CERRAR CUENTA",
            font=('Segoe UI', 14, 'bold'),
            bg='#e74c3c',
            fg='white',
            relief='flat',
            padx=30,
            pady=15,
            cursor='hand2',
            activebackground='#c0392b',
            activeforeground='white',
            command=self.close_account
        )
        close_btn.pack(side='left', padx=10)
        
        # Botón ver historial
        history_btn = tk.Button(
            buttons_frame,
            text="📋 VER HISTORIAL",
            font=('Segoe UI', 14, 'bold'),
            bg='#3498db',
            fg='white',
            relief='flat',
            padx=30,
            pady=15,
            cursor='hand2',
            activebackground='#2980b9',
            activeforeground='white',
            command=self.show_history
        )
        history_btn.pack(side='left', padx=10)
    
    def create_accounts_panel(self, parent):
        """Panel de cuentas activas"""
        accounts_frame = tk.LabelFrame(parent, text="🏪 Cuentas Activas", 
                                     bg='white', fg='#2c3e50', font=('Segoe UI', 14, 'bold'),
                                     relief='groove', bd=2)
        accounts_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Treeview para mostrar cuentas
        columns = ('ID', 'Cliente', 'Mesa/Ubicación', 'Hora Apertura', 'Tiempo Activo', 'Estado')
        self.accounts_tree = ttk.Treeview(accounts_frame, columns=columns, show='headings', height=10)
        
        # Configurar encabezados
        self.accounts_tree.heading('ID', text='ID Cuenta')
        self.accounts_tree.heading('Cliente', text='Cliente')
        self.accounts_tree.heading('Mesa/Ubicación', text='Mesa/Ubicación')
        self.accounts_tree.heading('Hora Apertura', text='Hora Apertura')
        self.accounts_tree.heading('Tiempo Activo', text='Tiempo Activo')
        self.accounts_tree.heading('Estado', text='Estado')
        
        # Configurar anchos
        self.accounts_tree.column('ID', width=80)
        self.accounts_tree.column('Cliente', width=150)
        self.accounts_tree.column('Mesa/Ubicación', width=120)
        self.accounts_tree.column('Hora Apertura', width=120)
        self.accounts_tree.column('Tiempo Activo', width=120)
        self.accounts_tree.column('Estado', width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(accounts_frame, orient="vertical", command=self.accounts_tree.yview)
        self.accounts_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview y scrollbar
        tree_frame = tk.Frame(accounts_frame, bg='white')
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.accounts_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Actualizar automáticamente cada 30 segundos
        self.update_accounts_display()
        self.window.after(30000, self.auto_update_display)
    
    def create_footer(self):
        """Footer con estadísticas - Verde turquesa"""
        footer_frame = tk.Frame(self.window, bg='#14b8a6', height=50)
        footer_frame.pack(fill='x', side='bottom')
        footer_frame.pack_propagate(False)
        
        stats_frame = tk.Frame(footer_frame, bg='#14b8a6')
        stats_frame.pack(pady=10)
        
        # Estadísticas básicas
        self.stats_label = tk.Label(
            stats_frame,
            text="🏪 Cuentas Activas: 0 | 💰 Total del Día: ₡0 | 🕒 " + datetime.now().strftime('%H:%M:%S'),
            font=('Segoe UI', 11, 'bold'),
            bg='#14b8a6',
            fg='white'  # Blanco sobre verde turquesa
        )
        self.stats_label.pack()
    
    def open_new_account(self):
        """Abre una nueva cuenta"""
        # Ventana para datos de la cuenta
        account_window = tk.Toplevel(self.window)
        account_window.title("🆕 Abrir Nueva Cuenta")
        account_window.geometry("500x400")
        account_window.transient(self.window)
        account_window.grab_set()
        account_window.configure(bg='white')
        
        # Header
        header_frame = tk.Frame(account_window, bg='#27ae60', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🆕 NUEVA CUENTA", 
                font=('Segoe UI', 16, 'bold'), bg='#27ae60', fg='white').pack(pady=15)
        
        # Formulario
        form_frame = tk.Frame(account_window, bg='white')
        form_frame.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Campo cliente
        tk.Label(form_frame, text="Nombre del Cliente:", bg='white', 
                font=('Segoe UI', 12, 'bold'), fg='#2c3e50').pack(anchor='w', pady=(0, 5))
        client_entry = tk.Entry(form_frame, width=40, font=('Segoe UI', 12), 
                              bg='#f8f9fa', fg='#2c3e50', relief='solid', bd=1)
        client_entry.pack(anchor='w', pady=(0, 15))
        client_entry.focus_set()
        
        # Campo mesa/ubicación
        tk.Label(form_frame, text="Mesa/Ubicación:", bg='white', 
                font=('Segoe UI', 12, 'bold'), fg='#2c3e50').pack(anchor='w', pady=(0, 5))
        location_entry = tk.Entry(form_frame, width=40, font=('Segoe UI', 12), 
                                bg='#f8f9fa', fg='#2c3e50', relief='solid', bd=1)
        location_entry.pack(anchor='w', pady=(0, 15))
        
        # Tipo de cuenta
        tk.Label(form_frame, text="Tipo de Cuenta:", bg='white', 
                font=('Segoe UI', 12, 'bold'), fg='#2c3e50').pack(anchor='w', pady=(0, 5))
        
        account_type = tk.StringVar(value="restaurante")
        types_frame = tk.Frame(form_frame, bg='white')
        types_frame.pack(anchor='w', pady=(0, 15))
        
        tk.Radiobutton(types_frame, text="🍽️ Restaurante", variable=account_type, 
                      value="restaurante", bg='white', fg='#2c3e50', 
                      font=('Segoe UI', 11)).pack(anchor='w')
        tk.Radiobutton(types_frame, text="🏪 Tienda", variable=account_type, 
                      value="tienda", bg='white', fg='#2c3e50', 
                      font=('Segoe UI', 11)).pack(anchor='w')
        tk.Radiobutton(types_frame, text="🛍️ Servicio", variable=account_type, 
                      value="servicio", bg='white', fg='#2c3e50', 
                      font=('Segoe UI', 11)).pack(anchor='w')
        
        # Notas
        tk.Label(form_frame, text="Notas (opcional):", bg='white', 
                font=('Segoe UI', 12, 'bold'), fg='#2c3e50').pack(anchor='w', pady=(0, 5))
        notes_text = tk.Text(form_frame, height=4, width=45, font=('Segoe UI', 10), 
                           bg='#f8f9fa', fg='#2c3e50', relief='solid', bd=1)
        notes_text.pack(anchor='w', pady=(0, 20))
        
        # Función para crear cuenta
        def create_account():
            client_name = client_entry.get().strip()
            location = location_entry.get().strip()
            acc_type = account_type.get()
            notes = notes_text.get(1.0, tk.END).strip()
            
            if not client_name:
                messagebox.showerror("Error", "El nombre del cliente es obligatorio")
                return
            
            if not location:
                location = f"Mesa {self.account_counter}"
            
            # Crear cuenta
            account_id = f"ACC{self.account_counter:04d}"
            account_data = {
                "id": account_id,
                "client": client_name,
                "location": location,
                "type": acc_type,
                "notes": notes,
                "opened_at": datetime.now(),
                "status": "activa",
                "total_amount": 0.0
            }
            
            self.active_accounts[account_id] = account_data
            self.account_counter += 1
            
            # Guardar en archivo
            self.save_accounts()
            
            # Actualizar display
            self.update_accounts_display()
            
            messagebox.showinfo("✅ Cuenta Creada", 
                              f"Cuenta {account_id} creada exitosamente\n" +
                              f"Cliente: {client_name}\n" +
                              f"Ubicación: {location}")
            
            account_window.destroy()
        
        # Botones
        button_frame = tk.Frame(form_frame, bg='white')
        button_frame.pack(fill='x', pady=20)
        
        tk.Button(button_frame, text="✅ Crear Cuenta", 
                 font=('Segoe UI', 12, 'bold'), bg='#27ae60', fg='white',
                 relief='flat', padx=20, pady=10, cursor='hand2',
                 command=create_account).pack(side='left', padx=10)
        
        tk.Button(button_frame, text="❌ Cancelar", 
                 font=('Segoe UI', 12, 'bold'), bg='#95a5a6', fg='white',
                 relief='flat', padx=20, pady=10, cursor='hand2',
                 command=account_window.destroy).pack(side='left', padx=10)
    
    def close_account(self):
        """Cierra una cuenta seleccionada"""
        selected = self.accounts_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona una cuenta para cerrar")
            return
        
        item = self.accounts_tree.item(selected[0])
        account_id = item['values'][0]
        account_data = self.active_accounts.get(account_id)
        
        if not account_data:
            messagebox.showerror("Error", "Cuenta no encontrada")
            return
        
        # Ventana de cierre
        close_window = tk.Toplevel(self.window)
        close_window.title(f"💳 Cerrar Cuenta {account_id}")
        close_window.geometry("500x400")
        close_window.transient(self.window)
        close_window.grab_set()
        close_window.configure(bg='white')
        
        # Header
        header_frame = tk.Frame(close_window, bg='#e74c3c', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=f"💳 CERRAR CUENTA {account_id}", 
                font=('Segoe UI', 16, 'bold'), bg='#e74c3c', fg='white').pack(pady=15)
        
        # Información de la cuenta
        info_frame = tk.Frame(close_window, bg='white')
        info_frame.pack(fill='x', padx=30, pady=20)
        
        tk.Label(info_frame, text=f"Cliente: {account_data['client']}", 
                font=('Segoe UI', 12, 'bold'), bg='white', fg='#2c3e50').pack(anchor='w')
        tk.Label(info_frame, text=f"Ubicación: {account_data['location']}", 
                font=('Segoe UI', 12), bg='white', fg='#2c3e50').pack(anchor='w')
        
        time_active = datetime.now() - account_data['opened_at']
        hours, remainder = divmod(time_active.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        tk.Label(info_frame, text=f"Tiempo activo: {hours}h {minutes}m", 
                font=('Segoe UI', 12), bg='white', fg='#2c3e50').pack(anchor='w')
        
        # Monto total
        total_frame = tk.Frame(close_window, bg='white')
        total_frame.pack(fill='x', padx=30, pady=20)
        
        tk.Label(total_frame, text="Monto Total de la Cuenta:", bg='white', 
                font=('Segoe UI', 12, 'bold'), fg='#2c3e50').pack(anchor='w')
        total_entry = tk.Entry(total_frame, width=20, font=('Segoe UI', 14, 'bold'), 
                             bg='#f8f9fa', fg='#27ae60', relief='solid', bd=2,
                             justify='center')
        total_entry.pack(anchor='w', pady=5)
        total_entry.insert(0, "0.00")
        total_entry.focus_set()
        
        # Método de pago
        payment_frame = tk.Frame(close_window, bg='white')
        payment_frame.pack(fill='x', padx=30, pady=10)
        
        tk.Label(payment_frame, text="Método de Pago:", bg='white', 
                font=('Segoe UI', 12, 'bold'), fg='#2c3e50').pack(anchor='w')
        
        payment_method = tk.StringVar(value="efectivo")
        methods_frame = tk.Frame(payment_frame, bg='white')
        methods_frame.pack(anchor='w', pady=5)
        
        tk.Radiobutton(methods_frame, text="💵 Efectivo", variable=payment_method, 
                      value="efectivo", bg='white', fg='#2c3e50', 
                      font=('Segoe UI', 11)).pack(side='left', padx=10)
        tk.Radiobutton(methods_frame, text="💳 Tarjeta", variable=payment_method, 
                      value="tarjeta", bg='white', fg='#2c3e50', 
                      font=('Segoe UI', 11)).pack(side='left', padx=10)
        tk.Radiobutton(methods_frame, text="📱 Sinpe", variable=payment_method, 
                      value="sinpe", bg='white', fg='#2c3e50', 
                      font=('Segoe UI', 11)).pack(side='left', padx=10)
        
        # Función para cerrar cuenta
        def finalize_closure():
            try:
                total_amount = float(total_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Ingresa un monto válido")
                return
            
            if total_amount < 0:
                messagebox.showerror("Error", "El monto no puede ser negativo")
                return
            
            # Confirmar cierre
            if messagebox.askyesno("Confirmar Cierre", 
                                  f"¿Cerrar cuenta {account_id}?\n\n" +
                                  f"Cliente: {account_data['client']}\n" +
                                  f"Total: ₡{total_amount:,.2f}\n" +
                                  f"Método: {payment_method.get().title()}"):
                
                # Actualizar datos de cuenta
                account_data['status'] = 'cerrada'
                account_data['closed_at'] = datetime.now()
                account_data['total_amount'] = total_amount
                account_data['payment_method'] = payment_method.get()
                
                # Mover a historial
                self.move_to_history(account_id, account_data)
                
                # Eliminar de cuentas activas
                del self.active_accounts[account_id]
                
                # Guardar cambios
                self.save_accounts()
                
                # Actualizar display
                self.update_accounts_display()
                
                messagebox.showinfo("✅ Cuenta Cerrada", 
                                  f"Cuenta {account_id} cerrada exitosamente\n" +
                                  f"Total: ₡{total_amount:,.2f}")
                
                close_window.destroy()
        
        # Botones
        button_frame = tk.Frame(close_window, bg='white')
        button_frame.pack(fill='x', padx=30, pady=20)
        
        tk.Button(button_frame, text="✅ Cerrar Cuenta", 
                 font=('Segoe UI', 12, 'bold'), bg='#e74c3c', fg='white',
                 relief='flat', padx=20, pady=10, cursor='hand2',
                 command=finalize_closure).pack(side='left', padx=10)
        
        tk.Button(button_frame, text="❌ Cancelar", 
                 font=('Segoe UI', 12, 'bold'), bg='#95a5a6', fg='white',
                 relief='flat', padx=20, pady=10, cursor='hand2',
                 command=close_window.destroy).pack(side='left', padx=10)
    
    def show_history(self):
        """Muestra el historial de cuentas cerradas"""
        history_window = tk.Toplevel(self.window)
        history_window.title("📋 Historial de Cuentas")
        history_window.geometry("800x600")
        history_window.transient(self.window)
        history_window.grab_set()
        history_window.configure(bg='white')
        
        # Header
        header_frame = tk.Frame(history_window, bg='#3498db', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="📋 HISTORIAL DE CUENTAS", 
                font=('Segoe UI', 16, 'bold'), bg='#3498db', fg='white').pack(pady=15)
        
        # Treeview para historial
        hist_frame = tk.Frame(history_window, bg='white')
        hist_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        columns = ('ID', 'Cliente', 'Fecha', 'Total', 'Método Pago')
        history_tree = ttk.Treeview(hist_frame, columns=columns, show='headings')
        
        # Configurar encabezados
        for col in columns:
            history_tree.heading(col, text=col)
            history_tree.column(col, width=150)
        
        # Scrollbar
        hist_scrollbar = ttk.Scrollbar(hist_frame, orient="vertical", command=history_tree.yview)
        history_tree.configure(yscrollcommand=hist_scrollbar.set)
        
        history_tree.pack(side="left", fill="both", expand=True)
        hist_scrollbar.pack(side="right", fill="y")
        
        # Cargar historial
        self.load_history_data(history_tree)
        
        # Botón cerrar
        tk.Button(history_window, text="❌ Cerrar", 
                 font=('Segoe UI', 12, 'bold'), bg='#95a5a6', fg='white',
                 relief='flat', padx=20, pady=10, cursor='hand2',
                 command=history_window.destroy).pack(pady=20)
    
    def update_accounts_display(self):
        """Actualiza la visualización de cuentas activas"""
        # Limpiar treeview
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)
        
        # Agregar cuentas activas
        for account_id, data in self.active_accounts.items():
            time_active = datetime.now() - data['opened_at']
            hours, remainder = divmod(time_active.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            time_str = f"{hours}h {minutes}m"
            
            self.accounts_tree.insert('', 'end', values=(
                account_id,
                data['client'],
                data['location'],
                data['opened_at'].strftime('%H:%M'),
                time_str,
                data['status'].upper()
            ))
        
        # Actualizar estadísticas
        active_count = len(self.active_accounts)
        total_day = self.calculate_daily_total()
        current_time = datetime.now().strftime('%H:%M:%S')
        
        self.stats_label.config(
            text=f"🏪 Cuentas Activas: {active_count} | 💰 Total del Día: ₡{total_day:,.2f} | 🕒 {current_time}"
        )
    
    def auto_update_display(self):
        """Actualización automática cada 30 segundos"""
        self.update_accounts_display()
        self.window.after(30000, self.auto_update_display)
    
    def save_accounts(self):
        """Guarda las cuentas activas en archivo"""
        try:
            accounts_data = {}
            for account_id, data in self.active_accounts.items():
                # Convertir datetime a string para JSON
                data_copy = data.copy()
                data_copy['opened_at'] = data['opened_at'].isoformat()
                accounts_data[account_id] = data_copy
            
            with open("active_accounts.json", "w", encoding="utf-8") as f:
                json.dump({
                    "accounts": accounts_data,
                    "counter": self.account_counter
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando cuentas: {e}")
    
    def load_accounts(self):
        """Carga las cuentas activas desde archivo"""
        try:
            if os.path.exists("active_accounts.json"):
                with open("active_accounts.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                self.account_counter = data.get("counter", 1)
                
                for account_id, account_data in data.get("accounts", {}).items():
                    # Convertir string de vuelta a datetime
                    account_data['opened_at'] = datetime.fromisoformat(account_data['opened_at'])
                    self.active_accounts[account_id] = account_data
        except Exception as e:
            print(f"Error cargando cuentas: {e}")
    
    def move_to_history(self, account_id, account_data):
        """Mueve una cuenta al historial"""
        try:
            # Preparar datos para historial
            history_data = account_data.copy()
            history_data['opened_at'] = account_data['opened_at'].isoformat()
            history_data['closed_at'] = account_data['closed_at'].isoformat()
            
            # Cargar historial existente
            history = []
            if os.path.exists("accounts_history.json"):
                with open("accounts_history.json", "r", encoding="utf-8") as f:
                    history = json.load(f)
            
            # Agregar nueva entrada
            history.append(history_data)
            
            # Guardar historial actualizado
            with open("accounts_history.json", "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando en historial: {e}")
    
    def load_history_data(self, tree):
        """Carga datos del historial en el treeview"""
        try:
            if os.path.exists("accounts_history.json"):
                with open("accounts_history.json", "r", encoding="utf-8") as f:
                    history = json.load(f)
                
                # Mostrar últimas 50 entradas
                for entry in history[-50:]:
                    closed_date = datetime.fromisoformat(entry['closed_at'])
                    tree.insert('', 0, values=(  # Insert at top (reverse order)
                        entry['id'],
                        entry['client'],
                        closed_date.strftime('%d/%m/%Y %H:%M'),
                        f"₡{entry['total_amount']:,.2f}",
                        entry['payment_method'].title()
                    ))
        except Exception as e:
            print(f"Error cargando historial: {e}")
    
    def calculate_daily_total(self):
        """Calcula el total del día desde el historial"""
        total = 0.0
        try:
            if os.path.exists("accounts_history.json"):
                with open("accounts_history.json", "r", encoding="utf-8") as f:
                    history = json.load(f)
                
                today = datetime.now().date()
                for entry in history:
                    closed_date = datetime.fromisoformat(entry['closed_at']).date()
                    if closed_date == today:
                        total += entry['total_amount']
        except Exception as e:
            print(f"Error calculando total diario: {e}")
        
        return total
    
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
    app = SimpleAccountManager()
    app.window.mainloop()
