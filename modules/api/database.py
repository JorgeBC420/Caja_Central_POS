"""
Manejo avanzado de base de datos para el sistema POS
Incluye manejo de conexiones, transacciones, migraciones y respaldos
"""

import sqlite3
import json
import logging
import os
import shutil
import threading
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
import hashlib
import time

@dataclass
class ConfiguracionDB:
    """Configuración de base de datos"""
    db_path: str
    backup_path: str
    max_connections: int = 10
    timeout: float = 30.0
    enable_wal: bool = True
    enable_foreign_keys: bool = True
    cache_size: int = 2000
    page_size: int = 4096
    
class DatabaseManager:
    """Gestor avanzado de base de datos SQLite"""
    
    def __init__(self, config: ConfiguracionDB = None):
        self.logger = logging.getLogger(__name__)
        
        if config is None:
            self.config = ConfiguracionDB(
                db_path="caja_registradora_pos_cr.db",
                backup_path="backups/"
            )
        else:
            self.config = config
        
        self._connection_pool = []
        self._pool_lock = threading.Lock()
        self._schema_version = self._get_schema_version()
        
        # Inicializar base de datos
        self._initialize_database()
    
    def _initialize_database(self):
        """Inicializa la base de datos con configuraciones optimizadas"""
        try:
            # Crear directorio de backups si no existe
            os.makedirs(self.config.backup_path, exist_ok=True)
            
            # Configurar base de datos
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Configuraciones de rendimiento
                if self.config.enable_wal:
                    cursor.execute("PRAGMA journal_mode=WAL")
                
                if self.config.enable_foreign_keys:
                    cursor.execute("PRAGMA foreign_keys=ON")
                
                cursor.execute(f"PRAGMA cache_size={self.config.cache_size}")
                cursor.execute(f"PRAGMA page_size={self.config.page_size}")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
                
                # Crear tablas base
                self._create_base_tables(cursor)
                
                # Aplicar migraciones si es necesario
                self._apply_migrations(conn)
                
                conn.commit()
                
            self.logger.info("Base de datos inicializada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando base de datos: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager para obtener conexión de BD"""
        conn = None
        try:
            conn = self._get_pooled_connection()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Error en conexión de BD: {e}")
            raise
        finally:
            if conn:
                self._return_to_pool(conn)
    
    def _get_pooled_connection(self) -> sqlite3.Connection:
        """Obtiene conexión del pool o crea nueva"""
        with self._pool_lock:
            if self._connection_pool:
                return self._connection_pool.pop()
        
        # Crear nueva conexión
        conn = sqlite3.connect(
            self.config.db_path,
            timeout=self.config.timeout,
            check_same_thread=False
        )
        
        # Configurar conexión
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        
        return conn
    
    def _return_to_pool(self, conn: sqlite3.Connection):
        """Retorna conexión al pool"""
        try:
            with self._pool_lock:
                if len(self._connection_pool) < self.config.max_connections:
                    self._connection_pool.append(conn)
                else:
                    conn.close()
        except Exception as e:
            self.logger.warning(f"Error retornando conexión al pool: {e}")
            try:
                conn.close()
            except:
                pass
    
    def _create_base_tables(self, cursor: sqlite3.Cursor):
        """Crea las tablas base del sistema"""
        
        # Tabla de versión de esquema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_date TEXT NOT NULL,
                description TEXT
            )
        """)
        
        # Tabla de configuraciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuraciones (
                clave TEXT PRIMARY KEY,
                valor TEXT NOT NULL,
                categoria TEXT DEFAULT 'general',
                fecha_modificacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                nombre TEXT NOT NULL,
                apellidos TEXT,
                email TEXT,
                telefono TEXT,
                rol TEXT NOT NULL DEFAULT 'vendedor',
                activo INTEGER DEFAULT 1,
                ultimo_acceso TEXT,
                intentos_fallidos INTEGER DEFAULT 0,
                bloqueado_hasta TEXT,
                fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de sesiones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sesiones (
                id TEXT PRIMARY KEY,
                usuario_id INTEGER NOT NULL,
                fecha_inicio TEXT NOT NULL,
                fecha_expiracion TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                activa INTEGER DEFAULT 1,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Tabla de clientes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellidos TEXT,
                identificacion TEXT UNIQUE,
                tipo_identificacion TEXT DEFAULT 'cedula',
                telefono TEXT,
                email TEXT,
                direccion TEXT,
                fecha_nacimiento TEXT,
                activo INTEGER DEFAULT 1,
                descuento_porcentaje REAL DEFAULT 0,
                limite_credito REAL DEFAULT 0,
                saldo_actual REAL DEFAULT 0,
                fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de proveedores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                contacto TEXT,
                telefono TEXT,
                email TEXT,
                direccion TEXT,
                cedula_juridica TEXT,
                activo INTEGER DEFAULT 1,
                dias_credito INTEGER DEFAULT 30,
                limite_credito REAL DEFAULT 0,
                fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de categorías
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                descripcion TEXT,
                activa INTEGER DEFAULT 1,
                fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de productos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                codigo_barras TEXT,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                categoria_id INTEGER,
                proveedor_id INTEGER,
                precio_compra REAL NOT NULL DEFAULT 0,
                precio_venta REAL NOT NULL DEFAULT 0,
                precio_mayoreo REAL DEFAULT 0,
                cantidad_mayoreo INTEGER DEFAULT 1,
                stock_actual INTEGER DEFAULT 0,
                stock_minimo INTEGER DEFAULT 1,
                stock_maximo INTEGER DEFAULT 100,
                unidad_medida TEXT DEFAULT 'unidad',
                aplica_iva INTEGER DEFAULT 1,
                porcentaje_iva REAL DEFAULT 13.0,
                activo INTEGER DEFAULT 1,
                fecha_vencimiento TEXT,
                ubicacion TEXT,
                fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (categoria_id) REFERENCES categorias(id),
                FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
            )
        """)
        
        # Tabla de ventas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_venta TEXT NOT NULL UNIQUE,
                cliente_id INTEGER,
                usuario_id INTEGER NOT NULL,
                fecha_venta TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                subtotal REAL NOT NULL DEFAULT 0,
                descuento REAL DEFAULT 0,
                iva REAL DEFAULT 0,
                total REAL NOT NULL DEFAULT 0,
                estado TEXT DEFAULT 'completada',
                metodo_pago TEXT DEFAULT 'efectivo',
                monto_recibido REAL DEFAULT 0,
                cambio REAL DEFAULT 0,
                notas TEXT,
                clave_hacienda TEXT,
                estado_hacienda TEXT,
                fecha_modificacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Tabla de detalle de ventas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario REAL NOT NULL,
                descuento REAL DEFAULT 0,
                subtotal REAL NOT NULL,
                iva REAL DEFAULT 0,
                total REAL NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            )
        """)
        
        # Tabla de compras
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_compra TEXT NOT NULL UNIQUE,
                proveedor_id INTEGER NOT NULL,
                usuario_id INTEGER NOT NULL,
                fecha_compra TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                subtotal REAL NOT NULL DEFAULT 0,
                iva REAL DEFAULT 0,
                total REAL NOT NULL DEFAULT 0,
                estado TEXT DEFAULT 'recibida',
                fecha_vencimiento TEXT,
                notas TEXT,
                fecha_modificacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Tabla de detalle de compras
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compra_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                iva REAL DEFAULT 0,
                total REAL NOT NULL,
                FOREIGN KEY (compra_id) REFERENCES compras(id) ON DELETE CASCADE,
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            )
        """)
        
        # Tabla de movimientos de inventario
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimientos_inventario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                tipo_movimiento TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                stock_anterior INTEGER NOT NULL,
                stock_nuevo INTEGER NOT NULL,
                precio_unitario REAL,
                referencia_id INTEGER,
                referencia_tipo TEXT,
                usuario_id INTEGER,
                fecha_movimiento TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                notas TEXT,
                FOREIGN KEY (producto_id) REFERENCES productos(id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Tabla de apartados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS apartados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_apartado TEXT NOT NULL UNIQUE,
                cliente_id INTEGER NOT NULL,
                usuario_id INTEGER NOT NULL,
                fecha_apartado TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fecha_vencimiento TEXT,
                subtotal REAL NOT NULL DEFAULT 0,
                descuento REAL DEFAULT 0,
                iva REAL DEFAULT 0,
                total REAL NOT NULL DEFAULT 0,
                abono REAL DEFAULT 0,
                saldo REAL NOT NULL DEFAULT 0,
                estado TEXT DEFAULT 'activo',
                notas TEXT,
                fecha_modificacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Tabla de pagos de apartados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagos_apartados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                apartado_id INTEGER NOT NULL,
                monto REAL NOT NULL,
                metodo_pago TEXT NOT NULL,
                usuario_id INTEGER NOT NULL,
                fecha_pago TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                notas TEXT,
                FOREIGN KEY (apartado_id) REFERENCES apartados(id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Tabla de documentos electrónicos (Hacienda)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documentos_electronicos (
                clave TEXT PRIMARY KEY,
                tipo_documento TEXT NOT NULL,
                numero_consecutivo TEXT NOT NULL,
                venta_id INTEGER,
                estado TEXT NOT NULL DEFAULT 'pendiente',
                xml_content TEXT,
                respuesta_hacienda TEXT,
                fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (venta_id) REFERENCES ventas(id)
            )
        """)
        
        # Tabla de XML documentos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS xml_documentos (
                clave TEXT PRIMARY KEY,
                xml_content TEXT NOT NULL,
                fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de auditoria
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tabla TEXT NOT NULL,
                operacion TEXT NOT NULL,
                registro_id INTEGER,
                datos_anteriores TEXT,
                datos_nuevos TEXT,
                usuario_id INTEGER,
                ip_address TEXT,
                user_agent TEXT,
                fecha_operacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Tabla de respaldos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS respaldos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_archivo TEXT NOT NULL,
                ruta_archivo TEXT NOT NULL,
                tamaño_bytes INTEGER,
                usuario_id INTEGER,
                tipo_respaldo TEXT DEFAULT 'manual',
                fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                notas TEXT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear índices para optimizar consultas
        self._create_indexes(cursor)
    
    def _create_indexes(self, cursor: sqlite3.Cursor):
        """Crea índices para optimizar consultas"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_usuarios_usuario ON usuarios(usuario)",
            "CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email)",
            "CREATE INDEX IF NOT EXISTS idx_clientes_identificacion ON clientes(identificacion)",
            "CREATE INDEX IF NOT EXISTS idx_productos_codigo ON productos(codigo)",
            "CREATE INDEX IF NOT EXISTS idx_productos_codigo_barras ON productos(codigo_barras)",
            "CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_numero ON ventas(numero_venta)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha_venta)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_cliente ON ventas(cliente_id)",
            "CREATE INDEX IF NOT EXISTS idx_detalle_ventas_venta ON detalle_ventas(venta_id)",
            "CREATE INDEX IF NOT EXISTS idx_detalle_ventas_producto ON detalle_ventas(producto_id)",
            "CREATE INDEX IF NOT EXISTS idx_movimientos_producto ON movimientos_inventario(producto_id)",
            "CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos_inventario(fecha_movimiento)",
            "CREATE INDEX IF NOT EXISTS idx_apartados_cliente ON apartados(cliente_id)",
            "CREATE INDEX IF NOT EXISTS idx_apartados_fecha ON apartados(fecha_apartado)",
            "CREATE INDEX IF NOT EXISTS idx_documentos_tipo ON documentos_electronicos(tipo_documento)",
            "CREATE INDEX IF NOT EXISTS idx_documentos_estado ON documentos_electronicos(estado)",
            "CREATE INDEX IF NOT EXISTS idx_auditoria_tabla ON auditoria(tabla)",
            "CREATE INDEX IF NOT EXISTS idx_auditoria_fecha ON auditoria(fecha_operacion)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except sqlite3.Error as e:
                self.logger.warning(f"Error creando índice: {e}")
    
    def _get_schema_version(self) -> int:
        """Obtiene la versión actual del esquema"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(version) FROM schema_version")
                result = cursor.fetchone()
                return result[0] if result[0] is not None else 0
        except:
            return 0
    
    def _apply_migrations(self, conn: sqlite3.Connection):
        """Aplica migraciones de base de datos"""
        current_version = self._get_schema_version()
        target_version = 1  # Versión objetivo actual
        
        if current_version < target_version:
            self.logger.info(f"Aplicando migraciones desde v{current_version} a v{target_version}")
            
            cursor = conn.cursor()
            
            # Migración v1: Configuraciones iniciales
            if current_version < 1:
                self._apply_migration_v1(cursor)
                current_version = 1
            
            # Actualizar versión del esquema
            cursor.execute("""
                INSERT OR REPLACE INTO schema_version (version, applied_date, description)
                VALUES (?, ?, ?)
            """, (target_version, datetime.now().isoformat(), f"Migración a versión {target_version}"))
            
            conn.commit()
            self.logger.info("Migraciones aplicadas correctamente")
    
    def _apply_migration_v1(self, cursor: sqlite3.Cursor):
        """Aplica migración versión 1"""
        # Configuraciones por defecto
        configuraciones_default = [
            ('empresa_nombre', 'CajaCentralPOS', 'general'),
            ('empresa_cedula', '', 'general'),
            ('empresa_telefono', '', 'general'),
            ('empresa_email', '', 'general'),
            ('empresa_direccion', '', 'general'),
            ('moneda_simbolo', '₡', 'general'),
            ('moneda_codigo', 'CRC', 'general'),
            ('iva_porcentaje', '13.0', 'impuestos'),
            ('numero_factura_actual', '1', 'numeracion'),
            ('numero_apartado_actual', '1', 'numeracion'),
            ('backup_automatico', 'True', 'backup'),
            ('backup_frecuencia_horas', '24', 'backup'),
            ('stock_minimo_alertas', 'True', 'inventario'),
            ('precio_incluye_iva', 'False', 'precios'),
            ('redondeo_decimales', '2', 'precios')
        ]
        
        for clave, valor, categoria in configuraciones_default:
            cursor.execute("""
                INSERT OR IGNORE INTO configuraciones (clave, valor, categoria)
                VALUES (?, ?, ?)
            """, (clave, valor, categoria))
        
        # Usuario administrador por defecto
        import secrets
        salt = secrets.token_hex(32)
        password = "admin123"  # Cambiar en producción
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
        
        cursor.execute("""
            INSERT OR IGNORE INTO usuarios (
                usuario, password_hash, salt, nombre, apellidos, email, rol
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('admin', password_hash, salt, 'Administrador', 'Sistema', 'admin@pos.com', 'administrador'))
    
    def ejecutar_consulta(self, query: str, params: Tuple = (), fetch: str = 'none') -> Any:
        """
        Ejecuta una consulta SQL de forma segura
        
        Args:
            query: Consulta SQL a ejecutar
            params: Parámetros para la consulta
            fetch: 'none', 'one', 'all' para determinar qué retornar
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if fetch == 'one':
                    return cursor.fetchone()
                elif fetch == 'all':
                    return cursor.fetchall()
                elif fetch == 'none':
                    conn.commit()
                    return cursor.rowcount
                
        except Exception as e:
            self.logger.error(f"Error ejecutando consulta: {e}")
            self.logger.error(f"Query: {query}")
            self.logger.error(f"Params: {params}")
            raise
    
    def ejecutar_transaccion(self, operations: List[Tuple[str, Tuple]]) -> bool:
        """
        Ejecuta múltiples operaciones en una transacción
        
        Args:
            operations: Lista de tuplas (query, params)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for query, params in operations:
                    cursor.execute(query, params)
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error en transacción: {e}")
            return False
    
    def backup_database(self, backup_name: str = None, usuario_id: int = None) -> Tuple[bool, str]:
        """Crea respaldo completo de la base de datos"""
        try:
            if backup_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}.db"
            
            backup_path = os.path.join(self.config.backup_path, backup_name)
            
            # Crear respaldo
            shutil.copy2(self.config.db_path, backup_path)
            
            # Registrar respaldo
            file_size = os.path.getsize(backup_path)
            
            self.ejecutar_consulta("""
                INSERT INTO respaldos (
                    nombre_archivo, ruta_archivo, tamaño_bytes, usuario_id, tipo_respaldo
                ) VALUES (?, ?, ?, ?, ?)
            """, (backup_name, backup_path, file_size, usuario_id, 'manual'))
            
            self.logger.info(f"Respaldo creado exitosamente: {backup_path}")
            return True, backup_path
            
        except Exception as e:
            error_msg = f"Error creando respaldo: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def restore_database(self, backup_path: str, usuario_id: int = None) -> Tuple[bool, str]:
        """Restaura base de datos desde respaldo"""
        try:
            # Verificar que el archivo existe
            if not os.path.exists(backup_path):
                return False, "Archivo de respaldo no encontrado"
            
            # Crear respaldo actual antes de restaurar
            current_backup_ok, current_backup_path = self.backup_database(
                f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                usuario_id
            )
            
            if not current_backup_ok:
                return False, "Error creando respaldo de seguridad"
            
            # Cerrar todas las conexiones
            with self._pool_lock:
                for conn in self._connection_pool:
                    conn.close()
                self._connection_pool.clear()
            
            # Restaurar
            shutil.copy2(backup_path, self.config.db_path)
            
            # Reinicializar
            self._initialize_database()
            
            self.logger.info(f"Base de datos restaurada desde: {backup_path}")
            return True, "Base de datos restaurada exitosamente"
            
        except Exception as e:
            error_msg = f"Error restaurando base de datos: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def obtener_estadisticas_db(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la base de datos"""
        try:
            stats = {}
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Información general
                cursor.execute("PRAGMA database_list")
                db_info = cursor.fetchall()
                stats['database_info'] = [dict(row) for row in db_info]
                
                # Tamaño de archivo
                stats['file_size_bytes'] = os.path.getsize(self.config.db_path)
                stats['file_size_mb'] = round(stats['file_size_bytes'] / (1024 * 1024), 2)
                
                # Conteo de registros por tabla
                tables = [
                    'usuarios', 'clientes', 'productos', 'ventas', 'detalle_ventas',
                    'compras', 'detalle_compras', 'apartados', 'movimientos_inventario',
                    'documentos_electronicos', 'auditoria', 'respaldos'
                ]
                
                stats['record_counts'] = {}
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        stats['record_counts'][table] = count
                    except:
                        stats['record_counts'][table] = 0
                
                # Información de índices
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
                indexes = cursor.fetchall()
                stats['indexes_count'] = len(indexes)
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def optimizar_database(self) -> Tuple[bool, str]:
        """Optimiza la base de datos"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # VACUUM para optimizar espacio
                cursor.execute("VACUUM")
                
                # ANALYZE para actualizar estadísticas
                cursor.execute("ANALYZE")
                
                # Reindexar
                cursor.execute("REINDEX")
                
                conn.commit()
            
            self.logger.info("Base de datos optimizada correctamente")
            return True, "Optimización completada"
            
        except Exception as e:
            error_msg = f"Error optimizando base de datos: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def limpiar_datos_antiguos(self, dias_antiguedad: int = 365) -> Tuple[bool, str]:
        """Limpia datos antiguos de la base de datos"""
        try:
            fecha_limite = (datetime.now() - timedelta(days=dias_antiguedad)).isoformat()
            
            operaciones = [
                # Limpiar sesiones expiradas
                ("DELETE FROM sesiones WHERE fecha_expiracion < ?", (datetime.now().isoformat(),)),
                
                # Limpiar auditoría antigua
                ("DELETE FROM auditoria WHERE fecha_operacion < ?", (fecha_limite,)),
                
                # Limpiar respaldos antiguos (mantener solo últimos 10)
                ("""DELETE FROM respaldos WHERE id NOT IN (
                    SELECT id FROM respaldos ORDER BY fecha_creacion DESC LIMIT 10
                )""", ()),
            ]
            
            exito = self.ejecutar_transaccion(operaciones)
            
            if exito:
                return True, f"Datos anteriores a {dias_antiguedad} días limpiados"
            else:
                return False, "Error limpiando datos antiguos"
                
        except Exception as e:
            error_msg = f"Error limpiando datos antiguos: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def cerrar_conexiones(self):
        """Cierra todas las conexiones del pool"""
        with self._pool_lock:
            for conn in self._connection_pool:
                try:
                    conn.close()
                except:
                    pass
            self._connection_pool.clear()

# Instancia global del gestor de base de datos
db_manager = DatabaseManager()

# Funciones de compatibilidad con código existente
def get_connection():
    """Función de compatibilidad"""
    return db_manager._get_pooled_connection()

def create_tables():
    """Función de compatibilidad"""
    db_manager._initialize_database()

def ejecutar_consulta_segura(query: str, params: Tuple = (), fetch: str = 'none') -> Any:
    """Función de utilidad para ejecutar consultas seguras"""
    return db_manager.ejecutar_consulta(query, params, fetch)

def get_db_cursor():
    """Context manager para obtener cursor de BD"""
    return db_manager.get_connection()