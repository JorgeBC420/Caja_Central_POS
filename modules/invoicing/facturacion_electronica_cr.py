"""
Módulo de Facturación Electrónica para Costa Rica
Sistema de generación de XML y PDF según normativas del Ministerio de Hacienda
Versión 4.4 - Compatible con régimen simplificado y tradicional
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, date
import uuid
import os
import hashlib
import base64
from decimal import Decimal, ROUND_UP
from fpdf import FPDF
import requests
import json
from typing import Dict, List, Optional, Tuple

class FacturacionElectronicaCR:
    """Sistema de facturación electrónica para Costa Rica"""
    
    def __init__(self, config: Dict = None):
        """Inicializar el sistema de facturación"""
        self.config = config or self.get_default_config()
        self.version_xml = "4.4"
        
        # URLs del Ministerio de Hacienda
        self.urls_hacienda = {
            'produccion': 'https://api.comprobanteselectronicos.go.cr/recepcion/v1/',
            'sandbox': 'https://api.comprobanteselectronicos.go.cr/recepcion-sandbox/v1/'
        }
        
        # Tipos de documento
        self.tipos_documento = {
            'factura_electronica': '01',
            'nota_debito': '02', 
            'nota_credito': '03',
            'tiquete_electronico': '04',
            'factura_compra': '08'
        }
        
        # Códigos de impuestos
        self.impuestos = {
            'iva_13': {'codigo': '01', 'tarifa': 13.00},
            'iva_4': {'codigo': '02', 'tarifa': 4.00},
            'iva_2': {'codigo': '03', 'tarifa': 2.00},
            'iva_1': {'codigo': '04', 'tarifa': 1.00},
            'exento': {'codigo': '07', 'tarifa': 0.00}
        }
    
    def get_default_config(self) -> Dict:
        """Configuración por defecto del sistema"""
        return {
            'empresa': {
                'nombre': 'Caja Central POS CR',
                'cedula': '3-101-123456',  # Cambiar por cédula real
                'telefono': '2222-3333',
                'email': 'facturacion@cajacentral.com',
                'direccion': 'San José, Costa Rica',
                'provincia': '1',
                'canton': '01', 
                'distrito': '01'
            },
            'certificado': {
                'archivo_p12': 'certificados/certificado.p12',
                'password': 'password_certificado',
                'pin': '1234'
            },
            'ambiente': 'sandbox',  # 'produccion' o 'sandbox'
            'regimen': 'simplificado',  # 'simplificado' o 'tradicional'
            'usuario_hacienda': 'usuario_api',
            'password_hacienda': 'password_api'
        }
    
    def generar_clave_numerica(self, tipo_documento: str, numero_consecutivo: str) -> str:
        """Genera la clave numérica de 50 dígitos"""
        fecha = datetime.now()
        
        # Formato: PPPDDMMAAAATTNNNNNNNNCS
        pais = "506"  # Costa Rica
        dia = fecha.strftime("%d")
        mes = fecha.strftime("%m") 
        año = fecha.strftime("%Y")
        cedula_emisor = self.config['empresa']['cedula'].replace('-', '').zfill(12)
        consecutivo = numero_consecutivo.zfill(20)
        situacion = "1"  # Normal
        codigo_seguridad = str(random.randint(10000000, 99999999))
        
        clave_base = f"{pais}{dia}{mes}{año}{cedula_emisor}{consecutivo}{situacion}{codigo_seguridad}"
        
        # Validar que tenga 50 dígitos
        if len(clave_base) != 50:
            # Ajustar si es necesario
            clave_base = clave_base[:50].ljust(50, '0')
        
        return clave_base
    
    def crear_xml_factura(self, datos_factura: Dict) -> str:
        """Crea el XML de la factura electrónica versión 4.4"""
        
        # Crear elemento raíz
        factura = ET.Element("FacturaElectronica")
        factura.set("xmlns", "https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica")
        factura.set("xmlns:ds", "http://www.w3.org/2000/09/xmldsig#")
        factura.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
        factura.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        
        # Clave
        clave = ET.SubElement(factura, "Clave")
        clave_numerica = self.generar_clave_numerica("01", datos_factura.get('numero', '1'))
        clave.text = clave_numerica
        
        # CodigoActividad
        codigo_actividad = ET.SubElement(factura, "CodigoActividad")
        codigo_actividad.text = datos_factura.get('codigo_actividad', '522001')
        
        # NumeroConsecutivo
        numero_consecutivo = ET.SubElement(factura, "NumeroConsecutivo")
        numero_consecutivo.text = f"00100001010000000{datos_factura.get('numero', '1').zfill(10)}"
        
        # FechaEmision
        fecha_emision = ET.SubElement(factura, "FechaEmision")
        fecha_emision.text = datetime.now().strftime("%Y-%m-%dT%H:%M:%S-06:00")
        
        # Emisor
        emisor = ET.SubElement(factura, "Emisor")
        self._agregar_datos_emisor(emisor)
        
        # Receptor (si existe)
        if datos_factura.get('cliente'):
            receptor = ET.SubElement(factura, "Receptor")
            self._agregar_datos_receptor(receptor, datos_factura['cliente'])
        
        # CondicionVenta
        condicion_venta = ET.SubElement(factura, "CondicionVenta")
        condicion_venta.text = datos_factura.get('condicion_venta', '01')  # Contado
        
        # PlazoCredito (si aplica)
        if datos_factura.get('condicion_venta') == '02':  # Crédito
            plazo_credito = ET.SubElement(factura, "PlazoCredito")
            plazo_credito.text = str(datos_factura.get('plazo_credito', 30))
        
        # MedioPago
        medio_pago = ET.SubElement(factura, "MedioPago")
        medio_pago.text = datos_factura.get('medio_pago', '01')  # Efectivo
        
        # DetalleServicio
        detalle_servicio = ET.SubElement(factura, "DetalleServicio")
        self._agregar_lineas_detalle(detalle_servicio, datos_factura.get('lineas', []))
        
        # OtrosCargos (si aplica)
        if datos_factura.get('otros_cargos'):
            otros_cargos = ET.SubElement(factura, "OtrosCargos")
            self._agregar_otros_cargos(otros_cargos, datos_factura['otros_cargos'])
        
        # ResumenFactura
        resumen_factura = ET.SubElement(factura, "ResumenFactura")
        self._agregar_resumen_factura(resumen_factura, datos_factura)
        
        # Información de referencia (si es nota)
        if datos_factura.get('documento_referencia'):
            info_referencia = ET.SubElement(factura, "InformacionReferencia")
            self._agregar_info_referencia(info_referencia, datos_factura['documento_referencia'])
        
        # Normativa
        normativa = ET.SubElement(factura, "Normativa")
        numero_resolucion = ET.SubElement(normativa, "NumeroResolucion")
        numero_resolucion.text = "DGT-R-48-2016"
        fecha_resolucion = ET.SubElement(normativa, "FechaResolucion")
        fecha_resolucion.text = "2016-07-04T00:00:00-06:00"
        
        # Otros datos específicos
        otros = ET.SubElement(factura, "Otros")
        otros_contenido = ET.SubElement(otros, "OtroContenido")
        otros_contenido.text = f"Generado por Caja Central POS CR v1.0 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self._formatear_xml(factura)
    
    def _agregar_datos_emisor(self, emisor_element: ET.Element):
        """Agrega los datos del emisor al XML"""
        empresa = self.config['empresa']
        
        nombre = ET.SubElement(emisor_element, "Nombre")
        nombre.text = empresa['nombre']
        
        identificacion = ET.SubElement(emisor_element, "Identificacion")
        tipo_id = ET.SubElement(identificacion, "Tipo")
        tipo_id.text = "02"  # Cédula jurídica
        numero_id = ET.SubElement(identificacion, "Numero")
        numero_id.text = empresa['cedula'].replace('-', '')
        
        nombre_comercial = ET.SubElement(emisor_element, "NombreComercial")
        nombre_comercial.text = empresa.get('nombre_comercial', empresa['nombre'])
        
        ubicacion = ET.SubElement(emisor_element, "Ubicacion")
        provincia = ET.SubElement(ubicacion, "Provincia")
        provincia.text = empresa['provincia']
        canton = ET.SubElement(ubicacion, "Canton")
        canton.text = empresa['canton']
        distrito = ET.SubElement(ubicacion, "Distrito")
        distrito.text = empresa['distrito']
        otras_senas = ET.SubElement(ubicacion, "OtrasSenas")
        otras_senas.text = empresa['direccion']
        
        telefono = ET.SubElement(emisor_element, "Telefono")
        codigo_pais = ET.SubElement(telefono, "CodigoPais")
        codigo_pais.text = "506"
        num_telefono = ET.SubElement(telefono, "NumTelefono")
        num_telefono.text = empresa['telefono'].replace('-', '')
        
        correo = ET.SubElement(emisor_element, "CorreoElectronico")
        correo.text = empresa['email']
    
    def _agregar_datos_receptor(self, receptor_element: ET.Element, cliente: Dict):
        """Agrega los datos del receptor al XML"""
        nombre = ET.SubElement(receptor_element, "Nombre")
        nombre.text = cliente.get('nombre', 'Cliente Contado')
        
        if cliente.get('cedula'):
            identificacion = ET.SubElement(receptor_element, "Identificacion")
            tipo_id = ET.SubElement(identificacion, "Tipo")
            tipo_id.text = cliente.get('tipo_identificacion', '01')  # Física
            numero_id = ET.SubElement(identificacion, "Numero")
            numero_id.text = cliente['cedula'].replace('-', '')
        
        if cliente.get('direccion'):
            ubicacion = ET.SubElement(receptor_element, "Ubicacion")
            provincia = ET.SubElement(ubicacion, "Provincia")
            provincia.text = cliente.get('provincia', '1')
            canton = ET.SubElement(ubicacion, "Canton")
            canton.text = cliente.get('canton', '01')
            distrito = ET.SubElement(ubicacion, "Distrito")
            distrito.text = cliente.get('distrito', '01')
            otras_senas = ET.SubElement(ubicacion, "OtrasSenas")
            otras_senas.text = cliente['direccion']
        
        if cliente.get('telefono'):
            telefono = ET.SubElement(receptor_element, "Telefono")
            codigo_pais = ET.SubElement(telefono, "CodigoPais")
            codigo_pais.text = "506"
            num_telefono = ET.SubElement(telefono, "NumTelefono")
            num_telefono.text = cliente['telefono'].replace('-', '')
        
        if cliente.get('email'):
            correo = ET.SubElement(receptor_element, "CorreoElectronico")
            correo.text = cliente['email']
    
    def _agregar_lineas_detalle(self, detalle_element: ET.Element, lineas: List[Dict]):
        """Agrega las líneas de detalle al XML"""
        for i, linea in enumerate(lineas, 1):
            linea_detalle = ET.SubElement(detalle_element, "LineaDetalle")
            linea_detalle.set("numeroLinea", str(i))
            
            # Código del producto/servicio
            if linea.get('codigo'):
                codigo = ET.SubElement(linea_detalle, "Codigo")
                tipo_codigo = ET.SubElement(codigo, "Tipo")
                tipo_codigo.text = "04"  # Código del vendedor
                codigo_valor = ET.SubElement(codigo, "Codigo")
                codigo_valor.text = linea['codigo']
            
            # Cantidad
            cantidad = ET.SubElement(linea_detalle, "Cantidad")
            cantidad.text = str(linea.get('cantidad', 1))
            
            # Unidad de medida
            unidad_medida = ET.SubElement(linea_detalle, "UnidadMedida")
            unidad_medida.text = linea.get('unidad_medida', 'Unid')
            
            # Detalle
            detalle = ET.SubElement(linea_detalle, "Detalle")
            detalle.text = linea.get('descripcion', 'Producto')
            
            # Precio unitario
            precio_unitario = ET.SubElement(linea_detalle, "PrecioUnitario")
            precio_unitario.text = f"{linea.get('precio_unitario', 0):.5f}"
            
            # Monto total
            monto_total = ET.SubElement(linea_detalle, "MontoTotal")
            total = Decimal(str(linea.get('cantidad', 1))) * Decimal(str(linea.get('precio_unitario', 0)))
            monto_total.text = f"{total:.5f}"
            
            # Descuento (si aplica)
            if linea.get('descuento', 0) > 0:
                descuento = ET.SubElement(linea_detalle, "Descuento")
                monto_descuento = ET.SubElement(descuento, "MontoDescuento")
                monto_desc = total * Decimal(str(linea['descuento'])) / 100
                monto_descuento.text = f"{monto_desc:.5f}"
                naturaleza_desc = ET.SubElement(descuento, "NaturalezaDescuento")
                naturaleza_desc.text = "Descuento comercial"
            
            # Subtotal
            subtotal = ET.SubElement(linea_detalle, "SubTotal")
            subtotal_valor = total - (total * Decimal(str(linea.get('descuento', 0))) / 100)
            subtotal.text = f"{subtotal_valor:.5f}"
            
            # Impuestos
            impuestos = ET.SubElement(linea_detalle, "Impuesto")
            codigo_imp = ET.SubElement(impuestos, "Codigo")
            codigo_imp.text = linea.get('codigo_impuesto', '01')  # IVA por defecto
            codigo_tarifa = ET.SubElement(impuestos, "CodigoTarifa")
            codigo_tarifa.text = "08"  # Tarifa general
            tarifa = ET.SubElement(impuestos, "Tarifa")
            tarifa_valor = linea.get('tarifa_impuesto', 13.00)
            tarifa.text = f"{tarifa_valor:.2f}"
            monto_imp = ET.SubElement(impuestos, "Monto")
            monto_impuesto = subtotal_valor * Decimal(str(tarifa_valor)) / 100
            monto_imp.text = f"{monto_impuesto:.5f}"
            
            # Monto total línea
            monto_total_linea = ET.SubElement(linea_detalle, "MontoTotalLinea")
            total_linea = subtotal_valor + monto_impuesto
            monto_total_linea.text = f"{total_linea:.5f}"
    
    def _agregar_resumen_factura(self, resumen_element: ET.Element, datos_factura: Dict):
        """Agrega el resumen de la factura al XML"""
        lineas = datos_factura.get('lineas', [])
        
        # Calcular totales
        subtotal_gravado = Decimal('0')
        subtotal_exento = Decimal('0')
        total_descuentos = Decimal('0')
        total_impuestos = Decimal('0')
        
        for linea in lineas:
            cantidad = Decimal(str(linea.get('cantidad', 1)))
            precio = Decimal(str(linea.get('precio_unitario', 0)))
            descuento_pct = Decimal(str(linea.get('descuento', 0)))
            tarifa_imp = Decimal(str(linea.get('tarifa_impuesto', 13.00)))
            
            subtotal_linea = cantidad * precio
            descuento_linea = subtotal_linea * descuento_pct / 100
            neto_linea = subtotal_linea - descuento_linea
            impuesto_linea = neto_linea * tarifa_imp / 100
            
            if tarifa_imp > 0:
                subtotal_gravado += neto_linea
            else:
                subtotal_exento += neto_linea
            
            total_descuentos += descuento_linea
            total_impuestos += impuesto_linea
        
        # Código de moneda
        codigo_moneda = ET.SubElement(resumen_element, "CodigoTipoMoneda")
        codigo_moneda.set("CodigoMoneda", "CRC")
        codigo_moneda.set("TipoCambio", "1.00000")
        codigo_moneda.text = "CRC"
        
        # Totales de servicios gravados
        if subtotal_gravado > 0:
            total_serv_gravados = ET.SubElement(resumen_element, "TotalServGravados")
            total_serv_gravados.text = f"{subtotal_gravado:.5f}"
        
        # Totales de servicios exentos
        if subtotal_exento > 0:
            total_serv_exentos = ET.SubElement(resumen_element, "TotalServExentos")
            total_serv_exentos.text = f"{subtotal_exento:.5f}"
        
        # Total de descuentos
        if total_descuentos > 0:
            total_desc = ET.SubElement(resumen_element, "TotalDescuentos")
            total_desc.text = f"{total_descuentos:.5f}"
        
        # Total gravado
        total_gravado = ET.SubElement(resumen_element, "TotalGravado")
        total_gravado.text = f"{subtotal_gravado:.5f}"
        
        # Total exento
        total_exento = ET.SubElement(resumen_element, "TotalExento")
        total_exento.text = f"{subtotal_exento:.5f}"
        
        # Total de impuestos
        total_imp = ET.SubElement(resumen_element, "TotalImpuesto")
        total_imp.text = f"{total_impuestos:.5f}"
        
        # IVA devuelto (si aplica)
        iva_devuelto = ET.SubElement(resumen_element, "TotalIVADevuelto")
        iva_devuelto.text = "0.00000"
        
        # Otros cargos (si aplica)
        otros_cargos = ET.SubElement(resumen_element, "TotalOtrosCargos")
        otros_cargos.text = "0.00000"
        
        # Total comprobante
        total_comprobante = ET.SubElement(resumen_element, "TotalComprobante")
        total_final = subtotal_gravado + subtotal_exento + total_impuestos
        total_comprobante.text = f"{total_final:.5f}"
    
    def _formatear_xml(self, elemento: ET.Element) -> str:
        """Formatea el XML con indentación"""
        rough_string = ET.tostring(elemento, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding=None)
    
    def generar_pdf_factura(self, datos_factura: Dict, nombre_archivo: str = None) -> str:
        """Genera el PDF de la factura"""
        
        if not nombre_archivo:
            fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"factura_{datos_factura.get('numero', '1')}_{fecha}.pdf"
        
        # Crear PDF
        pdf = FacturaPDF()
        pdf.add_page()
        
        # Configurar datos de la empresa
        pdf.set_empresa_data(self.config['empresa'])
        
        # Header de la factura
        pdf.header_factura(datos_factura)
        
        # Datos del cliente
        if datos_factura.get('cliente'):
            pdf.datos_cliente(datos_factura['cliente'])
        
        # Líneas de detalle
        pdf.tabla_productos(datos_factura.get('lineas', []))
        
        # Totales
        pdf.totales_factura(datos_factura)
        
        # Información legal
        pdf.info_legal()
        
        # Guardar archivo
        ruta_completa = os.path.join('facturas', nombre_archivo)
        os.makedirs('facturas', exist_ok=True)
        pdf.output(ruta_completa, 'F')
        
        return ruta_completa
    
    def generar_pdf_v44(self, datos_factura: Dict, nombre_archivo: str = None) -> str:
        """
        Genera factura en PDF versión 4.4 - Formato mejorado para contadores
        Compatible con requisitos de Hacienda Costa Rica
        """
        
        if not nombre_archivo:
            fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
            numero = datos_factura.get('numero', '001-001-00000001')
            nombre_archivo = f"factura_v44_{numero.replace('-', '_')}_{fecha}.pdf"
        
        # Crear PDF con formato A4
        pdf = FPDF('P', 'mm', 'A4')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # ENCABEZADO PRINCIPAL
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 12, 'FACTURA ELECTRÓNICA - VERSIÓN 4.4', 0, 1, 'C')
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(0, 1, '', 0, 1, 'C', True)
        pdf.ln(8)
        
        # INFORMACIÓN EMPRESARIAL
        empresa = datos_factura.get('empresa', {})
        
        # Logo y nombre empresa (lado izquierdo)
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(100, 10, empresa.get('nombre', 'EMPRESA S.A.'), 0, 0, 'L')
        
        # Información de factura (lado derecho)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(90, 10, f"FACTURA No: {datos_factura.get('numero', '001-001-00000001')}", 0, 1, 'R')
        
        # Datos empresa - columna izquierda
        pdf.set_font('Arial', '', 11)
        pdf.cell(100, 6, f"Cédula Jurídica: {empresa.get('cedula', '3-101-123456')}", 0, 0, 'L')
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(90, 6, f"Fecha: {datos_factura.get('fecha', datetime.now().strftime('%d/%m/%Y'))}", 0, 1, 'R')
        
        pdf.set_font('Arial', '', 11)
        pdf.cell(100, 6, f"Teléfono: {empresa.get('telefono', '2222-3333')}", 0, 0, 'L')
        pdf.cell(90, 6, f"Hora: {datos_factura.get('hora', datetime.now().strftime('%H:%M:%S'))}", 0, 1, 'R')
        
        pdf.cell(100, 6, f"Email: {empresa.get('email', 'info@empresa.co.cr')}", 0, 0, 'L')
        pdf.cell(90, 6, f"Tipo: {datos_factura.get('tipo_documento', 'Factura Electrónica')}", 0, 1, 'R')
        
        pdf.cell(100, 6, f"Actividad: {empresa.get('actividad', 'Comercio al por menor')}", 0, 0, 'L')
        pdf.cell(90, 6, f"Moneda: {datos_factura.get('moneda', 'Colones (CRC)')}", 0, 1, 'R')
        
        # Dirección completa
        direccion = empresa.get('direccion', 'San José, Costa Rica')
        pdf.cell(190, 6, f"Dirección: {direccion}", 0, 1, 'L')
        
        pdf.ln(10)
        
        # INFORMACIÓN DEL CLIENTE
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 8, 'INFORMACIÓN DEL CLIENTE', 0, 1, 'L')
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(0, 1, '', 0, 1, 'C', True)
        pdf.ln(5)
        
        cliente = datos_factura.get('cliente', {})
        pdf.set_font('Arial', '', 11)
        pdf.cell(100, 6, f"Cliente: {cliente.get('nombre', 'Cliente General')}", 0, 0, 'L')
        pdf.cell(90, 6, f"Identificación: {cliente.get('cedula', 'N/A')}", 0, 1, 'R')
        
        pdf.cell(100, 6, f"Teléfono: {cliente.get('telefono', 'N/A')}", 0, 0, 'L')
        pdf.cell(90, 6, f"Email: {cliente.get('email', 'N/A')}", 0, 1, 'R')
        
        pdf.cell(190, 6, f"Dirección: {cliente.get('direccion', 'N/A')}", 0, 1, 'L')
        
        pdf.ln(10)
        
        # TABLA DE PRODUCTOS V4.4
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'DETALLE DE PRODUCTOS Y SERVICIOS V4.4', 0, 1, 'L')
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(0, 1, '', 0, 1, 'C', True)
        pdf.ln(3)
        
        # Encabezados de tabla
        pdf.set_font('Arial', 'B', 9)
        headers = ['Código', 'Descripción', 'Cant.', 'P.Unit', 'Desc.%', 'IVA%', 'Subtotal', 'Total']
        widths = [22, 58, 18, 22, 18, 18, 26, 28]
        
        # Fondo de encabezados
        pdf.set_fill_color(220, 220, 220)
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            pdf.cell(width, 8, header, 1, 0, 'C', True)
        pdf.ln()
        
        # Productos
        productos = datos_factura.get('lineas', [])
        if not productos:
            # Producto de ejemplo
            productos = [{
                'codigo': '001',
                'descripcion': 'Producto de ejemplo',
                'cantidad': 1,
                'precio_unitario': 10000,
                'descuento_porcentaje': 0,
                'impuesto_porcentaje': 13
            }]
        
        pdf.set_font('Arial', '', 9)
        pdf.set_fill_color(255, 255, 255)
        
        subtotal_general = 0
        descuento_general = 0
        impuesto_general = 0
        total_general = 0
        
        for i, producto in enumerate(productos):
            # Alternar color de filas
            if i % 2 == 0:
                pdf.set_fill_color(248, 248, 248)
            else:
                pdf.set_fill_color(255, 255, 255)
            
            # Calcular valores
            cantidad = float(producto.get('cantidad', 1))
            precio_unit = float(producto.get('precio_unitario', 0))
            descuento_pct = float(producto.get('descuento_porcentaje', 0))
            impuesto_pct = float(producto.get('impuesto_porcentaje', 13))
            
            subtotal = cantidad * precio_unit
            descuento_monto = subtotal * (descuento_pct / 100)
            base_impuesto = subtotal - descuento_monto
            impuesto_monto = base_impuesto * (impuesto_pct / 100)
            total_linea = base_impuesto + impuesto_monto
            
            # Acumular totales
            subtotal_general += subtotal
            descuento_general += descuento_monto
            impuesto_general += impuesto_monto
            total_general += total_linea
            
            # Datos de la fila
            codigo = str(producto.get('codigo', ''))[:10]
            descripcion = str(producto.get('descripcion', ''))
            if len(descripcion) > 28:
                descripcion = descripcion[:25] + "..."
            
            values = [
                codigo,
                descripcion,
                f"{cantidad:.0f}",
                f"₡{precio_unit:,.0f}",
                f"{descuento_pct:.1f}%",
                f"{impuesto_pct:.1f}%",
                f"₡{base_impuesto:,.0f}",
                f"₡{total_linea:,.0f}"
            ]
            
            # Dibujar fila
            for j, (value, width) in enumerate(zip(values, widths)):
                align = 'C'
                if j == 1:  # Descripción alineada a la izquierda
                    align = 'L'
                elif j >= 3:  # Números alineados a la derecha
                    align = 'R'
                pdf.cell(width, 7, value, 1, 0, align, True)
            pdf.ln()
        
        pdf.ln(8)
        
        # RESUMEN FINANCIERO V4.4
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 8, 'RESUMEN FINANCIERO VERSIÓN 4.4', 0, 1, 'L')
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(0, 1, '', 0, 1, 'C', True)
        pdf.ln(5)
        
        # Tabla de totales
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(110, 8, '', 0, 0)  # Espacio
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(40, 8, 'Concepto', 1, 0, 'C', True)
        pdf.cell(40, 8, 'Monto', 1, 1, 'C', True)
        
        pdf.set_font('Arial', '', 11)
        pdf.set_fill_color(255, 255, 255)
        
        # Subtotal
        pdf.cell(110, 7, '', 0, 0)
        pdf.cell(40, 7, 'Subtotal', 1, 0, 'L', True)
        pdf.cell(40, 7, f"₡{subtotal_general:,.2f}", 1, 1, 'R', True)
        
        # Descuento
        pdf.cell(110, 7, '', 0, 0)
        pdf.cell(40, 7, 'Descuento', 1, 0, 'L', True)
        pdf.cell(40, 7, f"₡{descuento_general:,.2f}", 1, 1, 'R', True)
        
        # Base gravable
        base_gravable = subtotal_general - descuento_general
        pdf.cell(110, 7, '', 0, 0)
        pdf.cell(40, 7, 'Base Gravable', 1, 0, 'L', True)
        pdf.cell(40, 7, f"₡{base_gravable:,.2f}", 1, 1, 'R', True)
        
        # IVA
        pdf.cell(110, 7, '', 0, 0)
        pdf.cell(40, 7, 'IVA (13%)', 1, 0, 'L', True)
        pdf.cell(40, 7, f"₡{impuesto_general:,.2f}", 1, 1, 'R', True)
        
        # Total final
        pdf.set_font('Arial', 'B', 12)
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(110, 10, '', 0, 0)
        pdf.cell(40, 10, 'TOTAL FACTURA', 1, 0, 'C', True)
        pdf.cell(40, 10, f"₡{total_general:,.2f}", 1, 1, 'R', True)
        
        pdf.ln(10)
        
        # INFORMACIÓN TÉCNICA V4.4
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 6, 'INFORMACIÓN TÉCNICA VERSIÓN 4.4', 0, 1, 'L')
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(0, 1, '', 0, 1, 'C', True)
        pdf.ln(3)
        
        pdf.set_font('Arial', '', 10)
        
        # Información técnica en dos columnas
        pdf.cell(95, 5, f"Clave Numérica: {datos_factura.get('clave_numerica', 'N/A')[:25]}...", 0, 0, 'L')
        pdf.cell(95, 5, f"Consecutivo: {datos_factura.get('consecutivo', '001-001-01-00000001')}", 0, 1, 'L')
        
        pdf.cell(95, 5, f"Condición de Venta: {datos_factura.get('condicion_venta', 'Contado')}", 0, 0, 'L')
        pdf.cell(95, 5, f"Medio de Pago: {datos_factura.get('medio_pago', 'Efectivo')}", 0, 1, 'L')
        
        pdf.cell(95, 5, f"Tipo de Cambio: ₡{datos_factura.get('tipo_cambio', '590.00')}", 0, 0, 'L')
        pdf.cell(95, 5, f"Régimen: {datos_factura.get('regimen', 'Régimen Simplificado')}", 0, 1, 'L')
        
        pdf.cell(95, 5, f"Resolución DGT: {datos_factura.get('resolucion_dgt', 'DGT-R-48-2016')}", 0, 0, 'L')
        pdf.cell(95, 5, f"Vigencia: {datos_factura.get('vigencia_resolucion', '07/10/2016')}", 0, 1, 'L')
        
        pdf.ln(8)
        
        # PIE DE PÁGINA V4.4
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 5, 'INFORMACIÓN LEGAL - VERSIÓN 4.4', 0, 1, 'C')
        pdf.set_font('Arial', '', 9)
        pdf.cell(0, 4, f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Sistema Caja Central POS v4.4", 0, 1, 'C')
        pdf.cell(0, 4, "Factura electrónica autorizada por la Dirección General de Tributación de Costa Rica", 0, 1, 'C')
        pdf.cell(0, 4, "Documento válido para efectos contables y tributarios según Ley 8454", 0, 1, 'C')
        
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(0, 4, 'TÉRMINOS Y CONDICIONES', 0, 1, 'C')
        pdf.set_font('Arial', '', 8)
        pdf.cell(0, 3, '• Esta factura cumple con la normativa vigente de facturación electrónica de Costa Rica', 0, 1, 'L')
        pdf.cell(0, 3, '• Para consultas, reclamos o soporte técnico comunicarse a los números indicados', 0, 1, 'L')
        pdf.cell(0, 3, f'• Conserve este documento para sus registros contables y declaraciones fiscales', 0, 1, 'L')
        
        # Guardar archivo
        ruta_completa = os.path.join('facturas', nombre_archivo)
        os.makedirs('facturas', exist_ok=True)
        pdf.output(ruta_completa, 'F')
        
        return ruta_completa
    
    def enviar_hacienda(self, xml_factura: str, clave_numerica: str) -> Dict:
        """Envía la factura al Ministerio de Hacienda"""
        
        ambiente = 'sandbox' if self.config['ambiente'] == 'sandbox' else 'produccion'
        url_base = self.urls_hacienda[ambiente]
        
        # Preparar datos para envío
        datos_envio = {
            'clave': clave_numerica,
            'fecha': datetime.now().strftime("%Y-%m-%dT%H:%M:%S-06:00"),
            'emisor': {
                'tipoIdentificacion': '02',
                'numeroIdentificacion': self.config['empresa']['cedula'].replace('-', '')
            },
            'comprobanteXml': base64.b64encode(xml_factura.encode('utf-8')).decode('utf-8')
        }
        
        # Headers
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self._obtener_token_acceso()}"
        }
        
        try:
            # Enviar a recepción
            response = requests.post(
                f"{url_base}recepcion",
                json=datos_envio,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 202:
                return {
                    'exito': True,
                    'mensaje': 'Factura enviada correctamente',
                    'clave': clave_numerica,
                    'fecha_recepcion': datetime.now().isoformat()
                }
            else:
                return {
                    'exito': False,
                    'error': f"Error {response.status_code}: {response.text}",
                    'clave': clave_numerica
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'exito': False,
                'error': f"Error de conexión: {str(e)}",
                'clave': clave_numerica
            }
    
    def _obtener_token_acceso(self) -> str:
        """Obtiene el token de acceso para la API de Hacienda"""
        # Implementar autenticación OAuth2 con el ATV
        # Por ahora retorna un token de ejemplo
        return "token_ejemplo_oauth2"
    
    def consultar_estado_factura(self, clave_numerica: str) -> Dict:
        """Consulta el estado de una factura en Hacienda"""
        ambiente = 'sandbox' if self.config['ambiente'] == 'sandbox' else 'produccion'
        url_base = self.urls_hacienda[ambiente]
        
        headers = {
            'Authorization': f"Bearer {self._obtener_token_acceso()}"
        }
        
        try:
            response = requests.get(
                f"{url_base}consultas/{clave_numerica}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'error': f"Error {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'error': f"Error de conexión: {str(e)}"
            }


class FacturaPDF(FPDF):
    """Clase para generar PDFs de facturas"""
    
    def __init__(self):
        super().__init__()
        self.empresa_data = {}
        
    def set_empresa_data(self, empresa: Dict):
        """Configura los datos de la empresa"""
        self.empresa_data = empresa
    
    def header(self):
        """Header del PDF"""
        # Logo (si existe)
        logo_path = os.path.join('assets', 'logo.png')
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 33)
        
        # Título
        self.set_font('Arial', 'B', 16)
        self.set_text_color(44, 62, 80)  # Color azul oscuro
        self.cell(0, 10, 'FACTURA ELECTRÓNICA', 0, 1, 'C')
        self.ln(5)
    
    def header_factura(self, datos_factura: Dict):
        """Header específico de la factura"""
        # Datos de la empresa
        self.set_font('Arial', 'B', 12)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, self.empresa_data.get('nombre', ''), 0, 1, 'L')
        
        self.set_font('Arial', '', 10)
        self.cell(0, 6, f"Cédula Jurídica: {self.empresa_data.get('cedula', '')}", 0, 1, 'L')
        self.cell(0, 6, f"Teléfono: {self.empresa_data.get('telefono', '')}", 0, 1, 'L')
        self.cell(0, 6, f"Email: {self.empresa_data.get('email', '')}", 0, 1, 'L')
        self.cell(0, 6, f"Dirección: {self.empresa_data.get('direccion', '')}", 0, 1, 'L')
        
        # Información de la factura
        self.ln(5)
        self.set_font('Arial', 'B', 11)
        self.cell(0, 8, f"Factura No: {datos_factura.get('numero', '1')}", 0, 1, 'R')
        self.cell(0, 6, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, 'R')
        
        if datos_factura.get('clave_numerica'):
            self.ln(3)
            self.set_font('Arial', '', 8)
            self.cell(0, 5, f"Clave Numérica: {datos_factura['clave_numerica']}", 0, 1, 'L')
        
        self.ln(10)
    
    def datos_cliente(self, cliente: Dict):
        """Datos del cliente"""
        self.set_font('Arial', 'B', 11)
        self.cell(0, 8, 'DATOS DEL CLIENTE:', 0, 1, 'L')
        
        self.set_font('Arial', '', 10)
        self.cell(0, 6, f"Nombre: {cliente.get('nombre', '')}", 0, 1, 'L')
        
        if cliente.get('cedula'):
            self.cell(0, 6, f"Cédula: {cliente.get('cedula', '')}", 0, 1, 'L')
        
        if cliente.get('telefono'):
            self.cell(0, 6, f"Teléfono: {cliente.get('telefono', '')}", 0, 1, 'L')
        
        if cliente.get('email'):
            self.cell(0, 6, f"Email: {cliente.get('email', '')}", 0, 1, 'L')
        
        if cliente.get('direccion'):
            self.cell(0, 6, f"Dirección: {cliente.get('direccion', '')}", 0, 1, 'L')
        
        self.ln(8)
    
    def tabla_productos(self, lineas: List[Dict]):
        """Tabla de productos/servicios"""
        # Header de la tabla
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(44, 62, 80)  # Azul oscuro
        self.set_text_color(255, 255, 255)  # Blanco
        
        self.cell(80, 8, 'Descripción', 1, 0, 'C', 1)
        self.cell(20, 8, 'Cant.', 1, 0, 'C', 1)
        self.cell(30, 8, 'Precio', 1, 0, 'C', 1)
        self.cell(20, 8, 'Desc.', 1, 0, 'C', 1)
        self.cell(30, 8, 'Total', 1, 1, 'C', 1)
        
        # Líneas de productos
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)
        
        for linea in lineas:
            cantidad = linea.get('cantidad', 1)
            precio = linea.get('precio_unitario', 0)
            descuento = linea.get('descuento', 0)
            
            subtotal = cantidad * precio
            desc_monto = subtotal * descuento / 100
            total = subtotal - desc_monto
            
            # Descripción (puede ser larga)
            descripcion = linea.get('descripcion', '')[:40]  # Limitar caracteres
            
            self.cell(80, 8, descripcion, 1, 0, 'L')
            self.cell(20, 8, str(cantidad), 1, 0, 'C')
            self.cell(30, 8, f"₡{precio:,.2f}", 1, 0, 'R')
            self.cell(20, 8, f"{descuento:.1f}%", 1, 0, 'C')
            self.cell(30, 8, f"₡{total:,.2f}", 1, 1, 'R')
        
        self.ln(5)
    
    def totales_factura(self, datos_factura: Dict):
        """Totales de la factura"""
        lineas = datos_factura.get('lineas', [])
        
        # Calcular totales
        subtotal = 0
        total_descuentos = 0
        total_impuestos = 0
        
        for linea in lineas:
            cantidad = linea.get('cantidad', 1)
            precio = linea.get('precio_unitario', 0)
            descuento = linea.get('descuento', 0)
            tarifa_imp = linea.get('tarifa_impuesto', 13.00)
            
            subtotal_linea = cantidad * precio
            desc_linea = subtotal_linea * descuento / 100
            neto_linea = subtotal_linea - desc_linea
            imp_linea = neto_linea * tarifa_imp / 100
            
            subtotal += subtotal_linea
            total_descuentos += desc_linea
            total_impuestos += imp_linea
        
        total_neto = subtotal - total_descuentos
        total_final = total_neto + total_impuestos
        
        # Mostrar totales
        x_start = self.w - 80
        
        self.set_font('Arial', 'B', 10)
        
        self.set_xy(x_start, self.get_y())
        self.cell(40, 6, 'Subtotal:', 0, 0, 'R')
        self.cell(35, 6, f"₡{subtotal:,.2f}", 0, 1, 'R')
        
        if total_descuentos > 0:
            self.set_xy(x_start, self.get_y())
            self.cell(40, 6, 'Descuentos:', 0, 0, 'R')
            self.cell(35, 6, f"-₡{total_descuentos:,.2f}", 0, 1, 'R')
        
        self.set_xy(x_start, self.get_y())
        self.cell(40, 6, 'IVA (13%):', 0, 0, 'R')
        self.cell(35, 6, f"₡{total_impuestos:,.2f}", 0, 1, 'R')
        
        # Total final
        self.ln(2)
        self.set_font('Arial', 'B', 12)
        self.set_xy(x_start, self.get_y())
        self.cell(40, 8, 'TOTAL:', 1, 0, 'R', 1)
        self.cell(35, 8, f"₡{total_final:,.2f}", 1, 1, 'R', 1)
    
    def info_legal(self):
        """Información legal y footer"""
        self.ln(15)
        self.set_font('Arial', '', 8)
        self.set_text_color(100, 100, 100)
        
        info_legal = [
            "Esta factura electrónica cumple con la normativa vigente de Costa Rica.",
            "Resolución DGT-R-48-2016 del Ministerio de Hacienda.",
            f"Documento generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}",
            "Sistema: Caja Central POS CR - www.cajacentral.com"
        ]
        
        for linea in info_legal:
            self.cell(0, 4, linea, 0, 1, 'C')


import random

# Ejemplo de uso
def ejemplo_facturacion():
    """Ejemplo de uso del sistema de facturación"""
    
    # Configurar el sistema
    facturacion = FacturacionElectronicaCR()
    
    # Datos de ejemplo de una factura
    datos_factura = {
        'numero': '1',
        'codigo_actividad': '522001',  # Venta al por menor
        'condicion_venta': '01',  # Contado
        'medio_pago': '01',  # Efectivo
        'cliente': {
            'nombre': 'Juan Pérez Rodríguez',
            'cedula': '1-1234-5678',
            'tipo_identificacion': '01',  # Física
            'telefono': '8888-9999',
            'email': 'juan@email.com',
            'direccion': 'San José, Costa Rica',
            'provincia': '1',
            'canton': '01',
            'distrito': '01'
        },
        'lineas': [
            {
                'codigo': 'PROD001',
                'descripcion': 'Producto de ejemplo 1',
                'cantidad': 2,
                'precio_unitario': 15000.00,
                'descuento': 0.0,
                'unidad_medida': 'Unid',
                'codigo_impuesto': '01',
                'tarifa_impuesto': 13.00
            },
            {
                'codigo': 'PROD002', 
                'descripcion': 'Producto de ejemplo 2',
                'cantidad': 1,
                'precio_unitario': 8500.00,
                'descuento': 5.0,
                'unidad_medida': 'Unid',
                'codigo_impuesto': '01',
                'tarifa_impuesto': 13.00
            }
        ]
    }
    
    # Generar XML
    xml_factura = facturacion.crear_xml_factura(datos_factura)
    
    # Guardar XML
    with open('facturas/ejemplo_factura.xml', 'w', encoding='utf-8') as f:
        f.write(xml_factura)
    
    # Generar PDF
    pdf_path = facturacion.generar_pdf_factura(datos_factura)
    
    print(f"✅ Factura generada:")
    print(f"📄 XML: facturas/ejemplo_factura.xml")
    print(f"📄 PDF: {pdf_path}")
    
    # Simular envío a Hacienda (en producción necesitaría certificados)
    # resultado = facturacion.enviar_hacienda(xml_factura, datos_factura['clave_numerica'])
    # print(f"📤 Envío a Hacienda: {resultado}")

if __name__ == "__main__":
    ejemplo_facturacion()
