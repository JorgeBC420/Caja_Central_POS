"""
Integración con WhatsApp para el sistema POS
Envío de notificaciones, confirmaciones y promociones via WhatsApp
"""

import webbrowser
import urllib.parse
import requests
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
import json

from core.database import get_db_cursor, ejecutar_consulta_segura

@dataclass
class ContactoWhatsApp:
    """Contacto de WhatsApp"""
    nombre: str
    numero: str
    activo: bool = True
    grupo: str = ""  # cliente, proveedor, empleado, etc.
    
    def __post_init__(self):
        # Limpiar y validar número
        self.numero = self._limpiar_numero(self.numero)
    
    def _limpiar_numero(self, numero: str) -> str:
        """Limpia y formatea el número de teléfono"""
        # Remover espacios, guiones, paréntesis
        numero_limpio = re.sub(r'[\s\-\(\)]', '', numero)
        
        # Si no tiene código de país, agregar 506 (Costa Rica)
        if len(numero_limpio) == 8 and numero_limpio.isdigit():
            numero_limpio = f"506{numero_limpio}"
        
        # Remover el + si existe
        if numero_limpio.startswith('+'):
            numero_limpio = numero_limpio[1:]
        
        return numero_limpio
    
    def es_valido(self) -> bool:
        """Valida que el número sea válido para Costa Rica"""
        if len(self.numero) != 11:
            return False
        
        if not self.numero.startswith('506'):
            return False
        
        # Validar que los últimos 8 dígitos sean válidos para CR
        numero_local = self.numero[3:]
        return numero_local[0] in ['2', '4', '6', '7', '8'] and numero_local.isdigit()

