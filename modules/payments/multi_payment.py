"""
Sistema de pagos múltiples para el POS
Manejo de múltiples formas de pago en una sola transacción
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from modules.api.database import db_manager, ejecutar_consulta_segura

class TipoPago(Enum):
    """Tipos de pago disponibles"""
    EFECTIVO = "efectivo"
    TARJETA_DEBITO = "tarjeta_debito"
    TARJETA_CREDITO = "tarjeta_credito"
    TRANSFERENCIA = "transferencia"
    CHEQUE = "cheque"
    VALE = "vale"
    CREDITO = "credito"
    SINPE_MOVIL = "sinpe_movil"
    CRYPTO = "crypto"
    PUNTOS = "puntos"

class EstadoPago(Enum):
    """Estados de un pago"""
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando" 
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    CANCELADO = "cancelado"
    REEMBOLSADO = "reembolsado"

@dataclass
class DetallePago:
    """Detalle de un pago individual"""
    tipo_pago: str
    monto: float
    referencia: str = ""
    banco: str = ""
    numero_tarjeta: str = ""  # Solo últimos 4 dígitos
    numero_autorizacion: str = ""
    fecha_vencimiento: str = ""  # Para cheques
    titular: str = ""
    estado: str = EstadoPago.PENDIENTE.value
    comision: float = 0.0
    datos_adicionales: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.datos_adicionales is None:
            self.datos_adicionales = {}

@dataclass
class TransaccionPago:
    """Transacción de pago completa"""
    id: str
    total_venta: float
    pagos: List[DetallePago]
    total_pagado: float = 0.0
    cambio: float = 0.0
    estado: str = EstadoPago.PENDIENTE.value
    fecha_creacion: str = ""
    fecha_completado: str = ""
    usuario_id: int = 0
    cliente_id: int = 0
    venta_id: int = 0
    notas: str = ""
    
    def __post_init__(self):
        if not self.fecha_creacion:
            self.fecha_creacion = datetime.now().isoformat()
        
        self.total_pagado = sum(pago.monto for pago in self.pagos)
        self.cambio = max(0, self.total_pagado - self.total_venta)

class ValidadorPagos:
    """Validador de métodos de pago"""
    
    @staticmethod
    def validar_numero_tarjeta(numero: str) -> Tuple[bool, str, str]:
        """Valida número de tarjeta usando algoritmo de Luhn"""
        try:
            # Limpiar número
            numero_limpio = ''.join(filter(str.isdigit, numero))
            
            if len(numero_limpio) < 13 or len(numero_limpio) > 19:
                return False, "Número de tarjeta debe tener entre 13 y 19 dígitos", ""
            
            # Algoritmo de Luhn
            def luhn_checksum(num):
                digits = [int(x) for x in num]
                for i in range(len(digits) - 2, -1, -2):
                    digits[i] *= 2
                    if digits[i] > 9:
                        digits[i] -= 9
                return sum(digits) % 10
            
            if luhn_checksum(numero_limpio) != 0:
                return False, "Número de tarjeta inválido", ""
            
            # Identificar tipo de tarjeta
            tipo_tarjeta = ValidadorPagos._identificar_tipo_tarjeta(numero_limpio)
            
            return True, "Tarjeta válida", tipo_tarjeta
            
        except Exception as e:
            return False, f"Error validando tarjeta: {e}", ""
    
    @staticmethod
    def _identificar_tipo_tarjeta(numero: str) -> str:
        """Identifica el tipo de tarjeta"""
        if numero.startswith('4'):
            return "Visa"
        elif numero.startswith('5') or numero.startswith('2'):
            return "Mastercard"
        elif numero.startswith('3'):
            if numero.startswith('34') or numero.startswith('37'):
                return "American Express"
            else:
                return "Diners"
        elif numero.startswith('6'):
            return "Discover"
        else:
            return "Desconocida"
    
    @staticmethod
    def validar_fecha_vencimiento(fecha: str) -> bool:
        """Valida fecha de vencimiento MM/YY"""
        try:
            if '/' not in fecha:
                return False
            
            mes, año = fecha.split('/')
            
            if len(mes) != 2 or len(año) != 2:
                return False
            
            mes = int(mes)
            año = int(f"20{año}")
            
            if mes < 1 or mes > 12:
                return False
            
            fecha_vencimiento = datetime(año, mes, 1)
            fecha_actual = datetime.now()
            
            return fecha_vencimiento >= fecha_actual
            
        except:
            return False
    
    @staticmethod
    def validar_cvv(cvv: str, tipo_tarjeta: str) -> bool:
        """Valida código CVV"""
        if not cvv.isdigit():
            return False
        
        if tipo_tarjeta == "American Express":
            return len(cvv) == 4
        else:
            return len(cvv) == 3
    
    @staticmethod
    def validar_sinpe(numero_telefono: str) -> bool:
        """Valida número de teléfono para SINPE Móvil"""
        telefono_limpio = ''.join(filter(str.isdigit, numero_telefono))
        
        # 8 dígitos para Costa Rica
        if len(telefono_limpio) == 8:
            return telefono_limpio[0] in ['2', '4', '6', '7', '8']
        
        # 11 dígitos con código de país
        if len(telefono_limpio) == 11 and telefono_limpio.startswith('506'):
            return telefono_limpio[3] in ['2', '4', '6', '7', '8']
        
        return False

class CalculadoraCaja:
    """Calculadora avanzada para manejo de caja y cambio"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.precision = Decimal('0.01')  # Centimos
    
    def calcular_cambio_optimo(self, cambio: float, denominaciones_disponibles: Dict[str, int]) -> Dict[str, int]:
        """
        Calcula el cambio óptimo usando las denominaciones disponibles
        
        Args:
            cambio: Monto de cambio a dar
            denominaciones_disponibles: {denominacion: cantidad_disponible}
            
        Returns:
            Diccionario con denominaciones a dar: {denominacion: cantidad_usar}
        """
        try:
            cambio_decimal = Decimal(str(cambio)).quantize(self.precision, rounding=ROUND_HALF_UP)
            cambio_restante = cambio_decimal
            
            # Ordenar denominaciones de mayor a menor
            denominaciones_ordenadas = sorted(
                [(Decimal(str(denom)), cant) for denom, cant in denominaciones_disponibles.items()],
                key=lambda x: x[0],
                reverse=True
            )
            
            cambio_dar = {}
            
            for denominacion, cantidad_disponible in denominaciones_ordenadas:
                if cambio_restante <= 0:
                    break
                
                cantidad_necesaria = int(cambio_restante / denominacion)
                cantidad_usar = min(cantidad_necesaria, cantidad_disponible)
                
                if cantidad_usar > 0:
                    cambio_dar[str(float(denominacion))] = cantidad_usar
                    cambio_restante -= denominacion * cantidad_usar
            
            # Verificar si se pudo dar cambio exacto
            if cambio_restante > 0:
                self.logger.warning(f"No se puede dar cambio exacto. Faltante: {cambio_restante}")
            
            return cambio_dar
            
        except Exception as e:
            self.logger.error(f"Error calculando cambio óptimo: {e}")
            return {}
    
    def redondear_monto(self, monto: float, regla: str = "normal") -> float:
        """
        Redondea monto según reglas de redondeo
        
        Args:
            monto: Monto a redondear
            regla: "normal", "up", "down", "bankers"
        """
        try:
            monto_decimal = Decimal(str(monto))
            
            if regla == "normal":
                return float(monto_decimal.quantize(self.precision, rounding=ROUND_HALF_UP))
            elif regla == "up":
                return float(monto_decimal.quantize(self.precision, rounding='ROUND_UP'))
            elif regla == "down":
                return float(monto_decimal.quantize(self.precision, rounding='ROUND_DOWN'))
            elif regla == "bankers":
                return float(monto_decimal.quantize(self.precision, rounding='ROUND_HALF_EVEN'))
            else:
                return float(monto_decimal.quantize(self.precision, rounding=ROUND_HALF_UP))
                
        except Exception as e:
            self.logger.error(f"Error redondeando monto: {e}")
            return monto
    
    def validar_denominaciones_caja(self, denominaciones: Dict[str, int]) -> Tuple[bool, str, float]:
        """Valida y calcula total de denominaciones en caja"""
        try:
            total = Decimal('0')
            denominaciones_validas = [
                '50000', '20000', '10000', '5000', '2000', '1000',  # Billetes
                '500', '100', '50', '25', '10', '5'  # Monedas
            ]
            
            for denom_str, cantidad in denominaciones.items():
                try:
                    denominacion = Decimal(denom_str)
                    
                    if denom_str not in denominaciones_validas:
                        return False, f"Denominación no válida: {denom_str}", 0.0
                    
                    if cantidad < 0:
                        return False, f"Cantidad no puede ser negativa para denominación {denom_str}", 0.0
                    
                    total += denominacion * cantidad
                    
                except (ValueError, TypeError):
                    return False, f"Denominación o cantidad inválida: {denom_str}", 0.0
            
            return True, "Denominaciones válidas", float(total)
            
        except Exception as e:
            return False, f"Error validando denominaciones: {e}", 0.0

