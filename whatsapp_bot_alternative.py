"""
Bot WhatsApp Alternativo usando PyAutoGUI
Para casos donde Selenium no funciona correctamente
"""

import time
import pyautogui
import cv2
import numpy as np
from datetime import datetime
import subprocess
import os
import psutil
from core.ai_assistant import POSAIAssistant
from core.database import DatabaseManager

class WhatsAppBotPyAutoGUI:
    """Bot alternativo usando PyAutoGUI para automatización de escritorio"""
    
    def __init__(self):
        self.ai_assistant = None
        self.db = None
        self.is_running = False
        self.whatsapp_process = None
        
        print("🤖 Inicializando Bot WhatsApp (PyAutoGUI)...")
        self.setup_ai()
        
        # Configurar PyAutoGUI
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 1
        
    def setup_ai(self):
        """Inicializa el asistente de IA"""
        try:
            self.db = DatabaseManager()
            self.ai_assistant = POSAIAssistant(self.db)
            print("✅ Asistente IA cargado correctamente")
            
            status = self.ai_assistant.get_engine_status()
            print(f"🔧 Engines activos: {status['active_engines']}")
            
        except Exception as e:
            print(f"⚠️ Error cargando IA: {e}")
    
    def open_whatsapp_web(self):
        """Abre WhatsApp Web en el navegador predeterminado"""
        try:
            print("📱 Abriendo WhatsApp Web...")
            
            # Intentar abrir con Chrome específicamente
            chrome_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
            ]
            
            chrome_path = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_path = path
                    break
            
            if chrome_path:
                # Abrir Chrome con WhatsApp Web
                cmd = [
                    chrome_path,
                    "--new-window",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "https://web.whatsapp.com"
                ]
                
                self.whatsapp_process = subprocess.Popen(cmd)
                print("✅ Chrome abierto con WhatsApp Web")
                
                # Esperar a que cargue
                print("⏳ Esperando a que cargue WhatsApp Web...")
                time.sleep(10)
                
                return True
            else:
                # Fallback al navegador predeterminado
                import webbrowser
                webbrowser.open("https://web.whatsapp.com")
                print("✅ WhatsApp Web abierto en navegador predeterminado")
                return True
                
        except Exception as e:
            print(f"❌ Error abriendo WhatsApp Web: {e}")
            return False
    
    def find_whatsapp_window(self):
        """Encuentra la ventana de WhatsApp Web"""
        try:
            # Buscar ventana que contenga "WhatsApp"
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline']
                        if cmdline and any('whatsapp' in arg.lower() for arg in cmdline):
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return False
            
        except Exception as e:
            print(f"⚠️ Error buscando ventana WhatsApp: {e}")
            return False
    
    def take_screenshot(self):
        """Toma captura de pantalla de WhatsApp"""
        try:
            screenshot = pyautogui.screenshot()
            return np.array(screenshot)
        except Exception as e:
            print(f"⚠️ Error tomando captura: {e}")
            return None
    
    def find_unread_chats(self, screenshot):
        """Busca chats no leídos en la captura"""
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)
            
            # Buscar patrones circulares verdes (notificaciones)
            # Esto es una aproximación básica
            circles = cv2.HoughCircles(
                gray, cv2.HOUGH_GRADIENT, 1, 20,
                param1=50, param2=30, minRadius=5, maxRadius=25
            )
            
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                return len(circles)
            
            return 0
            
        except Exception as e:
            print(f"⚠️ Error detectando chats: {e}")
            return 0
    
    def click_first_unread_chat(self):
        """Hace clic en el primer chat no leído"""
        try:
            # Posición aproximada donde suelen estar los chats
            # Esto requeriría calibración según la resolución
            chat_x = 300  # Ajustar según pantalla
            chat_y = 200  # Ajustar según pantalla
            
            pyautogui.click(chat_x, chat_y)
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"⚠️ Error haciendo clic en chat: {e}")
            return False
    
    def read_last_message(self):
        """Lee el último mensaje de la conversación"""
        try:
            # Área aproximada donde aparecen los mensajes
            # Esto es muy básico y requeriría OCR real
            message_area = pyautogui.screenshot(region=(400, 300, 600, 100))
            
            # Aquí iría OCR para leer el texto
            # Por simplicidad, retornamos un mensaje de ejemplo
            return "Mensaje detectado por OCR"
            
        except Exception as e:
            print(f"⚠️ Error leyendo mensaje: {e}")
            return None
    
    def send_message(self, message):
        """Envía un mensaje escribiendo en el campo de texto"""
        try:
            # Hacer clic en el campo de texto (aproximado)
            text_field_x = 600  # Ajustar según pantalla
            text_field_y = 500  # Ajustar según pantalla
            
            pyautogui.click(text_field_x, text_field_y)
            time.sleep(1)
            
            # Escribir mensaje
            pyautogui.write(message, interval=0.05)
            time.sleep(1)
            
            # Presionar Enter
            pyautogui.press('enter')
            
            print(f"📤 Mensaje enviado: {message[:50]}...")
            return True
            
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
            return False
    
    def generate_response(self, message):
        """Genera respuesta usando IA"""
        try:
            if not self.ai_assistant:
                return "🤖 Gracias por tu mensaje. Te contactaremos pronto."
            
            # Contexto para WhatsApp
            context = """
            Estás respondiendo por WhatsApp.
            Sé amigable, conciso (máximo 200 caracteres).
            Usa emojis apropiados.
            """
            
            response = self.ai_assistant.ask(message, context=context)
            
            if response and response.get('answer'):
                answer = response['answer']
                if len(answer) > 200:
                    answer = answer[:197] + "..."
                return answer
            
            return "🤖 No pude procesar tu consulta. ¿Podrías reformularla?"
            
        except Exception as e:
            print(f"⚠️ Error generando respuesta: {e}")
            return "⚠️ Problema técnico. Te contactaremos pronto."
    
    def start_monitoring(self):
        """Inicia el monitoreo básico"""
        if not self.open_whatsapp_web():
            return
        
        print("🔍 Iniciando monitoreo básico...")
        print("⚠️ NOTA: Esta versión es básica y requiere configuración manual")
        print("💡 Para mejor funcionamiento, usa la versión con Selenium")
        
        self.is_running = True
        
        try:
            while self.is_running:
                # Tomar captura
                screenshot = self.take_screenshot()
                if screenshot is not None:
                    unread_count = self.find_unread_chats(screenshot)
                    
                    if unread_count > 0:
                        print(f"📩 {unread_count} mensajes detectados")
                        
                        # Intentar procesar (muy básico)
                        if self.click_first_unread_chat():
                            message = self.read_last_message()
                            if message:
                                response = self.generate_response(message)
                                self.send_message(response)
                
                time.sleep(5)  # Revisar cada 5 segundos
                
        except KeyboardInterrupt:
            print("\n🛑 Bot detenido por el usuario")
        except Exception as e:
            print(f"❌ Error en monitoreo: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Detiene el bot"""
        self.is_running = False
        
        if self.whatsapp_process:
            try:
                self.whatsapp_process.terminate()
            except:
                pass
        
        print("✅ Bot detenido")

def main():
    """Función principal para el bot alternativo"""
    print("🚀 CajaCentral POS - Bot WhatsApp (PyAutoGUI)")
    print("=" * 50)
    print("⚠️ VERSIÓN EXPERIMENTAL")
    print("💡 Usa esta versión solo si Selenium no funciona")
    print()
    
    try:
        # Verificar dependencias
        import pyautogui
        import cv2
        print("✅ Dependencias PyAutoGUI disponibles")
    except ImportError:
        print("❌ Faltan dependencias. Instala con:")
        print("pip install pyautogui opencv-python")
        return
    
    bot = WhatsAppBotPyAutoGUI()
    
    print("📱 Iniciando bot alternativo...")
    bot.start_monitoring()

if __name__ == "__main__":
    main()
