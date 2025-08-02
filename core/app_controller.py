import sys
import os
import tkinter as tk
from ui.ui_login import LoginUI
from ui.ui_main import InterfazPrincipal
from core.sistema import SistemaCaja
from core.database import DatabaseManager
from core.config import cargar_config_tienda

class AppController:
    def __init__(self):
        self.root_app_tk = tk.Tk()
        self.root_app_tk.withdraw()  # Raíz principal oculta
        self.db = DatabaseManager()
        self.db.inicializar_tablas()  # Verificar que este método existe
        self.config_tienda = cargar_config_tienda()
        self.sistema_caja = SistemaCaja()
        self.sistema_caja.db = self.db  # Asignar la instancia de DatabaseManager al sistema
        self.sistema_caja.config = self.config_tienda  # Asignar configuración
        self.ventana_actual = None

    def mostrar_ventana_login(self):
        if self.ventana_actual and hasattr(self.ventana_actual, 'window') and self.ventana_actual.window.winfo_exists():
            self.ventana_actual.window.destroy()
        self.ventana_actual = LoginUI(self.root_app_tk, self.al_completar_login)
        self.ventana_actual.create_login_window()

    def al_completar_login(self):
        if self.ventana_actual and hasattr(self.ventana_actual, 'window') and self.ventana_actual.window.winfo_exists():
            self.ventana_actual.window.destroy()
        self.ventana_actual = InterfazPrincipal(self.root_app_tk, self.sistema_caja)

    def iniciar_app(self):
        self.mostrar_ventana_login()

if __name__ == "__main__":
    app_controller = AppController()
    app_controller.iniciar_app()
    app_controller.root_app_tk.mainloop()