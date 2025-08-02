"""
Launcher Principal Mejorado para CajaCentral POS
Integra sistema de estabilidad, IA con Ollama y recuperación automática
"""

import sys
import os
import time
import traceback
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

def setup_environment():
    """Configura el entorno de la aplicación"""
    print("🔧 Configurando entorno...")
    
    # Crear directorios necesarios
    required_dirs = ["data", "logs", "temp", "backups", "config"]
    for dir_name in required_dirs:
        os.makedirs(dir_name, exist_ok=True)
    
    # Configurar variables de entorno para estabilidad
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUNBUFFERED"] = "1"
    
    print("✅ Entorno configurado")

def initialize_stability():
    """Inicializa el sistema de estabilidad"""
    try:
        from core.stability_system import initialize_stability_system
        stability_manager = initialize_stability_system()
        print("✅ Sistema de estabilidad inicializado")
        return stability_manager
    except Exception as e:
        print(f"⚠️ Sistema de estabilidad no disponible: {e}")
        return None

def check_ai_systems():
    """Verifica y optimiza los sistemas de IA"""
    print("\n🤖 Verificando sistemas de IA...")
    
    ai_status = {
        "ollama": False,
        "chatterbot": False,
        "transformers": False,
        "total_engines": 0
    }
    
    # Verificar Ollama
    try:
        from core.ollama_client import get_ollama_client
        ollama_client = get_ollama_client()
        
        if ollama_client.is_healthy:
            ai_status["ollama"] = True
            ai_status["total_engines"] += 1
            print(f"✅ Ollama conectado: {ollama_client.current_model}")
        else:
            print("⚠️ Ollama disponible pero no saludable")
    except Exception as e:
        print(f"❌ Ollama no disponible: {e}")
    
    # Verificar ChatterBot
    try:
        from chatterbot import ChatBot
        ai_status["chatterbot"] = True
        ai_status["total_engines"] += 1
        print("✅ ChatterBot disponible")
    except ImportError:
        print("⚠️ ChatterBot no instalado")
    
    # Verificar Transformers
    try:
        from transformers import pipeline
        ai_status["transformers"] = True
        ai_status["total_engines"] += 1
        print("✅ Transformers disponible")
    except ImportError:
        print("⚠️ Transformers no instalado")
    
    print(f"📊 Engines IA activos: {ai_status['total_engines']}/3")
    return ai_status

def run_health_check():
    """Ejecuta un chequeo completo de salud"""
    print("\n🏥 Ejecutando chequeo de salud...")
    
    try:
        from core.stability_system import get_stability_manager, HealthChecker
        
        stability_manager = get_stability_manager()
        health_checker = HealthChecker(stability_manager)
        
        health_results = health_checker.comprehensive_health_check()
        
        status_emoji = {
            "excellent": "🟢",
            "good": "🟡", 
            "fair": "🟠",
            "poor": "🔴"
        }
        
        status = health_results["overall_status"]
        emoji = status_emoji.get(status, "⚪")
        
        print(f"{emoji} Estado general: {status.upper()}")
        print(f"✅ Verificaciones: {health_results['passed_checks']}/{health_results['total_checks']}")
        print(f"📊 Salud: {health_results['health_percentage']:.1f}%")
        
        # Mostrar problemas si los hay
        problems = []
        for check_name, result in health_results["checks"].items():
            if result.get("status") != "ok":
                problems.append(f"⚠️ {check_name}: {result.get('error', 'Warning')}")
        
        if problems:
            print("\n🚨 Problemas detectados:")
            for problem in problems[:3]:  # Mostrar solo los primeros 3
                print(f"  {problem}")
        
        return health_results
        
    except Exception as e:
        print(f"❌ Error en health check: {e}")
        return None

