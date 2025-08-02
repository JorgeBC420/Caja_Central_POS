"""
Launcher inteligente para el Bot de WhatsApp
Prueba diferentes versiones hasta encontrar una que funcione
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def test_selenium():
    """Prueba si Selenium funciona correctamente"""
    print("🧪 Probando Selenium...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://www.google.com")
        
        success = "Google" in driver.title
        driver.quit()
        
        if success:
            print("✅ Selenium funcionando correctamente")
            return True
        else:
            print("❌ Selenium con problemas")
            return False
            
    except Exception as e:
        print(f"❌ Selenium falló: {e}")
        return False

def test_ai_assistant():
    """Prueba si el AI Assistant funciona"""
    print("🧪 Probando AI Assistant...")
    
    try:
        from core.ai_assistant import POSAIAssistant
        from core.database import DatabaseManager
        
        db = DatabaseManager()
        ai = POSAIAssistant(db)
        
        response = ai.ask("test")
        
        if response and response.get('answer'):
            engines = ai.get_engine_status()['active_engines']
            print(f"✅ AI Assistant OK - Engines: {engines}")
            return True
        else:
            print("⚠️ AI Assistant limitado")
            return True  # Aún funciona, solo limitado
            
    except Exception as e:
        print(f"❌ AI Assistant falló: {e}")
        return False

def check_chrome():
    """Verifica Chrome instalado"""
    print("🧪 Verificando Chrome...")
    
    chrome_paths = [
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ Chrome encontrado: {path}")
            return True
    
    print("❌ Chrome no encontrado")
    return False

def launch_bot_version(script_name, description):
    """Lanza una versión específica del bot"""
    print(f"\n🚀 Iniciando {description}...")
    print("=" * 50)
    
    try:
        # Ejecutar el script
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=False, 
                              text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error ejecutando {script_name}: {e}")
        return False

def show_menu():
    """Muestra menú de opciones"""
    print("\n📋 OPCIONES DISPONIBLES")
    print("=" * 30)
    print("1️⃣ Bot Estable (Recomendado)")
    print("2️⃣ Bot Original (Completo)")
    print("3️⃣ Bot Alternativo (Experimental)")
    print("4️⃣ Configurar dependencias")
    print("5️⃣ Diagnóstico completo")
    print("6️⃣ Abrir Chrome manualmente")
    print("7️⃣ Forzar Chrome (cerrar Edge)")
    print("0️⃣ Salir")
    print()

def run_diagnostics():
    """Ejecuta diagnóstico completo del sistema"""
    print("\n🔍 DIAGNÓSTICO COMPLETO")
    print("=" * 30)
    
    results = {
        "Chrome": check_chrome(),
        "Selenium": test_selenium(),
        "AI Assistant": test_ai_assistant()
    }
    
    print("\n📊 RESULTADOS:")
    for component, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {component}")
    
    print("\n💡 RECOMENDACIONES:")
    
    if all(results.values()):
        print("🎉 Todo funciona perfectamente!")
        print("🚀 Usa cualquier versión del bot")
    elif results["Chrome"] and results["AI Assistant"]:
        if not results["Selenium"]:
            print("⚠️ Selenium con problemas")
            print("🔧 Usa Bot Estable o Alternativo")
        else:
            print("✅ Sistema en buen estado")
    else:
        print("🚨 Problemas detectados:")
        if not results["Chrome"]:
            print("   - Instala Google Chrome")
        if not results["AI Assistant"]:
            print("   - Revisa configuración de base de datos")
        if not results["Selenium"]:
            print("   - Reinstala dependencias de Selenium")

def setup_dependencies():
    """Configura dependencias automáticamente"""
    print("\n📦 CONFIGURANDO DEPENDENCIAS")
    print("=" * 35)
    
    dependencies = [
        "selenium>=4.15.0",
        "webdriver-manager>=4.0.0",
        "pyautogui",
        "opencv-python",
        "psutil"
    ]
    
    for dep in dependencies:
        try:
            print(f"⬇️ Instalando {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep} instalado")
        except subprocess.CalledProcessError:
            print(f"❌ Error instalando {dep}")
    
    print("\n✅ Configuración completada")

def abrir_chrome_manual():
    """Abre Chrome manualmente para WhatsApp Web"""
    print("\n🌐 ABRIR CHROME MANUALMENTE")
    print("=" * 35)
    
    try:
        from chrome_utils import emergency_chrome_launch
        emergency_chrome_launch()
    except ImportError:
        # Fallback si no está disponible chrome_utils
        print("⚠️ Utilidades de Chrome no disponibles")
        print("🔧 Abriendo Chrome básico...")
        
        import webbrowser
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"))
        webbrowser.get('chrome').open("https://web.whatsapp.com")
        print("✅ Chrome abierto. Ve a WhatsApp Web y escanea el QR")

def forzar_chrome():
    """Fuerza el uso de Chrome cerrando Edge"""
    print("\n🔧 FORZAR CHROME (CERRAR EDGE)")
    print("=" * 35)
    
    try:
        from chrome_utils import prepare_chrome_environment
        if prepare_chrome_environment():
            print("✅ Entorno preparado para Chrome")
            print("💡 Ahora puedes intentar ejecutar el bot")
        else:
            print("⚠️ Algunos pasos fallaron, pero puedes intentar continuar")
    except ImportError:
        print("⚠️ Utilidades de Chrome no disponibles")
        print("🔧 Cerrando Edge manualmente...")
        
        import psutil
        edge_closed = False
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and 'edge' in proc.info['name'].lower():
                    print(f"🚫 Cerrando: {proc.info['name']}")
                    proc.terminate()
                    edge_closed = True
            except:
                pass
        
        if edge_closed:
            print("✅ Procesos de Edge cerrados")
        else:
            print("ℹ️ No se encontraron procesos de Edge ejecutándose")

    print("\n✅ Configuración completada")

def get_best_bot_version():
    """Determina automáticamente la mejor versión"""
    print("🤖 Determinando mejor versión del bot...")
    
    chrome_ok = check_chrome()
    selenium_ok = test_selenium()
    ai_ok = test_ai_assistant()
    
    if selenium_ok and chrome_ok and ai_ok:
        return "whatsapp_bot_simple.py", "Bot Original (Todas las funcionalidades)"
    elif chrome_ok and ai_ok:
        return "whatsapp_bot_stable.py", "Bot Estable (Configuración mínima)"
    elif chrome_ok:
        return "whatsapp_bot_alternative.py", "Bot Alternativo (PyAutoGUI)"
    else:
        return None, "No se puede ejecutar ningún bot"

def main():
    """Función principal del launcher"""
    print("🤖 LAUNCHER BOT WHATSAPP - CajaCentral POS")
    print("=" * 45)
    print("Seleccionando automáticamente la mejor versión...")
    
    # Diagnóstico rápido
    bot_script, bot_description = get_best_bot_version()
    
    if bot_script:
        print(f"\n🎯 Versión recomendada: {bot_description}")
        
        while True:
            show_menu()
            
            try:
                choice = input("Selecciona una opción (1-7, 0 para salir): ").strip()
                
                if choice == "0":
                    print("👋 ¡Hasta luego!")
                    break
                elif choice == "1":
                    launch_bot_version("whatsapp_bot_stable.py", "Bot Estable")
                elif choice == "2":
                    launch_bot_version("whatsapp_bot_simple.py", "Bot Original")
                elif choice == "3":
                    launch_bot_version("whatsapp_bot_alternative.py", "Bot Alternativo")
                elif choice == "4":
                    setup_dependencies()
                elif choice == "5":
                    run_diagnostics()
                elif choice == "6":
                    abrir_chrome_manual()
                elif choice == "7":
                    forzar_chrome()
                else:
                    print("❌ Opción inválida")
                
                if choice in ["1", "2", "3"]:
                    # Preguntar si quiere reintentar
                    retry = input("\n¿Quieres probar otra versión? (s/n): ").lower()
                    if retry not in ['s', 'si', 'sí', 'y', 'yes']:
                        break
                
            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    else:
        print("❌ No se puede ejecutar el bot. Ejecuta diagnóstico completo.")
        run_diagnostics()

if __name__ == "__main__":
    main()
