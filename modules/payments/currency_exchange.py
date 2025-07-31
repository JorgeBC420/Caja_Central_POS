
# currency_exchange.py

def get_exchange_rate(from_currency, to_currency):
    """Obtener tasa de cambio entre dos monedas."""
    return 1.0  # Tasa dummy

def convert_currency(amount, from_currency, to_currency):
    """Convertir monto entre monedas."""
    rate = get_exchange_rate(from_currency, to_currency)
    return amount * rate
