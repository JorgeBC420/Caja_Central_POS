"""
Utilidades de impresión para el sistema POS
Soporte para impresoras térmicas, tickets, reportes y facturas
"""

import logging
import os
import platform
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from decimal import Decimal
import tempfile
import subprocess

# Librerías de impresión
try:
    from escpos.printer import Usb, Serial, Network, File
    from escpos.exceptions import USBNotFoundError, SerialException
    ESC_POS_AVAILABLE = True
except ImportError:
    ESC_POS_AVAILABLE = False

try:
    import win32print
    import win32api
    WIN32_AVAILABLE = platform.system() == "Windows"
except ImportError:
    WIN32_AVAILABLE = False

from core.database import get_db_cursor, ejecutar_consulta_segura
from core.models import ConfigTienda

class PrinterConfig:
    """Configuración de impresoras"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = self._cargar_configuracion()
    
    def _cargar_configuracion(self) -> Dict[str, Any]:
        """Carga configuración de impresoras desde BD"""
        try:
            config = {}
            query = "SELECT clave, valor FROM configuraciones WHERE clave LIKE 'printer_%'"
            
            with get_db_cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                
                for row in rows:
                    config[row[0]] = row[1]
            
            # Valores por defecto
            defaults = {
                'printer_type': 'usb',  # usb, serial, network, windows
                'printer_usb_vendor': '0x04b8',
                'printer_usb_product': '0x0202',
                'printer_serial_port': 'COM1',
                'printer_serial_baudrate': '9600',
                'printer_network_ip': '192.168.1.100',
                'printer_network_port': '9100',
                'printer_windows_name': '',
                'printer_paper_width': '58',  # 58mm o 80mm
                'printer_chars_per_line': '32',
                'printer_cut_paper': 'True',
                'printer_open_drawer': 'True',
                'printer_copies': '1'
            }
            
            for key, default_value in defaults.items():
                if key not in config:
                    config[key] = default_value
            
            return config
            
        except Exception as e:
            self.logger.error(f"Error cargando configuración impresora: {e}")
            return {}
    
    def actualizar_configuracion(self, nueva_config: Dict[str, str]) -> bool:
        """Actualiza configuración de impresora"""
        try:
            for clave, valor in nueva_config.items():
                if clave.startswith('printer_'):
                    query = "INSERT OR REPLACE INTO configuraciones (clave, valor) VALUES (?, ?)"
                    ejecutar_consulta_segura(query, (clave, valor))
            
            self.config = self._cargar_configuracion()
            return True
            
        except Exception as e:
            self.logger.error(f"Error actualizando configuración impresora: {e}")
            return False

class PrinterConnector:
    """Conector para diferentes tipos de impresoras"""
    
    def __init__(self, config: PrinterConfig):
        self.config = config.config
        self.logger = logging.getLogger(__name__)
    
    def obtener_impresora(self):
        """Obtiene conexión a la impresora según configuración"""
        try:
            printer_type = self.config.get('printer_type', 'usb')
            
            if printer_type == 'usb' and ESC_POS_AVAILABLE:
                return self._conectar_usb()
            elif printer_type == 'serial' and ESC_POS_AVAILABLE:
                return self._conectar_serial()
            elif printer_type == 'network' and ESC_POS_AVAILABLE:
                return self._conectar_network()
            elif printer_type == 'windows' and WIN32_AVAILABLE:
                return self._conectar_windows()
            else:
                # Fallback a archivo para testing
                return self._conectar_archivo()
                
        except Exception as e:
            self.logger.error(f"Error conectando impresora: {e}")
            raise
    
    def _conectar_usb(self):
        """Conecta impresora USB"""
        try:
            vendor_id = int(self.config.get('printer_usb_vendor', '0x04b8'), 16)
            product_id = int(self.config.get('printer_usb_product', '0x0202'), 16)
            
            printer = Usb(vendor_id, product_id, 0)
            return printer
            
        except USBNotFoundError:
            raise Exception("Impresora USB no encontrada - Verificar conexión")
        except Exception as e:
            raise Exception(f"Error conectando impresora USB: {e}")
    
    def _conectar_serial(self):
        """Conecta impresora Serial"""
        try:
            port = self.config.get('printer_serial_port', 'COM1')
            baudrate = int(self.config.get('printer_serial_baudrate', '9600'))
            
            printer = Serial(devfile=port, baudrate=baudrate)
            return printer
            
        except SerialException:
            raise Exception(f"Puerto serial {port} no disponible")
        except Exception as e:
            raise Exception(f"Error conectando impresora Serial: {e}")
    
    def _conectar_network(self):
        """Conecta impresora de red"""
        try:
            ip = self.config.get('printer_network_ip', '192.168.1.100')
            port = int(self.config.get('printer_network_port', '9100'))
            
            printer = Network(ip, port=port)
            return printer
            
        except Exception as e:
            raise Exception(f"Error conectando impresora de red {ip}:{port} - {e}")
    
    def _conectar_windows(self):
        """Usa impresora de Windows"""
        try:
            printer_name = self.config.get('printer_windows_name', '')
            if not printer_name:
                # Usar impresora por defecto
                printer_name = win32print.GetDefaultPrinter()
            
            return printer_name
            
        except Exception as e:
            raise Exception(f"Error conectando impresora Windows: {e}")
    
    def _conectar_archivo(self):
        """Conecta impresora a archivo (para testing)"""
        try:
            temp_file = os.path.join(tempfile.gettempdir(), "pos_printer_output.txt")
            printer = File(temp_file)
            return printer
        except Exception as e:
            raise Exception(f"Error creando archivo de impresión: {e}")

class TicketFormatter:
    """Formateador de tickets"""
    
    def __init__(self, config: PrinterConfig):
        self.config = config.config
        self.chars_per_line = int(self.config.get('printer_chars_per_line', '32'))
        self.paper_width = int(self.config.get('printer_paper_width', '58'))
    
    def formatear_linea_centrada(self, texto: str) -> str:
        """Centra texto en la línea"""
        if len(texto) >= self.chars_per_line:
            return texto[:self.chars_per_line]
        
        espacios = (self.chars_per_line - len(texto)) // 2
        return ' ' * espacios + texto
    
    def formatear_linea_justificada(self, izquierda: str, derecha: str) -> str:
        """Justifica texto a izquierda y derecha"""
        total_chars = len(izquierda) + len(derecha)
        
        if total_chars >= self.chars_per_line:
            # Truncar si es muy largo
            izq_max = self.chars_per_line - len(derecha) - 1
            izquierda = izquierda[:izq_max]
        
        espacios = self.chars_per_line - len(izquierda) - len(derecha)
        return izquierda + ' ' * espacios + derecha
    
    def formatear_separador(self, caracter: str = '-') -> str:
        """Crea línea separadora"""
        return caracter * self.chars_per_line
    
    def formatear_item_producto(self, nombre: str, cantidad: float, precio: float, subtotal: float) -> List[str]:
        """Formatea línea de producto"""
        lineas = []
        
        # Primera línea: nombre del producto
        if len(nombre) > self.chars_per_line:
            lineas.append(nombre[:self.chars_per_line])
            if len(nombre) > self.chars_per_line:
                lineas.append(nombre[self.chars_per_line:self.chars_per_line*2])
        else:
            lineas.append(nombre)
        
        # Segunda línea: cantidad x precio = subtotal
        cantidad_str = f"{cantidad:.0f}" if cantidad == int(cantidad) else f"{cantidad:.2f}"
        precio_str = f"₡{precio:,.2f}"
        subtotal_str = f"₡{subtotal:,.2f}"
        
        linea_detalle = f"{cantidad_str}x {precio_str}"
        linea_completa = self.formatear_linea_justificada(linea_detalle, subtotal_str)
        lineas.append(linea_completa)
        
        return lineas

class TicketPrinter:
    """Impresora de tickets principal"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = PrinterConfig()
        self.connector = PrinterConnector(self.config)
        self.formatter = TicketFormatter(self.config)
    
    def imprimir_ticket_venta(self, datos_venta: Dict[str, Any], config_tienda: Optional[ConfigTienda] = None) -> Tuple[bool, str]:
        """Imprime ticket de venta"""
        try:
            # Verificar que ESC/POS esté disponible
            if not ESC_POS_AVAILABLE:
                return self._imprimir_ticket_texto(datos_venta, config_tienda)
            
            printer = self.connector.obtener_impresora()
            
            # Configurar impresora
            if hasattr(printer, 'set'):
                printer.set(align='center', text_type='B', width=2, height=2)
            
            # Encabezado
            self._imprimir_encabezado(printer, config_tienda)
            
            # Información de venta
            self._imprimir_info_venta(printer, datos_venta)
            
            # Items
            self._imprimir_items(printer, datos_venta.get('items', []))
            
            # Totales
            self._imprimir_totales(printer, datos_venta.get('totales', {}))
            
            # Métodos de pago
            if 'pagos' in datos_venta and datos_venta['pagos']:
                self._imprimir_pagos(printer, datos_venta['pagos'])
            
            # Pie de página
            self._imprimir_pie_pagina(printer)
            
            # Configuraciones finales
            if hasattr(printer, 'cut') and self.config.config.get('printer_cut_paper', 'True') == 'True':
                printer.cut()
            
            if hasattr(printer, 'cashdraw') and self.config.config.get('printer_open_drawer', 'True') == 'True':
                printer.cashdraw(2)
            
            self.logger.info("Ticket impreso exitosamente")
            return True, "Ticket impreso correctamente"
            
        except Exception as e:
            error_msg = f"Error imprimiendo ticket: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _imprimir_encabezado(self, printer, config_tienda: Optional[ConfigTienda]):
        """Imprime encabezado del ticket"""
        try:
            if hasattr(printer, 'set'):
                printer.set(align='center', text_type='B')
            
            if config_tienda:
                if hasattr(printer, 'text'):
                    printer.text(f"{config_tienda.nombre}\n")
                    if config_tienda.direccion:
                        printer.text(f"{config_tienda.direccion}\n")
                    if config_tienda.telefono:
                        printer.text(f"Tel: {config_tienda.telefono}\n")
                    if config_tienda.identificacion:
                        tipo_id = "Cédula Jurídica" if config_tienda.tipo_identificacion.value == "02" else "Identificación"
                        printer.text(f"{tipo_id}: {config_tienda.identificacion}\n")
                    if config_tienda.correo:
                        printer.text(f"Email: {config_tienda.correo}\n")
            else:
                if hasattr(printer, 'text'):
                    printer.text("CajaCentralPOS\n")
                    printer.text("Sistema de Punto de Venta\n")
            
            if hasattr(printer, 'text'):
                printer.text("\n")
            
        except Exception as e:
            self.logger.warning(f"Error imprimiendo encabezado: {e}")
    
    def _imprimir_info_venta(self, printer, datos_venta: Dict[str, Any]):
        """Imprime información básica de la venta"""
        try:
            if hasattr(printer, 'set'):
                printer.set(align='left', text_type='A')
            
            if hasattr(printer, 'text'):
                fecha = datos_venta.get('fecha', datetime.now())
                if isinstance(fecha, str):
                    printer.text(f"Fecha: {fecha}\n")
                else:
                    printer.text(f"Fecha: {fecha.strftime('%d/%m/%Y %H:%M')}\n")
                
                printer.text(f"Ticket: {datos_venta.get('numero_venta', 'N/A')}\n")
                printer.text(f"Cajero: {datos_venta.get('vendedor', 'N/A')}\n")
                
                if datos_venta.get('cliente_nombre'):
                    printer.text(f"Cliente: {datos_venta['cliente_nombre']}\n")
                
                printer.text(self.formatter.formatear_separador() + "\n")
            
        except Exception as e:
            self.logger.warning(f"Error imprimiendo info venta: {e}")
    
    def _imprimir_items(self, printer, items: List[Dict[str, Any]]):
        """Imprime items de la venta"""
        try:
            if not items:
                return
            
            if hasattr(printer, 'set'):
                printer.set(align='left', text_type='A')
            
            for item in items:
                nombre = item.get('nombre', item.get('producto_nombre', 'Producto'))
                cantidad = float(item.get('cantidad', 0))
                precio = float(item.get('precio', item.get('precio_unitario', 0)))
                subtotal = float(item.get('subtotal', item.get('total_item', 0)))
                
                lineas = self.formatter.formatear_item_producto(nombre, cantidad, precio, subtotal)
                
                if hasattr(printer, 'text'):
                    for linea in lineas:
                        printer.text(linea + "\n")
            
            if hasattr(printer, 'text'):
                printer.text(self.formatter.formatear_separador() + "\n")
            
        except Exception as e:
            self.logger.warning(f"Error imprimiendo items: {e}")
    
    def _imprimir_totales(self, printer, totales: Dict[str, Any]):
        """Imprime totales de la venta"""
        try:
            if hasattr(printer, 'set'):
                printer.set(align='right', text_type='A')
            
            if hasattr(printer, 'text'):
                subtotal = float(totales.get('subtotal', totales.get('subtotal_neto', 0)))
                impuesto = float(totales.get('impuesto', totales.get('impuestos', 0)))
                descuento = float(totales.get('descuento', totales.get('descuento_general', 0)))
                total = float(totales.get('total', 0))
                
                if subtotal > 0:
                    printer.text(f"Subtotal: ₡{subtotal:,.2f}\n")
                
                if descuento > 0:
                    printer.text(f"Descuento: -₡{descuento:,.2f}\n")
                
                if impuesto > 0:
                    printer.text(f"IVA (13%): ₡{impuesto:,.2f}\n")
                
                # Total en negrita
                if hasattr(printer, 'set'):
                    printer.set(text_type='B')
                printer.text(f"TOTAL: ₡{total:,.2f}\n")
                
                if hasattr(printer, 'set'):
                    printer.set(text_type='A')
            
        except Exception as e:
            self.logger.warning(f"Error imprimiendo totales: {e}")
    
    def _imprimir_pagos(self, printer, pagos: List[Dict[str, Any]]):
        """Imprime métodos de pago"""
        try:
            if hasattr(printer, 'text'):
                printer.text("\nFormas de pago:\n")
            
            if hasattr(printer, 'set'):
                printer.set(align='left', text_type='A')
            
            for pago in pagos:
                metodo = pago.get('metodo_pago', pago.get('method', 'Efectivo'))
                monto = float(pago.get('monto', pago.get('amount', 0)))
                referencia = pago.get('referencia', pago.get('reference', ''))
                
                linea_pago = f"  {metodo}: ₡{monto:,.2f}"
                if referencia:
                    linea_pago += f" (Ref: {referencia})"
                
                if hasattr(printer, 'text'):
                    printer.text(linea_pago + "\n")
            
        except Exception as e:
            self.logger.warning(f"Error imprimiendo pagos: {e}")
    
    def _imprimir_pie_pagina(self, printer):
        """Imprime pie de página"""
        try:
            if hasattr(printer, 'set'):
                printer.set(align='center', text_type='A')
            
            if hasattr(printer, 'text'):
                printer.text("\n" + self.formatter.formatear_separador() + "\n")
                printer.text("¡Gracias por su compra!\n")
                printer.text("Vuelva pronto\n")
                printer.text(f"\nSistema: CajaCentralPOS\n")
                printer.text(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                printer.text("\n\n")
            
        except Exception as e:
            self.logger.warning(f"Error imprimiendo pie de página: {e}")
    
    def _imprimir_ticket_texto(self, datos_venta: Dict[str, Any], config_tienda: Optional[ConfigTienda]) -> Tuple[bool, str]:
        """Fallback: imprime ticket como archivo de texto"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ticket_{timestamp}.txt"
            filepath = os.path.join(tempfile.gettempdir(), filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                # Encabezado
                f.write("=" * 40 + "\n")
                if config_tienda:
                    f.write(f"{config_tienda.nombre}\n")
                    f.write(f"{config_tienda.direccion}\n")
                    f.write(f"Tel: {config_tienda.telefono}\n")
                else:
                    f.write("CajaCentralPOS\n")
                
                f.write("=" * 40 + "\n")
                
                # Info venta
                fecha = datos_venta.get('fecha', datetime.now())
                f.write(f"Fecha: {fecha}\n")
                f.write(f"Ticket: {datos_venta.get('numero_venta', 'N/A')}\n")
                f.write(f"Cajero: {datos_venta.get('vendedor', 'N/A')}\n")
                f.write("-" * 40 + "\n")
                
                # Items
                for item in datos_venta.get('items', []):
                    nombre = item.get('nombre', 'Producto')
                    cantidad = item.get('cantidad', 0)
                    precio = item.get('precio', 0)
                    subtotal = item.get('subtotal', 0)
                    
                    f.write(f"{nombre}\n")
                    f.write(f"{cantidad} x ₡{precio:,.2f} = ₡{subtotal:,.2f}\n")
                
                f.write("-" * 40 + "\n")
                
                # Totales
                totales = datos_venta.get('totales', {})
                total = totales.get('total', 0)
                f.write(f"TOTAL: ₡{total:,.2f}\n")
                
                f.write("=" * 40 + "\n")
                f.write("¡Gracias por su compra!\n")
            
            # Intentar abrir el archivo
            if platform.system() == "Windows":
                os.startfile(filepath)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", filepath])
            else:  # Linux
                subprocess.call(["xdg-open", filepath])
            
            return True, f"Ticket guardado en: {filepath}"
            
        except Exception as e:
            return False, f"Error creando ticket de texto: {e}"
    
    def probar_impresora(self) -> Tuple[bool, str]:
        """Prueba la conexión de la impresora"""
        try:
            printer = self.connector.obtener_impresora()
            
            if hasattr(printer, 'text'):
                if hasattr(printer, 'set'):
                    printer.set(align='center', text_type='B')
                
                printer.text("PRUEBA DE IMPRESORA\n")
                printer.text("CajaCentralPOS\n")
                printer.text(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                printer.text("\nPrueba exitosa!\n\n")
                
                if hasattr(printer, 'cut'):
                    printer.cut()
            
            return True, "Prueba de impresión exitosa"
            
        except Exception as e:
            return False, f"Error en prueba de impresión: {e}"

class ReportPrinter:
    """Impresora de reportes"""
    
    def __init__(self):
        self.ticket_printer = TicketPrinter()
        self.logger = logging.getLogger(__name__)
    
    def imprimir_reporte_ventas_dia(self, datos_reporte: Dict[str, Any]) -> Tuple[bool, str]:
        """Imprime reporte de ventas del día"""
        try:
            # Convertir datos del reporte a formato de ticket
            datos_ticket = {
                'numero_venta': f"REPORTE-{datetime.now().strftime('%Y%m%d')}",
                'fecha': datetime.now(),
                'vendedor': datos_reporte.get('generado_por', 'Sistema'),
                'items': [],
                'totales': {
                    'total': datos_reporte.get('total_ingresos', 0)
                }
            }
            
            # Crear items del reporte como líneas de resumen
            resumen_items = [
                {'nombre': f"Ventas del día: {datos_reporte.get('fecha', datetime.now().strftime('%d/%m/%Y'))}", 'cantidad': '', 'precio': '', 'subtotal': ''},
                {'nombre': f"Total ventas: {datos_reporte.get('total_ventas', 0)}", 'cantidad': '', 'precio': '', 'subtotal': ''},
                {'nombre': f"Productos vendidos: {datos_reporte.get('productos_vendidos', 0)}", 'cantidad': '', 'precio': '', 'subtotal': ''},
                {'nombre': f"Ticket promedio: ₡{datos_reporte.get('ticket_promedio', 0):,.2f}", 'cantidad': '', 'precio': '', 'subtotal': ''}
            ]
            
            datos_ticket['items'] = resumen_items
            
            return self.ticket_printer.imprimir_ticket_venta(datos_ticket)
            
        except Exception as e:
            error_msg = f"Error imprimiendo reporte: {e}"
            self.logger.error(error_msg)
            return False, error_msg

# Instancias globales
ticket_printer = TicketPrinter()
report_printer = ReportPrinter()

# Función de compatibilidad con código existente
def imprimir_ticket(datos_venta_finalizada, usuario_actual, config_tienda=None):
    """Función de compatibilidad para código existente"""
    try:
        # Adaptar datos al nuevo formato
        datos_adaptados = {
            'numero_venta': datos_venta_finalizada.get('numero_venta', 'N/A'),
            'fecha': datos_venta_finalizada.get('fecha', datetime.now()),
            'vendedor': getattr(usuario_actual, 'nombre', 'N/A'),
            'items': datos_venta_finalizada.get('items_vendidos', datos_venta_finalizada.get('items', [])),
            'totales': datos_venta_finalizada.get('totales_calculados', datos_venta_finalizada.get('totales', {})),
            'pagos': datos_venta_finalizada.get('pagos', [])
        }
        
        success, message = ticket_printer.imprimir_ticket_venta(datos_adaptados, config_tienda)
        
        if not success:
            raise RuntimeError(message)
        
    except Exception as e:
        raise RuntimeError(f"No se pudo imprimir el ticket: {e}")