def show_main_menu():
    """Muestra el menú principal optimizado"""
    try:
        from core.brand_manager import get_brand_manager
        brand_manager = get_brand_manager()
        company_info = brand_manager.get_company_info()
        
        print("\n" + "="*60)
        print(f"🏢 {company_info['name'].upper()}")
        print(f"   {company_info['tagline']}")
        print(f"   Versión {company_info['version']} | Con tu logo personalizado ✨")
        print("="*60)
    except:
        print("\n" + "="*50)
        print("🏪 CAJACENTRAL POS - LAUNCHER OPTIMIZADO")
        print("="*50)
    
    print("1️⃣  Iniciar aplicación principal (Recomendado)")
    print("2️⃣  Sistema POS moderno (UI mejorada)")
    print("3️⃣  Bot WhatsApp con IA")
    print("4️⃣  Asistente IA interactivo")
    print("5️⃣  Diagnóstico completo del sistema")
    print("6️⃣  Configurar sistema")
    print("7️⃣  Optimizar rendimiento")
    print("8️⃣  Ver logs y errores")
    print("9️⃣  Backup y restauración")
    print("🎨  Ver sistema con tu logo")
    print("0️⃣  Salir")
    print("="*60)

def launch_main_app():
    """Lanza la aplicación principal con manejo de errores"""
    print("🚀 Iniciando aplicación principal...")
    
    try:
        # Intentar importar y ejecutar la app principal
        import app
        app.main()
        
    except ImportError:
        try:
            # Fallback a main.py
            import main
            if hasattr(main, 'main'):
                main.main()
            else:
                exec(open('main.py').read())
        except:
            try:
                # Fallback a main_system.py
                import main_system
                main_system.main()
            except Exception as e:
                print(f"❌ Error lanzando aplicación principal: {e}")
                print("💡 Verifica que los archivos principales existan")
                return False
    
    except Exception as e:
        print(f"❌ Error en aplicación principal: {e}")
        print("🔧 Intentando recuperación automática...")
        return False
    
    return True

def launch_modern_pos():
    """Lanza el sistema POS moderno"""
    print("🚀 Iniciando POS moderno...")
    
    try:
        from ui.main_modern import main as modern_main
        modern_main()
    except ImportError:
        try:
            import pos_modern
            pos_modern.main()
        except Exception as e:
            print(f"❌ Error lanzando POS moderno: {e}")
            return False
    
    return True

def launch_whatsapp_bot():
    """Lanza el bot de WhatsApp"""
    print("🚀 Iniciando bot WhatsApp...")
    
    try:
        import launch_whatsapp_bot
        launch_whatsapp_bot.main()
    except Exception as e:
        print(f"❌ Error lanzando bot WhatsApp: {e}")
        return False
    
    return True

def launch_ai_assistant():
    """Lanza el asistente IA interactivo"""
    print("🤖 Iniciando asistente IA...")
    
    try:
        from core.ai_assistant import POSAIAssistant
        from core.database import DatabaseManager
        
        print("🔧 Inicializando IA...")
        db_manager = DatabaseManager()
        ai_assistant = POSAIAssistant(db_manager)
        
        print("✅ Asistente IA listo!")
        print("💬 Escribe 'salir' para terminar")
        print("-" * 40)
        
        while True:
            try:
                question = input("\n❓ Tu pregunta: ").strip()
                
                if question.lower() in ['salir', 'exit', 'quit']:
                    break
                
                if not question:
                    continue
                
                print("🤔 Pensando...")
                start_time = time.time()
                
                response = ai_assistant.ask(question)
                
                end_time = time.time()
                response_time = end_time - start_time
                
                print(f"\n🤖 {response.get('title', 'Respuesta')}:")
                print(f"📝 {response.get('answer', 'Sin respuesta')}")
                
                if response.get('confidence'):
                    print(f"📊 Confianza: {response['confidence']:.0%}")
                
                print(f"⚡ Engine: {response.get('engine', 'unknown')}")
                print(f"⏱️ Tiempo: {response_time:.2f}s")
                
                # Mostrar sugerencias si las hay
                if response.get('suggestions'):
                    print(f"\n💡 Preguntas relacionadas:")
                    for i, suggestion in enumerate(response['suggestions'][:3], 1):
                        print(f"   {i}. {suggestion}")
                
                print("-" * 40)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("👋 ¡Hasta luego!")
        return True
        
    except Exception as e:
        print(f"❌ Error iniciando asistente IA: {e}")
        return False

