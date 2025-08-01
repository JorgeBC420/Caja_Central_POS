"""
Modelos de registro y transacciones para el sistema POS
Sistema completo de logging de operaciones y auditoría
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal
import json

Base = declarative_base()

class TipoRegistro:
    """Tipos de registro en el sistema"""
    VENTA = "venta"
    DEVOLUCION = "devolucion"
    PAGO = "pago"
    INVENTARIO = "inventario"
    USUARIO = "usuario"
    CONFIGURACION = "configuracion"
    SISTEMA = "sistema"
    ERROR = "error"
    AUDITORIA = "auditoria"

class Registro(Base):
    """Registro básico de operaciones"""
    __tablename__ = "registros"
    
    id = Column(Integer, primary_key=True, index=True)
    descripcion = Column(String(500), nullable=False)
    monto = Column(Float, default=0.0)
    tipo = Column(String(50), nullable=False, index=True)
    fecha = Column(DateTime, default=datetime.now, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True, index=True)
    referencia_id = Column(Integer, nullable=True, index=True)  # ID de referencia a otra tabla
    referencia_tabla = Column(String(50), nullable=True)  # Nombre de la tabla referenciada
    activo = Column(Boolean, default=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el registro a diccionario"""
        return {
            'id': self.id,
            'descripcion': self.descripcion,
            'monto': self.monto,
            'tipo': self.tipo,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'usuario_id': self.usuario_id,
            'referencia_id': self.referencia_id,
            'referencia_tabla': self.referencia_tabla,
            'activo': self.activo
        }

class RegistroVenta(Base):
    """Registro específico de ventas"""
    __tablename__ = "registro_ventas"
    
    id = Column(Integer, primary_key=True, index=True)
    venta_id = Column(Integer, ForeignKey('ventas.id'), nullable=False, index=True)
    numero_venta = Column(String(50), nullable=False, index=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False, index=True)
    fecha_venta = Column(DateTime, nullable=False, index=True)
    subtotal = Column(Float, nullable=False)
    impuesto = Column(Float, nullable=False)
    descuento = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    items_count = Column(Integer, nullable=False)
    metodos_pago = Column(Text)  # JSON string con métodos de pago
    estado = Column(String(20), nullable=False, default='completada')
    observaciones = Column(Text)
    fecha_registro = Column(DateTime, default=datetime.now)
    
    def set_metodos_pago(self, metodos: list):
        """Establece los métodos de pago como JSON"""
        self.metodos_pago = json.dumps(metodos) if metodos else None
    
    def get_metodos_pago(self) -> list:
        """Obtiene los métodos de pago desde JSON"""
        if self.metodos_pago:
            try:
                return json.loads(self.metodos_pago)
            except json.JSONDecodeError:
                return []
        return []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el registro de venta a diccionario"""
        return {
            'id': self.id,
            'venta_id': self.venta_id,
            'numero_venta': self.numero_venta,
            'cliente_id': self.cliente_id,
            'usuario_id': self.usuario_id,
            'fecha_venta': self.fecha_venta.isoformat() if self.fecha_venta else None,
            'subtotal': self.subtotal,
            'impuesto': self.impuesto,
            'descuento': self.descuento,
            'total': self.total,
            'items_count': self.items_count,
            'metodos_pago': self.get_metodos_pago(),
            'estado': self.estado,
            'observaciones': self.observaciones,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None
        }

class RegistroInventario(Base):
    """Registro de movimientos de inventario"""
    __tablename__ = "registro_inventario"
    
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=False, index=True)
    tipo_movimiento = Column(String(20), nullable=False, index=True)  # entrada, salida, ajuste
    cantidad_anterior = Column(Float, nullable=False)
    cantidad_movimiento = Column(Float, nullable=False)
    cantidad_nueva = Column(Float, nullable=False)
    costo_unitario = Column(Float, default=0.0)
    valor_total = Column(Float, default=0.0)
    motivo = Column(String(100), nullable=False)
    documento_referencia = Column(String(50))
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False, index=True)
    fecha_movimiento = Column(DateTime, nullable=False, index=True)
    observaciones = Column(Text)
    fecha_registro = Column(DateTime, default=datetime.now)
    
    def calcular_valor_total(self):
        """Calcula el valor total del movimiento"""
        self.valor_total = abs(self.cantidad_movimiento) * self.costo_unitario
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el registro de inventario a diccionario"""
        return {
            'id': self.id,
            'producto_id': self.producto_id,
            'tipo_movimiento': self.tipo_movimiento,
            'cantidad_anterior': self.cantidad_anterior,
            'cantidad_movimiento': self.cantidad_movimiento,
            'cantidad_nueva': self.cantidad_nueva,
            'costo_unitario': self.costo_unitario,
            'valor_total': self.valor_total,
            'motivo': self.motivo,
            'documento_referencia': self.documento_referencia,
            'usuario_id': self.usuario_id,
            'fecha_movimiento': self.fecha_movimiento.isoformat() if self.fecha_movimiento else None,
            'observaciones': self.observaciones,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None
        }

