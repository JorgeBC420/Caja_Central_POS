"""
Servicio de respaldo de base de datos
Maneja la creación, verificación y gestión de backups automáticos
"""

import os
import shutil
import sqlite3
import json
import gzip
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from core.database import get_db_connection, ejecutar_consulta_segura
from core.config import Config

class DatabaseBackupService:
    """Servicio para manejo de respaldos de base de datos"""
    
    def __init__(self):
        self.config = Config()
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Configuración de respaldos
        self.max_backups = self.config.get_config_value('max_backups', 30)
        self.compression_enabled = self.config.get_config_value('backup_compression', True)
        self.verify_backup = self.config.get_config_value('verify_backup', True)
    
    def crear_backup_completo(self, incluir_auditoria: bool = True) -> Tuple[bool, str]:
        """
        Crea un backup completo de la base de datos
        
        Args:
            incluir_auditoria: Si incluir tablas de auditoría
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje/ruta del archivo)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_completo_{timestamp}"
            
            # Crear directorio temporal para el backup
            temp_dir = self.backup_dir / "temp" / backup_name
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup de la base de datos principal
            db_backup_path = temp_dir / "database.db"
            success, message = self._backup_database(db_backup_path)
            
            if not success:
                self._cleanup_temp_dir(temp_dir.parent)
                return False, f"Error en backup de base de datos: {message}"
            
            # Crear metadata del backup
            metadata = self._crear_metadata_backup(incluir_auditoria)
            metadata_path = temp_dir / "metadata.json"
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
            
            # Backup de archivos de configuración si existen
            self._backup_config_files(temp_dir)
            
            # Comprimir el backup si está habilitado
            if self.compression_enabled:
                final_path = self.backup_dir / f"{backup_name}.tar.gz"
                success = self._comprimir_backup(temp_dir, final_path)
                self._cleanup_temp_dir(temp_dir.parent)
                
                if not success:
                    return False, "Error comprimiendo backup"
            else:
                # Mover directorio completo
                final_path = self.backup_dir / backup_name
                if final_path.exists():
                    shutil.rmtree(final_path)
                shutil.move(str(temp_dir), str(final_path))
                self._cleanup_temp_dir(temp_dir.parent)
            
            # Verificar integridad del backup
            if self.verify_backup:
                if not self._verificar_integridad_backup(final_path):
                    return False, "Backup creado pero falló la verificación de integridad"
            
            # Limpiar backups antiguos
            self._limpiar_backups_antiguos()
            
            # Registrar en auditoría
            self._registrar_backup_auditoria("COMPLETO", str(final_path), True)
            
            self.logger.info(f"Backup completo creado exitosamente: {final_path}")
            return True, str(final_path)
            
        except Exception as e:
            error_msg = f"Error creando backup completo: {str(e)}"
            self.logger.error(error_msg)
            self._registrar_backup_auditoria("COMPLETO", "", False, error_msg)
            return False, error_msg
    
    def crear_backup_incremental(self, fecha_desde: datetime = None) -> Tuple[bool, str]:
        """
        Crea un backup incremental desde una fecha específica
        
        Args:
            fecha_desde: Fecha desde la cual crear el backup incremental
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje/ruta del archivo)  
        """
        try:
            if fecha_desde is None:
                # Usar fecha del último backup
                fecha_desde = self._obtener_fecha_ultimo_backup()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_incremental_{timestamp}"
            
            # Crear directorio temporal
            temp_dir = self.backup_dir / "temp" / backup_name
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Obtener datos modificados desde fecha_desde
            datos_incrementales = self._obtener_datos_incrementales(fecha_desde)
            
            if not datos_incrementales:
                self._cleanup_temp_dir(temp_dir.parent)
                return True, "No hay cambios desde el último backup"
            
            # Guardar datos incrementales
            incremental_path = temp_dir / "incremental.json"
            with open(incremental_path, 'w', encoding='utf-8') as f:
                json.dump(datos_incrementales, f, indent=2, ensure_ascii=False, default=str)
            
            # Crear metadata
            metadata = self._crear_metadata_backup(True, fecha_desde)
            metadata_path = temp_dir / "metadata.json"
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
            
            # Comprimir si está habilitado
            if self.compression_enabled:
                final_path = self.backup_dir / f"{backup_name}.tar.gz"
                success = self._comprimir_backup(temp_dir, final_path)
                self._cleanup_temp_dir(temp_dir.parent)
                
                if not success:
                    return False, "Error comprimiendo backup incremental"
            else:
                final_path = self.backup_dir / backup_name
                if final_path.exists():
                    shutil.rmtree(final_path)
                shutil.move(str(temp_dir), str(final_path))
                self._cleanup_temp_dir(temp_dir.parent)
            
            # Registrar en auditoría
            self._registrar_backup_auditoria("INCREMENTAL", str(final_path), True)
            
            self.logger.info(f"Backup incremental creado: {final_path}")
            return True, str(final_path)
            
        except Exception as e:
            error_msg = f"Error creando backup incremental: {str(e)}"
            self.logger.error(error_msg)
            self._registrar_backup_auditoria("INCREMENTAL", "", False, error_msg)
            return False, error_msg
    
    def programar_backup_automatico(self, frecuencia_horas: int = 24) -> bool:
        """
        Programa backups automáticos
        
        Args:
            frecuencia_horas: Frecuencia en horas para los backups
            
        Returns:
            bool: True si se programó correctamente
        """
        try:
            # Guardar configuración de backup automático
            config_backup = {
                'habilitado': True,
                'frecuencia_horas': frecuencia_horas,
                'proximo_backup': (datetime.now() + timedelta(hours=frecuencia_horas)).isoformat(),
                'tipo': 'INCREMENTAL',  # Por defecto incremental
                'backup_completo_semanal': True  # Backup completo semanal
            }
            
            ejecutar_consulta_segura("""
                INSERT OR REPLACE INTO configuracion_sistema (clave, valor, descripcion, categoria)
                VALUES (?, ?, ?, ?)
            """, ('backup_automatico', json.dumps(config_backup), 
                  'Configuración de backup automático', 'BACKUP'))
            
            self.logger.info(f"Backup automático programado cada {frecuencia_horas} horas")
            return True
            
        except Exception as e:
            self.logger.error(f"Error programando backup automático: {e}")
            return False
    
    def ejecutar_backup_programado(self) -> Tuple[bool, str]:
        """
        Ejecuta backup programado si es necesario
        
        Returns:
            Tuple[bool, str]: (ejecutado, resultado)
        """
        try:
            # Verificar si hay backup programado
            cursor = get_db_connection().cursor()
            cursor.execute("""
                SELECT valor FROM configuracion_sistema 
                WHERE clave = 'backup_automatico'
            """)
            
            result = cursor.fetchone()
            if not result:
                return False, "No hay backup automático configurado"
            
            config = json.loads(result[0])
            
            if not config.get('habilitado', False):
                return False, "Backup automático deshabilitado"
            
            proximo_backup = datetime.fromisoformat(config['proximo_backup'])
            
            if datetime.now() < proximo_backup:
                return False, "Aún no es tiempo para el backup"
            
            # Determinar tipo de backup
            ultimo_completo = self._obtener_fecha_ultimo_backup_completo()
            dias_desde_completo = (datetime.now() - ultimo_completo).days if ultimo_completo else 7
            
            if dias_desde_completo >= 7 or config.get('backup_completo_semanal', True):
                # Backup completo semanal
                success, message = self.crear_backup_completo()
                tipo_backup = "COMPLETO"
            else:
                # Backup incremental
                success, message = self.crear_backup_incremental()
                tipo_backup = "INCREMENTAL"
            
            # Actualizar fecha del próximo backup
            if success:
                config['proximo_backup'] = (datetime.now() + 
                                          timedelta(hours=config['frecuencia_horas'])).isoformat()
                
                ejecutar_consulta_segura("""
                    UPDATE configuracion_sistema 
                    SET valor = ? 
                    WHERE clave = 'backup_automatico'
                """, (json.dumps(config),))
            
            return success, f"Backup {tipo_backup}: {message}"
            
        except Exception as e:
            error_msg = f"Error ejecutando backup programado: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def listar_backups(self) -> List[Dict[str, Any]]:
        """
        Lista todos los backups disponibles
        
        Returns:
            List[Dict]: Lista de backups con su información
        """
        backups = []
        
        try:
            for item in self.backup_dir.iterdir():
                if item.name.startswith('backup_') and item.name != 'temp':
                    info_backup = self._obtener_info_backup(item)
                    if info_backup:
                        backups.append(info_backup)
            
            # Ordenar por fecha descendente
            backups.sort(key=lambda x: x['fecha_creacion'], reverse=True)
            return backups
            
        except Exception as e:
            self.logger.error(f"Error listando backups: {e}")
            return []
    
    def _backup_database(self, backup_path: Path) -> Tuple[bool, str]:
        """Respalda la base de datos principal"""
        try:
            # Obtener conexión a la base de datos fuente
            source_conn = get_db_connection()
            
            # Crear nueva base de datos para el backup
            backup_conn = sqlite3.connect(str(backup_path))
            
            # Copiar esquema y datos
            source_conn.backup(backup_conn)
            
            backup_conn.close()
            
            return True, f"Base de datos respaldada en {backup_path}"
            
        except Exception as e:
            return False, str(e)
    
    def _crear_metadata_backup(self, incluir_auditoria: bool, fecha_desde: datetime = None) -> Dict[str, Any]:
        """Crea metadata del backup"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Información básica
            metadata = {
                'fecha_creacion': datetime.now().isoformat(),
                'version_app': '1.0.0',  # Obtener de configuración
                'incluir_auditoria': incluir_auditoria,
                'tipo_backup': 'INCREMENTAL' if fecha_desde else 'COMPLETO',
                'fecha_desde': fecha_desde.isoformat() if fecha_desde else None,
                'tablas': {}
            }
            
            # Obtener información de tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tablas = cursor.fetchall()
            
            for tabla in tablas:
                nombre_tabla = tabla[0]
                if not incluir_auditoria and 'auditoria' in nombre_tabla.lower():
                    continue
                
                cursor.execute(f"SELECT COUNT(*) FROM {nombre_tabla}")
                count = cursor.fetchone()[0]
                
                metadata['tablas'][nombre_tabla] = {
                    'registros': count,
                    'incluida': True
                }
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error creando metadata: {e}")
            return {'error': str(e)}
    
    def _backup_config_files(self, temp_dir: Path):
        """Respalda archivos de configuración"""
        try:
            config_files = ['config.json', 'settings.ini', 'printer_config.json']
            config_dir = temp_dir / "config"
            
            for config_file in config_files:
                if os.path.exists(config_file):
                    config_dir.mkdir(exist_ok=True)
                    shutil.copy2(config_file, config_dir / config_file)
                    
        except Exception as e:
            self.logger.warning(f"No se pudieron respaldar archivos de configuración: {e}")
    
    def _comprimir_backup(self, source_dir: Path, output_path: Path) -> bool:
        """Comprime el backup usando gzip"""
        try:
            import tarfile
            
            with tarfile.open(output_path, "w:gz") as tar:
                tar.add(source_dir, arcname=source_dir.name)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error comprimiendo backup: {e}")
            return False
    
    def _verificar_integridad_backup(self, backup_path: Path) -> bool:
        """Verifica la integridad del backup"""
        try:
            if backup_path.suffix == '.gz':
                # Verificar archivo comprimido
                import tarfile
                with tarfile.open(backup_path, "r:gz") as tar:
                    # Intentar leer todos los archivos
                    for member in tar.getmembers():
                        if member.isfile():
                            tar.extractfile(member).read(1024)  # Leer una muestra
                return True
            else:
                # Verificar directorio
                db_file = backup_path / "database.db"
                if db_file.exists():
                    # Verificar que la base de datos se puede abrir
                    conn = sqlite3.connect(str(db_file))
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master")
                    conn.close()
                return True
                
        except Exception as e:
            self.logger.error(f"Error verificando integridad: {e}")
            return False
    
    def _obtener_datos_incrementales(self, fecha_desde: datetime) -> Dict[str, Any]:
        """Obtiene datos modificados desde una fecha"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            datos = {'tablas': {}}
            fecha_str = fecha_desde.strftime('%Y-%m-%d %H:%M:%S')
            
            # Tablas con campos de fecha de modificación
            tablas_con_fecha = {
                'productos': 'fecha_modificacion',
                'clientes': 'fecha_modificacion', 
                'ventas': 'fecha_venta',
                'detalle_ventas': 'fecha_creacion',
                'movimientos_inventario': 'fecha_movimiento',
                'configuracion_sistema': 'fecha_modificacion'
            }
            
            for tabla, campo_fecha in tablas_con_fecha.items():
                try:
                    cursor.execute(f"""
                        SELECT * FROM {tabla} 
                        WHERE {campo_fecha} >= ?
                    """, (fecha_str,))
                    
                    registros = cursor.fetchall()
                    if registros:
                        # Obtener nombres de columnas
                        cursor.execute(f"PRAGMA table_info({tabla})")
                        columnas = [col[1] for col in cursor.fetchall()]
                        
                        # Convertir a diccionarios
                        datos['tablas'][tabla] = [
                            dict(zip(columnas, registro)) for registro in registros
                        ]
                        
                except sqlite3.Error as e:
                    self.logger.warning(f"No se pudo obtener data incremental de {tabla}: {e}")
                    continue
            
            return datos
            
        except Exception as e:
            self.logger.error(f"Error obteniendo datos incrementales: {e}")
            return {}
    
    def _obtener_fecha_ultimo_backup(self) -> datetime:
        """Obtiene la fecha del último backup"""
        try:
            backups = self.listar_backups()
            if backups:
                return datetime.fromisoformat(backups[0]['fecha_creacion'])
            else:
                return datetime.now() - timedelta(days=1)  # Ayer por defecto
                
        except Exception:
            return datetime.now() - timedelta(days=1)
    
    def _obtener_fecha_ultimo_backup_completo(self) -> Optional[datetime]:
        """Obtiene la fecha del último backup completo"""
        try:
            backups = self.listar_backups()
            for backup in backups:
                if backup.get('tipo') == 'COMPLETO':
                    return datetime.fromisoformat(backup['fecha_creacion'])
            return None
            
        except Exception:
            return None
    
    def _obtener_info_backup(self, backup_path: Path) -> Optional[Dict[str, Any]]:
        """Obtiene información de un backup"""
        try:
            info = {
                'nombre': backup_path.name,
                'ruta': str(backup_path),
                'tamaño': 0
            }
            
            if backup_path.is_file():
                # Archivo comprimido
                info['tamaño'] = backup_path.stat().st_size
                info['comprimido'] = True
                
                # Intentar leer metadata del archivo comprimido
                import tarfile
                with tarfile.open(backup_path, "r:gz") as tar:
                    try:
                        metadata_member = tar.getmember(f"{backup_path.stem}/metadata.json")
                        metadata_file = tar.extractfile(metadata_member)
                        metadata = json.loads(metadata_file.read().decode())
                        info.update(metadata)
                    except:
                        pass
            else:
                # Directorio
                info['tamaño'] = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
                info['comprimido'] = False
                
                # Leer metadata si existe
                metadata_path = backup_path / "metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        info.update(metadata)
            
            # Extraer fecha del nombre si no está en metadata
            if 'fecha_creacion' not in info:
                try:
                    # Formato: backup_tipo_YYYYMMDD_HHMMSS
                    parts = backup_path.stem.split('_')
                    if len(parts) >= 3:
                        fecha_str = f"{parts[-2]}_{parts[-1]}"  
                        info['fecha_creacion'] = datetime.strptime(fecha_str, "%Y%m%d_%H%M%S").isoformat()
                except:
                    info['fecha_creacion'] = datetime.fromtimestamp(backup_path.stat().st_mtime).isoformat()
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error obteniendo info de backup {backup_path}: {e}")
            return None
    
    def _limpiar_backups_antiguos(self):
        """Limpia backups antiguos según configuración"""
        try:
            backups = self.listar_backups()
            
            if len(backups) > self.max_backups:
                # Eliminar los más antiguos
                backups_a_eliminar = backups[self.max_backups:]
                
                for backup in backups_a_eliminar:
                    backup_path = Path(backup['ruta'])
                    if backup_path.exists():
                        if backup_path.is_file():
                            backup_path.unlink()
                        else:
                            shutil.rmtree(backup_path)
                        
                        self.logger.info(f"Backup antiguo eliminado: {backup['nombre']}")
                        
        except Exception as e:
            self.logger.error(f"Error limpiando backups antiguos: {e}")
    
    def _registrar_backup_auditoria(self, tipo: str, ruta: str, exitoso: bool, error: str = None):
        """Registra operación de backup en auditoría"""
        try:
            ejecutar_consulta_segura("""
                INSERT INTO auditoria_sistema (
                    operacion, tabla_afectada, detalles, usuario, fecha_operacion, exitoso
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                f'BACKUP_{tipo}',
                'SISTEMA',
                json.dumps({
                    'ruta_backup': ruta,
                    'error': error
                }, default=str),
                'SISTEMA',
                datetime.now(),
                exitoso
            ))
            
        except Exception as e:
            self.logger.error(f"Error registrando backup en auditoría: {e}")
    
    def _cleanup_temp_dir(self, temp_parent: Path):
        """Limpia directorio temporal"""
        try:
            if temp_parent.exists() and temp_parent.name == "temp":
                shutil.rmtree(temp_parent)
        except Exception as e:
            self.logger.warning(f"No se pudo limpiar directorio temporal: {e}")

# Función de conveniencia para uso directo
def crear_backup_completo() -> Tuple[bool, str]:
    """Función de conveniencia para crear backup completo"""
    service = DatabaseBackupService()
    return service.crear_backup_completo()

def crear_backup_incremental(fecha_desde: datetime = None) -> Tuple[bool, str]:
    """Función de conveniencia para crear backup incremental"""
    service = DatabaseBackupService()
    return service.crear_backup_incremental(fecha_desde)

def listar_backups_disponibles() -> List[Dict[str, Any]]:
    """Función de conveniencia para listar backups"""
    service = DatabaseBackupService()
    return service.listar_backups()
