from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional
import logging

class ProductoVenta:
    """Clase para representar un producto en una venta"""
    def __init__(self, id, codigo, nombre, precio, cantidad, precio_manual=None, descuento_item=0, exento_impuesto=False):
        self.id = id
        self.codigo = codigo
        self.nombre = nombre
        self.precio = Decimal(str(precio))
        self.cantidad = Decimal(str(cantidad))
        self.precio_manual = Decimal(str(precio_manual)) if precio_manual else None
        self.descuento_item = Decimal(str(descuento_item))  # Descuento específico del item
        self.exento_impuesto = exento_impuesto
    
    @property
    def precio_efectivo(self):
        """Precio efectivo considerando precio manual"""
        return self.precio_manual if self.precio_manual else self.precio
    
    @property
    def subtotal_item(self):
        """Subtotal del item sin impuestos"""
        return self.precio_efectivo * self.cantidad - self.descuento_item

class CalculadoraCaja:
    def __init__(self, tasa_iva=0.13):
        if not (0 <= tasa_iva <= 1):
            raise ValueError("La tasa_iva debe estar entre 0 y 1 (por ejemplo, 0.13 para 13%)")
        self.tasa_iva = Decimal(str(tasa_iva))
        self.logger = logging.getLogger(__name__)

    def calcular_subtotal(self, productos: List[ProductoVenta]) -> Decimal:
        """Calcula el subtotal de todos los productos"""
        subtotal = Decimal('0')
        for producto in productos:
            precio_efectivo = producto.precio_manual if producto.precio_manual else producto.precio
            subtotal += precio_efectivo * producto.cantidad
        return self._redondear(subtotal)

    def calcular_descuentos_items(self, productos: List[ProductoVenta]) -> Decimal:
        """Calcula el total de descuentos específicos por item"""
        total_descuentos = sum(producto.descuento_item for producto in productos)
        return self._redondear(total_descuentos)

    def calcular_descuento_general(self, subtotal: Decimal, porcentaje: Decimal) -> Decimal:
        """Calcula el descuento general sobre el subtotal"""
        if porcentaje < 0 or porcentaje > 100:
            raise ValueError("El porcentaje de descuento debe estar entre 0 y 100")
        descuento = subtotal * (porcentaje / 100)
        return self._redondear(descuento)

    def calcular_base_imponible(self, productos: List[ProductoVenta], descuento_general: Decimal = Decimal('0')) -> Dict[str, Decimal]:
        """Calcula la base imponible separando productos gravados y exentos"""
        base_gravada = Decimal('0')
        base_exenta = Decimal('0')
        
        for producto in productos:
            subtotal_item = producto.subtotal_item
            
            if producto.exento_impuesto:
                base_exenta += subtotal_item
            else:
                base_gravada += subtotal_item
        
        # Aplicar descuento general proporcionalmente
        if descuento_general > 0:
            total_base = base_gravada + base_exenta
            if total_base > 0:
                factor_descuento = descuento_general / total_base
                descuento_gravado = base_gravada * factor_descuento
                descuento_exento = base_exenta * factor_descuento
                
                base_gravada -= descuento_gravado
                base_exenta -= descuento_exento
        
        return {
            'base_gravada': self._redondear(base_gravada),
            'base_exenta': self._redondear(base_exenta),
            'total_base': self._redondear(base_gravada + base_exenta)
        }

    def calcular_impuesto(self, base_gravada: Decimal) -> Decimal:
        """Calcula el impuesto sobre la base gravada"""
        impuesto = base_gravada * self.tasa_iva
        return self._redondear(impuesto)

    def calcular_total_venta(self, productos: List[ProductoVenta], descuento_porcentaje: Decimal = Decimal('0')) -> Dict[str, Decimal]:
        """Calcula todos los valores de una venta"""
        # Subtotal antes de descuentos
        subtotal_bruto = self.calcular_subtotal(productos)
        descuentos_items = self.calcular_descuentos_items(productos)
        subtotal_neto = subtotal_bruto - descuentos_items
        
        # Descuento general
        descuento_general = self.calcular_descuento_general(subtotal_neto, descuento_porcentaje)
        
        # Base imponible
        bases = self.calcular_base_imponible(productos, descuento_general)
        
        # Impuestos
        impuesto = self.calcular_impuesto(bases['base_gravada'])
        
        # Total final
        total = bases['total_base'] + impuesto
        
        return {
            'subtotal_bruto': self._redondear(subtotal_bruto),
            'descuentos_items': self._redondear(descuentos_items),
            'subtotal_neto': self._redondear(subtotal_neto),
            'descuento_general': self._redondear(descuento_general),
            'base_gravada': bases['base_gravada'],
            'base_exenta': bases['base_exenta'],
            'impuesto': self._redondear(impuesto),
            'total': self._redondear(total)
        }

    def calcular_cambio(self, total: Decimal, pago: Decimal) -> Decimal:
        """Calcula el cambio a devolver"""
        if pago < total:
            raise ValueError("El pago no puede ser menor al total")
        cambio = pago - total
        return self._redondear(cambio)

    def calcular_pago_multiple(self, total: Decimal, pagos: List[Dict]) -> Dict:
        """
        Calcula pagos múltiples (efectivo, tarjeta, etc.)
        pagos = [{'metodo': 'efectivo', 'monto': 10000}, {'metodo': 'tarjeta', 'monto': 5000}]
        """
        total_pagado = sum(Decimal(str(pago['monto'])) for pago in pagos)
        
        if total_pagado < total:
            return {
                'status': 'insuficiente',
                'total_pagado': self._redondear(total_pagado),
                'faltante': self._redondear(total - total_pagado),
                'cambio': Decimal('0')
            }
        
        cambio = total_pagado - total
        return {
            'status': 'completo',
            'total_pagado': self._redondear(total_pagado),
            'faltante': Decimal('0'),
            'cambio': self._redondear(cambio)
        }

    def convertir_moneda(self, monto: Decimal, tasa_cambio: Decimal, moneda_origen: str = 'CRC', moneda_destino: str = 'USD') -> Dict:
        """Convierte entre colones y dólares"""
        if moneda_origen == 'CRC' and moneda_destino == 'USD':
            monto_convertido = monto / tasa_cambio
        elif moneda_origen == 'USD' and moneda_destino == 'CRC':
            monto_convertido = monto * tasa_cambio
        else:
            raise ValueError("Solo se soporta conversión entre CRC y USD")
        
        return {
            'monto_original': self._redondear(monto),
            'monto_convertido': self._redondear(monto_convertido),
            'tasa_cambio': self._redondear(tasa_cambio),
            'moneda_origen': moneda_origen,
            'moneda_destino': moneda_destino
        }

    def aplicar_promocion(self, productos: List[ProductoVenta], promocion: Dict) -> Decimal:
        """
        Aplica una promoción específica
        promocion = {'tipo': 'porcentaje'|'monto', 'valor': decimal, 'productos_aplicables': [ids]}
        """
        descuento_total = Decimal('0')
        
        if promocion['tipo'] == 'porcentaje':
            for producto in productos:
                if not promocion.get('productos_aplicables') or producto.id in promocion['productos_aplicables']:
                    descuento_item = producto.subtotal_item * (Decimal(str(promocion['valor'])) / 100)
                    descuento_total += descuento_item
        
        elif promocion['tipo'] == 'monto':
            # Aplicar descuento fijo distribuido proporcionalmente
            subtotal_aplicable = sum(
                p.subtotal_item for p in productos 
                if not promocion.get('productos_aplicables') or p.id in promocion['productos_aplicables']
            )
            
            if subtotal_aplicable > 0:
                descuento_total = min(Decimal(str(promocion['valor'])), subtotal_aplicable)
        
        return self._redondear(descuento_total)

    def generar_resumen_impuestos(self, calculo_venta: Dict) -> Dict:
        """Genera resumen detallado de impuestos para facturación"""
        return {
            'base_gravada': calculo_venta['base_gravada'],
            'base_exenta': calculo_venta['base_exenta'],
            'tasa_impuesto': self.tasa_iva * 100,  # Convertir a porcentaje
            'monto_impuesto': calculo_venta['impuesto'],
            'total_con_impuesto': calculo_venta['total']
        }

    def _redondear(self, valor: Decimal) -> Decimal:
        """Redondea a 2 decimales usando redondeo bancario"""
        return valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def validar_precios(self, productos: List[ProductoVenta]) -> List[str]:
        """Valida que los precios sean correctos"""
        errores = []
        
        for producto in productos:
            if producto.precio <= 0:
                errores.append(f"Precio inválido para {producto.nombre}: {producto.precio}")
            
            if producto.cantidad <= 0:
                errores.append(f"Cantidad inválida para {producto.nombre}: {producto.cantidad}")
            
            if producto.precio_manual and producto.precio_manual <= 0:
                errores.append(f"Precio manual inválido para {producto.nombre}: {producto.precio_manual}")
        
        return errores