"""
Utilitario para forzar Chrome y evitar Edge
Funciones auxiliares para el bot de WhatsApp
"""

import psutil
import subprocess
import os
import time

def kill_edge_processes():
    """Cierra procesos de Edge que puedan interferir"""
    print("🔍 Verificando procesos de Edge que puedan interferir...")
    
    edge_processes = [
        "msedge.exe",
        "msedgewebview2.exe", 
        "MicrosoftEdge.exe",
        "WebView2.exe"
    ]
    
    killed_any = False
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and any(edge in proc.info['name'] for edge in edge_processes):
                print(f"🚫 Cerrando proceso Edge: {proc.info['name']} (PID: {proc.info['pid']})")
                proc.terminate()
                killed_any = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if killed_any:
        print("⏳ Esperando a que Edge se cierre completamente...")
        time.sleep(3)
        print("✅ Procesos de Edge cerrados")
    else:
        print("✅ No hay procesos de Edge ejecutándose")

def force_chrome_default():
    """Intenta configurar Chrome como navegador predeterminado temporalmente"""
    try:
        # Verificar Chrome instalado
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
        
        chrome_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                break
        
        if not chrome_path:
            print("❌ Chrome no encontrado para configurar como predeterminado")
            return False
        
        print("🔧 Configurando Chrome como navegador predeterminado temporalmente...")
        
        # Comando para hacer Chrome predeterminado (requiere confirmación del usuario)
        subprocess.run([chrome_path, "--make-default-browser"], check=False)
        
        print("✅ Configuración de Chrome completada")
        return True
        
    except Exception as e:
        print(f"⚠️ No se pudo configurar Chrome como predeterminado: {e}")
        return False

def get_chrome_executable():
    """Obtiene la ruta exacta del ejecutable de Chrome"""
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            return path
    
    return None

def verify_chrome_installation():
    """Verifica que Chrome esté correctamente instalado"""
    print("🔍 Verificando instalación completa de Chrome...")
    
    chrome_exe = get_chrome_executable()
    if not chrome_exe:
        print("❌ Ejecutable de Chrome no encontrado")
        return False
    
    try:
        # Verificar versión
        result = subprocess.run([chrome_exe, "--version"], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            version = result.stdout.strip()
            if "Google Chrome" in version:
                print(f"✅ Chrome verificado: {version}")
                return True
            else:
                print(f"⚠️ Versión inesperada: {version}")
                return False
        else:
            print("❌ Chrome no responde correctamente")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Chrome tardó demasiado en responder")
        return False
    except Exception as e:
        print(f"❌ Error verificando Chrome: {e}")
        return False

def open_chrome_manually(url="https://web.whatsapp.com"):
    """Abre Chrome manualmente como último recurso"""
    print(f"🌐 Abriendo Chrome manualmente para: {url}")
    
    chrome_exe = get_chrome_executable()
    if not chrome_exe:
        print("❌ No se puede abrir Chrome manualmente")
        return False
    
    try:
        # Cerrar Edge primero
        kill_edge_processes()
        
        # Abrir Chrome con parámetros específicos
        cmd = [
            chrome_exe,
            "--new-window",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--user-data-dir=./whatsapp_session",
            url
        ]
        
        process = subprocess.Popen(cmd)
        print(f"✅ Chrome abierto manualmente (PID: {process.pid})")
        print("📱 Por favor, escanea el código QR en WhatsApp Web")
        
        return True
        
    except Exception as e:
        print(f"❌ Error abriendo Chrome manualmente: {e}")
        return False

def prepare_chrome_environment():
    """Prepara el entorno para usar Chrome exclusivamente"""
    print("🔧 Preparando entorno para Chrome...")
    
    steps = [
        ("Cerrando procesos Edge", kill_edge_processes),
        ("Verificando Chrome", verify_chrome_installation),
    ]
    
    success = True
    for step_name, step_func in steps:
        try:
            print(f"⏳ {step_name}...")
            result = step_func()
            if result:
                print(f"✅ {step_name} - OK")
            else:
                print(f"⚠️ {step_name} - Advertencia")
                success = False
        except Exception as e:
            print(f"❌ {step_name} - Error: {e}")
            success = False
    
    return success

# Función de emergencia para usar Chrome cuando Selenium falla
def emergency_chrome_launch():
    """Lanza Chrome como último recurso cuando Selenium falla"""
    print("🚨 MODO EMERGENCIA: Iniciando Chrome manualmente")
    print("=" * 50)
    
    if not prepare_chrome_environment():
        print("❌ No se pudo preparar el entorno para Chrome")
        return False
    
    if open_chrome_manually():
        print("\n✅ Chrome abierto exitosamente en modo manual")
        print("📋 INSTRUCCIONES:")
        print("1. Ve a la pestaña de WhatsApp Web que se abrió")
        print("2. Escanea el código QR con tu teléfono")
        print("3. Una vez conectado, el bot podrá funcionar")
        print("4. Mantén esta ventana de Chrome abierta")
        
        return True
    else:
        print("❌ No se pudo abrir Chrome en modo manual")
        return False

if __name__ == "__main__":
    print("🧪 Probando utilidades de Chrome...")
    prepare_chrome_environment()
    
    # Preguntar si quiere abrir Chrome manualmente
    choice = input("\n¿Abrir Chrome manualmente para prueba? (s/n): ")
    if choice.lower() in ['s', 'si', 'sí', 'yes', 'y']:
        emergency_chrome_launch()