class RegistroUsuario(Base):
    """Registro de actividades de usuarios"""
    __tablename__ = "registro_usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False, index=True)
    accion = Column(String(50), nullable=False, index=True)  # login, logout, crear, modificar, eliminar
    detalle = Column(Text)  # JSON con detalles de la acción
    ip_address = Column(String(45))  # IPv4 o IPv6
    user_agent = Column(String(500))
    resultado = Column(String(20), default='exitoso')  # exitoso, fallido, bloqueado
    fecha_accion = Column(DateTime, nullable=False, index=True)
    duracion_sesion = Column(Integer)  # En minutos para logout
    fecha_registro = Column(DateTime, default=datetime.now)
    
    def set_detalle(self, detalle: dict):
        """Establece el detalle como JSON"""
        self.detalle = json.dumps(detalle) if detalle else None
    
    def get_detalle(self) -> dict:
        """Obtiene el detalle desde JSON"""
        if self.detalle:
            try:
                return json.loads(self.detalle)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el registro de usuario a diccionario"""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'accion': self.accion,
            'detalle': self.get_detalle(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'resultado': self.resultado,
            'fecha_accion': self.fecha_accion.isoformat() if self.fecha_accion else None,
            'duracion_sesion': self.duracion_sesion,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None
        }

class RegistroError(Base):
    """Registro de errores del sistema"""
    __tablename__ = "registro_errores"
    
    id = Column(Integer, primary_key=True, index=True)
    modulo = Column(String(50), nullable=False, index=True)
    funcion = Column(String(100), nullable=False)
    mensaje_error = Column(Text, nullable=False)
    stack_trace = Column(Text)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True, index=True)
    ip_address = Column(String(45))
    parametros = Column(Text)  # JSON con parámetros que causaron el error
    severidad = Column(String(20), default='error', index=True)  # info, warning, error, critical
    resuelto = Column(Boolean, default=False, index=True)
    fecha_error = Column(DateTime, nullable=False, index=True)
    fecha_resolucion = Column(DateTime)
    notas_resolucion = Column(Text)
    fecha_registro = Column(DateTime, default=datetime.now)
    
    def set_parametros(self, parametros: dict):
        """Establece los parámetros como JSON"""
        self.parametros = json.dumps(parametros, default=str) if parametros else None
    
    def get_parametros(self) -> dict:
        """Obtiene los parámetros desde JSON"""
        if self.parametros:
            try:
                return json.loads(self.parametros)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def marcar_resuelto(self, notas: str = ""):
        """Marca el error como resuelto"""
        self.resuelto = True
        self.fecha_resolucion = datetime.now()
        self.notas_resolucion = notas
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el registro de error a diccionario"""
        return {
            'id': self.id,
            'modulo': self.modulo,
            'funcion': self.funcion,
            'mensaje_error': self.mensaje_error,
            'stack_trace': self.stack_trace,
            'usuario_id': self.usuario_id,
            'ip_address': self.ip_address,
            'parametros': self.get_parametros(),
            'severidad': self.severidad,
            'resuelto': self.resuelto,
            'fecha_error': self.fecha_error.isoformat() if self.fecha_error else None,
            'fecha_resolucion': self.fecha_resolucion.isoformat() if self.fecha_resolucion else None,
            'notas_resolucion': self.notas_resolucion,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None
        }

