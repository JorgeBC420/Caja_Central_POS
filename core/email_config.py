"""
Configuración y manejo de correos electrónicos para el sistema POS
Incluye notificaciones, reportes y facturación electrónica
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.image import MIMEImage
from typing import List, Dict, Optional, Any
from datetime import datetime
import ssl
import os
from pathlib import Path

from core.database import get_db_cursor, ejecutar_consulta_segura

class EmailConfig:
    """Configuración de parámetros de correo"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = self._cargar_configuracion()
    
    def _cargar_configuracion(self) -> Dict[str, Any]:
        """Carga la configuración de correo desde la base de datos"""
        try:
            config = {}
            query = "SELECT clave, valor FROM configuraciones WHERE clave LIKE 'email_%'"
            
            with get_db_cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                
                for row in rows:
                    config[row[0]] = row[1]
            
            # Valores por defecto si no existen en BD
            defaults = {
                'email_smtp_server': 'smtp.gmail.com',
                'email_smtp_port': '587',
                'email_username': '',
                'email_password': '',
                'email_from_name': 'Sistema POS',
                'email_use_tls': 'True',
                'email_timeout': '30',
                'email_max_attachments': '5',
                'email_max_size_mb': '25'
            }
            
            for key, default_value in defaults.items():
                if key not in config:
                    config[key] = default_value
            
            return config
            
        except Exception as e:
            self.logger.error(f"Error cargando configuración de email: {e}")
            return {}
    
    def actualizar_configuracion(self, nueva_config: Dict[str, str]) -> bool:
        """Actualiza la configuración de correo"""
        try:
            for clave, valor in nueva_config.items():
                if clave.startswith('email_'):
                    query = "INSERT OR REPLACE INTO configuraciones (clave, valor) VALUES (?, ?)"
                    ejecutar_consulta_segura(query, (clave, valor))
            
            # Recargar configuración
            self.config = self._cargar_configuracion()
            self.logger.info("Configuración de email actualizada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error actualizando configuración de email: {e}")
            return False
    
    def obtener_configuracion(self) -> Dict[str, str]:
        """Retorna la configuración actual (sin password)"""
        config_segura = self.config.copy()
        config_segura['email_password'] = '***' if config_segura.get('email_password') else ''
        return config_segura
    
    def validar_configuracion(self) -> tuple[bool, str]:
        """Valida que la configuración esté completa"""
        campos_requeridos = ['email_smtp_server', 'email_username', 'email_password']
        
        for campo in campos_requeridos:
            if not self.config.get(campo):
                return False, f"Campo requerido faltante: {campo}"
        
        return True, "Configuración válida"

