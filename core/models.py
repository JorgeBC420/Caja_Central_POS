from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

class Usuario:
    def __init__(self, id, username, nombre, rol):
        self.id = id
        self.username = username
        self.nombre = nombre
        self.rol = rol

class Producto:
    def __init__(self, id, codigo_barras, nombre, precio, stock, categoria_id, iva_tasa, costo, stock_minimo, descripcion, observaciones_stock):
        self.id = id
        self.codigo_barras = codigo_barras
        self.nombre = nombre
        self.precio = precio
        self.stock = stock
        self.categoria_id = categoria_id
        self.iva_tasa = iva_tasa
        self.costo = costo
        self.stock_minimo = stock_minimo
        self.descripcion = descripcion
        self.observaciones_stock = observaciones_stock

class Cliente:
    def __init__(self, id, nombre, identificacion, tipo_identificacion, correo, telefono, direccion, fecha_registro, activo):
        self.id = id
        self.nombre = nombre
        self.identificacion = identificacion
        self.tipo_identificacion = tipo_identificacion
        self.correo = correo
        self.telefono = telefono
        self.direccion = direccion
        self.fecha_registro = fecha_registro
        self.activo = activo

class Venta:
    def __init__(self, id, fecha, cliente_id, usuario_id, total, subtotal, iva, estado, pagos, items):
        self.id = id
        self.fecha = fecha
        self.cliente_id = cliente_id
        self.usuario_id = usuario_id
        self.total = total
        self.subtotal = subtotal
        self.iva = iva
        self.estado = estado  # 'finalizada', 'anulada', etc.
        self.pagos = pagos  # lista de objetos Pago
        self.items = items  # lista de objetos VentaItem

class VentaItem:
    def __init__(self, producto_id, cantidad, precio_unitario, subtotal, iva):
        self.producto_id = producto_id
        self.cantidad = cantidad
        self.precio_unitario = precio_unitario
        self.subtotal = subtotal
        self.iva = iva

class MovimientoInventario:
    def __init__(self, id, producto_id, tipo, cantidad, fecha, usuario_id, observacion):
        self.id = id
        self.producto_id = producto_id
        self.tipo = tipo  # 'entrada', 'salida', 'ajuste'
        self.cantidad = cantidad
        self.fecha = fecha
        self.usuario_id = usuario_id
        self.observacion = observacion
        
class ConfigTienda:
    def __init__(self, nombre, cedula_juridica, telefono, direccion, correo, resolucion_hacienda, logo_path):
        self.nombre = nombre
        self.cedula_juridica = cedula_juridica
        self.telefono = telefono
        self.direccion = direccion
        self.correo = correo
        self.resolucion_hacienda = resolucion_hacienda
        self.logo_path = logo_path
        
class LicenciaSistema:
    def __init__(self, clave, fecha_activacion, fecha_expiracion, estado):
        self.clave = clave
        self.fecha_activacion = fecha_activacion
        self.fecha_expiracion = fecha_expiracion
        self.estado = estado  # 'activa', 'expirada', 'bloqueada'
        
class Apartado:
    def __init__(self, id, cliente_id, fecha, total, abonos, usuario_id, estado):
        self.id = id
        self.cliente_id = cliente_id
        self.fecha = fecha
        self.total = total
        self.abonos = abonos  # lista de objetos Abono
        self.usuario_id = usuario_id
        self.estado = estado  # 'activo', 'cancelado', 'finalizado', etc.

class Abono:
    def __init__(self, id, apartado_id, fecha, monto, usuario_id):
        self.id = id
        self.apartado_id = apartado_id
        self.fecha = fecha
        self.monto = monto

        # Mejoras sugeridas:
        # 1. Usar dataclasses para reducir código repetitivo y mejorar legibilidad.
        # 2. Agregar __repr__ automáticamente.
        # 3. Opcional: Validar tipos con type hints.


        @dataclass
        class Usuario:
            id: int
            username: str
            nombre: str
            rol: str

        @dataclass
        class Producto:
            id: int
            codigo_barras: str
            nombre: str
            precio: float
            stock: int
            categoria_id: int
            iva_tasa: float
            costo: float
            stock_minimo: int
            descripcion: str
            observaciones_stock: str

        @dataclass
        class Cliente:
            id: int
            nombre: str
            identificacion: str
            tipo_identificacion: str
            correo: str
            telefono: str
            direccion: str
            fecha_registro: datetime
            activo: bool

        @dataclass
        class VentaItem:
            producto_id: int
            cantidad: int
            precio_unitario: float
            subtotal: float
            iva: float

        @dataclass
        class Venta:
            id: int
            fecha: datetime
            cliente_id: int
            usuario_id: int
            total: float
            subtotal: float
            iva: float
            estado: str
            pagos: List  # Debería ser List[Pago] si existe la clase Pago
            items: List[VentaItem]

        @dataclass
        class MovimientoInventario:
            id: int
            producto_id: int
            tipo: str
            cantidad: int
            fecha: datetime
            usuario_id: int
            observacion: str

        @dataclass
        class ConfigTienda:
            nombre: str
            cedula_juridica: str
            telefono: str
            direccion: str
            correo: str
            resolucion_hacienda: str
            logo_path: str

        @dataclass
        class LicenciaSistema:
            clave: str
            fecha_activacion: datetime
            fecha_expiracion: datetime
            estado: str

        @dataclass
        class Abono:
            id: int
            apartado_id: int
            fecha: datetime
            monto: float
            usuario_id: int

        @dataclass
        class Apartado:
            id: int
            cliente_id: int
            fecha: datetime
            total: float
            abonos: List[Abono]
            usuario_id: int
            estado: str
