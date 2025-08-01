"""
Modelos de datos para el sistema POS
Definición de todas las entidades del negocio con validaciones y métodos
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum

# ===== ENUMERACIONES =====

class EstadoUsuario(Enum):
    """Estados posibles de un usuario"""
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    BLOQUEADO = "bloqueado"
    SUSPENDIDO = "suspendido"

class RolUsuario(Enum):
    """Roles de usuario en el sistema"""
    ADMIN = "admin"
    SUBADMIN = "subadmin"
    CAJERO = "cajero"
    VENDEDOR = "vendedor"

class EstadoVenta(Enum):
    """Estados de una venta"""
    EN_PROGRESO = "en_progreso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"
    ANULADA = "anulada"
    PENDIENTE = "pendiente"

class TipoMovimiento(Enum):
    """Tipos de movimiento de inventario"""
    ENTRADA = "entrada"
    SALIDA = "salida"
    AJUSTE = "ajuste"
    DEVOLUCION = "devolucion"
    MERMA = "merma"

class EstadoApartado(Enum):
    """Estados de un apartado"""
    ACTIVO = "activo"
    FINALIZADO = "finalizado"
    CANCELADO = "cancelado"
    VENCIDO = "vencido"

class EstadoLicencia(Enum):
    """Estados de la licencia del sistema"""
    ACTIVA = "activa"
    EXPIRADA = "expirada"
    BLOQUEADA = "bloqueada"
    SUSPENDIDA = "suspendida"

class TipoIdentificacion(Enum):
    """Tipos de identificación en Costa Rica"""
    CEDULA_FISICA = "01"
    CEDULA_JURIDICA = "02"
    DIMEX = "03"
    NITE = "04"
    EXTRANJERO = "05"

# ===== MODELOS PRINCIPALES =====

@dataclass
class Usuario:
    """Modelo de usuario del sistema"""
    id: int
    username: str
    nombre: str
    email: str
    rol: RolUsuario
    estado: EstadoUsuario = EstadoUsuario.ACTIVO
    fecha_creacion: datetime = field(default_factory=datetime.now)
    ultimo_login: Optional[datetime] = None
    intentos_fallidos: int = 0
    password_hash: str = ""
    
    def __post_init__(self):
        if isinstance(self.rol, str):
            self.rol = RolUsuario(self.rol)
        if isinstance(self.estado, str):
            self.estado = EstadoUsuario(self.estado)
    
    @property
    def esta_activo(self) -> bool:
        """Verifica si el usuario está activo"""
        return self.estado == EstadoUsuario.ACTIVO
    
    @property
    def puede_iniciar_sesion(self) -> bool:
        """Verifica si el usuario puede iniciar sesión"""
        return self.esta_activo and self.intentos_fallidos < 5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el usuario a diccionario (sin password)"""
        return {
            'id': self.id,
            'username': self.username,
            'nombre': self.nombre,
            'email': self.email,
            'rol': self.rol.value,
            'estado': self.estado.value,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'ultimo_login': self.ultimo_login.isoformat() if self.ultimo_login else None,
            'intentos_fallidos': self.intentos_fallidos
        }

@dataclass
class Categoria:
    """Categoría de productos"""
    id: int
    nombre: str
    descripcion: str = ""
    activa: bool = True
    fecha_creacion: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'activa': self.activa,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }

