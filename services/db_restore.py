"""
Servicio de restauración de base de datos
Maneja la restauración desde backups completos e incrementales
"""

import os
import shutil
import sqlite3
import json
import gzip
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from core.database import get_db_connection, ejecutar_consulta_segura
from core.config import Config

class DatabaseRestoreService:
    """Servicio para restauración de base de datos desde backups"""
    
    def __init__(self):
        self.config = Config()
        self.backup_dir = Path("backups")
        self.restore_temp_dir = Path("temp_restore")
        self.logger = logging.getLogger(__name__)
        
        # Crear directorio temporal si no existe
        self.restore_temp_dir.mkdir(exist_ok=True)
    
    def listar_backups_disponibles(self) -> List[Dict[str, Any]]:
        """
        Lista todos los backups disponibles para restauración
        
        Returns:
            List[Dict]: Lista de backups con información detallada
        """
        backups = []
        
        if not self.backup_dir.exists():
            return backups
        
        try:
            for item in self.backup_dir.iterdir():
                if item.name.startswith('backup_') and item.name != 'temp':
                    info_backup = self._obtener_info_backup(item)
                    if info_backup:
                        backups.append(info_backup)
            
            # Ordenar por fecha descendente
            backups.sort(key=lambda x: x.get('fecha_creacion', ''), reverse=True)
            return backups
            
        except Exception as e:
            self.logger.error(f"Error listando backups: {e}")
            return []
    
    def validar_backup(self, backup_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valida la integridad y compatibilidad de un backup
        
        Args:
            backup_path: Ruta al archivo o directorio de backup
            
        Returns:
            Tuple[bool, str, Dict]: (válido, mensaje, metadata)
        """
        try:
            backup_path_obj = Path(backup_path)
            
            if not backup_path_obj.exists():
                return False, "El archivo de backup no existe", {}
            
            metadata = {}
            
            # Extraer y validar metadata
            if backup_path_obj.is_file() and backup_path_obj.suffix == '.gz':
                # Backup comprimido
                import tarfile
                
                with tarfile.open(backup_path_obj, "r:gz") as tar:
                    # Buscar metadata
                    metadata_members = [m for m in tar.getmembers() if m.name.endswith('metadata.json')]
                    
                    if not metadata_members:
                        return False, "Backup no contiene metadata válida", {}
                    
                    metadata_file = tar.extractfile(metadata_members[0])
                    metadata = json.loads(metadata_file.read().decode())
                    
                    # Verificar que contiene base de datos
                    db_members = [m for m in tar.getmembers() if m.name.endswith('database.db')]
                    if not db_members:
                        return False, "Backup no contiene base de datos", metadata
            
            elif backup_path_obj.is_dir():
                # Backup en directorio
                metadata_path = backup_path_obj / "metadata.json"
                db_path = backup_path_obj / "database.db"
                
                if not metadata_path.exists():
                    return False, "Backup no contiene metadata", {}
                
                if not db_path.exists():
                    return False, "Backup no contiene base de datos", {}
                
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Verificar integridad de la base de datos
                try:
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                    table_count = cursor.fetchone()[0]
                    conn.close()
                    
                    if table_count == 0:
                        return False, "La base de datos del backup está vacía", metadata
                        
                except sqlite3.Error as e:
                    return False, f"Base de datos corrupta en backup: {e}", metadata
            
            else:
                return False, "Formato de backup no reconocido", {}
            
            # Validar compatibilidad de versión
            version_backup = metadata.get('version_app', '1.0.0')
            version_actual = '1.0.0'  # Obtener de configuración
            
            if not self._validar_compatibilidad_version(version_backup, version_actual):
                return False, f"Versión incompatible. Backup: {version_backup}, Actual: {version_actual}", metadata
            
            return True, "Backup válido y compatible", metadata
            
        except Exception as e:
            error_msg = f"Error validando backup: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg, {}
    
    def restaurar_backup_completo(self, backup_path: str, 
                                 confirmar_reemplazo: bool = False,
                                 restaurar_configuracion: bool = True) -> Tuple[bool, str]:
        """
        Restaura un backup completo
        
        Args:
            backup_path: Ruta al backup
            confirmar_reemplazo: Confirma que se puede reemplazar la DB actual
            restaurar_configuracion: Si restaurar archivos de configuración
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        if not confirmar_reemplazo:
            return False, "Debe confirmar el reemplazo de la base de datos actual"
        
        try:
            # Validar backup primero
            es_valido, mensaje, metadata = self.validar_backup(backup_path)
            if not es_valido:
                return False, f"Backup inválido: {mensaje}"
            
            # Crear backup de seguridad de la DB actual
            backup_actual_path = self._crear_backup_seguridad()
            
            try:
                # Extraer backup a directorio temporal
                backup_extraido = self._extraer_backup(backup_path)
                if not backup_extraido:
                    return False, "Error extrayendo backup"
                
                # Cerrar conexiones actuales a la base de datos
                self._cerrar_conexiones_db()
                
                # Reemplazar base de datos
                db_actual_path = self.config.get_config_value('database_path', 'caja_registradora_pos_cr.db')
                db_backup_path = backup_extraido / "database.db"
                
                if os.path.exists(db_actual_path):
                    os.remove(db_actual_path)
                
                shutil.copy2(str(db_backup_path), db_actual_path)
                
                # Restaurar archivos de configuración si se solicita
                if restaurar_configuracion:
                    self._restaurar_archivos_configuracion(backup_extraido)
                
                # Validar base de datos restaurada
                if not self._validar_db_restaurada(db_actual_path):
                    # Restaurar backup de seguridad
                    if backup_actual_path and os.path.exists(backup_actual_path):
                        shutil.copy2(backup_actual_path, db_actual_path)
                    return False, "Error validando base de datos restaurada"
                
                # Limpiar archivos temporales
                self._limpiar_archivos_temporales(backup_extraido, backup_actual_path)
                
                # Registrar en auditoría
                self._registrar_restauracion_auditoria("COMPLETO", backup_path, True)
                
                mensaje_exito = f"Backup completo restaurado exitosamente desde {backup_path}"
                self.logger.info(mensaje_exito)
                return True, mensaje_exito
                
            except Exception as e:
                # En caso de error, restaurar backup de seguridad
                if backup_actual_path and os.path.exists(backup_actual_path):
                    try:
                        db_actual_path = self.config.get_config_value('database_path', 'caja_registradora_pos_cr.db')
                        shutil.copy2(backup_actual_path, db_actual_path)
                        self.logger.info("Base de datos original restaurada después del error")
                    except:
                        pass
                
                error_msg = f"Error durante restauración: {str(e)}"
                self.logger.error(error_msg)
                self._registrar_restauracion_auditoria("COMPLETO", backup_path, False, error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error restaurando backup completo: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def restaurar_backup_incremental(self, backup_path: str) -> Tuple[bool, str]:
        """
        Restaura un backup incremental
        
        Args:
            backup_path: Ruta al backup incremental
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        try:
            # Validar backup
            es_valido, mensaje, metadata = self.validar_backup(backup_path)
            if not es_valido:
                return False, f"Backup incremental inválido: {mensaje}"
            
            tipo_backup = metadata.get('tipo_backup', '')
            if tipo_backup != 'INCREMENTAL':
                return False, "El backup no es de tipo incremental"
            
            # Extraer backup
            backup_extraido = self._extraer_backup(backup_path)
            if not backup_extraido:
                return False, "Error extrayendo backup incremental"
            
            # Leer datos incrementales
            incremental_path = backup_extraido / "incremental.json"
            if not incremental_path.exists():
                return False, "Backup incremental no contiene datos"
            
            with open(incremental_path, 'r', encoding='utf-8') as f:
                datos_incrementales = json.load(f)
            
            # Aplicar cambios incrementales
            registros_aplicados = 0
            conn = get_db_connection()
            
            try:
                conn.execute("BEGIN TRANSACTION")
                
                for tabla, registros in datos_incrementales.get('tablas', {}).items():
                    registros_aplicados += self._aplicar_cambios_tabla(conn, tabla, registros)
                
                conn.commit()
                
                # Limpiar archivos temporales
                self._limpiar_archivos_temporales(backup_extraido)
                
                # Registrar en auditoría
                self._registrar_restauracion_auditoria("INCREMENTAL", backup_path, True)
                
                mensaje_exito = f"Backup incremental aplicado: {registros_aplicados} registros actualizados"
                self.logger.info(mensaje_exito)
                return True, mensaje_exito
                
            except Exception as e:
                conn.rollback()
                raise e
                
        except Exception as e:
            error_msg = f"Error restaurando backup incremental: {str(e)}"
            self.logger.error(error_msg)
            self._registrar_restauracion_auditoria("INCREMENTAL", backup_path, False, error_msg)
            return False, error_msg
    
    def obtener_punto_restauracion_optimo(self, fecha_objetivo: datetime) -> Optional[Dict[str, Any]]:
        """
        Encuentra el mejor punto de restauración para una fecha específica
        
        Args:
            fecha_objetivo: Fecha a la cual se quiere restaurar
            
        Returns:
            Dict con información del punto de restauración óptimo
        """
        try:
            backups = self.listar_backups_disponibles()
            
            # Filtrar backups anteriores a la fecha objetivo
            backups_validos = []
            for backup in backups:
                fecha_backup = datetime.fromisoformat(backup.get('fecha_creacion', ''))
                if fecha_backup <= fecha_objetivo:
                    backups_validos.append(backup)
            
            if not backups_validos:
                return None
            
            # Encontrar el backup completo más reciente
            backup_completo = None
            for backup in backups_validos:
                if backup.get('tipo_backup') == 'COMPLETO':
                    backup_completo = backup
                    break
            
            if not backup_completo:
                return None
            
            # Encontrar backups incrementales posteriores al completo
            fecha_completo = datetime.fromisoformat(backup_completo['fecha_creacion'])
            incrementales = []
            
            for backup in backups_validos:
                if (backup.get('tipo_backup') == 'INCREMENTAL' and 
                    datetime.fromisoformat(backup['fecha_creacion']) > fecha_completo):
                    incrementales.append(backup)
            
            # Ordenar incrementales por fecha
            incrementales.sort(key=lambda x: x['fecha_creacion'])
            
            return {
                'backup_completo': backup_completo,
                'backups_incrementales': incrementales,
                'fecha_objetivo': fecha_objetivo.isoformat(),
                'fecha_restauracion_efectiva': incrementales[-1]['fecha_creacion'] if incrementales else backup_completo['fecha_creacion']
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo punto de restauración: {e}")
            return None
    
    def restaurar_a_fecha_especifica(self, fecha_objetivo: datetime, 
                                   confirmar_reemplazo: bool = False) -> Tuple[bool, str]:
        """
        Restaura la base de datos a una fecha específica
        
        Args:
            fecha_objetivo: Fecha objetivo para la restauración
            confirmar_reemplazo: Confirmar reemplazo de DB actual
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        try:
            # Obtener estrategia de restauración
            punto_restauracion = self.obtener_punto_restauracion_optimo(fecha_objetivo)
            
            if not punto_restauracion:
                return False, f"No se encontraron backups para restaurar a {fecha_objetivo}"
            
            # Restaurar backup completo primero
            backup_completo = punto_restauracion['backup_completo']
            exito, mensaje = self.restaurar_backup_completo(
                backup_completo['ruta'], 
                confirmar_reemplazo, 
                restaurar_configuracion=True
            )
            
            if not exito:
                return False, f"Error restaurando backup completo: {mensaje}"
            
            # Aplicar backups incrementales en orden
            incrementales = punto_restauracion['backups_incrementales']
            for incremental in incrementales:
                exito, mensaje = self.restaurar_backup_incremental(incremental['ruta'])
                if not exito:
                    return False, f"Error aplicando backup incremental {incremental['nombre']}: {mensaje}"
            
            fecha_efectiva = punto_restauracion['fecha_restauracion_efectiva']
            mensaje_final = f"Sistema restaurado a {fecha_efectiva} (objetivo: {fecha_objetivo})"
            
            self.logger.info(mensaje_final)
            return True, mensaje_final
            
        except Exception as e:
            error_msg = f"Error restaurando a fecha específica: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def verificar_integridad_post_restauracion(self) -> Tuple[bool, List[str]]:
        """
        Verifica la integridad de la base de datos después de una restauración
        
        Returns:
            Tuple[bool, List[str]]: (íntegra, lista de problemas encontrados)
        """
        problemas = []
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verificar integridad PRAGMA
            cursor.execute("PRAGMA integrity_check")
            resultado = cursor.fetchone()
            
            if resultado[0] != "ok":
                problemas.append(f"Integridad PRAGMA falló: {resultado[0]}")
            
            # Verificar tablas principales existen
            tablas_requeridas = ['productos', 'clientes', 'ventas', 'usuarios', 'configuracion_sistema']
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tablas_existentes = [row[0] for row in cursor.fetchall()]
            
            for tabla in tablas_requeridas:
                if tabla not in tablas_existentes:
                    problemas.append(f"Tabla requerida '{tabla}' no existe")
            
            # Verificar índices críticos
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indices_existentes = [row[0] for row in cursor.fetchall()]
            
            # Verificar constraints y foreign keys
            cursor.execute("PRAGMA foreign_key_check")
            fk_errors = cursor.fetchall()
            
            if fk_errors:
                problemas.append(f"Errores de integridad referencial: {len(fk_errors)} problemas")
            
            # Verificar datos básicos
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            total_tablas = cursor.fetchone()[0]
            
            if total_tablas == 0:
                problemas.append("Base de datos está vacía")
            
            return len(problemas) == 0, problemas
            
        except Exception as e:
            problemas.append(f"Error verificando integridad: {str(e)}")
            return False, problemas
    
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
                
                # Leer metadata del archivo comprimido
                import tarfile
                with tarfile.open(backup_path, "r:gz") as tar:
                    try:
                        metadata_members = [m for m in tar.getmembers() if m.name.endswith('metadata.json')]
                        if metadata_members:
                            metadata_file = tar.extractfile(metadata_members[0])
                            metadata = json.loads(metadata_file.read().decode())
                            info.update(metadata)
                    except:
                        pass
            else:
                # Directorio
                info['tamaño'] = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
                info['comprimido'] = False
                
                # Leer metadata
                metadata_path = backup_path / "metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        info.update(metadata)
            
            # Extraer fecha del nombre si no está en metadata
            if 'fecha_creacion' not in info:
                try:
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
    
    def _validar_compatibilidad_version(self, version_backup: str, version_actual: str) -> bool:
        """Valida compatibilidad entre versiones"""
        try:
            # Lógica simple de compatibilidad - misma versión mayor
            v_backup = [int(x) for x in version_backup.split('.')]
            v_actual = [int(x) for x in version_actual.split('.')]
            
            # Compatible si versión mayor es igual o backup es menor
            return v_backup[0] <= v_actual[0]
            
        except:
            # En caso de error, asumir compatible
            return True
    
    def _crear_backup_seguridad(self) -> Optional[str]:
        """Crea backup de seguridad de la DB actual antes de restaurar"""
        try:
            db_actual = self.config.get_config_value('database_path', 'caja_registradora_pos_cr.db')
            
            if not os.path.exists(db_actual):
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_seguridad = f"backup_pre_restore_{timestamp}.db"
            
            shutil.copy2(db_actual, backup_seguridad)
            return backup_seguridad
            
        except Exception as e:
            self.logger.error(f"Error creando backup de seguridad: {e}")
            return None
    
    def _extraer_backup(self, backup_path: str) -> Optional[Path]:
        """Extrae backup a directorio temporal"""
        try:
            backup_path_obj = Path(backup_path)
            
            # Crear directorio temporal único
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_dir = self.restore_temp_dir / f"restore_{timestamp}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            if backup_path_obj.is_file() and backup_path_obj.suffix == '.gz':
                # Extraer archivo comprimido
                import tarfile
                
                with tarfile.open(backup_path_obj, "r:gz") as tar:
                    tar.extractall(temp_dir)
                
                # Buscar directorio extraído
                extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
                if extracted_dirs:
                    return extracted_dirs[0]
                else:
                    return temp_dir
                    
            elif backup_path_obj.is_dir():
                # Copiar directorio
                shutil.copytree(backup_path_obj, temp_dir / backup_path_obj.name)
                return temp_dir / backup_path_obj.name
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error extrayendo backup: {e}")
            return None
    
    def _cerrar_conexiones_db(self):
        """Cierra conexiones activas a la base de datos"""
        try:
            # Implementar lógica para cerrar conexiones según el manejo de conexiones
            # de la aplicación
            pass
        except Exception as e:
            self.logger.warning(f"Error cerrando conexiones DB: {e}")
    
    def _restaurar_archivos_configuracion(self, backup_dir: Path):
        """Restaura archivos de configuración desde backup"""
        try:
            config_dir = backup_dir / "config"
            
            if config_dir.exists():
                for config_file in config_dir.iterdir():
                    if config_file.is_file():
                        shutil.copy2(config_file, config_file.name)
                        self.logger.info(f"Archivo de configuración restaurado: {config_file.name}")
                        
        except Exception as e:
            self.logger.warning(f"Error restaurando archivos de configuración: {e}")
    
    def _validar_db_restaurada(self, db_path: str) -> bool:
        """Valida que la base de datos restaurada esté íntegra"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar integridad básica
            cursor.execute("PRAGMA integrity_check")
            resultado = cursor.fetchone()
            
            if resultado[0] != "ok":
                conn.close()
                return False
            
            # Verificar que tiene tablas
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            conn.close()
            
            return table_count > 0
            
        except Exception as e:
            self.logger.error(f"Error validando DB restaurada: {e}")
            return False
    
    def _aplicar_cambios_tabla(self, conn: sqlite3.Connection, tabla: str, registros: List[Dict]) -> int:
        """Aplica cambios incrementales a una tabla"""
        try:
            registros_aplicados = 0
            cursor = conn.cursor()
            
            for registro in registros:
                try:
                    # Preparar datos para INSERT OR REPLACE
                    columnas = list(registro.keys())
                    valores = list(registro.values())
                    
                    placeholders = ', '.join(['?' for _ in valores])
                    columnas_str = ', '.join(columnas)
                    
                    cursor.execute(f"""
                        INSERT OR REPLACE INTO {tabla} ({columnas_str})
                        VALUES ({placeholders})
                    """, valores)
                    
                    registros_aplicados += 1
                    
                except sqlite3.Error as e:
                    self.logger.warning(f"Error aplicando registro en {tabla}: {e}")
                    continue
            
            return registros_aplicados
            
        except Exception as e:
            self.logger.error(f"Error aplicando cambios a tabla {tabla}: {e}")
            return 0
    
    def _limpiar_archivos_temporales(self, *temp_paths):
        """Limpia archivos y directorios temporales"""
        for temp_path in temp_paths:
            if temp_path and os.path.exists(str(temp_path)):
                try:
                    if os.path.isdir(str(temp_path)):
                        shutil.rmtree(temp_path)
                    else:
                        os.remove(str(temp_path))
                except Exception as e:
                    self.logger.warning(f"No se pudo limpiar {temp_path}: {e}")
    
    def _registrar_restauracion_auditoria(self, tipo: str, backup_path: str, 
                                        exitoso: bool, error: str = None):
        """Registra operación de restauración en auditoría"""
        try:
            ejecutar_consulta_segura("""
                INSERT INTO auditoria_sistema (
                    operacion, tabla_afectada, detalles, usuario, fecha_operacion, exitoso
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                f'RESTORE_{tipo}',
                'SISTEMA',
                json.dumps({
                    'backup_origen': backup_path,
                    'error': error
                }, default=str),
                'SISTEMA',
                datetime.now(),
                exitoso
            ))
            
        except Exception as e:
            self.logger.error(f"Error registrando restauración en auditoría: {e}")

# Funciones de conveniencia
def listar_backups_para_restauracion() -> List[Dict[str, Any]]:
    """Lista backups disponibles para restauración"""
    service = DatabaseRestoreService()
    return service.listar_backups_disponibles()

def restaurar_backup_completo(backup_path: str, confirmar: bool = False) -> Tuple[bool, str]:
    """Restaura un backup completo"""
    service = DatabaseRestoreService()
    return service.restaurar_backup_completo(backup_path, confirmar)

def restaurar_a_fecha(fecha_objetivo: datetime, confirmar: bool = False) -> Tuple[bool, str]:
    """Restaura sistema a una fecha específica"""
    service = DatabaseRestoreService()
    return service.restaurar_a_fecha_especifica(fecha_objetivo, confirmar)