class RegistroConfiguracion(Base):
    """Registro de cambios de configuración"""
    __tablename__ = "registro_configuracion"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False, index=True)
    modulo = Column(String(50), nullable=False, index=True)
    clave_configuracion = Column(String(100), nullable=False, index=True)
    valor_anterior = Column(Text)
    valor_nuevo = Column(Text)
    descripcion = Column(String(200))
    ip_address = Column(String(45))
    fecha_cambio = Column(DateTime, nullable=False, index=True)
    fecha_registro = Column(DateTime, default=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el registro de configuración a diccionario"""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'modulo': self.modulo,
            'clave_configuracion': self.clave_configuracion,
            'valor_anterior': self.valor_anterior,
            'valor_nuevo': self.valor_nuevo,
            'descripcion': self.descripcion,
            'ip_address': self.ip_address,
            'fecha_cambio': self.fecha_cambio.isoformat() if self.fecha_cambio else None,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None
        }

class RegistroBackup(Base):
    """Registro de backups y restauraciones"""
    __tablename__ = "registro_backups"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo_operacion = Column(String(20), nullable=False, index=True)  # backup, restore
    archivo_backup = Column(String(255), nullable=False)
    tamaño_archivo = Column(Integer)  # En bytes
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False, index=True)
    estado = Column(String(20), nullable=False, default='en_progreso', index=True)  # en_progreso, exitoso, fallido
    mensaje_resultado = Column(Text)
    duracion_segundos = Column(Integer)
    tablas_incluidas = Column(Text)  # JSON con lista de tablas
    fecha_inicio = Column(DateTime, nullable=False, index=True)
    fecha_fin = Column(DateTime)
    fecha_registro = Column(DateTime, default=datetime.now)
    
    def set_tablas_incluidas(self, tablas: list):
        """Establece las tablas incluidas como JSON"""
        self.tablas_incluidas = json.dumps(tablas) if tablas else None
    
    def get_tablas_incluidas(self) -> list:
        """Obtiene las tablas incluidas desde JSON"""
        if self.tablas_incluidas:
            try:
                return json.loads(self.tablas_incluidas)
            except json.JSONDecodeError:
                return []
        return []
    
    def finalizar_operacion(self, estado: str, mensaje: str = ""):
        """Finaliza la operación de backup/restore"""
        self.fecha_fin = datetime.now()
        self.estado = estado
        self.mensaje_resultado = mensaje
        if self.fecha_inicio:
            delta = self.fecha_fin - self.fecha_inicio
            self.duracion_segundos = int(delta.total_seconds())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el registro de backup a diccionario"""
        return {
            'id': self.id,
            'tipo_operacion': self.tipo_operacion,
            'archivo_backup': self.archivo_backup,
            'tamaño_archivo': self.tamaño_archivo,
            'usuario_id': self.usuario_id,
            'estado': self.estado,
            'mensaje_resultado': self.mensaje_resultado,
            'duracion_segundos': self.duracion_segundos,
            'tablas_incluidas': self.get_tablas_incluidas(),
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None
        }

# Función de utilidad para crear registros básicos
def crear_registro_simple(descripcion: str, tipo: str, monto: float = 0.0, 
                         usuario_id: Optional[int] = None, 
                         referencia_id: Optional[int] = None,
                         referencia_tabla: Optional[str] = None) -> Registro:
    """Crea un registro simple"""
    return Registro(
        descripcion=descripcion,
        monto=monto,
        tipo=tipo,
        usuario_id=usuario_id,
        referencia_id=referencia_id,
        referencia_tabla=referencia_tabla,
        fecha=datetime.now()
    )