import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from core.database import get_db_cursor, ejecutar_consulta_segura

class UIHelpers:
    """Clase con helpers para estandarizar elementos de UI"""
    
    @staticmethod
    def crear_form_frame(parent, title):
        """Crea un frame estándar para formularios"""
        frame = ttk.LabelFrame(parent, text=title, padding="10")
        frame.pack(fill="x", padx=10, pady=5)
        return frame
    
    @staticmethod
    def crear_campo_entrada(parent, label, row, column=0, width=20):
        """Crea un campo de entrada estándar"""
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", padx=5, pady=2)
        entry = ttk.Entry(parent, width=width)
        entry.grid(row=row, column=column+1, sticky="ew", padx=5, pady=2)
        return entry
    
    @staticmethod
    def crear_treeview(parent, columns, headings, heights=400):
        """Crea un TreeView estandarizado con scrollbars"""
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # TreeView
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=heights//20)
        
        # Headers
        for col, heading in zip(columns, headings):
            tree.heading(col, text=heading)
            tree.column(col, width=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        h_scrollbar = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid
        tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        return tree
    
    @staticmethod
    def crear_botones_crud(parent, callbacks):
        """Crea botones estándar para operaciones CRUD"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        buttons = {}
        actions = [
            ("Agregar", "agregar", "success"),
            ("Editar", "editar", "warning"),
            ("Eliminar", "eliminar", "danger"),
            ("Actualizar", "actualizar", "info")
        ]
        
        for i, (text, action, style) in enumerate(actions):
            if action in callbacks:
                btn = ttk.Button(button_frame, text=text, command=callbacks[action])
                btn.pack(side="left", padx=5)
                buttons[action] = btn
        
        return buttons
    
    @staticmethod
    def validar_campos_obligatorios(campos):
        """Valida que los campos obligatorios no estén vacíos"""
        for nombre, entry in campos.items():
            if not entry.get().strip():
                messagebox.showerror("Error", f"El campo {nombre} es obligatorio")
                entry.focus()
                return False
        return True
    
    @staticmethod
    def limpiar_campos(campos):
        """Limpia todos los campos de entrada"""
        for entry in campos.values():
            if isinstance(entry, ttk.Entry):
                entry.delete(0, tk.END)
            elif isinstance(entry, ttk.Combobox):
                entry.set("")
    
    @staticmethod
    def cargar_datos_treeview(tree, query, params=None):
        """Carga datos en un TreeView desde una consulta SQL"""
        # Limpiar TreeView
        for item in tree.get_children():
            tree.delete(item)
        
        # Ejecutar consulta
        try:
            with get_db_cursor() as cursor:
                cursor.execute(query, params or ())
                rows = cursor.fetchall()
                
                for row in rows:
                    tree.insert("", "end", values=row)
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos: {e}")
    
    @staticmethod
    def obtener_seleccion_treeview(tree):
        """Obtiene la selección actual del TreeView"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un elemento de la lista")
            return None
        
        item = tree.item(selection[0])
        return item["values"]
    
    @staticmethod
    def confirmar_eliminacion(mensaje="¿Está seguro de eliminar este elemento?"):
        """Muestra diálogo de confirmación para eliminación"""
        return messagebox.askyesno("Confirmar", mensaje)

class CRUDHelper:
    """Helper para operaciones CRUD estandarizadas"""
    
    def __init__(self, table_name):
        self.table_name = table_name
    
    def insertar(self, datos, usuario_id=None):
        """Inserta un nuevo registro"""
        campos = ", ".join(datos.keys())
        placeholders = ", ".join(["?" for _ in datos])
        query = f"INSERT INTO {self.table_name} ({campos}) VALUES ({placeholders})"
        
        success, message = ejecutar_consulta_segura(query, list(datos.values()), usuario_id)
        
        if success:
            messagebox.showinfo("Éxito", "Registro agregado correctamente")
        else:
            messagebox.showerror("Error", f"Error al agregar: {message}")
        
        return success
    
    def actualizar(self, id_campo, id_valor, datos, usuario_id=None):
        """Actualiza un registro existente"""
        campos = ", ".join([f"{k} = ?" for k in datos.keys()])
        query = f"UPDATE {self.table_name} SET {campos} WHERE {id_campo} = ?"
        
        valores = list(datos.values()) + [id_valor]
        success, message = ejecutar_consulta_segura(query, valores, usuario_id)
        
        if success:
            messagebox.showinfo("Éxito", "Registro actualizado correctamente")
        else:
            messagebox.showerror("Error", f"Error al actualizar: {message}")
        
        return success
    
    def eliminar(self, id_campo, id_valor, usuario_id=None):
        """Elimina un registro"""
        query = f"DELETE FROM {self.table_name} WHERE {id_campo} = ?"
        
        success, message = ejecutar_consulta_segura(query, [id_valor], usuario_id)
        
        if success:
            messagebox.showinfo("Éxito", "Registro eliminado correctamente")
        else:
            messagebox.showerror("Error", f"Error al eliminar: {message}")
        
        return success

def create_styled_frame(parent, title=""):
    """Crea un frame estilizado con título"""
    if title:
        frame = ttk.LabelFrame(parent, text=title, padding="10")
    else:
        frame = ttk.Frame(parent, padding="10")
    return frame

def create_input_frame(parent, label_text, row, column=0, width=20, **kwargs):
    """Crea un frame con label y entry"""
    ttk.Label(parent, text=label_text).grid(row=row, column=column, sticky="w", padx=5, pady=2)
    entry = ttk.Entry(parent, width=width, **kwargs)
    entry.grid(row=row, column=column+1, sticky="ew", padx=5, pady=2)
    return entry

def format_currency(amount):
    """Formatea cantidad como moneda costarricense"""
    try:
        return f"₡{float(amount):,.2f}"
    except (ValueError, TypeError):
        return "₡0.00"

def validate_numeric_input(value):
    """Valida entrada numérica"""
    if value == "":
        return True
    try:
        float(value)
        return True
    except ValueError:
        return False

def center_window(window, width=None, height=None):
    """Centra una ventana en la pantalla"""
    window.update_idletasks()
    
    if width is None:
        width = window.winfo_width()
    if height is None:
        height = window.winfo_height()
    
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    
    window.geometry(f"{width}x{height}+{x}+{y}")