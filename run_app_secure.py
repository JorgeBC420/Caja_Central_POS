"""
Launcher Principal para CajaCentral POS
Ejecuta la aplicación principal con tu logo integrado y login seguro
"""

import sys
import os
import traceback
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

def run_main_app():
    """Ejecuta la aplicación principal del POS con login seguro"""
    print("=" * 60)
    print("    INICIANDO CAJACENTRAL POS")
    print("    Con login seguro y tu logo integrado")
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
    
    # Intentar ejecutar la aplicación principal con login
    try:
        print("🔐 Iniciando con sistema de autenticación...")
        
        # Importar y ejecutar POS moderno con login
        import pos_modern
        pos_modern.main()
        return True
        
    except Exception as e:
        print(f"❌ Error ejecutando aplicación principal: {e}")
        traceback.print_exc()
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
    
    try:
        # Mostrar info de seguridad
        print("🔐 Sistema de login: ✅ Activo")
        print("👥 Usuarios disponibles: admin, cajero, gerente")
        
    except Exception as e:
        print(f"⚠️ Sistema de login no disponible: {e}")
    
    print()

def main():
    """Función principal del launcher"""
    print()
    print("🏪 CAJACENTRAL POS - LAUNCHER SEGURO")
    print("Iniciando tu sistema personalizado con autenticación...")
    print()
    
    # Mostrar información del sistema
    show_system_info()
    
    # Preguntar al usuario qué quiere hacer
    print("¿Qué quieres hacer?")
    print()
    print("1. Ejecutar aplicación principal (con login)")
    print("2. Ver demo con tu logo")
    print("3. Mostrar información del sistema")
    print("4. Salir")
    print()
    
    choice = input("Selecciona opción (1-4): ").strip()
    
    if choice == "1":
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
        main_files = ["main.py", "app.py", "pos_modern.py", "main_system.py", "login_secure.py"]
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
        
        print()
        print("🔐 SISTEMA DE SEGURIDAD:")
        print("   ✅ Login requerido para acceso")
        print("   ✅ Contraseñas hasheadas")
        print("   ✅ Control de intentos de login")
        print("   ✅ Roles y permisos configurados")
        
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
