"""
Sistema completo de ventas para el POS
Manejo de ventas, cálculos, impuestos y integración con inventario
"""

import logging
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP
import uuid

from modules.api.database import db_manager, ejecutar_consulta_segura
from modules.inventory.inventory import inventory_manager, TipoMovimiento
from modules.clients.client_manager import client_manager
from core.calculadora_caja import CalculadoraCaja, ProductoVenta
from core.models import Venta, VentaItem, EstadoVenta

@dataclass
class ItemVenta:
    """Item de venta con cálculos"""
    producto_id: int
    codigo: str
    nombre: str
    cantidad: int
    precio_unitario: float
    precio_original: float
    descuento_item: float = 0.0
    porcentaje_iva: float = 13.0
    aplica_iva: bool = True
    exento_impuesto: bool = False
    subtotal: float = 0.0
    iva: float = 0.0
    total: float = 0.0
    
    def __post_init__(self):
        self.calcular_totales()
    
    def calcular_totales(self):
        """Calcula subtotal, IVA y total del item"""
        self.subtotal = (self.precio_unitario * self.cantidad) - self.descuento_item
        
        if self.aplica_iva and not self.exento_impuesto:
            self.iva = self.subtotal * (self.porcentaje_iva / 100)
        else:
            self.iva = 0.0
        
        self.total = self.subtotal + self.iva

@dataclass
class ResumenVenta:
    """Resumen calculado de la venta"""
    subtotal: float = 0.0
    descuento_general: float = 0.0
    subtotal_con_descuento: float = 0.0
    iva_total: float = 0.0
    total_venta: float = 0.0
    cantidad_items: int = 0
    
    def calcular_desde_items(self, items: List[ItemVenta], descuento_general: float = 0.0):
        """Calcula resumen desde lista de items"""
        self.subtotal = sum(item.subtotal for item in items)
        self.descuento_general = descuento_general
        self.subtotal_con_descuento = self.subtotal - self.descuento_general
        self.iva_total = sum(item.iva for item in items)
        self.total_venta = self.subtotal_con_descuento + self.iva_total
        self.cantidad_items = sum(item.cantidad for item in items)

class ValidadorVentas:
    """Validador de ventas"""
    
    @staticmethod
    def validar_cantidad(cantidad: Union[int, float]) -> Tuple[bool, str]:
        """Valida cantidad de producto"""
        try:
            cantidad_num = float(cantidad)
            if cantidad_num <= 0:
                return False, "La cantidad debe ser mayor a cero"
            if cantidad_num > 1000:
                return False, "Cantidad máxima excedida (1000)"
            return True, "Cantidad válida"
        except (ValueError, TypeError):
            return False, "Cantidad debe ser un número válido"
    
    @staticmethod
    def validar_precio(precio: Union[int, float]) -> Tuple[bool, str]:
        """Valida precio de producto"""
        try:
            precio_num = float(precio)
            if precio_num < 0:
                return False, "El precio no puede ser negativo"
            if precio_num > 10000000:  # 10 millones
                return False, "Precio máximo excedido"
            return True, "Precio válido"
        except (ValueError, TypeError):
            return False, "Precio debe ser un número válido"
    
    @staticmethod
    def validar_descuento(descuento: Union[int, float], subtotal: float) -> Tuple[bool, str]:
        """Valida descuento"""
        try:
            descuento_num = float(descuento)
            if descuento_num < 0:
                return False, "El descuento no puede ser negativo"
            if descuento_num > subtotal:
                return False, "El descuento no puede ser mayor al subtotal"
            return True, "Descuento válido"
        except (ValueError, TypeError):
            return False, "Descuento debe ser un número válido"

