"""
Sistema de Auditoría Avanzado - Caja Central POS
Registro detallado de todas las operaciones del sistema
"""

import json
import logging
import sqlite3
from datetime import datetime, date
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from core.database import get_db_cursor

class TipoEvento(Enum):
    """Tipos de eventos auditables"""
    # Autenticación y sesiones
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FALLIDO = "login_fallido"
    SESION_EXPIRADA = "sesion_expirada"
    
    # Transacciones de venta
    VENTA_CREADA = "venta_creada"
    VENTA_MODIFICADA = "venta_modificada"
    VENTA_CANCELADA = "venta_cancelada"
    VENTA_ANULADA = "venta_anulada"
    DESCUENTO_APLICADO = "descuento_aplicado"
    
    # Inventario
    PRODUCTO_CREADO = "producto_creado"
    PRODUCTO_MODIFICADO = "producto_modificado"
    PRODUCTO_ELIMINADO = "producto_eliminado"
    INVENTARIO_AJUSTADO = "inventario_ajustado"
    TRANSFERENCIA_INVENTARIO = "transferencia_inventario"
    
    # Usuarios y permisos
    USUARIO_CREADO = "usuario_creado"
    USUARIO_MODIFICADO = "usuario_modificado"
    USUARIO_ELIMINADO = "usuario_eliminado"
    CAMBIO_ROL = "cambio_rol"
    CAMBIO_PERMISOS = "cambio_permisos"
    
    # Configuración
    CONFIG_MODIFICADA = "config_modificada"
    PARAMETROS_FACTURACION = "parametros_facturacion"
    CONFIGURACION_IMPRESORA = "configuracion_impresora"
    
    # Facturación electrónica
    FACTURA_ENVIADA = "factura_enviada"
    FACTURA_ACEPTADA = "factura_aceptada"
    FACTURA_RECHAZADA = "factura_rechazada"
    CERTIFICADO_ACTUALIZADO = "certificado_actualizado"
    
    # Base de datos
    BACKUP_CREADO = "backup_creado"
    BACKUP_RESTAURADO = "backup_restaurado"
    MANTENIMIENTO_BD = "mantenimiento_bd"
    
    # Sistema
    SISTEMA_INICIADO = "sistema_iniciado"
    SISTEMA_DETENIDO = "sistema_detenido"
    ERROR_CRITICO = "error_critico"
    ACTUALIZACION_SISTEMA = "actualizacion_sistema"
    
    # Multi-tienda
    SINCRONIZACION_TIENDA = "sincronizacion_tienda"
    TRANSFERENCIA_PRODUCTOS = "transferencia_productos"
    
    # Restaurante
    MESA_ABIERTA = "mesa_abierta"
    MESA_CERRADA = "mesa_cerrada"
    ORDEN_COCINA = "orden_cocina"
    CUENTA_DIVIDIDA = "cuenta_dividida"

