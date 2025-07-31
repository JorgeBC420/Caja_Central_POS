class ElectronicInvoice:
    def __init__(self, cliente, productos, total, fecha, consecutivo):
        self.cliente = cliente
        self.productos = productos
        self.total = total
        self.fecha = fecha
        self.consecutivo = consecutivo

    def generar_xml(self):
        # Lógica para generar el XML de la factura electrónica
        pass

    def validar_datos(self):
        # Validaciones requeridas por Hacienda
        pass