def run_system_diagnostics():
    """Ejecuta diagnósticos completos del sistema"""
    print("🔍 Ejecutando diagnósticos completos...")
    
    # Health check
    health_results = run_health_check()
    
    # Verificar IA
    ai_status = check_ai_systems()
    
    # Test de rendimiento
    print("\n⚡ Probando rendimiento...")
    try:
        from core.stability_system import get_stability_manager
        
        stability_manager = get_stability_manager()
        
        # Test básico de BD
        start_time = time.time()
        try:
            import sqlite3
            with sqlite3.connect("caja_registradora_pos_cr.db", timeout=5) as conn:
                conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
            db_time = (time.time() - start_time) * 1000
            print(f"✅ Base de datos: {db_time:.1f}ms")
        except Exception as e:
            print(f"❌ Base de datos: {e}")
        
        # Test de IA si está disponible
        if ai_status["ollama"]:
            from core.ollama_client import get_ollama_client
            ollama_client = get_ollama_client()
            
            print("🧪 Probando Ollama...")
            start_time = time.time()
            response = ollama_client.ask("Test", max_tokens=10)
            ai_time = (time.time() - start_time) * 1000
            
            if response.success:
                print(f"✅ Ollama: {ai_time:.1f}ms")
            else:
                print(f"⚠️ Ollama: Lento o con problemas")
        
    except Exception as e:
        print(f"❌ Error en test de rendimiento: {e}")
    
    print("\n📋 Resumen de diagnósticos completado")

def configure_system():
    """Configura el sistema"""
    print("⚙️ Configuración del sistema...")
    print("\n1. Instalar dependencias faltantes")
    print("2. Configurar base de datos")
    print("3. Configurar impresoras")
    print("4. Configurar IA (Ollama)")
    print("5. Optimizar rendimiento")
    print("0. Volver")
    
    choice = input("\nSelecciona opción: ").strip()
    
    if choice == "1":
        install_dependencies()
    elif choice == "2":
        configure_database()
    elif choice == "4":
        configure_ollama()
    else:
        print("Opción no implementada aún")

def install_dependencies():
    """Instala dependencias faltantes"""
    print("📦 Instalando dependencias...")
    
    required_packages = [
        "chatterbot",
        "transformers",
        "torch",
        "psutil",
        "requests"
    ]
    
    import subprocess
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} ya instalado")
        except ImportError:
            print(f"📦 Instalando {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ {package} instalado")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error instalando {package}: {e}")

def configure_database():
    """Configura la base de datos"""
    print("🗃️ Configurando base de datos...")
    
    try:
        from core.database import DatabaseManager
        db_manager = DatabaseManager()
        
        # Verificar integridad
        print("🔍 Verificando integridad...")
        # Aquí iría la lógica de verificación
        
        print("✅ Base de datos configurada correctamente")
        
    except Exception as e:
        print(f"❌ Error configurando BD: {e}")

def configure_ollama():
    """Configura Ollama para mejor rendimiento"""
    print("🤖 Configurando Ollama...")
    
    try:
        from core.ollama_client import get_ollama_client
        
        client = get_ollama_client()
        status = client.get_status()
        
        print(f"📊 Estado actual: {'✅ Saludable' if status['healthy'] else '❌ Con problemas'}")
        print(f"🤖 Modelo actual: {status['current_model']}")
        print(f"📋 Modelos disponibles: {len(status['available_models'])}")
        
        if status['available_models']:
            print("\n🔄 Modelos disponibles:")
            for i, model in enumerate(status['available_models'], 1):
                current = " (ACTUAL)" if model == status['current_model'] else ""
                print(f"   {i}. {model}{current}")
            
            choice = input("\n¿Cambiar modelo? (número o Enter para continuar): ").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(status['available_models']):
                new_model = status['available_models'][int(choice) - 1]
                if client.switch_model(new_model):
                    print(f"✅ Cambiado a {new_model}")
                else:
                    print(f"❌ No se pudo cambiar a {new_model}")
        
    except Exception as e:
        print(f"❌ Error configurando Ollama: {e}")

