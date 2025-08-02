"""
WhatsApp AI Bot integrado con LLaMA
Conecta tu asistente de IA existente con WhatsApp Web
"""

import time
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from core.ai_assistant import POSAIAssistant
from core.database import DatabaseManager

class WhatsAppAIBot:
    """Bot de WhatsApp con IA integrada para atención al cliente"""
    
    def __init__(self, db_manager: DatabaseManager = None, headless: bool = False):
        self.db = db_manager
        self.driver = None
        self.ai_assistant = POSAIAssistant(db_manager)
        self.is_running = False
        self.processed_messages = set()
        self.client_conversations = {}
        self.headless = headless
        
        # Configuración del bot
        self.config = {
            "response_delay": 2,  # Segundos antes de responder
            "max_response_length": 1000,  # Caracteres máximos por respuesta
            "business_hours": {"start": 8, "end": 20},  # Horario de atención
            "auto_responses": True,
            "manual_mode": False,  # Si True, solo sugiere respuestas
            "keywords_for_human": ["urgente", "gerente", "queja", "problema grave"]
        }
        
        # Respuestas automáticas predefinidas
        self.quick_responses = {
            "saludo": [
                "¡Hola! 👋 Soy el asistente virtual de CajaCentral POS. ¿En qué puedo ayudarte?",
                "¡Buen día! 🌟 ¿Cómo puedo asistirte con tu sistema POS hoy?",
                "¡Hola! Estoy aquí para ayudarte con cualquier duda sobre tu sistema. ¿Qué necesitas?"
            ],
            "despedida": [
                "¡Gracias por contactarnos! 😊 Que tengas un excelente día.",
                "¡Hasta pronto! Si necesitas algo más, no dudes en escribir. 👋",
                "¡Fue un placer ayudarte! Estamos aquí cuando nos necesites. 🌟"
            ],
            "fuera_horario": "🕐 Actualmente estamos fuera del horario de atención (8:00 AM - 8:00 PM). Tu mensaje es importante, responderemos en cuanto abramos. ¡Gracias!",
            "derivar_humano": "🙋‍♂️ Tu consulta requiere atención personalizada. Un miembro de nuestro equipo te contactará pronto. Gracias por tu paciencia."
        }
    
    def setup_driver(self):
        """Configura el driver de Chrome para WhatsApp Web"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--user-data-dir=./whatsapp_session")  # Mantener sesión
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.get("https://web.whatsapp.com")
            
            print("🔗 WhatsApp Web abierto. Escanea el código QR si es necesario...")
            
            # Esperar a que cargue WhatsApp
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='chat-list']"))
            )
            
            print("✅ WhatsApp Web conectado correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error conectando WhatsApp: {e}")
            return False
    
    def start_bot(self):
        """Inicia el bot de WhatsApp"""
        if not self.setup_driver():
            return False
        
        self.is_running = True
        print("🤖 Bot de WhatsApp iniciado. Monitoreando mensajes...")
        
        try:
            while self.is_running:
                self.check_new_messages()
                time.sleep(2)  # Revisar cada 2 segundos
                
        except KeyboardInterrupt:
            print("\n🛑 Bot detenido por el usuario")
        except Exception as e:
            print(f"❌ Error en el bot: {e}")
        finally:
            self.stop_bot()
    
    def check_new_messages(self):
        """Revisa si hay mensajes nuevos y los procesa"""
        try:
            # Buscar conversaciones con mensajes no leídos
            unread_chats = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "[data-testid='chat'] [data-testid='icon-unread']"
            )
            
            for chat in unread_chats:
                try:
                    # Hacer click en la conversación
                    chat_container = chat.find_element(By.XPATH, "./ancestor::*[@data-testid='chat'][1]")
                    chat_container.click()
                    time.sleep(1)
                    
                    # Procesar mensajes de esta conversación
                    self.process_current_chat()
                    
                except Exception as e:
                    print(f"⚠️ Error procesando chat: {e}")
                    continue
        
        except Exception as e:
            print(f"⚠️ Error revisando mensajes: {e}")
    
    def process_current_chat(self):
        """Procesa los mensajes de la conversación actual"""
        try:
            # Obtener nombre del contacto
            contact_name = self.get_current_contact_name()
            
            # Obtener mensajes recientes
            messages = self.get_recent_messages()
            
            for message_data in messages:
                message_id = message_data.get("id")
                message_text = message_data.get("text", "")
                is_from_contact = message_data.get("is_from_contact", False)
                
                # Solo procesar mensajes del contacto que no hemos procesado
                if is_from_contact and message_id not in self.processed_messages:
                    self.processed_messages.add(message_id)
                    
                    print(f"📩 Nuevo mensaje de {contact_name}: {message_text[:50]}...")
                    
                    # Generar y enviar respuesta
                    response = self.generate_ai_response(message_text, contact_name)
                    if response:
                        self.send_message(response)
                        print(f"🤖 Respuesta enviada: {response[:50]}...")
        
        except Exception as e:
            print(f"⚠️ Error procesando conversación: {e}")
    
    def get_current_contact_name(self) -> str:
        """Obtiene el nombre del contacto actual"""
        try:
            contact_element = self.driver.find_element(
                By.CSS_SELECTOR, 
                "[data-testid='conversation-header'] [data-testid='conversation-info-header-chat-title']"
            )
            return contact_element.text.strip()
        except:
            return "Cliente"
    
    def get_recent_messages(self) -> List[Dict]:
        """Obtiene los mensajes recientes de la conversación"""
        messages = []
        try:
            # Obtener elementos de mensajes
            message_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                "[data-testid='msg-container']"
            )
            
            # Procesar últimos 5 mensajes
            for msg_element in message_elements[-5:]:
                try:
                    # Determinar si es mensaje entrante o saliente
                    is_outgoing = "message-out" in msg_element.get_attribute("class")
                    is_from_contact = not is_outgoing
                    
                    # Obtener texto del mensaje
                    text_element = msg_element.find_element(
                        By.CSS_SELECTOR,
                        "[data-testid='conversation-text']"
                    )
                    message_text = text_element.text.strip()
                    
                    # Crear ID único para el mensaje
                    message_id = f"{hash(message_text)}_{msg_element.location}"
                    
                    messages.append({
                        "id": message_id,
                        "text": message_text,
                        "is_from_contact": is_from_contact,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    continue
        
        except Exception as e:
            print(f"⚠️ Error obteniendo mensajes: {e}")
        
        return messages
    
    def generate_ai_response(self, message: str, contact_name: str = None) -> Optional[str]:
        """Genera respuesta usando el asistente de IA"""
        try:
            # Verificar horario de atención
            current_hour = datetime.now().hour
            if not (self.config["business_hours"]["start"] <= current_hour <= self.config["business_hours"]["end"]):
                return self.quick_responses["fuera_horario"]
            
            # Verificar si requiere atención humana
            if any(keyword in message.lower() for keyword in self.config["keywords_for_human"]):
                return self.quick_responses["derivar_humano"]
            
            # Detectar saludos
            if any(word in message.lower() for word in ["hola", "buenos", "buenas", "hi", "hello"]):
                import random
                return random.choice(self.quick_responses["saludo"])
            
            # Detectar despedidas
            if any(word in message.lower() for word in ["gracias", "bye", "chau", "adiós", "hasta"]):
                import random
                return random.choice(self.quick_responses["despedida"])
            
            # Agregar contexto específico de WhatsApp para la IA
            whatsapp_context = f"""
            Eres el asistente virtual oficial de CajaCentral POS respondiendo por WhatsApp.
            Cliente: {contact_name or 'Cliente'}
            Contexto: Atención al cliente via mensajería instantánea
            Estilo: Amigable, conciso, usa emojis apropiados
            Límite: Máximo {self.config['max_response_length']} caracteres
            """
            
            # Usar el asistente de IA existente
            ai_response = self.ai_assistant.ask(message, context=whatsapp_context)
            
            if ai_response and ai_response.get("answer"):
                response_text = ai_response["answer"]
                
                # Limitar longitud
                if len(response_text) > self.config["max_response_length"]:
                    response_text = response_text[:self.config["max_response_length"]-3] + "..."
                
                # Agregar emoji apropiado según el tipo de respuesta
                if ai_response.get("type") == "how_to":
                    response_text = "📋 " + response_text
                elif ai_response.get("type") == "error_help":
                    response_text = "🔧 " + response_text
                elif ai_response.get("type") == "shortcuts":
                    response_text = "⌨️ " + response_text
                
                return response_text
            
            return "🤖 Lo siento, no pude procesar tu consulta. ¿Podrías reformularla?"
            
        except Exception as e:
            print(f"⚠️ Error generando respuesta IA: {e}")
            return "⚠️ Disculpa, hay un problema técnico. Un agente te contactará pronto."
    
    def send_message(self, message: str):
        """Envía un mensaje en WhatsApp"""
        try:
            # Esperar un poco antes de responder (más natural)
            time.sleep(self.config["response_delay"])
            
            # Encontrar el campo de input
            input_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='conversation-compose-box-input']"))
            )
            
            # Limpiar y escribir mensaje
            input_box.clear()
            input_box.send_keys(message)
            
            # Enviar mensaje
            input_box.send_keys(Keys.ENTER)
            
            # Guardar en historial si hay DB
            if self.db:
                self.save_bot_interaction(message)
        
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
    
    def save_bot_interaction(self, message: str):
        """Guarda la interacción del bot en la base de datos"""
        try:
            # Implementar guardado en BD si es necesario
            pass
        except Exception as e:
            print(f"⚠️ Error guardando interacción: {e}")
    
    def set_manual_mode(self, enabled: bool):
        """Activa/desactiva modo manual (solo sugerencias)"""
        self.config["manual_mode"] = enabled
        mode = "manual" if enabled else "automático"
        print(f"🔄 Modo {mode} activado")
    
    def set_business_hours(self, start_hour: int, end_hour: int):
        """Configura horario de atención"""
        self.config["business_hours"] = {"start": start_hour, "end": end_hour}
        print(f"🕐 Horario configurado: {start_hour}:00 - {end_hour}:00")
    
    def add_keyword_for_human(self, keyword: str):
        """Agrega palabra clave que requiere atención humana"""
        self.config["keywords_for_human"].append(keyword.lower())
        print(f"👤 Palabra clave agregada: {keyword}")
    
    def get_bot_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del bot"""
        return {
            "messages_processed": len(self.processed_messages),
            "conversations_active": len(self.client_conversations),
            "is_running": self.is_running,
            "config": self.config,
            "ai_engine_status": self.ai_assistant.get_engine_status() if self.ai_assistant else None
        }
    
    def export_conversations(self) -> Dict[str, Any]:
        """Exporta conversaciones del bot"""
        return {
            "export_date": datetime.now().isoformat(),
            "conversations": self.client_conversations,
            "processed_messages": list(self.processed_messages),
            "bot_stats": self.get_bot_statistics()
        }
    
    def stop_bot(self):
        """Detiene el bot"""
        self.is_running = False
        if self.driver:
            self.driver.quit()
        print("🛑 Bot de WhatsApp detenido")


