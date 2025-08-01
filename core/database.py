import sqlite3
import hashlib
import os
import shutil
import csv
from contextlib import contextmanager
import logging

# Constantes
DB_NAME = 'caja_registradora_pos_cr.db'
DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = 'admin123'
DEFAULT_IVA_RATE = 0.13
DEFAULT_REGIMEN_EMISOR = 'tradicional'

class DatabaseManager:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.logger = logging.getLogger(__name__)
        self._ensure_db_initialized()
        
    def _get_connection(self):
        return sqlite3.connect(self.db_name)
        
    @property
    def connection(self):
        return sqlite3.connect(self.db_name)

    # Context managers
    @contextmanager
    def get_db_connection(self):
        """Context manager para conexiones seguras"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager  
    def get_db_cursor(self):
        """Context manager para operaciones con cursor"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                self.logger.error(f"Error en base de datos: {e}")
                raise e

    # Métodos centralizados
    def ejecutar_consulta_segura(self, query, params=None):
        """Método centralizado para consultas SELECT"""
        with self.get_db_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()

    def ejecutar_insercion_segura(self, query, params):
        """Método centralizado para INSERT"""
        with self.get_db_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.lastrowid

    def ejecutar_actualizacion_segura(self, query, params):
        """Método centralizado para UPDATE/DELETE"""
        with self.get_db_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

    # Métodos de auditoría
    def insertar_auditoria(self, evento):
        """Método específico para auditoría"""
        query = """
        INSERT INTO auditoria (usuario, accion, descripcion, fecha) 
        VALUES (?, ?, ?, ?)
        """
        params = (
            evento['usuario'],
            evento['accion'], 
            evento['descripcion'],
            evento['fecha']
        )
        return self.ejecutar_insercion_segura(query, params)

    def obtener_auditoria(self, limit=100):
        """Obtener registros de auditoría"""
        query = "SELECT * FROM auditoria ORDER BY fecha DESC LIMIT ?"
        return self.ejecutar_consulta_segura(query, (limit,))

    def _ensure_db_initialized(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla de auditoría
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT NOT NULL,
                    accion TEXT NOT NULL,
                    descripcion TEXT,
                    fecha TEXT NOT NULL
                )
            """)
            
            # Tablas principales
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metodos_pago (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    descripcion TEXT
                )   
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    descripcion TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pagos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id INTEGER NOT NULL,
                    metodo TEXT NOT NULL,
                    monto REAL NOT NULL,
                    referencia TEXT,
                    banco TEXT,
                    fecha TEXT NOT NULL,
                    FOREIGN KEY (venta_id) REFERENCES ventas(id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_barras TEXT UNIQUE,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    precio REAL NOT NULL,
                    costo REAL,
                    stock INTEGER DEFAULT 0,
                    stock_minimo INTEGER DEFAULT 5,
                    categoria_id INTEGER,
                    iva_tasa REAL DEFAULT 0.13,
                    observaciones_stock TEXT,
                    usuario_creacion TEXT,
                    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    cedula TEXT,
                    telefono TEXT,
                    email TEXT,
                    direccion TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    total REAL NOT NULL,
                    impuesto_monto REAL,
                    tasa_iva_aplicada REAL,
                    subtotal_neto REAL,
                    pago_recibido REAL,
                    cambio REAL,
                    usuario_id INTEGER,
                    regimen_emisor_venta TEXT,
                    fe_cr_clave TEXT,
                    fe_cr_consecutivo TEXT,
                    fe_cr_estado_hacienda TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS venta_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL,
                    precio_unitario_original REAL,
                    precio_unitario_efectivo REAL,
                    tipo_descuento_linea TEXT,
                    valor_descuento_linea REAL,
                    descripcion_modificacion TEXT,
                    iva_aplicado_linea_monto REAL,
                    subtotal REAL,
                    FOREIGN KEY (venta_id) REFERENCES ventas(id),
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimientos_inventario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    cantidad INTEGER NOT NULL,
                    fecha TEXT NOT NULL,
                    usuario_id INTEGER,
                    observaciones TEXT,
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS devoluciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id INTEGER NOT NULL,
                    fecha TEXT NOT NULL,
                    motivo TEXT,
                    monto REAL,
                    usuario_id INTEGER,
                    FOREIGN KEY (venta_id) REFERENCES ventas(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    nombre TEXT,
                    rol TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bitacora (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    accion TEXT NOT NULL,
                    descripcion TEXT,
                    fecha TEXT DEFAULT (datetime('now','localtime'))
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS descuentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    tipo TEXT,
                    valor REAL NOT NULL,
                    descripcion TEXT,
                    activo INTEGER DEFAULT 1
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS promociones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    fecha_inicio TEXT,
                    fecha_fin TEXT,
                    tipo TEXT,
                    valor REAL,
                    activo INTEGER DEFAULT 1
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuracion (
                    clave TEXT PRIMARY KEY,
                    valor TEXT
                )
            """)
            
            # Usuario admin por defecto
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username=?", (DEFAULT_ADMIN_USERNAME,))
            if cursor.fetchone()[0] == 0:
                hashed_pw = hashlib.sha256(DEFAULT_ADMIN_PASSWORD.encode()).hexdigest()
                cursor.execute(
                    "INSERT INTO usuarios (username, password, nombre, rol) VALUES (?, ?, ?, ?)",
                    (DEFAULT_ADMIN_USERNAME, hashed_pw, "Administrador", "admin")
                )
                
            # Categoría de ejemplo
            cursor.execute("SELECT COUNT(*) FROM categorias")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)", ("General", "Categoría por defecto"))
                
            # Producto de ejemplo
            cursor.execute("SELECT COUNT(*) FROM productos")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO productos (codigo_barras, nombre, descripcion, precio, costo, stock, stock_minimo, categoria_id, iva_tasa, observaciones_stock, usuario_creacion)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, ("00000001", "Producto Ejemplo", "Producto de prueba", 1000, 700, 10, 2, 1, DEFAULT_IVA_RATE, "", DEFAULT_ADMIN_USERNAME))
                
            conn.commit()

    # Método original para compatibilidad
    def ejecutar_consulta(self, consulta, parametros=(), fetchone=False, fetchall=False, commit=False):
        conexion = self._get_connection()
        cursor = conexion.cursor()
        last_id = None
        try:
            cursor.execute(consulta, parametros)
            if commit:
                conexion.commit()
                last_id = cursor.lastrowid
            if fetchone:
                return cursor.fetchone()
            if fetchall:
                return cursor.fetchall()
            if commit:
                return last_id if last_id is not None else True
        except sqlite3.Error as e:
            print(f"Error DB: {e} en '{consulta}' con {parametros}")
            if commit:
                conexion.rollback()
            return None if (fetchone or fetchall) else False
        finally:
            conexion.close()
        return None if (fetchone or fetchall) else False if commit else None


    def registrar_bitacora(self, usuario_id, accion, descripcion=None):
        with self.connection as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO bitacora (usuario_id, accion, descripcion) VALUES (?, ?, ?)",
                (usuario_id, accion, descripcion)
            )
            conn.commit()
    # --- Consulta de bitácora ---
    def obtener_bitacora(self, usuario_id=None, fecha_inicio=None, fecha_fin=None, accion=None):
        consulta = "SELECT * FROM bitacora WHERE 1=1"
        parametros = []
        if usuario_id:
            consulta += " AND usuario_id=?"
            parametros.append(usuario_id)
        if fecha_inicio:
            consulta += " AND fecha >= ?"
            parametros.append(fecha_inicio)
        if fecha_fin:
            consulta += " AND fecha <= ?"
            parametros.append(fecha_fin)
        if accion:
            consulta += " AND accion LIKE ?"
            parametros.append(f"%{accion}%")
        consulta += " ORDER BY fecha DESC"
        return self.ejecutar_consulta(consulta, tuple(parametros), fetchall=True)
    # --- Reportes ---
    def reporte_ventas_por_usuario(self, fecha_inicio, fecha_fin):
        consulta = '''
            SELECT u.username, u.nombre, COUNT(v.id) as cantidad_ventas, SUM(v.total) as total_ventas
            FROM ventas v
            JOIN usuarios u ON v.usuario_id = u.id
            WHERE v.fecha BETWEEN ? AND ?
            GROUP BY v.usuario_id
        '''
        return self.ejecutar_consulta(consulta, (fecha_inicio, fecha_fin), fetchall=True)

    def reporte_ventas_por_metodo_pago(self, fecha_inicio, fecha_fin):
        consulta = '''
            SELECT metodo, SUM(monto) as total, COUNT(*) as cantidad
            FROM pagos
            WHERE fecha BETWEEN ? AND ?
            GROUP BY metodo
        '''
        return self.ejecutar_consulta(consulta, (fecha_inicio, fecha_fin), fetchall=True)

    def reporte_inventario_bajo_minimo(self):
        consulta = '''
            SELECT * FROM productos WHERE stock <= stock_minimo
        '''
        return self.ejecutar_consulta(consulta, fetchall=True)

    def reporte_productos_sin_movimiento(self, dias=30):
        consulta = '''
            SELECT p.*
            FROM productos p
            LEFT JOIN movimientos_inventario m ON p.id = m.producto_id AND m.fecha >= date('now', ?)
            WHERE m.id IS NULL
        '''
        intervalo = f'-{dias} days'
        return self.ejecutar_consulta(consulta, (intervalo,), fetchall=True)

    # --- Inventario ---
    def ajustar_inventario(self, producto_id, nuevo_stock, usuario_id, observaciones="Ajuste manual"):
        self.actualizar_stock_producto(producto_id, nuevo_stock)
        movimiento = {
            'producto_id': producto_id,
            'tipo': 'ajuste',
            'cantidad': nuevo_stock,
            'fecha': None,
            'usuario_id': usuario_id,
            'observaciones': observaciones
        }
        self.agregar_movimiento_inventario(movimiento)

    def agregar_movimiento_inventario(self, movimiento):
        consulta = '''
            INSERT INTO movimientos_inventario (producto_id, tipo, cantidad, fecha, usuario_id, observaciones)
            VALUES (?, ?, ?, datetime('now','localtime'), ?, ?)
        '''
        parametros = (
            movimiento.get('producto_id'),
            movimiento.get('tipo'),
            movimiento.get('cantidad'),
            movimiento.get('usuario_id'),
            movimiento.get('observaciones')
        )
        return self.ejecutar_consulta(consulta, parametros, commit=True)

    def obtener_movimientos_inventario(self, producto_id=None, fecha_inicio=None, fecha_fin=None):
        consulta = "SELECT * FROM movimientos_inventario WHERE 1=1"
        parametros = []
        if producto_id:
            consulta += " AND producto_id=?"
            parametros.append(producto_id)
        if fecha_inicio:
            consulta += " AND fecha >= ?"
            parametros.append(fecha_inicio)
        if fecha_fin:
            consulta += " AND fecha <= ?"
            parametros.append(fecha_fin)
        return self.ejecutar_consulta(consulta, tuple(parametros), fetchall=True)

    # --- Utilidades ---
    def backup_db(self, backup_path):
        shutil.copyfile(self.db_name, backup_path)

    def exportar_productos_csv(self, ruta_csv):
        productos = self.obtener_todos_los_productos()
        with open(ruta_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'codigo_barras', 'nombre', 'descripcion', 'precio', 'costo', 'stock', 'stock_minimo', 'categoria_id', 'iva_tasa', 'observaciones_stock', 'usuario_creacion'])
            for prod in productos:
                writer.writerow(prod)

    # --- Otros ---
    def eliminar_venta(self, venta_id, usuario_id):
        self.registrar_bitacora(usuario_id, "Eliminar venta", f"Venta ID: {venta_id}")
        consulta = "DELETE FROM ventas WHERE id=?"
        return self.ejecutar_consulta(consulta, (venta_id,), commit=True)

 
    # (Incluye aquí todos los métodos CRUD que ya tienes, como agregar_producto, modificar_producto, etc.)

    def ejecutar_consulta(self, consulta, parametros=(), fetchone=False, fetchall=False, commit=False):
        conexion = self._get_connection()
        cursor = conexion.cursor()
        last_id = None
        try:
            cursor.execute(consulta, parametros)
            if commit:
                conexion.commit()
                last_id = cursor.lastrowid
            if fetchone:
                return cursor.fetchone()
            if fetchall:
                return cursor.fetchall()
            if commit:
                return last_id if last_id is not None else True
        except sqlite3.Error as e:
            print(f"Error DB: {e} en '{consulta}' con {parametros}")
            if commit:
                conexion.rollback()
            return None if (fetchone or fetchall) else False
        finally:
            conexion.close()
        return None if (fetchone or fetchall) else False if commit else None
    # ... (Resto de la clase DatabaseManager) ...
    # --- CRUD de productos ---
    def agregar_producto(self, producto):
        consulta = '''
            INSERT INTO productos (codigo_barras, nombre, descripcion, precio, costo, stock, stock_minimo, categoria_id, iva_tasa, observaciones_stock, usuario_creacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        parametros = (
            producto.get('codigo_barras'),
            producto.get('nombre'),
            producto.get('descripcion'),
            producto.get('precio'),
            producto.get('costo', 0),
            producto.get('stock', 0),
            producto.get('stock_minimo', 5),
            producto.get('categoria_id'),
            producto.get('iva_tasa', DEFAULT_IVA_RATE),
            producto.get('observaciones_stock'),
            producto.get('usuario_creacion')
        )
        return self.ejecutar_consulta(consulta, parametros, commit=True)

    def modificar_producto(self, producto_id, campos):
        set_clause = ', '.join([f"{k}=?" for k in campos.keys()])
        consulta = f"UPDATE productos SET {set_clause} WHERE id=?"
        parametros = list(campos.values()) + [producto_id]
        return self.ejecutar_consulta(consulta, parametros, commit=True)

    def eliminar_producto(self, producto_id):
        consulta = "DELETE FROM productos WHERE id=?"
        return self.ejecutar_consulta(consulta, (producto_id,), commit=True)

    def obtener_producto_por_id(self, producto_id):
        consulta = "SELECT * FROM productos WHERE id=?"
        return self.ejecutar_consulta(consulta, (producto_id,), fetchone=True)

    def obtener_todos_los_productos(self):
        consulta = "SELECT * FROM productos"
        return self.ejecutar_consulta(consulta, fetchall=True)

    def buscar_productos(self, criterio):
        consulta = """
            SELECT * FROM productos
            WHERE nombre LIKE ? OR codigo_barras LIKE ?
        """
        like_criterio = f"%{criterio}%"
        return self.ejecutar_consulta(consulta, (like_criterio, like_criterio), fetchall=True)

    def actualizar_stock_producto(self, producto_id, nuevo_stock):
        consulta = "UPDATE productos SET stock=? WHERE id=?"
        return self.ejecutar_consulta(consulta, (nuevo_stock, producto_id), commit=True)
    def insertar_pago(self, venta_id, metodo, monto, referencia=None, banco=None, fecha_pago=None):
        """
        Inserta un registro de pago en la tabla pagos.
        """
        query = """
            INSERT INTO pagos (venta_id, metodo, monto, referencia, banco, fecha_pago)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (venta_id, metodo, monto, referencia, banco, fecha_pago)
        with self.connection as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    def crear_usuario(self, nombre, email, password, rol):
        query = "INSERT INTO usuarios (nombre, email, password, rol) VALUES (?, ?, ?, ?)"
        params = (nombre, email, password, rol)
        with self.connection as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def obtener_usuario_por_id(self, usuario_id):
        query = "SELECT * FROM usuarios WHERE id = ?"
        with self.connection as conn:
            cursor = conn.cursor()
            cursor.execute(query, (usuario_id,))
            return cursor.fetchone()

    def obtener_todos_usuarios(self):
        query = "SELECT * FROM usuarios"
        with self.connection as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()

    def actualizar_usuario(self, usuario_id, nombre=None, email=None, password=None, rol=None):
        campos = []
        params = []
        if nombre:
            campos.append("nombre = ?")
            params.append(nombre)
        if email:
            campos.append("email = ?")
            params.append(email)
        if password:
            campos.append("password = ?")
            params.append(password)
        if rol:
            campos.append("rol = ?")
            params.append(rol)
        params.append(usuario_id)
        query = f"UPDATE usuarios SET {', '.join(campos)} WHERE id = ?"
        with self.connection as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def eliminar_usuario(self, usuario_id):
        query = "DELETE FROM usuarios WHERE id = ?"
        with self.connection as conn:
            cursor = conn.cursor()
            cursor.execute(query, (usuario_id,))
            conn.commit()
            return cursor.rowcount
    def agregar_config(self, clave, valor):
        consulta = "INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)"
        return self.ejecutar_consulta(consulta, (clave, valor), commit=True)

    def obtener_config(self, clave):
        consulta = "SELECT valor FROM configuracion WHERE clave=?"
        resultado = self.ejecutar_consulta(consulta, (clave,), fetchone=True)
        return resultado[0] if resultado else None

    def obtener_toda_config(self):
        consulta = "SELECT clave, valor FROM configuracion"
        return dict(self.ejecutar_consulta(consulta, fetchall=True))

    def eliminar_config(self, clave):
        consulta = "DELETE FROM configuracion WHERE clave=?"
        return self.ejecutar_consulta(consulta, (clave,), commit=True)
    # --- CRUD de categorías ---
    def obtener_categorias(self):
        consulta = "SELECT * FROM categorias"
        return self.ejecutar_consulta(consulta, fetchall=True)

    def agregar_categoria(self, nombre, descripcion=None):
        consulta = "INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)"
        parametros = (nombre, descripcion)
        return self.ejecutar_consulta(consulta, parametros, commit=True)

    def modificar_categoria(self, categoria_id, nombre, descripcion=None):
        consulta = "UPDATE categorias SET nombre=?, descripcion=? WHERE id=?"
        parametros = (nombre, descripcion, categoria_id)
        return self.ejecutar_consulta(consulta, parametros, commit=True)

    def eliminar_categoria(self, categoria_id):
        consulta = "DELETE FROM categorias WHERE id=?"
        return self.ejecutar_consulta(consulta, (categoria_id,), commit=True)

    def agregar_metodo_pago(self, nombre, descripcion=None):
        consulta = "INSERT INTO metodos_pago (nombre, descripcion) VALUES (?, ?)"
        return self.ejecutar_consulta(consulta, (nombre, descripcion), commit=True)

    def modificar_metodo_pago(self, metodo_id, nombre, descripcion=None):
        consulta = "UPDATE metodos_pago SET nombre=?, descripcion=? WHERE id=?"
        return self.ejecutar_consulta(consulta, (nombre, descripcion, metodo_id), commit=True)

    def eliminar_metodo_pago(self, metodo_id):
        consulta = "DELETE FROM metodos_pago WHERE id=?"
        return self.ejecutar_consulta(consulta, (metodo_id,), commit=True)

    def obtener_metodos_pago(self):
        consulta = "SELECT * FROM metodos_pago"
        return self.ejecutar_consulta(consulta, fetchall=True)

    def obtener_metodo_pago_por_id(self, metodo_id):
        consulta = "SELECT * FROM metodos_pago WHERE id=?"
        return self.ejecutar_consulta(consulta, (metodo_id,), fetchone=True)

    def obtener_categoria_por_id(self, categoria_id):
        consulta = "SELECT * FROM categorias WHERE id=?"
        return self.ejecutar_consulta(consulta, (categoria_id,), fetchone=True)

    def categoria_existe(self, nombre):
        consulta = "SELECT COUNT(*) FROM categorias WHERE nombre=?"
        resultado = self.ejecutar_consulta(consulta, (nombre,), fetchone=True)
        return resultado[0] > 0 if resultado else False

    # --- CRUD de clientes ---
    def agregar_cliente(self, cliente):
        consulta = '''
            INSERT INTO clientes (nombre, cedula, telefono, email, direccion)
            VALUES (?, ?, ?, ?, ?)
        '''
        parametros = (
            cliente.get('nombre'),
            cliente.get('cedula'),
            cliente.get('telefono'),
            cliente.get('email'),
            cliente.get('direccion')
        )
        return self.ejecutar_consulta(consulta, parametros, commit=True)

    def agregar_devolucion(self, devolucion):
        consulta = '''
            INSERT INTO devoluciones (venta_id, fecha, motivo, monto, usuario_id)
            VALUES (?, ?, ?, ?, ?)
        '''
        parametros = (
            devolucion.get('venta_id'),
            devolucion.get('fecha'),
            devolucion.get('motivo'),
            devolucion.get('monto'),
            devolucion.get('usuario_id')
        )
        return self.ejecutar_consulta(consulta, parametros, commit=True)

    def modificar_devolucion(self, devolucion_id, campos):
        set_clause = ', '.join([f"{k}=?" for k in campos.keys()])
        consulta = f"UPDATE devoluciones SET {set_clause} WHERE id=?"
        parametros = list(campos.values()) + [devolucion_id]
        return self.ejecutar_consulta(consulta, parametros, commit=True)

    def eliminar_devolucion(self, devolucion_id):
        consulta = "DELETE FROM devoluciones WHERE id=?"
        return self.ejecutar_consulta(consulta, (devolucion_id,), commit=True)

    def obtener_devolucion_por_id(self, devolucion_id):
        consulta = "SELECT * FROM devoluciones WHERE id=?"
        return self.ejecutar_consulta(consulta, (devolucion_id,), fetchone=True)

    def obtener_devoluciones(self, venta_id=None):
        consulta = "SELECT * FROM devoluciones"
        parametros = []
        if venta_id:
            consulta += " WHERE venta_id=?"
            parametros.append(venta_id)
        return self.ejecutar_consulta(consulta, tuple(parametros), fetchall=True)

    def modificar_cliente(self, cliente_id, campos):
        set_clause = ', '.join([f"{k}=?" for k in campos.keys()])
        consulta = f"UPDATE clientes SET {set_clause} WHERE id=?"
        parametros = list(campos.values()) + [cliente_id]
        return self.ejecutar_consulta(consulta, parametros, commit=True)

    def eliminar_cliente(self, cliente_id):
        consulta = "DELETE FROM clientes WHERE id=?"
        return self.ejecutar_consulta(consulta, (cliente_id,), commit=True)

    def obtener_cliente_por_id(self, cliente_id):
        consulta = "SELECT * FROM clientes WHERE id=?"
        return self.ejecutar_consulta(consulta, (cliente_id,), fetchone=True)

    def buscar_clientes(self, criterio):
        consulta = """
            SELECT * FROM clientes
            WHERE nombre LIKE ? OR cedula LIKE ? OR telefono LIKE ?
        """
        like_criterio = f"%{criterio}%"
        return self.ejecutar_consulta(consulta, (like_criterio, like_criterio, like_criterio), fetchall=True)

    def obtener_todos_los_clientes(self):
        consulta = "SELECT * FROM clientes"
        return self.ejecutar_consulta(consulta, fetchall=True)

    # --- CRUD de ventas ---
    def crear_venta(self, venta):
        consulta = '''
            INSERT INTO ventas (fecha, total, impuesto_monto, tasa_iva_aplicada, subtotal_neto, pago_recibido, cambio, usuario_id, regimen_emisor_venta, fe_cr_clave, fe_cr_consecutivo, fe_cr_estado_hacienda)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        parametros = (
            venta.get('fecha'),
            venta.get('total'),
            venta.get('impuesto_monto'),
            venta.get('tasa_iva_aplicada'),
            venta.get('subtotal_neto'),
            venta.get('pago_recibido'),
            venta.get('cambio'),
            venta.get('usuario_id'),
            venta.get('regimen_emisor_venta'),
            venta.get('fe_cr_clave'),
            venta.get('fe_cr_consecutivo'),
            venta.get('fe_cr_estado_hacienda')
            )
        return self.ejecutar_consulta(consulta, parametros, commit=True)

    def agregar_descuento(self, descuento):
        consulta = '''
            INSERT INTO descuentos (nombre, tipo, valor, descripcion, activo)
            VALUES (?, ?, ?, ?, ?)
        '''
        parametros = (
            descuento.get('nombre'),
            descuento.get('tipo'),
            descuento.get('valor'),
            descuento.get('descripcion'),
            descuento.get('activo', 1)
        )
        return self.ejecutar_consulta(consulta, parametros, commit=True)

    def modificar_descuento(self, descuento_id, campos):
        set_clause = ', '.join([f"{k}=?" for k in campos.keys()])
        consulta = f"UPDATE descuentos SET {set_clause} WHERE id=?"
        parametros = list(campos.values()) + [descuento_id]
        return self.ejecutar_consulta(consulta, parametros, commit=True)

    def eliminar_descuento(self, descuento_id):
        consulta = "DELETE FROM descuentos WHERE id=?"
        return self.ejecutar_consulta(consulta, (descuento_id,), commit=True)

    def obtener_descuento_por_id(self, descuento_id):
        consulta = "SELECT * FROM descuentos WHERE id=?"
        return self.ejecutar_consulta(consulta, (descuento_id,), fetchone=True)

    def obtener_descuentos(self, solo_activos=True):
        consulta = "SELECT * FROM descuentos"
        if solo_activos:
            consulta += " WHERE activo=1"
        return self.ejecutar_consulta(consulta, fetchall=True)

    def obtener_venta_por_id(self, venta_id):
        consulta = "SELECT * FROM ventas WHERE id=?"
        return self.ejecutar_consulta(consulta, (venta_id,), fetchone=True)
    def modificar_venta(self, venta_id, campos):
        set_clause = ', '.join([f"{k}=?" for k in campos.keys()])
        consulta = f"UPDATE ventas SET {set_clause} WHERE id=?"
        parametros = list(campos.values()) + [venta_id]
        return self.ejecutar_consulta(consulta, parametros, commit=True)
    
    def obtener_ventas(self, fecha_inicio=None, fecha_fin=None, usuario_id=None):
        consulta = "SELECT * FROM ventas WHERE 1=1"
        parametros = []
        if fecha_inicio:
            consulta += " AND fecha >= ?"
            parametros.append(fecha_inicio)
        if fecha_fin:
            consulta += " AND fecha <= ?"
            parametros.append(fecha_fin)
        if usuario_id:
            consulta += " AND usuario_id = ?"
            parametros.append(usuario_id)
        return self.ejecutar_consulta(consulta, tuple(parametros), fetchall=True)

    # --- CRUD de venta_items ---
    def agregar_venta_item(self, venta_item):
        consulta = '''
            INSERT INTO venta_items (venta_id, producto_id, cantidad, precio_unitario_original, precio_unitario_efectivo, tipo_descuento_linea, valor_descuento_linea, descripcion_modificacion, iva_aplicado_linea_monto, subtotal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        parametros = (
            venta_item.get('venta_id'),
            venta_item.get('producto_id'),
            venta_item.get('cantidad'),
            venta_item.get('precio_unitario_original'),
            venta_item.get('precio_unitario_efectivo'),
            venta_item.get('tipo_descuento_linea'),
            venta_item.get('valor_descuento_linea'),
            venta_item.get('descripcion_modificacion'),
            venta_item.get('iva_aplicado_linea_monto'),
            venta_item.get('subtotal')
        )
        return self.ejecutar_consulta(consulta, parametros, commit=True)

    def agregar_promocion(self, promocion):
        consulta = '''
            INSERT INTO promociones (nombre, descripcion, fecha_inicio, fecha_fin, tipo, valor, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        parametros = (
            promocion.get('nombre'),
            promocion.get('descripcion'),
            promocion.get('fecha_inicio'),
            promocion.get('fecha_fin'),
            promocion.get('tipo'),
            promocion.get('valor'),
            promocion.get('activo', 1)
        )
        return self.ejecutar_consulta(consulta, parametros, commit=True)

    def modificar_promocion(self, promocion_id, campos):
        set_clause = ', '.join([f"{k}=?" for k in campos.keys()])
        consulta = f"UPDATE promociones SET {set_clause} WHERE id=?"
        parametros = list(campos.values()) + [promocion_id]
        return self.ejecutar_consulta(consulta, parametros, commit=True)

    def eliminar_promocion(self, promocion_id):
        consulta = "DELETE FROM promociones WHERE id=?"
        return self.ejecutar_consulta(consulta, (promocion_id,), commit=True)

    def obtener_promocion_por_id(self, promocion_id):
        consulta = "SELECT * FROM promociones WHERE id=?"
        return self.ejecutar_consulta(consulta, (promocion_id,), fetchone=True)

    def obtener_promociones(self, solo_activos=True):
        consulta = "SELECT * FROM promociones"
        if solo_activos:
            consulta += " WHERE activo=1"
        return self.ejecutar_consulta(consulta, fetchall=True)

    def obtener_venta_items(self, venta_id):
        consulta = "SELECT * FROM venta_items WHERE venta_id=?"
        return self.ejecutar_consulta(consulta, (venta_id,), fetchall=True)

    # --- Historial de movimientos de inventario ---
    def agregar_movimiento_inventario(self, movimiento):
        consulta = '''
            INSERT INTO movimientos_inventario (producto_id, tipo, cantidad, fecha, usuario_id, observaciones)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        parametros = (
            movimiento.get('producto_id'),
            movimiento.get('tipo'),
            movimiento.get('cantidad'),
            movimiento.get('fecha'),
            movimiento.get('usuario_id'),
            movimiento.get('observaciones')
        )
        return self.ejecutar_consulta(consulta, parametros, commit=True)

    def obtener_movimientos_inventario(self, producto_id=None, fecha_inicio=None, fecha_fin=None):
        consulta = "SELECT * FROM movimientos_inventario WHERE 1=1"
        parametros = []
        if producto_id:
            consulta += " AND producto_id=?"
            parametros.append(producto_id)
        if fecha_inicio:
            consulta += " AND fecha >= ?"
            parametros.append(fecha_inicio)
        if fecha_fin:
            consulta += " AND fecha <= ?"
            parametros.append(fecha_fin)
        return self.ejecutar_consulta(consulta, tuple(parametros), fetchall=True)

    # --- Paginación y filtros avanzados ---
    def obtener_productos_paginados(self, pagina=1, por_pagina=20, criterio=None):
        offset = (pagina - 1) * por_pagina
        consulta = "SELECT * FROM productos"
        parametros = []
        if criterio:
            consulta += " WHERE nombre LIKE ? OR codigo_barras LIKE ?"
            like_criterio = f"%{criterio}%"
            parametros.extend([like_criterio, like_criterio])
        consulta += " LIMIT ? OFFSET ?"
        parametros.extend([por_pagina, offset])
        return self.ejecutar_consulta(consulta, tuple(parametros), fetchall=True)

    # --- Métodos para reportes ---
    def reporte_ventas_por_fecha(self, fecha_inicio, fecha_fin):
        consulta = '''
            SELECT fecha, SUM(total) as total_ventas, SUM(impuesto_monto) as total_impuestos, COUNT(*) as cantidad_ventas
            FROM ventas
            WHERE fecha BETWEEN ? AND ?
            GROUP BY fecha
        '''
        return self.ejecutar_consulta(consulta, (fecha_inicio, fecha_fin), fetchall=True)

    def reporte_productos_mas_vendidos(self, fecha_inicio=None, fecha_fin=None, limite=10):
        consulta = '''
            SELECT p.nombre, SUM(vi.cantidad) as total_vendido
            FROM venta_items vi
            JOIN productos p ON vi.producto_id = p.id
            JOIN ventas v ON vi.venta_id = v.id
            WHERE 1=1
        '''
        parametros = []
        if fecha_inicio:
            consulta += " AND v.fecha >= ?"
            parametros.append(fecha_inicio)
        if fecha_fin:
            consulta += " AND v.fecha <= ?"
            parametros.append(fecha_fin)
        consulta += " GROUP BY p.nombre ORDER BY total_vendido DESC LIMIT ?"
        parametros.append(limite)
        return self.ejecutar_consulta(consulta, tuple(parametros), fetchall=True)
    
    def inicializar_tablas(self):
        """Inicializa todas las tablas necesarias del sistema"""
        tablas = {
            'usuarios': '''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    usuario TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    rol TEXT NOT NULL DEFAULT 'cajero',
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'productos': '''
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    precio REAL NOT NULL,
                    stock INTEGER DEFAULT 0,
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'clientes': '''
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    cedula TEXT UNIQUE,
                    telefono TEXT,
                    email TEXT,
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'ventas': '''
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    cliente_id INTEGER,
                    subtotal REAL NOT NULL,
                    impuestos REAL DEFAULT 0,
                    total REAL NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT DEFAULT 'completada',
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
                )
            ''',
            'venta_items': '''
                CREATE TABLE IF NOT EXISTS venta_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL,
                    precio_unitario REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    FOREIGN KEY (venta_id) REFERENCES ventas(id),
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                )
            ''',
            'promociones': '''
                CREATE TABLE IF NOT EXISTS promociones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    fecha_inicio DATE,
                    fecha_fin DATE,
                    tipo TEXT NOT NULL,
                    valor REAL NOT NULL,
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'descuentos': '''
                CREATE TABLE IF NOT EXISTS descuentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    valor REAL NOT NULL,
                    descripcion TEXT,
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'devoluciones': '''
                CREATE TABLE IF NOT EXISTS devoluciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id INTEGER NOT NULL,
                    fecha DATE DEFAULT CURRENT_DATE,
                    motivo TEXT,
                    monto REAL NOT NULL,
                    usuario_id INTEGER,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (venta_id) REFERENCES ventas(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            ''',
            'auditoria': '''
                CREATE TABLE IF NOT EXISTS auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    accion TEXT NOT NULL,
                    tabla TEXT,
                    registro_id INTEGER,
                    detalles TEXT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            ''',
            'configuraciones': '''
                CREATE TABLE IF NOT EXISTS configuraciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clave TEXT UNIQUE NOT NULL,
                    valor TEXT NOT NULL,
                    descripcion TEXT,
                    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        }
        
        try:
            with self.get_db_cursor() as cursor:
                for tabla, sql in tablas.items():
                    cursor.execute(sql)
                    self.logger.info(f"Tabla {tabla} inicializada correctamente")
                
                # Crear usuario admin por defecto si no existe
                cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = ?", (DEFAULT_ADMIN_USERNAME,))
                if cursor.fetchone()[0] == 0:
                    password_hash = hashlib.sha256(DEFAULT_ADMIN_PASSWORD.encode()).hexdigest()
                    cursor.execute("""
                        INSERT INTO usuarios (nombre, usuario, password, rol) 
                        VALUES (?, ?, ?, ?)
                    """, ("Administrador", DEFAULT_ADMIN_USERNAME, password_hash, "admin"))
                    self.logger.info("Usuario administrador creado por defecto")
                
                # Crear configuraciones por defecto
                configs_default = [
                    ('tasa_iva', str(DEFAULT_IVA_RATE), 'Tasa de IVA'),
                    ('regimen_emisor', DEFAULT_REGIMEN_EMISOR, 'Régimen del emisor'),
                    ('tasa_dolar', '560.0', 'Tasa de cambio del dólar')
                ]
                
                for clave, valor, desc in configs_default:
                    cursor.execute("SELECT COUNT(*) FROM configuraciones WHERE clave = ?", (clave,))
                    if cursor.fetchone()[0] == 0:
                        cursor.execute("""
                            INSERT INTO configuraciones (clave, valor, descripcion) 
                            VALUES (?, ?, ?)
                        """, (clave, valor, desc))
                
                self.logger.info("Todas las tablas han sido inicializadas correctamente")
                        
        except Exception as e:
            self.logger.error(f"Error al inicializar tablas: {e}")
            raise