class WhatsAppConfig:
    """Configuración de WhatsApp"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = self._cargar_configuracion()
    
    def _cargar_configuracion(self) -> Dict[str, str]:
        """Carga configuración de WhatsApp desde BD"""
        try:
            config = {}
            query = "SELECT clave, valor FROM configuraciones WHERE clave LIKE 'whatsapp_%'"
            
            with get_db_cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                
                for row in rows:
                    config[row[0]] = row[1]
            
            # Valores por defecto
            defaults = {
                'whatsapp_api_enabled': 'False',
                'whatsapp_api_url': '',
                'whatsapp_api_token': '',
                'whatsapp_business_number': '',
                'whatsapp_enviar_confirmaciones': 'True',
                'whatsapp_enviar_promociones': 'False',
                'whatsapp_enviar_recordatorios': 'True',
                'whatsapp_template_venta': 'Hola {cliente}, tu compra por ₡{total} ha sido procesada. Ticket: {numero_ticket}. ¡Gracias!',
                'whatsapp_template_promocion': 'Hola {cliente}, tenemos una oferta especial para ti: {promocion}. ¡No te la pierdas!',
                'whatsapp_template_recordatorio': 'Hola {cliente}, tienes un apartado pendiente por ₡{saldo}. Pasa a completar tu compra.',
                'whatsapp_horario_envio_inicio': '08:00',
                'whatsapp_horario_envio_fin': '20:00'
            }
            
            for key, default_value in defaults.items():
                if key not in config:
                    config[key] = default_value
            
            return config
            
        except Exception as e:
            self.logger.error(f"Error cargando configuración WhatsApp: {e}")
            return {}
    
    def actualizar_configuracion(self, nueva_config: Dict[str, str]) -> bool:
        """Actualiza configuración de WhatsApp"""
        try:
            for clave, valor in nueva_config.items():
                if clave.startswith('whatsapp_'):
                    query = "INSERT OR REPLACE INTO configuraciones (clave, valor) VALUES (?, ?)"
                    ejecutar_consulta_segura(query, (clave, valor))
            
            self.config = self._cargar_configuracion()
            return True
            
        except Exception as e:
            self.logger.error(f"Error actualizando configuración WhatsApp: {e}")
            return False

class WhatsAppAPI:
    """Cliente para API de WhatsApp Business"""
    
    def __init__(self, config: WhatsAppConfig):
        self.config = config.config
        self.logger = logging.getLogger(__name__)
    
    def enviar_mensaje_api(self, numero: str, mensaje: str) -> Tuple[bool, str]:
        """Envía mensaje usando API de WhatsApp Business"""
        try:
            if not self.config.get('whatsapp_api_enabled', 'False') == 'True':
                return False, "API de WhatsApp no está habilitada"
            
            api_url = self.config.get('whatsapp_api_url', '')
            api_token = self.config.get('whatsapp_api_token', '')
            
            if not api_url or not api_token:
                return False, "Configuración de API incompleta"
            
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messaging_product': 'whatsapp',
                'to': numero,
                'type': 'text',
                'text': {
                    'body': mensaje
                }
            }
            
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                self.logger.info(f"Mensaje WhatsApp enviado exitosamente a {numero}")
                return True, "Mensaje enviado correctamente"
            else:
                error_msg = f"Error API WhatsApp: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return False, error_msg
                
        except requests.RequestException as e:
            error_msg = f"Error de conexión con API WhatsApp: {e}"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error enviando mensaje WhatsApp: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def verificar_estado_api(self) -> Tuple[bool, str]:
        """Verifica el estado de la API"""
        try:
            if not self.config.get('whatsapp_api_enabled', 'False') == 'True':
                return False, "API no habilitada"
            
            # Hacer ping a la API para verificar conectividad
            api_url = self.config.get('whatsapp_api_url', '')
            api_token = self.config.get('whatsapp_api_token', '')
            
            if not api_url or not api_token:
                return False, "Configuración incompleta"
            
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            }
            
            # Endpoint para verificar estado (ajustar según la API específica)
            health_url = api_url.replace('/messages', '/health')
            response = requests.get(health_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return True, "API funcionando correctamente"
            else:
                return False, f"API responde con error: {response.status_code}"
                
        except Exception as e:
            return False, f"Error verificando API: {e}"

class WhatsAppNotifier:
    """Notificador principal de WhatsApp"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_manager = WhatsAppConfig()
        self.api_client = WhatsAppAPI(self.config_manager)
    
    def send_message(self, number: str, message: str, usar_api: bool = False) -> Tuple[bool, str]:
        """
        Envía mensaje por WhatsApp
        Args:
            number: Número de teléfono en formato internacional
            message: Mensaje a enviar
            usar_api: Si usar API de WhatsApp Business o abrir navegador
        """
        try:
            # Crear contacto para validar número
            contacto = ContactoWhatsApp("Temporal", number)
            
            if not contacto.es_valido():
                return False, f"Número de teléfono inválido: {number}"
            
            # Verificar horario de envío
            if not self._en_horario_envio():
                return False, "Fuera del horario permitido para envío de mensajes"
            
            if usar_api:
                return self.api_client.enviar_mensaje_api(contacto.numero, message)
            else:
                return self._abrir_whatsapp_web(contacto.numero, message)
                
        except Exception as e:
            error_msg = f"Error enviando mensaje WhatsApp: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _abrir_whatsapp_web(self, numero: str, mensaje: str) -> Tuple[bool, str]:
        """Abre WhatsApp Web con el mensaje prellenado"""
        try:
            mensaje_codificado = urllib.parse.quote(mensaje)
            url = f"https://wa.me/{numero}?text={mensaje_codificado}"
            webbrowser.open(url)
            
            self.logger.info(f"WhatsApp Web abierto para {numero}")
            return True, "WhatsApp Web abierto correctamente"
            
        except Exception as e:
            return False, f"Error abriendo WhatsApp Web: {e}"
    
    def _en_horario_envio(self) -> bool:
        """Verifica si está en horario permitido para envío"""
        try:
            ahora = datetime.now().time()
            inicio_str = self.config_manager.config.get('whatsapp_horario_envio_inicio', '08:00')
            fin_str = self.config_manager.config.get('whatsapp_horario_envio_fin', '20:00')
            
            inicio = datetime.strptime(inicio_str, '%H:%M').time()
            fin = datetime.strptime(fin_str, '%H:%M').time()
            
            return inicio <= ahora <= fin
            
        except Exception as e:
            self.logger.warning(f"Error verificando horario: {e}")
            return True  # Permitir envío si hay error
    
    def enviar_confirmacion_venta(self, datos_venta: Dict[str, Any], numero_cliente: str) -> Tuple[bool, str]:
        """Envía confirmación de venta por WhatsApp"""
        try:
            if not self.config_manager.config.get('whatsapp_enviar_confirmaciones', 'True') == 'True':
                return False, "Confirmaciones por WhatsApp deshabilitadas"
            
            template = self.config_manager.config.get('whatsapp_template_venta', 
                'Hola {cliente}, tu compra por ₡{total} ha sido procesada. Ticket: {numero_ticket}. ¡Gracias!')
            
            mensaje = template.format(
                cliente=datos_venta.get('cliente_nombre', 'estimado cliente'),
                total=f"{datos_venta.get('total', 0):,.2f}",
                numero_ticket=datos_venta.get('numero_venta', 'N/A'),
                fecha=datetime.now().strftime('%d/%m/%Y %H:%M'),
                tienda=datos_venta.get('nombre_tienda', 'CajaCentralPOS')
            )
            
            return self.send_message(numero_cliente, mensaje, usar_api=True)
            
        except Exception as e:
            error_msg = f"Error enviando confirmación de venta: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def enviar_promocion(self, numero_cliente: str, nombre_cliente: str, promocion: str) -> Tuple[bool, str]:
        """Envía promoción por WhatsApp"""
        try:
            if not self.config_manager.config.get('whatsapp_enviar_promociones', 'False') == 'True':
                return False, "Promociones por WhatsApp deshabilitadas"
            
            template = self.config_manager.config.get('whatsapp_template_promocion',
                'Hola {cliente}, tenemos una oferta especial para ti: {promocion}. ¡No te la pierdas!')
            
            mensaje = template.format(
                cliente=nombre_cliente,
                promocion=promocion,
                fecha=datetime.now().strftime('%d/%m/%Y')
            )
            
            return self.send_message(numero_cliente, mensaje, usar_api=True)
            
        except Exception as e:
            error_msg = f"Error enviando promoción: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def enviar_recordatorio_apartado(self, datos_apartado: Dict[str, Any], numero_cliente: str) -> Tuple[bool, str]:
        """Envía recordatorio de apartado pendiente"""
        try:
            if not self.config_manager.config.get('whatsapp_enviar_recordatorios', 'True') == 'True':
                return False, "Recordatorios por WhatsApp deshabilitados"
            
            template = self.config_manager.config.get('whatsapp_template_recordatorio',
                'Hola {cliente}, tienes un apartado pendiente por ₡{saldo}. Pasa a completar tu compra.')
            
            mensaje = template.format(
                cliente=datos_apartado.get('cliente_nombre', 'estimado cliente'),
                saldo=f"{datos_apartado.get('saldo_pendiente', 0):,.2f}",
                fecha_apartado=datos_apartado.get('fecha', ''),
                dias_pendiente=datos_apartado.get('dias_pendiente', 0)
            )
            
            return self.send_message(numero_cliente, mensaje, usar_api=True)
            
        except Exception as e:
            error_msg = f"Error enviando recordatorio: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def enviar_alerta_stock_bajo(self, productos_bajo_stock: List[Dict], numero_administrador: str) -> Tuple[bool, str]:
        """Envía alerta de stock bajo a administradores"""
        try:
            if not productos_bajo_stock:
                return False, "No hay productos con stock bajo"
            
            mensaje = f"🚨 ALERTA DE STOCK BAJO ({len(productos_bajo_stock)} productos):\n\n"
            
            for producto in productos_bajo_stock[:10]:  # Máximo 10 productos
                nombre = producto.get('nombre', 'Producto')[:30]
                stock_actual = producto.get('stock_actual', 0)
                stock_minimo = producto.get('stock_minimo', 0)
                mensaje += f"• {nombre}: {stock_actual} (mín: {stock_minimo})\n"
            
            if len(productos_bajo_stock) > 10:
                mensaje += f"... y {len(productos_bajo_stock) - 10} productos más.\n"
            
            mensaje += f"\nFecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            mensaje += f"\nSistema: CajaCentralPOS"
            
            return self.send_message(numero_administrador, mensaje, usar_api=True)
            
        except Exception as e:
            error_msg = f"Error enviando alerta de stock: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def obtener_contactos_grupo(self, grupo: str) -> List[ContactoWhatsApp]:
        """Obtiene contactos de WhatsApp por grupo"""
        try:
            contactos = []
            query = """
                SELECT nombre, telefono FROM clientes 
                WHERE telefono IS NOT NULL AND telefono != '' AND activo = 1
            """
            
            if grupo == 'empleados':
                query = """
                    SELECT nombre, telefono FROM usuarios 
                    WHERE telefono IS NOT NULL AND telefono != '' AND activo = 1
                """
            
            with get_db_cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                
                for row in rows:
                    contacto = ContactoWhatsApp(row[0], row[1], grupo=grupo)
                    if contacto.es_valido():
                        contactos.append(contacto)
            
            return contactos
            
        except Exception as e:
            self.logger.error(f"Error obteniendo contactos: {e}")
            return []
    
    def enviar_mensaje_masivo(self, mensaje: str, grupo: str = "clientes") -> Dict[str, Any]:
        """Envía mensaje masivo a un grupo de contactos"""
        try:
            contactos = self.obtener_contactos_grupo(grupo)
            
            if not contactos:
                return {
                    'exitoso': False,
                    'mensaje': f'No se encontraron contactos válidos en el grupo: {grupo}',
                    'enviados': 0,
                    'fallidos': 0
                }
            
            enviados = 0
            fallidos = 0
            errores = []
            
            for contacto in contactos:
                exito, error = self.send_message(contacto.numero, mensaje, usar_api=True)
                
                if exito:
                    enviados += 1
                else:
                    fallidos += 1
                    errores.append(f"{contacto.nombre}: {error}")
                
                # Pausa para evitar spam
                import time
                time.sleep(1)
            
            return {
                'exitoso': True,
                'mensaje': f'Envío masivo completado',
                'enviados': enviados,
                'fallidos': fallidos,
                'total_contactos': len(contactos),
                'errores': errores[:10]  # Máximo 10 errores
            }
            
        except Exception as e:
            return {
                'exitoso': False,
                'mensaje': f'Error en envío masivo: {e}',
                'enviados': 0,
                'fallidos': 0
            }

# Instancia global
whatsapp_notifier = WhatsAppNotifier()

# Funciones de utilidad para compatibilidad con código existente
def enviar_mensaje_whatsapp(numero: str, mensaje: str) -> bool:
    """Función de compatibilidad"""
    exito, _ = whatsapp_notifier.send_message(numero, mensaje)
    return exito

def validar_numero_whatsapp(numero: str) -> bool:
    """Valida número de WhatsApp para Costa Rica"""
    try:
        contacto = ContactoWhatsApp("Temporal", numero)
        return contacto.es_valido()
    except:
        return False