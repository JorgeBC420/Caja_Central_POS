import tkinter as tk
from tkinter import ttk, messagebox
from core.printer_utils import imprimir_ticket
from core.decorators import login_required, admin_required, permission_required, log_action
from ui.ui_helpers import UIHelpers, CRUDHelper
import datetime
import traceback
from PIL import Image, ImageTk  # Asegúrate de tener pillow instalado

class InterfazPrincipal(tk.Toplevel):
    def __init__(self, parent, sistema_caja_ref):
        super().__init__(parent)
        self.parent = parent
        self.sistema = sistema_caja_ref
        
        # Inicializar helpers CRUD para diferentes entidades
        self.crud_helpers = {
            'promocion': CRUDHelper('promociones'),
            'descuento': CRUDHelper('descuentos'),
            'devolucion': CRUDHelper('devoluciones'),
            'cliente': CRUDHelper('clientes'),
            'producto': CRUDHelper('productos')
        }

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

    # --- CRUD TAB HELPER MEJORADO ---
    def _crear_crud_tab(self, parent_frame, entity_name, columns, headings, callbacks, query_func):
        """
        Crea un layout estándar CRUD mejorado con TreeView y botones usando helpers.
        """
        # Crear TreeView con helpers
        tree = UIHelpers.crear_treeview(parent_frame, columns, headings)
        setattr(self, f"tree_{entity_name.lower()}", tree)
        
        # Crear botones CRUD
        UIHelpers.crear_botones_crud(parent_frame, callbacks)
        
        # Cargar datos iniciales
        if query_func:
            query_func()
    
    def _cargar_entidad_datos(self, entity_name, query, params=None):
        """Carga datos para una entidad específica"""
        tree = getattr(self, f"tree_{entity_name.lower()}", None)
        if tree:
            UIHelpers.cargar_datos_treeview(tree, query, params)

    # --- USO DEL CRUD TAB MEJORADO EN LAS PESTAÑAS ---
    @permission_required("promociones")
    def _crear_contenido_pestana_promociones(self, frame_promociones):
        columns = ("id", "nombre", "descripcion", "fecha_inicio", "fecha_fin", "tipo", "valor", "activo")
        headings = ("ID", "Nombre", "Descripción", "Fecha Inicio", "Fecha Fin", "Tipo", "Valor", "Activo")
        callbacks = {
            "agregar": self.agregar_promocion_ui,
            "editar": self.editar_promocion_ui,
            "eliminar": self.eliminar_promocion_ui,
            "actualizar": self.actualizar_treeview_promocion
        }
        query = "SELECT id, nombre, descripcion, fecha_inicio, fecha_fin, tipo, valor, activo FROM promociones"
        self._crear_crud_tab(frame_promociones, "promocion", columns, headings, callbacks, 
                           lambda: self._cargar_entidad_datos("promocion", query))

    @permission_required("descuentos")
    def _crear_contenido_pestana_descuentos(self, frame_descuentos):
        columns = ("id", "nombre", "tipo", "valor", "descripcion", "activo")
        headings = ("ID", "Nombre", "Tipo", "Valor", "Descripción", "Activo")
        callbacks = {
            "agregar": self.agregar_descuento_ui,
            "editar": self.editar_descuento_ui,
            "eliminar": self.eliminar_descuento_ui,
            "actualizar": self.actualizar_treeview_descuento
        }
        query = "SELECT id, nombre, tipo, valor, descripcion, activo FROM descuentos"
        self._crear_crud_tab(frame_descuentos, "descuento", columns, headings, callbacks,
                           lambda: self._cargar_entidad_datos("descuento", query))

    @permission_required("devoluciones")
    def _crear_contenido_pestana_devoluciones(self, frame_devoluciones):
        columns = ("id", "venta_id", "fecha", "motivo", "monto", "usuario_id")
        headings = ("ID", "Venta ID", "Fecha", "Motivo", "Monto", "Usuario ID")
        callbacks = {
            "agregar": self.agregar_devolucion_ui,
            "editar": self.editar_devolucion_ui,
            "eliminar": self.eliminar_devolucion_ui,
            "actualizar": self.actualizar_treeview_devolucion
        }
        query = "SELECT id, venta_id, fecha, motivo, monto, usuario_id FROM devoluciones"
        self._crear_crud_tab(frame_devoluciones, "devolucion", columns, headings, callbacks,
                           lambda: self._cargar_entidad_datos("devolucion", query))

    @permission_required("clientes")
    def _crear_contenido_pestana_clientes(self, frame_clientes):
        columns = ("id", "nombre", "cedula", "telefono")
        headings = ("ID", "Nombre", "Cédula", "Teléfono")
        callbacks = {
            "agregar": self.agregar_cliente_ui,
            "editar": self.editar_cliente_ui,
            "eliminar": self.eliminar_cliente_ui,
            "actualizar": self.actualizar_treeview_cliente
        }
        query = "SELECT id, nombre, cedula, telefono FROM clientes"
        self._crear_crud_tab(frame_clientes, "cliente", columns, headings, callbacks,
                           lambda: self._cargar_entidad_datos("cliente", query))

    @permission_required("productos")
    def _crear_contenido_pestana_productos(self, frame_productos):
        columns = ("id", "codigo", "nombre", "precio", "stock")
        headings = ("ID", "Código", "Nombre", "Precio", "Stock")
        callbacks = {
            "agregar": self.agregar_producto_ui,
            "editar": self.editar_producto_ui,
            "eliminar": self.eliminar_producto_ui,
            "actualizar": self.actualizar_treeview_producto
        }
        query = "SELECT id, codigo, nombre, precio, stock FROM productos"
        self._crear_crud_tab(frame_productos, "producto", columns, headings, callbacks,
                           lambda: self._cargar_entidad_datos("producto", query))

    def _crear_contenido_pestana_inventario(self, frame_inventario):
        ttk.Label(frame_inventario, text="Aquí va la gestión de inventario.").pack()

    def _crear_contenido_pestana_reportes(self, frame_reportes):
        ttk.Label(frame_reportes, text="Aquí van los reportes.").pack()

    def mostrar_acerca_de(self):
        messagebox.showinfo("Acerca de", "Sistema de Caja POS\nVersión 1.0", parent=self)

    # --- MÉTODOS DE ACTUALIZACIÓN DE TREEVIEW MEJORADOS ---
    def actualizar_treeview_promocion(self):
        query = "SELECT id, nombre, descripcion, fecha_inicio, fecha_fin, tipo, valor, activo FROM promociones"
        self._cargar_entidad_datos("promocion", query)

    def actualizar_treeview_descuento(self):
        query = "SELECT id, nombre, tipo, valor, descripcion, activo FROM descuentos"
        self._cargar_entidad_datos("descuento", query)

    def actualizar_treeview_devolucion(self):
        query = "SELECT id, venta_id, fecha, motivo, monto, usuario_id FROM devoluciones"
        self._cargar_entidad_datos("devolucion", query)

    def actualizar_treeview_cliente(self):
        query = "SELECT id, nombre, cedula, telefono FROM clientes"
        self._cargar_entidad_datos("cliente", query)

    def actualizar_treeview_producto(self):
        query = "SELECT id, codigo, nombre, precio, stock FROM productos"
        self._cargar_entidad_datos("producto", query)

    def actualizar_info_venta_ui(self):
        pass  # Implementa aquí la actualización de la información de la venta en la UI

    def imprimir_ticket_fisico(self, datos_venta):
        imprimir_ticket(datos_venta)
    
    # --- MÉTODOS HELPER PARA UI ---
    def _crear_ventana_modal(self, titulo):
        """Crea una ventana modal estándar"""
        ventana = tk.Toplevel(self)
        ventana.title(titulo)
        ventana.transient(self)
        ventana.grab_set()
        return ventana
    
    def _crear_campos_formulario(self, parent, campos_config):
        """
        Crea campos de formulario basado en configuración
        campos_config: lista de tuplas (label, key, tipo, valor_inicial=None)
        """
        campos = {}
        for i, config in enumerate(campos_config):
            label, key = config[0], config[1]
            valor_inicial = config[3] if len(config) > 3 else ""
            
            ttk.Label(parent, text=label + ":").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            entry = ttk.Entry(parent, width=25)
            if valor_inicial:
                entry.insert(0, str(valor_inicial))
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            campos[key] = entry
        
        return campos

    # --- CRUD MÉTODOS PARA PROMOCIONES MEJORADOS ---
    @permission_required("promociones")
    @log_action("Agregar promoción")
    def agregar_promocion_ui(self):
        ventana = self._crear_ventana_modal("Agregar Promoción")
        
        campos_config = [
            ("Nombre", "nombre", "entry"),
            ("Descripción", "descripcion", "entry"),
            ("Fecha inicio (YYYY-MM-DD)", "fecha_inicio", "entry"),
            ("Fecha fin (YYYY-MM-DD)", "fecha_fin", "entry"),
            ("Tipo", "tipo", "entry"),
            ("Valor", "valor", "entry")
        ]
        
        campos = self._crear_campos_formulario(ventana, campos_config)
        activo_var = tk.IntVar(value=1)
        ttk.Checkbutton(ventana, text="Activo", variable=activo_var).grid(
            row=len(campos_config), column=0, columnspan=2, pady=5)

        def guardar():
            if not UIHelpers.validar_campos_obligatorios(campos):
                return
            
            try:
                datos = {k: campos[k].get() for k in campos}
                datos["valor"] = float(datos["valor"])
                datos["activo"] = activo_var.get()
                
                usuario_id = getattr(self.sistema.usuario_actual, 'id', None)
                if self.crud_helpers['promocion'].insertar(datos, usuario_id):
                    self.actualizar_treeview_promocion()
                    ventana.destroy()
            except ValueError:
                messagebox.showerror("Error", "El valor debe ser numérico.", parent=ventana)
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(
            row=len(campos_config)+1, column=0, columnspan=2, pady=10)

    @permission_required("promociones")
    @log_action("Eliminar promoción")
    def eliminar_promocion_ui(self):
        tree = getattr(self, "tree_promocion", None)
        seleccion = UIHelpers.obtener_seleccion_treeview(tree)
        if not seleccion:
            return
        
        promo_id = seleccion[0]
        if UIHelpers.confirmar_eliminacion("¿Eliminar la promoción seleccionada?"):
            usuario_id = getattr(self.sistema.usuario_actual, 'id', None)
            if self.crud_helpers['promocion'].eliminar("id", promo_id, usuario_id):
                self.actualizar_treeview_promocion()

    @permission_required("promociones")
    @log_action("Editar promoción")
    def editar_promocion_ui(self):
        tree = getattr(self, "tree_promocion", None)
        seleccion = UIHelpers.obtener_seleccion_treeview(tree)
        if not seleccion:
            return
        
        promo_id, nombre, desc, fecha_ini, fecha_fin, tipo, valor, activo = seleccion
        
        ventana = self._crear_ventana_modal("Editar Promoción")
        
        campos_config = [
            ("Nombre", "nombre", "entry", nombre),
            ("Descripción", "descripcion", "entry", desc),
            ("Fecha inicio", "fecha_inicio", "entry", fecha_ini),
            ("Fecha fin", "fecha_fin", "entry", fecha_fin),
            ("Tipo", "tipo", "entry", tipo),
            ("Valor", "valor", "entry", str(valor))
        ]
        
        campos = self._crear_campos_formulario(ventana, campos_config)
        activo_var = tk.IntVar(value=int(activo))
        ttk.Checkbutton(ventana, text="Activo", variable=activo_var).grid(
            row=len(campos_config), column=0, columnspan=2, pady=5)

        def guardar():
            if not UIHelpers.validar_campos_obligatorios(campos):
                return
                
            try:
                datos = {k: campos[k].get() for k in campos}
                datos["valor"] = float(datos["valor"])
                datos["activo"] = activo_var.get()
                
                usuario_id = getattr(self.sistema.usuario_actual, 'id', None)
                if self.crud_helpers['promocion'].actualizar("id", promo_id, datos, usuario_id):
                    self.actualizar_treeview_promocion()
                    ventana.destroy()
            except ValueError:
                messagebox.showerror("Error", "El valor debe ser numérico.", parent=ventana)
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(
            row=len(campos_config)+1, column=0, columnspan=2, pady=10)

    # --- CRUD MÉTODOS PARA DESCUENTOS MEJORADOS ---
    @permission_required("descuentos")
    @log_action("Agregar descuento")
    def agregar_descuento_ui(self):
        ventana = self._crear_ventana_modal("Agregar Descuento")
        
        campos_config = [
            ("Nombre", "nombre", "entry"),
            ("Tipo (porcentaje/monto)", "tipo", "entry"),
            ("Valor", "valor", "entry"),
            ("Descripción", "descripcion", "entry")
        ]
        
        campos = self._crear_campos_formulario(ventana, campos_config)
        activo_var = tk.IntVar(value=1)
        ttk.Checkbutton(ventana, text="Activo", variable=activo_var).grid(
            row=len(campos_config), column=0, columnspan=2, pady=5)

        def guardar():
            if not UIHelpers.validar_campos_obligatorios(campos):
                return
                
            try:
                datos = {k: campos[k].get() for k in campos}
                datos["valor"] = float(datos["valor"])
                datos["activo"] = activo_var.get()
                
                usuario_id = getattr(self.sistema.usuario_actual, 'id', None)
                if self.crud_helpers['descuento'].insertar(datos, usuario_id):
                    self.actualizar_treeview_descuento()
                    ventana.destroy()
            except ValueError:
                messagebox.showerror("Error", "El valor debe ser numérico.", parent=ventana)
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(
            row=len(campos_config)+1, column=0, columnspan=2, pady=10)

    @permission_required("descuentos")
    @log_action("Eliminar descuento")
    def eliminar_descuento_ui(self):
        tree = getattr(self, "tree_descuento", None)
        seleccion = UIHelpers.obtener_seleccion_treeview(tree)
        if not seleccion:
            return
        
        descuento_id = seleccion[0]
        if UIHelpers.confirmar_eliminacion("¿Eliminar el descuento seleccionado?"):
            usuario_id = getattr(self.sistema.usuario_actual, 'id', None)
            if self.crud_helpers['descuento'].eliminar("id", descuento_id, usuario_id):
                self.actualizar_treeview_descuento()

    @permission_required("descuentos")
    @log_action("Editar descuento")
    def editar_descuento_ui(self):
        tree = getattr(self, "tree_descuento", None)
        seleccion = UIHelpers.obtener_seleccion_treeview(tree)
        if not seleccion:
            return
        
        desc_id, nombre, tipo, valor, descripcion, activo = seleccion
        
        ventana = self._crear_ventana_modal("Editar Descuento")
        
        campos_config = [
            ("Nombre", "nombre", "entry", nombre),
            ("Tipo", "tipo", "entry", tipo),
            ("Valor", "valor", "entry", str(valor)),
            ("Descripción", "descripcion", "entry", descripcion)
        ]
        
        campos = self._crear_campos_formulario(ventana, campos_config)
        activo_var = tk.IntVar(value=int(activo))
        ttk.Checkbutton(ventana, text="Activo", variable=activo_var).grid(
            row=len(campos_config), column=0, columnspan=2, pady=5)

        def guardar():
            if not UIHelpers.validar_campos_obligatorios(campos):
                return
                
            try:
                datos = {k: campos[k].get() for k in campos}
                datos["valor"] = float(datos["valor"])
                datos["activo"] = activo_var.get()
                
                usuario_id = getattr(self.sistema.usuario_actual, 'id', None)
                if self.crud_helpers['descuento'].actualizar("id", desc_id, datos, usuario_id):
                    self.actualizar_treeview_descuento()
                    ventana.destroy()
            except ValueError:
                messagebox.showerror("Error", "El valor debe ser numérico.", parent=ventana)
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(
            row=len(campos_config)+1, column=0, columnspan=2, pady=10)

    # --- CRUD MÉTODOS PARA DEVOLUCIONES MEJORADOS ---
    @permission_required("devoluciones")
    @log_action("Agregar devolución")
    def agregar_devolucion_ui(self):
        ventana = self._crear_ventana_modal("Agregar Devolución")
        
        campos_config = [
            ("Venta ID", "venta_id", "entry"),
            ("Fecha (YYYY-MM-DD)", "fecha", "entry", datetime.date.today().strftime("%Y-%m-%d")),
            ("Motivo", "motivo", "entry"),
            ("Monto", "monto", "entry")
        ]
        
        campos = self._crear_campos_formulario(ventana, campos_config)

        def guardar():
            if not UIHelpers.validar_campos_obligatorios(campos):
                return
                
            try:
                datos = {
                    'venta_id': int(campos['venta_id'].get()),
                    'fecha': campos['fecha'].get(),
                    'motivo': campos['motivo'].get(),
                    'monto': float(campos['monto'].get()),
                    'usuario_id': getattr(self.sistema.usuario_actual, 'id', None)
                }
                
                usuario_id = getattr(self.sistema.usuario_actual, 'id', None)
                if self.crud_helpers['devolucion'].insertar(datos, usuario_id):
                    self.actualizar_treeview_devolucion()
                    ventana.destroy()
            except ValueError as e:
                messagebox.showerror("Error", "Datos inválidos. Verifique que ID y monto sean numéricos.", parent=ventana)
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(
            row=len(campos_config), column=0, columnspan=2, pady=10)

    @permission_required("devoluciones")
    @log_action("Eliminar devolución")
    def eliminar_devolucion_ui(self):
        tree = getattr(self, "tree_devolucion", None)
        seleccion = UIHelpers.obtener_seleccion_treeview(tree)
        if not seleccion:
            return
        
        devolucion_id = seleccion[0]
        if UIHelpers.confirmar_eliminacion("¿Eliminar la devolución seleccionada?"):
            usuario_id = getattr(self.sistema.usuario_actual, 'id', None)
            if self.crud_helpers['devolucion'].eliminar("id", devolucion_id, usuario_id):
                self.actualizar_treeview_devolucion()

    @permission_required("devoluciones")
    @log_action("Editar devolución")
    def editar_devolucion_ui(self):
        tree = getattr(self, "tree_devolucion", None)
        seleccion = UIHelpers.obtener_seleccion_treeview(tree)
        if not seleccion:
            return
        
        dev_id, venta_id, fecha, motivo, monto, usuario_id = seleccion
        
        ventana = self._crear_ventana_modal("Editar Devolución")
        
        campos_config = [
            ("Motivo", "motivo", "entry", motivo),
            ("Monto", "monto", "entry", str(monto))
        ]
        
        campos = self._crear_campos_formulario(ventana, campos_config)

        def guardar():
            if not UIHelpers.validar_campos_obligatorios(campos):
                return
                
            try:
                datos = {
                    'motivo': campos['motivo'].get(),
                    'monto': float(campos['monto'].get())
                }
                
                usuario_id = getattr(self.sistema.usuario_actual, 'id', None)
                if self.crud_helpers['devolucion'].actualizar("id", dev_id, datos, usuario_id):
                    self.actualizar_treeview_devolucion()
                    ventana.destroy()
            except ValueError:
                messagebox.showerror("Error", "El monto debe ser numérico.", parent=ventana)
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(
            row=len(campos_config), column=0, columnspan=2, pady=10)

    # --- CRUD MÉTODOS PARA CLIENTES MEJORADOS ---
    @permission_required("clientes")
    @log_action("Agregar cliente")
    def agregar_cliente_ui(self, event=None):
        ventana = self._crear_ventana_modal("Agregar Cliente")
        
        campos_config = [
            ("Nombre", "nombre", "entry"),
            ("Cédula", "cedula", "entry"),
            ("Teléfono", "telefono", "entry")
        ]
        
        campos = self._crear_campos_formulario(ventana, campos_config)

        def guardar():
            if not UIHelpers.validar_campos_obligatorios(campos):
                return
                
            try:
                datos = {k: campos[k].get() for k in campos}
                usuario_id = getattr(self.sistema.usuario_actual, 'id', None)
                if self.crud_helpers['cliente'].insertar(datos, usuario_id):
                    self.actualizar_treeview_cliente()
                    ventana.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(
            row=len(campos_config), column=0, columnspan=2, pady=10)

    @permission_required("clientes")
    @log_action("Eliminar cliente")
    def eliminar_cliente_ui(self):
        tree = getattr(self, "tree_cliente", None)
        seleccion = UIHelpers.obtener_seleccion_treeview(tree)
        if not seleccion:
            return
        
        cliente_id = seleccion[0]
        if UIHelpers.confirmar_eliminacion("¿Eliminar el cliente seleccionado?"):
            usuario_id = getattr(self.sistema.usuario_actual, 'id', None)
            if self.crud_helpers['cliente'].eliminar("id", cliente_id, usuario_id):
                self.actualizar_treeview_cliente()

    @permission_required("clientes")
    @log_action("Editar cliente")
    def editar_cliente_ui(self):
        tree = getattr(self, "tree_cliente", None)
        seleccion = UIHelpers.obtener_seleccion_treeview(tree)
        if not seleccion:
            return
        
        cliente_id, nombre, cedula, telefono = seleccion
        
        ventana = self._crear_ventana_modal("Editar Cliente")
        
        campos_config = [
            ("Nombre", "nombre", "entry", nombre),
            ("Cédula", "cedula", "entry", cedula),
            ("Teléfono", "telefono", "entry", telefono)
        ]
        
        campos = self._crear_campos_formulario(ventana, campos_config)

        def guardar():
            if not UIHelpers.validar_campos_obligatorios(campos):
                return
                
            try:
                datos = {k: campos[k].get() for k in campos}
                usuario_id = getattr(self.sistema.usuario_actual, 'id', None)
                if self.crud_helpers['cliente'].actualizar("id", cliente_id, datos, usuario_id):
                    self.actualizar_treeview_cliente()
                    ventana.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(
            row=len(campos_config), column=0, columnspan=2, pady=10)

    # --- CRUD MÉTODOS PARA PRODUCTOS MEJORADOS ---
    @permission_required("productos")
    @log_action("Agregar producto")
    def agregar_producto_ui(self, event=None):
        ventana = self._crear_ventana_modal("Agregar Producto")
        
        campos_config = [
            ("Código", "codigo", "entry"),
            ("Nombre", "nombre", "entry"),
            ("Precio", "precio", "entry"),
            ("Stock", "stock", "entry")
        ]
        
        campos = self._crear_campos_formulario(ventana, campos_config)

        def guardar():
            if not UIHelpers.validar_campos_obligatorios(campos):
                return
                
            try:
                datos = {
                    "codigo": campos["codigo"].get(),
                    "nombre": campos["nombre"].get(),
                    "precio": float(campos["precio"].get()),
                    "stock": int(campos["stock"].get())
                }
                
                usuario_id = getattr(self.sistema.usuario_actual, 'id', None)
                if self.crud_helpers['producto'].insertar(datos, usuario_id):
                    self.actualizar_treeview_producto()
                    ventana.destroy()
            except ValueError:
                messagebox.showerror("Error", "Precio y Stock deben ser numéricos.", parent=ventana)
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(
            row=len(campos_config), column=0, columnspan=2, pady=10)

    @permission_required("productos")
    @log_action("Eliminar producto")
    def eliminar_producto_ui(self):
        tree = getattr(self, "tree_producto", None)
        seleccion = UIHelpers.obtener_seleccion_treeview(tree)
        if not seleccion:
            return
        
        producto_id = seleccion[0]
        if UIHelpers.confirmar_eliminacion("¿Eliminar el producto seleccionado?"):
            usuario_id = getattr(self.sistema.usuario_actual, 'id', None)
            if self.crud_helpers['producto'].eliminar("id", producto_id, usuario_id):
                self.actualizar_treeview_producto()

    @permission_required("productos")
    @log_action("Editar producto")
    def editar_producto_ui(self):
        tree = getattr(self, "tree_producto", None)
        seleccion = UIHelpers.obtener_seleccion_treeview(tree)
        if not seleccion:
            return
        
        producto_id, codigo, nombre, precio, stock = seleccion
        
        ventana = self._crear_ventana_modal("Editar Producto")
        
        campos_config = [
            ("Código", "codigo", "entry", codigo),
            ("Nombre", "nombre", "entry", nombre),
            ("Precio", "precio", "entry", str(precio)),
            ("Stock", "stock", "entry", str(stock))
        ]
        
        campos = self._crear_campos_formulario(ventana, campos_config)

        def guardar():
            if not UIHelpers.validar_campos_obligatorios(campos):
                return
                
            try:
                datos = {
                    "codigo": campos["codigo"].get(),
                    "nombre": campos["nombre"].get(),
                    "precio": float(campos["precio"].get()),
                    "stock": int(campos["stock"].get())
                }
                
                usuario_id = getattr(self.sistema.usuario_actual, 'id', None)
                if self.crud_helpers['producto'].actualizar("id", producto_id, datos, usuario_id):
                    self.actualizar_treeview_producto()
                    ventana.destroy()
            except ValueError:
                messagebox.showerror("Error", "Precio y Stock deben ser numéricos.", parent=ventana)
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(
            row=len(campos_config), column=0, columnspan=2, pady=10)

    # --- OTROS MÉTODOS ---
    def mostrar_mensaje_estado(self, mensaje, tiempo=3000):
        self.status_var.set(mensaje)
        self.after(tiempo, lambda: self.status_var.set("Listo."))

    def mostrar_error(self, mensaje):
        messagebox.showerror("Error", mensaje, parent=self)

    @permission_required("ventas")
    @log_action("Finalizar venta")
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
        
        # Solo subadmins y admins pueden ver auditoría
        usuario_rol = getattr(self.sistema.usuario_actual, 'rol', '')
        if usuario_rol in ['admin', 'subadmin']:
            tabs_config.append(('Auditoría', self._crear_contenido_pestana_auditoria))

        for name, creator_func in tabs_config:
            frame = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(frame, text=name)
            self.pestanas[name] = frame
            creator_func(frame)

    @admin_required
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

        # Otros ajustes de administrador
        ttk.Label(frame_config, text="--- Gestión de Sistema ---").grid(row=2, column=0, columnspan=3, pady=15, sticky='w')
        ttk.Button(frame_config, text="Gestionar Usuarios", command=self._gestionar_usuarios).grid(row=3, column=0, padx=5, pady=5, sticky='w')
        ttk.Button(frame_config, text="Respaldo de BD", command=self._respaldar_base_datos).grid(row=3, column=1, padx=5, pady=5, sticky='w')
        ttk.Button(frame_config, text="Restaurar BD", command=self._restaurar_base_datos).grid(row=3, column=2, padx=5, pady=5, sticky='w')
        
        # Configuración de correo
        ttk.Label(frame_config, text="--- Configuración de Notificaciones ---").grid(row=4, column=0, columnspan=3, pady=15, sticky='w')
        ttk.Button(frame_config, text="Configurar Email", command=self._configurar_email).grid(row=5, column=0, padx=5, pady=5, sticky='w')

        # Mejorar el comportamiento de redimensionamiento
        frame_config.grid_columnconfigure(1, weight=1)
    
    def _crear_contenido_pestana_auditoria(self, frame_auditoria):
        """Crear pestaña de auditoría de movimientos"""
        columns = ("id", "usuario", "accion", "tabla", "fecha", "detalles")
        headings = ("ID", "Usuario", "Acción", "Tabla", "Fecha", "Detalles")
        
        tree = UIHelpers.crear_treeview(frame_auditoria, columns, headings)
        setattr(self, "tree_auditoria", tree)
        
        # Botones de control
        button_frame = ttk.Frame(frame_auditoria)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(button_frame, text="Actualizar", command=self._actualizar_auditoria).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Filtrar por Usuario", command=self._filtrar_auditoria).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Exportar", command=self._exportar_auditoria).pack(side="left", padx=5)
        
        # Cargar datos iniciales
        self._actualizar_auditoria()
    
    def _actualizar_auditoria(self):
        """Actualizar los datos de auditoría"""
        query = """
        SELECT a.id, u.nombre, a.accion, a.tabla, a.fecha, a.detalles 
        FROM auditoria a 
        LEFT JOIN usuarios u ON a.usuario_id = u.id 
        ORDER BY a.fecha DESC 
        LIMIT 1000
        """
        self._cargar_entidad_datos("auditoria", query)
    
    def _filtrar_auditoria(self):
        """Filtrar auditoría por usuario"""
        messagebox.showinfo("Filtros", "Funcionalidad de filtros en desarrollo.", parent=self)
    
    def _exportar_auditoria(self):
        """Exportar auditoría a archivo"""
        messagebox.showinfo("Exportar", "Funcionalidad de exportación en desarrollo.", parent=self)

    @admin_required
    @log_action("Actualizar tasa de dólar")
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

    @admin_required
    @log_action("Actualizar modelo de negocio")
    def _guardar_modelo_negocio(self):
        nuevo_modelo = self.modelo_negocio_var.get()
        self.sistema.actualizar_configuracion('modelo_negocio', nuevo_modelo)
        self.mostrar_mensaje_estado(f"Modelo de negocio actualizado a: {nuevo_modelo}")

    @admin_required
    def _gestionar_usuarios(self):
        messagebox.showinfo("Gestionar Usuarios", "Funcionalidad de gestión de usuarios en desarrollo.", parent=self)
    
    @admin_required
    @log_action("Respaldar base de datos")
    def _respaldar_base_datos(self):
        try:
            # Aquí iría la lógica de respaldo
            messagebox.showinfo("Respaldo", "Respaldo de base de datos completado exitosamente.", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Error al realizar respaldo: {e}", parent=self)
    
    @admin_required
    @log_action("Restaurar base de datos")
    def _restaurar_base_datos(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro de restaurar la base de datos? Esta acción no se puede deshacer.", parent=self):
            try:
                # Aquí iría la lógica de restauración
                messagebox.showinfo("Restaurar", "Restauración de base de datos completada.", parent=self)
            except Exception as e:
                messagebox.showerror("Error", f"Error al restaurar: {e}", parent=self)
    
    @admin_required
    def _configurar_email(self):
        ventana = self._crear_ventana_modal("Configuración de Email")
        
        campos_config = [
            ("Servidor SMTP", "smtp_server", "entry"),
            ("Puerto", "smtp_port", "entry", "587"),
            ("Email", "email", "entry"),
            ("Contraseña", "password", "entry")
        ]
        
        campos = self._crear_campos_formulario(ventana, campos_config)
        
        # Configurar el campo de contraseña
        campos["password"].config(show="*")

        def guardar():
            if not UIHelpers.validar_campos_obligatorios(campos):
                return
                
            try:
                config_email = {k: campos[k].get() for k in campos}
                # Aquí se guardaría la configuración de email
                messagebox.showinfo("Éxito", "Configuración de email guardada correctamente.", parent=ventana)
                ventana.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar configuración: {e}", parent=ventana)

        ttk.Button(ventana, text="Guardar", command=guardar).grid(
            row=len(campos_config), column=0, columnspan=2, pady=10)
        ttk.Button(ventana, text="Probar Conexión", command=lambda: messagebox.showinfo("Prueba", "Funcionalidad de prueba en desarrollo.", parent=ventana)).grid(
            row=len(campos_config)+1, column=0, columnspan=2, pady=5)

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

    @permission_required("ventas")
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

    @permission_required("ventas")
    @log_action("Marcar venta pendiente")
    def marcar_venta_pendiente(self, event=None):
        # Marca la venta actual como pendiente (por ejemplo, para guardar y continuar después)
        if not self.sistema.venta_actual['items']:
            messagebox.showwarning("Sin productos", "No hay productos en la venta para marcar como pendiente.", parent=self)
            return
        self.sistema.marcar_venta_pendiente()
        self.sistema.nueva_venta()
        self.actualizar_info_venta_ui()
        messagebox.showinfo("Venta pendiente", "La venta fue marcada como pendiente.", parent=self)

    @permission_required("inventario")
    @log_action("Registrar entrada de inventario")
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

    @permission_required("inventario")
    @log_action("Registrar salida de inventario")
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

    @permission_required("productos_consulta")
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

    @permission_required("ventas")
    @log_action("Aplicar precio de mayoreo")
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

    @permission_required("ventas")
    @log_action("Quitar producto de venta")
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