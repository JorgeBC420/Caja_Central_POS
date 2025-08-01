"""
Integración con el Ministerio de Hacienda de Costa Rica
Facturación electrónica y comunicación con ATV (Administración Tributaria Virtual)
"""

import requests
import xml.etree.ElementTree as ET
import json
import logging
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
import re

from core.database import get_db_cursor, ejecutar_consulta_segura

@dataclass 
class ConfiguracionHacienda:
    """Configuración para API de Hacienda"""
    api_url_recepcion: str
    api_url_consulta: str
    token_api: str
    usuario_hacienda: str
    password_hacienda: str
    pin_certificado: str
    ruta_certificado: str
    ambiente: str  # sandbox | produccion
    codigo_actividad: str
    nombre_comercial: str
    cedula_juridica: str
    provincia: str
    canton: str
    distrito: str
    barrio: str
    otras_senas: str
    codigo_postal: str
    telefono: str
    fax: str
    correo: str
    
    def es_produccion(self) -> bool:
        return self.ambiente.lower() == 'produccion'

class EstadoDocumento:
    """Estados posibles de documentos en Hacienda"""
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    ACEPTADO = "aceptado"
    RECHAZADO = "rechazado"
    ERROR = "error"
    ENVIADO = "enviado"
    CONFIRMADO = "confirmado"

class TipoDocumento:
    """Tipos de documentos tributarios"""
    FACTURA_ELECTRONICA = "01"
    NOTA_DEBITO = "02"
    NOTA_CREDITO = "03"
    TIQUETE_ELECTRONICO = "04"
    NOTA_DEBITO_TIQUETE = "05"
    NOTA_CREDITO_TIQUETE = "06"
    FACTURA_COMPRA = "07"
    FACTURA_EXPORTACION = "08"
    FACTURA_CONTINGENCIA = "09"

class MedioPago:
    """Medios de pago según Hacienda"""
    EFECTIVO = "01"
    TARJETA = "02"
    CHEQUE = "03"
    TRANSFERENCIA = "04"
    RECAUDADO_TERCEROS = "05"
    OTROS = "99"

class HaciendaAPIException(Exception):
    """Excepción específica para errores de Hacienda API"""
    def __init__(self, message: str, code: str = None, details: Dict = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}

class ValidadorDocumentos:
    """Validador de documentos tributarios"""
    
    @staticmethod
    def validar_cedula(cedula: str) -> Tuple[bool, str]:
        """Valida cédula costarricense"""
        try:
            # Limpiar cédula
            cedula = re.sub(r'[^0-9]', '', cedula)
            
            if len(cedula) == 9:
                # Cédula física
                if cedula[0] == '0':
                    return False, "Cédula no puede empezar con 0"
                
                # Algoritmo de validación para cédula física
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
                    return True, "Cédula física válida"
                else:
                    return False, "Dígito verificador incorrecto"
                    
            elif len(cedula) == 10:
                # Cédula jurídica
                if cedula[0] != '3':
                    return False, "Cédula jurídica debe empezar con 3"
                
                return True, "Cédula jurídica válida"
                
            elif len(cedula) == 11 or len(cedula) == 12:
                # DIMEX o documento extranjero
                return True, "Documento extranjero válido"
                
            else:
                return False, "Longitud de cédula incorrecta"
                
        except Exception as e:
            return False, f"Error validando cédula: {e}"
    
    @staticmethod
    def validar_email(email: str) -> bool:
        """Valida formato de email"""
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(patron, email) is not None
    
    @staticmethod
    def validar_telefono_cr(telefono: str) -> bool:
        """Valida teléfono costarricense"""
        telefono = re.sub(r'[^0-9]', '', telefono)
        
        # 8 dígitos para teléfono local
        if len(telefono) == 8:
            return telefono[0] in ['2', '4', '6', '7', '8']
        
        # 11 dígitos con código de país
        if len(telefono) == 11 and telefono.startswith('506'):
            return telefono[3:4] in ['2', '4', '6', '7', '8']
        
        return False

