"""
Interfaz Avanzada para el Asistente de IA del Sistema POS
Incluye múltiples engines, analytics y configuración
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
from datetime import datetime
from typing import Dict, Any, List
from core.ai_assistant import POSAIAssistant

class AdvancedAIAssistantUI:
    """Interfaz avanzada para el asistente de IA"""
    
    def __init__(self, parent, db_manager=None):
        self.parent = parent
        self.assistant = POSAIAssistant(db_manager)
        self.window = None
        
    def show_assistant(self):
        """Muestra la ventana del asistente"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
            
        self.window = tk.Toplevel(self.parent)
        self.window.title("🤖 Asistente IA Avanzado - Sistema POS")
        self.window.geometry("900x700")
        self.window.resizable(True, True)
        
        # Configurar estilo
        self._setup_styles()
        
        # Crear interfaz
        self._create_interface()
        
        # Mostrar estado inicial
        self._update_engine_status()
        
    def _setup_styles(self):
        """Configura estilos personalizados"""
        style = ttk.Style()
        
        # Estilo para pestañas
        style.configure("AI.TNotebook", background="#f0f0f0")
        style.configure("AI.TNotebook.Tab", padding=[20, 10])
        
        # Estilo para botones
        style.configure("AI.TButton", font=("Segoe UI", 10))
        style.configure("Success.TButton", foreground="green")
        style.configure("Warning.TButton", foreground="orange")
        style.configure("Error.TButton", foreground="red")
        
    def _create_interface(self):
        """Crea la interfaz principal"""
        
        # Notebook principal
        self.notebook = ttk.Notebook(self.window, style="AI.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Pestañas
        self._create_chat_tab()
        self._create_analytics_tab()
        self._create_config_tab()
        self._create_training_tab()
        
        # Barra de estado
        self._create_status_bar()
        
    def _create_chat_tab(self):
        """Crea la pestaña de chat"""
        chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(chat_frame, text="💬 Chat Inteligente")
        
        # Frame superior: Selector de engine
        engine_frame = ttk.LabelFrame(chat_frame, text="🔧 Engine de IA", padding=10)
        engine_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(engine_frame, text="Usar engine:").pack(side="left")
        
        self.engine_var = tk.StringVar(value="auto")
        self.engine_combo = ttk.Combobox(
            engine_frame, 
            textvariable=self.engine_var,
            values=["auto", "chatterbot", "transformers", "llama_api", "rules"],
            state="readonly",
            width=15
        )
        self.engine_combo.pack(side="left", padx=(5, 10))
        
        # Botón de estado de engines
        self.status_btn = ttk.Button(
            engine_frame, 
            text="Estado Engines", 
            command=self._show_engine_status,
            style="AI.TButton"
        )
        self.status_btn.pack(side="left", padx=5)
        
        # Área de conversación
        conv_frame = ttk.LabelFrame(chat_frame, text="🗨️ Conversación", padding=5)
        conv_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            conv_frame, 
            wrap=tk.WORD, 
            height=20,
            font=("Consolas", 10),
            bg="#f8f8f8"
        )
        self.chat_display.pack(fill="both", expand=True, pady=5)
        
        # Frame de entrada
        input_frame = ttk.Frame(conv_frame)
        input_frame.pack(fill="x", pady=5)
        
        ttk.Label(input_frame, text="Pregunta:").pack(side="left")
        
        self.question_entry = ttk.Entry(input_frame, font=("Segoe UI", 11))
        self.question_entry.pack(side="left", fill="x", expand=True, padx=(5, 10))
        self.question_entry.bind("<Return>", lambda e: self._ask_question())
        
        ttk.Button(
            input_frame, 
            text="🤖 Preguntar", 
            command=self._ask_question,
            style="Success.TButton"
        ).pack(side="right")
        
        # Botones de ejemplos
        examples_frame = ttk.Frame(conv_frame)
        examples_frame.pack(fill="x", pady=5)
        
        ttk.Label(examples_frame, text="Ejemplos rápidos:").pack(side="left")
        
        examples = [
            "¿Cómo hacer una venta?",
            "¿Qué atajos hay?",
            "Error de impresión",
            "¿Cómo cerrar caja?"
        ]
        
        for example in examples:
            btn = ttk.Button(
                examples_frame,
                text=example,
                command=lambda q=example: self._ask_example(q),
                style="AI.TButton"
            )
            btn.pack(side="left", padx=2)
        
    def _create_analytics_tab(self):
        """Crea la pestaña de analytics"""
        analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(analytics_frame, text="📊 Analytics")
        
        # Estadísticas generales
        stats_frame = ttk.LabelFrame(analytics_frame, text="📈 Estadísticas de Uso", padding=10)
        stats_frame.pack(fill="x", padx=5, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=8, font=("Consolas", 10))
        self.stats_text.pack(fill="x", pady=5)
        
        # Botones de analytics
        analytics_btn_frame = ttk.Frame(stats_frame)
        analytics_btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(
            analytics_btn_frame,
            text="🔄 Actualizar Analytics",
            command=self._update_analytics,
            style="AI.TButton"
        ).pack(side="left", padx=5)
        
        ttk.Button(
            analytics_btn_frame,
            text="💡 Sugerencias",
            command=self._show_suggestions,
            style="Warning.TButton"
        ).pack(side="left", padx=5)
        
        ttk.Button(
            analytics_btn_frame,
            text="📁 Exportar Historial",
            command=self._export_history,
            style="AI.TButton"
        ).pack(side="left", padx=5)
        
        # Gráfico de engines (texto)
        engine_frame = ttk.LabelFrame(analytics_frame, text="🔧 Uso por Engine", padding=10)
        engine_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.engine_usage_text = scrolledtext.ScrolledText(
            engine_frame, 
            height=15, 
            font=("Consolas", 9)
        )
        self.engine_usage_text.pack(fill="both", expand=True)
        
    def _create_config_tab(self):
        """Crea la pestaña de configuración"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="⚙️ Configuración")
        
        # Configuración de engines
        engines_frame = ttk.LabelFrame(config_frame, text="🤖 Configuración de Engines", padding=10)
        engines_frame.pack(fill="x", padx=5, pady=5)
        
        # ChatterBot
        self.chatterbot_var = tk.BooleanVar(value=self.assistant.config["use_chatterbot"])
        ttk.Checkbutton(
            engines_frame,
            text="Usar ChatterBot (Local, entrenado)",
            variable=self.chatterbot_var,
            command=self._update_config
        ).pack(anchor="w")
        
        # Transformers
        self.transformers_var = tk.BooleanVar(value=self.assistant.config["use_transformers"])
        ttk.Checkbutton(
            engines_frame,
            text="Usar Transformers (Local, QA)",
            variable=self.transformers_var,
            command=self._update_config
        ).pack(anchor="w")
        
        # Llama API
        self.llama_var = tk.BooleanVar(value=self.assistant.config["use_llama_api"])
        ttk.Checkbutton(
            engines_frame,
            text="Usar Llama API (Cloud/Local)",
            variable=self.llama_var,
            command=self._update_config
        ).pack(anchor="w")
        
        # URL de Llama API
        api_frame = ttk.Frame(engines_frame)
        api_frame.pack(fill="x", pady=5)
        
        ttk.Label(api_frame, text="Llama API URL:").pack(side="left")
        self.api_url_entry = ttk.Entry(api_frame)
        self.api_url_entry.pack(side="left", fill="x", expand=True, padx=(5, 10))
        self.api_url_entry.insert(0, self.assistant.config["llama_api_url"])
        
        ttk.Button(
            api_frame,
            text="🧪 Probar",
            command=self._test_llama_connection,
            style="AI.TButton"
        ).pack(side="right")
        
        # Instalación de dependencias
        deps_frame = ttk.LabelFrame(config_frame, text="📦 Dependencias", padding=10)
        deps_frame.pack(fill="x", padx=5, pady=5)
        
        deps_text = tk.Text(deps_frame, height=6, font=("Consolas", 9))
        deps_text.pack(fill="x")
        
        deps_text.insert("1.0", """Para usar todos los engines, instala:

pip install chatterbot chatterbot-corpus
pip install transformers torch
pip install requests  # Para Llama API

Nota: ChatterBot requiere Python 3.8 o menor""")
        deps_text.config(state="disabled")
        
    def _create_training_tab(self):
        """Crea la pestaña de entrenamiento"""
        training_frame = ttk.Frame(self.notebook)
        self.notebook.add(training_frame, text="🎓 Entrenamiento")
        
        # Entrenamiento manual
        manual_frame = ttk.LabelFrame(training_frame, text="✏️ Entrenamiento Manual", padding=10)
        manual_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(manual_frame, text="Pregunta:").pack(anchor="w")
        self.train_question_entry = ttk.Entry(manual_frame, font=("Segoe UI", 10))
        self.train_question_entry.pack(fill="x", pady=2)
        
        ttk.Label(manual_frame, text="Respuesta correcta:").pack(anchor="w", pady=(10, 0))
        self.train_answer_text = tk.Text(manual_frame, height=4, font=("Segoe UI", 10))
        self.train_answer_text.pack(fill="x", pady=2)
        
        ttk.Button(
            manual_frame,
            text="🎯 Entrenar",
            command=self._train_manual,
            style="Success.TButton"
        ).pack(pady=10)
        
        # Historial de entrenamiento
        history_frame = ttk.LabelFrame(training_frame, text="📚 Historial de Entrenamiento", padding=10)
        history_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.training_history = scrolledtext.ScrolledText(
            history_frame,
            font=("Consolas", 9),
            height=15
        )
        self.training_history.pack(fill="both", expand=True)
        
    def _create_status_bar(self):
        """Crea la barra de estado"""
        self.status_bar = ttk.Frame(self.window)
        self.status_bar.pack(fill="x", side="bottom")
        
        self.status_label = ttk.Label(
            self.status_bar, 
            text="🤖 Asistente IA listo",
            font=("Segoe UI", 9)
        )
        self.status_label.pack(side="left", padx=5)
        
        # Indicador de engines activos
        self.engines_label = ttk.Label(
            self.status_bar,
            text="",
            font=("Segoe UI", 9),
            foreground="blue"
        )
        self.engines_label.pack(side="right", padx=5)
        
    def _ask_question(self):
        """Procesa una pregunta del usuario"""
        question = self.question_entry.get().strip()
        if not question:
            return
        
        # Limpiar entrada
        self.question_entry.delete(0, tk.END)
        
        # Mostrar pregunta en chat
        self._add_to_chat(f"👤 Usuario: {question}", "user")
        
        # Actualizar estado
        self.status_label.config(text="🤔 Procesando...")
        self.window.update()
        
        try:
            # Obtener respuesta
            engine = self.engine_var.get()
            response = self.assistant.ask(question, use_engine=engine)
            
            # Mostrar respuesta
            engine_used = response.get("engine", "unknown")
            confidence = response.get("confidence", 0.0)
            
            answer_text = f"🤖 Asistente ({engine_used}, confianza: {confidence:.2f}):\n{response.get('answer', 'Sin respuesta')}"
            
            # Agregar información adicional si existe
            if "steps" in response:
                answer_text += f"\n\n📋 Pasos:\n" + "\n".join([f"  {i+1}. {step}" for i, step in enumerate(response["steps"])])
            
            if "shortcuts" in response:
                answer_text += f"\n\n⌨️ Atajos: {', '.join(response['shortcuts'])}"
            
            if "suggestions" in response:
                answer_text += f"\n\n💡 Relacionado: {', '.join(response['suggestions'][:3])}"
            
            self._add_to_chat(answer_text, "assistant")
            
            # Actualizar estado
            self.status_label.config(text=f"✅ Respondido con {engine_used}")
            
        except Exception as e:
            self._add_to_chat(f"❌ Error: {str(e)}", "error")
            self.status_label.config(text="❌ Error al procesar")
        
        # Auto-scroll
        self.chat_display.see("end")
        
    def _ask_example(self, question: str):
        """Ejecuta una pregunta de ejemplo"""
        self.question_entry.delete(0, tk.END)
        self.question_entry.insert(0, question)
        self._ask_question()
        
    def _add_to_chat(self, text: str, msg_type: str):
        """Agrega mensaje al chat"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Configurar colores
        if msg_type == "user":
            color = "#0066cc"
        elif msg_type == "assistant":
            color = "#009900"
        elif msg_type == "error":
            color = "#cc0000"
        else:
            color = "#333333"
        
        # Agregar al display
        self.chat_display.config(state="normal")
        self.chat_display.insert("end", f"[{timestamp}] {text}\n\n")
        
        # Aplicar color (simplificado)
        self.chat_display.config(state="disabled")
        
    def _update_engine_status(self):
        """Actualiza el estado de los engines"""
        status = self.assistant.get_engine_status()
        engines_text = f"Activos: {', '.join(status['active_engines']) if status['active_engines'] else 'Solo reglas'}"
        self.engines_label.config(text=engines_text)
        
    def _show_engine_status(self):
        """Muestra ventana detallada del estado de engines"""
        status = self.assistant.get_engine_status()
        
        status_window = tk.Toplevel(self.window)
        status_window.title("🔧 Estado de Engines IA")
        status_window.geometry("500x400")
        
        text_widget = scrolledtext.ScrolledText(status_window, font=("Consolas", 10))
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        status_text = f"""🤖 ESTADO DE ENGINES DE IA
{'='*40}

Engines Activos: {len(status['active_engines'])}
{', '.join(status['active_engines']) if status['active_engines'] else 'Ninguno (solo reglas)'}

📊 Detalles:
• ChatterBot: {'✅ Activo' if status['chatterbot_available'] else '❌ No disponible'}
• Transformers: {'✅ Activo' if status['transformers_available'] else '❌ No disponible'}
• Llama API: {'✅ Activo' if status['llama_api_available'] else '❌ No disponible'}

💬 Estadísticas:
• Total conversaciones: {status['total_conversations']}
• Último engine usado: {status['last_engine_used'] or 'N/A'}

🔧 Para activar engines faltantes:
pip install chatterbot chatterbot-corpus
pip install transformers torch
"""
        
        text_widget.insert("1.0", status_text)
        text_widget.config(state="disabled")
        
    def _update_analytics(self):
        """Actualiza los analytics"""
        analytics = self.assistant.get_conversation_analytics()
        
        # Actualizar estadísticas
        stats_text = f"""📊 ANALYTICS DEL ASISTENTE IA
{'='*35}

Total Preguntas: {analytics['total_questions']}
Total Respuestas: {analytics['total_responses']}
Preguntas última hora: {analytics['last_hour_questions']}

Engine más usado: {analytics.get('most_used_engine', 'N/A')}

Palabras clave más comunes:
"""
        
        for word, count in analytics.get('common_keywords', [])[:5]:
            stats_text += f"  • {word}: {count} veces\n"
        
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("1.0", stats_text)
        
        # Actualizar uso por engine
        engine_usage = analytics.get('engine_usage', {})
        usage_text = "📈 USO POR ENGINE:\n" + "="*25 + "\n\n"
        
        for engine, count in engine_usage.items():
            percentage = (count / sum(engine_usage.values())) * 100 if engine_usage else 0
            bar = "█" * int(percentage / 5)  # Barra visual simple
            usage_text += f"{engine:12}: {count:3} ({percentage:5.1f}%) {bar}\n"
        
        self.engine_usage_text.delete("1.0", "end")
        self.engine_usage_text.insert("1.0", usage_text)
        
    def _show_suggestions(self):
        """Muestra sugerencias de mejora"""
        suggestions = self.assistant.suggest_improvements()
        
        if not suggestions:
            messagebox.showinfo("💡 Sugerencias", "¡Todo perfecto! No hay sugerencias por ahora.")
            return
        
        suggestions_text = "💡 SUGERENCIAS DE MEJORA:\n\n" + "\n\n".join(suggestions)
        messagebox.showinfo("💡 Sugerencias", suggestions_text)
        
    def _export_history(self):
        """Exporta el historial de conversaciones"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                format_type = "json" if filename.endswith(".json") else "txt"
                history = self.assistant.export_conversation_history(format_type)
                
                with open(filename, "w", encoding="utf-8") as f:
                    if format_type == "json":
                        json.dump(history, f, indent=2, ensure_ascii=False)
                    else:
                        f.write(history)
                
                messagebox.showinfo("✅ Exportación", f"Historial exportado a:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("❌ Error", f"Error al exportar: {str(e)}")
                
    def _update_config(self):
        """Actualiza la configuración"""
        self.assistant.config["use_chatterbot"] = self.chatterbot_var.get()
        self.assistant.config["use_transformers"] = self.transformers_var.get()
        self.assistant.config["use_llama_api"] = self.llama_var.get()
        
        # Reinicializar engines si es necesario
        # (En implementación real, podrías reinicializar selectivamente)
        messagebox.showinfo("⚙️ Configuración", "Configuración actualizada. Reinicia el asistente para aplicar cambios.")
        
    def _test_llama_connection(self):
        """Prueba la conexión con Llama API"""
        url = self.api_url_entry.get().strip()
        if not url:
            messagebox.showwarning("⚠️ Advertencia", "Ingresa una URL válida")
            return
        
        self.assistant.config["llama_api_url"] = url
        
        # Probar conexión
        try:
            import requests
            response = requests.post(
                url,
                json={"prompt": "Test", "max_tokens": 1},
                timeout=5
            )
            
            if response.status_code == 200:
                messagebox.showinfo("✅ Conexión", "¡Llama API conectado correctamente!")
                self.assistant.config["use_llama_api"] = True
                self._update_engine_status()
            else:
                messagebox.showerror("❌ Error", f"Error HTTP: {response.status_code}")
                
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo conectar:\n{str(e)}")
            
    def _train_manual(self):
        """Entrena manualmente con nueva pregunta/respuesta"""
        question = self.train_question_entry.get().strip()
        answer = self.train_answer_text.get("1.0", "end").strip()
        
        if not question or not answer:
            messagebox.showwarning("⚠️ Advertencia", "Completa tanto la pregunta como la respuesta")
            return
        
        try:
            self.assistant.train_with_conversation(question, answer)
            
            # Agregar al historial
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            training_entry = f"[{timestamp}] Entrenado:\nP: {question}\nR: {answer}\n{'-'*50}\n"
            
            self.training_history.insert("1.0", training_entry)
            
            # Limpiar campos
            self.train_question_entry.delete(0, tk.END)
            self.train_answer_text.delete("1.0", "end")
            
            messagebox.showinfo("✅ Entrenamiento", "¡Entrenamiento completado!")
            
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error al entrenar:\n{str(e)}")