# Clase para UI de administración del bot
class WhatsAppBotUI:
    """Interfaz para administrar el bot de WhatsApp"""
    
    def __init__(self, bot: WhatsAppAIBot):
        self.bot = bot
        self.root = None
    
    def create_admin_window(self):
        """Crea ventana de administración del bot"""
        import tkinter as tk
        from tkinter import ttk, messagebox, scrolledtext
        
        # Crear ventana principal si no existe
        if not hasattr(tk, '_default_root') or tk._default_root is None:
            root = tk.Tk()
            root.withdraw()
        
        self.root = tk.Toplevel()
        self.root.title("🤖 Administrador Bot WhatsApp")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Notebook para pestañas
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña de Control
        control_frame = ttk.Frame(notebook)
        notebook.add(control_frame, text="🎮 Control")
        self.create_control_tab(control_frame)
        
        # Pestaña de Configuración
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="⚙️ Configuración")
        self.create_config_tab(config_frame)
        
        # Pestaña de Estadísticas
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="📊 Estadísticas")
        self.create_stats_tab(stats_frame)
        
        # Pestaña de Conversaciones
        conv_frame = ttk.Frame(notebook)
        notebook.add(conv_frame, text="💬 Conversaciones")
        self.create_conversations_tab(conv_frame)
    
    def create_control_tab(self, parent):
        """Crea la pestaña de control del bot"""
        # Estado del bot
        status_frame = ttk.LabelFrame(parent, text="Estado del Bot")
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="🔴 Detenido", font=("Arial", 12, "bold"))
        self.status_label.pack(pady=10)
        
        # Botones de control
        button_frame = ttk.Frame(status_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="🚀 Iniciar Bot", 
                  command=self.start_bot_thread).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🛑 Detener Bot", 
                  command=self.stop_bot).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Reiniciar", 
                  command=self.restart_bot).pack(side=tk.LEFT, padx=5)
        
        # Modo del bot
        mode_frame = ttk.LabelFrame(parent, text="Modo de Operación")
        mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.mode_var = tk.StringVar(value="automático")
        ttk.Radiobutton(mode_frame, text="🤖 Automático (responde solo)", 
                       variable=self.mode_var, value="automático",
                       command=self.change_mode).pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(mode_frame, text="👤 Manual (solo sugerencias)", 
                       variable=self.mode_var, value="manual",
                       command=self.change_mode).pack(anchor=tk.W, padx=10, pady=2)
        
        # Log de actividad
        log_frame = ttk.LabelFrame(parent, text="Log de Actividad")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_config_tab(self, parent):
        """Crea la pestaña de configuración"""
        # Horario de atención
        schedule_frame = ttk.LabelFrame(parent, text="Horario de Atención")
        schedule_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(schedule_frame, text="Hora inicio:").grid(row=0, column=0, padx=5, pady=5)
        self.start_hour = tk.IntVar(value=8)
        ttk.Spinbox(schedule_frame, from_=0, to=23, textvariable=self.start_hour, width=5).grid(row=0, column=1, padx=5)
        
        ttk.Label(schedule_frame, text="Hora fin:").grid(row=0, column=2, padx=5, pady=5)
        self.end_hour = tk.IntVar(value=20)
        ttk.Spinbox(schedule_frame, from_=0, to=23, textvariable=self.end_hour, width=5).grid(row=0, column=3, padx=5)
        
        ttk.Button(schedule_frame, text="Aplicar Horario", 
                  command=self.update_schedule).grid(row=0, column=4, padx=10)
        
        # Configuración de respuestas
        response_frame = ttk.LabelFrame(parent, text="Configuración de Respuestas")
        response_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(response_frame, text="Demora antes de responder (seg):").grid(row=0, column=0, padx=5, pady=5)
        self.response_delay = tk.IntVar(value=2)
        ttk.Spinbox(response_frame, from_=1, to=10, textvariable=self.response_delay, width=5).grid(row=0, column=1, padx=5)
        
        ttk.Label(response_frame, text="Máximo caracteres por respuesta:").grid(row=1, column=0, padx=5, pady=5)
        self.max_length = tk.IntVar(value=1000)
        ttk.Spinbox(response_frame, from_=100, to=2000, textvariable=self.max_length, width=8).grid(row=1, column=1, padx=5)
        
        ttk.Button(response_frame, text="Aplicar Configuración", 
                  command=self.update_response_config).grid(row=2, column=0, columnspan=2, pady=10)
    
    def create_stats_tab(self, parent):
        """Crea la pestaña de estadísticas"""
        stats_frame = ttk.LabelFrame(parent, text="Estadísticas del Bot")
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=20)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Button(stats_frame, text="🔄 Actualizar Estadísticas", 
                  command=self.update_stats).pack(pady=5)
    
    def create_conversations_tab(self, parent):
        """Crea la pestaña de conversaciones"""
        conv_frame = ttk.LabelFrame(parent, text="Historial de Conversaciones")
        conv_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.conversations_text = scrolledtext.ScrolledText(conv_frame, height=20)
        self.conversations_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        button_frame = ttk.Frame(conv_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="🔄 Actualizar", 
                  command=self.update_conversations).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Exportar", 
                  command=self.export_conversations).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Limpiar", 
                  command=self.clear_conversations).pack(side=tk.LEFT, padx=5)
    
    def start_bot_thread(self):
        """Inicia el bot en un hilo separado"""
        import threading
        threading.Thread(target=self.bot.start_bot, daemon=True).start()
        self.status_label.config(text="🟢 Ejecutándose", foreground="green")
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Bot iniciado\n")
        self.log_text.see(tk.END)
    
    def stop_bot(self):
        """Detiene el bot"""
        self.bot.stop_bot()
        self.status_label.config(text="🔴 Detenido", foreground="red")
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Bot detenido\n")
        self.log_text.see(tk.END)
    
    def restart_bot(self):
        """Reinicia el bot"""
        self.stop_bot()
        time.sleep(2)
        self.start_bot_thread()
    
    def change_mode(self):
        """Cambia el modo del bot"""
        mode = self.mode_var.get()
        self.bot.set_manual_mode(mode == "manual")
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Modo cambiado a: {mode}\n")
    
    def update_schedule(self):
        """Actualiza el horario de atención"""
        self.bot.set_business_hours(self.start_hour.get(), self.end_hour.get())
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Horario actualizado\n")
    
    def update_response_config(self):
        """Actualiza configuración de respuestas"""
        self.bot.config["response_delay"] = self.response_delay.get()
        self.bot.config["max_response_length"] = self.max_length.get()
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Configuración actualizada\n")
    
    def update_stats(self):
        """Actualiza las estadísticas mostradas"""
        stats = self.bot.get_bot_statistics()
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, json.dumps(stats, indent=2, ensure_ascii=False))
    
    def update_conversations(self):
        """Actualiza el historial de conversaciones"""
        conversations = self.bot.export_conversations()
        self.conversations_text.delete(1.0, tk.END)
        self.conversations_text.insert(tk.END, json.dumps(conversations, indent=2, ensure_ascii=False))
    
    def export_conversations(self):
        """Exporta las conversaciones a archivo"""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            conversations = self.bot.export_conversations()
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(conversations, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Éxito", f"Conversaciones exportadas a: {filename}")
    
    def clear_conversations(self):
        """Limpia el historial de conversaciones"""
        if messagebox.askyesno("Confirmar", "¿Limpiar todo el historial de conversaciones?"):
            self.bot.client_conversations.clear()
            self.bot.processed_messages.clear()
            self.conversations_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Historial limpiado\n")

# Función principal para iniciar el bot
def main():
    """Función principal para probar el bot"""
    from core.database import DatabaseManager
    
    print("🤖 Iniciando Bot de WhatsApp con IA...")
    
    # Inicializar componentes
    db = DatabaseManager()
    bot = WhatsAppAIBot(db, headless=False)
    
    # Crear interfaz de administración
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal
    
    admin_ui = WhatsAppBotUI(bot)
    admin_ui.create_admin_window()
    
    print("✅ Interfaz de administración abierta")
    root.mainloop()

if __name__ == "__main__":
    main()
