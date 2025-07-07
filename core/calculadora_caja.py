class CalculadoraCaja:
    def __init__(self, tasa_iva=0.13):
        if not (0 <= tasa_iva <= 1):
            raise ValueError("La tasa_iva debe estar entre 0 y 1 (por ejemplo, 0.13 para 13%)")
        self.tasa_iva = tasa_iva

    def calcular_subtotal(self, productos):
        """Calcula el subtotal usando precio normal, o precio_manual si está definido."""
        return sum(
            (p.precio_manual if hasattr(p, 'precio_manual') and p.precio_manual is not None else p.precio) * p.cantidad
            for p in productos
        )

    def calcular_descuento(self, subtotal, porcentaje):
        """Calcula el monto de descuento dado un porcentaje."""
        return subtotal * (porcentaje / 100)

    def calcular_impuesto(self, subtotal):
        """Calcula el impuesto sobre el subtotal."""
        return subtotal * self.tasa_iva

    def calcular_total(self, productos, descuento_porcentaje=0):
        """Calcula el total (subtotal - descuento + impuesto)."""
        subtotal = self.calcular_subtotal(productos)
        descuento = self.calcular_descuento(subtotal, descuento_porcentaje) if descuento_porcentaje > 0 else 0
        subtotal_con_descuento = subtotal - descuento
        impuesto = self.calcular_impuesto(subtotal_con_descuento)
        return subtotal_con_descuento + impuesto

    def calcular_cambio(self, total, pago):
        """Calcula el cambio a devolver."""
        return pago - total if pago >= total else 0