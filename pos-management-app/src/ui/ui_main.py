from tkinter import ttk, messagebox
import tkinter as tk
from src.config import settings
from src.db import models
from src.audit.movement_audit import MovementAudit
from src.roles.roles import RoleManager
from src.notifications.email_notifications import EmailNotifier

class InterfazPrincipal(tk.Toplevel):
    def __init__(self, parent, sistema_caja_ref):
        super().__init__(parent)
        self.parent = parent
        self.sistema = sistema_caja_ref
        self.title("Sistema de Gestión POS")
        self.geometry("800x600")
        self.status_var = tk.StringVar(value="Listo.")
        self._crear_menu_principal()
        self._crear_notebook_principal()
        self._crear_barra_estado()
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar_ventana_principal)

    def _crear_menu_principal(self):
        menu_principal = tk.Menu(self)
        self.config(menu=menu_principal)

        menu_archivo = tk.Menu(menu_principal, tearoff=0)
        menu_archivo.add_command(label="Backup DB", command=self._backup_db)
        menu_archivo.add_command(label="Restore DB", command=self._restore_db)
        menu_archivo.add_separator()
        menu_archivo.add_command(label="Salir", command=self._al_cerrar_ventana_principal)
        menu_principal.add_cascade(label="Archivo", menu=menu_archivo)

        menu_roles = tk.Menu(menu_principal, tearoff=0)
        menu_roles.add_command(label="Gestionar Roles", command=self._gestionar_roles)
        menu_principal.add_cascade(label="Roles", menu=menu_roles)

        menu_notificaciones = tk.Menu(menu_principal, tearoff=0)
        menu_notificaciones.add_command(label="Configuración de Email", command=self._configurar_email)
        menu_principal.add_cascade(label="Notificaciones", menu=menu_notificaciones)

    def _crear_barra_estado(self):
        barra_estado = ttk.Frame(self)
        barra_estado.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(barra_estado, textvariable=self.status_var).pack(side=tk.LEFT, padx=5, pady=5)

    def _crear_notebook_principal(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.pestanas = {}
        tabs_config = [
            ('Ventas', self._crear_contenido_pestana_ventas),
            ('Clientes', self._crear_contenido_pestana_clientes),
            ('Productos', self._crear_contenido_pestana_productos),
            ('Inventario', self._crear_contenido_pestana_inventario),
            ('Promociones', self._crear_contenido_pestana_promociones),
            ('Descuentos', self._crear_contenido_pestana_descuentos),
            ('Devoluciones', self._crear_contenido_pestana_devoluciones),
            ('Reportes', self._crear_contenido_pestana_reportes),
        ]
        for name, creator_func in tabs_config:
            frame = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(frame, text=name)
            self.pestanas[name] = frame
            creator_func(frame)

    def _crear_contenido_pestana_ventas(self, frame_ventas):
        ttk.Label(frame_ventas, text="Aquí va la interfaz de venta principal.").pack()

    def _crear_contenido_pestana_clientes(self, frame_clientes):
        ttk.Label(frame_clientes, text="Aquí va la gestión de clientes.").pack()

    def _crear_contenido_pestana_productos(self, frame_productos):
        ttk.Label(frame_productos, text="Aquí va la gestión de productos.").pack()

    def _crear_contenido_pestana_inventario(self, frame_inventario):
        ttk.Label(frame_inventario, text="Aquí va la gestión de inventario.").pack()

    def _crear_contenido_pestana_promociones(self, frame_promociones):
        ttk.Label(frame_promociones, text="Aquí va la gestión de promociones.").pack()

    def _crear_contenido_pestana_descuentos(self, frame_descuentos):
        ttk.Label(frame_descuentos, text="Aquí va la gestión de descuentos.").pack()

    def _crear_contenido_pestana_devoluciones(self, frame_devoluciones):
        ttk.Label(frame_devoluciones, text="Aquí va la gestión de devoluciones.").pack()

    def _crear_contenido_pestana_reportes(self, frame_reportes):
        ttk.Label(frame_reportes, text="Aquí van los reportes.").pack()

    def _al_cerrar_ventana_principal(self):
        if messagebox.askokcancel("Salir", "¿Está seguro que desea salir?", parent=self):
            self.parent.destroy()

    def _backup_db(self):
        # Implementar lógica de respaldo de base de datos
        pass

    def _restore_db(self):
        # Implementar lógica de restauración de base de datos
        pass

    def _gestionar_roles(self):
        # Implementar lógica para gestionar roles
        pass

    def _configurar_email(self):
        # Implementar lógica para configurar email
        pass

    def mostrar_mensaje_estado(self, mensaje, tiempo=3000):
        self.status_var.set(mensaje)
        self.after(tiempo, lambda: self.status_var.set("Listo."))