class GeneradorXMLHacienda:
    """Generador de XML para documentos tributarios"""
    
    def __init__(self, config: ConfiguracionHacienda):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def generar_clave_numerica(self, tipo_documento: str, numero_consecutivo: int, 
                              fecha: datetime = None) -> str:
        """Genera clave numérica según especificaciones de Hacienda"""
        try:
            if fecha is None:
                fecha = datetime.now()
            
            # Formato: PPaaammddttnnnnnnnncs
            # PP = país (506)
            # aaa = día del año (001-366)
            # mm = mes (01-12)
            # dd = día (01-31)
            # tt = tipo documento
            # nnnnnnnn = número consecutivo (8 dígitos)
            # c = código de seguridad (1 dígito aleatorio)
            # s = dígito verificador
            
            pais = "506"
            dia_ano = f"{fecha.timetuple().tm_yday:03d}"
            mes = f"{fecha.month:02d}"
            dia = f"{fecha.day:02d}"
            tipo = tipo_documento.zfill(2)
            consecutivo = f"{numero_consecutivo:08d}"
            
            # Código de seguridad aleatorio
            import random
            codigo_seguridad = str(random.randint(1, 9))
            
            # Construir clave sin dígito verificador
            clave_sin_dv = f"{pais}{dia_ano}{mes}{dia}{tipo}{consecutivo}{codigo_seguridad}"
            
            # Calcular dígito verificador
            digito_verificador = self._calcular_digito_verificador(clave_sin_dv)
            
            clave_completa = f"{clave_sin_dv}{digito_verificador}"
            
            return clave_completa
            
        except Exception as e:
            self.logger.error(f"Error generando clave numérica: {e}")
            raise HaciendaAPIException(f"Error generando clave: {e}")
    
    def _calcular_digito_verificador(self, clave: str) -> int:
        """Calcula dígito verificador usando algoritmo Luhn modificado"""
        try:
            # Multiplicadores en orden inverso
            multiplicadores = [2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1]
            
            suma = 0
            for i, digito in enumerate(reversed(clave)):
                producto = int(digito) * multiplicadores[i % len(multiplicadores)]
                if producto > 9:
                    producto = (producto // 10) + (producto % 10)
                suma += producto
            
            digito_verificador = (10 - (suma % 10)) % 10
            return digito_verificador
            
        except Exception as e:
            self.logger.error(f"Error calculando dígito verificador: {e}")
            return 0
    
    def generar_xml_factura(self, datos_factura: Dict[str, Any]) -> str:
        """Genera XML de factura electrónica"""
        try:
            # Crear elemento raíz
            factura = ET.Element("FacturaElectronica")
            factura.set("xmlns", "https://tribunet.hacienda.go.cr/docs/esquemas/2017/v4.3/facturaElectronica")
            factura.set("xmlns:ds", "http://www.w3.org/2000/09/xmldsig#")
            factura.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
            factura.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
            
            # Clave
            clave_elem = ET.SubElement(factura, "Clave")
            clave_elem.text = datos_factura['clave_numerica']
            
            # Código de actividad
            cod_actividad = ET.SubElement(factura, "CodigoActividad")
            cod_actividad.text = self.config.codigo_actividad
            
            # Número consecutivo
            num_consecutivo = ET.SubElement(factura, "NumeroConsecutivo")
            num_consecutivo.text = datos_factura['numero_consecutivo']
            
            # Fecha emisión
            fecha_emision = ET.SubElement(factura, "FechaEmision")
            fecha_emision.text = datos_factura['fecha_emision'].isoformat()
            
            # Emisor
            self._agregar_emisor(factura)
            
            # Receptor
            if datos_factura.get('receptor'):
                self._agregar_receptor(factura, datos_factura['receptor'])
            
            # Condición de venta
            condicion_venta = ET.SubElement(factura, "CondicionVenta")
            condicion_venta.text = datos_factura.get('condicion_venta', '01')  # Contado
            
            # Plazo de crédito (si aplica)
            if datos_factura.get('plazo_credito'):
                plazo_credito = ET.SubElement(factura, "PlazoCredito")
                plazo_credito.text = str(datos_factura['plazo_credito'])
            
            # Medio de pago
            medio_pago = ET.SubElement(factura, "MedioPago")
            medio_pago.text = datos_factura.get('medio_pago', MedioPago.EFECTIVO)
            
            # Detalle de servicios
            detalle_servicio = ET.SubElement(factura, "DetalleServicio")
            
            for linea in datos_factura['lineas']:
                self._agregar_linea_detalle(detalle_servicio, linea)
            
            # Resumen factura
            self._agregar_resumen_factura(factura, datos_factura['resumen'])
            
            # Información de referencia (si aplica)
            if datos_factura.get('referencia'):
                self._agregar_informacion_referencia(factura, datos_factura['referencia'])
            
            # Otros (opcional)
            if datos_factura.get('otros'):
                otros = ET.SubElement(factura, "Otros")
                otros.text = datos_factura['otros']
            
            # Convertir a string XML
            xml_string = ET.tostring(factura, encoding='unicode', method='xml')
            
            # Formatear XML
            import xml.dom.minidom
            dom = xml.dom.minidom.parseString(xml_string)
            xml_formatted = dom.toprettyxml(indent="  ")
            
            # Remover líneas vacías
            xml_lines = [line for line in xml_formatted.split('\n') if line.strip()]
            xml_final = '\n'.join(xml_lines)
            
            return xml_final
            
        except Exception as e:
            self.logger.error(f"Error generando XML factura: {e}")
            raise HaciendaAPIException(f"Error generando XML: {e}")
    
    def _agregar_emisor(self, parent: ET.Element):
        """Agrega información del emisor"""
        emisor = ET.SubElement(parent, "Emisor")
        
        nombre = ET.SubElement(emisor, "Nombre")
        nombre.text = self.config.nombre_comercial
        
        identificacion = ET.SubElement(emisor, "Identificacion")
        tipo_id = ET.SubElement(identificacion, "Tipo")
        tipo_id.text = "02"  # Cédula jurídica
        numero_id = ET.SubElement(identificacion, "Numero")
        numero_id.text = self.config.cedula_juridica
        
        # Ubicación
        ubicacion = ET.SubElement(emisor, "Ubicacion")
        provincia = ET.SubElement(ubicacion, "Provincia")
        provincia.text = self.config.provincia
        canton = ET.SubElement(ubicacion, "Canton")
        canton.text = self.config.canton
        distrito = ET.SubElement(ubicacion, "Distrito")
        distrito.text = self.config.distrito
        barrio = ET.SubElement(ubicacion, "Barrio")
        barrio.text = self.config.barrio
        otras_senas = ET.SubElement(ubicacion, "OtrasSenas")
        otras_senas.text = self.config.otras_senas
        
        # Teléfono
        telefono = ET.SubElement(emisor, "Telefono")
        cod_pais = ET.SubElement(telefono, "CodigoPais")
        cod_pais.text = "506"
        num_telefono = ET.SubElement(telefono, "NumTelefono")
        num_telefono.text = self.config.telefono
        
        # Correo
        correo = ET.SubElement(emisor, "CorreoElectronico")
        correo.text = self.config.correo
    
    def _agregar_receptor(self, parent: ET.Element, datos_receptor: Dict):
        """Agrega información del receptor"""
        receptor = ET.SubElement(parent, "Receptor")
        
        nombre = ET.SubElement(receptor, "Nombre")
        nombre.text = datos_receptor['nombre']
        
        identificacion = ET.SubElement(receptor, "Identificacion")
        tipo_id = ET.SubElement(identificacion, "Tipo")
        tipo_id.text = datos_receptor.get('tipo_identificacion', '01')
        numero_id = ET.SubElement(identificacion, "Numero")
        numero_id.text = datos_receptor['numero_identificacion']
        
        # Correo opcional
        if datos_receptor.get('correo'):
            correo = ET.SubElement(receptor, "CorreoElectronico")
            correo.text = datos_receptor['correo']
    
    def _agregar_linea_detalle(self, parent: ET.Element, linea: Dict):
        """Agrega una línea de detalle al XML"""
        linea_detalle = ET.SubElement(parent, "LineaDetalle")
        
        numero_linea = ET.SubElement(linea_detalle, "NumeroLinea")
        numero_linea.text = str(linea['numero_linea'])
        
        # Código
        if linea.get('codigo'):
            codigo = ET.SubElement(linea_detalle, "Codigo")
            tipo_codigo = ET.SubElement(codigo, "Tipo")
            tipo_codigo.text = "04"  # Código asignado por vendedor
            codigo_val = ET.SubElement(codigo, "Codigo")
            codigo_val.text = linea['codigo']
        
        # Cantidad
        cantidad = ET.SubElement(linea_detalle, "Cantidad")
        cantidad.text = str(linea['cantidad'])
        
        # Unidad de medida
        unidad_medida = ET.SubElement(linea_detalle, "UnidadMedida")
        unidad_medida.text = linea.get('unidad_medida', 'Unid')
        
        # Detalle
        detalle = ET.SubElement(linea_detalle, "Detalle")
        detalle.text = linea['descripcion']
        
        # Precio unitario
        precio_unitario = ET.SubElement(linea_detalle, "PrecioUnitario")
        precio_unitario.text = f"{linea['precio_unitario']:.5f}"
        
        # Monto total
        monto_total = ET.SubElement(linea_detalle, "MontoTotal")
        monto_total.text = f"{linea['monto_total']:.5f}"
        
        # Subtotal (sin impuestos)
        subtotal = ET.SubElement(linea_detalle, "SubTotal")
        subtotal.text = f"{linea['subtotal']:.5f}"
        
        # Impuesto (si aplica)
        if linea.get('impuesto', 0) > 0:
            impuesto = ET.SubElement(linea_detalle, "Impuesto")
            codigo_imp = ET.SubElement(impuesto, "Codigo")
            codigo_imp.text = "01"  # IVA
            codigo_tarifa = ET.SubElement(impuesto, "CodigoTarifa")
            codigo_tarifa.text = "08"  # Tarifa general
            tarifa = ET.SubElement(impuesto, "Tarifa")
            tarifa.text = f"{linea['tarifa_impuesto']:.2f}"
            monto_imp = ET.SubElement(impuesto, "Monto")
            monto_imp.text = f"{linea['impuesto']:.5f}"
        
        # Monto total línea
        monto_total_linea = ET.SubElement(linea_detalle, "MontoTotalLinea")
        monto_total_linea.text = f"{linea['monto_total_linea']:.5f}"
    
    def _agregar_resumen_factura(self, parent: ET.Element, resumen: Dict):
        """Agrega el resumen de la factura"""
        resumen_factura = ET.SubElement(parent, "ResumenFactura")
        
        # Código moneda
        cod_moneda = ET.SubElement(resumen_factura, "CodigoTipoMoneda")
        cod_moneda.text = resumen.get('codigo_moneda', 'CRC')
        
        # Tipo de cambio
        if resumen.get('tipo_cambio'):
            tipo_cambio = ET.SubElement(resumen_factura, "TipoCambio")
            tipo_cambio.text = f"{resumen['tipo_cambio']:.5f}"
        
        # Total servicios gravados
        total_gravados = ET.SubElement(resumen_factura, "TotalServGravados")
        total_gravados.text = f"{resumen['total_gravados']:.5f}"
        
        # Total servicios exentos
        total_exentos = ET.SubElement(resumen_factura, "TotalServExentos")
        total_exentos.text = f"{resumen['total_exentos']:.5f}"
        
        # Total servicios exonerados
        total_exonerados = ET.SubElement(resumen_factura, "TotalServExonerados")
        total_exonerados.text = f"{resumen['total_exonerados']:.5f}"
        
        # Total mercancias gravadas
        total_merc_gravadas = ET.SubElement(resumen_factura, "TotalMercanciasGravadas")
        total_merc_gravadas.text = f"{resumen['total_mercancias_gravadas']:.5f}"
        
        # Total mercancias exentas
        total_merc_exentas = ET.SubElement(resumen_factura, "TotalMercanciasExentas")
        total_merc_exentas.text = f"{resumen['total_mercancias_exentas']:.5f}"
        
        # Total mercancias exoneradas
        total_merc_exoneradas = ET.SubElement(resumen_factura, "TotalMercanciasExoneradas")
        total_merc_exoneradas.text = f"{resumen['total_mercancias_exoneradas']:.5f}"
        
        # Total gravado
        total_gravado = ET.SubElement(resumen_factura, "TotalGravado")
        total_gravado.text = f"{resumen['total_gravado']:.5f}"
        
        # Total exento
        total_exento = ET.SubElement(resumen_factura, "TotalExento")
        total_exento.text = f"{resumen['total_exento']:.5f}"
        
        # Total exonerado
        total_exonerado = ET.SubElement(resumen_factura, "TotalExonerado")
        total_exonerado.text = f"{resumen['total_exonerado']:.5f}"
        
        # Total venta
        total_venta = ET.SubElement(resumen_factura, "TotalVenta")
        total_venta.text = f"{resumen['total_venta']:.5f}"
        
        # Total descuentos
        total_descuentos = ET.SubElement(resumen_factura, "TotalDescuentos")
        total_descuentos.text = f"{resumen['total_descuentos']:.5f}"
        
        # Total venta neta
        total_venta_neta = ET.SubElement(resumen_factura, "TotalVentaNeta")
        total_venta_neta.text = f"{resumen['total_venta_neta']:.5f}"
        
        # Total impuesto
        total_impuesto = ET.SubElement(resumen_factura, "TotalImpuesto")
        total_impuesto.text = f"{resumen['total_impuesto']:.5f}"
        
        # Total comprobante
        total_comprobante = ET.SubElement(resumen_factura, "TotalComprobante")
        total_comprobante.text = f"{resumen['total_comprobante']:.5f}"
    
    def _agregar_informacion_referencia(self, parent: ET.Element, referencia: Dict):
        """Agrega información de referencia (para notas de crédito/débito)"""
        info_referencia = ET.SubElement(parent, "InformacionReferencia")
        
        tipo_doc = ET.SubElement(info_referencia, "TipoDoc")
        tipo_doc.text = referencia['tipo_documento']
        
        numero = ET.SubElement(info_referencia, "Numero")
        numero.text = referencia['numero']
        
        fecha_emision = ET.SubElement(info_referencia, "FechaEmision")
        fecha_emision.text = referencia['fecha_emision']
        
        codigo = ET.SubElement(info_referencia, "Codigo")
        codigo.text = referencia['codigo_referencia']
        
        razon = ET.SubElement(info_referencia, "Razon")
        razon.text = referencia['razon']

class HaciendaAPI:
    """Cliente principal para API de Hacienda"""
    
    def __init__(self, config: ConfiguracionHacienda = None):
        self.logger = logging.getLogger(__name__)
        
        if config is None:
            self.config = self._cargar_configuracion()
        else:
            self.config = config
            
        self.generador_xml = GeneradorXMLHacienda(self.config)
        self.validador = ValidadorDocumentos()
        
        # URLs de API según ambiente
        if self.config.es_produccion():
            self.base_url = "https://api.comprobanteselectronicos.go.cr"
        else:
            self.base_url = "https://idp.comprobanteselectronicos.go.cr"
    
    def _cargar_configuracion(self) -> ConfiguracionHacienda:
        """Carga configuración desde base de datos"""
        try:
            config_dict = {}
            query = "SELECT clave, valor FROM configuraciones WHERE clave LIKE 'hacienda_%'"
            
            with get_db_cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                
                for row in rows:
                    key = row[0].replace('hacienda_', '')
                    config_dict[key] = row[1]
            
            # Valores por defecto
            defaults = {
                'api_url_recepcion': f"{self.base_url}/recepcion-fi/",
                'api_url_consulta': f"{self.base_url}/consultas/",
                'token_api': '',
                'usuario_hacienda': '',
                'password_hacienda': '',
                'pin_certificado': '',
                'ruta_certificado': '',
                'ambiente': 'sandbox',
                'codigo_actividad': '722003',
                'nombre_comercial': 'CajaCentralPOS',
                'cedula_juridica': '',
                'provincia': '1',
                'canton': '01',
                'distrito': '01',
                'barrio': '01',
                'otras_senas': '',
                'codigo_postal': '10101',
                'telefono': '',
                'fax': '',
                'correo': ''
            }
            
            for key, default_value in defaults.items():
                if key not in config_dict:
                    config_dict[key] = default_value
            
            return ConfiguracionHacienda(**config_dict)
            
        except Exception as e:
            self.logger.error(f"Error cargando configuración Hacienda: {e}")
            raise HaciendaAPIException(f"Error configuración: {e}")
    
    def autenticar(self) -> Tuple[bool, str]:
        """Autentica con la API de Hacienda"""
        try:
            auth_url = f"{self.base_url}/auth"
            
            payload = {
                'username': self.config.usuario_hacienda,
                'password': self.config.password_hacienda,
                'client_id': 'api-prod' if self.config.es_produccion() else 'api-stag'
            }
            
            response = requests.post(auth_url, data=payload, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                self.config.token_api = token_data.get('access_token', '')
                
                # Guardar token en BD
                query = "UPDATE configuraciones SET valor = ? WHERE clave = 'hacienda_token_api'"
                ejecutar_consulta_segura(query, (self.config.token_api,))
                
                self.logger.info("Autenticación con Hacienda exitosa")
                return True, "Autenticación exitosa"
            else:
                error_msg = f"Error autenticación: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error autenticando con Hacienda: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def enviar_documento(self, xml_data: str, clave: str) -> Tuple[bool, str, Dict]:
        """Envía documento electrónico a Hacienda"""
        try:
            if not self.config.token_api:
                auth_ok, auth_msg = self.autenticar()
                if not auth_ok:
                    return False, f"Error autenticación: {auth_msg}", {}
            
            url_envio = f"{self.base_url}/recepcion"
            
            headers = {
                'Authorization': f'Bearer {self.config.token_api}',
                'Content-Type': 'application/json'
            }
            
            # Codificar XML en base64
            xml_base64 = base64.b64encode(xml_data.encode('utf-8')).decode('utf-8')
            
            payload = {
                'clave': clave,
                'fecha': datetime.now().isoformat(),
                'emisor': {
                    'tipoIdentificacion': '02',
                    'numeroIdentificacion': self.config.cedula_juridica
                },
                'comprobanteXml': xml_base64
            }
            
            response = requests.post(url_envio, json=payload, headers=headers, timeout=60)
            
            if response.status_code in [200, 202]:
                result = response.json()
                
                # Actualizar estado en BD
                self._actualizar_estado_documento(clave, EstadoDocumento.ENVIADO, result)
                
                self.logger.info(f"Documento {clave} enviado exitosamente a Hacienda")
                return True, "Documento enviado correctamente", result
            else:
                error_msg = f"Error enviando documento: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                
                # Actualizar estado de error
                self._actualizar_estado_documento(clave, EstadoDocumento.ERROR, {'error': error_msg})
                
                return False, error_msg, {}
                
        except Exception as e:
            error_msg = f"Error enviando documento a Hacienda: {e}"
            self.logger.error(error_msg)
            
            # Actualizar estado de error
            self._actualizar_estado_documento(clave, EstadoDocumento.ERROR, {'error': str(e)})
            
            return False, error_msg, {}
    
    def consultar_estado_documento(self, clave: str) -> Tuple[bool, str, Dict]:
        """Consulta el estado de un documento en Hacienda"""
        try:
            if not self.config.token_api:
                auth_ok, auth_msg = self.autenticar()
                if not auth_ok:
                    return False, f"Error autenticación: {auth_msg}", {}
            
            url_consulta = f"{self.base_url}/consultas/recepcion/{clave}"
            
            headers = {
                'Authorization': f'Bearer {self.config.token_api}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url_consulta, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Mapear estado de Hacienda a nuestros estados
                estado_hacienda = result.get('ind-estado', '')
                estado_interno = self._mapear_estado_hacienda(estado_hacienda)
                
                # Actualizar estado en BD
                self._actualizar_estado_documento(clave, estado_interno, result)
                
                return True, f"Estado: {estado_interno}", result
            else:
                error_msg = f"Error consultando estado: {response.status_code} - {response.text}"
                return False, error_msg, {}
                
        except Exception as e:
            error_msg = f"Error consultando estado documento: {e}"
            self.logger.error(error_msg)
            return False, error_msg, {}
    
    def _mapear_estado_hacienda(self, estado_hacienda: str) -> str:
        """Mapea estados de Hacienda a estados internos"""
        mapeo = {
            'recibido': EstadoDocumento.PROCESANDO,
            'procesando': EstadoDocumento.PROCESANDO,
            'aceptado': EstadoDocumento.ACEPTADO,
            'rechazado': EstadoDocumento.RECHAZADO,
            'error': EstadoDocumento.ERROR
        }
        
        return mapeo.get(estado_hacienda.lower(), EstadoDocumento.PENDIENTE)
    
    def _actualizar_estado_documento(self, clave: str, estado: str, respuesta_api: Dict):
        """Actualiza estado del documento en BD"""
        try:
            query = """
                INSERT OR REPLACE INTO documentos_electronicos 
                (clave, estado, respuesta_hacienda, fecha_actualizacion)
                VALUES (?, ?, ?, ?)
            """
            
            respuesta_json = json.dumps(respuesta_api, ensure_ascii=False)
            
            ejecutar_consulta_segura(query, (
                clave, 
                estado, 
                respuesta_json, 
                datetime.now().isoformat()
            ))
            
        except Exception as e:
            self.logger.error(f"Error actualizando estado documento: {e}")
    
    def generar_y_enviar_factura(self, datos_factura: Dict[str, Any]) -> Tuple[bool, str, str]:
        """Genera XML y envía factura completa"""
        try:
            # Generar clave numérica
            clave = self.generador_xml.generar_clave_numerica(
                TipoDocumento.FACTURA_ELECTRONICA,
                datos_factura['numero_consecutivo']
            )
            
            # Agregar clave a los datos
            datos_factura['clave_numerica'] = clave
            
            # Generar XML
            xml_factura = self.generador_xml.generar_xml_factura(datos_factura)
            
            # Enviar a Hacienda
            exito, mensaje, respuesta = self.enviar_documento(xml_factura, clave)
            
            if exito:
                # Guardar XML generado
                self._guardar_xml_documento(clave, xml_factura)
                
                return True, f"Factura enviada. Clave: {clave}", clave
            else:
                return False, mensaje, clave
                
        except Exception as e:
            error_msg = f"Error generando y enviando factura: {e}"
            self.logger.error(error_msg)
            return False, error_msg, ""
    
    def _guardar_xml_documento(self, clave: str, xml_content: str):
        """Guarda XML del documento en BD"""
        try:
            query = """
                INSERT OR REPLACE INTO xml_documentos (clave, xml_content, fecha_creacion)
                VALUES (?, ?, ?)
            """
            
            ejecutar_consulta_segura(query, (
                clave,
                xml_content,
                datetime.now().isoformat()
            ))
            
        except Exception as e:
            self.logger.error(f"Error guardando XML documento: {e}")
    
    def obtener_documentos_pendientes(self) -> List[Dict[str, Any]]:
        """Obtiene documentos pendientes de procesar"""
        try:
            query = """
                SELECT clave, estado, fecha_actualizacion 
                FROM documentos_electronicos 
                WHERE estado IN (?, ?, ?)
                ORDER BY fecha_actualizacion ASC
            """
            
            documentos = []
            
            with get_db_cursor() as cursor:
                cursor.execute(query, (
                    EstadoDocumento.PENDIENTE,
                    EstadoDocumento.ENVIADO,
                    EstadoDocumento.PROCESANDO
                ))
                
                rows = cursor.fetchall()
                
                for row in rows:
                    documentos.append({
                        'clave': row[0],
                        'estado': row[1],
                        'fecha_actualizacion': row[2]
                    })
            
            return documentos
            
        except Exception as e:
            self.logger.error(f"Error obteniendo documentos pendientes: {e}")
            return []
    
    def procesar_documentos_pendientes(self) -> Dict[str, int]:
        """Procesa todos los documentos pendientes"""
        try:
            documentos = self.obtener_documentos_pendientes()
            
            procesados = 0
            errores = 0
            
            for doc in documentos:
                try:
                    exito, mensaje, resultado = self.consultar_estado_documento(doc['clave'])
                    
                    if exito:
                        procesados += 1
                        self.logger.info(f"Documento {doc['clave']}: {mensaje}")
                    else:
                        errores += 1
                        self.logger.error(f"Error procesando {doc['clave']}: {mensaje}")
                    
                    # Pausa entre consultas
                    import time
                    time.sleep(2)
                    
                except Exception as e:
                    errores += 1
                    self.logger.error(f"Error procesando documento {doc['clave']}: {e}")
            
            return {
                'total': len(documentos),
                'procesados': procesados,
                'errores': errores
            }
            
        except Exception as e:
            self.logger.error(f"Error procesando documentos pendientes: {e}")
            return {'total': 0, 'procesados': 0, 'errores': 1}

# Instancia global
hacienda_api = HaciendaAPI()

# Funciones de utilidad
def validar_cedula_costarricense(cedula: str) -> bool:
    """Función de utilidad para validar cédula"""
    validador = ValidadorDocumentos()
    valida, _ = validador.validar_cedula(cedula)
    return valida

def generar_factura_electronica(datos_venta: Dict) -> Tuple[bool, str, str]:
    """Función de utilidad para generar factura electrónica"""
    return hacienda_api.generar_y_enviar_factura(datos_venta)