class NivelGravedad(Enum):
    """Niveles de gravedad de los eventos"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class EventoAuditoria:
    """Estructura de un evento de auditoría"""
    tipo_evento: TipoEvento
    usuario_id: str
    usuario_nombre: str
    nivel_gravedad: NivelGravedad
    descripcion: str
    detalles: Dict[str, Any]
    ip_address: str = ""
    user_agent: str = ""
    modulo: str = ""
    tabla_afectada: str = ""
    registro_id: str = ""
    valores_anteriores: Dict[str, Any] = None
    valores_nuevos: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.valores_anteriores is None:
            self.valores_anteriores = {}
        if self.valores_nuevos is None:
            self.valores_nuevos = {}

class SistemaAuditoriaAvanzado:
    """Sistema completo de auditoría avanzado"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._init_database()
        self._configuracion = self._cargar_configuracion()
    
    def _init_database(self):
        """Inicializar tablas de auditoría"""
        try:
            with get_db_cursor() as cursor:
                # Tabla principal de eventos de auditoría
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS auditoria_eventos_avanzada (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tipo_evento TEXT NOT NULL,
                        usuario_id TEXT NOT NULL,
                        usuario_nombre TEXT NOT NULL,
                        nivel_gravedad TEXT NOT NULL,
                        descripcion TEXT NOT NULL,
                        detalles TEXT,  -- JSON
                        ip_address TEXT,
                        user_agent TEXT,
                        modulo TEXT,
                        tabla_afectada TEXT,
                        registro_id TEXT,
                        valores_anteriores TEXT,  -- JSON
                        valores_nuevos TEXT,  -- JSON
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        fecha_creacion DATE DEFAULT (DATE('now'))
                    )
                ''')
                
                # Crear índices para mejorar rendimiento
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_auditoria_avanzada_tipo ON auditoria_eventos_avanzada(tipo_evento)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_auditoria_avanzada_usuario ON auditoria_eventos_avanzada(usuario_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_auditoria_avanzada_fecha ON auditoria_eventos_avanzada(fecha_creacion)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_auditoria_avanzada_gravedad ON auditoria_eventos_avanzada(nivel_gravedad)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_auditoria_avanzada_tabla ON auditoria_eventos_avanzada(tabla_afectada)')
                
                # Tabla de configuración de auditoría
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS auditoria_configuracion_avanzada (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        clave TEXT UNIQUE NOT NULL,
                        valor TEXT NOT NULL,
                        descripcion TEXT,
                        fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                self._insertar_configuracion_defecto(cursor)
                
        except Exception as e:
            self.logger.error(f"Error inicializando base de datos de auditoría avanzada: {e}")
    
    def _insertar_configuracion_defecto(self, cursor):
        """Insertar configuración por defecto"""
        config_defecto = [
            ('auditoria_activa', 'true', 'Sistema de auditoría activo'),
            ('nivel_minimo', 'info', 'Nivel mínimo de eventos a registrar'),
            ('max_eventos_por_dia', '10000', 'Máximo de eventos por día'),
            ('purga_automatica', 'true', 'Purga automática de eventos antiguos'),
            ('dias_retencion', '365', 'Días de retención de eventos'),
            ('notificar_eventos_criticos', 'true', 'Notificar eventos críticos'),
            ('incluir_detalles_completos', 'true', 'Incluir detalles completos en eventos'),
            ('registrar_ip', 'true', 'Registrar dirección IP del usuario'),
        ]
        
        for clave, valor, descripcion in config_defecto:
            cursor.execute('''
                INSERT OR IGNORE INTO auditoria_configuracion_avanzada (clave, valor, descripcion) 
                VALUES (?, ?, ?)
            ''', (clave, valor, descripcion))
    
    def _cargar_configuracion(self) -> Dict[str, Any]:
        """Cargar configuración de auditoría"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute('SELECT clave, valor FROM auditoria_configuracion_avanzada')
                config = {}
                for row in cursor.fetchall():
                    clave, valor = row
                    # Convertir valores booleanos
                    if valor.lower() in ('true', 'false'):
                        config[clave] = valor.lower() == 'true'
                    elif valor.isdigit():
                        config[clave] = int(valor)
                    else:
                        config[clave] = valor
                return config
        except Exception as e:
            self.logger.error(f"Error cargando configuración de auditoría: {e}")
            return {}
    
    def registrar_evento(self, evento: EventoAuditoria) -> bool:
        """Registrar un evento de auditoría"""
        if not self._configuracion.get('auditoria_activa', True):
            return True
        
        try:
            # Verificar nivel mínimo
            nivel_minimo = self._configuracion.get('nivel_minimo', 'info')
            niveles_orden = ['info', 'warning', 'error', 'critical']
            
            if niveles_orden.index(evento.nivel_gravedad.value) < niveles_orden.index(nivel_minimo):
                return True
            
            with get_db_cursor() as cursor:
                cursor.execute('''
                    INSERT INTO auditoria_eventos_avanzada (
                        tipo_evento, usuario_id, usuario_nombre, nivel_gravedad,
                        descripcion, detalles, ip_address, user_agent, modulo,
                        tabla_afectada, registro_id, valores_anteriores, valores_nuevos,
                        timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    evento.tipo_evento.value,
                    evento.usuario_id,
                    evento.usuario_nombre,
                    evento.nivel_gravedad.value,
                    evento.descripcion,
                    json.dumps(evento.detalles, ensure_ascii=False),
                    evento.ip_address,
                    evento.user_agent,
                    evento.modulo,
                    evento.tabla_afectada,
                    evento.registro_id,
                    json.dumps(evento.valores_anteriores, ensure_ascii=False),
                    json.dumps(evento.valores_nuevos, ensure_ascii=False),
                    evento.timestamp
                ))
            
            # Notificar eventos críticos si está configurado
            if (evento.nivel_gravedad == NivelGravedad.CRITICAL and 
                self._configuracion.get('notificar_eventos_criticos', True)):
                self._notificar_evento_critico(evento)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error registrando evento de auditoría: {e}")
            return False
    
    def _notificar_evento_critico(self, evento: EventoAuditoria):
        """Notificar evento crítico"""
        self.logger.critical(f"EVENTO CRÍTICO: {evento.descripcion} - Usuario: {evento.usuario_nombre}")
    
    def obtener_eventos(self, filtros: Dict[str, Any] = None, 
                       limite: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Obtener eventos de auditoría con filtros"""
        try:
            where_clauses = []
            params = []
            
            if filtros:
                if 'usuario_id' in filtros:
                    where_clauses.append('usuario_id = ?')
                    params.append(filtros['usuario_id'])
                
                if 'tipo_evento' in filtros:
                    where_clauses.append('tipo_evento = ?')
                    params.append(filtros['tipo_evento'])
                
                if 'nivel_gravedad' in filtros:
                    where_clauses.append('nivel_gravedad = ?')
                    params.append(filtros['nivel_gravedad'])
                
                if 'fecha_desde' in filtros:
                    where_clauses.append('DATE(timestamp) >= ?')
                    params.append(filtros['fecha_desde'])
                
                if 'fecha_hasta' in filtros:
                    where_clauses.append('DATE(timestamp) <= ?')
                    params.append(filtros['fecha_hasta'])
                
                if 'modulo' in filtros:
                    where_clauses.append('modulo = ?')
                    params.append(filtros['modulo'])
            
            where_sql = ' WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''
            
            query = f'''
                SELECT id, tipo_evento, usuario_id, usuario_nombre, nivel_gravedad,
                       descripcion, detalles, ip_address, timestamp, modulo, tabla_afectada
                FROM auditoria_eventos_avanzada
                {where_sql}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            '''
            
            params.extend([limite, offset])
            
            with get_db_cursor() as cursor:
                cursor.execute(query, params)
                eventos = []
                
                for row in cursor.fetchall():
                    evento = {
                        'id': row[0],
                        'tipo_evento': row[1],
                        'usuario_id': row[2],
                        'usuario_nombre': row[3],
                        'nivel_gravedad': row[4],
                        'descripcion': row[5],
                        'detalles': json.loads(row[6]) if row[6] else {},
                        'ip_address': row[7],
                        'timestamp': row[8],
                        'modulo': row[9],
                        'tabla_afectada': row[10]
                    }
                    eventos.append(evento)
                
                return eventos
                
        except Exception as e:
            self.logger.error(f"Error obteniendo eventos de auditoría: {e}")
            return []
    
    def obtener_estadisticas(self, fecha_desde: date = None, 
                           fecha_hasta: date = None) -> Dict[str, Any]:
        """Obtener estadísticas de auditoría"""
        try:
            fecha_desde = fecha_desde or date.today().replace(day=1)
            fecha_hasta = fecha_hasta or date.today()
            
            with get_db_cursor() as cursor:
                # Total de eventos
                cursor.execute('''
                    SELECT COUNT(*) FROM auditoria_eventos_avanzada 
                    WHERE DATE(timestamp) BETWEEN ? AND ?
                ''', (fecha_desde, fecha_hasta))
                total_eventos = cursor.fetchone()[0]
                
                # Eventos por tipo
                cursor.execute('''
                    SELECT tipo_evento, COUNT(*) 
                    FROM auditoria_eventos_avanzada 
                    WHERE DATE(timestamp) BETWEEN ? AND ?
                    GROUP BY tipo_evento
                    ORDER BY COUNT(*) DESC
                ''', (fecha_desde, fecha_hasta))
                eventos_por_tipo = dict(cursor.fetchall())
                
                # Eventos por usuario
                cursor.execute('''
                    SELECT usuario_nombre, COUNT(*) 
                    FROM auditoria_eventos_avanzada 
                    WHERE DATE(timestamp) BETWEEN ? AND ?
                    GROUP BY usuario_id, usuario_nombre
                    ORDER BY COUNT(*) DESC
                    LIMIT 10
                ''', (fecha_desde, fecha_hasta))
                eventos_por_usuario = dict(cursor.fetchall())
                
                # Eventos por nivel de gravedad
                cursor.execute('''
                    SELECT nivel_gravedad, COUNT(*) 
                    FROM auditoria_eventos_avanzada 
                    WHERE DATE(timestamp) BETWEEN ? AND ?
                    GROUP BY nivel_gravedad
                ''', (fecha_desde, fecha_hasta))
                eventos_por_gravedad = dict(cursor.fetchall())
                
                return {
                    'total_eventos': total_eventos,
                    'eventos_por_tipo': eventos_por_tipo,
                    'eventos_por_usuario': eventos_por_usuario,
                    'eventos_por_gravedad': eventos_por_gravedad,
                    'periodo': f"{fecha_desde} - {fecha_hasta}"
                }
                
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas de auditoría: {e}")
            return {}
    
    def purgar_eventos_antiguos(self) -> int:
        """Purgar eventos antiguos según configuración"""
        if not self._configuracion.get('purga_automatica', True):
            return 0
        
        try:
            dias_retencion = self._configuracion.get('dias_retencion', 365)
            
            with get_db_cursor() as cursor:
                cursor.execute('''
                    DELETE FROM auditoria_eventos_avanzada 
                    WHERE DATE(timestamp) < DATE('now', '-{} days')
                '''.format(dias_retencion))
                
                eventos_eliminados = cursor.rowcount
                
                if eventos_eliminados > 0:
                    self.logger.info(f"Purgados {eventos_eliminados} eventos de auditoría antiguos")
                
                return eventos_eliminados
                
        except Exception as e:
            self.logger.error(f"Error purgando eventos antiguos: {e}")
            return 0

# Instancia global del sistema de auditoría avanzado
auditoria_avanzada = SistemaAuditoriaAvanzado()

# Funciones de conveniencia para registro de eventos comunes
def registrar_login_avanzado(usuario_id: str, usuario_nombre: str, ip: str = "", exito: bool = True):
    """Registrar evento de login avanzado"""
    tipo_evento = TipoEvento.LOGIN if exito else TipoEvento.LOGIN_FALLIDO
    nivel = NivelGravedad.INFO if exito else NivelGravedad.WARNING
    
    evento = EventoAuditoria(
        tipo_evento=tipo_evento,
        usuario_id=usuario_id,
        usuario_nombre=usuario_nombre,
        nivel_gravedad=nivel,
        descripcion=f"{'Inicio de sesión exitoso' if exito else 'Intento de login fallido'} para {usuario_nombre}",
        detalles={'exito': exito, 'timestamp': datetime.now().isoformat()},
        ip_address=ip,
        modulo='autenticacion'
    )
    
    return auditoria_avanzada.registrar_evento(evento)

def registrar_venta_avanzada(usuario_id: str, usuario_nombre: str, venta_id: str, 
                            total: float, cliente: str = "", metodo_pago: str = ""):
    """Registrar evento de venta avanzado"""
    evento = EventoAuditoria(
        tipo_evento=TipoEvento.VENTA_CREADA,
        usuario_id=usuario_id,
        usuario_nombre=usuario_nombre,
        nivel_gravedad=NivelGravedad.INFO,
        descripcion=f"Venta registrada por {usuario_nombre} - Total: ₡{total:,.2f}",
        detalles={
            'venta_id': venta_id,
            'total': total,
            'cliente': cliente,
            'metodo_pago': metodo_pago,
            'timestamp': datetime.now().isoformat()
        },
        modulo='ventas',
        tabla_afectada='ventas',
        registro_id=venta_id
    )
    
    return auditoria_avanzada.registrar_evento(evento)

def registrar_error_critico_avanzado(usuario_id: str, usuario_nombre: str, 
                                   error: str, modulo: str = "", contexto: Dict = None):
    """Registrar error crítico avanzado"""
    evento = EventoAuditoria(
        tipo_evento=TipoEvento.ERROR_CRITICO,
        usuario_id=usuario_id,
        usuario_nombre=usuario_nombre,
        nivel_gravedad=NivelGravedad.CRITICAL,
        descripcion=f"Error crítico en el sistema: {error}",
        detalles={
            'error': error, 
            'contexto': contexto or {},
            'timestamp': datetime.now().isoformat()
        },
        modulo=modulo
    )
    
    return auditoria_avanzada.registrar_evento(evento)
