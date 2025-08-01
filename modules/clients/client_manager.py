
"""
Gestor avanzado de clientes para el sistema POS
Manejo completo de información de clientes, historial y análisis
"""

import sqlite3
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict

from modules.api.database import db_manager, ejecutar_consulta_segura
from core.models import Cliente, EstadoCliente

@dataclass
class HistorialCompra:
    """Historial de compras del cliente"""
    venta_id: int
    fecha: str
    total: float
    productos: int
    metodo_pago: str
    estado: str

@dataclass
class EstadisticasCliente:
    """Estadísticas del cliente"""
    total_compras: int
    monto_total_gastado: float
    promedio_compra: float
    ultima_compra: str
    producto_favorito: str
    categoria_favorita: str
    frecuencia_compras_mes: float

@dataclass
class ClienteDetallado(Cliente):
    """Cliente con información detallada"""
    estadisticas: EstadisticasCliente = None
    historial: List[HistorialCompra] = None
    apartados_activos: int = 0
    saldo_apartados: float = 0.0

class ValidadorCliente:
    """Validador de datos de clientes"""
    
    @staticmethod
    def validar_identificacion(identificacion: str, tipo: str = 'cedula') -> Tuple[bool, str]:
        """Valida identificación según el tipo"""
        try:
            # Limpiar identificación
            id_limpia = re.sub(r'[^0-9]', '', identificacion)
            
            if tipo.lower() == 'cedula':
                return ValidadorCliente._validar_cedula_cr(id_limpia)
            elif tipo.lower() == 'dimex':
                return ValidadorCliente._validar_dimex(id_limpia)
            elif tipo.lower() == 'nite':
                return ValidadorCliente._validar_nite(id_limpia)
            elif tipo.lower() == 'juridica':
                return ValidadorCliente._validar_cedula_juridica(id_limpia)
            else:
                return True, "Tipo de identificación válido"
                
        except Exception as e:
            return False, f"Error validando identificación: {e}"
    
    @staticmethod
    def _validar_cedula_cr(cedula: str) -> Tuple[bool, str]:
        """Valida cédula costarricense"""
        if len(cedula) != 9:
            return False, "Cédula debe tener 9 dígitos"
        
        if cedula[0] == '0':
            return False, "Cédula no puede empezar con 0"
        
        # Algoritmo de validación
        digitos = [int(d) for d in cedula[:8]]
        multiplicadores = [2, 1, 2, 1, 2, 1, 2, 1]
        
        suma = 0
        for i, digito in enumerate(digitos):
            producto = digito * multiplicadores[i]
            if producto > 9:
                producto = producto // 10 + producto % 10
            suma += producto
        
        digito_verificador = (10 - (suma % 10)) % 10
        
        if digito_verificador == int(cedula[8]):
            return True, "Cédula válida"
        else:
            return False, "Dígito verificador incorrecto"
    
    @staticmethod
    def _validar_dimex(dimex: str) -> Tuple[bool, str]:
        """Valida DIMEX"""
        if len(dimex) in [11, 12]:
            return True, "DIMEX válido"
        return False, "DIMEX debe tener 11 o 12 dígitos"
    
    @staticmethod
    def _validar_nite(nite: str) -> Tuple[bool, str]:
        """Valida NITE"""
        if len(nite) == 10:
            return True, "NITE válido"
        return False, "NITE debe tener 10 dígitos"
    
    @staticmethod
    def _validar_cedula_juridica(cedula: str) -> Tuple[bool, str]:
        """Valida cédula jurídica"""
        if len(cedula) == 10 and cedula.startswith('3'):
            return True, "Cédula jurídica válida"
        return False, "Cédula jurídica debe tener 10 dígitos y empezar con 3"
    
    @staticmethod
    def validar_email(email: str) -> bool:
        """Valida formato de email"""
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(patron, email) is not None
    
    @staticmethod
    def validar_telefono(telefono: str) -> bool:
        """Valida teléfono costarricense"""
        tel_limpio = re.sub(r'[^0-9]', '', telefono)
        
        # 8 dígitos para teléfono local
        if len(tel_limpio) == 8:
            return tel_limpio[0] in ['2', '4', '6', '7', '8']
        
        # 11 dígitos con código de país
        if len(tel_limpio) == 11 and tel_limpio.startswith('506'):
            return tel_limpio[3:4] in ['2', '4', '6', '7', '8']
        
        return False