class SalesManager:
    """Gestor principal de ventas"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.calculadora = CalculadoraCaja()
        self.validador = ValidadorVentas()
    
    def crear_nueva_venta(self, usuario_id: int, cliente_id: int = None) -> Tuple[bool, str, str]:
        """
        Crea una nueva venta
        
        Returns:
            Tupla (éxito, mensaje, numero_venta)
        """
        try:
            # Generar número de venta único
            numero_venta = self._generar_numero_venta()
            
            query = """
                INSERT INTO ventas (
                    numero_venta, cliente_id, usuario_id, fecha_venta, estado
                ) VALUES (?, ?, ?, ?, ?)
            """
            
            params = (
                numero_venta,
                cliente_id,
                usuario_id, 
                datetime.now().isoformat(),
                EstadoVenta.BORRADOR.value
            )
            
            ejecutar_consulta_segura(query, params)
            
            self.logger.info(f"Nueva venta creada: {numero_venta} por usuario {usuario_id}")
            return True, "Venta creada exitosamente", numero_venta
            
        except Exception as e:
            error_msg = f"Error creando nueva venta: {e}"
            self.logger.error(error_msg)
            return False, error_msg, ""
    
    def agregar_item_venta(self, numero_venta: str, producto_id: int, cantidad: int, 
                          precio_unitario: float = None, descuento_item: float = 0) -> Tuple[bool, str]:
        """
        Agrega un item a la venta
        
        Args:
            numero_venta: Número de la venta
            producto_id: ID del producto
            cantidad: Cantidad a vender
            precio_unitario: Precio unitario (opcional, usa precio del producto si no se especifica)
            descuento_item: Descuento específico del item
        """
        try:
            # Obtener venta
            venta = self._obtener_venta_por_numero(numero_venta)
            if not venta:
                return False, "Venta no encontrada"
            
            if venta['estado'] != EstadoVenta.BORRADOR.value:
                return False, "Solo se pueden agregar items a ventas en estado borrador"
            
            # Validar cantidad
            valida_cantidad, msg_cantidad = self.validador.validar_cantidad(cantidad)
            if not valida_cantidad:
                return False, msg_cantidad
            
            # Obtener producto
            producto = inventory_manager.obtener_producto(producto_id)
            if not producto:
                return False, "Producto no encontrado"
            
            if not producto.activo:
                return False, "Producto no está activo"
            
            # Verificar stock disponible
            if producto.stock_actual < cantidad:
                return False, f"Stock insuficiente. Disponible: {producto.stock_actual}"
            
            # Usar precio del producto si no se especifica
            if precio_unitario is None:
                precio_unitario = producto.precio_venta
            
            # Validar precio
            valida_precio, msg_precio = self.validador.validar_precio(precio_unitario)
            if not valida_precio:
                return False, msg_precio
            
            # Crear item de venta
            item_venta = ItemVenta(
                producto_id=producto_id,
                codigo=producto.codigo,
                nombre=producto.nombre,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                precio_original=producto.precio_venta,
                descuento_item=descuento_item,
                porcentaje_iva=producto.porcentaje_iva,
                aplica_iva=producto.aplica_iva,
                exento_impuesto=False
            )
            
            # Verificar si el item ya existe en la venta
            item_existente = self._obtener_item_venta_existente(venta['id'], producto_id, precio_unitario)
            
            if item_existente:
                # Actualizar cantidad del item existente
                nueva_cantidad = item_existente['cantidad'] + cantidad
                
                # Verificar stock con nueva cantidad
                if producto.stock_actual < nueva_cantidad:
                    return False, f"Stock insuficiente para cantidad total: {nueva_cantidad}. Disponible: {producto.stock_actual}"
                
                # Actualizar item
                query_update = """
                    UPDATE detalle_ventas 
                    SET cantidad = ?, subtotal = ?, iva = ?, total = ?
                    WHERE id = ?
                """
                
                item_venta.cantidad = nueva_cantidad
                item_venta.calcular_totales()
                
                params_update = (
                    nueva_cantidad,
                    item_venta.subtotal,
                    item_venta.iva,
                    item_venta.total,
                    item_existente['id']
                )
                
                ejecutar_consulta_segura(query_update, params_update)
                accion = "actualizado"
                
            else:
                # Insertar nuevo item
                query_insert = """
                    INSERT INTO detalle_ventas (
                        venta_id, producto_id, cantidad, precio_unitario, 
                        descuento, subtotal, iva, total
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                params_insert = (
                    venta['id'],
                    producto_id,
                    cantidad,
                    precio_unitario,
                    descuento_item,
                    item_venta.subtotal,
                    item_venta.iva,
                    item_venta.total
                )
                
                ejecutar_consulta_segura(query_insert, params_insert)
                accion = "agregado"
            
            # Actualizar totales de la venta
            self._actualizar_totales_venta(venta['id'])
            
            self.logger.info(f"Item {accion} en venta {numero_venta}: {producto.nombre} x{cantidad}")
            return True, f"Item {accion} exitosamente"
            
        except Exception as e:
            error_msg = f"Error agregando item a venta: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def remover_item_venta(self, numero_venta: str, detalle_id: int) -> Tuple[bool, str]:
        """Remueve un item de la venta"""
        try:
            # Obtener venta
            venta = self._obtener_venta_por_numero(numero_venta)
            if not venta:
                return False, "Venta no encontrada"
            
            if venta['estado'] != EstadoVenta.BORRADOR.value:
                return False, "Solo se pueden remover items de ventas en estado borrador"
            
            # Verificar que el item pertenece a la venta
            query_verificar = "SELECT id FROM detalle_ventas WHERE id = ? AND venta_id = ?"
            item_existe = ejecutar_consulta_segura(query_verificar, (detalle_id, venta['id']), fetch='one')
            
            if not item_existe:
                return False, "Item no encontrado en la venta"
            
            # Eliminar item
            query_eliminar = "DELETE FROM detalle_ventas WHERE id = ?"
            filas_afectadas = ejecutar_consulta_segura(query_eliminar, (detalle_id,))
            
            if filas_afectadas > 0:
                # Actualizar totales de la venta
                self._actualizar_totales_venta(venta['id'])
                
                self.logger.info(f"Item removido de venta {numero_venta}")
                return True, "Item removido exitosamente"
            else:
                return False, "No se pudo remover el item"
                
        except Exception as e:
            error_msg = f"Error removiendo item de venta: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def aplicar_descuento_general(self, numero_venta: str, descuento: float, 
                                 tipo_descuento: str = "monto") -> Tuple[bool, str]:
        """
        Aplica descuento general a la venta
        
        Args:
            numero_venta: Número de la venta
            descuento: Valor del descuento
            tipo_descuento: "monto" o "porcentaje"
        """
        try:
            # Obtener venta
            venta = self._obtener_venta_por_numero(numero_venta)
            if not venta:
                return False, "Venta no encontrada"
            
            if venta['estado'] != EstadoVenta.BORRADOR.value:
                return False, "Solo se puede aplicar descuento a ventas en estado borrador"
            
            # Calcular monto de descuento
            if tipo_descuento == "porcentaje":
                if descuento < 0 or descuento > 100:
                    return False, "El porcentaje de descuento debe estar entre 0 y 100"
                monto_descuento = venta['subtotal'] * (descuento / 100)
            else:
                monto_descuento = descuento
            
            # Validar descuento
            valida_descuento, msg_descuento = self.validador.validar_descuento(monto_descuento, venta['subtotal'])
            if not valida_descuento:
                return False, msg_descuento
            
            # Aplicar descuento
            query_descuento = """
                UPDATE ventas 
                SET descuento = ?, fecha_modificacion = ?
                WHERE id = ?
            """
            
            params_descuento = (
                monto_descuento,
                datetime.now().isoformat(),
                venta['id']
            )
            
            ejecutar_consulta_segura(query_descuento, params_descuento)
            
            # Actualizar totales
            self._actualizar_totales_venta(venta['id'])
            
            self.logger.info(f"Descuento aplicado a venta {numero_venta}: ₡{monto_descuento:.2f}")
            return True, "Descuento aplicado exitosamente"
            
        except Exception as e:
            error_msg = f"Error aplicando descuento: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def finalizar_venta(self, numero_venta: str, metodo_pago: str = "efectivo", 
                       monto_recibido: float = 0) -> Tuple[bool, str, Dict]:
        """
        Finaliza una venta y actualiza inventario
        
        Returns:
            Tupla (éxito, mensaje, datos_venta)
        """
        try:
            # Obtener venta completa
            venta_completa = self.obtener_venta_completa(numero_venta)
            if not venta_completa:
                return False, "Venta no encontrada", {}
            
            if venta_completa['estado'] != EstadoVenta.BORRADOR.value:
                return False, f"La venta ya está en estado: {venta_completa['estado']}", {}
            
            if not venta_completa['items']:
                return False, "No se puede finalizar venta sin items", {}
            
            # Verificar stock disponible para todos los items
            for item in venta_completa['items']:
                producto = inventory_manager.obtener_producto(item['producto_id'])
                if not producto or producto.stock_actual < item['cantidad']:
                    return False, f"Stock insuficiente para {item['nombre']}", {}
            
            # Calcular cambio
            cambio = max(0, monto_recibido - venta_completa['total'])
            
            # Operaciones en transacción
            operaciones = []
            
            # 1. Actualizar venta
            operaciones.append((
                """UPDATE ventas 
                   SET estado = ?, metodo_pago = ?, monto_recibido = ?, cambio = ?, 
                       fecha_modificacion = ?
                   WHERE numero_venta = ?""",
                (EstadoVenta.COMPLETADA.value, metodo_pago, monto_recibido, cambio,
                 datetime.now().isoformat(), numero_venta)
            ))
            
            # 2. Registrar movimientos de inventario
            for item in venta_completa['items']:
                # Actualizar stock
                inventory_manager.registrar_movimiento(
                    producto_id=item['producto_id'],
                    tipo_movimiento=TipoMovimiento.SALIDA_VENTA.value,
                    cantidad=item['cantidad'],
                    precio_unitario=item['precio_unitario'],
                    referencia_id=venta_completa['id'],
                    referencia_tipo='venta',
                    usuario_id=venta_completa['usuario_id'],
                    notas=f"Venta {numero_venta}"
                )
            
            # Ejecutar transacción
            exito_transaccion = db_manager.ejecutar_transaccion(operaciones)
            
            if not exito_transaccion:
                return False, "Error procesando venta", {}
            
            # Actualizar datos de respuesta
            venta_completa['estado'] = EstadoVenta.COMPLETADA.value
            venta_completa['metodo_pago'] = metodo_pago
            venta_completa['monto_recibido'] = monto_recibido
            venta_completa['cambio'] = cambio
            
            self.logger.info(f"Venta finalizada exitosamente: {numero_venta}")
            return True, "Venta finalizada exitosamente", venta_completa
            
        except Exception as e:
            error_msg = f"Error finalizando venta: {e}"
            self.logger.error(error_msg)
            return False, error_msg, {}
    
    def cancelar_venta(self, numero_venta: str, motivo: str = "") -> Tuple[bool, str]:
        """Cancela una venta"""
        try:
            # Obtener venta
            venta = self._obtener_venta_por_numero(numero_venta)
            if not venta:
                return False, "Venta no encontrada"
            
            if venta['estado'] == EstadoVenta.CANCELADA.value:
                return False, "La venta ya está cancelada"
            
            # Cancelar venta
            query_cancelar = """
                UPDATE ventas 
                SET estado = ?, notas = COALESCE(notas, '') || ?, fecha_modificacion = ?
                WHERE numero_venta = ?
            """
            
            nota_cancelacion = f" [CANCELADA: {motivo}]" if motivo else " [CANCELADA]"
            
            params_cancelar = (
                EstadoVenta.CANCELADA.value,
                nota_cancelacion,
                datetime.now().isoformat(),
                numero_venta
            )
            
            filas_afectadas = ejecutar_consulta_segura(query_cancelar, params_cancelar)
            
            if filas_afectadas > 0:
                self.logger.info(f"Venta cancelada: {numero_venta}. Motivo: {motivo}")
                return True, "Venta cancelada exitosamente"
            else:
                return False, "No se pudo cancelar la venta"
                
        except Exception as e:
            error_msg = f"Error cancelando venta: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def obtener_venta_completa(self, numero_venta: str) -> Optional[Dict]:
        """Obtiene venta completa con todos sus items"""
        try:
            # Obtener datos de venta
            query_venta = "SELECT * FROM ventas WHERE numero_venta = ?"
            venta_row = ejecutar_consulta_segura(query_venta, (numero_venta,), fetch='one')
            
            if not venta_row:
                return None
            
            venta_dict = dict(venta_row)
            
            # Obtener items de la venta
            query_items = """
                SELECT dv.*, p.codigo, p.nombre, p.unidad_medida
                FROM detalle_ventas dv
                JOIN productos p ON dv.producto_id = p.id
                WHERE dv.venta_id = ?
                ORDER BY dv.id
            """
            
            items_rows = ejecutar_consulta_segura(query_items, (venta_dict['id'],), fetch='all')
            
            items = []
            for item_row in items_rows:
                item_dict = dict(item_row)
                items.append(item_dict)
            
            # Obtener datos del cliente si existe
            cliente = None
            if venta_dict['cliente_id']:
                cliente_obj = client_manager.get_client(venta_dict['cliente_id'])
                if cliente_obj:
                    cliente = asdict(cliente_obj)
            
            # Construir resultado
            venta_completa = {
                **venta_dict,
                'items': items,
                'cliente': cliente,
                'cantidad_items': len(items),
                'cantidad_productos': sum(item['cantidad'] for item in items)
            }
            
            return venta_completa
            
        except Exception as e:
            self.logger.error(f"Error obteniendo venta completa: {e}")
            return None
    
    def listar_ventas(self, filtros: Dict[str, Any] = None, limite: int = 50, 
                     offset: int = 0) -> List[Dict]:
        """Lista ventas con filtros opcionales"""
        try:
            where_conditions = []
            params = []
            
            # Aplicar filtros
            if filtros:
                if filtros.get('estado'):
                    where_conditions.append("estado = ?")
                    params.append(filtros['estado'])
                
                if filtros.get('usuario_id'):
                    where_conditions.append("usuario_id = ?")
                    params.append(filtros['usuario_id'])
                
                if filtros.get('cliente_id'):
                    where_conditions.append("cliente_id = ?")
                    params.append(filtros['cliente_id'])
                
                if filtros.get('fecha_desde'):
                    where_conditions.append("DATE(fecha_venta) >= ?")
                    params.append(filtros['fecha_desde'])
                
                if filtros.get('fecha_hasta'):
                    where_conditions.append("DATE(fecha_venta) <= ?")
                    params.append(filtros['fecha_hasta'])
                
                if filtros.get('metodo_pago'):
                    where_conditions.append("metodo_pago = ?")
                    params.append(filtros['metodo_pago'])
                
                if filtros.get('total_min'):
                    where_conditions.append("total >= ?")
                    params.append(filtros['total_min'])
                
                if filtros.get('total_max'):
                    where_conditions.append("total <= ?")
                    params.append(filtros['total_max'])
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            query = f"""
                SELECT v.*, c.nombre as cliente_nombre
                FROM ventas v
                LEFT JOIN clientes c ON v.cliente_id = c.id
                WHERE {where_clause}
                ORDER BY v.fecha_venta DESC
                LIMIT ? OFFSET ?
            """
            
            params.extend([limite, offset])
            
            rows = ejecutar_consulta_segura(query, tuple(params), fetch='all')
            
            ventas = []
            for row in rows:
                venta_dict = dict(row)
                ventas.append(venta_dict)
            
            return ventas
            
        except Exception as e:
            self.logger.error(f"Error listando ventas: {e}")
            return []
    
    def _generar_numero_venta(self) -> str:
        """Genera número único de venta"""
        try:
            # Obtener último número de venta del día
            fecha_hoy = date.today().strftime('%Y%m%d')
            
            query = """
                SELECT COUNT(*) + 1
                FROM ventas 
                WHERE DATE(fecha_venta) = DATE('now', 'localtime')
            """
            
            result = ejecutar_consulta_segura(query, (), fetch='one')
            numero_secuencial = result[0] if result else 1
            
            return f"V{fecha_hoy}{numero_secuencial:04d}"  # V202312250001
            
        except:
            # Si hay error, usar timestamp
            import time
            return f"V{int(time.time())}"
    
    def _obtener_venta_por_numero(self, numero_venta: str) -> Optional[Dict]:
        """Obtiene venta por número"""
        try:
            query = "SELECT * FROM ventas WHERE numero_venta = ?"
            row = ejecutar_consulta_segura(query, (numero_venta,), fetch='one')
            return dict(row) if row else None
        except:
            return None
    
    def _obtener_item_venta_existente(self, venta_id: int, producto_id: int, 
                                     precio_unitario: float) -> Optional[Dict]:
        """Obtiene item existente en la venta con mismo producto y precio"""
        try:
            query = """
                SELECT * FROM detalle_ventas 
                WHERE venta_id = ? AND producto_id = ? AND precio_unitario = ?
            """
            row = ejecutar_consulta_segura(query, (venta_id, producto_id, precio_unitario), fetch='one')
            return dict(row) if row else None
        except:
            return None
    
    def _actualizar_totales_venta(self, venta_id: int):
        """Actualiza los totales calculados de la venta"""
        try:
            # Obtener totales de items
            query_totales = """
                SELECT 
                    COALESCE(SUM(subtotal), 0) as subtotal_items,
                    COALESCE(SUM(iva), 0) as iva_items,
                    COALESCE(SUM(total), 0) as total_items
                FROM detalle_ventas 
                WHERE venta_id = ?
            """
            
            result = ejecutar_consulta_segura(query_totales, (venta_id,), fetch='one')
            
            if result:
                subtotal_items = result[0]
                iva_items = result[1]
                total_items = result[2]
                
                # Obtener descuento general actual
                query_descuento = "SELECT COALESCE(descuento, 0) FROM ventas WHERE id = ?"
                descuento_result = ejecutar_consulta_segura(query_descuento, (venta_id,), fetch='one')
                descuento_general = descuento_result[0] if descuento_result else 0
                
                # Calcular totales finales
                subtotal_final = subtotal_items
                total_final = total_items - descuento_general
                
                # Actualizar venta
                query_update = """
                    UPDATE ventas 
                    SET subtotal = ?, iva = ?, total = ?, fecha_modificacion = ?
                    WHERE id = ?
                """
                
                params_update = (
                    subtotal_final,
                    iva_items,
                    total_final,
                    datetime.now().isoformat(),
                    venta_id
                )
                
                ejecutar_consulta_segura(query_update, params_update)
                
        except Exception as e:
            self.logger.error(f"Error actualizando totales de venta: {e}")

# Instancia global del gestor de ventas
sales_manager = SalesManager()

# Funciones de compatibilidad con código existente
def create_new_sale(user: Dict) -> bool:
    """Función de compatibilidad simplificada"""
    try:
        usuario_id = user.get('id', 1)
        exito, _, _ = sales_manager.crear_nueva_venta(usuario_id)
        return exito
    except:
        return False

def procesar_venta_completa(datos_venta: Dict) -> Tuple[bool, str, Dict]:
    """Función de utilidad para procesar venta completa"""
    return sales_manager.finalizar_venta(
        datos_venta['numero_venta'],
        datos_venta.get('metodo_pago', 'efectivo'),
        datos_venta.get('monto_recibido', 0)
    )