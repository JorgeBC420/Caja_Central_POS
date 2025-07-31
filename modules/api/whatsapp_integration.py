import webbrowser
import urllib.parse

class WhatsAppNotifier:
    def send_message(self, number, message):
        """Abre WhatsApp Web/Desktop con el mensaje prellenado para el número dado."""
        # El número debe estar en formato internacional, ej: 506XXXXXXXX
        mensaje_codificado = urllib.parse.quote(message)
        url = f"https://wa.me/{number}?text={mensaje_codificado}"
        webbrowser.open(url)