@dataclass
class Producto:
    """Modelo de producto"""
    id: int
    codigo_barras: str
    nombre: str
    precio: Decimal
    stock: Decimal
    categoria_id: int
    costo: Decimal = Decimal('0')
    stock_minimo: Decimal = Decimal('0')
    descripcion: str = ""
    observaciones_stock: str = ""
    iva_tasa: Decimal = Decimal('0.13')
    exento_impuesto: bool = False
    activo: bool = True
    fecha_creacion: datetime = field(default_factory=datetime.now)
    fecha_actualizacion: Optional[datetime] = None
    
    def __post_init__(self):
        # Convertir a Decimal si vienen como float o str
        if not isinstance(self.precio, Decimal):
            self.precio = Decimal(str(self.precio))
        if not isinstance(self.stock, Decimal):
            self.stock = Decimal(str(self.stock))
        if not isinstance(self.costo, Decimal):
            self.costo = Decimal(str(self.costo))
        if not isinstance(self.stock_minimo, Decimal):
            self.stock_minimo = Decimal(str(self.stock_minimo))
        if not isinstance(self.iva_tasa, Decimal):
            self.iva_tasa = Decimal(str(self.iva_tasa))
    
    @property
    def margen_ganancia(self) -> Decimal:
        """Calcula el margen de ganancia"""
        if self.costo > 0:
            return ((self.precio - self.costo) / self.costo) * 100
        return Decimal('0')
    
    @property
    def stock_bajo(self) -> bool:
        """Verifica si el stock está por debajo del mínimo"""
        return self.stock <= self.stock_minimo
    
    @property
    def valor_inventario(self) -> Decimal:
        """Calcula el valor del inventario (stock * costo)"""
        return self.stock * self.costo
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'codigo_barras': self.codigo_barras,
            'nombre': self.nombre,
            'precio': float(self.precio),
            'stock': float(self.stock),
            'categoria_id': self.categoria_id,
            'costo': float(self.costo),
            'stock_minimo': float(self.stock_minimo),
            'descripcion': self.descripcion,
            'observaciones_stock': self.observaciones_stock,
            'iva_tasa': float(self.iva_tasa),
            'exento_impuesto': self.exento_impuesto,
            'activo': self.activo,
            'margen_ganancia': float(self.margen_ganancia),
            'stock_bajo': self.stock_bajo,
            'valor_inventario': float(self.valor_inventario)
        }

@dataclass
class Cliente:
    """Modelo de cliente"""
    id: int
    nombre: str
    identificacion: str
    tipo_identificacion: TipoIdentificacion
    correo: str = ""
    telefono: str = ""
    direccion: str = ""
    activo: bool = True
    fecha_registro: datetime = field(default_factory=datetime.now)
    limite_credito: Decimal = Decimal('0')
    credito_utilizado: Decimal = Decimal('0')
    
    def __post_init__(self):
        if isinstance(self.tipo_identificacion, str):
            self.tipo_identificacion = TipoIdentificacion(self.tipo_identificacion)
        if not isinstance(self.limite_credito, Decimal):
            self.limite_credito = Decimal(str(self.limite_credito))
        if not isinstance(self.credito_utilizado, Decimal):
            self.credito_utilizado = Decimal(str(self.credito_utilizado))
    
    @property
    def credito_disponible(self) -> Decimal:
        """Calcula el crédito disponible"""
        return self.limite_credito - self.credito_utilizado
    
    @property
    def tiene_credito_disponible(self) -> bool:
        """Verifica si tiene crédito disponible"""
        return self.credito_disponible > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'nombre': self.nombre,
            'identificacion': self.identificacion,
            'tipo_identificacion': self.tipo_identificacion.value,
            'correo': self.correo,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'activo': self.activo,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'limite_credito': float(self.limite_credito),
            'credito_utilizado': float(self.credito_utilizado),
            'credito_disponible': float(self.credito_disponible)
        }

@dataclass
class VentaItem:
    """Item individual de una venta"""
    id: Optional[int]
    venta_id: Optional[int]
    producto_id: int
    cantidad: Decimal
    precio_unitario: Decimal
    subtotal: Decimal
    impuesto: Decimal = Decimal('0')
    descuento: Decimal = Decimal('0')
    producto_nombre: str = ""
    producto_codigo: str = ""
    
    def __post_init__(self):
        # Convertir a Decimal
        for field_name in ['cantidad', 'precio_unitario', 'subtotal', 'impuesto', 'descuento']:
            value = getattr(self, field_name)
            if not isinstance(value, Decimal):
                setattr(self, field_name, Decimal(str(value)))
    
    @property
    def total_item(self) -> Decimal:
        """Total del item (subtotal + impuesto - descuento)"""
        return self.subtotal + self.impuesto - self.descuento
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'venta_id': self.venta_id,
            'producto_id': self.producto_id,
            'cantidad': float(self.cantidad),
            'precio_unitario': float(self.precio_unitario),
            'subtotal': float(self.subtotal),
            'impuesto': float(self.impuesto),
            'descuento': float(self.descuento),
            'total_item': float(self.total_item),
            'producto_nombre': self.producto_nombre,
            'producto_codigo': self.producto_codigo
        }

