import requests

class HaciendaAPI:
    def __init__(self, api_url, token):
        self.api_url = api_url
        self.token = token

    def enviar_factura(self, xml_data):
        """Envía factura electrónica a Hacienda"""
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/xml'
        }
        response = requests.post(f"{self.api_url}/recepcion", data=xml_data, headers=headers)
        return response.json()

    def consultar_estado(self, clave):
        """Consulta el estado de una factura en Hacienda"""
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        response = requests.get(f"{self.api_url}/recepcion/{clave}", headers=headers)
        return response.json()