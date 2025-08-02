"""
Script de configuración para el Bot de WhatsApp
Instala dependencias y configura el entorno
"""

import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """Instala las dependencias necesarias"""
    print("📦 Instalando dependencias para WhatsApp Bot...")
    
    dependencies = [
        "selenium>=4.15.0",
        "webdriver-manager>=4.0.0"
    ]
    
    for dep in dependencies:
        try:
            print(f"⬇️ Instalando {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep} instalado correctamente")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando {dep}: {e}")
            return False
    
    return True

def check_chrome():
    """Verifica si Google Chrome está instalado (NO Edge)"""
    print("🌐 Verificando instalación de Google Chrome...")
    
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ Google Chrome encontrado en: {path}")
            
            # Verificar que es realmente Chrome y no Edge
            try:
                import subprocess
                result = subprocess.run([path, "--version"], 
                                      capture_output=True, text=True, timeout=5)
                version_info = result.stdout.strip()
                
                if "Google Chrome" in version_info:
                    print(f"✅ Versión confirmada: {version_info}")
                elif "Microsoft Edge" in version_info:
                    print(f"⚠️ Detectado Edge en lugar de Chrome: {version_info}")
                    continue  # Buscar en otra ruta
                else:
                    print(f"✅ Chrome encontrado (versión: {version_info})")
            except:
                print("✅ Chrome encontrado (no se pudo verificar versión)")
            
            return True
    
    print("❌ Google Chrome no encontrado.")
    print("📥 Por favor instala Google Chrome desde:")
    print("🔗 https://www.google.com/chrome/")
    print("⚠️ IMPORTANTE: Microsoft Edge NO es compatible, necesitas Chrome específicamente")
    return False

def create_session_folder():
    """Crea la carpeta para mantener la sesión de WhatsApp"""
    session_path = Path("whatsapp_session")
    session_path.mkdir(exist_ok=True)
    print(f"📁 Carpeta de sesión creada: {session_path.absolute()}")

def test_ai_assistant():
    """Prueba que el AI Assistant funcione"""
    print("🤖 Probando AI Assistant...")
    
    try:
        from core.ai_assistant import POSAIAssistant
        from core.database import DatabaseManager
        
        db = DatabaseManager()
        ai = POSAIAssistant(db)
        
        # Probar respuesta
        response = ai.ask("¿Cómo hacer una venta?")
        
        if response and response.get('answer'):
            print("✅ AI Assistant funcionando correctamente")
            print(f"🧠 Engines disponibles: {ai.get_engine_status()['active_engines']}")
            return True
        else:
            print("⚠️ AI Assistant responde pero sin contenido")
            return False
            
    except Exception as e:
        print(f"❌ Error en AI Assistant: {e}")
        print("💡 El bot funcionará con respuestas básicas")
        return False

def create_startup_script():
    """Crea script de inicio rápido"""
    script_content = '''@echo off
echo 🚀 Iniciando Bot de WhatsApp para CajaCentral POS
echo.
python whatsapp_bot_simple.py
pause
'''
    
    with open("start_whatsapp_bot.bat", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("✅ Script de inicio creado: start_whatsapp_bot.bat")

def show_usage_instructions():
    """Muestra instrucciones de uso"""
    print("\n" + "="*60)
    print("📋 INSTRUCCIONES DE USO")
    print("="*60)
    print()
    print("1️⃣ Para iniciar el bot:")
    print("   • Ejecuta: python whatsapp_bot_simple.py")
    print("   • O usa: start_whatsapp_bot.bat")
    print()
    print("2️⃣ Primera vez:")
    print("   • Se abrirá Chrome con WhatsApp Web")
    print("   • Escanea el código QR con tu teléfono")
    print("   • ¡Listo! El bot monitoreará mensajes")
    print()
    print("3️⃣ Funcionalidades:")
    print("   • Responde automáticamente con IA")
    print("   • Horario: 8:00 AM - 8:00 PM")
    print("   • Integrado con tu sistema POS")
    print()
    print("4️⃣ Para detener:")
    print("   • Presiona Ctrl+C en la consola")
    print()
    print("⚠️ IMPORTANTE:")
    print("   • Mantén WhatsApp Web abierto")
    print("   • No cierres la ventana de Chrome")
    print("   • La sesión se guarda automáticamente")
    print()

def main():
    """Configuración principal"""
    print("🔧 CONFIGURADOR BOT WHATSAPP - CajaCentral POS")
    print("=" * 55)
    print()
    
    steps = [
        ("Verificando Chrome", check_chrome),
        ("Instalando dependencias", install_dependencies), 
        ("Creando carpeta de sesión", lambda: (create_session_folder(), True)[1]),
        ("Probando AI Assistant", test_ai_assistant),
        ("Creando script de inicio", lambda: (create_startup_script(), True)[1])
    ]
    
    all_ok = True
    
    for step_name, step_func in steps:
        print(f"⏳ {step_name}...")
        try:
            result = step_func()
            if result:
                print(f"✅ {step_name} - OK")
            else:
                print(f"⚠️ {step_name} - Advertencia")
                all_ok = False
        except Exception as e:
            print(f"❌ {step_name} - Error: {e}")
            all_ok = False
        print()
    
    print("🎯 RESUMEN DE CONFIGURACIÓN")
    print("-" * 30)
    
    if all_ok:
        print("✅ Configuración completada exitosamente")
        print("🚀 El bot está listo para usar")
    else:
        print("⚠️ Configuración completada con advertencias")
        print("🔧 Revisa los errores arriba, pero el bot debería funcionar")
    
    show_usage_instructions()
    
    # Preguntar si quiere iniciar ahora
    try:
        start_now = input("¿Quiere iniciar el bot ahora? (s/n): ").lower().strip()
        if start_now in ['s', 'si', 'sí', 'yes', 'y']:
            print("\n🚀 Iniciando bot...")
            import whatsapp_bot_simple
            whatsapp_bot_simple.main()
    except KeyboardInterrupt:
        print("\n👋 ¡Hasta luego!")

if __name__ == "__main__":
    main()
