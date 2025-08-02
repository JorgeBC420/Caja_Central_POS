#!/usr/bin/env python3
"""
Aplicación Principal - Caja Central POS
Sistema de Punto de Venta simplificado para inicio rápido
"""

import sys
import os
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import hashlib

# Configuración
DATABASE_PATH = "data/caja_registradora_pos_cr.db"

class SimplePOS:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Caja Central POS - Sistema Simplificado")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Inicializar base de datos
        self.init_database()
        
        # Crear interfaz
        self.create_interface()
        
    def init_database(self):
        """Inicializa la base de datos básica"""
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Tabla usuarios básica
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                nombre TEXT NOT NULL,
                rol TEXT DEFAULT 'cajero',
                activo INTEGER DEFAULT 1,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla productos básica
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE,
                nombre TEXT NOT NULL,
                precio REAL NOT NULL,
                stock INTEGER DEFAULT 0,
                activo INTEGER DEFAULT 1,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla ventas básica
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario_id INTEGER,
                total REAL NOT NULL,
                estado TEXT DEFAULT 'completada'
            )
        ''')
        
        # Usuario admin por defecto
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            password_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute('''
                INSERT INTO usuarios (username, password, nombre, rol) 
                VALUES (?, ?, ?, ?)
            ''', ("admin", password_hash, "Administrador", "admin"))
        
        # Productos de ejemplo
        cursor.execute("SELECT COUNT(*) FROM productos")
        if cursor.fetchone()[0] == 0:
            productos_ejemplo = [
                ("001", "Producto A", 1500),
                ("002", "Producto B", 2500),
                ("003", "Producto C", 3500),
            ]
            cursor.executemany('''
                INSERT INTO productos (codigo, nombre, precio, stock) 
                VALUES (?, ?, ?, 10)
            ''', productos_ejemplo)
        
        conn.commit()
        conn.close()
        
    def create_interface(self):
        """Crea la interfaz principal"""
        # Título
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="🏪 CAJA CENTRAL POS", 
            font=('Arial', 20, 'bold'),
            fg='white', 
            bg='#2c3e50'
        )
        title_label.pack(expand=True)
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Estado del sistema
        status_frame = tk.LabelFrame(main_frame, text="Estado del Sistema", font=('Arial', 12, 'bold'))
        status_frame.pack(fill='x', pady=(0, 20))
        
        # Información del sistema
        info_text = f"""
🚀 Sistema POS inicializado correctamente
📁 Base de datos: {DATABASE_PATH}
📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}
👤 Usuario: admin (por defecto)
🔑 Password: admin123
        """
        
        info_label = tk.Label(status_frame, text=info_text.strip(), justify='left', bg='#f0f0f0')
        info_label.pack(padx=10, pady=10)
        
        # Botones principales
        buttons_frame = tk.Frame(main_frame, bg='#f0f0f0')
        buttons_frame.pack(fill='both', expand=True)
        
        # Configurar grid
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        # Botones
        btn_productos = tk.Button(
            buttons_frame, 
            text="📦 Ver Productos",
            font=('Arial', 14, 'bold'),
            bg='#3498db', 
            fg='white',
            height=3,
            command=self.mostrar_productos
        )
        btn_productos.grid(row=0, column=0, padx=10, pady=10, sticky='ew')
        
        btn_venta = tk.Button(
            buttons_frame, 
            text="💰 Nueva Venta",
            font=('Arial', 14, 'bold'),
            bg='#27ae60', 
            fg='white',
            height=3,
            command=self.nueva_venta
        )
        btn_venta.grid(row=0, column=1, padx=10, pady=10, sticky='ew')
        
        btn_usuarios = tk.Button(
            buttons_frame, 
            text="👥 Usuarios",
            font=('Arial', 14, 'bold'),
            bg='#e74c3c', 
            fg='white',
            height=3,
            command=self.mostrar_usuarios
        )
        btn_usuarios.grid(row=1, column=0, padx=10, pady=10, sticky='ew')
        
        btn_reportes = tk.Button(
            buttons_frame, 
            text="📊 Reportes",
            font=('Arial', 14, 'bold'),
            bg='#9b59b6', 
            fg='white',
            height=3,
            command=self.mostrar_reportes
        )
        btn_reportes.grid(row=1, column=1, padx=10, pady=10, sticky='ew')
        
        # Pie de página
        footer_frame = tk.Frame(self.root, bg='#34495e', height=40)
        footer_frame.pack(fill='x', side='bottom')
        footer_frame.pack_propagate(False)
        
        footer_label = tk.Label(
            footer_frame, 
            text="Caja Central POS v1.0 - Sistema Simplificado", 
            font=('Arial', 10),
            fg='white', 
            bg='#34495e'
        )
        footer_label.pack(expand=True)
        
    def mostrar_productos(self):
        """Muestra la lista de productos"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Lista de Productos")
        ventana.geometry("600x400")
        
        # Frame para la lista
        frame = tk.Frame(ventana)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Treeview para mostrar productos
        columns = ('ID', 'Código', 'Nombre', 'Precio', 'Stock')
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Cargar datos
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, codigo, nombre, precio, stock FROM productos WHERE activo = 1")
        productos = cursor.fetchall()
        conn.close()
        
        for producto in productos:
            tree.insert('', 'end', values=producto)
        
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
    def nueva_venta(self):
        """Interfaz para nueva venta"""
        messagebox.showinfo("Nueva Venta", "Función de ventas en desarrollo.\n\nPor ahora puedes:\n- Ver productos\n- Gestionar usuarios\n- Ver reportes básicos")
        
    def mostrar_usuarios(self):
        """Muestra la lista de usuarios"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Lista de Usuarios")
        ventana.geometry("500x300")
        
        frame = tk.Frame(ventana)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('ID', 'Usuario', 'Nombre', 'Rol')
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, nombre, rol FROM usuarios WHERE activo = 1")
        usuarios = cursor.fetchall()
        conn.close()
        
        for usuario in usuarios:
            tree.insert('', 'end', values=usuario)
        
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
    def mostrar_reportes(self):
        """Muestra reportes básicos"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Reportes del Sistema")
        ventana.geometry("400x300")
        
        frame = tk.Frame(ventana)
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Obtener estadísticas básicas
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM productos WHERE activo = 1")
        total_productos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE activo = 1")
        total_usuarios = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ventas")
        total_ventas = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(total), 0) FROM ventas")
        total_ingresos = cursor.fetchone()[0]
        
        conn.close()
        
        # Mostrar estadísticas
        stats_text = f"""
📊 ESTADÍSTICAS DEL SISTEMA

📦 Total Productos: {total_productos}
👥 Total Usuarios: {total_usuarios}
💰 Total Ventas: {total_ventas}
💵 Ingresos Totales: ₡{total_ingresos:,.2f}

📅 Sistema inicializado: {datetime.now().strftime('%d/%m/%Y')}
🗃️ Base de datos: SQLite
        """
        
        stats_label = tk.Label(frame, text=stats_text.strip(), justify='left', font=('Arial', 11))
        stats_label.pack(expand=True)
        
    def run(self):
        """Ejecuta la aplicación"""
        try:
            print("🚀 Iniciando Caja Central POS...")
            print(f"📁 Base de datos: {DATABASE_PATH}")
            print("✅ Sistema listo!")
            self.root.mainloop()
        except Exception as e:
            print(f"❌ Error: {e}")
            messagebox.showerror("Error", f"Error iniciando la aplicación:\n{e}")

def main():
    """Función principal"""
    print("=" * 50)
    print("🏪 CAJA CENTRAL POS - SISTEMA SIMPLIFICADO")
    print("=" * 50)
    
    try:
        app = SimplePOS()
        app.run()
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()
