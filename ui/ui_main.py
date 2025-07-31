import tkinter as tk
from tkinter import ttk, messagebox
from core.printer_utils import imprimir_ticket
import datetime
import traceback
from PIL import Image, ImageTk  # Asegúrate de tener pillow instalado

class InterfazPrincipal(tk.Toplevel):
    def __init__(self, parent, sistema_caja_ref):
        super().__init__(parent)
        self.parent = parent
        self.sistema = sistema_caja_ref

        # Construcción de la interfaz principal
        self._crear_menu_principal()
        self._crear_notebook_principal()
        self._crear_barra_estado()
        self._configurar_atajos()
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar_ventana_principal)
        self.status_var.set("Listo.")

        # Menú Archivo
        menu_archivo = tk.Menu(self.menu_principal, tearoff=0)
        menu_archivo.add_command(label="Cerrar sesión", command=self.sistema.cerrar_sesion)
        menu_archivo.add_command(label="Salir", command=self._al_cerrar_ventana_principal)
        self.menu_principal.add_cascade(label="Archivo", menu=menu_archivo)

        # Menú Ayuda
        menu_ayuda = tk.Menu(self.menu_principal, tearoff=0)
        menu_ayuda.add_command(label="Acerca de", command=self.mostrar_acerca_de)
        self.menu_principal.add_cascade(label="Ayuda", menu=menu_ayuda)

    # Métodos utilitarios y de construcción de interfaz
    def _crear_menu_principal(self):
        self.menu_principal = tk.Menu(self)
        self.config(menu=self.menu_principal)

    def _crear_barra_estado(self):
        self.status_var = tk.StringVar(value="Listo.")
        barra_estado = ttk.Label(self, textvariable=self.status_var, anchor='w', relief=tk.SUNKEN, padding=5)
        barra_estado.pack(side=tk.BOTTOM, fill=tk.X)

    def _configurar_atajos(self):
        atajos = {
            "<F1>": lambda e: self.notebook.select(self.pestanas['Ventas']),
            "<F2>": lambda e: self.notebook.select(self.pestanas['Clientes']),
            "<F3>": lambda e: self.notebook.select(self.pestanas['Productos']),
            "<F4>": lambda e: self.notebook.select(self.pestanas['Inventario']),
            "<F5>": self.cambiar_producto_seleccionado,
            "<F6>": self.marcar_venta_pendiente,
            "<F7>": self.registrar_entrada_inventario,
            "<F8>": self.registrar_salida_inventario,
            "<F10>": self.buscar_producto,
            "<F11>": self.aplicar_mayoreo,
            "<F12>": self.finalizar_venta_ui,
            "<Delete>": self.quitar_item_venta_ui,
        }
        for atajo, comando in atajos.items():
            self.bind(atajo, comando)

    # --- CRUD TAB HELPER ---
    def _crear_crud_tab(self, parent_frame, entity_name, columns, add_cmd, delete_cmd, edit_cmd, update_cmd_ref):
        """
        Crea un layout estándar CRUD con botones y un Treeview.
        """
        button_frame = ttk.Frame(parent_frame)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(button_frame, text=f"Agregar {entity_name}", command=add_cmd).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(button_frame, text=f"Eliminar {entity_name}", command=delete_cmd).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(button_frame, text=f"Editar {entity_name}", command=edit_cmd).pack(side=tk.LEFT, padx=5, pady=5)

        tree = ttk.Treeview(parent_frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col.replace('_', ' ').capitalize())
            if col == "id" or col.endswith("id"):
                tree.column(col, width=50, anchor=tk.CENTER)
            else:
                tree.column(col, width=150, anchor=tk.W)
        tree.pack(fill=tk.BOTH, expand=True, pady=5)

        setattr(self, f"tree_{entity_name.lower()}", tree)
        update_cmd_ref()

    # --- USO DEL CRUD TAB EN LAS PESTAÑAS ---
    def _crear_contenido_pestana_promociones(self, frame_promociones):
        self._crear_crud_tab(
            frame_promociones,
            "promocion",
            ("id", "nombre", "descripcion", "fecha_inicio", "fecha_fin", "tipo", "valor", "activo"),
            self.agregar_promocion_ui,
            self.eliminar_promocion_ui,
            self.editar_promocion_ui,
            self.actualizar_treeview_promocion
        )

    def _crear_contenido_pestana_descuentos(self, frame_descuentos):
        self._crear_crud_tab(
            frame_descuentos,
            "descuento",
            ("id", "nombre", "tipo", "valor", "descripcion", "activo"),
            self.agregar_descuento_ui,
            self.eliminar_descuento_ui,
            self.editar_descuento_ui,
            self.actualizar_treeview_descuento
        )

    def _crear_contenido_pestana_devoluciones(self, frame_devoluciones):
        self._crear_crud_tab(
            frame_devoluciones,
            "devolucion",
            ("id", "venta_id", "fecha", "motivo", "monto", "usuario_id"),
            self.agregar_devolucion_ui,
            self.eliminar_devolucion_ui,
            self.editar_devolucion_ui,
            self.actualizar_treeview_devolucion
        )

    def _crear_contenido_pestana_clientes(self, frame_clientes):
        self._crear_crud_tab(
            frame_clientes,
            "cliente",
            ("id", "nombre", "cedula", "telefono"),
            self.agregar_cliente_ui,
            self.eliminar_cliente_ui,
            self.editar_cliente_ui,
            self.actualizar_treeview_cliente
        )

    def _crear_contenido_pestana_productos(self, frame_productos):
        self._crear_crud_tab(
            frame_productos,
            "producto",
            ("id", "codigo", "nombre", "precio", "stock"),
            self.agregar_producto_ui,
            self.eliminar_producto_ui,
            self.editar_producto_ui,
            self.actualizar_treeview_producto
        )

    def _crear_contenido_pestana_inventario(self, frame_inventario):
        ttk.Label(frame_inventario, text="Aquí va la gestión de inventario.").pack()

    def _crear_contenido_pestana_reportes(self, frame_reportes):
        ttk.Label(frame_reportes, text="Aquí van los reportes.").pack()

    def mostrar_acerca_de(self):
        messagebox.showinfo("Acerca de", "Sistema de Caja POS\nVersión 1.0", parent=self)

    # --- MÉTODOS DE ACTUALIZACIÓN DE TREEVIEW ---
    def actualizar_treeview_promocion(self):
        tree = getattr(self, "tree_promocion", None)
        if tree:
            for row in tree.get_children():
                tree.delete(row)
            promociones = self.sistema.db.obtener_promociones(solo_activos=False) if hasattr(self.sistema.db, 'obtener_promociones') else []
            for promo in promociones:
                tree.insert('', tk.END, values=promo)

    def actualizar_treeview_descuento(self):
        tree = getattr(self, "tree_descuento", None)
        if tree:
            for row in tree.get_children():
                tree.delete(row)
            descuentos = self.sistema.db.obtener_descuentos(solo_activos=False) if hasattr(self.sistema.db, 'obtener_descuentos') else []
            for descuento in descuentos:
                tree.insert('', tk.END, values=descuento)

    def actualizar_treeview_devolucion(self):
        tree = getattr(self, "tree_devolucion", None)
        if tree:
            for row in tree.get_children():
                tree.delete(row)
            devoluciones = self.sistema.db.obtener_devoluciones() if hasattr(self.sistema.db, 'obtener_devoluciones') else []
            for devolucion in devoluciones:
                tree.insert('', tk.END, values=devolucion)

    def actualizar_treeview_cliente(self):
        tree = getattr(self, "tree_cliente", None)
        if tree:
            for row in tree.get_children():
                tree.delete(row)
            clientes = self.sistema.db.obtener_clientes() if hasattr(self.sistema.db, 'obtener_clientes') else []
            for cliente in clientes:
                tree.insert('', tk.END, values=cliente)

    def actualizar_treeview_producto(self):
        tree = getattr(self, "tree_producto", None)
        if tree:
            for row in tree.get_children():
                tree.delete(row)
            productos = self.sistema.db.obtener_productos() if hasattr(self.sistema.db, 'obtener_productos') else []
            for producto in productos:
                tree.insert('', tk.END, values=producto)

    def actualizar_info_venta_ui(self):
        pass  # Implementa aquí la actualización de la información de la venta en la UI

    def imprimir_ticket_fisico(self, datos_venta):
        imprimir_ticket(datos_venta)

    # --- CRUD MÉTODOS PARA PROMOCIONES ---
    def agregar_promocion_ui(self):
        ventana = tk.Toplevel(self)
        ventana.title("Agregar Promoción")
        ventana.transient(self)
        ventana.grab_set()

        campos = [
            ("Nombre", "nombre"),
            ("Descripción", "descripcion"),
            ("Fecha inicio (YYYY-MM-DD)", "fecha_inicio"),
            ("Fecha fin (YYYY-MM-DD)", "fecha_fin"),
            ("Tipo", "tipo"),
            ("Valor", "valor"),
        ]
        entradas = {}
        for i, (label, key) in enumerate(campos):
            ttk.Label(ventana, text=label + ":").grid(row=i, column=0, padx=5, pady=5)
            entry = ttk.Entry(ventana)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entradas[key] = entry

        activo_var = tk.IntVar(value=1)
        ttk.Checkbutton(ventana, text="Activo", variable=activo_var).grid(row=len(campos), column=0, columnspan=2)

        def guardar():
            try:
                valor = float(entradas["valor"].get())
            except ValueError:
                messagebox.showerror("Error", "El valor debe ser numérico.", parent=ventana)
                return
            promocion = {k: entradas[k].get() for _, k in campos}
            promocion["valor"] = valor
            promocion["activo"] = activo_var.get()
            self.sistema.db.agregar_promocion(promocion)
            self.actualizar_treeview_promocion()
            messagebox.showinfo("Éxito", "Promoción agregada correctamente.", parent=ventana)
            ventana.destroy()

        ttk.Button(ventana, text="Guardar", command=guardar).grid(row=len(campos)+1, column=0, columnspan=2, pady=10)

    def eliminar_promocion_ui(self):
        tree = getattr(self, "tree_promocion", None)
        seleccion = tree.selection() if tree else []
        if not seleccion:
            messagebox.showwarning("Selecciona una promoción", "Debes seleccionar una promoción para eliminar.", parent=self)
            return
        item = tree.item(seleccion[0])
        promo_id = item['values'][0]
        if messagebox.askyesno("Confirmar", "¿Eliminar la promoción seleccionada?", parent=self):
            self.sistema.db.eliminar_promocion(promo_id)
            self.actualizar_treeview_promocion()

    def editar_promocion_ui(self):
        tree = getattr(self, "tree_promocion", None)
        seleccion = tree.selection() if tree else []
        if not seleccion:
            messagebox.showwarning("Selecciona una promoción", "Debes seleccionar una promoción para editar.", parent=self)
            return
        item = tree.item(seleccion[0])
        promo_id = item['values'][0]
        datos = item['values']

        ventana = tk.Toplevel(self)
        ventana.title("Editar Promoción")
        ventana.transient(self)
        ventana.grab_set()

        campos = [
            ("Nombre", "nombre", datos[1]),
            ("Descripción", "descripcion", datos[2]),
            ("Fecha inicio (YYYY-MM-DD)", "fecha_inicio", datos[3]),
            ("Fecha fin (YYYY-MM-DD)", "fecha_fin", datos[4]),
            ("Tipo", "tipo", datos[5]),
            ("Valor", "valor", datos[6]),
        ]
        entradas = {}
        for i, (label, key, valor) in enumerate(campos):
            ttk.Label(ventana, text=label + ":").grid(row=i, column=0, padx=5, pady=5)
            entry = ttk.Entry(ventana)
            entry.insert(0, valor)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entradas[key] = entry

        activo_var = tk.IntVar(value=datos[7])
        ttk.Checkbutton(ventana, text="Activo", variable=activo_var).grid(row=len(campos), column=0, columnspan=2)

        def guardar():
            try:
                valor = float(entradas["valor"].get())
            except ValueError:
                messagebox.showerror("Error", "El valor debe ser numérico.", parent=ventana)
                return
            campos_mod = {k: entradas[k].get() for _, k, _ in campos}
            campos_mod["valor"] = valor
            campos_mod["activo"] = activo_var.get()
            self.sistema.db.modificar_promocion(promo_id, campos_mod)
            self.actualizar_treeview_promocion()
            messagebox.showinfo("Éxito", "Promoción editada correctamente.", parent=ventana)
            ventana.destroy()

        ttk.Button(ventana, text="Guardar", command=guardar).grid(row=len(campos)+1, column=0, columnspan=2, pady=10)

    # --- CRUD MÉTODOS PARA DESCUENTOS ---
    def agregar_descuento_ui(self):
        ventana = tk.Toplevel(self)
        ventana.title("Agregar Descuento")
        ventana.transient(self)
        ventana.grab_set()

        campos = [
            ("Nombre", "nombre"),
            ("Tipo (porcentaje/monto)", "tipo"),
            ("Valor", "valor"),
            ("Descripción", "descripcion"),
        ]
        entradas = {}
        for i, (label, key) in enumerate(campos):
            ttk.Label(ventana, text=label + ":").grid(row=i, column=0, padx=5, pady=5)
            entry = ttk.Entry(ventana)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entradas[key] = entry

        activo_var = tk.IntVar(value=1)
        ttk.Checkbutton(ventana, text="Activo", variable=activo_var).grid(row=len(campos), column=0, columnspan=2)

        def guardar():
            try:
                valor = float(entradas["valor"].get())
            except ValueError:
                messagebox.showerror("Error", "El valor debe ser numérico.", parent=ventana)
                return
            descuento = {k: entradas[k].get() for _, k in campos}
            descuento["valor"] = valor
            descuento["activo"] = activo_var.get()
            self.sistema.db.agregar_descuento(descuento)
            self.actualizar_treeview_descuento()
            messagebox.showinfo("Éxito", "Descuento agregado correctamente.", parent=ventana)
            ventana.destroy()

        ttk.Button(ventana, text="Guardar", command=guardar).grid(row=len(campos)+1, column=0, columnspan=2, pady=10)

    def eliminar_descuento_ui(self):
        tree = getattr(self, "tree_descuento", None)
        seleccion = tree.selection() if tree else []
        if not seleccion:
            messagebox.showwarning("Selecciona un descuento", "Debes seleccionar un descuento para eliminar.", parent=self)
            return
        item = tree.item(seleccion[0])
        descuento_id = item['values'][0]
        if messagebox.askyesno("Confirmar", "¿Eliminar el descuento seleccionado?", parent=self):
            self.sistema.db.eliminar_descuento(descuento_id)
            self.actualizar_treeview_descuento()

    def editar_descuento_ui(self):
        tree = getattr(self, "tree_descuento", None)
        seleccion = tree.selection() if tree else []
        if not seleccion:
            messagebox.showwarning("Selecciona un descuento", "Debes seleccionar un descuento para editar.", parent=self)
            return
        item = tree.item(seleccion[0])
        descuento_id = item['values'][0]
        datos = item['values']

        ventana = tk.Toplevel(self)
        ventana.title("Editar Descuento")
        ventana.transient(self)
        ventana.grab_set()

        campos = [
            ("Nombre", "nombre", datos[1]),
            ("Tipo (porcentaje/monto)", "tipo", datos[2]),
            ("Valor", "valor", datos[3]),
            ("Descripción", "descripcion", datos[4]),
        ]
        entradas = {}
        for i, (label, key, valor) in enumerate(campos):
            ttk.Label(ventana, text=label + ":").grid(row=i, column=0, padx=5, pady=5)
            entry = ttk.Entry(ventana)
            entry.insert(0, valor)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entradas[key] = entry

        activo_var = tk.IntVar(value=datos[5])
        ttk.Checkbutton(ventana, text="Activo", variable=activo_var).grid(row=len(campos), column=0, columnspan=2)

        def guardar():
            try:
                valor = float(entradas["valor"].get())
            except ValueError:
                messagebox.showerror("Error", "El valor debe ser numérico.", parent=ventana)
                return
            campos_mod = {k: entradas[k].get() for _, k, _ in campos}
            campos_mod["valor"] = valor
            campos_mod["activo"] = activo_var.get()
            self.sistema.db.modificar_descuento(descuento_id, campos_mod)
            self.actualizar_treeview_descuento()
            messagebox.showinfo("Éxito", "Descuento editado correctamente.", parent=ventana)
            ventana.destroy()

        ttk.Button(ventana, text="Guardar", command=guardar).grid(row=len(campos)+1, column=0, columnspan=2, pady=10)

    # --- CRUD MÉTODOS PARA DEVOLUCIONES ---
    def agregar_devolucion_ui(self):
        ventana = tk.Toplevel(self)
        ventana.title("Agregar Devolución")
        ventana.transient(self)
        ventana.grab_set()

        ttk.Label(ventana, text="Venta ID:").grid(row=0, column=0, padx=5, pady=5)
        entry_venta_id = ttk.Entry(ventana)
        entry_venta_id.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(ventana, text="Fecha (YYYY-MM-DD):").grid(row=1, column=0, padx=5, pady=5)
        entry_fecha = ttk.Entry(ventana)
        entry_fecha.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        entry_fecha.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(ventana, text="Motivo:").grid(row=2, column=0, padx=5, pady=5)
        entry_motivo = ttk.Entry(ventana)
        entry_motivo.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(ventana, text="Monto:").grid(row=3, column=0, padx=5, pady=5)
        entry_monto = ttk.Entry(ventana)
        entry_monto.grid(row=3, column=1, padx=5, pady=5)

        def guardar():
            try:
                devolucion = {
                    'venta_id': int(entry_venta_id.get()),
                    'fecha': entry_fecha.get(),
                    'motivo': entry_motivo.get(),
                    'monto': float(entry_monto.get()),
                    'usuario_id': self.sistema.usuario_actual.id
                }
                self.sistema.db.agregar_devolucion(devolucion)
                self.actualizar_treeview_devolucion()
                messagebox.showinfo("Éxito", "Devolución agregada correctamente.", parent=ventana)
                ventana.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Datos inválidos: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(row=4, column=0, columnspan=2, pady=10)

    def eliminar_devolucion_ui(self):
        tree = getattr(self, "tree_devolucion", None)
        seleccion = tree.selection() if tree else []
        if not seleccion:
            messagebox.showwarning("Selecciona una devolución", "Debes seleccionar una devolución para eliminar.", parent=self)
            return
        item = tree.item(seleccion[0])
        devolucion_id = item['values'][0]
        if messagebox.askyesno("Confirmar", "¿Eliminar la devolución seleccionada?", parent=self):
            self.sistema.db.eliminar_devolucion(devolucion_id)
            self.actualizar_treeview_devolucion()

    def editar_devolucion_ui(self):
        tree = getattr(self, "tree_devolucion", None)
        seleccion = tree.selection() if tree else []
        if not seleccion:
            messagebox.showwarning("Selecciona una devolución", "Debes seleccionar una devolución para editar.", parent=self)
            return
        item = tree.item(seleccion[0])
        devolucion_id = item['values'][0]
        datos = item['values']

        ventana = tk.Toplevel(self)
        ventana.title("Editar Devolución")
        ventana.transient(self)
        ventana.grab_set()

        ttk.Label(ventana, text="Motivo:").grid(row=0, column=0, padx=5, pady=5)
        entry_motivo = ttk.Entry(ventana)
        entry_motivo.insert(0, datos[3])
        entry_motivo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(ventana, text="Monto:").grid(row=1, column=0, padx=5, pady=5)
        entry_monto = ttk.Entry(ventana)
        entry_monto.insert(0, datos[4])
        entry_monto.grid(row=1, column=1, padx=5, pady=5)

        def guardar():
            try:
                campos = {
                    'motivo': entry_motivo.get(),
                    'monto': float(entry_monto.get())
                }
                self.sistema.db.modificar_devolucion(devolucion_id, campos)
                self.actualizar_treeview_devolucion()
                messagebox.showinfo("Éxito", "Devolución editada correctamente.", parent=ventana)
                ventana.destroy()
            except ValueError:
                messagebox.showerror("Error", "El monto debe ser numérico.", parent=ventana)
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(row=2, column=0, columnspan=2, pady=10)

    # --- CRUD MÉTODOS PARA CLIENTES ---
    def agregar_cliente_ui(self, event=None):
        ventana = tk.Toplevel(self)
        ventana.title("Agregar Cliente")
        ventana.transient(self)
        ventana.grab_set()

        campos = [
            ("Nombre", "nombre"),
            ("Cédula", "cedula"),
            ("Teléfono", "telefono"),
        ]
        entradas = {}
        for i, (label, key) in enumerate(campos):
            ttk.Label(ventana, text=label + ":").grid(row=i, column=0, padx=5, pady=5)
            entry = ttk.Entry(ventana)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entradas[key] = entry

        def guardar():
            try:
                cliente = {k: entradas[k].get() for _, k in campos}
                self.sistema.db.agregar_cliente(cliente)
                self.actualizar_treeview_cliente()
                messagebox.showinfo("Éxito", "Cliente agregado correctamente.", parent=ventana)
                ventana.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Datos inválidos: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(row=len(campos), column=0, columnspan=2, pady=10)

    def eliminar_cliente_ui(self):
        tree = getattr(self, "tree_cliente", None)
        seleccion = tree.selection() if tree else []
        if not seleccion:
            messagebox.showwarning("Selecciona un cliente", "Debes seleccionar un cliente para eliminar.", parent=self)
            return
        item = tree.item(seleccion[0])
        client_id = item['values'][0]
        if messagebox.askyesno("Confirmar", "¿Eliminar el cliente seleccionado?", parent=self):
            self.sistema.db.eliminar_cliente(client_id)
            self.actualizar_treeview_cliente()

    def editar_cliente_ui(self):
        tree = getattr(self, "tree_cliente", None)
        seleccion = tree.selection() if tree else []
        if not seleccion:
            messagebox.showwarning("Selecciona un cliente", "Debes seleccionar un cliente para editar.", parent=self)
            return
        item = tree.item(seleccion[0])
        client_id = item['values'][0]
        datos = item['values']

        ventana = tk.Toplevel(self)
        ventana.title("Editar Cliente")
        ventana.transient(self)
        ventana.grab_set()

        campos = [
            ("Nombre", "nombre", datos[1]),
            ("Cédula", "cedula", datos[2]),
            ("Teléfono", "telefono", datos[3]),
        ]
        entradas = {}
        for i, (label, key, valor) in enumerate(campos):
            ttk.Label(ventana, text=label + ":").grid(row=i, column=0, padx=5, pady=5)
            entry = ttk.Entry(ventana)
            entry.insert(0, valor)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entradas[key] = entry

        def guardar():
            try:
                campos_mod = {
                    "nombre": entradas["nombre"].get(),
                    "cedula": entradas["cedula"].get(),
                    "telefono": entradas["telefono"].get()
                }
                self.sistema.db.modificar_cliente(client_id, campos_mod)
                self.actualizar_treeview_cliente()
                messagebox.showinfo("Éxito", "Cliente editado correctamente.", parent=ventana)
                ventana.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(row=len(campos), column=0, columnspan=2, pady=10)

    # --- CRUD MÉTODOS PARA PRODUCTOS ---
    def agregar_producto_ui(self, event=None):
        ventana = tk.Toplevel(self)
        ventana.title("Agregar Producto")
        ventana.transient(self)
        ventana.grab_set()

        campos = [
            ("Código", "codigo"),
            ("Nombre", "nombre"),
            ("Precio", "precio"),
            ("Stock", "stock"),
        ]
        entradas = {}
        for i, (label, key) in enumerate(campos):
            ttk.Label(ventana, text=label + ":").grid(row=i, column=0, padx=5, pady=5)
            entry = ttk.Entry(ventana)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entradas[key] = entry

        def guardar():
            try:
                producto = {
                    "codigo": entradas["codigo"].get(),
                    "nombre": entradas["nombre"].get(),
                    "precio": float(entradas["precio"].get()),
                    "stock": int(entradas["stock"].get())
                }
                self.sistema.db.agregar_producto(producto)
                self.actualizar_treeview_producto()
                messagebox.showinfo("Éxito", "Producto agregado correctamente.", parent=ventana)
                ventana.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Datos inválidos: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(row=len(campos), column=0, columnspan=2, pady=10)

    def eliminar_producto_ui(self):
        tree = getattr(self, "tree_producto", None)
        seleccion = tree.selection() if tree else []
        if not seleccion:
            messagebox.showwarning("Selecciona un producto", "Debes seleccionar un producto para eliminar.", parent=self)
            return
        item = tree.item(seleccion[0])
        product_id = item['values'][0]
        if messagebox.askyesno("Confirmar", "¿Eliminar el producto seleccionado?", parent=self):
            self.sistema.db.eliminar_producto(product_id)
            self.actualizar_treeview_producto()

    def editar_producto_ui(self):
        tree = getattr(self, "tree_producto", None)
        seleccion = tree.selection() if tree else []
        if not seleccion:
            messagebox.showwarning("Selecciona un producto", "Debes seleccionar un producto para editar.", parent=self)
            return
        item = tree.item(seleccion[0])
        product_id = item['values'][0]
        datos = item['values']

        ventana = tk.Toplevel(self)
        ventana.title("Editar Producto")
        ventana.transient(self)
        ventana.grab_set()

        campos = [
            ("Código", "codigo", datos[1]),
            ("Nombre", "nombre", datos[2]),
            ("Precio", "precio", datos[3]),
            ("Stock", "stock", datos[4]),
        ]
        entradas = {}
        for i, (label, key, valor) in enumerate(campos):
            ttk.Label(ventana, text=label + ":").grid(row=i, column=0, padx=5, pady=5)
            entry = ttk.Entry(ventana)
            entry.insert(0, valor)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entradas[key] = entry

        def guardar():
            try:
                campos_mod = {
                    "codigo": entradas["codigo"].get(),
                    "nombre": entradas["nombre"].get(),
                    "precio": float(entradas["precio"].get()),
                    "stock": int(entradas["stock"].get())
                }
                self.sistema.db.modificar_producto(product_id, campos_mod)
                self.actualizar_treeview_producto()
                messagebox.showinfo("Éxito", "Producto editado correctamente.", parent=ventana)
                ventana.destroy()
            except ValueError:
                messagebox.showerror("Error", "Precio y Stock deben ser numéricos.", parent=ventana)
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(row=len(campos), column=0, columnspan=2, pady=10)

    # --- OTROS MÉTODOS ---
    def mostrar_mensaje_estado(self, mensaje, tiempo=3000):
        self.status_var.set(mensaje)
        self.after(tiempo, lambda: self.status_var.set("Listo."))

    def mostrar_error(self, mensaje):
        messagebox.showerror("Error", mensaje, parent=self)

    def finalizar_venta_ui(self, event=None):
        if not self.sistema.venta_actual['items']:
            messagebox.showwarning("Sin productos", "Agrega productos antes de finalizar la venta.", parent=self)
            return
        if not messagebox.askyesno("Confirmar", "¿Desea finalizar y cobrar la venta?", parent=self):
            return
        datos_venta_finalizada = self.sistema.generar_datos_venta_finalizada()
        self.imprimir_ticket_fisico(datos_venta_finalizada)
        self.sistema.guardar_venta(datos_venta_finalizada)
        self.sistema.nueva_venta()
        self.actualizar_treeview_producto()
        self.actualizar_info_venta_ui()
        messagebox.showinfo("Venta finalizada", "La venta se completó y el ticket fue impreso.", parent=self)

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
        # Solo los administradores pueden ver la pestaña de configuración
        if self.sistema.usuario_actual and getattr(self.sistema.usuario_actual, 'rol', '') == 'admin':
            tabs_config.append(('Configuración', self._crear_contenido_pestana_configuracion))

        for name, creator_func in tabs_config:
            frame = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(frame, text=name)
            self.pestanas[name] = frame
            creator_func(frame)

    def _crear_contenido_pestana_configuracion(self, frame_config):
        # Tasa de Dólar
        ttk.Label(frame_config, text="Tasa de dólar actual:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.tasa_dolar_var = tk.StringVar(value=str(self.sistema.config.get('tasa_dolar', '')))
        entry_tasa_dolar = ttk.Entry(frame_config, textvariable=self.tasa_dolar_var, width=15)
        entry_tasa_dolar.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        ttk.Button(frame_config, text="Guardar Tasa", command=self._guardar_tasa_dolar).grid(row=0, column=2, padx=5, pady=5)

        # Modelo de Negocio
        ttk.Label(frame_config, text="Modelo de Negocio:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.modelo_negocio_var = tk.StringVar(value=self.sistema.config.get('modelo_negocio', 'Régimen Simplificado'))
        modelo_negocio_options = ["Régimen Simplificado", "Régimen Tradicional"]
        option_menu_modelo_negocio = ttk.OptionMenu(
            frame_config,
            self.modelo_negocio_var,
            self.modelo_negocio_var.get() if self.modelo_negocio_var.get() else modelo_negocio_options[0],
            *modelo_negocio_options
        )
        option_menu_modelo_negocio.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        ttk.Button(frame_config, text="Guardar Modelo", command=self._guardar_modelo_negocio).grid(row=1, column=2, padx=5, pady=5)

        # Otros ajustes de administrador (Placeholder)
        ttk.Label(frame_config, text="--- Otros Ajustes de Administrador ---").grid(row=2, column=0, columnspan=3, pady=15, sticky='w')
        ttk.Button(frame_config, text="Gestionar Usuarios", command=self._gestionar_usuarios).grid(row=3, column=0, padx=5, pady=5, sticky='w')
        # Puedes agregar más botones de administración aquí

        # Mejorar el comportamiento de redimensionamiento
        frame_config.grid_columnconfigure(1, weight=1)

    def _guardar_tasa_dolar(self):
        try:
            nueva_tasa = float(self.tasa_dolar_var.get())
            if nueva_tasa <= 0:
                messagebox.showerror("Error", "La tasa de dólar debe ser un número positivo.", parent=self)
                return
            self.sistema.actualizar_configuracion('tasa_dolar', nueva_tasa)
            self.mostrar_mensaje_estado(f"Tasa de dólar actualizada a: {nueva_tasa}")
        except ValueError:
            messagebox.showerror("Error", "Por favor, ingresa un valor numérico válido para la tasa de dólar.", parent=self)

    def _guardar_modelo_negocio(self):
        nuevo_modelo = self.modelo_negocio_var.get()
        self.sistema.actualizar_configuracion('modelo_negocio', nuevo_modelo)
        self.mostrar_mensaje_estado(f"Modelo de negocio actualizado a: {nuevo_modelo}")

    def _gestionar_usuarios(self):
        messagebox.showinfo("Gestionar Usuarios", "Funcionalidad de gestión de usuarios en desarrollo.", parent=self)
        # Aquí podrías abrir una ventana de gestión de usuarios en el futuro

# NOTA: Asegúrate de que tu clase SistemaCaja tenga el método actualizar_configuracion(key, value)
# que actualice self.config y persista el cambio en la base de datos o

    def _crear_contenido_pestana_ventas(self, frame_ventas):
        ttk.Label(frame_ventas, text="Aquí va la interfaz de venta principal.").pack()

    def _crear_contenido_pestana_configuracion(self, frame_config):
        ttk.Label(frame_config, text="Tasa de dólar actual:").pack(side=tk.LEFT, padx=5, pady=5)
        self.tasa_dolar_var = tk.StringVar(value=str(self.sistema.config['tasa_dolar']))
        entry = ttk.Entry(frame_config, textvariable=self.tasa_dolar_var, width=10)
        entry.pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(
            frame_config,
            text="Actualizar",
            command=self._actualizar_tasa_dolar # <--- Aquí se completa el comando
        ).pack(side=tk.LEFT, padx=5, pady=5) # <--- Aquí se completa el .pack()

    def _al_cerrar_ventana_principal(self):
        if messagebox.askokcancel("Salir", "¿Está seguro que desea salir?", parent=self):
            self.parent.destroy()

    def cambiar_producto_seleccionado(self, event=None):
        # Permite editar el producto seleccionado en la venta actual
        tree = getattr(self, "tree_producto", None)
        seleccion = tree.selection() if tree else []
        if not seleccion:
            messagebox.showwarning("Selecciona un producto", "Debes seleccionar un producto para cambiar.", parent=self)
            return
        item = tree.item(seleccion[0])
        codigo = item['values'][1]
        producto = self.sistema.obtener_producto_en_venta(codigo)
        if not producto:
            messagebox.showerror("Error", "No se encontró el producto en la venta.", parent=self)
            return

        ventana = tk.Toplevel(self)
        ventana.title("Editar producto en venta")
        ventana.transient(self)
        ventana.grab_set()

        ttk.Label(ventana, text="Cantidad:").grid(row=0, column=0, padx=5, pady=5)
        cantidad_var = tk.IntVar(value=producto.get('cantidad', 1))
        entry_cantidad = ttk.Entry(ventana, textvariable=cantidad_var)
        entry_cantidad.grid(row=0, column=1, padx=5, pady=5)

        def guardar():
            try:
                nueva_cantidad = int(entry_cantidad.get())
                if nueva_cantidad <= 0:
                    raise ValueError("La cantidad debe ser mayor a cero.")
                self.sistema.cambiar_cantidad_producto_en_venta(codigo, nueva_cantidad)
                self.actualizar_info_venta_ui()
                ventana.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Cantidad inválida: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(row=1, column=0, columnspan=2, pady=10)

    def marcar_venta_pendiente(self, event=None):
        # Marca la venta actual como pendiente (por ejemplo, para guardar y continuar después)
        if not self.sistema.venta_actual['items']:
            messagebox.showwarning("Sin productos", "No hay productos en la venta para marcar como pendiente.", parent=self)
            return
        self.sistema.marcar_venta_pendiente()
        self.sistema.nueva_venta()
        self.actualizar_info_venta_ui()
        messagebox.showinfo("Venta pendiente", "La venta fue marcada como pendiente.", parent=self)

    def registrar_entrada_inventario(self, event=None):
        # Permite registrar una entrada de inventario para un producto
        tree = getattr(self, "tree_producto", None)
        seleccion = tree.selection() if tree else []
        if not seleccion:
            messagebox.showwarning("Selecciona un producto", "Debes seleccionar un producto para registrar entrada.", parent=self)
            return
        item = tree.item(seleccion[0])
        product_id = item['values'][0]
        ventana = tk.Toplevel(self)
        ventana.title("Registrar entrada de inventario")
        ventana.transient(self)
        ventana.grab_set()

        ttk.Label(ventana, text="Cantidad a ingresar:").grid(row=0, column=0, padx=5, pady=5)
        cantidad_var = tk.IntVar(value=1)
        entry_cantidad = ttk.Entry(ventana, textvariable=cantidad_var)
        entry_cantidad.grid(row=0, column=1, padx=5, pady=5)

        def guardar():
            try:
                cantidad = int(entry_cantidad.get())
                if cantidad <= 0:
                    raise ValueError("La cantidad debe ser mayor a cero.")
                self.sistema.db.registrar_entrada_inventario(product_id, cantidad)
                self.actualizar_treeview_producto()
                ventana.destroy()
                messagebox.showinfo("Entrada registrada", "Entrada de inventario registrada correctamente.", parent=self)
            except Exception as e:
                messagebox.showerror("Error", f"Cantidad inválida: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(row=1, column=0, columnspan=2, pady=10)

    def registrar_salida_inventario(self, event=None):
        # Permite registrar una salida de inventario para un producto
        tree = getattr(self, "tree_producto", None)
        seleccion = tree.selection() if tree else []
        if not seleccion:
            messagebox.showwarning("Selecciona un producto", "Debes seleccionar un producto para registrar salida.", parent=self)
            return
        item = tree.item(seleccion[0])
        product_id = item['values'][0]
        ventana = tk.Toplevel(self)
        ventana.title("Registrar salida de inventario")
        ventana.transient(self)
        ventana.grab_set()

        ttk.Label(ventana, text="Cantidad a retirar:").grid(row=0, column=0, padx=5, pady=5)
        cantidad_var = tk.IntVar(value=1)
        entry_cantidad = ttk.Entry(ventana, textvariable=cantidad_var)
        entry_cantidad.grid(row=0, column=1, padx=5, pady=5)

        def guardar():
            try:
                cantidad = int(entry_cantidad.get())
                if cantidad <= 0:
                    raise ValueError("La cantidad debe ser mayor a cero.")
                self.sistema.db.registrar_salida_inventario(product_id, cantidad)
                self.actualizar_treeview_producto()
                ventana.destroy()
                messagebox.showinfo("Salida registrada", "Salida de inventario registrada correctamente.", parent=self)
            except Exception as e:
                messagebox.showerror("Error", f"Cantidad inválida: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(row=1, column=0, columnspan=2, pady=10)

    def buscar_producto(self, event=None):
        ventana = tk.Toplevel(self)
        ventana.title("Buscar producto")
        ventana.transient(self)
        ventana.grab_set()

        ttk.Label(ventana, text="Buscar por nombre o código:").grid(row=0, column=0, padx=5, pady=5)
        busqueda_var = tk.StringVar()
        entry_busqueda = ttk.Entry(ventana, textvariable=busqueda_var)
        entry_busqueda.grid(row=0, column=1, padx=5, pady=5)

        resultado_var = tk.StringVar(value="")

        def buscar():
            texto = busqueda_var.get().strip()
            if not texto:
                resultado_var.set("⚠️ Ingrese un término de búsqueda.")
                return

            try:
                productos = self.sistema.db.buscar_productos(texto)
                if productos:
                    resultado = "\n".join(
                        [f"🛒 {p[1]} - ₡{p[2]:.2f} (Stock: {p[4]})" for p in productos]
                    )
                    resultado_var.set(resultado)
                else:
                    resultado_var.set("❌ No se encontraron productos.")
            except Exception as e:
                resultado_var.set("❌ Ocurrió un error al buscar.")
                print("Error en buscar_producto:", e)
                traceback.print_exc()

        ttk.Button(ventana, text="Buscar", command=buscar).grid(row=1, column=0, columnspan=2, pady=5)
        ttk.Label(ventana, textvariable=resultado_var, justify=tk.LEFT).grid(row=2, column=0, columnspan=2, padx=5, pady=5)

    def aplicar_mayoreo(self, event=None):
        # Aplica el precio de mayoreo al producto seleccionado en la venta
        tree = getattr(self, "tree_producto", None)
        seleccion = tree.selection() if tree else []
        if not seleccion:
            messagebox.showwarning("Selecciona un producto", "Debes seleccionar un producto para aplicar mayoreo.", parent=self)
            return
        item = tree.item(seleccion[0])
        codigo = item['values'][1]
        if self.sistema.aplicar_precio_mayoreo(codigo):
            self.actualizar_info_venta_ui()
            messagebox.showinfo("Mayoreo aplicado", "Se aplicó el precio de mayoreo.", parent=self)
        else:
            messagebox.showwarning("No aplica", "No se pudo aplicar el precio de mayoreo.", parent=self)

    def quitar_item_venta_ui(self, event=None):
        tree = getattr(self, "tree_producto", None)
        seleccion = tree.selection() if tree else []
        if not seleccion:
            messagebox.showwarning("Selecciona un producto", "Debes seleccionar un producto para quitar.", parent=self)
            return
        item = tree.item(seleccion[0])
        codigo = item['values'][1]  # Asumiendo que el código es el segundo campo
        if messagebox.askyesno("Quitar producto", f"¿Quitar el producto '{codigo}' de la venta?", parent=self):
            # Quita el producto de la venta actual usando el método del sistema
            self.sistema.quitar_producto_de_venta(codigo)
            self.actualizar_treeview_producto()
            self.actualizar_info_venta_ui()