# product.py
class Product:
    def __init__(self, id, name, price, stock, iva_rate=0.13):
        self.id = id
        self.name = name
        self.price = price
        self.stock = stock
        self.iva_rate = iva_rate

# inventory.py
class InventoryManager:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def add_product(self, product_data):
        """Agrega nuevo producto al inventario"""
        pass
    
    def update_stock(self, product_id, quantity):
        """Actualiza niveles de inventario"""
        pass
    
    def get_low_stock_items(self, threshold=5):
        """Devuelve productos con stock bajo"""
        pass