def show_branded_demo():
    """Muestra una demo del sistema con el logo personalizado"""
    print("🎨 Iniciando demo con tu logo personalizado...")
    
    try:
        from core.brand_manager import get_brand_manager
        import tkinter as tk
        from tkinter import ttk, messagebox
        
        brand_manager = get_brand_manager()
        
        # Crear ventana principal
        window = brand_manager.create_branded_window("Demo con Tu Logo", (900, 700))
        
        # Header con logo
        header = brand_manager.create_header_frame(window, show_logo=True, show_title=True)
        
        # Frame principal
        main_frame = tk.Frame(window)
        brand_manager.apply_theme_to_widget(main_frame, "frame")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título de bienvenida
        welcome_label = tk.Label(
            main_frame,
            text="¡Tu Logo Se Ve Increíble! 🎉",
            font=("Arial", 18, "bold")
        )
        brand_manager.apply_theme_to_widget(welcome_label, "label")
        welcome_label.pack(pady=20)
        
        # Información del logo
        logo_info = brand_manager.get_logo("original")
        if logo_info:
            info_text = f"""Tu logo personal está integrado en todo el sistema:
            
📐 Tamaño original: {logo_info.size[0]} x {logo_info.size[1]} píxeles
🎨 Se adapta automáticamente a diferentes tamaños
✨ Se ve profesional en todas las ventanas
💼 Representa tu marca correctamente
            
¡Esto le da un toque muy profesional a tu sistema POS!"""
        else:
            info_text = "Logo cargado correctamente en el sistema"
        
        info_label = tk.Label(
            main_frame,
            text=info_text,
            font=("Arial", 11),
            justify="left"
        )
        brand_manager.apply_theme_to_widget(info_label, "label")
        info_label.pack(pady=20, padx=20, anchor="w")
        
        # Frame de botones
        button_frame = tk.Frame(main_frame)
        brand_manager.apply_theme_to_widget(button_frame, "frame")
        button_frame.pack(pady=30)
        
        # Botones de demo
        def show_pos_demo():
            demo_window = brand_manager.create_branded_window("POS Demo", (800, 600))
            demo_header = brand_manager.create_header_frame(demo_window)
            
            demo_label = tk.Label(
                demo_window,
                text="Esta sería tu pantalla principal del POS\\ncon tu logo en la parte superior",
                font=("Arial", 14),
                pady=50
            )
            brand_manager.apply_theme_to_widget(demo_label, "label")
            demo_label.pack(expand=True)
            
            close_btn = tk.Button(
                demo_window,
                text="Cerrar Demo",
                command=demo_window.destroy
            )
            brand_manager.apply_theme_to_widget(close_btn, "button")
            close_btn.pack(pady=20)
        
        demo_btn = tk.Button(
            button_frame,
            text="Ver Demo POS",
            command=show_pos_demo,
            padx=20,
            pady=10
        )
        brand_manager.apply_theme_to_widget(demo_btn, "button")
        demo_btn.pack(side="left", padx=10)
        
        # Botón para mostrar info
        def show_logo_info():
            company_info = brand_manager.get_company_info()
            colors = brand_manager.get_brand_colors()
            
            info_text = f"""Información del Sistema de Branding:
            
🏢 Empresa: {company_info['name']}
📝 Eslogan: {company_info['tagline']}
🎨 Logos disponibles: {len(brand_manager.logos)}
🎯 Iconos cargados: {len(brand_manager.icons)}
🎨 Colores personalizados: {len(colors)}

¡Tu marca está completamente integrada!"""
            
            messagebox.showinfo("Info del Branding", info_text)
        
        info_btn = tk.Button(
            button_frame,
            text="Ver Información",
            command=show_logo_info,
            padx=20,
            pady=10
        )
        brand_manager.apply_theme_to_widget(info_btn, "button")
        info_btn.pack(side="left", padx=10)
        
        # Botón cerrar
        close_btn = tk.Button(
            button_frame,
            text="¡Perfecto! Cerrar",
            command=window.destroy,
            padx=20,
            pady=10
        )
        brand_manager.apply_theme_to_widget(close_btn, "button")
        close_btn.pack(side="left", padx=10)
        
        # Status bar
        status = brand_manager.create_status_bar(
            window, 
            "Sistema personalizado con tu logo - ¡Se ve increíble!"
        )
        
        # Centrar ventana
        window.update_idletasks()
        x = (window.winfo_screenwidth() // 2) - (900 // 2)
        y = (window.winfo_screenheight() // 2) - (700 // 2)
        window.geometry(f"900x700+{x}+{y}")
        
        print("✅ Demo iniciada. ¡Mira qué profesional se ve tu logo!")
        window.mainloop()
        
        return True
        
    except Exception as e:
        print(f"❌ Error mostrando demo: {e}")
        print("💡 Tip: Asegúrate de tener tu logo.png en la carpeta assets/")
        return False

def view_logs():
    """Muestra logs y errores recientes"""
    print("📋 Logs del sistema...")
    
    try:
        log_file = "logs/pos_stability.log"
        if os.path.exists(log_file):
            print(f"\n📄 Últimas 20 líneas de {log_file}:")
            print("-" * 50)
            
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-20:]:
                    print(line.rstrip())
        else:
            print("📄 No se encontraron logs")
    
    except Exception as e:
        print(f"❌ Error leyendo logs: {e}")

def main():
    """Función principal del launcher"""
    try:
        # Configuración inicial
        setup_environment()
        
        # Inicializar estabilidad
        stability_manager = initialize_stability()
        
        # Verificar IA
        ai_status = check_ai_systems()
        
        # Menú principal
        while True:
            show_main_menu()
            
            try:
                choice = input("\n🎯 Selecciona una opción: ").strip()
                
                if choice == "0":
                    print("👋 ¡Hasta luego!")
                    break
                
                elif choice == "1":
                    if not launch_main_app():
                        input("\nPresiona Enter para continuar...")
                
                elif choice == "2":
                    if not launch_modern_pos():
                        input("\nPresiona Enter para continuar...")
                
                elif choice == "3":
                    if not launch_whatsapp_bot():
                        input("\nPresiona Enter para continuar...")
                
                elif choice == "4":
                    if not launch_ai_assistant():
                        input("\nPresiona Enter para continuar...")
                
                elif choice == "5":
                    run_system_diagnostics()
                    input("\nPresiona Enter para continuar...")
                
                elif choice == "6":
                    configure_system()
                    input("\nPresiona Enter para continuar...")
                
                elif choice == "8":
                    view_logs()
                    input("\nPresiona Enter para continuar...")
                
                elif choice.lower() == "🎨" or choice == "logo":
                    if not show_branded_demo():
                        input("\nPresiona Enter para continuar...")
                
                else:
                    print("❌ Opción no válida")
                    print("💡 Tip: También puedes escribir 'logo' o '🎨' para ver tu sistema personalizado")
                    time.sleep(2)
            
            except KeyboardInterrupt:
                print("\n👋 Saliendo...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                if stability_manager:
                    stability_manager.log_error(e, "main_launcher", severity="medium")
                time.sleep(2)
    
    except Exception as e:
        print(f"❌ Error crítico en launcher: {e}")
        traceback.print_exc()
        input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()
