"""
Launcher Principal para CajaCentral POS
Ejecuta la aplicación principal con tu logo integrado
"""

import sys
import os
import traceback
fro    elif choice == "1":
        print()
        print("🔐 Iniciando aplicación con login seguro...")
        print()
        
        if run_main_app():
            print()
            print("✅ Aplicación ejecutada correctamente")
        else:
            print()
            print("❌ No se pudo ejecutar la aplicación")
            print("💡 Verifica que los archivos principales existan")
            
        input("\nPresiona Enter para continuar...")rt Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

def run_main_app():
    """Ejecuta la aplicación principal del POS"""
    print("=" * 60)
    print("    INICIANDO CAJACENTRAL POS")
    print("    Con tu logo personalizado integrado")
    print("=" * 60)
    print()
    
    try:
        # Intentar cargar el sistema de branding primero
        print("🎨 Cargando sistema de branding...")
        from core.brand_manager import get_brand_manager
        brand_manager = get_brand_manager()
        print(f"✅ Logo cargado: {len(brand_manager.logos)} tamaños disponibles")
        print()
    except Exception as e:
        print(f"⚠️ Sistema de branding no disponible: {e}")
        print()
    
    # Intentar ejecutar las diferentes versiones en orden de preferencia
    apps_to_try = [
        ("UI Moderna", "ui.main_modern", "main"),
        ("Sistema Principal", "main_system", "main"),
        ("POS Moderno", "pos_modern", "main"),
        ("Aplicación Principal", "app", "main"),
        ("Sistema Simple", "main_simple", "main"),
        ("Main General", "main", "main")
    ]
    
    for app_name, module_name, function_name in apps_to_try:
        try:
            print(f"🚀 Intentando ejecutar: {app_name}")
            
            # Importar el módulo
            module = __import__(module_name, fromlist=[function_name])
            
            # Obtener la función principal
            if hasattr(module, function_name):
                main_function = getattr(module, function_name)
                print(f"✅ {app_name} encontrada, ejecutando...")
                print()
                
                # Ejecutar la aplicación
                main_function()
                return True
                
            else:
                print(f"⚠️ Función '{function_name}' no encontrada en {module_name}")
                
        except ImportError as e:
            print(f"⚠️ No se pudo importar {module_name}: {e}")
        except Exception as e:
            print(f"❌ Error ejecutando {app_name}: {e}")
            print("🔧 Intentando siguiente opción...")
            print()
    
    # Si nada funcionó, intentar ejecutar directamente archivos Python
    print("🔄 Intentando ejecutar archivos directamente...")
    
    python_files = [
        "pos_modern.py",
        "main_system.py", 
        "main.py",
        "app.py"
    ]
    
    for py_file in python_files:
        if os.path.exists(py_file):
            try:
                print(f"🚀 Ejecutando {py_file}...")
                os.system(f"python {py_file}")
                return True
            except Exception as e:
                print(f"❌ Error ejecutando {py_file}: {e}")
    
    print("❌ No se pudo ejecutar ninguna versión de la aplicación")
    return False

def show_system_info():
    """Muestra información del sistema antes de ejecutar"""
    print("📊 INFORMACIÓN DEL SISTEMA")
    print("-" * 40)
    
    try:
        # Mostrar info de IA
        from core.ai_assistant import POSAIAssistant
        from core.database import DatabaseManager
        
        db_manager = DatabaseManager()
        ai = POSAIAssistant(db_manager)
        status = ai.get_engine_status()
        
        print(f"🤖 Engines IA activos: {len(status['active_engines'])}")
        if status['active_engines']:
            for engine in status['active_engines']:
                print(f"   ✅ {engine}")
        
        if status.get('ollama_available'):
            print(f"🧠 Modelo Ollama: {status.get('ollama_current_model', 'N/A')}")
        
    except Exception as e:
        print(f"⚠️ IA no disponible: {e}")
    
    try:
        # Mostrar info de branding
        from core.brand_manager import get_brand_manager
        brand_manager = get_brand_manager()
        company_info = brand_manager.get_company_info()
        
        print(f"🎨 Logo: ✅ Cargado ({len(brand_manager.logos)} tamaños)")
        print(f"🏢 Empresa: {company_info['name']}")
        print(f"📝 Versión: {company_info['version']}")
        
    except Exception as e:
        print(f"⚠️ Branding no disponible: {e}")
    
    print()

def main():
    """Función principal del launcher"""
    print()
    print("🏪 CAJACENTRAL POS - LAUNCHER")
    print("Iniciando tu sistema personalizado...")
    print()
    
    # Mostrar información del sistema
    show_system_info()
    
    # Preguntar al usuario qué quiere hacer
    print("¿Qué quieres hacer?")
    print()
    print("1. Ejecutar aplicación principal")
    print("2. Ver demo con tu logo")
    print("3. Mostrar información del sistema")
    print("4. Salir")
    print()
    
    choice = input("Selecciona opción (1-4): ").strip()
    
    if choice == "1":
        print()
        print("🚀 Ejecutando aplicación principal...")
        print()
        
        if run_main_app():
            print()
            print("✅ Aplicación ejecutada correctamente")
        else:
            print()
            print("❌ No se pudo ejecutar la aplicación")
            print("💡 Verifica que los archivos principales existan")
            
        input("\nPresiona Enter para continuar...")
    
    elif choice == "2":
        try:
            import logo_demo
            logo_demo.main()
        except Exception as e:
            print(f"❌ Error ejecutando demo: {e}")
            input("\nPresiona Enter para continuar...")
    
    elif choice == "3":
        print()
        show_system_info()
        
        # Mostrar más detalles
        print("📁 ARCHIVOS PRINCIPALES ENCONTRADOS:")
        main_files = ["main.py", "app.py", "pos_modern.py", "main_system.py"]
        for file in main_files:
            if os.path.exists(file):
                print(f"   ✅ {file}")
            else:
                print(f"   ❌ {file}")
        
        print()
        print("📂 CARPETAS IMPORTANTES:")
        folders = ["core", "ui", "assets", "data", "logs"]
        for folder in folders:
            if os.path.exists(folder):
                print(f"   ✅ {folder}/")
            else:
                print(f"   ❌ {folder}/")
        
        input("\nPresiona Enter para continuar...")
    
    elif choice == "4":
        print("👋 ¡Hasta luego!")
        return
    
    else:
        print("❌ Opción no válida")
        input("Presiona Enter para continuar...")
    
    # Volver al menú
    main()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Saliendo...")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        print("\nDetalles del error:")
        traceback.print_exc()
        input("\nPresiona Enter para salir...")
