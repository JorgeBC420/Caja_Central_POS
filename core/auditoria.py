import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from core.database import get_db_cursor, ejecutar_consulta_segura

class AuditoriaManager:
    """Gestor de auditoría para el sistema POS"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def registrar_accion(self, usuario_id: int, accion: str, tabla: str = None, 
                        registro_id: int = None, detalles: Dict = None, 
                        ip_address: str = None) -> bool:
        """
        Registra una acción en el sistema de auditoría
        
        Args:
            usuario_id: ID del usuario que realizó la acción
            accion: Descripción de la acción realizada
            tabla: Tabla afectada (opcional)
            registro_id: ID del registro afectado (opcional)
            detalles: Detalles adicionales de la acción
            ip_address: Dirección IP del usuario (opcional)
        """
        try:
            detalles_json = json.dumps(detalles, default=str) if detalles else None
            
            query = """
                INSERT INTO auditoria (
                    usuario_id, accion, tabla, registro_id, detalles, 
                    fecha, ip_address
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                usuario_id,
                accion,
                tabla,
                registro_id,
                detalles_json,
                datetime.now().isoformat(),
                ip_address
            )
            
            success, message = ejecutar_consulta_segura(query, params)
            
            if not success:
                self.logger.error(f"Error al registrar auditoría: {message}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error en registrar_accion: {e}")
            return False
    
    def registrar_login(self, usuario_id: int, exito: bool, ip_address: str = None) -> bool:
        """Registra un intento de login"""
        accion = "LOGIN_EXITOSO" if exito else "LOGIN_FALLIDO"
        detalles = {
            "tipo_evento": "autenticacion",
            "exito": exito,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.registrar_accion(
            usuario_id=usuario_id,
            accion=accion,
            tabla="usuarios",
            registro_id=usuario_id,
            detalles=detalles,
            ip_address=ip_address
        )
    
    def registrar_logout(self, usuario_id: int, duracion_sesion: int = None) -> bool:
        """Registra el cierre de sesión"""
        detalles = {
            "tipo_evento": "autenticacion",
            "duracion_sesion_minutos": duracion_sesion,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.registrar_accion(
            usuario_id=usuario_id,
            accion="LOGOUT",
            tabla="usuarios",
            registro_id=usuario_id,
            detalles=detalles
        )
    
    def registrar_venta(self, usuario_id: int, venta_id: int, monto_total: float, 
                       items_count: int, metodo_pago: str) -> bool:
        """Registra una venta completada"""
        detalles = {
            "tipo_evento": "venta",
            "monto_total": monto_total,
            "cantidad_items": items_count,
            "metodo_pago": metodo_pago,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.registrar_accion(
            usuario_id=usuario_id,
            accion="VENTA_COMPLETADA",
            tabla="ventas",
            registro_id=venta_id,
            detalles=detalles
        )
    
    def registrar_devolucion(self, usuario_id: int, venta_id: int, monto_devuelto: float, 
                           motivo: str) -> bool:
        """Registra una devolución"""
        detalles = {
            "tipo_evento": "devolucion",
            "venta_original_id": venta_id,
            "monto_devuelto": monto_devuelto,
            "motivo": motivo,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.registrar_accion(
            usuario_id=usuario_id,
            accion="DEVOLUCION_REGISTRADA",
            tabla="devoluciones",
            detalles=detalles
        )
    
    def registrar_cambio_inventario(self, usuario_id: int, producto_id: int, 
                                  tipo_cambio: str, cantidad: int, motivo: str) -> bool:
        """Registra cambios en el inventario"""
        detalles = {
            "tipo_evento": "inventario",
            "tipo_cambio": tipo_cambio,  # "entrada", "salida", "ajuste"
            "cantidad": cantidad,
            "motivo": motivo,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.registrar_accion(
            usuario_id=usuario_id,
            accion=f"INVENTARIO_{tipo_cambio.upper()}",
            tabla="productos",
            registro_id=producto_id,
            detalles=detalles
        )
    
    def registrar_cambio_precio(self, usuario_id: int, producto_id: int, 
                              precio_anterior: float, precio_nuevo: float) -> bool:
        """Registra cambios de precio"""
        detalles = {
            "tipo_evento": "precio",
            "precio_anterior": precio_anterior,
            "precio_nuevo": precio_nuevo,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.registrar_accion(
            usuario_id=usuario_id,
            accion="PRECIO_MODIFICADO",
            tabla="productos",
            registro_id=producto_id,
            detalles=detalles
        )
    
    def registrar_configuracion(self, usuario_id: int, clave: str, 
                              valor_anterior: str, valor_nuevo: str) -> bool:
        """Registra cambios en la configuración"""
        detalles = {
            "tipo_evento": "configuracion",
            "clave": clave,
            "valor_anterior": valor_anterior,
            "valor_nuevo": valor_nuevo,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.registrar_accion(
            usuario_id=usuario_id,
            accion="CONFIGURACION_MODIFICADA",
            tabla="configuraciones",
            detalles=detalles
        )
    
    def obtener_logs_usuario(self, usuario_id: int, fecha_inicio: str = None, 
                           fecha_fin: str = None, limite: int = 100) -> List[Dict]:
        """Obtiene los logs de un usuario específico"""
        query = """
            SELECT a.*, u.nombre as nombre_usuario 
            FROM auditoria a 
            LEFT JOIN usuarios u ON a.usuario_id = u.id 
            WHERE a.usuario_id = ?
        """
        params = [usuario_id]
        
        if fecha_inicio:
            query += " AND a.fecha >= ?"
            params.append(fecha_inicio)
        
        if fecha_fin:
            query += " AND a.fecha <= ?"
            params.append(fecha_fin)
        
        query += " ORDER BY a.fecha DESC LIMIT ?"
        params.append(limite)
        
        try:
            with get_db_cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                logs = []
                for row in rows:
                    log_dict = dict(row) if hasattr(row, 'keys') else {
                        'id': row[0], 'usuario_id': row[1], 'accion': row[2],
                        'tabla': row[3], 'registro_id': row[4], 'detalles': row[5],
                        'fecha': row[6], 'ip_address': row[7] if len(row) > 7 else None,
                        'nombre_usuario': row[8] if len(row) > 8 else None
                    }
                    
                    # Parsear detalles JSON
                    if log_dict.get('detalles'):
                        try:
                            log_dict['detalles'] = json.loads(log_dict['detalles'])
                        except:
                            pass
                    
                    logs.append(log_dict)
                
                return logs
                
        except Exception as e:
            self.logger.error(f"Error al obtener logs de usuario: {e}")
            return []
    
    def obtener_logs_tabla(self, tabla: str, registro_id: int = None, 
                          limite: int = 50) -> List[Dict]:
        """Obtiene los logs de una tabla específica"""
        query = """
            SELECT a.*, u.nombre as nombre_usuario 
            FROM auditoria a 
            LEFT JOIN usuarios u ON a.usuario_id = u.id 
            WHERE a.tabla = ?
        """
        params = [tabla]
        
        if registro_id:
            query += " AND a.registro_id = ?"
            params.append(registro_id)
        
        query += " ORDER BY a.fecha DESC LIMIT ?"
        params.append(limite)
        
        try:
            with get_db_cursor() as cursor:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error al obtener logs de tabla: {e}")
            return []
    
    def obtener_estadisticas_auditoria(self, fecha_inicio: str = None, 
                                     fecha_fin: str = None) -> Dict:
        """Obtiene estadísticas de auditoría"""
        try:
            with get_db_cursor() as cursor:
                # Contar acciones por tipo
                query_acciones = """
                    SELECT accion, COUNT(*) as cantidad 
                    FROM auditoria 
                    WHERE 1=1
                """
                params = []
                
                if fecha_inicio:
                    query_acciones += " AND fecha >= ?"
                    params.append(fecha_inicio)
                
                if fecha_fin:
                    query_acciones += " AND fecha <= ?"
                    params.append(fecha_fin)
                
                query_acciones += " GROUP BY accion ORDER BY cantidad DESC"
                
                cursor.execute(query_acciones, params)
                acciones_por_tipo = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Contar acciones por usuario
                query_usuarios = """
                    SELECT u.nombre, COUNT(*) as cantidad 
                    FROM auditoria a 
                    LEFT JOIN usuarios u ON a.usuario_id = u.id 
                    WHERE 1=1
                """
                
                if fecha_inicio:
                    query_usuarios += " AND a.fecha >= ?"
                
                if fecha_fin:
                    query_usuarios += " AND a.fecha <= ?"
                
                query_usuarios += " GROUP BY u.nombre ORDER BY cantidad DESC LIMIT 10"
                
                cursor.execute(query_usuarios, params)
                acciones_por_usuario = {row[0] or 'Usuario desconocido': row[1] 
                                      for row in cursor.fetchall()}
                
                return {
                    'acciones_por_tipo': acciones_por_tipo,
                    'acciones_por_usuario': acciones_por_usuario,
                    'total_eventos': sum(acciones_por_tipo.values())
                }
                
        except Exception as e:
            self.logger.error(f"Error al obtener estadísticas: {e}")
            return {'error': str(e)}
    
    def limpiar_logs_antiguos(self, dias_antiguedad: int = 90) -> int:
        """Limpia logs más antiguos que X días"""
        try:
            query = """
                DELETE FROM auditoria 
                WHERE fecha < datetime('now', '-{} days')
            """.format(dias_antiguedad)
            
            success, message = ejecutar_consulta_segura(query, [])
            
            if success:
                # Contar cuántos se eliminaron (aproximado)
                with get_db_cursor() as cursor:
                    cursor.execute("SELECT changes()")
                    eliminados = cursor.fetchone()[0]
                    self.logger.info(f"Eliminados {eliminados} registros de auditoría antiguos")
                    return eliminados
            else:
                self.logger.error(f"Error al limpiar logs: {message}")
                return 0
                
        except Exception as e:
            self.logger.error(f"Error en limpiar_logs_antiguos: {e}")
            return 0

# Instancia global del manager de auditoría
auditoria_manager = AuditoriaManager()
