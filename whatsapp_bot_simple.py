"""
Script simple para conectar tu AI Assistant con WhatsApp Web
Integra directamente con el sistema existente de ai_assistant.py
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Importar tu asistente IA existente
from core.ai_assistant import POSAIAssistant
from core.database import DatabaseManager

class SimpleWhatsAppBot:
    """Bot simple de WhatsApp que usa tu AI Assistant existente"""
    
    def __init__(self):
        self.driver = None
        self.ai_assistant = None
        self.db = None
        self.is_running = False
        self.processed_messages = set()
        
        print("🤖 Inicializando Bot de WhatsApp...")
        self.setup_ai()
        
    def setup_ai(self):
        """Inicializa el asistente de IA"""
        try:
            self.db = DatabaseManager()
            self.ai_assistant = POSAIAssistant(self.db)
            print("✅ Asistente IA cargado correctamente")
            
            # Mostrar engines disponibles
            status = self.ai_assistant.get_engine_status()
            print(f"🔧 Engines activos: {status['active_engines']}")
            
        except Exception as e:
            print(f"⚠️ Error cargando IA: {e}")
            print("📝 El bot funcionará con respuestas básicas")
    
    def setup_chrome(self):
        """Configura Chrome para WhatsApp Web"""
        try:
            print("🌐 Configurando Google Chrome específicamente...")
            
            chrome_options = Options()
            
            # Opciones para evitar errores de DevTools y forzar Chrome
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            chrome_options.add_argument("--remote-debugging-port=0")
            
            # Buscar Chrome específicamente (NO Edge)
            import os
            chrome_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe")
            ]
            
            chrome_binary = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_binary = path
                    print(f"✅ Google Chrome encontrado: {path}")
                    break
            
            if not chrome_binary:
                print("❌ Google Chrome no está instalado!")
                print("📥 Por favor instala Chrome desde: https://www.google.com/chrome/")
                print("⚠️ Edge u otros navegadores no son compatibles con esta función")
                return False
            
            # FORZAR el uso de Chrome específico
            chrome_options.binary_location = chrome_binary
            
            # Carpeta de datos de usuario
            session_dir = os.path.abspath("whatsapp_session")
            chrome_options.add_argument(f"--user-data-dir={session_dir}")
            
            # Configuraciones adicionales para evitar detección
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 2
            })
            
            # Instalar ChromeDriver automáticamente con configuración específica
            service = Service(ChromeDriverManager().install())
            service.creation_flags = 0x08000000  # CREATE_NO_WINDOW en Windows
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Verificar que es realmente Chrome
            try:
                user_agent = self.driver.execute_script("return navigator.userAgent;")
                if "Chrome" not in user_agent or "Edge" in user_agent:
                    print(f"❌ Navegador incorrecto detectado: {user_agent}")
                    self.driver.quit()
                    return False
                else:
                    print("✅ Google Chrome verificado correctamente")
            except:
                pass
            
            # Configurar el navegador para evitar detección
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Error configurando Chrome: {e}")
            print("💡 Sugerencias:")
            print("   1. Asegúrate de que Google Chrome esté instalado (no Edge)")
            print("   2. Cierra todas las ventanas de Chrome")
            print("   3. Ejecuta como administrador si es necesario")
            print("   4. Verifica que no haya procesos de Chrome en el Task Manager")
            return False
    
    def connect_whatsapp(self):
        """Conecta a WhatsApp Web"""
        if not self.setup_chrome():
            return False
        
        try:
            print("📱 Conectando a WhatsApp Web...")
            self.driver.get("https://web.whatsapp.com")
            
            print("📷 Por favor, escanea el código QR en tu teléfono...")
            print("⏳ Esperando conexión...")
            
            # Esperar hasta que aparezca la lista de chats
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='chat-list']"))
            )
            
            print("✅ WhatsApp conectado correctamente!")
            return True
            
        except Exception as e:
            print(f"❌ Error conectando WhatsApp: {e}")
            return False
    
    def start_monitoring(self):
        """Inicia el monitoreo de mensajes"""
        if not self.connect_whatsapp():
            return
        
        self.is_running = True
        print("👀 Monitoreando mensajes...")
        print("💡 Presiona Ctrl+C para detener")
        
        try:
            while self.is_running:
                self.check_for_messages()
                time.sleep(3)  # Revisar cada 3 segundos
                
        except KeyboardInterrupt:
            print("\n🛑 Bot detenido por el usuario")
        except Exception as e:
            print(f"❌ Error en monitoreo: {e}")
        finally:
            self.stop()
    
    def check_for_messages(self):
        """Revisa si hay mensajes nuevos"""
        try:
            # Buscar notificaciones de mensajes no leídos
            unread_badges = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "[data-testid='icon-unread']"
            )
            
            if unread_badges:
                print(f"📩 {len(unread_badges)} conversación(es) con mensajes nuevos")
                
                for badge in unread_badges[:3]:  # Procesar máximo 3 a la vez
                    try:
                        self.process_conversation(badge)
                        time.sleep(2)  # Pausa entre conversaciones
                    except Exception as e:
                        print(f"⚠️ Error procesando conversación: {e}")
                        continue
        
        except Exception as e:
            print(f"⚠️ Error revisando mensajes: {e}")
    
    def process_conversation(self, unread_badge):
        """Procesa una conversación específica"""
        try:
            # Hacer clic en la conversación
            chat_element = unread_badge.find_element(By.XPATH, "./ancestor::*[@data-testid='chat'][1]")
            contact_name = self.get_contact_name(chat_element)
            
            chat_element.click()
            time.sleep(1)
            
            # Obtener mensajes recientes
            messages = self.get_recent_messages()
            
            for msg in messages:
                if msg['is_incoming'] and msg['id'] not in self.processed_messages:
                    self.processed_messages.add(msg['id'])
                    
                    print(f"💬 {contact_name}: {msg['text'][:60]}...")
                    
                    # Generar respuesta con IA
                    response = self.generate_response(msg['text'], contact_name)
                    
                    if response:
                        self.send_message(response)
                        print(f"🤖 Respondido: {response[:60]}...")
                    
                    time.sleep(1)
        
        except Exception as e:
            print(f"⚠️ Error en conversación: {e}")
    
    def get_contact_name(self, chat_element):
        """Obtiene el nombre del contacto"""
        try:
            name_element = chat_element.find_element(
                By.CSS_SELECTOR, 
                "[data-testid='cell-frame-title']"
            )
            return name_element.text.strip()
        except:
            return "Cliente"
    
    def get_recent_messages(self):
        """Obtiene mensajes recientes de la conversación actual"""
        messages = []
        try:
            # Obtener contenedor de mensajes
            message_containers = self.driver.find_elements(
                By.CSS_SELECTOR,
                "[data-testid='msg-container']"
            )
            
            # Procesar últimos 3 mensajes
            for container in message_containers[-3:]:
                try:
                    # Verificar si es mensaje entrante (no saliente)
                    is_outgoing = "message-out" in container.get_attribute("class")
                    
                    if not is_outgoing:  # Solo mensajes entrantes
                        # Obtener texto del mensaje
                        text_elements = container.find_elements(
                            By.CSS_SELECTOR,
                            "[data-testid='conversation-text']"
                        )
                        
                        if text_elements:
                            message_text = text_elements[0].text.strip()
                            
                            # Crear ID único
                            message_id = f"{hash(message_text)}_{container.location}"
                            
                            messages.append({
                                'id': message_id,
                                'text': message_text,
                                'is_incoming': True,
                                'timestamp': datetime.now()
                            })
                
                except Exception as e:
                    continue
        
        except Exception as e:
            print(f"⚠️ Error obteniendo mensajes: {e}")
        
        return messages
    
    def generate_response(self, message, contact_name):
        """Genera respuesta usando el AI Assistant"""
        try:
            # Verificar horario (8 AM - 8 PM)
            current_hour = datetime.now().hour
            if not (8 <= current_hour <= 20):
                return "🕐 Estamos fuera del horario de atención (8:00 AM - 8:00 PM). Te responderemos en cuanto abramos. ¡Gracias!"
            
            # Saludos automáticos
            if any(saludo in message.lower() for saludo in ["hola", "buenos", "buenas", "hi"]):
                return f"¡Hola {contact_name}! 👋 Soy el asistente virtual de CajaCentral POS. ¿En qué puedo ayudarte?"
            
            # Despedidas
            if any(despedida in message.lower() for despedida in ["gracias", "bye", "chau", "adiós"]):
                return "¡De nada! 😊 Que tengas un excelente día. Estamos aquí cuando nos necesites."
            
            # Usar el AI Assistant si está disponible
            if self.ai_assistant:
                context = f"""
                Estás respondiendo por WhatsApp a {contact_name}.
                Sé amigable, conciso y profesional.
                Máximo 300 caracteres.
                Usa emojis apropiados.
                """
                
                ai_response = self.ai_assistant.ask(message, context=context)
                
                if ai_response and ai_response.get('answer'):
                    response = ai_response['answer']
                    
                    # Limitar longitud para WhatsApp
                    if len(response) > 300:
                        response = response[:297] + "..."
                    
                    # Agregar emoji según el tipo
                    if ai_response.get('type') == 'how_to':
                        response = "📋 " + response
                    elif ai_response.get('type') == 'error_help':
                        response = "🔧 " + response
                    
                    return response
            
            # Respuesta de fallback
            return "🤖 Gracias por tu mensaje. Un miembro de nuestro equipo te contactará pronto para ayudarte mejor."
        
        except Exception as e:
            print(f"⚠️ Error generando respuesta: {e}")
            return "⚠️ Disculpa, hay un problema técnico. Te contactaremos pronto."
    
    def send_message(self, message):
        """Envía un mensaje en WhatsApp"""
        try:
            # Esperar un poco (más natural)
            time.sleep(2)
            
            # Encontrar el campo de texto
            text_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    "[data-testid='conversation-compose-box-input']"
                ))
            )
            
            # Escribir mensaje
            text_box.click()
            text_box.clear()
            text_box.send_keys(message)
            
            # Enviar
            text_box.send_keys(Keys.ENTER)
            
            return True
        
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
            return False
    
    def stop(self):
        """Detiene el bot"""
        self.is_running = False
        if self.driver:
            print("🔒 Cerrando navegador...")
            self.driver.quit()
        print("✅ Bot detenido")
    
    def get_status(self):
        """Obtiene el estado actual del bot"""
        status = {
            "running": self.is_running,
            "messages_processed": len(self.processed_messages),
            "ai_available": self.ai_assistant is not None,
            "chrome_active": self.driver is not None
        }
        
        if self.ai_assistant:
            status["ai_engines"] = self.ai_assistant.get_engine_status()
        
        return status

def main():
    """Función principal para ejecutar el bot"""
    print("🚀 CajaCentral POS - Bot de WhatsApp con IA")
    print("=" * 50)
    
    bot = SimpleWhatsAppBot()
    
    # Mostrar estado
    status = bot.get_status()
    print(f"🤖 IA disponible: {'✅' if status['ai_available'] else '❌'}")
    
    if status['ai_available']:
        engines = status['ai_engines']['active_engines']
        print(f"🔧 Engines IA: {', '.join(engines) if engines else 'Solo reglas básicas'}")
    
    print("\n📱 Iniciando conexión con WhatsApp...")
    
    try:
        bot.start_monitoring()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
    finally:
        bot.stop()

if __name__ == "__main__":
    main()
