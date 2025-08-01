"""
Sistema de métodos de pago para POS de Costa Rica
Incluye manejo de múltiples monedas, comisiones y validaciones
"""

import logging
import re
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class TipoPago(Enum):
    """Tipos de métodos de pago disponibles"""
    EFECTIVO_CRC = "efectivo_crc"
    EFECTIVO_USD = "efectivo_usd"
    TARJETA_CREDITO = "tarjeta_credito"
    TARJETA_DEBITO = "tarjeta_debito"
    SINPE_MOVIL = "sinpe_movil"
    TRANSFERENCIA = "transferencia"
    CHEQUE = "cheque"
    BITCOIN = "bitcoin"

@dataclass
class InfoPago:
    """Información completa de un pago"""
    metodo: TipoPago
    monto: Decimal
    moneda: str
    referencia: Optional[str] = None
    banco: Optional[str] = None
    comision: Decimal = Decimal('0')
    tasa_cambio: Decimal = Decimal('1')
    monto_crc: Decimal = None
    fecha: datetime = None
    validado: bool = False
    
    def __post_init__(self):
        if self.fecha is None:
            self.fecha = datetime.now()
        if self.monto_crc is None:
            self.monto_crc = self.monto * self.tasa_cambio

class CurrencyManager:
    """Manejo de conversión de divisas"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Tasas de cambio por defecto (deberían venir de una API o configuración)
        self.tasas_cambio = {
            'USD': Decimal('560.00'),  # CRC por 1 USD
            'EUR': Decimal('620.00'),  # CRC por 1 EUR
            'CRC': Decimal('1.00'),    # Base
            'BTC': Decimal('28000000.00')  # CRC por 1 BTC (aproximado)
        }
        
    def obtener_tasa_cambio(self, moneda: str) -> Decimal:
        """Obtiene la tasa de cambio para una moneda específica"""
        return self.tasas_cambio.get(moneda.upper(), Decimal('1.00'))
    
    def actualizar_tasa_cambio(self, moneda: str, nueva_tasa: Decimal):
        """Actualiza la tasa de cambio de una moneda"""
        self.tasas_cambio[moneda.upper()] = nueva_tasa
        self.logger.info(f"Tasa de cambio actualizada: {moneda} = {nueva_tasa}")
    
    def convert_to_crc(self, monto: Decimal, moneda: str) -> Decimal:
        """Convierte un monto a colones costarricenses"""
        if moneda.upper() == 'CRC':
            return monto
        
        tasa = self.obtener_tasa_cambio(moneda)
        return monto * tasa
    
    def convert_from_crc(self, monto_crc: Decimal, moneda: str) -> Decimal:
        """Convierte colones a otra moneda"""
        if moneda.upper() == 'CRC':
            return monto_crc
        
        tasa = self.obtener_tasa_cambio(moneda)
        return monto_crc / tasa
    
    def calcular_cambio(self, monto_pagado: Decimal, total_venta: Decimal, 
                       moneda_pago: str) -> Dict[str, Any]:
        """Calcula el cambio considerando la moneda de pago"""
        pagado_crc = self.convert_to_crc(monto_pagado, moneda_pago)
        cambio_crc = pagado_crc - total_venta
        
        if cambio_crc < 0:
            return {
                'error': 'Pago insuficiente',
                'faltante_crc': abs(cambio_crc),
                'faltante_moneda': abs(self.convert_from_crc(cambio_crc, moneda_pago))
            }
        
        return {
            'cambio_crc': cambio_crc,
            'cambio_usd': self.convert_from_crc(cambio_crc, 'USD'),
            'sugerencia_billetes': self._sugerir_billetes_cambio(cambio_crc)
        }
    
    def _sugerir_billetes_cambio(self, cambio_crc: Decimal) -> Dict[str, int]:
        """Sugiere denominaciones de billetes para el cambio"""
        billetes = [20000, 10000, 5000, 2000, 1000, 500, 100, 50, 25, 10, 5]
        resultado = {}
        
        cambio_restante = int(cambio_crc)
        
        for billete in billetes:
            cantidad = cambio_restante // billete
            if cantidad > 0:
                resultado[f"{billete}"] = cantidad
                cambio_restante -= cantidad * billete
        
        return resultado

class PaymentValidator:
    """Validador de pagos específicos"""
    
    @staticmethod
    def validar_tarjeta(numero_tarjeta: str) -> Tuple[bool, str]:
        """Valida número de tarjeta usando algoritmo de Luhn"""
        # Remover espacios y guiones
        numero = re.sub(r'[\s-]', '', numero_tarjeta)
        
        if not numero.isdigit():
            return False, "Número debe contener solo dígitos"
        
        if len(numero) < 13 or len(numero) > 19:
            return False, "Número de tarjeta inválido"
        
        # Algoritmo de Luhn
        total = 0
        reverse_digits = numero[::-1]
        
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n = n // 10 + n % 10
            total += n
        
        is_valid = total % 10 == 0
        tipo_tarjeta = PaymentValidator._detectar_tipo_tarjeta(numero)
        
        return is_valid, tipo_tarjeta
    
    @staticmethod
    def _detectar_tipo_tarjeta(numero: str) -> str:
        """Detecta el tipo de tarjeta basado en el número"""
        if numero.startswith('4'):
            return 'Visa'
        elif numero.startswith(('51', '52', '53', '54', '55')):
            return 'MasterCard'
        elif numero.startswith(('34', '37')):
            return 'American Express'
        else:
            return 'Desconocida'
    
    @staticmethod
    def validar_sinpe(numero_telefono: str) -> Tuple[bool, str]:
        """Valida número de teléfono para SINPE Móvil"""
        # Formato costarricense: +506 XXXX-XXXX o 506XXXXXXXX
        patron = r'^(\+?506)?[2,4,6,7,8]\d{7}$'
        numero_limpio = re.sub(r'[\s()-]', '', numero_telefono)
        
        if re.match(patron, numero_limpio):
            return True, f"Número válido: {numero_limpio}"
        else:
            return False, "Formato de teléfono inválido para Costa Rica"

class PaymentProcessor:
    """Procesador de pagos principal"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.currency_manager = CurrencyManager()
        self.validator = PaymentValidator()
        
        # Configuración de métodos de pago
        self.metodos_disponibles = {
            TipoPago.EFECTIVO_CRC: {
                'nombre': 'Efectivo CRC',
                'moneda': 'CRC',
                'comision': Decimal('0'),
                'requiere_validacion': False
            },
            TipoPago.EFECTIVO_USD: {
                'nombre': 'Efectivo USD',
                'moneda': 'USD',
                'comision': Decimal('0'),
                'requiere_validacion': False
            },
            TipoPago.TARJETA_CREDITO: {
                'nombre': 'Tarjeta de Crédito',
                'moneda': 'CRC',
                'comision': Decimal('0.03'),  # 3%
                'requiere_validacion': True
            },
            TipoPago.TARJETA_DEBITO: {
                'nombre': 'Tarjeta de Débito',
                'moneda': 'CRC',
                'comision': Decimal('0.015'),  # 1.5%
                'requiere_validacion': True
            },
            TipoPago.SINPE_MOVIL: {
                'nombre': 'SINPE Móvil',
                'moneda': 'CRC',
                'comision': Decimal('0'),
                'requiere_validacion': True
            },
            TipoPago.TRANSFERENCIA: {
                'nombre': 'Transferencia Bancaria',
                'moneda': 'CRC',
                'comision': Decimal('0.005'),  # 0.5%
                'requiere_validacion': True
            }
        }
    
    def procesar_pago(self, metodo: TipoPago, monto: Decimal, 
                     moneda: str = 'CRC', referencia: str = None,
                     banco: str = None) -> InfoPago:
        """Procesa un pago individual"""
        try:
            config_metodo = self.metodos_disponibles.get(metodo)
            if not config_metodo:
                raise ValueError(f"Método de pago no válido: {metodo}")
            
            # Calcular tasa de cambio
            tasa_cambio = self.currency_manager.obtener_tasa_cambio(moneda)
            
            # Calcular comisión
            comision = monto * config_metodo['comision']
            
            # Crear información del pago
            info_pago = InfoPago(
                metodo=metodo,
                monto=monto,
                moneda=moneda,
                referencia=referencia,
                banco=banco,
                comision=comision,
                tasa_cambio=tasa_cambio
            )
            
            # Validar si es necesario
            if config_metodo['requiere_validacion']:
                info_pago.validado = self._validar_pago(info_pago)
            else:
                info_pago.validado = True
            
            self.logger.info(f"Pago procesado: {metodo.value} por {monto} {moneda}")
            return info_pago
            
        except Exception as e:
            self.logger.error(f"Error procesando pago: {e}")
            raise
    
    def _validar_pago(self, info_pago: InfoPago) -> bool:
        """Valida un pago según su método"""
        try:
            if info_pago.metodo in [TipoPago.TARJETA_CREDITO, TipoPago.TARJETA_DEBITO]:
                if info_pago.referencia:
                    valido, mensaje = self.validator.validar_tarjeta(info_pago.referencia)
                    if not valido:
                        self.logger.warning(f"Tarjeta inválida: {mensaje}")
                        return False
                else:
                    self.logger.warning("Número de tarjeta requerido")
                    return False
            
            elif info_pago.metodo == TipoPago.SINPE_MOVIL:
                if info_pago.referencia:
                    valido, mensaje = self.validator.validar_sinpe(info_pago.referencia)
                    if not valido:
                        self.logger.warning(f"SINPE inválido: {mensaje}")
                        return False
                else:
                    self.logger.warning("Número de teléfono requerido para SINPE")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validando pago: {e}")
            return False

