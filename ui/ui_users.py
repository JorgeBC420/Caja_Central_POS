import tkinter as tk
from tkinter import messagebox, ttk
from modules.api.auth import login_user
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.api.database import create_tables
from modules.invoicing.export import export_to_excel
from modules.invoicing.sales import create_new_sale
from modules.invoicing.history import show_user_history

class LoginFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=20)
        self.controller = controller

        ttk.Label(self, text="Usuario:").grid(row=0, column=0, pady=5)
        self.entry_user = ttk.Entry(self)
        self.entry_user.grid(row=0, column=1, pady=5)

        ttk.Label(self, text="Contraseña:").grid(row=1, column=0, pady=5)
        self.entry_pass = ttk.Entry(self, show="*")
        self.entry_pass.grid(row=1, column=1, pady=5)

        login_btn = ttk.Button(self, text="Iniciar sesión", command=self.login)
        login_btn.grid(row=2, column=0, columnspan=2, pady=10)

    def login(self):
        username = self.entry_user.get()
        password = self.entry_pass.get()
        user = login_user(username, password)

        if user:
            self.controller.show_main(user)
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")

class MainFrame(ttk.Frame):
    def __init__(self, parent, controller, user):
        super().__init__(parent, padding=20)
        self.controller = controller
        self.user = user

        ttk.Label(self, text=f"Bienvenido {user['username']} ({user['role']})").pack(pady=10)
        menu_frame = ttk.Frame(self)
        menu_frame.pack(pady=10)

        self.sale_btn = ttk.Button(menu_frame, text="Nueva Venta", command=self.new_sale)
        self.sale_btn.grid(row=0, column=0, padx=10, pady=5)

        self.history_btn = ttk.Button(menu_frame, text="Historial", command=self.view_history)
        self.history_btn.grid(row=1, column=0, padx=10, pady=5)

        self.export_btn = ttk.Button(menu_frame, text="Exportar a Excel", command=self.export_excel)
        self.export_btn.grid(row=2, column=0, padx=10, pady=5)

        self.logout_btn = ttk.Button(menu_frame, text="Cerrar sesión", command=self.logout)
        self.logout_btn.grid(row=3, column=0, padx=10, pady=5)

        if user['role'] != 'admin':
            self.export_btn.state(['disabled'])

    def new_sale(self):
        create_new_sale(self.user)

    def view_history(self):
        show_user_history(self.user)

    def export_excel(self):
        export_to_excel(self.user)

    def logout(self):
        self.controller.show_login()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Caja POS")
        self.geometry("400x300")
        self.resizable(False, False)
        self.center_window()

        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        self.show_login()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def show_login(self):
        frame = LoginFrame(self.container, self)
        self._show_frame(frame)

    def show_main(self, user):
        frame = MainFrame(self.container, self, user)
        self._show_frame(frame)

    def _show_frame(self, frame):
        for widget in self.container.winfo_children():
            widget.destroy()
        frame.pack(fill="both", expand=True)

if __name__ == '__main__':
    create_tables()
    app = App()
    app.mainloop()