class ClientManager:
    """Gestor principal de clientes"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validador = ValidadorCliente()
    
    def add_client(self, datos_cliente: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        Agregar un nuevo cliente
        
        Args:
            datos_cliente: Diccionario con datos del cliente
            
        Returns:
            Tupla (éxito, mensaje, cliente_id)
        """
        try:
            # Validar datos requeridos
            if not datos_cliente.get('nombre'):
                return False, "El nombre es requerido", 0
            
            # Validar identificación si se proporciona
            if datos_cliente.get('identificacion'):
                valida, mensaje = self.validador.validar_identificacion(
                    datos_cliente['identificacion'],
                    datos_cliente.get('tipo_identificacion', 'cedula')
                )
                if not valida:
                    return False, f"Identificación inválida: {mensaje}", 0
                
                # Verificar que no exista otro cliente con la misma identificación
                if self._existe_identificacion(datos_cliente['identificacion']):
                    return False, "Ya existe un cliente con esta identificación", 0
            
            # Validar email si se proporciona
            if datos_cliente.get('email'):
                if not self.validador.validar_email(datos_cliente['email']):
                    return False, "Formato de email inválido", 0
            
            # Validar teléfono si se proporciona
            if datos_cliente.get('telefono'):
                if not self.validador.validar_telefono(datos_cliente['telefono']):
                    return False, "Formato de teléfono inválido", 0
            
            # Insertar cliente
            query = """
                INSERT INTO clientes (
                    nombre, apellidos, identificacion, tipo_identificacion,
                    telefono, email, direccion, fecha_nacimiento,
                    descuento_porcentaje, limite_credito
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                datos_cliente['nombre'],
                datos_cliente.get('apellidos', ''),
                datos_cliente.get('identificacion', ''),
                datos_cliente.get('tipo_identificacion', 'cedula'),
                datos_cliente.get('telefono', ''),
                datos_cliente.get('email', ''),
                datos_cliente.get('direccion', ''),
                datos_cliente.get('fecha_nacimiento', ''),
                datos_cliente.get('descuento_porcentaje', 0),
                datos_cliente.get('limite_credito', 0)
            )
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                cliente_id = cursor.lastrowid
                conn.commit()
            
            self.logger.info(f"Cliente creado: {datos_cliente['nombre']} (ID: {cliente_id})")
            return True, "Cliente creado exitosamente", cliente_id
            
        except Exception as e:
            error_msg = f"Error creando cliente: {e}"
            self.logger.error(error_msg)
            return False, error_msg, 0
    
    def update_client(self, client_id: int, datos_actualizacion: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Actualizar datos del cliente
        
        Args:
            client_id: ID del cliente
            datos_actualizacion: Datos a actualizar
        """
        try:
            # Verificar que el cliente existe
            if not self._cliente_existe(client_id):
                return False, "Cliente no encontrado"
            
            # Validar datos si se proporcionan
            if 'identificacion' in datos_actualizacion and datos_actualizacion['identificacion']:
                valida, mensaje = self.validador.validar_identificacion(
                    datos_actualizacion['identificacion'],
                    datos_actualizacion.get('tipo_identificacion', 'cedula')
                )
                if not valida:
                    return False, f"Identificación inválida: {mensaje}"
                
                # Verificar que no exista en otro cliente
                if self._existe_identificacion(datos_actualizacion['identificacion'], client_id):
                    return False, "Ya existe otro cliente con esta identificación"
            
            if 'email' in datos_actualizacion and datos_actualizacion['email']:
                if not self.validador.validar_email(datos_actualizacion['email']):
                    return False, "Formato de email inválido"
            
            if 'telefono' in datos_actualizacion and datos_actualizacion['telefono']:
                if not self.validador.validar_telefono(datos_actualizacion['telefono']):
                    return False, "Formato de teléfono inválido"
            
            # Construir query de actualización
            campos_actualizacion = []
            valores = []
            
            campos_permitidos = [
                'nombre', 'apellidos', 'identificacion', 'tipo_identificacion',
                'telefono', 'email', 'direccion', 'fecha_nacimiento',
                'descuento_porcentaje', 'limite_credito', 'activo'
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
            valores.append(client_id)
            
            query = f"""
                UPDATE clientes 
                SET {', '.join(campos_actualizacion)}
                WHERE id = ?
            """
            
            filas_afectadas = ejecutar_consulta_segura(query, tuple(valores))
            
            if filas_afectadas > 0:
                self.logger.info(f"Cliente {client_id} actualizado exitosamente")
                return True, "Cliente actualizado exitosamente"
            else:
                return False, "No se realizaron cambios"
            
        except Exception as e:
            error_msg = f"Error actualizando cliente: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def delete_client(self, client_id: int, eliminar_fisicamente: bool = False) -> Tuple[bool, str]:
        """
        Eliminar cliente por ID
        
        Args:
            client_id: ID del cliente
            eliminar_fisicamente: Si eliminar físicamente o solo desactivar
        """
        try:
            # Verificar que el cliente existe
            if not self._cliente_existe(client_id):
                return False, "Cliente no encontrado"
            
            # Verificar si tiene ventas o apartados activos
            tiene_ventas = self._cliente_tiene_ventas(client_id)
            tiene_apartados = self._cliente_tiene_apartados_activos(client_id)
            
            if (tiene_ventas or tiene_apartados) and eliminar_fisicamente:
                return False, "No se puede eliminar: cliente tiene ventas o apartados registrados"
            
            if eliminar_fisicamente and not (tiene_ventas or tiene_apartados):
                # Eliminación física
                query = "DELETE FROM clientes WHERE id = ?"
                filas_afectadas = ejecutar_consulta_segura(query, (client_id,))
                mensaje = "Cliente eliminado permanentemente"
            else:
                # Eliminación lógica (desactivar)
                query = """
                    UPDATE clientes 
                    SET activo = 0, fecha_modificacion = ?
                    WHERE id = ?
                """
                filas_afectadas = ejecutar_consulta_segura(query, (datetime.now().isoformat(), client_id))
                mensaje = "Cliente desactivado"
            
            if filas_afectadas > 0:
                self.logger.info(f"Cliente {client_id}: {mensaje}")
                return True, mensaje
            else:
                return False, "No se pudo realizar la operación"
                
        except Exception as e:
            error_msg = f"Error eliminando cliente: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_client(self, client_id: int, incluir_estadisticas: bool = False) -> Optional[ClienteDetallado]:
        """
        Obtener información completa de un cliente
        
        Args:
            client_id: ID del cliente
            incluir_estadisticas: Si incluir estadísticas y historial
        """
        try:
            # Obtener datos básicos del cliente
            query = """
                SELECT * FROM clientes WHERE id = ? AND activo = 1
            """
            
            row = ejecutar_consulta_segura(query, (client_id,), fetch='one')
            
            if not row:
                return None
            
            # Convertir a diccionario
            cliente_dict = dict(row)
            
            # Crear cliente detallado
            cliente = ClienteDetallado(
                id=cliente_dict['id'],
                nombre=cliente_dict['nombre'],
                apellidos=cliente_dict['apellidos'] or '',
                identificacion=cliente_dict['identificacion'] or '',
                tipo_identificacion=cliente_dict['tipo_identificacion'],
                telefono=cliente_dict['telefono'] or '',
                email=cliente_dict['email'] or '',
                direccion=cliente_dict['direccion'] or '',
                fecha_nacimiento=cliente_dict['fecha_nacimiento'] or '',
                activo=bool(cliente_dict['activo']),
                descuento_porcentaje=cliente_dict['descuento_porcentaje'],
                limite_credito=cliente_dict['limite_credito'],
                saldo_actual=cliente_dict['saldo_actual'],
                fecha_creacion=cliente_dict['fecha_creacion'],
                fecha_modificacion=cliente_dict['fecha_modificacion']
            )
            
            # Obtener apartados activos
            apartados_info = self._obtener_apartados_activos(client_id)
            cliente.apartados_activos = apartados_info['cantidad']
            cliente.saldo_apartados = apartados_info['saldo_total']
            
            if incluir_estadisticas:
                cliente.estadisticas = self._obtener_estadisticas_cliente(client_id)
                cliente.historial = self._obtener_historial_compras(client_id)
            
            return cliente
            
        except Exception as e:
            self.logger.error(f"Error obteniendo cliente {client_id}: {e}")
            return None
    
    def list_clients(self, filtros: Dict[str, Any] = None, incluir_inactivos: bool = False, 
                    limite: int = 100, offset: int = 0) -> List[Cliente]:
        """
        Listar clientes con filtros opcionales
        
        Args:
            filtros: Diccionario con filtros (nombre, identificacion, email, etc.)
            incluir_inactivos: Si incluir clientes inactivos
            limite: Límite de resultados
            offset: Offset para paginación
        """
        try:
            # Construir query base
            where_conditions = []
            params = []
            
            if not incluir_inactivos:
                where_conditions.append("activo = 1")
            
            # Aplicar filtros
            if filtros:
                if filtros.get('nombre'):
                    where_conditions.append("(nombre LIKE ? OR apellidos LIKE ?)")
                    busqueda = f"%{filtros['nombre']}%"
                    params.extend([busqueda, busqueda])
                
                if filtros.get('identificacion'):
                    where_conditions.append("identificacion LIKE ?")
                    params.append(f"%{filtros['identificacion']}%")
                
                if filtros.get('email'):
                    where_conditions.append("email LIKE ?")
                    params.append(f"%{filtros['email']}%")
                
                if filtros.get('telefono'):
                    where_conditions.append("telefono LIKE ?")
                    params.append(f"%{filtros['telefono']}%")
                
                if filtros.get('tipo_identificacion'):
                    where_conditions.append("tipo_identificacion = ?")
                    params.append(filtros['tipo_identificacion'])
            
            # Construir query completo
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            query = f"""
                SELECT * FROM clientes 
                WHERE {where_clause}
                ORDER BY nombre, apellidos
                LIMIT ? OFFSET ?
            """
            
            params.extend([limite, offset])
            
            rows = ejecutar_consulta_segura(query, tuple(params), fetch='all')
            
            # Convertir a objetos Cliente
            clientes = []
            for row in rows:
                cliente_dict = dict(row)
                cliente = Cliente(
                    id=cliente_dict['id'],
                    nombre=cliente_dict['nombre'],
                    apellidos=cliente_dict['apellidos'] or '',
                    identificacion=cliente_dict['identificacion'] or '',
                    tipo_identificacion=cliente_dict['tipo_identificacion'],
                    telefono=cliente_dict['telefono'] or '',
                    email=cliente_dict['email'] or '',
                    direccion=cliente_dict['direccion'] or '',
                    fecha_nacimiento=cliente_dict['fecha_nacimiento'] or '',
                    activo=bool(cliente_dict['activo']),
                    descuento_porcentaje=cliente_dict['descuento_porcentaje'],
                    limite_credito=cliente_dict['limite_credito'],
                    saldo_actual=cliente_dict['saldo_actual'],
                    fecha_creacion=cliente_dict['fecha_creacion'],
                    fecha_modificacion=cliente_dict['fecha_modificacion']
                )
                clientes.append(cliente)
            
            return clientes
            
        except Exception as e:
            self.logger.error(f"Error listando clientes: {e}")
            return []
    
    def buscar_clientes(self, termino_busqueda: str, limite: int = 20) -> List[Cliente]:
        """
        Búsqueda rápida de clientes por nombre, identificación o teléfono
        
        Args:
            termino_busqueda: Término a buscar
            limite: Límite de resultados
        """
        try:
            query = """
                SELECT * FROM clientes 
                WHERE activo = 1 AND (
                    nombre LIKE ? OR 
                    apellidos LIKE ? OR 
                    identificacion LIKE ? OR 
                    telefono LIKE ? OR
                    email LIKE ?
                )
                ORDER BY 
                    CASE 
                        WHEN nombre LIKE ? THEN 1
                        WHEN identificacion = ? THEN 2
                        ELSE 3
                    END,
                    nombre, apellidos
                LIMIT ?
            """
            
            busqueda = f"%{termino_busqueda}%"
            params = [busqueda] * 5 + [f"{termino_busqueda}%", termino_busqueda, limite]
            
            rows = ejecutar_consulta_segura(query, tuple(params), fetch='all')
            
            clientes = []
            for row in rows:
                cliente_dict = dict(row)
                cliente = Cliente(
                    id=cliente_dict['id'],
                    nombre=cliente_dict['nombre'],
                    apellidos=cliente_dict['apellidos'] or '',
                    identificacion=cliente_dict['identificacion'] or '',
                    tipo_identificacion=cliente_dict['tipo_identificacion'],
                    telefono=cliente_dict['telefono'] or '',
                    email=cliente_dict['email'] or '',
                    direccion=cliente_dict['direccion'] or '',
                    fecha_nacimiento=cliente_dict['fecha_nacimiento'] or '',
                    activo=bool(cliente_dict['activo']),
                    descuento_porcentaje=cliente_dict['descuento_porcentaje'],
                    limite_credito=cliente_dict['limite_credito'],
                    saldo_actual=cliente_dict['saldo_actual'],
                    fecha_creacion=cliente_dict['fecha_creacion'],
                    fecha_modificacion=cliente_dict['fecha_modificacion']
                )
                clientes.append(cliente)
            
            return clientes
            
        except Exception as e:
            self.logger.error(f"Error buscando clientes: {e}")
            return []
    
    def _cliente_existe(self, client_id: int) -> bool:
        """Verifica si un cliente existe"""
        try:
            query = "SELECT COUNT(*) FROM clientes WHERE id = ?"
            result = ejecutar_consulta_segura(query, (client_id,), fetch='one')
            return result[0] > 0
        except:
            return False
    
    def _existe_identificacion(self, identificacion: str, excluir_id: int = None) -> bool:
        """Verifica si existe otro cliente con la misma identificación"""
        try:
            if excluir_id:
                query = "SELECT COUNT(*) FROM clientes WHERE identificacion = ? AND id != ?"
                params = (identificacion, excluir_id)
            else:
                query = "SELECT COUNT(*) FROM clientes WHERE identificacion = ?"
                params = (identificacion,)
            
            result = ejecutar_consulta_segura(query, params, fetch='one')
            return result[0] > 0
        except:
            return False
    
    def _cliente_tiene_ventas(self, client_id: int) -> bool:
        """Verifica si el cliente tiene ventas registradas"""
        try:
            query = "SELECT COUNT(*) FROM ventas WHERE cliente_id = ?"
            result = ejecutar_consulta_segura(query, (client_id,), fetch='one')
            return result[0] > 0
        except:
            return False
    
    def _cliente_tiene_apartados_activos(self, client_id: int) -> bool:
        """Verifica si el cliente tiene apartados activos"""
        try:
            query = "SELECT COUNT(*) FROM apartados WHERE cliente_id = ? AND estado = 'activo'"
            result = ejecutar_consulta_segura(query, (client_id,), fetch='one')
            return result[0] > 0
        except:
            return False
    
    def _obtener_apartados_activos(self, client_id: int) -> Dict[str, Any]:
        """Obtiene información de apartados activos del cliente"""
        try:
            query = """
                SELECT COUNT(*) as cantidad, COALESCE(SUM(saldo), 0) as saldo_total
                FROM apartados 
                WHERE cliente_id = ? AND estado = 'activo'
            """
            
            result = ejecutar_consulta_segura(query, (client_id,), fetch='one')
            
            return {
                'cantidad': result[0] if result else 0,
                'saldo_total': result[1] if result else 0.0
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo apartados activos: {e}")
            return {'cantidad': 0, 'saldo_total': 0.0}
    
    def _obtener_estadisticas_cliente(self, client_id: int) -> EstadisticasCliente:
        """Obtiene estadísticas del cliente"""
        try:
            # Estadísticas básicas de ventas
            query_ventas = """
                SELECT 
                    COUNT(*) as total_compras,
                    COALESCE(SUM(total), 0) as monto_total,
                    COALESCE(AVG(total), 0) as promedio_compra,
                    MAX(fecha_venta) as ultima_compra
                FROM ventas 
                WHERE cliente_id = ? AND estado = 'completada'
            """
            
            result = ejecutar_consulta_segura(query_ventas, (client_id,), fetch='one')
            
            if not result or result[0] == 0:
                return EstadisticasCliente(
                    total_compras=0,
                    monto_total_gastado=0.0,
                    promedio_compra=0.0,
                    ultima_compra='',
                    producto_favorito='',
                    categoria_favorita='',
                    frecuencia_compras_mes=0.0
                )
            
            # Producto más comprado
            query_producto = """
                SELECT p.nombre, SUM(dv.cantidad) as total_cantidad
                FROM detalle_ventas dv
                JOIN ventas v ON dv.venta_id = v.id
                JOIN productos p ON dv.producto_id = p.id
                WHERE v.cliente_id = ? AND v.estado = 'completada'
                GROUP BY p.id, p.nombre
                ORDER BY total_cantidad DESC
                LIMIT 1
            """
            
            producto_result = ejecutar_consulta_segura(query_producto, (client_id,), fetch='one')
            producto_favorito = producto_result[0] if producto_result else ''
            
            # Categoría favorita
            query_categoria = """
                SELECT c.nombre, COUNT(*) as total_productos
                FROM detalle_ventas dv
                JOIN ventas v ON dv.venta_id = v.id
                JOIN productos p ON dv.producto_id = p.id
                JOIN categorias c ON p.categoria_id = c.id
                WHERE v.cliente_id = ? AND v.estado = 'completada'
                GROUP BY c.id, c.nombre
                ORDER BY total_productos DESC
                LIMIT 1
            """
            
            categoria_result = ejecutar_consulta_segura(query_categoria, (client_id,), fetch='one')
            categoria_favorita = categoria_result[0] if categoria_result else ''
            
            # Frecuencia de compras (compras por mes)
            fecha_hace_6_meses = (datetime.now() - timedelta(days=180)).isoformat()
            query_frecuencia = """
                SELECT COUNT(*) as compras_recientes
                FROM ventas 
                WHERE cliente_id = ? AND estado = 'completada' AND fecha_venta >= ?
            """
            
            frecuencia_result = ejecutar_consulta_segura(query_frecuencia, (client_id, fecha_hace_6_meses), fetch='one')
            compras_6_meses = frecuencia_result[0] if frecuencia_result else 0
            frecuencia_mes = compras_6_meses / 6.0
            
            return EstadisticasCliente(
                total_compras=result[0],
                monto_total_gastado=result[1],
                promedio_compra=result[2],
                ultima_compra=result[3] or '',
                producto_favorito=producto_favorito,
                categoria_favorita=categoria_favorita,
                frecuencia_compras_mes=frecuencia_mes
            )
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas cliente: {e}")
            return EstadisticasCliente(
                total_compras=0,
                monto_total_gastado=0.0,
                promedio_compra=0.0,
                ultima_compra='',
                producto_favorito='',
                categoria_favorita='',
                frecuencia_compras_mes=0.0
            )
    
    def _obtener_historial_compras(self, client_id: int, limite: int = 20) -> List[HistorialCompra]:
        """Obtiene historial de compras del cliente"""
        try:
            query = """
                SELECT 
                    v.id,
                    v.fecha_venta,
                    v.total,
                    COUNT(dv.id) as productos,
                    v.metodo_pago,
                    v.estado
                FROM ventas v
                LEFT JOIN detalle_ventas dv ON v.id = dv.venta_id
                WHERE v.cliente_id = ?
                GROUP BY v.id
                ORDER BY v.fecha_venta DESC
                LIMIT ?
            """
            
            rows = ejecutar_consulta_segura(query, (client_id, limite), fetch='all')
            
            historial = []
            for row in rows:
                compra = HistorialCompra(
                    venta_id=row[0],
                    fecha=row[1],
                    total=row[2],
                    productos=row[3],
                    metodo_pago=row[4],
                    estado=row[5]
                )
                historial.append(compra)
            
            return historial
            
        except Exception as e:
            self.logger.error(f"Error obteniendo historial compras: {e}")
            return []

# Instancia global del gestor de clientes
client_manager = ClientManager()

# Funciones de compatibilidad para código existente
def add_client(name: str, contact: str = '') -> bool:
    """Función de compatibilidad simplificada"""
    datos = {'nombre': name, 'telefono': contact}
    exito, _, _ = client_manager.add_client(datos)
    return exito

def update_client(client_id: int, name: str = None, contact: str = None) -> bool:
    """Función de compatibilidad simplificada"""
    datos = {}
    if name:
        datos['nombre'] = name
    if contact:
        datos['telefono'] = contact
    
    if datos:
        exito, _ = client_manager.update_client(client_id, datos)
        return exito
    return False

def delete_client(client_id: int) -> bool:
    """Función de compatibilidad simplificada"""
    exito, _ = client_manager.delete_client(client_id)
    return exito

def get_client(client_id: int) -> Optional[Dict]:
    """Función de compatibilidad simplificada"""
    cliente = client_manager.get_client(client_id)
    if cliente:
        return asdict(cliente)
    return None

def list_clients() -> List[Dict]:
    """Función de compatibilidad simplificada"""
    clientes = client_manager.list_clients()
    return [asdict(cliente) for cliente in clientes]