@dataclass
class Pago:
    """Registro de un pago"""
    id: Optional[int]
    venta_id: Optional[int]
    metodo_pago: str
    monto: Decimal
    referencia: str = ""
    banco: str = ""
    fecha: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not isinstance(self.monto, Decimal):
            self.monto = Decimal(str(self.monto))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'venta_id': self.venta_id,
            'metodo_pago': self.metodo_pago,
            'monto': float(self.monto),
            'referencia': self.referencia,
            'banco': self.banco,
            'fecha': self.fecha.isoformat() if self.fecha else None
        }

@dataclass
class Venta:
    """Modelo de venta completa"""
    id: Optional[int]
    numero_venta: str
    fecha: datetime
    cliente_id: Optional[int]
    usuario_id: int
    subtotal: Decimal
    impuesto: Decimal
    descuento: Decimal
    total: Decimal
    estado: EstadoVenta
    observaciones: str = ""
    items: List[VentaItem] = field(default_factory=list)
    pagos: List[Pago] = field(default_factory=list)
    cliente_nombre: str = ""
    usuario_nombre: str = ""
    
    def __post_init__(self):
        # Convertir a Decimal
        for field_name in ['subtotal', 'impuesto', 'descuento', 'total']:
            value = getattr(self, field_name)
            if not isinstance(value, Decimal):
                setattr(self, field_name, Decimal(str(value)))
        
        if isinstance(self.estado, str):
            self.estado = EstadoVenta(self.estado)
    
    @property
    def total_pagado(self) -> Decimal:
        """Total pagado en la venta"""
        return sum(pago.monto for pago in self.pagos)
    
    @property
    def saldo_pendiente(self) -> Decimal:
        """Saldo pendiente de pago"""
        return self.total - self.total_pagado
    
    @property
    def esta_pagada_completa(self) -> bool:
        """Verifica si la venta está pagada completamente"""
        return self.saldo_pendiente <= Decimal('0.01')  # Tolerancia de 1 centavo
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'numero_venta': self.numero_venta,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'cliente_id': self.cliente_id,
            'usuario_id': self.usuario_id,
            'subtotal': float(self.subtotal),
            'impuesto': float(self.impuesto),
            'descuento': float(self.descuento),
            'total': float(self.total),
            'estado': self.estado.value,
            'observaciones': self.observaciones,
            'total_pagado': float(self.total_pagado),
            'saldo_pendiente': float(self.saldo_pendiente),
            'esta_pagada_completa': self.esta_pagada_completa,
            'cliente_nombre': self.cliente_nombre,
            'usuario_nombre': self.usuario_nombre,
            'items': [item.to_dict() for item in self.items],
            'pagos': [pago.to_dict() for pago in self.pagos]
        }

@dataclass
class MovimientoInventario:
    """Movimiento de inventario"""
    id: Optional[int]
    producto_id: int
    tipo: TipoMovimiento
    cantidad: Decimal
    fecha: datetime
    usuario_id: int
    observacion: str
    costo_unitario: Decimal = Decimal('0')
    numero_documento: str = ""
    producto_nombre: str = ""
    usuario_nombre: str = ""
    
    def __post_init__(self):
        if not isinstance(self.cantidad, Decimal):
            self.cantidad = Decimal(str(self.cantidad))
        if not isinstance(self.costo_unitario, Decimal):
            self.costo_unitario = Decimal(str(self.costo_unitario))
        if isinstance(self.tipo, str):
            self.tipo = TipoMovimiento(self.tipo)
    
    @property
    def valor_total(self) -> Decimal:
        """Valor total del movimiento"""
        return self.cantidad * self.costo_unitario
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'producto_id': self.producto_id,
            'tipo': self.tipo.value,
            'cantidad': float(self.cantidad),
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'usuario_id': self.usuario_id,
            'observacion': self.observacion,
            'costo_unitario': float(self.costo_unitario),
            'valor_total': float(self.valor_total),
            'numero_documento': self.numero_documento,
            'producto_nombre': self.producto_nombre,
            'usuario_nombre': self.usuario_nombre
        }

@dataclass
class Abono:
    """Abono a un apartado"""
    id: Optional[int]
    apartado_id: int
    fecha: datetime
    monto: Decimal
    usuario_id: int
    metodo_pago: str = "efectivo"
    referencia: str = ""
    
    def __post_init__(self):
        if not isinstance(self.monto, Decimal):
            self.monto = Decimal(str(self.monto))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'apartado_id': self.apartado_id,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'monto': float(self.monto),
            'usuario_id': self.usuario_id,
            'metodo_pago': self.metodo_pago,
            'referencia': self.referencia
        }

