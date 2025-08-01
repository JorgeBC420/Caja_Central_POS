"""
Sistema completo de gestión de inventario para POS
Incluye control de stock, movimientos, alertas y análisis
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

from modules.api.database import db_manager, ejecutar_consulta_segura
from core.models import Producto, EstadoProducto

class TipoMovimiento(Enum):
    """Tipos de movimientos de inventario"""
    ENTRADA_COMPRA = "entrada_compra"
    ENTRADA_AJUSTE = "entrada_ajuste"
    ENTRADA_DEVOLUCION = "entrada_devolucion"
    SALIDA_VENTA = "salida_venta"
    SALIDA_AJUSTE = "salida_ajuste"
    SALIDA_MERMA = "salida_merma"
    SALIDA_REGALO = "salida_regalo"
    SALIDA_MUESTRA = "salida_muestra"
    TRANSFERENCIA_ENTRADA = "transferencia_entrada"
    TRANSFERENCIA_SALIDA = "transferencia_salida"

@dataclass
class MovimientoInventario:
    """Movimiento de inventario"""
    id: int = 0
    producto_id: int = 0
    tipo_movimiento: str = ""
    cantidad: int = 0
    stock_anterior: int = 0
    stock_nuevo: int = 0
    precio_unitario: float = 0.0
    referencia_id: int = 0
    referencia_tipo: str = ""
    usuario_id: int = 0
    fecha_movimiento: str = ""
    notas: str = ""

@dataclass
class AlertaStock:
    """Alerta de stock"""
    producto_id: int
    codigo: str
    nombre: str
    stock_actual: int
    stock_minimo: int
    stock_maximo: int
    tipo_alerta: str  # bajo, agotado, exceso
    dias_sin_movimiento: int = 0
    
@dataclass
class EstadisticasInventario:
    """Estadísticas del inventario"""
    total_productos: int
    productos_activos: int
    productos_bajo_stock: int
    productos_agotados: int
    productos_exceso: int
    valor_total_inventario: float
    valor_inventario_costo: float
    rotacion_promedio: float
    productos_sin_movimiento: int

class InventoryManager:
    """Gestor principal de inventario"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def agregar_producto(self, datos_producto: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        Agregar nuevo producto al inventario
        
        Args:
            datos_producto: Datos del producto
            
        Returns:
            Tupla (éxito, mensaje, producto_id)
        """
        try:
            # Validar datos requeridos
            if not datos_producto.get('nombre'):
                return False, "El nombre del producto es requerido", 0
            
            if not datos_producto.get('codigo'):
                return False, "El código del producto es requerido", 0
            
            # Verificar que el código no exista
            if self._codigo_existe(datos_producto['codigo']):
                return False, "Ya existe un producto con este código", 0
            
            # Verificar código de barras si se proporciona
            if datos_producto.get('codigo_barras'):
                if self._codigo_barras_existe(datos_producto['codigo_barras']):
                    return False, "Ya existe un producto con este código de barras", 0
            
            # Generar código si no se proporciona
            if not datos_producto.get('codigo'):
                datos_producto['codigo'] = self._generar_codigo_producto()
            
            # Insertar producto
            query = """
                INSERT INTO productos (
                    codigo, codigo_barras, nombre, descripcion, categoria_id, proveedor_id,
                    precio_compra, precio_venta, precio_mayoreo, cantidad_mayoreo,
                    stock_actual, stock_minimo, stock_maximo, unidad_medida,
                    aplica_iva, porcentaje_iva, fecha_vencimiento, ubicacion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                datos_producto['codigo'],
                datos_producto.get('codigo_barras', ''),
                datos_producto['nombre'],
                datos_producto.get('descripcion', ''),
                datos_producto.get('categoria_id'),
                datos_producto.get('proveedor_id'),
                datos_producto.get('precio_compra', 0),
                datos_producto.get('precio_venta', 0),
                datos_producto.get('precio_mayoreo', 0),
                datos_producto.get('cantidad_mayoreo', 1),
                datos_producto.get('stock_inicial', 0),
                datos_producto.get('stock_minimo', 1),
                datos_producto.get('stock_maximo', 100),
                datos_producto.get('unidad_medida', 'unidad'),
                datos_producto.get('aplica_iva', True),
                datos_producto.get('porcentaje_iva', 13.0),
                datos_producto.get('fecha_vencimiento', ''),
                datos_producto.get('ubicacion', '')
            )
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                producto_id = cursor.lastrowid
                conn.commit()
            
            # Registrar movimiento inicial si hay stock
            stock_inicial = datos_producto.get('stock_inicial', 0)
            if stock_inicial > 0:
                self.registrar_movimiento(
                    producto_id=producto_id,
                    tipo_movimiento=TipoMovimiento.ENTRADA_AJUSTE.value,
                    cantidad=stock_inicial,
                    precio_unitario=datos_producto.get('precio_compra', 0),
                    notas="Stock inicial",
                    usuario_id=datos_producto.get('usuario_id', 1)
                )
            
            self.logger.info(f"Producto creado: {datos_producto['nombre']} (ID: {producto_id})")
            return True, "Producto creado exitosamente", producto_id
            
        except Exception as e:
            error_msg = f"Error creando producto: {e}"
            self.logger.error(error_msg)
            return False, error_msg, 0
    
    def actualizar_producto(self, producto_id: int, datos_actualizacion: Dict[str, Any]) -> Tuple[bool, str]:
        """Actualizar producto existente"""
        try:
            # Verificar que el producto existe
            if not self._producto_existe(producto_id):
                return False, "Producto no encontrado"
            
            # Validar código único si se actualiza
            if 'codigo' in datos_actualizacion:
                if self._codigo_existe(datos_actualizacion['codigo'], excluir_id=producto_id):
                    return False, "Ya existe otro producto con este código"
            
            # Validar código de barras único si se actualiza
            if 'codigo_barras' in datos_actualizacion and datos_actualizacion['codigo_barras']:
                if self._codigo_barras_existe(datos_actualizacion['codigo_barras'], excluir_id=producto_id):
                    return False, "Ya existe otro producto con este código de barras"
            
            # Construir query de actualización
            campos_actualizacion = []
            valores = []
            
            campos_permitidos = [
                'codigo', 'codigo_barras', 'nombre', 'descripcion', 'categoria_id', 'proveedor_id',
                'precio_compra', 'precio_venta', 'precio_mayoreo', 'cantidad_mayoreo',
                'stock_minimo', 'stock_maximo', 'unidad_medida', 'aplica_iva', 'porcentaje_iva',
                'fecha_vencimiento', 'ubicacion', 'activo'
            ]
            
            for campo in campos_permitidos:
                if campo in datos_actualizacion:
                    campos_actualizacion.append(f"{campo} = ?")
                    valores.append(datos_actualizacion[campo])
            
            if not campos_actualizacion:
                return False, "No hay datos para actualizar"
            
            # Agregar fecha de modificación
            campos_actualizacion.append("fecha_modificacion = ?")
            valores.append(datetime.now().isoformat())
            valores.append(producto_id)
            
            query = f"""
                UPDATE productos 
                SET {', '.join(campos_actualizacion)}
                WHERE id = ?
            """
            
            filas_afectadas = ejecutar_consulta_segura(query, tuple(valores))
            
            if filas_afectadas > 0:
                self.logger.info(f"Producto {producto_id} actualizado")
                return True, "Producto actualizado exitosamente"
            else:
                return False, "No se realizaron cambios"
                
        except Exception as e:
            error_msg = f"Error actualizando producto: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def eliminar_producto(self, producto_id: int, eliminar_fisicamente: bool = False) -> Tuple[bool, str]:
        """Eliminar producto del inventario"""
        try:
            # Verificar que el producto existe
            if not self._producto_existe(producto_id):
                return False, "Producto no encontrado"
            
            # Verificar si tiene movimientos de inventario
            tiene_movimientos = self._producto_tiene_movimientos(producto_id)
            
            if tiene_movimientos and eliminar_fisicamente:
                return False, "No se puede eliminar: producto tiene movimientos registrados"
            
            if eliminar_fisicamente and not tiene_movimientos:
                # Eliminación física
                query = "DELETE FROM productos WHERE id = ?"
                filas_afectadas = ejecutar_consulta_segura(query, (producto_id,))
                mensaje = "Producto eliminado permanentemente"
            else:
                # Eliminación lógica (desactivar)
                query = """
                    UPDATE productos 
                    SET activo = 0, fecha_modificacion = ?
                    WHERE id = ?
                """
                filas_afectadas = ejecutar_consulta_segura(query, (datetime.now().isoformat(), producto_id))
                mensaje = "Producto desactivado"
            
            if filas_afectadas > 0:
                self.logger.info(f"Producto {producto_id}: {mensaje}")
                return True, mensaje
            else:
                return False, "No se pudo realizar la operación"
                
        except Exception as e:
            error_msg = f"Error eliminando producto: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def obtener_producto(self, producto_id: int) -> Optional[Producto]:
        """Obtener producto por ID"""
        try:
            query = "SELECT * FROM productos WHERE id = ? AND activo = 1"
            row = ejecutar_consulta_segura(query, (producto_id,), fetch='one')
            
            if not row:
                return None
            
            return self._row_to_producto(row)
            
        except Exception as e:
            self.logger.error(f"Error obteniendo producto {producto_id}: {e}")
            return None
    
    def buscar_productos(self, termino_busqueda: str, limite: int = 50) -> List[Producto]:
        """Búsqueda de productos por código, nombre o descripción"""
        try:
            query = """
                SELECT * FROM productos 
                WHERE activo = 1 AND (
                    codigo LIKE ? OR 
                    codigo_barras = ? OR
                    nombre LIKE ? OR 
                    descripcion LIKE ?
                )
                ORDER BY 
                    CASE 
                        WHEN codigo = ? THEN 1
                        WHEN codigo_barras = ? THEN 2
                        WHEN nombre LIKE ? THEN 3
                        ELSE 4
                    END,
                    nombre
                LIMIT ?
            """
            
            busqueda = f"%{termino_busqueda}%"
            params = [
                busqueda, termino_busqueda, busqueda, busqueda,
                termino_busqueda, termino_busqueda, f"{termino_busqueda}%",
                limite
            ]
            
            rows = ejecutar_consulta_segura(query, tuple(params), fetch='all')
            
            productos = []
            for row in rows:
                producto = self._row_to_producto(row)
                if producto:
                    productos.append(producto)
            
            return productos
            
        except Exception as e:
            self.logger.error(f"Error buscando productos: {e}")
            return []
    
    def listar_productos(self, filtros: Dict[str, Any] = None, limite: int = 100, offset: int = 0) -> List[Producto]:
        """Listar productos con filtros opcionales"""
        try:
            where_conditions = ["activo = 1"]
            params = []
            
            # Aplicar filtros
            if filtros:
                if filtros.get('categoria_id'):
                    where_conditions.append("categoria_id = ?")
                    params.append(filtros['categoria_id'])
                
                if filtros.get('proveedor_id'):
                    where_conditions.append("proveedor_id = ?")
                    params.append(filtros['proveedor_id'])
                
                if filtros.get('stock_bajo'):
                    where_conditions.append("stock_actual <= stock_minimo")
                
                if filtros.get('agotados'):
                    where_conditions.append("stock_actual = 0")
                
                if filtros.get('con_stock'):
                    where_conditions.append("stock_actual > 0")
                
                if filtros.get('precio_min'):
                    where_conditions.append("precio_venta >= ?")
                    params.append(filtros['precio_min'])
                
                if filtros.get('precio_max'):
                    where_conditions.append("precio_venta <= ?")
                    params.append(filtros['precio_max'])
            
            where_clause = " AND ".join(where_conditions)
            
            query = f"""
                SELECT * FROM productos 
                WHERE {where_clause}
                ORDER BY nombre
                LIMIT ? OFFSET ?
            """
            
            params.extend([limite, offset])
            
            rows = ejecutar_consulta_segura(query, tuple(params), fetch='all')
            
            productos = []
            for row in rows:
                producto = self._row_to_producto(row)
                if producto:
                    productos.append(producto)
            
            return productos
            
        except Exception as e:
            self.logger.error(f"Error listando productos: {e}")
            return []
    
    def registrar_movimiento(self, producto_id: int, tipo_movimiento: str, cantidad: int,
                           precio_unitario: float = 0, referencia_id: int = 0,
                           referencia_tipo: str = "", usuario_id: int = 0,
                           notas: str = "") -> Tuple[bool, str]:
        """Registrar movimiento de inventario"""
        try:
            # Obtener stock actual
            query_stock = "SELECT stock_actual FROM productos WHERE id = ?"
            result = ejecutar_consulta_segura(query_stock, (producto_id,), fetch='one')
            
            if not result:
                return False, "Producto no encontrado"
            
            stock_anterior = result[0]
            
            # Calcular nuevo stock
            if tipo_movimiento in [TipoMovimiento.ENTRADA_COMPRA.value, TipoMovimiento.ENTRADA_AJUSTE.value, 
                                  TipoMovimiento.ENTRADA_DEVOLUCION.value, TipoMovimiento.TRANSFERENCIA_ENTRADA.value]:
                stock_nuevo = stock_anterior + cantidad
            elif tipo_movimiento in [TipoMovimiento.SALIDA_VENTA.value, TipoMovimiento.SALIDA_AJUSTE.value, 
                                   TipoMovimiento.SALIDA_MERMA.value, TipoMovimiento.SALIDA_REGALO.value,
                                   TipoMovimiento.SALIDA_MUESTRA.value, TipoMovimiento.TRANSFERENCIA_SALIDA.value]:
                stock_nuevo = stock_anterior - cantidad
                if stock_nuevo < 0:
                    return False, f"Stock insuficiente. Stock actual: {stock_anterior}, intentando retirar: {cantidad}"
            else:
                return False, f"Tipo de movimiento no válido: {tipo_movimiento}"
            
            # Operaciones en transacción
            operaciones = [
                # Actualizar stock del producto
                ("UPDATE productos SET stock_actual = ?, fecha_modificacion = ? WHERE id = ?",
                 (stock_nuevo, datetime.now().isoformat(), producto_id)),
                
                # Registrar movimiento
                ("""INSERT INTO movimientos_inventario 
                    (producto_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, 
                     precio_unitario, referencia_id, referencia_tipo, usuario_id, notas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                 (producto_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo,
                  precio_unitario, referencia_id, referencia_tipo, usuario_id, notas))
            ]
            
            exito = db_manager.ejecutar_transaccion(operaciones)
            
            if exito:
                self.logger.info(f"Movimiento registrado: Producto {producto_id}, {tipo_movimiento}, cantidad {cantidad}")
                return True, "Movimiento registrado exitosamente"
            else:
                return False, "Error registrando movimiento"
                
        except Exception as e:
            error_msg = f"Error registrando movimiento: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def ajustar_stock(self, producto_id: int, nuevo_stock: int, usuario_id: int, 
                     motivo: str = "") -> Tuple[bool, str]:
        """Ajustar stock de un producto"""
        try:
            # Obtener stock actual
            query_stock = "SELECT stock_actual FROM productos WHERE id = ?"
            result = ejecutar_consulta_segura(query_stock, (producto_id,), fetch='one')
            
            if not result:
                return False, "Producto no encontrado"
            
            stock_actual = result[0]
            diferencia = nuevo_stock - stock_actual
            
            if diferencia == 0:
                return True, "No hay cambios en el stock"
            
            # Determinar tipo de movimiento
            if diferencia > 0:
                tipo_movimiento = TipoMovimiento.ENTRADA_AJUSTE.value
                cantidad = diferencia
            else:
                tipo_movimiento = TipoMovimiento.SALIDA_AJUSTE.value
                cantidad = abs(diferencia)
            
            notas = f"Ajuste de stock. Motivo: {motivo}" if motivo else "Ajuste de stock"
            
            return self.registrar_movimiento(
                producto_id=producto_id,
                tipo_movimiento=tipo_movimiento,
                cantidad=cantidad,
                usuario_id=usuario_id,
                notas=notas
            )
            
        except Exception as e:
            error_msg = f"Error ajustando stock: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def obtener_alertas_stock(self) -> List[AlertaStock]:
        """Obtener alertas de stock bajo, agotado o en exceso"""
        try:
            query = """
                SELECT 
                    p.id, p.codigo, p.nombre, p.stock_actual, 
                    p.stock_minimo, p.stock_maximo,
                    COALESCE((
                        SELECT MAX(fecha_movimiento) 
                        FROM movimientos_inventario 
                        WHERE producto_id = p.id
                    ), p.fecha_creacion) as ultimo_movimiento
                FROM productos p
                WHERE p.activo = 1 AND (
                    p.stock_actual <= p.stock_minimo OR 
                    p.stock_actual = 0 OR 
                    p.stock_actual > p.stock_maximo
                )
                ORDER BY 
                    CASE 
                        WHEN p.stock_actual = 0 THEN 1
                        WHEN p.stock_actual <= p.stock_minimo THEN 2
                        WHEN p.stock_actual > p.stock_maximo THEN 3
                        ELSE 4
                    END,
                    p.nombre
            """
            
            rows = ejecutar_consulta_segura(query, (), fetch='all')
            
            alertas = []
            for row in rows:
                # Determinar tipo de alerta
                if row[3] == 0:  # stock_actual = 0
                    tipo_alerta = "agotado"
                elif row[3] <= row[4]:  # stock_actual <= stock_minimo
                    tipo_alerta = "bajo"
                elif row[3] > row[5]:  # stock_actual > stock_maximo
                    tipo_alerta = "exceso"
                else:
                    tipo_alerta = "normal"
                
                # Calcular días sin movimiento
                ultimo_movimiento = datetime.fromisoformat(row[6])
                dias_sin_movimiento = (datetime.now() - ultimo_movimiento).days
                
                alerta = AlertaStock(
                    producto_id=row[0],
                    codigo=row[1],
                    nombre=row[2],
                    stock_actual=row[3],
                    stock_minimo=row[4],
                    stock_maximo=row[5],
                    tipo_alerta=tipo_alerta,
                    dias_sin_movimiento=dias_sin_movimiento
                )
                alertas.append(alerta)
            
            return alertas
            
        except Exception as e:
            self.logger.error(f"Error obteniendo alertas de stock: {e}")
            return []
    
    def obtener_estadisticas_inventario(self) -> EstadisticasInventario:
        """Obtener estadísticas generales del inventario"""
        try:
            # Estadísticas básicas
            query_basicas = """
                SELECT 
                    COUNT(*) as total_productos,
                    COUNT(CASE WHEN activo = 1 THEN 1 END) as productos_activos,
                    COUNT(CASE WHEN activo = 1 AND stock_actual <= stock_minimo THEN 1 END) as productos_bajo_stock,
                    COUNT(CASE WHEN activo = 1 AND stock_actual = 0 THEN 1 END) as productos_agotados,
                    COUNT(CASE WHEN activo = 1 AND stock_actual > stock_maximo THEN 1 END) as productos_exceso,
                    COALESCE(SUM(CASE WHEN activo = 1 THEN stock_actual * precio_venta END), 0) as valor_total,
                    COALESCE(SUM(CASE WHEN activo = 1 THEN stock_actual * precio_compra END), 0) as valor_costo
                FROM productos
            """
            
            result = ejecutar_consulta_segura(query_basicas, (), fetch='one')
            
            if not result:
                return EstadisticasInventario(0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0)
            
            # Productos sin movimiento en 90 días
            fecha_limite = (datetime.now() - timedelta(days=90)).isoformat()
            query_sin_movimiento = """
                SELECT COUNT(*) FROM productos p
                WHERE p.activo = 1 
                AND p.id NOT IN (
                    SELECT DISTINCT producto_id 
                    FROM movimientos_inventario 
                    WHERE fecha_movimiento >= ?
                )
            """
            
            sin_movimiento_result = ejecutar_consulta_segura(query_sin_movimiento, (fecha_limite,), fetch='one')
            productos_sin_movimiento = sin_movimiento_result[0] if sin_movimiento_result else 0
            
            # Rotación promedio (simplificada)
            # Se podría calcular de manera más sofisticada con más datos
            rotacion_promedio = 0.0
            if result[1] > 0:  # productos_activos > 0
                rotacion_promedio = (result[1] - productos_sin_movimiento) / result[1] * 100
            
            return EstadisticasInventario(
                total_productos=result[0],
                productos_activos=result[1],
                productos_bajo_stock=result[2],
                productos_agotados=result[3],
                productos_exceso=result[4],
                valor_total_inventario=result[5],
                valor_inventario_costo=result[6],
                rotacion_promedio=rotacion_promedio,
                productos_sin_movimiento=productos_sin_movimiento
            )
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return EstadisticasInventario(0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0)
    
    def obtener_movimientos_producto(self, producto_id: int, limite: int = 50) -> List[MovimientoInventario]:
        """Obtener historial de movimientos de un producto"""
        try:
            query = """
                SELECT * FROM movimientos_inventario 
                WHERE producto_id = ?
                ORDER BY fecha_movimiento DESC
                LIMIT ?
            """
            
            rows = ejecutar_consulta_segura(query, (producto_id, limite), fetch='all')
            
            movimientos = []
            for row in rows:
                movimiento = MovimientoInventario(
                    id=row[0],
                    producto_id=row[1],
                    tipo_movimiento=row[2],
                    cantidad=row[3],
                    stock_anterior=row[4],
                    stock_nuevo=row[5],
                    precio_unitario=row[6] or 0.0,
                    referencia_id=row[7] or 0,
                    referencia_tipo=row[8] or "",
                    usuario_id=row[9] or 0,
                    fecha_movimiento=row[10],
                    notas=row[11] or ""
                )
                movimientos.append(movimiento)
            
            return movimientos
            
        except Exception as e:
            self.logger.error(f"Error obteniendo movimientos del producto {producto_id}: {e}")
            return []
    
    def generar_reporte_rotacion(self, dias: int = 30) -> List[Dict[str, Any]]:
        """Generar reporte de rotación de productos"""
        try:
            fecha_inicio = (datetime.now() - timedelta(days=dias)).isoformat()
            
            query = """
                SELECT 
                    p.id, p.codigo, p.nombre, p.stock_actual, p.precio_venta,
                    COALESCE(SUM(
                        CASE WHEN m.tipo_movimiento LIKE 'salida_%' 
                        THEN m.cantidad ELSE 0 END
                    ), 0) as cantidad_vendida,
                    COUNT(CASE WHEN m.tipo_movimiento LIKE 'salida_%' THEN 1 END) as transacciones,
                    COALESCE(AVG(p.stock_actual), 0) as stock_promedio
                FROM productos p
                LEFT JOIN movimientos_inventario m ON p.id = m.producto_id 
                    AND m.fecha_movimiento >= ?
                WHERE p.activo = 1
                GROUP BY p.id, p.codigo, p.nombre, p.stock_actual, p.precio_venta
                HAVING cantidad_vendida > 0 OR stock_actual > 0
                ORDER BY cantidad_vendida DESC, transacciones DESC
            """
            
            rows = ejecutar_consulta_segura(query, (fecha_inicio,), fetch='all')
            
            reporte = []
            for row in rows:
                # Calcular rotación
                rotacion = 0.0
                if row[7] > 0:  # stock_promedio > 0
                    rotacion = row[5] / row[7]  # cantidad_vendida / stock_promedio
                
                # Calcular ingresos
                ingresos = row[5] * row[4]  # cantidad_vendida * precio_venta
                
                item = {
                    'producto_id': row[0],
                    'codigo': row[1],
                    'nombre': row[2],
                    'stock_actual': row[3],
                    'precio_venta': row[4],
                    'cantidad_vendida': row[5],
                    'transacciones': row[6],
                    'stock_promedio': row[7],
                    'rotacion': round(rotacion, 2),
                    'ingresos': round(ingresos, 2),
                    'dias_analisis': dias
                }
                reporte.append(item)
            
            return reporte
            
        except Exception as e:
            self.logger.error(f"Error generando reporte de rotación: {e}")
            return []
    
    def _producto_existe(self, producto_id: int) -> bool:
        """Verifica si un producto existe"""
        try:
            query = "SELECT COUNT(*) FROM productos WHERE id = ?"
            result = ejecutar_consulta_segura(query, (producto_id,), fetch='one')
            return result[0] > 0
        except:
            return False
    
    def _codigo_existe(self, codigo: str, excluir_id: int = None) -> bool:
        """Verifica si existe un producto con el mismo código"""
        try:
            if excluir_id:
                query = "SELECT COUNT(*) FROM productos WHERE codigo = ? AND id != ?"
                params = (codigo, excluir_id)
            else:
                query = "SELECT COUNT(*) FROM productos WHERE codigo = ?"
                params = (codigo,)
            
            result = ejecutar_consulta_segura(query, params, fetch='one')
            return result[0] > 0
        except:
            return False
    
    def _codigo_barras_existe(self, codigo_barras: str, excluir_id: int = None) -> bool:
        """Verifica si existe un producto con el mismo código de barras"""
        try:
            if excluir_id:
                query = "SELECT COUNT(*) FROM productos WHERE codigo_barras = ? AND id != ?"
                params = (codigo_barras, excluir_id)
            else:
                query = "SELECT COUNT(*) FROM productos WHERE codigo_barras = ?"
                params = (codigo_barras,)
            
            result = ejecutar_consulta_segura(query, params, fetch='one')
            return result[0] > 0
        except:
            return False
    
    def _producto_tiene_movimientos(self, producto_id: int) -> bool:
        """Verifica si un producto tiene movimientos registrados"""
        try:
            query = "SELECT COUNT(*) FROM movimientos_inventario WHERE producto_id = ?"
            result = ejecutar_consulta_segura(query, (producto_id,), fetch='one')
            return result[0] > 0
        except:
            return False
    
    def _generar_codigo_producto(self) -> str:
        """Genera un código único para producto"""
        try:
            # Obtener el último número de código
            query = """
                SELECT COALESCE(MAX(CAST(SUBSTR(codigo, 2) AS INTEGER)), 0) + 1 
                FROM productos 
                WHERE codigo LIKE 'P%' AND LENGTH(codigo) <= 8
            """
            
            result = ejecutar_consulta_segura(query, (), fetch='one')
            nuevo_numero = result[0] if result else 1
            
            return f"P{nuevo_numero:06d}"  # P000001, P000002, etc.
            
        except:
            # Si hay error, usar timestamp
            import time
            return f"P{int(time.time())}"
    
    def _row_to_producto(self, row) -> Optional[Producto]:
        """Convierte row de BD a objeto Producto"""
        try:
            if not row:
                return None
            
            return Producto(
                id=row[0],
                codigo=row[1],
                codigo_barras=row[2] or '',
                nombre=row[3],
                descripcion=row[4] or '',
                categoria_id=row[5],
                proveedor_id=row[6],
                precio_compra=row[7],
                precio_venta=row[8],
                precio_mayoreo=row[9] or 0,
                cantidad_mayoreo=row[10] or 1,
                stock_actual=row[11],
                stock_minimo=row[12],
                stock_maximo=row[13],
                unidad_medida=row[14] or 'unidad',
                aplica_iva=bool(row[15]),
                porcentaje_iva=row[16] or 0,
                activo=bool(row[17]),
                fecha_vencimiento=row[18] or '',
                ubicacion=row[19] or '',
                fecha_creacion=row[20],
                fecha_modificacion=row[21]
            )
            
        except Exception as e:
            self.logger.error(f"Error convirtiendo row a producto: {e}")
            return None

# Instancia global del gestor de inventario
inventory_manager = InventoryManager()

# Funciones de utilidad para compatibilidad
def agregar_producto(datos: Dict) -> bool:
    """Función de compatibilidad"""
    exito, _, _ = inventory_manager.agregar_producto(datos)
    return exito

def actualizar_stock(producto_id: int, nuevo_stock: int, usuario_id: int = 1) -> bool:
    """Función de utilidad para actualizar stock"""
    exito, _ = inventory_manager.ajustar_stock(producto_id, nuevo_stock, usuario_id)
    return exito

def obtener_productos_bajo_stock() -> List[Dict]:
    """Función de utilidad para obtener productos con stock bajo"""
    alertas = inventory_manager.obtener_alertas_stock()
    return [asdict(alerta) for alerta in alertas if alerta.tipo_alerta in ['bajo', 'agotado']]