class EmailSender:
    """Clase principal para envío de correos"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_manager = EmailConfig()
        self.config = self.config_manager.config
    
    def enviar_correo(self, destinatarios: List[str], asunto: str, 
                     mensaje_html: str, mensaje_texto: str = None,
                     archivos_adjuntos: List[str] = None) -> bool:
        """
        Envía un correo electrónico
        
        Args:
            destinatarios: Lista de direcciones de correo
            asunto: Asunto del correo
            mensaje_html: Mensaje en formato HTML
            mensaje_texto: Mensaje en texto plano (opcional)
            archivos_adjuntos: Lista de rutas de archivos a adjuntar
        """
        try:
            # Validar configuración
            valida, mensaje = self.config_manager.validar_configuracion()
            if not valida:
                self.logger.error(f"Configuración inválida: {mensaje}")
                return False
            
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.config.get('email_from_name', 'Sistema POS')} <{self.config['email_username']}>"
            msg['To'] = ', '.join(destinatarios)
            msg['Subject'] = asunto
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Agregar contenido
            if mensaje_texto:
                part_texto = MIMEText(mensaje_texto, 'plain', 'utf-8')
                msg.attach(part_texto)
            
            part_html = MIMEText(mensaje_html, 'html', 'utf-8')
            msg.attach(part_html)
            
            # Agregar archivos adjuntos
            if archivos_adjuntos:
                if not self._agregar_archivos_adjuntos(msg, archivos_adjuntos):
                    return False
            
            # Enviar correo
            return self._enviar_mensaje(msg, destinatarios)
            
        except Exception as e:
            self.logger.error(f"Error enviando correo: {e}")
            return False
    
    def _agregar_archivos_adjuntos(self, msg: MIMEMultipart, archivos: List[str]) -> bool:
        """Agrega archivos adjuntos al mensaje"""
        try:
            max_attachments = int(self.config.get('email_max_attachments', 5))
            max_size_mb = int(self.config.get('email_max_size_mb', 25))
            
            if len(archivos) > max_attachments:
                self.logger.warning(f"Demasiados archivos adjuntos: {len(archivos)} > {max_attachments}")
                archivos = archivos[:max_attachments]
            
            total_size = 0
            
            for archivo_path in archivos:
                if not os.path.exists(archivo_path):
                    self.logger.warning(f"Archivo no encontrado: {archivo_path}")
                    continue
                
                file_size = os.path.getsize(archivo_path) / (1024 * 1024)  # MB
                total_size += file_size
                
                if total_size > max_size_mb:
                    self.logger.warning(f"Tamaño total de archivos excede {max_size_mb}MB")
                    break
                
                with open(archivo_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                filename = Path(archivo_path).name
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                msg.attach(part)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error agregando archivos adjuntos: {e}")
            return False
    
    def _enviar_mensaje(self, msg: MIMEMultipart, destinatarios: List[str]) -> bool:
        """Envía el mensaje usando SMTP"""
        try:
            server = None
            smtp_server = self.config['email_smtp_server']
            smtp_port = int(self.config.get('email_smtp_port', 587))
            username = self.config['email_username']
            password = self.config['email_password']
            use_tls = self.config.get('email_use_tls', 'True').lower() == 'true'
            timeout = int(self.config.get('email_timeout', 30))
            
            # Crear conexión SMTP
            if smtp_port == 465:  # SSL
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=timeout)
            else:  # TLS
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=timeout)
                if use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
            
            # Autenticar
            server.login(username, password)
            
            # Enviar mensaje
            texto_mensaje = msg.as_string()
            server.sendmail(username, destinatarios, texto_mensaje)
            
            self.logger.info(f"Correo enviado exitosamente a: {', '.join(destinatarios)}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            self.logger.error("Error de autenticación SMTP - Verificar credenciales")
            return False
        except smtplib.SMTPRecipientsRefused:
            self.logger.error("Destinatarios rechazados por el servidor SMTP")
            return False
        except smtplib.SMTPServerDisconnected:
            self.logger.error("Servidor SMTP desconectado inesperadamente")
            return False
        except Exception as e:
            self.logger.error(f"Error enviando mensaje SMTP: {e}")
            return False
        finally:
            if server:
                try:
                    server.quit()
                except:
                    pass
    
    def probar_conexion(self) -> tuple[bool, str]:
        """Prueba la conexión con el servidor SMTP"""
        try:
            valida, mensaje = self.config_manager.validar_configuracion()
            if not valida:
                return False, mensaje
            
            smtp_server = self.config['email_smtp_server']
            smtp_port = int(self.config.get('email_smtp_port', 587))
            username = self.config['email_username']
            password = self.config['email_password']
            use_tls = self.config.get('email_use_tls', 'True').lower() == 'true'
            
            server = None
            
            if smtp_port == 465:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=10)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
                if use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
            
            server.login(username, password)
            server.quit()
            
            return True, "Conexión exitosa con el servidor SMTP"
            
        except smtplib.SMTPAuthenticationError:
            return False, "Error de autenticación - Verificar usuario y contraseña"
        except smtplib.SMTPConnectError:
            return False, "No se pudo conectar al servidor SMTP"
        except Exception as e:
            return False, f"Error de conexión: {str(e)}"

class EmailTemplates:
    """Templates de correo para diferentes situaciones"""
    
    @staticmethod
    def template_venta_completada(datos_venta: Dict) -> tuple[str, str]:
        """Template para notificación de venta completada"""
        fecha_str = datos_venta.get('fecha', datetime.now().strftime('%d/%m/%Y %H:%M'))
        asunto = f"Venta #{datos_venta.get('numero_venta', 'N/A')} - {fecha_str}"
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; }}
                .total {{ font-size: 18px; font-weight: bold; color: #2E7D32; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Venta Completada</h2>
            </div>
            <div class="content">
                <p><strong>Número de Venta:</strong> {datos_venta.get('numero_venta', 'N/A')}</p>
                <p><strong>Fecha:</strong> {datos_venta.get('fecha', datetime.now().strftime('%d/%m/%Y %H:%M'))}</p>
                <p><strong>Vendedor:</strong> {datos_venta.get('vendedor', 'N/A')}</p>
                
                <h3>Detalle de Productos</h3>
                <table>
                    <tr>
                        <th>Producto</th>
                        <th>Cantidad</th>
                        <th>Precio</th>
                        <th>Subtotal</th>
                    </tr>
                    {"".join([f"<tr><td>{item.get('nombre', '')}</td><td>{item.get('cantidad', 0)}</td><td>₡{item.get('precio', 0):,.2f}</td><td>₡{item.get('subtotal', 0):,.2f}</td></tr>" for item in datos_venta.get('items', [])])}
                </table>
                
                <div class="total">
                    <p>Total: ₡{datos_venta.get('total', 0):,.2f}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return asunto, html
    
    @staticmethod
    def template_stock_bajo(productos_bajo_stock: List[Dict]) -> tuple[str, str]:
        """Template para alerta de stock bajo"""
        asunto = f"Alerta: {len(productos_bajo_stock)} productos con stock bajo"
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #FF9800; color: white; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; }}
                .alert {{ background-color: #FFF3E0; border-left: 4px solid #FF9800; padding: 10px; margin: 10px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Alerta de Stock Bajo</h2>
            </div>
            <div class="content">
                <div class="alert">
                    <strong>¡Atención!</strong> Los siguientes productos tienen stock por debajo del mínimo establecido.
                </div>
                
                <table>
                    <tr>
                        <th>Código</th>
                        <th>Producto</th>
                        <th>Stock Actual</th>
                        <th>Stock Mínimo</th>
                        <th>Diferencia</th>
                    </tr>
                    {"".join([f"<tr><td>{p.get('codigo', '')}</td><td>{p.get('nombre', '')}</td><td>{p.get('stock_actual', 0)}</td><td>{p.get('stock_minimo', 0)}</td><td style='color: red;'>{p.get('stock_actual', 0) - p.get('stock_minimo', 0)}</td></tr>" for p in productos_bajo_stock])}
                </table>
                
                <p><strong>Fecha del reporte:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
        </body>
        </html>
        """
        
        return asunto, html
    
    @staticmethod
    def template_reporte_diario(datos_reporte: Dict) -> tuple[str, str]:
        """Template para reporte diario de ventas"""
        fecha = datos_reporte.get('fecha', datetime.now().strftime('%d/%m/%Y'))
        asunto = f"Reporte Diario de Ventas - {fecha}"
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #2196F3; color: white; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; }}
                .summary {{ background-color: #E3F2FD; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .metric {{ display: inline-block; margin: 10px 20px; text-align: center; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #1976D2; }}
                .metric-label {{ font-size: 14px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Reporte Diario de Ventas</h2>
            </div>
            <div class="content">
                <h3>Resumen del día {fecha}</h3>
                
                <div class="summary">
                    <div class="metric">
                        <div class="metric-value">{datos_reporte.get('total_ventas', 0)}</div>
                        <div class="metric-label">Ventas</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">₡{datos_reporte.get('total_ingresos', 0):,.2f}</div>
                        <div class="metric-label">Ingresos</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{datos_reporte.get('productos_vendidos', 0)}</div>
                        <div class="metric-label">Productos Vendidos</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">₡{datos_reporte.get('ticket_promedio', 0):,.2f}</div>
                        <div class="metric-label">Ticket Promedio</div>
                    </div>
                </div>
                
                <p><strong>Período:</strong> {datos_reporte.get('hora_inicio', '00:00')} - {datos_reporte.get('hora_fin', '23:59')}</p>
                <p><strong>Generado:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
        </body>
        </html>
        """
        
        return asunto, html

class EmailNotifier:
    """Clase para manejar notificaciones por correo"""
    
    def __init__(self):
        self.sender = EmailSender()
        self.logger = logging.getLogger(__name__)
    
    def notificar_venta_completada(self, datos_venta: Dict, destinatarios: List[str]) -> bool:
        """Notifica cuando se completa una venta"""
        try:
            asunto, html = EmailTemplates.template_venta_completada(datos_venta)
            return self.sender.enviar_correo(destinatarios, asunto, html)
        except Exception as e:
            self.logger.error(f"Error enviando notificación de venta: {e}")
            return False
    
    def notificar_stock_bajo(self, productos: List[Dict], destinatarios: List[str]) -> bool:
        """Notifica productos con stock bajo"""
        try:
            asunto, html = EmailTemplates.template_stock_bajo(productos)
            return self.sender.enviar_correo(destinatarios, asunto, html)
        except Exception as e:
            self.logger.error(f"Error enviando alerta de stock: {e}")
            return False
    
    def enviar_reporte_diario(self, datos_reporte: Dict, destinatarios: List[str]) -> bool:
        """Envía reporte diario por correo"""
        try:
            asunto, html = EmailTemplates.template_reporte_diario(datos_reporte)
            return self.sender.enviar_correo(destinatarios, asunto, html)
        except Exception as e:
            self.logger.error(f"Error enviando reporte diario: {e}")
            return False

# Instancia global
email_notifier = EmailNotifier()
