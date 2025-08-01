"""
Sistema de licencias para el POS
Maneja validación, activación y control de funcionalidades según licencia
"""

import hashlib
import hmac
import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import os
import platform
import uuid

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logging.warning("cryptography library not available, using basic encryption")

from core.database import get_db_cursor, ejecutar_consulta_segura
from core.models import LicenciaSistema, EstadoLicencia

class LicenseError(Exception):
    """Excepción personalizada para errores de licencia"""
    pass

class HardwareFingerprint:
    """Genera huella digital del hardware"""
    
    @staticmethod
    def obtener_mac_address() -> str:
        """Obtiene la dirección MAC principal"""
        try:
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                           for elements in range(0,2*6,2)][::-1])
            return mac
        except:
            return "00:00:00:00:00:00"
    
    @staticmethod
    def obtener_cpu_info() -> str:
        """Obtiene información básica del CPU"""
        try:
            if platform.system() == "Windows":
                try:
                    import wmi
                    c = wmi.WMI()
                    for processor in c.Win32_Processor():
                        return processor.ProcessorId[:16]
                except ImportError:
                    # Fallback usando subprocess
                    try:
                        import subprocess
                        result = subprocess.run(['wmic', 'cpu', 'get', 'ProcessorId'], 
                                              capture_output=True, text=True)
                        lines = result.stdout.strip().split('\n')
                        if len(lines) > 1:
                            return lines[1].strip()[:16]
                    except:
                        pass
            else:
                # Para Linux/Mac, usar información disponible
                return platform.processor()[:16]
        except:
            pass
        return platform.machine()[:16]
    
    @staticmethod
    def obtener_disk_serial() -> str:
        """Obtiene serial del disco principal"""
        try:
            if platform.system() == "Windows":
                try:
                    import wmi
                    c = wmi.WMI()
                    for disk in c.Win32_PhysicalMedia():
                        if disk.SerialNumber:
                            return disk.SerialNumber.strip()[:16]
                except ImportError:
                    # Fallback usando subprocess
                    try:
                        import subprocess
                        result = subprocess.run(['wmic', 'diskdrive', 'get', 'serialnumber'], 
                                              capture_output=True, text=True)
                        lines = result.stdout.strip().split('\n')
                        for line in lines[1:]:
                            if line.strip():
                                return line.strip()[:16]
                    except:
                        pass
            return "UNKNOWN_DISK"
        except:
            return "UNKNOWN_DISK"
    
    @classmethod
    def generar_fingerprint(cls) -> str:
        """Genera fingerprint único del hardware"""
        try:
            mac = cls.obtener_mac_address()
            cpu = cls.obtener_cpu_info()
            disk = cls.obtener_disk_serial()
            sistema = platform.system()
            
            # Combinar información y generar hash
            info_hardware = f"{mac}|{cpu}|{disk}|{sistema}"
            fingerprint = hashlib.sha256(info_hardware.encode()).hexdigest()[:32]
            
            return fingerprint.upper()
            
        except Exception as e:
            logging.error(f"Error generando fingerprint: {e}")
            # Fingerprint de fallback basado en información básica
            fallback = f"{platform.node()}|{platform.system()}|{platform.release()}"
            return hashlib.md5(fallback.encode()).hexdigest()[:32].upper()

