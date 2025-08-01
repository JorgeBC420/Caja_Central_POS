"""
Parámetros de facturación para Costa Rica
Maneja configuración de impuestos, numeración, y datos fiscales
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from dataclasses import dataclass
from enum import Enum

from core.database import get_db_cursor, ejecutar_consulta_segura

class TipoDocumento(Enum):
    """Tipos de documentos fiscales en Costa Rica"""
    FACTURA_ELECTRONICA = "FE"
    NOTA_CREDITO = "NC"
    NOTA_DEBITO = "ND"
    TIQUETE_ELECTRONICO = "TE"
    FACTURA_COMPRA = "FC"
    FACTURA_EXPORTACION = "FEE"

class TipoIdentificacion(Enum):
    """Tipos de identificación válidos en Costa Rica"""
    CEDULA_FISICA = "01"
    CEDULA_JURIDICA = "02"
    DIMEX = "03"
    NITE = "04"
    EXTRANJERO = "05"

class TipoImpuesto(Enum):
    """Tipos de impuestos en Costa Rica"""
    IVA = "01"
    SELECTIVO_CONSUMO = "02"
    UNICO_COMBUSTIBLES = "03"
    BEBIDAS_ALCOHOLICAS = "04"
    BEBIDAS_ENVASADAS = "05"
    PRODUCTOS_TABACO = "06"
    CEMENTO = "07"
    OTROS = "99"

@dataclass
class ConfiguracionImpuesto:
    """Configuración de un impuesto específico"""
    tipo: TipoImpuesto
    nombre: str
    tasa: Decimal
    activo: bool = True
    codigo_hacienda: str = ""
    descripcion: str = ""

@dataclass
class DatosEmpresa:
    """Datos fiscales de la empresa emisora"""
    razon_social: str
    nombre_comercial: str
    identificacion: str
    tipo_identificacion: TipoIdentificacion
    direccion: str
    provincia: str
    canton: str
    distrito: str
    codigo_postal: str
    telefono: str
    email: str
    actividad_economica: str
    regimen_tributario: str
    logo_path: Optional[str] = None

class ParametrosFacturacion:
    """Manejo de parámetros de facturación"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._datos_empresa = None
        self._impuestos = None
        self._numeracion = None
    
    @property
    def datos_empresa(self) -> DatosEmpresa:
        """Obtiene los datos de la empresa"""
        if self._datos_empresa is None:
            self._datos_empresa = self._cargar_datos_empresa()
        return self._datos_empresa
    
    @property
    def impuestos(self) -> List[ConfiguracionImpuesto]:
        """Obtiene la configuración de impuestos"""
        if self._impuestos is None:
            self._impuestos = self._cargar_impuestos()
        return self._impuestos
    
    @property
    def numeracion(self) -> Dict[str, Any]:
        """Obtiene la configuración de numeración"""
        if self._numeracion is None:
            self._numeracion = self._cargar_numeracion()
        return self._numeracion
    
    def _cargar_datos_empresa(self) -> DatosEmpresa:
        """Carga los datos de la empresa desde la base de datos"""
        try:
            query = """
                SELECT clave, valor FROM configuraciones 
                WHERE clave LIKE 'empresa_%' OR clave LIKE 'fiscal_%'
            """
            
            config = {}
            with get_db_cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                for row in rows:
                    config[row[0]] = row[1]
            
            return DatosEmpresa(
                razon_social=config.get('empresa_razon_social', ''),
                nombre_comercial=config.get('empresa_nombre_comercial', ''),
                identificacion=config.get('empresa_identificacion', ''),
                tipo_identificacion=TipoIdentificacion(config.get('empresa_tipo_identificacion', '01')),
                direccion=config.get('empresa_direccion', ''),
                provincia=config.get('empresa_provincia', ''),
                canton=config.get('empresa_canton', ''),
                distrito=config.get('empresa_distrito', ''),
                codigo_postal=config.get('empresa_codigo_postal', ''),
                telefono=config.get('empresa_telefono', ''),
                email=config.get('empresa_email', ''),
                actividad_economica=config.get('fiscal_actividad_economica', ''),
                regimen_tributario=config.get('fiscal_regimen_tributario', 'Régimen Tradicional'),
                logo_path=config.get('empresa_logo_path')
            )
            
        except Exception as e:
            self.logger.error(f"Error cargando datos de empresa: {e}")
            return DatosEmpresa("", "", "", TipoIdentificacion.CEDULA_JURIDICA, 
                              "", "", "", "", "", "", "", "", "")
    
    def _cargar_impuestos(self) -> List[ConfiguracionImpuesto]:
        """Carga la configuración de impuestos"""
        try:
            query = """
                SELECT tipo, nombre, tasa, activo, codigo_hacienda, descripcion
                FROM impuestos WHERE activo = 1
                ORDER BY tipo
            """
            
            impuestos = []
            with get_db_cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                
                for row in rows:
                    impuesto = ConfiguracionImpuesto(
                        tipo=TipoImpuesto(row[0]),
                        nombre=row[1],
                        tasa=Decimal(str(row[2])),
                        activo=bool(row[3]),
                        codigo_hacienda=row[4] or "",
                        descripcion=row[5] or ""
                    )
                    impuestos.append(impuesto)
            
            # Si no hay impuestos configurados, agregar IVA por defecto
            if not impuestos:
                iva_default = ConfiguracionImpuesto(
                    tipo=TipoImpuesto.IVA,
                    nombre="IVA",
                    tasa=Decimal('0.13'),
                    codigo_hacienda="01"
                )
                impuestos.append(iva_default)
                self._guardar_impuesto(iva_default)
            
            return impuestos
            
        except Exception as e:
            self.logger.error(f"Error cargando impuestos: {e}")
            return []
    
    def _cargar_numeracion(self) -> Dict[str, Any]:
        """Carga la configuración de numeración de documentos"""
        try:
            query = """
                SELECT tipo_documento, prefijo, siguiente_numero, longitud_numero,
                       sucursal, terminal_pos FROM numeracion_documentos
            """
            
            numeracion = {}
            with get_db_cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                
                for row in rows:
                    tipo_doc = row[0]
                    numeracion[tipo_doc] = {
                        'prefijo': row[1] or '',
                        'siguiente_numero': int(row[2] or 1),
                        'longitud_numero': int(row[3] or 6),
                        'sucursal': row[4] or '001',
                        'terminal_pos': row[5] or '001'
                    }
            
            # Configuraciones por defecto si no existen
            tipos_default = [
                TipoDocumento.FACTURA_ELECTRONICA.value,
                TipoDocumento.TIQUETE_ELECTRONICO.value,
                TipoDocumento.NOTA_CREDITO.value
            ]
            
            for tipo in tipos_default:
                if tipo not in numeracion:
                    numeracion[tipo] = {
                        'prefijo': '',
                        'siguiente_numero': 1,
                        'longitud_numero': 10,
                        'sucursal': '001',
                        'terminal_pos': '001'
                    }
                    self._guardar_numeracion(tipo, numeracion[tipo])
            
            return numeracion
            
        except Exception as e:
            self.logger.error(f"Error cargando numeración: {e}")
            return {}
    
    def obtener_siguiente_numero(self, tipo_documento: str) -> str:
        """Obtiene y reserva el siguiente número de documento"""
        try:
            config_num = self.numeracion.get(tipo_documento)
            if not config_num:
                raise ValueError(f"Tipo de documento no configurado: {tipo_documento}")
            
            # Obtener número actual y incrementar
            numero_actual = config_num['siguiente_numero']
            longitud = config_num['longitud_numero']
            prefijo = config_num['prefijo']
            sucursal = config_num['sucursal']
            terminal = config_num['terminal_pos']
            
            # Formatear número
            numero_formateado = str(numero_actual).zfill(longitud)
            
            # Construir número completo según estándar CR
            if tipo_documento == TipoDocumento.FACTURA_ELECTRONICA.value:
                numero_completo = f"{sucursal}{terminal}{numero_formateado}"
            else:
                numero_completo = f"{prefijo}{numero_formateado}"
            
            # Actualizar siguiente número en BD
            self._actualizar_siguiente_numero(tipo_documento, numero_actual + 1)
            
            # Actualizar cache
            config_num['siguiente_numero'] = numero_actual + 1
            
            return numero_completo
            
        except Exception as e:
            self.logger.error(f"Error obteniendo siguiente número: {e}")
            raise
    
    def _actualizar_siguiente_numero(self, tipo_documento: str, siguiente_numero: int):
        """Actualiza el siguiente número en la base de datos"""
        query = """
            UPDATE numeracion_documentos 
            SET siguiente_numero = ? 
            WHERE tipo_documento = ?
        """
        ejecutar_consulta_segura(query, (siguiente_numero, tipo_documento))
    
    def _guardar_numeracion(self, tipo_documento: str, config: Dict[str, Any]):
        """Guarda configuración de numeración en BD"""
        query = """
            INSERT OR REPLACE INTO numeracion_documentos 
            (tipo_documento, prefijo, siguiente_numero, longitud_numero, sucursal, terminal_pos)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        
        ejecutar_consulta_segura(query, (
            tipo_documento,
            config['prefijo'],
            config['siguiente_numero'],
            config['longitud_numero'],
            config['sucursal'],
            config['terminal_pos']
        ))
    
    def _guardar_impuesto(self, impuesto: ConfiguracionImpuesto):
        """Guarda configuración de impuesto en BD"""
        query = """
            INSERT OR REPLACE INTO impuestos 
            (tipo, nombre, tasa, activo, codigo_hacienda, descripcion)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        
        ejecutar_consulta_segura(query, (
            impuesto.tipo.value,
            impuesto.nombre,
            float(impuesto.tasa),
            impuesto.activo,
            impuesto.codigo_hacienda,
            impuesto.descripcion
        ))
    
    def actualizar_datos_empresa(self, datos: Dict[str, str]) -> bool:
        """Actualiza los datos de la empresa"""
        try:
            for campo, valor in datos.items():
                if campo.startswith(('empresa_', 'fiscal_')):
                    query = "INSERT OR REPLACE INTO configuraciones (clave, valor) VALUES (?, ?)"
                    ejecutar_consulta_segura(query, (campo, valor))
            
            # Limpiar cache para forzar recarga
            self._datos_empresa = None
            
            self.logger.info("Datos de empresa actualizados exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error actualizando datos de empresa: {e}")
            return False
    
    def actualizar_impuesto(self, tipo: str, tasa: Decimal, activo: bool = True) -> bool:
        """Actualiza la configuración de un impuesto"""
        try:
            query = """
                UPDATE impuestos SET tasa = ?, activo = ? WHERE tipo = ?
            """
            
            success, message = ejecutar_consulta_segura(query, (float(tasa), activo, tipo))
            
            if success:
                # Limpiar cache
                self._impuestos = None
                self.logger.info(f"Impuesto {tipo} actualizado: tasa={tasa}, activo={activo}")
                return True
            else:
                self.logger.error(f"Error actualizando impuesto: {message}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error actualizando impuesto: {e}")
            return False
    
    def obtener_tasa_iva(self) -> Decimal:
        """Obtiene la tasa de IVA actual"""
        for impuesto in self.impuestos:
            if impuesto.tipo == TipoImpuesto.IVA and impuesto.activo:
                return impuesto.tasa
        return Decimal('0.13')  # Tasa por defecto en Costa Rica
    
    def validar_identificacion(self, identificacion: str, tipo: str) -> tuple[bool, str]:
        """Valida una identificación según su tipo"""
        try:
            # Remover espacios y guiones
            id_limpia = identificacion.replace(' ', '').replace('-', '')
            
            if tipo == TipoIdentificacion.CEDULA_FISICA.value:
                return self._validar_cedula_fisica(id_limpia)
            elif tipo == TipoIdentificacion.CEDULA_JURIDICA.value:
                return self._validar_cedula_juridica(id_limpia)
            elif tipo == TipoIdentificacion.DIMEX.value:
                return self._validar_dimex(id_limpia)
            else:
                return True, "Tipo de identificación válido"
                
        except Exception as e:
            return False, f"Error validando identificación: {e}"
    
    def _validar_cedula_fisica(self, cedula: str) -> tuple[bool, str]:
        """Valida cédula física costarricense"""
        if len(cedula) != 9 or not cedula.isdigit():
            return False, "Cédula física debe tener 9 dígitos"
        
        if cedula.startswith(('0', '1', '2', '3', '4', '5', '6', '7')):
            return True, "Cédula física válida"
        else:
            return False, "Cédula física con formato inválido"
    
    def _validar_cedula_juridica(self, cedula: str) -> tuple[bool, str]:
        """Valida cédula jurídica costarricense"""
        if len(cedula) != 10 or not cedula.isdigit():
            return False, "Cédula jurídica debe tener 10 dígitos"
        
        if cedula.startswith('3'):
            return True, "Cédula jurídica válida"
        else:
            return False, "Cédula jurídica debe iniciar con 3"
    
    def _validar_dimex(self, dimex: str) -> tuple[bool, str]:
        """Valida DIMEX (Documento de Identidad Migratoria para Extranjeros)"""
        if len(dimex) in [11, 12] and dimex.isdigit():
            return True, "DIMEX válido"
        else:
            return False, "DIMEX debe tener 11 o 12 dígitos"
    
    def generar_resumen_configuracion(self) -> Dict[str, Any]:
        """Genera un resumen de la configuración actual"""
        return {
            'empresa': {
                'razon_social': self.datos_empresa.razon_social,
                'identificacion': self.datos_empresa.identificacion,
                'email': self.datos_empresa.email,
                'telefono': self.datos_empresa.telefono
            },
            'impuestos': [
                {
                    'tipo': imp.tipo.value,
                    'nombre': imp.nombre,
                    'tasa': float(imp.tasa * 100),  # Convertir a porcentaje
                    'activo': imp.activo
                } for imp in self.impuestos
            ],
            'numeracion': {
                tipo: {
                    'siguiente_numero': config['siguiente_numero'],
                    'prefijo': config['prefijo']
                } for tipo, config in self.numeracion.items()
            }
        }
    
    def reiniciar_cache(self):
        """Reinicia el cache de configuración"""
        self._datos_empresa = None
        self._impuestos = None
        self._numeracion = None

# Instancia global
parametros_facturacion = ParametrosFacturacion()
