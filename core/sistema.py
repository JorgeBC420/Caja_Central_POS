import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal

from core.database import DatabaseManager, get_db_cursor, ejecutar_consulta_segura
from core.calculadora_caja import CalculadoraCaja, ProductoVenta
from core.config import ConfigManager
from core.auditoria import auditoria_manager

class Usuario:
    """Clase para representar un usuario del sistema"""
    def __init__(self, id, nombre, usuario, rol, activo=True):
        self.id = id
        self.nombre = nombre
        self.usuario = usuario
        self.rol = rol
        self.activo = activo
        self.fecha_login = None
        self.sesion_activa = False

class MetodoPago:
    """Clase para representar un método de pago"""
    def __init__(self, metodo, monto, referencia=None, banco=None, fecha_pago=None):
        self.metodo = metodo
        self.monto = Decimal(str(monto))
        self.referencia = referencia
        self.banco = banco
        self.fecha_pago = fecha_pago or datetime.now()

class VentaActual:
    """Clase para manejar la venta en progreso"""
    def __init__(self):
        self.items = []
        self.cliente_id = None
        self.descuento_general = Decimal('0')
        self.observaciones = ""
        self.metodos_pago = []
        self.estado = "en_progreso"  # en_progreso, pendiente, completada, cancelada

class SistemaCaja:
    def __init__(self):
        self.usuario_actual: Optional[Usuario] = None
        self.db = None  # Se asignará desde AppController
        self.config = {}  # Se asignará desde AppController
        self.calculadora = CalculadoraCaja()
        self.venta_actual = VentaActual()
        self.logger = logging.getLogger(__name__)
        
    # --- AUTENTICACIÓN ---
    def autenticar_usuario(self, username: str, password: str) -> bool:
        """Valida usuario y contraseña contra la base de datos"""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            query = """
                SELECT id, nombre, usuario, rol, activo 
                FROM usuarios 
                WHERE usuario = ? AND password = ? AND activo = 1
            """
            
            with get_db_cursor() as cursor:
                cursor.execute(query, (username, password_hash))
                row = cursor.fetchone()
                
                if row:
                    self.usuario_actual = Usuario(
                        id=row[0],
                        nombre=row[1], 
                        usuario=row[2],
                        rol=row[3],
                        activo=bool(row[4])
                    )
                    self.usuario_actual.fecha_login = datetime.now()
                    self.usuario_actual.sesion_activa = True
                    
                    # Registrar login exitoso en auditoría
                    auditoria_manager.registrar_login(
                        usuario_id=self.usuario_actual.id,
                        exito=True
                    )
                    
                    self.logger.info(f"Login exitoso para usuario: {username}")
                    return True
                else:
                    # Registrar intento fallido
                    self.logger.warning(f"Intento de login fallido para usuario: {username}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error en autenticación: {e}")
            return False

    def cerrar_sesion(self):
        """Cierra la sesión del usuario actual"""
        if self.usuario_actual:
            # Calcular duración de sesión
            duracion = None
            if self.usuario_actual.fecha_login:
                duracion = (datetime.now() - self.usuario_actual.fecha_login).seconds // 60
            
            # Registrar logout en auditoría
            auditoria_manager.registrar_logout(
                usuario_id=self.usuario_actual.id,
                duracion_sesion=duracion
            )
            
            self.logger.info(f"Sesión cerrada para usuario: {self.usuario_actual.usuario}")
            self.usuario_actual = None
            
        # Limpiar venta actual
        self.nueva_venta()

    # --- GESTIÓN DE VENTAS ---
    def nueva_venta(self):
        """Inicia una nueva venta"""
        self.venta_actual = VentaActual()

    def agregar_producto_venta(self, producto_id: int, cantidad: int = 1, 
                              precio_manual: Optional[float] = None) -> bool:
        """Agrega un producto a la venta actual"""
        try:
            # Obtener información del producto
            query = "SELECT id, codigo, nombre, precio, stock FROM productos WHERE id = ? AND activo = 1"
            
            with get_db_cursor() as cursor:
                cursor.execute(query, (producto_id,))
                row = cursor.fetchone()
                
                if not row:
                    self.logger.warning(f"Producto no encontrado: {producto_id}")
                    return False
                
                # Verificar stock
                if row[4] < cantidad:
                    self.logger.warning(f"Stock insuficiente para producto {row[2]}: disponible {row[4]}, solicitado {cantidad}")
                    return False
                
                # Crear objeto ProductoVenta
                producto_venta = ProductoVenta(
                    id=row[0],
                    codigo=row[1],
                    nombre=row[2],
                    precio=row[3],
                    cantidad=cantidad,
                    precio_manual=precio_manual
                )
                
                # Verificar si el producto ya está en la venta
                producto_existente = None
                for item in self.venta_actual.items:
                    if item.id == producto_id:
                        producto_existente = item
                        break
                
                if producto_existente:
                    # Actualizar cantidad
                    producto_existente.cantidad += cantidad
                else:
                    # Agregar nuevo producto
                    self.venta_actual.items.append(producto_venta)
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error al agregar producto a venta: {e}")
            return False

    def remover_producto_venta(self, producto_id: int) -> bool:
        """Remueve un producto de la venta actual"""
        try:
            self.venta_actual.items = [
                item for item in self.venta_actual.items 
                if item.id != producto_id
            ]
            return True
        except Exception as e:
            self.logger.error(f"Error al remover producto de venta: {e}")
            return False

    def actualizar_cantidad_producto(self, producto_id: int, nueva_cantidad: int) -> bool:
        """Actualiza la cantidad de un producto en la venta"""
        try:
            for item in self.venta_actual.items:
                if item.id == producto_id:
                    if nueva_cantidad <= 0:
                        return self.remover_producto_venta(producto_id)
                    else:
                        item.cantidad = nueva_cantidad
                        return True
            return False
        except Exception as e:
            self.logger.error(f"Error al actualizar cantidad: {e}")
            return False

    def aplicar_descuento_general(self, porcentaje: float) -> bool:
        """Aplica descuento general a la venta"""
        try:
            if 0 <= porcentaje <= 100:
                self.venta_actual.descuento_general = Decimal(str(porcentaje))
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error al aplicar descuento: {e}")
            return False

    def calcular_totales_venta(self) -> Dict:
        """Calcula todos los totales de la venta actual"""
        try:
            if not self.venta_actual.items:
                return {
                    'subtotal_bruto': Decimal('0'),
                    'descuento_general': Decimal('0'),
                    'impuesto': Decimal('0'),
                    'total': Decimal('0'),
                    'items_count': 0
                }
            
            # Actualizar tasa de IVA desde configuración
            tasa_iva = float(self.config.get('tasa_iva', 0.13))
            self.calculadora.tasa_iva = Decimal(str(tasa_iva))
            
            # Calcular totales
            totales = self.calculadora.calcular_total_venta(
                productos=self.venta_actual.items,
                descuento_porcentaje=self.venta_actual.descuento_general
            )
            
            totales['items_count'] = len(self.venta_actual.items)
            return totales
            
        except Exception as e:
            self.logger.error(f"Error al calcular totales: {e}")
            return {}

    def finalizar_venta(self, metodos_pago: List[Dict]) -> Optional[int]:
        """
        Finaliza la venta actual
        metodos_pago: [{'metodo': 'efectivo', 'monto': 10000}, ...]
        """
        try:
            if not self.venta_actual.items:
                raise ValueError("No hay productos en la venta")
            
            if not self.usuario_actual:
                raise ValueError("Usuario no autenticado")
            
            # Calcular totales
            totales = self.calcular_totales_venta()
            total_venta = totales['total']
            
            # Validar pagos
            total_pagado = sum(Decimal(str(pago['monto'])) for pago in metodos_pago)
            if total_pagado < total_venta:
                raise ValueError("Pago insuficiente")
            
            # Guardar venta en base de datos
            venta_id = self._guardar_venta_bd(totales, metodos_pago)
            
            if venta_id:
                # Actualizar inventario
                self._actualizar_inventario_venta()
                
                # Registrar en auditoría
                auditoria_manager.registrar_venta(
                    usuario_id=self.usuario_actual.id,
                    venta_id=venta_id,
                    monto_total=float(total_venta),
                    items_count=len(self.venta_actual.items),
                    metodo_pago=', '.join([m['metodo'] for m in metodos_pago])
                )
                
                # Limpiar venta actual
                self.nueva_venta()
                
                return venta_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error al finalizar venta: {e}")
            raise

    def _guardar_venta_bd(self, totales: Dict, metodos_pago: List[Dict]) -> Optional[int]:
        """Guarda la venta en la base de datos"""
        try:
            with get_db_cursor() as cursor:
                # Insertar venta principal
                query_venta = """
                    INSERT INTO ventas (
                        usuario_id, cliente_id, subtotal, impuestos, total, estado
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(query_venta, (
                    self.usuario_actual.id,
                    self.venta_actual.cliente_id,
                    float(totales['subtotal_neto']),
                    float(totales['impuesto']),
                    float(totales['total']),
                    'completada'
                ))
                
                venta_id = cursor.lastrowid
                
                # Insertar items de venta
                for item in self.venta_actual.items:
                    query_item = """
                        INSERT INTO venta_items (
                            venta_id, producto_id, cantidad, precio_unitario, subtotal
                        ) VALUES (?, ?, ?, ?, ?)
                    """
                    
                    precio_efectivo = item.precio_manual or item.precio
                    subtotal_item = precio_efectivo * item.cantidad
                    
                    cursor.execute(query_item, (
                        venta_id,
                        item.id,
                        float(item.cantidad),
                        float(precio_efectivo),
                        float(subtotal_item)
                    ))
                
                return venta_id
                
        except Exception as e:
            self.logger.error(f"Error al guardar venta en BD: {e}")
            return None

    def _actualizar_inventario_venta(self):
        """Actualiza el inventario después de una venta"""
        try:
            for item in self.venta_actual.items:
                query = "UPDATE productos SET stock = stock - ? WHERE id = ?"
                ejecutar_consulta_segura(query, (float(item.cantidad), item.id))
                
                # Registrar movimiento de inventario
                auditoria_manager.registrar_cambio_inventario(
                    usuario_id=self.usuario_actual.id,
                    producto_id=item.id,
                    tipo_cambio="salida",
                    cantidad=int(item.cantidad),
                    motivo="Venta"
                )
                
        except Exception as e:
            self.logger.error(f"Error al actualizar inventario: {e}")

    # --- CONFIGURACIÓN ---
    def actualizar_configuracion(self, clave: str, valor: Any) -> bool:
        """Actualiza una configuración del sistema"""
        try:
            if not self.usuario_actual or self.usuario_actual.rol != 'admin':
                raise ValueError("Solo administradores pueden cambiar configuración")
            
            valor_anterior = self.config.get(clave, "")
            
            # Actualizar en memoria
            self.config[clave] = valor
            
            # Actualizar en base de datos
            query = """
                INSERT OR REPLACE INTO configuraciones (clave, valor) 
                VALUES (?, ?)
            """
            
            success, message = ejecutar_consulta_segura(query, (clave, str(valor)))
            
            if success:
                # Registrar cambio en auditoría
                auditoria_manager.registrar_configuracion(
                    usuario_id=self.usuario_actual.id,
                    clave=clave,
                    valor_anterior=str(valor_anterior),
                    valor_nuevo=str(valor)
                )
                
                self.logger.info(f"Configuración actualizada: {clave} = {valor}")
                return True
            else:
                self.logger.error(f"Error al actualizar configuración: {message}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error en actualizar_configuracion: {e}")
            return False

    # --- REPORTES BÁSICOS ---
    def obtener_ventas_del_dia(self) -> List[Dict]:
        """Obtiene las ventas del día actual"""
        try:
            fecha_hoy = datetime.now().strftime("%Y-%m-%d")
            query = """
                SELECT v.*, u.nombre as vendedor
                FROM ventas v
                LEFT JOIN usuarios u ON v.usuario_id = u.id
                WHERE DATE(v.fecha) = ?
                ORDER BY v.fecha DESC
            """
            
            with get_db_cursor() as cursor:
                cursor.execute(query, (fecha_hoy,))
                rows = cursor.fetchall()
                
                ventas = []
                for row in rows:
                    venta_dict = dict(row) if hasattr(row, 'keys') else {
                        'id': row[0], 'usuario_id': row[1], 'cliente_id': row[2],
                        'subtotal': row[3], 'impuestos': row[4], 'total': row[5],
                        'fecha': row[6], 'estado': row[7], 'vendedor': row[8] if len(row) > 8 else None
                    }
                    ventas.append(venta_dict)
                
                return ventas
                
        except Exception as e:
            self.logger.error(f"Error al obtener ventas del día: {e}")
            return []

    def generar_datos_venta_finalizada(self) -> Dict:
        """Genera los datos para imprimir ticket"""
        totales = self.calcular_totales_venta()
        
        return {
            'numero_venta': None,  # Se asignará después de guardar
            'fecha': datetime.now(),
            'vendedor': self.usuario_actual.nombre if self.usuario_actual else "Desconocido",
            'items': [
                {
                    'codigo': item.codigo,
                    'nombre': item.nombre,
                    'cantidad': float(item.cantidad),
                    'precio': float(item.precio_efectivo),
                    'subtotal': float(item.subtotal_item)
                }
                for item in self.venta_actual.items
            ],
            'totales': {
                'subtotal': float(totales.get('subtotal_neto', 0)),
                'descuento': float(totales.get('descuento_general', 0)),
                'impuesto': float(totales.get('impuesto', 0)),
                'total': float(totales.get('total', 0))
            }
        }

    # --- Inventario ---
    def ajustar_inventario(self, producto_id, cantidad, motivo=""):
        """Ajusta el inventario de un producto."""
        pass

    def obtener_stock(self, producto_id):
        """Devuelve el stock actual de un producto."""
        pass

    # --- Clientes ---
    def agregar_cliente(self, datos_cliente):
        """Agrega un nuevo cliente."""
        pass

    def modificar_cliente(self, cliente_id, nuevos_datos):
        """Modifica los datos de un cliente."""
        pass

    def eliminar_cliente(self, cliente_id):
        """Elimina un cliente."""
        pass

    def buscar_cliente(self, criterio):
        """Busca clientes por nombre, ID, etc."""
        pass

    # --- Apartados / Créditos ---
    def crear_apartado(self, cliente_id, productos, plazo_meses):
        """Crea un nuevo apartado."""
        pass

    def abonar_apartado(self, apartado_id, monto):
        """Registra un abono a un apartado."""
        pass

    # --- Configuración ---
    def cargar_configuraciones(self):
        """Carga configuraciones del sistema."""
        pass

    def actualizar_configuracion(self, clave, valor):
        """Actualiza una configuración."""
        pass

    # --- Reportes ---
    def generar_reporte_ventas(self, fecha_inicio, fecha_fin):
        """Genera un reporte de ventas."""
        pass

    def generar_reporte_inventario(self):
        """Genera un reporte de inventario."""
        pass

def registrar_pago(self, venta_id, metodo, monto, referencia=None, banco=None, fecha_pago=None):
    """
    Registra un método de pago para una venta específica.
    """
    venta = self.obtener_venta_por_id(venta_id)
    if not venta:
        raise ValueError("Venta no encontrada")

    pago = MetodoPago(
        method=metodo,
        amount=monto,
        reference=referencia,
        banco=banco,
        fecha_pago=fecha_pago
    )
    if not hasattr(venta, 'pagos') or venta.pagos is None:
        venta.pagos = []
    venta.pagos.append(pago)
    # Aquí podrías guardar la venta actualizada en la base de datos si aplica
    return pago

def obtener_venta_por_id(self, venta_id):
    # Implementa la lógica para buscar y devolver la venta por su ID
    # Por ejemplo, buscar en una lista o consultar la base de datos
    pass