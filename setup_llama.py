"""
Configuración y prueba de Llama local para el asistente POS
Usa llama.cpp para ejecutar modelos localmente
"""

import os
import sys
import requests
import json
from pathlib import Path
import subprocess

def download_llama_model():
    """Descarga un modelo Llama pequeño y optimizado"""
    
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Modelo recomendado: Llama-2-7B-Chat quantizado (más pequeño y rápido)
    model_url = "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf"
    model_path = models_dir / "llama-2-7b-chat.Q4_K_M.gguf"
    
    if model_path.exists():
        print(f"✅ Modelo ya existe: {model_path}")
        return str(model_path)
    
    print(f"📥 Descargando modelo Llama (esto puede tomar varios minutos)...")
    print(f"URL: {model_url}")
    print(f"Destino: {model_path}")
    
    try:
        response = requests.get(model_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(model_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\r📊 Progreso: {progress:.1f}% ({downloaded // 1024 // 1024} MB)", end='')
        
        print(f"\n✅ Modelo descargado: {model_path}")
        return str(model_path)
        
    except Exception as e:
        print(f"❌ Error descargando modelo: {e}")
        return None

def setup_llama_cpp():
    """Configura llama.cpp para ejecutar modelos localmente"""
    
    print("🔧 Configurando llama.cpp...")
    
    # Verificar si ya está instalado
    try:
        import llama_cpp
        print("✅ llama-cpp-python ya está instalado")
        return True
    except ImportError:
        pass
    
    # Instalar llama-cpp-python
    try:
        print("📦 Instalando llama-cpp-python...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "llama-cpp-python", 
            "--upgrade", 
            "--force-reinstall", 
            "--no-cache-dir"
        ])
        print("✅ llama-cpp-python instalado correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando llama-cpp-python: {e}")
        return False

def test_llama_local():
    """Prueba el modelo Llama local"""
    
    try:
        from llama_cpp import Llama
    except ImportError:
        print("❌ llama-cpp-python no disponible")
        return False
    
    model_path = Path("models/llama-2-7b-chat.Q4_K_M.gguf")
    
    if not model_path.exists():
        print(f"❌ Modelo no encontrado: {model_path}")
        return False
    
    print("🚀 Iniciando Llama local...")
    
    try:
        # Cargar modelo (puede tomar unos minutos la primera vez)
        llm = Llama(
            model_path=str(model_path),
            n_ctx=2048,  # Contexto máximo
            n_threads=4,  # Ajustar según tu CPU
            verbose=False
        )
        
        print("✅ Modelo cargado correctamente")
        
        # Probar con una pregunta sobre POS
        test_prompt = """[INST] <<SYS>>
Eres un asistente experto en sistemas POS (Punto de Venta). 
Respondes de forma clara y concisa sobre funciones básicas de caja.
<</SYS>>

¿Cómo hacer una venta en un sistema POS? [/INST]"""
        
        print("💭 Generando respuesta...")
        response = llm(
            test_prompt,
            max_tokens=200,
            temperature=0.7,
            stop=["[INST]", "</s>"]
        )
        
        answer = response["choices"][0]["text"].strip()
        print(f"\n🤖 Respuesta de Llama:\n{answer}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Error ejecutando Llama: {e}")
        return False

def create_llama_server():
    """Crea un servidor simple para Llama"""
    
    server_code = '''
import json
from flask import Flask, request, jsonify
from llama_cpp import Llama
import os

app = Flask(__name__)

# Cargar modelo al iniciar
model_path = "models/llama-2-7b-chat.Q4_K_M.gguf"
llm = None

def load_model():
    global llm
    if os.path.exists(model_path):
        print(f"Cargando modelo: {model_path}")
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            verbose=False
        )
        print("Modelo cargado correctamente")
    else:
        print(f"Error: Modelo no encontrado en {model_path}")

@app.route("/completion", methods=["POST"])
def completion():
    global llm
    
    if llm is None:
        return jsonify({"error": "Modelo no cargado"}), 500
    
    data = request.json
    prompt = data.get("prompt", "")
    max_tokens = data.get("max_tokens", 150)
    temperature = data.get("temperature", 0.7)
    
    # Formato para Llama-2-Chat
    formatted_prompt = f"""[INST] <<SYS>>
Eres un asistente experto en sistemas POS. Respondes claro y conciso.
<</SYS>>

{prompt} [/INST]"""
    
    try:
        response = llm(
            formatted_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["[INST]", "</s>"]
        )
        
        return jsonify({
            "content": response["choices"][0]["text"].strip(),
            "model": "llama-2-7b-chat"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model_loaded": llm is not None})

if __name__ == "__main__":
    load_model()
    print("🚀 Servidor Llama iniciado en http://localhost:5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
'''
    
    with open("llama_server.py", "w", encoding="utf-8") as f:
        f.write(server_code)
    
    print("✅ Servidor Llama creado: llama_server.py")
    print("Para iniciar: python llama_server.py")

def main():
    """Función principal de configuración"""
    
    print("🤖 CONFIGURACIÓN DE LLAMA LOCAL PARA POS")
    print("=" * 50)
    
    # Paso 1: Configurar llama.cpp
    if not setup_llama_cpp():
        print("❌ No se pudo configurar llama.cpp")
        return
    
    # Paso 2: Descargar modelo (opcional, es grande)
    print("\\n📥 ¿Descargar modelo Llama? (será ~4GB)")
    download_choice = input("Escribir 'si' para descargar: ").lower().strip()
    
    if download_choice == 'si':
        model_path = download_llama_model()
        if not model_path:
            print("❌ No se pudo descargar el modelo")
            return
        
        # Paso 3: Probar modelo
        print("\\n🧪 Probando modelo local...")
        if test_llama_local():
            print("✅ Llama local funcionando correctamente!")
        else:
            print("❌ Error probando Llama local")
            return
    
    # Paso 4: Crear servidor
    create_llama_server()
    
    print("\\n🎉 CONFIGURACIÓN COMPLETA!")
    print("\\nPara usar Llama local:")
    print("1. Ejecutar: python llama_server.py")
    print("2. En el asistente IA, configurar URL: http://localhost:5001/completion")
    print("3. Activar 'Usar Llama API' en configuración")
    
    print("\\n💡 Nota: El modelo es grande y requiere al menos 8GB RAM")
    print("Si tienes problemas, usa solo ChatterBot y Transformers")

if __name__ == "__main__":
    main()
