# payment_methods.py
class PaymentProcessor:
    def __init__(self):
        self.available_methods = {
            'cash_crc': {'name': 'Efectivo CRC', 'currency': 'CRC'},
            'cash_usd': {'name': 'Efectivo USD', 'currency': 'USD'},
            'visa': {'name': 'Visa', 'fee': 0.03},
            'mastercard': {'name': 'MasterCard', 'fee': 0.025},
            'sinpe': {'name': 'SINPE Móvil', 'fee': 0.0}
        }
    
    def process_payment(self, method, amount, reference=None):
        """Procesa un pago individual"""
        pass

# currency_exchange.py
class CurrencyManager:
    def __init__(self):
        self.exchange_rate = 560.0  # CRC por 1 USD
    
    def convert_to_crc(self, usd_amount):
        return usd_amount * self.exchange_rate
    
    def convert_to_usd(self, crc_amount):
        return crc_amount / self.exchange_rate

# multi_payment.py
class MultiPaymentHandler:
    def __init__(self):
        self.payment_processor = PaymentProcessor()
        self.currency_manager = CurrencyManager()
    
    def process_mixed_payment(self, payments):
        """Procesa combinación de pagos"""
        total_paid = 0
        results = []
        
        for payment in payments:
            processed = self._process_single_payment(payment)
            total_paid += processed['amount_crc']
            results.append(processed)
        
        return {
            'total_paid': total_paid,
            'payments': results
        }