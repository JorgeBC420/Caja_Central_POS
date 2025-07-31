from core.calculadora_caja import CalculadoraCaja
class InvoiceManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def crear_factura(self, cliente, productos, usuario_id):
        # Lógica para crear una factura en la base de datos
        pass

    def registrar_pago(self, factura_id, monto, metodo_pago):
        # Lógica para registrar el pago de una factura
        pass