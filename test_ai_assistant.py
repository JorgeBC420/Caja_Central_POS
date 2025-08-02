"""
Script de prueba para el Asistente IA Avanzado
Prueba todos los engines y funcionalidades
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Agregar la ruta del proyecto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.ui_ai_assistant_advanced import AdvancedAIAssistantUI

def test_ai_assistant():
    """Prueba el asistente IA en una ventana independiente"""
    
    # Crear ventana principal
    root = tk.Tk()
    root.title("🧪 Test - Asistente IA Avanzado")
    root.geometry("600x400")
    
    # Frame principal
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill="both", expand=True)
    
    # Título
    title_label = ttk.Label(
        main_frame, 
        text="🤖 Test del Asistente IA Avanzado",
        font=("Segoe UI", 16, "bold")
    )
    title_label.pack(pady=10)
    
    # Información
    info_text = """Este asistente incluye múltiples engines de IA:

🔧 Engines Disponibles:
• ChatterBot: Entrenado específicamente para funciones POS
• Transformers: Para análisis avanzado de preguntas
• Llama API: Para respuestas contextuales detalladas
• Sistema de Reglas: Fallback con knowledge base

💡 Ejemplos de preguntas:
• "¿Cómo hacer una venta?"
• "¿Qué atajos de teclado hay?"
• "Error: producto no encontrado"
• "Explica paso a paso cómo cerrar la caja"

🎯 Funciones Avanzadas:
• Analytics de conversaciones
• Entrenamiento personalizado
• Exportación de historial
• Configuración de engines"""
    
    info_label = ttk.Label(main_frame, text=info_text, justify="left")
    info_label.pack(pady=10, fill="both", expand=True)
    
    # Botón para abrir asistente
    def abrir_asistente():
        try:
            assistant_ui = AdvancedAIAssistantUI(root)
            assistant_ui.show_assistant()
        except Exception as e:
            import traceback
            error_msg = f"Error al abrir asistente:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            print(error_msg)
            tk.messagebox.showerror("Error", error_msg)
    
    open_btn = ttk.Button(
        main_frame,
        text="🚀 Abrir Asistente IA Avanzado",
        command=abrir_asistente,
        style="Accent.TButton"
    )
    open_btn.pack(pady=20)
    
    # Información sobre dependencias
    deps_frame = ttk.LabelFrame(main_frame, text="📦 Estado de Dependencias", padding=10)
    deps_frame.pack(fill="x", pady=10)
    
    # Verificar dependencias
    deps_status = []
    
    try:
        import chatterbot
        deps_status.append("✅ ChatterBot: Disponible")
    except ImportError:
        deps_status.append("❌ ChatterBot: No instalado (pip install chatterbot)")
    
    try:
        import transformers
        deps_status.append("✅ Transformers: Disponible")
    except ImportError:
        deps_status.append("❌ Transformers: No instalado (pip install transformers torch)")
    
    try:
        import requests
        deps_status.append("✅ Requests: Disponible (para Llama API)")
    except ImportError:
        deps_status.append("❌ Requests: No instalado (pip install requests)")
    
    deps_text = "\n".join(deps_status)
    deps_label = ttk.Label(deps_frame, text=deps_text, justify="left")
    deps_label.pack()
    
    # Configurar estilo
    style = ttk.Style()
    try:
        style.theme_use("winnative")
    except:
        pass
    
    # Ejecutar
    root.mainloop()

if __name__ == "__main__":
    test_ai_assistant()