@dataclass
class Apartado:
    """Apartado de productos"""
    id: Optional[int]
    cliente_id: int
    fecha: datetime
    total: Decimal
    usuario_id: int
    estado: EstadoApartado
    observaciones: str = ""
    fecha_vencimiento: Optional[datetime] = None
    items: List[VentaItem] = field(default_factory=list)
    abonos: List[Abono] = field(default_factory=list)
    cliente_nombre: str = ""
    usuario_nombre: str = ""
    
    def __post_init__(self):
        if not isinstance(self.total, Decimal):
            self.total = Decimal(str(self.total))
        if isinstance(self.estado, str):
            self.estado = EstadoApartado(self.estado)
    
    @property
    def total_abonado(self) -> Decimal:
        """Total abonado al apartado"""
        return sum(abono.monto for abono in self.abonos)
    
    @property
    def saldo_pendiente(self) -> Decimal:
        """Saldo pendiente del apartado"""
        return self.total - self.total_abonado
    
    @property
    def esta_pagado_completo(self) -> bool:
        """Verifica si el apartado está pagado completamente"""
        return self.saldo_pendiente <= Decimal('0.01')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'total': float(self.total),
            'usuario_id': self.usuario_id,
            'estado': self.estado.value,
            'observaciones': self.observaciones,
            'fecha_vencimiento': self.fecha_vencimiento.isoformat() if self.fecha_vencimiento else None,
            'total_abonado': float(self.total_abonado),
            'saldo_pendiente': float(self.saldo_pendiente),
            'esta_pagado_completo': self.esta_pagado_completo,
            'cliente_nombre': self.cliente_nombre,
            'usuario_nombre': self.usuario_nombre,
            'items': [item.to_dict() for item in self.items],
            'abonos': [abono.to_dict() for abono in self.abonos]
        }

@dataclass
class ConfigTienda:
    """Configuración de la tienda"""
    nombre: str
    identificacion: str
    tipo_identificacion: TipoIdentificacion
    telefono: str
    direccion: str
    correo: str
    resolucion_hacienda: str = ""
    logo_path: str = ""
    provincia: str = ""
    canton: str = ""
    distrito: str = ""
    codigo_postal: str = ""
    
    def __post_init__(self):
        if isinstance(self.tipo_identificacion, str):
            self.tipo_identificacion = TipoIdentificacion(self.tipo_identificacion)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'nombre': self.nombre,
            'identificacion': self.identificacion,
            'tipo_identificacion': self.tipo_identificacion.value,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'correo': self.correo,
            'resolucion_hacienda': self.resolucion_hacienda,
            'logo_path': self.logo_path,
            'provincia': self.provincia,
            'canton': self.canton,
            'distrito': self.distrito,
            'codigo_postal': self.codigo_postal
        }

@dataclass
class LicenciaSistema:
    """Licencia del sistema"""
    clave: str
    fecha_activacion: datetime
    fecha_expiracion: datetime
    estado: EstadoLicencia
    max_usuarios: int = 1
    max_productos: int = 1000
    modulos_habilitados: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if isinstance(self.estado, str):
            self.estado = EstadoLicencia(self.estado)
    
    @property
    def dias_restantes(self) -> int:
        """Días restantes de la licencia"""
        if self.fecha_expiracion:
            delta = self.fecha_expiracion - datetime.now()
            return max(0, delta.days)
        return 0
    
    @property
    def esta_vigente(self) -> bool:
        """Verifica si la licencia está vigente"""
        return (self.estado == EstadoLicencia.ACTIVA and 
                self.fecha_expiracion > datetime.now())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'clave': self.clave,
            'fecha_activacion': self.fecha_activacion.isoformat() if self.fecha_activacion else None,
            'fecha_expiracion': self.fecha_expiracion.isoformat() if self.fecha_expiracion else None,
            'estado': self.estado.value,
            'max_usuarios': self.max_usuarios,
            'max_productos': self.max_productos,
            'modulos_habilitados': self.modulos_habilitados,
            'dias_restantes': self.dias_restantes,
            'esta_vigente': self.esta_vigente
        }
