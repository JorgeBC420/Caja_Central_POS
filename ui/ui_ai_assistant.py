"""
Interfaz gráfica para el Asistente de IA del Sistema POS
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Dict, Any, List
import threading
import json
from datetime import datetime

from core.ai_assistant import POSAIAssistant

class AIAssistantUI:
    """Interfaz gráfica para el asistente de IA"""
    
    def __init__(self, parent=None, db_manager=None):
        self.parent = parent
        self.ai_assistant = POSAIAssistant(db_manager)
        self.window = None
        self.chat_history = []
        
        # Configuración de la interfaz
        self.colors = {
            "bg": "#f0f0f0",
            "chat_bg": "#ffffff",
            "user_msg": "#e3f2fd",
            "ai_msg": "#f3e5f5",
            "button": "#2196f3",
            "button_hover": "#1976d2"
        }
        
    def create_window(self):
        """Crea la ventana del asistente"""
        if self.parent:
            self.window = tk.Toplevel(self.parent)
        else:
            self.window = tk.Tk()
            
        self.window.title("🤖 Asistente IA - Sistema POS")
        self.window.geometry("800x600")
        self.window.configure(bg=self.colors["bg"])
        
        # Centrar ventana
        self._center_window()
        
        # Crear interfaz
        self._create_ui()
        
        # Configurar eventos
        self._setup_events()
        
        # Mostrar mensaje de bienvenida
        self._show_welcome_message()
        
    def _center_window(self):
        """Centra la ventana en la pantalla"""
        self.window.update_idletasks()
        width = 800
        height = 600
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
    def _create_ui(self):
        """Crea la interfaz de usuario"""
        
        # Frame principal
        main_frame = tk.Frame(self.window, bg=self.colors["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        self._create_header(main_frame)
        
        # Chat area
        self._create_chat_area(main_frame)
        
        # Input area
        self._create_input_area(main_frame)
        
        # Sidebar con funciones rápidas
        self._create_sidebar(main_frame)
        
    def _create_header(self, parent):
        """Crea el header de la aplicación"""
        header_frame = tk.Frame(parent, bg="#2196f3", height=60)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Título
        title_label = tk.Label(
            header_frame,
            text="🤖 Asistente IA del Sistema POS",
            font=("Arial", 16, "bold"),
            bg="#2196f3",
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=15, pady=15)
        
        # Botón de ayuda
        help_btn = tk.Button(
            header_frame,
            text="❓ Ayuda",
            command=self._show_help,
            bg="white",
            fg="#2196f3",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=15
        )
        help_btn.pack(side=tk.RIGHT, padx=15, pady=15)
        
        # Botón de limpiar chat
        clear_btn = tk.Button(
            header_frame,
            text="🗑️ Limpiar",
            command=self._clear_chat,
            bg="white",
            fg="#2196f3",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=15
        )
        clear_btn.pack(side=tk.RIGHT, padx=5, pady=15)
        
    def _create_chat_area(self, parent):
        """Crea el área de chat"""
        # Frame para chat y sidebar
        content_frame = tk.Frame(parent, bg=self.colors["bg"])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Chat frame
        chat_frame = tk.Frame(content_frame, bg=self.colors["bg"])
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Área de chat con scroll
        self.chat_text = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            bg=self.colors["chat_bg"],
            fg="#333333",
            font=("Arial", 11),
            padx=15,
            pady=15,
            state=tk.DISABLED,
            height=20
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True)
        
        # Configurar tags para diferentes tipos de mensajes
        self.chat_text.tag_configure("user", background=self.colors["user_msg"], lmargin1=10, lmargin2=10, rmargin=10)
        self.chat_text.tag_configure("ai", background=self.colors["ai_msg"], lmargin1=10, lmargin2=10, rmargin=10)
        self.chat_text.tag_configure("system", background="#ffecb3", lmargin1=10, lmargin2=10, rmargin=10)
        self.chat_text.tag_configure("timestamp", font=("Arial", 9), foreground="#666666")
        
    def _create_input_area(self, parent):
        """Crea el área de entrada de texto"""
        input_frame = tk.Frame(parent, bg=self.colors["bg"])
        input_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Frame para entrada y botón
        entry_frame = tk.Frame(input_frame, bg=self.colors["bg"])
        entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Entrada de texto
        self.input_entry = tk.Entry(
            entry_frame,
            font=("Arial", 12),
            bg="white",
            fg="#333333",
            relief=tk.SOLID,
            borderwidth=1
        )
        self.input_entry.pack(fill=tk.X, ipady=8)
        
        # Botón enviar
        self.send_button = tk.Button(
            input_frame,
            text="📤 Enviar",
            command=self._send_message,
            bg=self.colors["button"],
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Indicador de escritura
        self.typing_label = tk.Label(
            input_frame,
            text="",
            font=("Arial", 9),
            bg=self.colors["bg"],
            fg="#666666"
        )
        self.typing_label.pack(side=tk.LEFT, padx=(0, 10))
        
    def _create_sidebar(self, parent):
        """Crea la barra lateral con funciones rápidas"""
        sidebar_frame = tk.Frame(parent, bg="#f5f5f5", width=200)
        sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        sidebar_frame.pack_propagate(False)
        
        # Título sidebar
        sidebar_title = tk.Label(
            sidebar_frame,
            text="🚀 Acciones Rápidas",
            font=("Arial", 12, "bold"),
            bg="#f5f5f5",
            fg="#333333"
        )
        sidebar_title.pack(pady=15)
        
        # Botones de acción rápida
        quick_actions = [
            ("💰 ¿Cómo cobro?", "¿cómo cobro una venta?"),
            ("🔍 Buscar productos", "¿cómo busco un producto?"),
            ("📦 Gestionar inventario", "¿cómo gestiono el inventario?"),
            ("🎯 Atajos de teclado", "¿qué atajos de teclado hay?"),
            ("📊 Ver reportes", "¿cómo veo las ventas del día?"),
            ("🔄 Hacer devolución", "¿cómo hago una devolución?"),
            ("🖨️ Imprimir ticket", "¿cómo imprimo un duplicado?"),
            ("💡 Tips útiles", "dame algunos tips útiles")
        ]
        
        for text, query in quick_actions:
            btn = tk.Button(
                sidebar_frame,
                text=text,
                command=lambda q=query: self._quick_question(q),
                bg="white",
                fg="#333333",
                font=("Arial", 9),
                relief=tk.SOLID,
                borderwidth=1,
                padx=10,
                pady=5,
                anchor="w"
            )
            btn.pack(fill=tk.X, padx=10, pady=2)
            
        # Estado del sistema
        status_frame = tk.Frame(sidebar_frame, bg="#f5f5f5")
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        status_label = tk.Label(
            status_frame,
            text="🟢 IA Activa",
            font=("Arial", 10, "bold"),
            bg="#f5f5f5",
            fg="#4caf50"
        )
        status_label.pack()
        
    def _setup_events(self):
        """Configura los eventos de la interfaz"""
        self.input_entry.bind("<Return>", lambda e: self._send_message())
        self.input_entry.bind("<KeyPress>", self._on_typing)
        
        # Hover effects para botones
        self.send_button.bind("<Enter>", lambda e: self.send_button.configure(bg=self.colors["button_hover"]))
        self.send_button.bind("<Leave>", lambda e: self.send_button.configure(bg=self.colors["button"]))
        
    def _show_welcome_message(self):
        """Muestra el mensaje de bienvenida"""
        welcome_response = self.ai_assistant.ask("hola")
        self._add_message("system", "¡Bienvenido al Asistente IA del Sistema POS!")
        self._add_message("ai", welcome_response["answer"])
        
        if "examples" in welcome_response:
            examples_text = "\n\nPuedes preguntarme cosas como:\n" + "\n".join(f"• {ex}" for ex in welcome_response["examples"])
            self._add_message("ai", examples_text)
            
    def _send_message(self):
        """Envía un mensaje al asistente"""
        message = self.input_entry.get().strip()
        if not message:
            return
            
        # Limpiar entrada
        self.input_entry.delete(0, tk.END)
        
        # Mostrar mensaje del usuario
        self._add_message("user", message)
        
        # Mostrar indicador de "escribiendo"
        self._show_typing_indicator()
        
        # Procesar respuesta en hilo separado
        threading.Thread(target=self._process_response, args=(message,), daemon=True).start()
        
    def _process_response(self, message: str):
        """Procesa la respuesta del asistente en un hilo separado"""
        try:
            response = self.ai_assistant.ask(message)
            
            # Programar actualización de UI en el hilo principal
            self.window.after(0, lambda: self._show_ai_response(response))
            
        except Exception as e:
            error_msg = f"Lo siento, ocurrió un error: {str(e)}"
            self.window.after(0, lambda: self._show_ai_response({
                "type": "error",
                "answer": error_msg,
                "confidence": 0.1
            }))
            
    def _show_ai_response(self, response: Dict[str, Any]):
        """Muestra la respuesta del asistente"""
        # Ocultar indicador de escritura
        self._hide_typing_indicator()
        
        # Mostrar respuesta principal
        self._add_message("ai", response["answer"])
        
        # Mostrar información adicional según el tipo
        if response["type"] == "how_to" and "steps" in response:
            steps_text = "\n\n📋 Pasos a seguir:\n" + "\n".join(f"{i+1}. {step}" for i, step in enumerate(response["steps"]))
            self._add_message("ai", steps_text)
            
            if "shortcuts" in response:
                shortcuts_text = "\n⌨️ Atajos útiles:\n" + "\n".join(f"• {sc}" for sc in response["shortcuts"])
                self._add_message("ai", shortcuts_text)
                
        elif response["type"] == "shortcuts":
            shortcuts_text = "\n\n⌨️ Atajos disponibles:\n"
            for key, desc in response["shortcuts"].items():
                shortcuts_text += f"• {key}: {desc}\n"
            self._add_message("ai", shortcuts_text)
            
        elif "suggestions" in response:
            suggestions_text = "\n\n💡 ¿Te refieres a alguna de estas?:\n" + "\n".join(f"• {sug}" for sug in response["suggestions"][:3])
            self._add_message("ai", suggestions_text)
            
        # Mostrar nivel de confianza si es bajo
        if response.get("confidence", 1.0) < 0.7:
            confidence_text = f"\n\n🤔 Confianza: {response['confidence']*100:.0f}% - ¿Podrías ser más específico?"
            self._add_message("system", confidence_text)
            
    def _add_message(self, sender: str, message: str):
        """Agrega un mensaje al chat"""
        self.chat_text.configure(state=tk.NORMAL)
        
        # Timestamp
        timestamp = datetime.now().strftime("%H:%M")
        
        # Determinar icono y etiqueta
        if sender == "user":
            icon = "👤"
            label = "Tú"
            tag = "user"
        elif sender == "ai":
            icon = "🤖"
            label = "Asistente IA"
            tag = "ai"
        else:
            icon = "ℹ️"
            label = "Sistema"
            tag = "system"
            
        # Agregar mensaje
        self.chat_text.insert(tk.END, f"\n{icon} {label} ({timestamp})\n", "timestamp")
        self.chat_text.insert(tk.END, f"{message}\n\n", tag)
        
        # Scroll al final
        self.chat_text.see(tk.END)
        self.chat_text.configure(state=tk.DISABLED)
        
    def _quick_question(self, question: str):
        """Envía una pregunta rápida"""
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, question)
        self._send_message()
        
    def _show_typing_indicator(self):
        """Muestra el indicador de escritura"""
        self.typing_label.configure(text="🤖 Asistente escribiendo...")
        self.send_button.configure(state=tk.DISABLED)
        
    def _hide_typing_indicator(self):
        """Oculta el indicador de escritura"""
        self.typing_label.configure(text="")
        self.send_button.configure(state=tk.NORMAL)
        
    def _on_typing(self, event):
        """Maneja el evento de escritura"""
        # Aquí se podría implementar autocompletado o sugerencias
        pass
        
    def _clear_chat(self):
        """Limpia el historial de chat"""
        result = messagebox.askyesno(
            "Limpiar Chat",
            "¿Estás seguro de que quieres limpiar el historial de chat?"
        )
        
        if result:
            self.chat_text.configure(state=tk.NORMAL)
            self.chat_text.delete(1.0, tk.END)
            self.chat_text.configure(state=tk.DISABLED)
            self.ai_assistant.conversation_history.clear()
            self._show_welcome_message()
            
    def _show_help(self):
        """Muestra la ayuda del asistente"""
        help_text = """🤖 Asistente IA del Sistema POS

¿Cómo usarme?
• Escribe tu pregunta en lenguaje natural
• Usa los botones de acciones rápidas
• Pregunta sobre funciones específicas

Ejemplos de preguntas:
• "¿Cómo cobro una venta?"
• "No encuentro un producto"
• "¿Qué atajos de teclado hay?"
• "Error al imprimir ticket"

¡Estoy aquí para ayudarte! 😊"""
        
        messagebox.showinfo("Ayuda - Asistente IA", help_text)
        
    def show(self):
        """Muestra la ventana del asistente"""
        if not self.window:
            self.create_window()
        else:
            self.window.deiconify()
            self.window.lift()
            
        self.input_entry.focus_set()
        
    def hide(self):
        """Oculta la ventana del asistente"""
        if self.window:
            self.window.withdraw()
