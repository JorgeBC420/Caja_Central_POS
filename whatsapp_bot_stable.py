"""
Bot WhatsApp Simplificado - Versión Estable
Enfoque minimalista pero funcional
"""

import time
import threading
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import subprocess
import os

# AI Assistant
from core.ai_assistant import POSAIAssistant
from core.database import DatabaseManager

class WhatsAppBotSimple:
    """Bot WhatsApp simplificado y estable"""
    
    def __init__(self):
        self.driver = None
        self.ai_assistant = None
        self.is_running = False
        self.processed_messages = set()
        
        print("🤖 Bot WhatsApp Simplificado v1.0")
        self.setup_ai()
    
    def setup_ai(self):
        """Configurar AI Assistant"""
        try:
            self.db = DatabaseManager()
            self.ai_assistant = POSAIAssistant(self.db)
            print("✅ AI Assistant listo")
        except Exception as e:
            print(f"⚠️ AI limitado: {e}")
    
    def start_chrome_minimal(self):
        """Inicia Chrome de forma minimalista"""
        try:
            print("🌐 Iniciando Google Chrome específicamente...")
            
            # Configuración mínima pero robusta
            options = Options()
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument("--remote-debugging-port=0")
            
            # Crear carpeta de sesión si no existe
            session_dir = os.path.abspath("whatsapp_session")
            os.makedirs(session_dir, exist_ok=True)
            options.add_argument(f"--user-data-dir={session_dir}")
            
            # Buscar Chrome ESPECÍFICAMENTE (no Edge ni otros)
            chrome_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe")
            ]
            
            chrome_binary = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_binary = path
                    print(f"✅ Chrome encontrado en: {path}")
                    break
            
            if not chrome_binary:
                print("❌ Google Chrome no encontrado!")
                print("📥 Descarga Chrome desde: https://www.google.com/chrome/")
                return False
            
            # FORZAR el uso de Chrome específico
            options.binary_location = chrome_binary
            
            # Evitar que use Edge o cualquier otro navegador
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.notifications": 2
            })
            
            # Intentar crear driver con Chrome específico
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                service.creation_flags = 0x08000000  # CREATE_NO_WINDOW en Windows
                self.driver = webdriver.Chrome(service=service, options=options)
                print("✅ Chrome iniciado con WebDriver Manager")
            except Exception as e1:
                print(f"⚠️ WebDriver Manager falló: {e1}")
                # Fallback directo
                try:
                    self.driver = webdriver.Chrome(options=options)
                    print("✅ Chrome iniciado directamente")
                except Exception as e2:
                    print(f"❌ Fallback también falló: {e2}")
                    return False
            
            # Verificar que realmente abrió Chrome
            try:
                user_agent = self.driver.execute_script("return navigator.userAgent;")
                if "Chrome" not in user_agent:
                    print(f"⚠️ Navegador detectado: {user_agent}")
                    print("❌ No es Chrome! Cerrando...")
                    self.driver.quit()
                    return False
                else:
                    print("✅ Chrome confirmado correctamente")
            except:
                pass  # Si no puede verificar, continúa
            
            print("✅ Chrome iniciado correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error con Chrome: {e}")
            return False
    
    def open_whatsapp(self):
        """Abrir WhatsApp Web"""
        if not self.start_chrome_minimal():
            return False
        
        try:
            print("📱 Conectando WhatsApp Web...")
            self.driver.get("https://web.whatsapp.com")
            
            print("📷 Escanea el código QR en tu teléfono")
            print("⏳ Esperando conexión (máximo 60 seg)...")
            
            # Esperar a que aparezca la interfaz principal
            wait = WebDriverWait(self.driver, 60)
            
            # Buscar elemento que indique que WhatsApp está cargado
            try:
                wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='chat-list']")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='chat']")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".two"))
                    )
                )
                print("✅ WhatsApp conectado!")
                return True
            except:
                print("⏰ Tiempo agotado. ¿Escaneaste el QR?")
                return False
                
        except Exception as e:
            print(f"❌ Error conectando WhatsApp: {e}")
            return False
    
    def find_unread_messages(self):
        """Buscar mensajes no leídos de forma simple"""
        try:
            # Buscar elementos que indiquen mensajes no leídos
            unread_indicators = self.driver.find_elements(
                By.CSS_SELECTOR,
                "span[data-testid='icon-unread'], .VOr2j, ._38M1B"
            )
            
            return len(unread_indicators)
            
        except Exception as e:
            print(f"⚠️ Error buscando mensajes: {e}")
            return 0
    
    def click_first_unread(self):
        """Hacer clic en el primer chat no leído"""
        try:
            # Buscar chat con mensaje no leído
            unread_chats = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div[data-testid='chat']:has(span[data-testid='icon-unread'])"
            )
            
            if not unread_chats:
                # Fallback: buscar por clase CSS
                unread_chats = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[role='listitem']:has(.VOr2j)"
                )
            
            if unread_chats:
                unread_chats[0].click()
                time.sleep(2)
                return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Error seleccionando chat: {e}")
            return False
    
    def get_last_message(self):
        """Obtener último mensaje de forma simple"""
        try:
            # Buscar todos los mensajes
            messages = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div[data-testid='conversation-text']"
            )
            
            if messages:
                # Tomar el último mensaje
                last_message = messages[-1].text.strip()
                
                # Verificar que no sea mensaje propio (outgoing)
                message_container = messages[-1].find_element(By.XPATH, "./ancestor::div[contains(@class, 'message')]")
                if "message-out" not in message_container.get_attribute("class"):
                    return last_message
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error leyendo mensaje: {e}")
            return None
    
    def send_response(self, message):
        """Enviar respuesta de forma simple"""
        try:
            # Buscar campo de texto
            text_selectors = [
                "div[data-testid='conversation-compose-box-input']",
                "div[contenteditable='true']",
                ".selectable-text"
            ]
            
            text_box = None
            for selector in text_selectors:
                try:
                    text_box = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if text_box:
                        break
                except:
                    continue
            
            if not text_box:
                print("❌ No se encontró campo de texto")
                return False
            
            # Escribir mensaje
            text_box.click()
            text_box.clear()
            text_box.send_keys(message)
            
            # Enviar
            text_box.send_keys(Keys.ENTER)
            
            print(f"📤 Enviado: {message[:50]}...")
            return True
            
        except Exception as e:
            print(f"❌ Error enviando: {e}")
            return False
    
    def generate_ai_response(self, message):
        """Generar respuesta con IA"""
        try:
            # Horario de atención
            hour = datetime.now().hour
            if not (8 <= hour <= 20):
                return "🕐 Fuera del horario de atención (8 AM - 8 PM). Te responderemos al abrir."
            
            # Saludos automáticos
            if any(word in message.lower() for word in ["hola", "buenos", "hi"]):
                return "¡Hola! 👋 Soy el asistente de CajaCentral POS. ¿En qué puedo ayudarte?"
            
            # IA si está disponible
            if self.ai_assistant:
                response = self.ai_assistant.ask(message, context="WhatsApp, máximo 200 caracteres")
                if response and response.get('answer'):
                    answer = response['answer']
                    return answer[:200] + "..." if len(answer) > 200 else answer
            
            # Respuesta por defecto
            return "🤖 Gracias por escribir. Un miembro del equipo te contactará pronto."
            
        except Exception as e:
            print(f"⚠️ Error generando respuesta: {e}")
            return "⚠️ Problema técnico. Te contactaremos pronto."
    
    def monitor_loop(self):
        """Loop principal de monitoreo"""
        print("👀 Iniciando monitoreo...")
        print("💡 Presiona Ctrl+C para detener\n")
        
        while self.is_running:
            try:
                unread_count = self.find_unread_messages()
                
                if unread_count > 0:
                    print(f"📩 {unread_count} mensaje(s) nuevo(s)")
                    
                    if self.click_first_unread():
                        message = self.get_last_message()
                        
                        if message and message not in self.processed_messages:
                            self.processed_messages.add(message)
                            
                            print(f"💬 Recibido: {message[:60]}...")
                            
                            response = self.generate_ai_response(message)
                            
                            if self.send_response(response):
                                print(f"✅ Respondido correctamente\n")
                            else:
                                print("❌ Fallo enviando respuesta\n")
                
                time.sleep(5)  # Revisar cada 5 segundos
                
            except Exception as e:
                print(f"⚠️ Error en loop: {e}")
                time.sleep(10)
    
    def start(self):
        """Iniciar el bot"""
        if not self.open_whatsapp():
            print("❌ No se pudo conectar WhatsApp")
            return
        
        self.is_running = True
        
        try:
            self.monitor_loop()
        except KeyboardInterrupt:
            print("\n🛑 Detenido por usuario")
        except Exception as e:
            print(f"\n❌ Error fatal: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Detener el bot"""
        self.is_running = False
        
        if self.driver:
            try:
                print("🔒 Cerrando navegador...")
                self.driver.quit()
            except:
                pass
        
        print("✅ Bot detenido completamente")

def main():
    """Función principal"""
    print("🚀 CajaCentral POS - Bot WhatsApp Simplificado")
    print("=" * 50)
    
    bot = WhatsAppBotSimple()
    bot.start()

if __name__ == "__main__":
    main()