class LicenseEncryption:
    """Manejo de encriptación de licencias"""
    
    def __init__(self, master_key: str = "POS_CENTRAL_MASTER_KEY_2024"):
        self.master_key = master_key.encode()
        
    def _generar_clave_derivada(self, salt: bytes) -> bytes:
        """Genera una clave derivada usando PBKDF2"""
        if CRYPTO_AVAILABLE:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            return base64.urlsafe_b64encode(kdf.derive(self.master_key))
        else:
            # Fallback usando hashlib PBKDF2
            import hashlib
            dk = hashlib.pbkdf2_hmac('sha256', self.master_key, salt, 100000, 32)
            return base64.urlsafe_b64encode(dk)
    
    def _encriptar_basico(self, data: str, key: bytes) -> bytes:
        """Encriptación básica usando XOR cuando cryptography no está disponible"""
        key_hash = hashlib.sha256(key).digest()
        result = bytearray()
        for i, byte in enumerate(data.encode()):
            result.append(byte ^ key_hash[i % len(key_hash)])
        return bytes(result)
    
    def _desencriptar_basico(self, data: bytes, key: bytes) -> str:
        """Desencriptación básica usando XOR cuando cryptography no está disponible"""
        key_hash = hashlib.sha256(key).digest()
        result = bytearray()
        for i, byte in enumerate(data):
            result.append(byte ^ key_hash[i % len(key_hash)])
        return result.decode()
    
    def encriptar_licencia(self, datos_licencia: Dict[str, Any]) -> str:
        """Encripta los datos de la licencia"""
        try:
            # Convertir a JSON
            json_data = json.dumps(datos_licencia, default=str)
            
            # Generar salt aleatorio
            salt = os.urandom(16)
            
            # Crear clave de encriptación
            key = self._generar_clave_derivada(salt)
            
            if CRYPTO_AVAILABLE:
                f = Fernet(key)
                encrypted_data = f.encrypt(json_data.encode())
            else:
                # Usar encriptación básica
                encrypted_data = self._encriptar_basico(json_data, key)
            
            # Combinar salt y datos encriptados
            license_data = base64.b64encode(salt + encrypted_data).decode()
            
            return license_data
            
        except Exception as e:
            raise LicenseError(f"Error encriptando licencia: {e}")
    
    def desencriptar_licencia(self, license_key: str) -> Dict[str, Any]:
        """Desencripta los datos de la licencia"""
        try:
            # Decodificar base64
            combined_data = base64.b64decode(license_key.encode())
            
            # Separar salt y datos encriptados
            salt = combined_data[:16]
            encrypted_data = combined_data[16:]
            
            # Generar clave de desencriptación
            key = self._generar_clave_derivada(salt)
            
            if CRYPTO_AVAILABLE:
                f = Fernet(key)
                decrypted_data = f.decrypt(encrypted_data)
                json_data = decrypted_data.decode()
            else:
                # Usar desencriptación básica
                json_data = self._desencriptar_basico(encrypted_data, key)
            
            # Convertir de JSON
            datos_licencia = json.loads(json_data)
            
            return datos_licencia
            
        except Exception as e:
            raise LicenseError(f"Error desencriptando licencia: {e}")

