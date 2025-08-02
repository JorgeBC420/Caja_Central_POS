"""
Launcher Simple para mostrar el sistema con tu logo
Sin problemas de encoding y enfocado en mostrar tu branding
"""

import sys
import os
import time

def show_logo_demo():
    """Muestra tu sistema POS con tu logo real"""
    print("=" * 60)
    print("   DEMO DE TU SISTEMA POS PERSONALIZADO")
    print("=" * 60)
    print()
    
    try:
        from core.brand_manager import get_brand_manager
        import tkinter as tk
        from tkinter import messagebox
        
        brand_manager = get_brand_manager()
        
        print("Cargando tu logo...")
        
        # Crear ventana principal
        window = brand_manager.create_branded_window("Tu Sistema POS Personalizado", (1000, 700))
        
        # Header con tu logo
        header = brand_manager.create_header_frame(window, show_logo=True, show_title=True)
        
        # Frame principal
        main_frame = tk.Frame(window)
        brand_manager.apply_theme_to_widget(main_frame, "frame")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Título principal
        title_label = tk.Label(
            main_frame,
            text="¡Tu Logo Se Ve Increíble en el Sistema POS!",
            font=("Arial", 20, "bold")
        )
        brand_manager.apply_theme_to_widget(title_label, "label")
        title_label.pack(pady=20)
        
        # Información del logo
        logo_original = brand_manager.get_logo("original")
        if logo_original:
            info_text = f"""INFORMACIÓN DE TU LOGO:
            
Tamaño original: {logo_original.size[0]} x {logo_original.size[1]} píxeles
Eso está perfecto para un sistema profesional!

CARACTERÍSTICAS DEL SISTEMA:
• Tu logo aparece en todas las ventanas principales
• Se adapta automáticamente a diferentes tamaños
• Mantiene la calidad profesional en todo momento
• Le da identidad única a tu negocio

ESTO ES LO QUE TE COSTÓ TRABAJO:
Tu logo real, tu marca, tu identidad empresarial
¡Y ahora está completamente integrado en tu sistema POS!"""
        else:
            info_text = "Sistema cargado con tu branding personalizado"
        
        info_label = tk.Label(
            main_frame,
            text=info_text,
            font=("Arial", 12),
            justify="left"
        )
        brand_manager.apply_theme_to_widget(info_label, "label")
        info_label.pack(pady=20, anchor="w")
        
        # Frame de botones
        button_frame = tk.Frame(main_frame)
        brand_manager.apply_theme_to_widget(button_frame, "frame")
        button_frame.pack(pady=30)
        
        # Botón para demo del POS
        def demo_pos():
            pos_window = brand_manager.create_branded_window("POS Demo - Con Tu Logo", (900, 600))
            pos_header = brand_manager.create_header_frame(pos_window)
            
            demo_content = tk.Frame(pos_window)
            brand_manager.apply_theme_to_widget(demo_content, "frame")
            demo_content.pack(fill="both", expand=True, padx=40, pady=40)
            
            demo_title = tk.Label(
                demo_content,
                text="PANTALLA PRINCIPAL DEL POS",
                font=("Arial", 16, "bold")
            )
            brand_manager.apply_theme_to_widget(demo_title, "label")
            demo_title.pack(pady=20)
            
            demo_info = tk.Label(
                demo_content,
                text="""Así se vería tu pantalla principal de ventas:

• Tu logo siempre visible en la parte superior
• Interfaz profesional y personalizada
• Colores que representan tu marca
• Un sistema que se ve como TU negocio

¡Esto es lo que hace la diferencia entre un sistema
genérico y TU sistema personalizado!""",
                font=("Arial", 12),
                justify="left"
            )
            brand_manager.apply_theme_to_widget(demo_info, "label")
            demo_info.pack(pady=20)
            
            close_demo = tk.Button(
                demo_content,
                text="Cerrar Demo",
                command=pos_window.destroy,
                font=("Arial", 12, "bold"),
                padx=20,
                pady=10
            )
            brand_manager.apply_theme_to_widget(close_demo, "button")
            close_demo.pack(pady=30)
            
            # Centrar ventana
            pos_window.update_idletasks()
            x = (pos_window.winfo_screenwidth() // 2) - (450)
            y = (pos_window.winfo_screenheight() // 2) - (300)
            pos_window.geometry(f"900x600+{x}+{y}")
        
        demo_btn = tk.Button(
            button_frame,
            text="Ver Demo del POS",
            command=demo_pos,
            font=("Arial", 12, "bold"),
            padx=20,
            pady=10
        )
        brand_manager.apply_theme_to_widget(demo_btn, "button")
        demo_btn.pack(side="left", padx=15)
        
        # Botón de información
        def show_info():
            company_info = brand_manager.get_company_info()
            
            info_msg = f"""INFORMACIÓN DEL SISTEMA:

Empresa: {company_info['name']}
Eslogan: {company_info['tagline']}
Versión: {company_info['version']}

LOGOS DISPONIBLES: {len(brand_manager.logos)}
ICONOS CARGADOS: {len(brand_manager.icons)}

Tu logo está disponible en estos tamaños:
• Original: Para documentos e impresiones
• Grande: Para pantallas principales  
• Mediano: Para ventanas normales
• Pequeño: Para barras de herramientas
• Icono: Para la barra de tareas

¡Todo automático y profesional!"""
            
            messagebox.showinfo("Información del Sistema", info_msg)
        
        info_btn = tk.Button(
            button_frame,
            text="Ver Información",
            command=show_info,
            font=("Arial", 12, "bold"),
            padx=20,
            pady=10
        )
        brand_manager.apply_theme_to_widget(info_btn, "button")
        info_btn.pack(side="left", padx=15)
        
        # Botón principal
        main_btn = tk.Button(
            button_frame,
            text="¡PERFECTO! Se ve genial",
            command=window.destroy,
            font=("Arial", 14, "bold"),
            padx=30,
            pady=15
        )
        brand_manager.apply_theme_to_widget(main_btn, "button")
        main_btn.pack(side="left", padx=15)
        
        # Status bar
        status = brand_manager.create_status_bar(
            window, 
            "Tu sistema personalizado - Logo cargado correctamente"
        )
        
        # Centrar ventana
        window.update_idletasks()
        x = (window.winfo_screenwidth() // 2) - (500)
        y = (window.winfo_screenheight() // 2) - (350)
        window.geometry(f"1000x700+{x}+{y}")
        
        print("VENTANA ABIERTA - Mira qué profesional se ve tu logo!")
        print("Tu logo de", logo_original.size[0], "x", logo_original.size[1], "píxeles se ve perfecto")
        print()
        
        window.mainloop()
        
        print("¡Excelente! Tu logo le da un toque muy profesional al sistema")
        return True
        
    except Exception as e:
        print(f"Error mostrando demo: {e}")
        print("Verifica que tengas tu logo.png en la carpeta assets/")
        return False

def main():
    """Función principal"""
    print()
    print("=" * 60)
    print("      SISTEMA POS CON TU LOGO PERSONALIZADO")
    print("=" * 60)
    print()
    print("Este launcher te muestra cómo se ve tu sistema")
    print("con tu logo real integrado.")
    print()
    print("Tu logo que te costó trabajo crear ahora está")
    print("completamente integrado en el sistema POS!")
    print()
    print("¿Quieres ver cómo se ve?")
    print()
    print("1. Ver demo con mi logo")
    print("2. Salir")
    print()
    
    choice = input("Selecciona opción (1-2): ").strip()
    
    if choice == "1":
        print()
        print("Iniciando demo con tu logo...")
        if show_logo_demo():
            print("Demo completada exitosamente!")
        else:
            print("Hubo un problema con la demo")
            input("Presiona Enter para continuar...")
    
    elif choice == "2":
        print("¡Hasta luego!")
    
    else:
        print("Opción no válida")
        time.sleep(2)
        main()

if __name__ == "__main__":
    main()