class ProcessorPagosMultiples:
    """Procesador de pagos múltiples"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validador = ValidadorPagos()
        self.calculadora = CalculadoraCaja()
    
    def procesar_pago_multiple(self, transaccion: TransaccionPago) -> Tuple[bool, str, TransaccionPago]:
        """
        Procesa una transacción con múltiples métodos de pago
        
        Args:
            transaccion: Transacción de pago a procesar
            
        Returns:
            Tupla (éxito, mensaje, transacción_actualizada)
        """
        try:
            # Validar transacción
            validacion_ok, mensaje_validacion = self._validar_transaccion(transaccion)
            if not validacion_ok:
                return False, mensaje_validacion, transaccion
            
            # Procesar cada pago individual
            pagos_aprobados = []
            pagos_rechazados = []
            
            for i, pago in enumerate(transaccion.pagos):
                exito_pago, mensaje_pago, pago_actualizado = self._procesar_pago_individual(pago)
                
                if exito_pago:
                    pagos_aprobados.append(pago_actualizado)
                else:
                    pagos_rechazados.append((pago_actualizado, mensaje_pago))
                    self.logger.warning(f"Pago {i+1} rechazado: {mensaje_pago}")
            
            # Verificar si todos los pagos fueron aprobados
            if pagos_rechazados:
                # Reversar pagos aprobados
                for pago_aprobado in pagos_aprobados:
                    self._reversar_pago(pago_aprobado)
                
                transaccion.estado = EstadoPago.RECHAZADO.value
                mensajes_rechazo = [f"Pago {i+1}: {msg}" for i, (_, msg) in enumerate(pagos_rechazados)]
                return False, f"Pagos rechazados: {'; '.join(mensajes_rechazo)}", transaccion
            
            # Actualizar transacción
            transaccion.pagos = pagos_aprobados
            transaccion.total_pagado = sum(pago.monto for pago in pagos_aprobados)
            transaccion.cambio = max(0, transaccion.total_pagado - transaccion.total_venta)
            transaccion.estado = EstadoPago.APROBADO.value
            transaccion.fecha_completado = datetime.now().isoformat()
            
            # Guardar transacción en BD
            exito_guardado = self._guardar_transaccion(transaccion)
            if not exito_guardado:
                # Reversar todos los pagos
                for pago in pagos_aprobados:
                    self._reversar_pago(pago)
                return False, "Error guardando transacción", transaccion
            
            self.logger.info(f"Transacción procesada exitosamente: {transaccion.id}")
            return True, "Pago procesado exitosamente", transaccion
            
        except Exception as e:
            error_msg = f"Error procesando pago múltiple: {e}"
            self.logger.error(error_msg)
            return False, error_msg, transaccion
    
    def _validar_transaccion(self, transaccion: TransaccionPago) -> Tuple[bool, str]:
        """Valida una transacción de pago"""
        try:
            # Verificar que hay pagos
            if not transaccion.pagos:
                return False, "No hay métodos de pago especificados"
            
            # Verificar monto total
            if transaccion.total_venta <= 0:
                return False, "El total de la venta debe ser mayor a cero"
            
            # Verificar que el total pagado cubra la venta
            total_pagos = sum(pago.monto for pago in transaccion.pagos)
            if total_pagos < transaccion.total_venta:
                faltante = transaccion.total_venta - total_pagos
                return False, f"Monto insuficiente. Falta: ₡{faltante:.2f}"
            
            # Validar cada pago individual
            for i, pago in enumerate(transaccion.pagos):
                if pago.monto <= 0:
                    return False, f"Pago {i+1}: El monto debe ser mayor a cero"
                
                if not pago.tipo_pago:
                    return False, f"Pago {i+1}: Debe especificar el tipo de pago"
                
                # Validaciones específicas por tipo de pago
                validacion_ok, mensaje = self._validar_pago_por_tipo(pago)
                if not validacion_ok:
                    return False, f"Pago {i+1}: {mensaje}"
            
            return True, "Transacción válida"
            
        except Exception as e:
            return False, f"Error validando transacción: {e}"
    
    def _validar_pago_por_tipo(self, pago: DetallePago) -> Tuple[bool, str]:
        """Valida pago según su tipo"""
        try:
            tipo = pago.tipo_pago.lower()
            
            if tipo == TipoPago.EFECTIVO.value:
                return True, "Pago en efectivo válido"
            
            elif tipo in [TipoPago.TARJETA_DEBITO.value, TipoPago.TARJETA_CREDITO.value]:
                if not pago.numero_tarjeta or len(pago.numero_tarjeta) < 4:
                    return False, "Debe especificar los últimos 4 dígitos de la tarjeta"
                
                if not pago.numero_autorizacion:
                    return False, "Número de autorización requerido"
                
                return True, "Tarjeta válida"
            
            elif tipo == TipoPago.CHEQUE.value:
                if not pago.referencia:
                    return False, "Número de cheque requerido"
                
                if not pago.banco:
                    return False, "Banco emisor requerido"
                
                if not pago.titular:
                    return False, "Titular del cheque requerido"
                
                if pago.fecha_vencimiento:
                    if not self.validador.validar_fecha_vencimiento(pago.fecha_vencimiento):
                        return False, "Fecha de vencimiento inválida"
                
                return True, "Cheque válido"
            
            elif tipo == TipoPago.TRANSFERENCIA.value:
                if not pago.referencia:
                    return False, "Referencia de transferencia requerida"
                
                return True, "Transferencia válida"
            
            elif tipo == TipoPago.SINPE_MOVIL.value:
                if not pago.referencia:
                    return False, "Número de teléfono SINPE requerido"
                
                if not self.validador.validar_sinpe(pago.referencia):
                    return False, "Número de teléfono SINPE inválido"
                
                return True, "SINPE Móvil válido"
            
            elif tipo == TipoPago.CREDITO.value:
                # Validar límite de crédito del cliente
                return True, "Crédito válido"
            
            else:
                return True, f"Tipo de pago {tipo} válido"
                
        except Exception as e:
            return False, f"Error validando pago: {e}"
    
    def _procesar_pago_individual(self, pago: DetallePago) -> Tuple[bool, str, DetallePago]:
        """Procesa un pago individual"""
        try:
            pago.estado = EstadoPago.PROCESANDO.value
            
            tipo = pago.tipo_pago.lower()
            
            if tipo == TipoPago.EFECTIVO.value:
                # Efectivo siempre se aprueba (ya está validado)
                pago.estado = EstadoPago.APROBADO.value
                return True, "Pago en efectivo aprobado", pago
            
            elif tipo in [TipoPago.TARJETA_DEBITO.value, TipoPago.TARJETA_CREDITO.value]:
                # Simular procesamiento de tarjeta
                # En implementación real, aquí se conectaría con el procesador de pagos
                if self._simular_procesamiento_tarjeta(pago):
                    pago.estado = EstadoPago.APROBADO.value
                    return True, "Tarjeta aprobada", pago
                else:
                    pago.estado = EstadoPago.RECHAZADO.value
                    return False, "Tarjeta rechazada", pago
            
            elif tipo == TipoPago.CHEQUE.value:
                # Los cheques se aprueban pero quedan pendientes de cobro
                pago.estado = EstadoPago.APROBADO.value
                pago.datos_adicionales['pendiente_cobro'] = True
                return True, "Cheque aceptado", pago
            
            elif tipo == TipoPago.TRANSFERENCIA.value:
                # Transferencias se aprueban (requieren verificación posterior)
                pago.estado = EstadoPago.APROBADO.value
                pago.datos_adicionales['requiere_verificacion'] = True
                return True, "Transferencia aceptada", pago
            
            elif tipo == TipoPago.SINPE_MOVIL.value:
                # SINPE Móvil requiere confirmación
                pago.estado = EstadoPago.APROBADO.value
                pago.datos_adicionales['requiere_confirmacion'] = True
                return True, "SINPE Móvil aceptado", pago
            
            else:
                pago.estado = EstadoPago.APROBADO.value
                return True, f"Pago {tipo} aprobado", pago
                
        except Exception as e:
            pago.estado = EstadoPago.RECHAZADO.value
            return False, f"Error procesando pago: {e}", pago
    
    def _simular_procesamiento_tarjeta(self, pago: DetallePago) -> bool:
        """Simula procesamiento de tarjeta (para desarrollo)"""
        # En producción, aquí se conectaría con el procesador real
        # Por ahora, simular aprobación del 95% de las transacciones
        import random
        return random.random() > 0.05
    
    def _reversar_pago(self, pago: DetallePago) -> bool:
        """Reversa un pago previamente aprobado"""
        try:
            if pago.estado != EstadoPago.APROBADO.value:
                return True
            
            # Marcar como cancelado
            pago.estado = EstadoPago.CANCELADO.value
            
            # Aquí se implementaría la lógica específica de reversión
            # según el tipo de pago (reversa de tarjeta, etc.)
            
            self.logger.info(f"Pago revertido: {pago.tipo_pago} por ₡{pago.monto:.2f}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error reversando pago: {e}")
            return False
    
    def _guardar_transaccion(self, transaccion: TransaccionPago) -> bool:
        """Guarda transacción en base de datos"""
        try:
            # Convertir pagos a JSON
            pagos_json = json.dumps([asdict(pago) for pago in transaccion.pagos], ensure_ascii=False)
            
            query = """
                INSERT INTO transacciones_pago (
                    id, total_venta, pagos_json, total_pagado, cambio, estado,
                    fecha_creacion, fecha_completado, usuario_id, cliente_id, venta_id, notas
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                transaccion.id,
                transaccion.total_venta,
                pagos_json,
                transaccion.total_pagado,
                transaccion.cambio,
                transaccion.estado,
                transaccion.fecha_creacion,
                transaccion.fecha_completado,
                transaccion.usuario_id,
                transaccion.cliente_id,
                transaccion.venta_id,
                transaccion.notas
            )
            
            filas_afectadas = ejecutar_consulta_segura(query, params)
            return filas_afectadas > 0
            
        except Exception as e:
            self.logger.error(f"Error guardando transacción: {e}")
            return False
    
    def generar_recibo_pago(self, transaccion: TransaccionPago) -> str:
        """Genera recibo de pago formateado"""
        try:
            recibo = []
            recibo.append("=" * 40)
            recibo.append("         RECIBO DE PAGO")
            recibo.append("=" * 40)
            recibo.append(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            recibo.append(f"ID Transacción: {transaccion.id}")
            recibo.append("-" * 40)
            recibo.append(f"Total Venta:      ₡{transaccion.total_venta:>10,.2f}")
            recibo.append("")
            recibo.append("FORMAS DE PAGO:")
            
            for i, pago in enumerate(transaccion.pagos, 1):
                recibo.append(f"{i}. {pago.tipo_pago.replace('_', ' ').title()}")
                recibo.append(f"   Monto:         ₡{pago.monto:>10,.2f}")
                
                if pago.referencia:
                    recibo.append(f"   Referencia:    {pago.referencia}")
                if pago.numero_autorizacion:
                    recibo.append(f"   Autorización:  {pago.numero_autorizacion}")
                if pago.numero_tarjeta:
                    recibo.append(f"   Tarjeta:       ****{pago.numero_tarjeta}")
                
                recibo.append("")
            
            recibo.append("-" * 40)
            recibo.append(f"Total Pagado:     ₡{transaccion.total_pagado:>10,.2f}")
            
            if transaccion.cambio > 0:
                recibo.append(f"Cambio:           ₡{transaccion.cambio:>10,.2f}")
            
            recibo.append("=" * 40)
            recibo.append("   ¡GRACIAS POR SU COMPRA!")
            recibo.append("=" * 40)
            
            return "\n".join(recibo)
            
        except Exception as e:
            self.logger.error(f"Error generando recibo: {e}")
            return "Error generando recibo"

class SomeClass:
    """Clase de compatibilidad"""
    def __init__(self):
        self.calculadora = CalculadoraCaja()

# Instancia global del procesador
processor_pagos = ProcessorPagosMultiples()

# Funciones de utilidad
def procesar_pago_multiple(datos_transaccion: Dict) -> Tuple[bool, str]:
    """Función de utilidad para procesar pago múltiple"""
    try:
        # Convertir datos a objetos
        pagos = []
        for pago_data in datos_transaccion.get('pagos', []):
            pago = DetallePago(**pago_data)
            pagos.append(pago)
        
        transaccion = TransaccionPago(
            id=datos_transaccion.get('id', f"T{int(datetime.now().timestamp())}"),
            total_venta=datos_transaccion['total_venta'],
            pagos=pagos,
            usuario_id=datos_transaccion.get('usuario_id', 0),
            cliente_id=datos_transaccion.get('cliente_id', 0),
            venta_id=datos_transaccion.get('venta_id', 0)
        )
        
        exito, mensaje, _ = processor_pagos.procesar_pago_multiple(transaccion)
        return exito, mensaje
        
    except Exception as e:
        return False, f"Error procesando pago: {e}"

def calcular_cambio_denominaciones(cambio: float, denominaciones: Dict[str, int]) -> Dict[str, int]:
    """Función de utilidad para calculatear cambio con denominaciones"""
    calculadora = CalculadoraCaja()
    return calculadora.calcular_cambio_optimo(cambio, denominaciones)