class MultiPaymentHandler:
    """Maneja pagos múltiples y mixtos"""
    
    def __init__(self):
        self.payment_processor = PaymentProcessor()
        self.currency_manager = CurrencyManager()
        self.logger = logging.getLogger(__name__)
    
    def process_mixed_payment(self, pagos: List[Dict], total_venta: Decimal) -> Dict[str, Any]:
        """
        Procesa una combinación de pagos
        pagos: [{'metodo': TipoPago, 'monto': Decimal, 'moneda': str, ...}, ...]
        """
        try:
            pagos_procesados = []
            total_pagado_crc = Decimal('0')
            total_comisiones = Decimal('0')
            
            for pago_data in pagos:
                metodo = pago_data['metodo']
                if isinstance(metodo, str):
                    metodo = TipoPago(metodo)
                
                info_pago = self.payment_processor.procesar_pago(
                    metodo=metodo,
                    monto=pago_data['monto'],
                    moneda=pago_data.get('moneda', 'CRC'),
                    referencia=pago_data.get('referencia'),
                    banco=pago_data.get('banco')
                )
                
                if not info_pago.validado:
                    raise ValueError(f"Pago inválido: {metodo.value}")
                
                pagos_procesados.append(info_pago)
                total_pagado_crc += info_pago.monto_crc
                total_comisiones += info_pago.comision
            
            # Calcular cambio
            cambio_info = self.currency_manager.calcular_cambio(
                total_pagado_crc, total_venta, 'CRC'
            )
            
            resultado = {
                'pagos': pagos_procesados,
                'total_pagado_crc': total_pagado_crc,
                'total_venta': total_venta,
                'total_comisiones': total_comisiones,
                'cambio_info': cambio_info,
                'pago_completo': total_pagado_crc >= total_venta,
                'resumen': self._generar_resumen_pago(pagos_procesados, total_venta)
            }
            
            self.logger.info(f"Pago múltiple procesado: {len(pagos)} métodos")
            return resultado
            
        except Exception as e:
            self.logger.error(f"Error procesando pago múltiple: {e}")
            raise
    
    def _generar_resumen_pago(self, pagos: List[InfoPago], total_venta: Decimal) -> Dict[str, Any]:
        """Genera un resumen del pago múltiple"""
        resumen_por_metodo = {}
        
        for pago in pagos:
            metodo_str = pago.metodo.value
            if metodo_str not in resumen_por_metodo:
                resumen_por_metodo[metodo_str] = {
                    'monto_total': Decimal('0'),
                    'comision_total': Decimal('0'),
                    'cantidad_transacciones': 0
                }
            
            resumen_por_metodo[metodo_str]['monto_total'] += pago.monto_crc
            resumen_por_metodo[metodo_str]['comision_total'] += pago.comision
            resumen_por_metodo[metodo_str]['cantidad_transacciones'] += 1
        
        return {
            'metodos_utilizados': len(resumen_por_metodo),
            'detalle_por_metodo': resumen_por_metodo,
            'total_transacciones': len(pagos)
        }
    
    def calcular_propina_sugerida(self, total_venta: Decimal, 
                                 porcentajes: List[float] = [10, 15, 20]) -> Dict[str, Decimal]:
        """Calcula propinas sugeridas"""
        propinas = {}
        
        for porcentaje in porcentajes:
            propina = total_venta * Decimal(str(porcentaje / 100))
            propinas[f"{porcentaje}%"] = propina
        
        return propinas

# ===== Funciones de utilidad =====
def obtener_metodos_pago_disponibles() -> List[Dict[str, str]]:
    """Retorna lista de métodos de pago disponibles"""
    processor = PaymentProcessor()
    metodos = []
    
    for metodo, config in processor.metodos_disponibles.items():
        metodos.append({
            'codigo': metodo.value,
            'nombre': config['nombre'],
            'moneda': config['moneda'],
            'comision': str(config['comision'])
        })
    
    return metodos

def validar_monto_pago(monto: str) -> Tuple[bool, Decimal]:
    """Valida y convierte un monto de pago"""
    try:
        monto_decimal = Decimal(str(monto))
        if monto_decimal <= 0:
            return False, Decimal('0')
        return True, monto_decimal
    except:
        return False, Decimal('0')