class LicenseValidator:
    """Validador de licencias"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.encryption = LicenseEncryption()
        self.fingerprint = HardwareFingerprint()
    
    def validar_estructura_licencia(self, datos_licencia: Dict[str, Any]) -> Tuple[bool, str]:
        """Valida la estructura básica de la licencia"""
        campos_requeridos = [
            'clave_licencia', 'fecha_activacion', 'fecha_expiracion',
            'estado', 'fingerprint_hardware', 'max_usuarios',
            'max_productos', 'modulos_habilitados', 'hash_verificacion'
        ]
        
        for campo in campos_requeridos:
            if campo not in datos_licencia:
                return False, f"Campo requerido faltante: {campo}"
        
        return True, "Estructura válida"
    
    def validar_fecha_vigencia(self, fecha_expiracion: str) -> Tuple[bool, str]:
        """Valida que la licencia no esté expirada"""
        try:
            fecha_exp = datetime.fromisoformat(fecha_expiracion)
            fecha_actual = datetime.now()
            
            if fecha_exp < fecha_actual:
                dias_expirada = (fecha_actual - fecha_exp).days
                return False, f"Licencia expirada hace {dias_expirada} días"
            
            dias_restantes = (fecha_exp - fecha_actual).days
            return True, f"Licencia válida por {dias_restantes} días"
            
        except Exception as e:
            return False, f"Error validando fecha: {e}"
    
    def validar_hardware(self, fingerprint_licencia: str) -> Tuple[bool, str]:
        """Valida que la licencia corresponda al hardware actual"""
        try:
            fingerprint_actual = self.fingerprint.generar_fingerprint()
            
            if fingerprint_licencia != fingerprint_actual:
                return False, "La licencia no corresponde a este equipo"
            
            return True, "Hardware validado correctamente"
            
        except Exception as e:
            return False, f"Error validando hardware: {e}"
    
    def validar_integridad(self, datos_licencia: Dict[str, Any]) -> Tuple[bool, str]:
        """Valida la integridad de los datos usando hash"""
        try:
            hash_almacenado = datos_licencia.pop('hash_verificacion', '')
            
            # Crear hash de los datos
            datos_str = json.dumps(datos_licencia, sort_keys=True)
            hash_calculado = hashlib.sha256(datos_str.encode()).hexdigest()
            
            # Restaurar hash en los datos
            datos_licencia['hash_verificacion'] = hash_almacenado
            
            if hash_almacenado != hash_calculado:
                return False, "Los datos de la licencia han sido modificados"
            
            return True, "Integridad verificada"
            
        except Exception as e:
            return False, f"Error validando integridad: {e}"
    
    def validar_licencia_completa(self, license_key: str) -> Tuple[bool, str, Optional[Dict]]:
        """Validación completa de la licencia"""
        try:
            # Desencriptar licencia
            try:
                datos_licencia = self.encryption.desencriptar_licencia(license_key)
            except LicenseError as e:
                return False, f"Licencia inválida: {e}", None
            
            # Validar estructura
            valida, mensaje = self.validar_estructura_licencia(datos_licencia)
            if not valida:
                return False, mensaje, None
            
            # Validar integridad
            valida, mensaje = self.validar_integridad(datos_licencia)
            if not valida:
                return False, mensaje, None
            
            # Validar hardware
            valida, mensaje = self.validar_hardware(datos_licencia['fingerprint_hardware'])
            if not valida:
                return False, mensaje, None
            
            # Validar fechas
            valida, mensaje = self.validar_fecha_vigencia(datos_licencia['fecha_expiracion'])
            if not valida:
                return False, mensaje, None
            
            return True, "Licencia válida", datos_licencia
            
        except Exception as e:
            self.logger.error(f"Error en validación completa: {e}")
            return False, f"Error interno: {e}", None

class LicenseManager:
    """Gestor principal de licencias"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validator = LicenseValidator()
        self.encryption = LicenseEncryption()
        self._licencia_actual = None
    
    def obtener_licencia_actual(self) -> Optional[LicenciaSistema]:
        """Obtiene la licencia actual desde la base de datos"""
        try:
            if self._licencia_actual is None:
                self._cargar_licencia_bd()
            return self._licencia_actual
        except Exception as e:
            self.logger.error(f"Error obteniendo licencia: {e}")
            return None
    
    def _cargar_licencia_bd(self):
        """Carga la licencia desde la base de datos"""
        try:
            query = "SELECT clave_licencia, datos_licencia FROM licencia ORDER BY id DESC LIMIT 1"
            
            with get_db_cursor() as cursor:
                cursor.execute(query)
                row = cursor.fetchone()
                
                if row:
                    clave_licencia = row[0]
                    
                    # Validar licencia
                    valida, mensaje, datos = self.validator.validar_licencia_completa(clave_licencia)
                    
                    if valida and datos:
                        self._licencia_actual = LicenciaSistema(
                            clave=clave_licencia,
                            fecha_activacion=datetime.fromisoformat(datos['fecha_activacion']),
                            fecha_expiracion=datetime.fromisoformat(datos['fecha_expiracion']),
                            estado=EstadoLicencia(datos['estado']),
                            max_usuarios=datos.get('max_usuarios', 1),
                            max_productos=datos.get('max_productos', 1000),
                            modulos_habilitados=datos.get('modulos_habilitados', [])
                        )
                    else:
                        # Licencia inválida
                        self._licencia_actual = None
                        self.logger.warning(f"Licencia inválida: {mensaje}")
                
        except Exception as e:
            self.logger.error(f"Error cargando licencia: {e}")
            self._licencia_actual = None
    
    def activar_licencia(self, clave_licencia: str) -> Tuple[bool, str]:
        """Activa una nueva licencia"""
        try:
            # Validar licencia
            valida, mensaje, datos = self.validator.validar_licencia_completa(clave_licencia)
            
            if not valida:
                return False, mensaje
            
            # Guardar en base de datos
            query = """
                INSERT OR REPLACE INTO licencia 
                (clave_licencia, datos_licencia, fecha_activacion, estado)
                VALUES (?, ?, ?, ?)
            """
            
            success, db_message = ejecutar_consulta_segura(
                query, 
                (clave_licencia, json.dumps(datos), datetime.now().isoformat(), 'activa')
            )
            
            if success:
                # Limpiar cache para forzar recarga
                self._licencia_actual = None
                self.logger.info("Licencia activada exitosamente")
                return True, "Licencia activada correctamente"
            else:
                return False, f"Error guardando licencia: {db_message}"
                
        except Exception as e:
            self.logger.error(f"Error activando licencia: {e}")
            return False, f"Error interno: {e}"
    
    def verificar_funcionalidad(self, modulo: str) -> bool:
        """Verifica si un módulo está habilitado en la licencia"""
        try:
            licencia = self.obtener_licencia_actual()
            
            if not licencia or not licencia.esta_vigente:
                return False
            
            # Módulos básicos siempre disponibles
            modulos_basicos = ['ventas', 'productos', 'clientes', 'reportes_basicos']
            
            if modulo in modulos_basicos:
                return True
            
            # Verificar módulos de la licencia
            return modulo in licencia.modulos_habilitados
            
        except Exception as e:
            self.logger.error(f"Error verificando funcionalidad {modulo}: {e}")
            return False
    
    def verificar_limite_usuarios(self, usuarios_activos: int) -> bool:
        """Verifica si se puede tener más usuarios activos"""
        try:
            licencia = self.obtener_licencia_actual()
            
            if not licencia or not licencia.esta_vigente:
                return False
            
            return usuarios_activos <= licencia.max_usuarios
            
        except Exception as e:
            self.logger.error(f"Error verificando límite usuarios: {e}")
            return False
    
    def verificar_limite_productos(self, productos_activos: int) -> bool:
        """Verifica si se pueden tener más productos"""
        try:
            licencia = self.obtener_licencia_actual()
            
            if not licencia or not licencia.esta_vigente:
                return False
            
            return productos_activos <= licencia.max_productos
            
        except Exception as e:
            self.logger.error(f"Error verificando límite productos: {e}")
            return False
    
    def obtener_info_licencia(self) -> Dict[str, Any]:
        """Obtiene información completa de la licencia"""
        try:
            licencia = self.obtener_licencia_actual()
            
            if not licencia:
                return {
                    'tiene_licencia': False,
                    'estado': 'sin_licencia',
                    'mensaje': 'No hay licencia activada'
                }
            
            return {
                'tiene_licencia': True,
                'estado': licencia.estado.value,
                'vigente': licencia.esta_vigente,
                'dias_restantes': licencia.dias_restantes,
                'fecha_expiracion': licencia.fecha_expiracion.strftime('%d/%m/%Y'),
                'max_usuarios': licencia.max_usuarios,
                'max_productos': licencia.max_productos,
                'modulos_habilitados': licencia.modulos_habilitados,
                'mensaje': f"Licencia válida por {licencia.dias_restantes} días"
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo info licencia: {e}")
            return {
                'tiene_licencia': False,
                'estado': 'error',
                'mensaje': f'Error: {e}'
            }
    
    def generar_info_hardware(self) -> Dict[str, str]:
        """Genera información del hardware para solicitar licencia"""
        try:
            fingerprint = HardwareFingerprint()
            
            return {
                'fingerprint': fingerprint.generar_fingerprint(),
                'mac_address': fingerprint.obtener_mac_address(),
                'sistema_operativo': platform.system(),
                'version_sistema': platform.release(),
                'arquitectura': platform.architecture()[0],
                'nombre_equipo': platform.node(),
                'fecha_solicitud': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generando info hardware: {e}")
            return {}

# Funciones de utilidad para la UI
def verificar_licencia_ui(parent_widget=None) -> bool:
    """Verifica la licencia y muestra mensajes apropiados"""
    try:
        from tkinter import messagebox
        
        license_manager = LicenseManager()
        info_licencia = license_manager.obtener_info_licencia()
        
        if not info_licencia['tiene_licencia']:
            messagebox.showerror(
                "Licencia requerida",
                "El sistema no tiene una licencia válida activada.\n"
                "Contacte al administrador para activar el sistema.",
                parent=parent_widget
            )
            return False
        
        if not info_licencia['vigente']:
            messagebox.showerror(
                "Licencia expirada",
                f"La licencia del sistema ha expirado.\n"
                f"Estado: {info_licencia['estado']}\n"
                f"Contacte al proveedor para renovar la licencia.",
                parent=parent_widget
            )
            return False
        
        # Advertir si queda poco tiempo
        if info_licencia['dias_restantes'] <= 30:
            messagebox.showwarning(
                "Licencia por expirar",
                f"La licencia expirará en {info_licencia['dias_restantes']} días.\n"
                f"Fecha de expiración: {info_licencia['fecha_expiracion']}\n"
                f"Contacte al proveedor para renovar.",
                parent=parent_widget
            )
        
        return True
        
    except Exception as e:
        if 'messagebox' in locals():
            messagebox.showerror(
                "Error de licencia",
                f"Error verificando licencia: {e}",
                parent=parent_widget
            )
        return False

def deshabilitar_funcionalidad_sin_licencia(parent_widget):
    """Deshabilita la funcionalidad cuando no hay licencia válida"""
    try:
        if hasattr(parent_widget, "destroy") and callable(parent_widget.destroy):
            parent_widget.destroy()
        elif hasattr(parent_widget, "winfo_children"):
            for widget in parent_widget.winfo_children():
                try:
                    widget.configure(state="disabled")
                except Exception:
                    pass
    except Exception as e:
        logging.error(f"Error deshabilitando funcionalidad: {e}")

# Instancia global
license_manager = LicenseManager()