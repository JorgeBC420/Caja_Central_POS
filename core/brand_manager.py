"""
Gestor de Assets y Branding para CajaCentral POS
Maneja logos, iconos y elementos visuales del sistema
"""

import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import base64
from typing import Dict, Optional, Tuple, Any

class BrandManager:
    """Gestor de marca y assets visuales"""
    
    def __init__(self, assets_path: str = "assets"):
        self.assets_path = assets_path
        self.logos = {}
        self.icons = {}
        self.images = {}
        
        # Configuración de marca
        self.brand_config = {
            "company_name": "CajaCentral POS",
            "tagline": "Sistema de Punto de Venta Profesional",
            "primary_color": "#2E3440",
            "secondary_color": "#5E81AC", 
            "accent_color": "#88C0D0",
            "success_color": "#A3BE8C",
            "warning_color": "#EBCB8B",
            "error_color": "#BF616A",
            "text_color": "#ECEFF4",
            "background_color": "#3B4252"
        }
        
        self._load_assets()
    
    def _load_assets(self):
        """Carga todos los assets disponibles"""
        if not os.path.exists(self.assets_path):
            os.makedirs(self.assets_path, exist_ok=True)
            print(f"📁 Creada carpeta de assets: {self.assets_path}")
            return
        
        # Cargar logo principal
        logo_path = os.path.join(self.assets_path, "logo.png")
        if os.path.exists(logo_path):
            try:
                # Cargar en diferentes tamaños
                original_logo = Image.open(logo_path)
                
                self.logos["original"] = original_logo
                self.logos["large"] = original_logo.resize((200, 100), Image.Resampling.LANCZOS)
                self.logos["medium"] = original_logo.resize((120, 60), Image.Resampling.LANCZOS)
                self.logos["small"] = original_logo.resize((80, 40), Image.Resampling.LANCZOS)
                self.logos["icon"] = original_logo.resize((32, 32), Image.Resampling.LANCZOS)
                
                print(f"✅ Logo cargado: {logo_path}")
                print(f"📐 Tamaño original: {original_logo.size}")
                
            except Exception as e:
                print(f"❌ Error cargando logo: {e}")
                self._create_fallback_logo()
        else:
            print(f"⚠️ Logo no encontrado en: {logo_path}")
            self._create_fallback_logo()
        
        # Cargar iconos adicionales
        self._load_icons()
    
    def _create_fallback_logo(self):
        """Crea un logo de respaldo si no se encuentra el original"""
        print("🎨 Creando logo de respaldo...")
        
        # Crear un logo simple con texto
        sizes = [(200, 100), (120, 60), (80, 40), (32, 32)]
        size_names = ["large", "medium", "small", "icon"]
        
        for size, name in zip(sizes, size_names):
            img = Image.new('RGBA', size, (46, 52, 64, 255))  # Color de fondo
            self.logos[name] = img
        
        # El original es el más grande
        self.logos["original"] = self.logos["large"]
    
    def _load_icons(self):
        """Carga iconos adicionales"""
        icon_files = [
            "barcode_icon.png",
            "sale_icon.png",
            "product_icon.png",
            "report_icon.png",
            "settings_icon.png"
        ]
        
        for icon_file in icon_files:
            icon_path = os.path.join(self.assets_path, icon_file)
            if os.path.exists(icon_path):
                try:
                    icon = Image.open(icon_path)
                    icon_name = icon_file.replace("_icon.png", "").replace(".png", "")
                    self.icons[icon_name] = icon.resize((24, 24), Image.Resampling.LANCZOS)
                    print(f"✅ Icono cargado: {icon_name}")
                except Exception as e:
                    print(f"❌ Error cargando icono {icon_file}: {e}")
    
    def get_logo(self, size: str = "medium") -> Optional[Image.Image]:
        """
        Obtiene el logo en el tamaño especificado
        
        Args:
            size: "original", "large", "medium", "small", "icon"
        """
        return self.logos.get(size)
    
    def get_logo_tk(self, size: str = "medium") -> Optional[ImageTk.PhotoImage]:
        """Obtiene el logo como PhotoImage para Tkinter"""
        logo = self.get_logo(size)
        if logo:
            try:
                return ImageTk.PhotoImage(logo)
            except Exception as e:
                print(f"❌ Error convirtiendo logo a PhotoImage: {e}")
        return None
    
    def get_icon(self, name: str) -> Optional[Image.Image]:
        """Obtiene un icono por nombre"""
        return self.icons.get(name)
    
    def get_icon_tk(self, name: str) -> Optional[ImageTk.PhotoImage]:
        """Obtiene un icono como PhotoImage para Tkinter"""
        icon = self.get_icon(name)
        if icon:
            try:
                return ImageTk.PhotoImage(icon)
            except Exception as e:
                print(f"❌ Error convirtiendo icono a PhotoImage: {e}")
        return None
    
    def get_brand_colors(self) -> Dict[str, str]:
        """Obtiene los colores de la marca"""
        return self.brand_config.copy()
    
    def apply_theme_to_widget(self, widget, widget_type: str = "frame"):
        """Aplica el tema de la marca a un widget de Tkinter"""
        colors = self.get_brand_colors()
        
        try:
            if widget_type == "frame":
                widget.configure(bg=colors["background_color"])
            
            elif widget_type == "label":
                widget.configure(
                    bg=colors["background_color"],
                    fg=colors["text_color"],
                    font=("Arial", 10)
                )
            
            elif widget_type == "button":
                widget.configure(
                    bg=colors["secondary_color"],
                    fg=colors["text_color"],
                    activebackground=colors["accent_color"],
                    activeforeground=colors["text_color"],
                    relief="flat",
                    font=("Arial", 10, "bold")
                )
            
            elif widget_type == "entry":
                widget.configure(
                    bg=colors["text_color"],
                    fg=colors["primary_color"],
                    insertbackground=colors["primary_color"],
                    relief="flat"
                )
                
            elif widget_type == "text":
                widget.configure(
                    bg=colors["text_color"],
                    fg=colors["primary_color"],
                    insertbackground=colors["primary_color"],
                    selectbackground=colors["accent_color"]
                )
        
        except Exception as e:
            print(f"⚠️ Error aplicando tema a widget: {e}")
    
    def create_branded_window(self, title: str, size: Tuple[int, int] = (800, 600)) -> tk.Tk:
        """Crea una ventana con el branding aplicado"""
        window = tk.Tk()
        window.title(f"{self.brand_config['company_name']} - {title}")
        window.geometry(f"{size[0]}x{size[1]}")
        
        # Aplicar colores
        colors = self.get_brand_colors()
        window.configure(bg=colors["background_color"])
        
        # Configurar icono de ventana si está disponible
        icon_logo = self.get_logo_tk("icon")
        if icon_logo:
            try:
                window.iconphoto(True, icon_logo)
            except:
                pass
        
        return window
    
    def create_header_frame(self, parent, show_logo: bool = True, show_title: bool = True) -> tk.Frame:
        """Crea un frame de cabecera con logo y título"""
        colors = self.get_brand_colors()
        
        header_frame = tk.Frame(parent, bg=colors["primary_color"], height=80)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        if show_logo:
            # Logo
            logo_tk = self.get_logo_tk("medium")
            if logo_tk:
                logo_label = tk.Label(
                    header_frame, 
                    image=logo_tk, 
                    bg=colors["primary_color"]
                )
                logo_label.image = logo_tk  # Mantener referencia
                logo_label.pack(side="left", padx=20, pady=10)
        
        if show_title:
            # Información de la empresa
            info_frame = tk.Frame(header_frame, bg=colors["primary_color"])
            info_frame.pack(side="left", fill="both", expand=True, padx=20, pady=10)
            
            company_label = tk.Label(
                info_frame,
                text=self.brand_config["company_name"],
                bg=colors["primary_color"],
                fg=colors["text_color"],
                font=("Arial", 16, "bold")
            )
            company_label.pack(anchor="w")
            
            tagline_label = tk.Label(
                info_frame,
                text=self.brand_config["tagline"],
                bg=colors["primary_color"],
                fg=colors["accent_color"],
                font=("Arial", 10)
            )
            tagline_label.pack(anchor="w")
        
        return header_frame
    
    def create_status_bar(self, parent, initial_text: str = "Listo") -> tk.Label:
        """Crea una barra de estado con estilo"""
        colors = self.get_brand_colors()
        
        status_bar = tk.Label(
            parent,
            text=initial_text,
            bg=colors["primary_color"],
            fg=colors["text_color"],
            font=("Arial", 9),
            anchor="w",
            padx=10,
            pady=5
        )
        status_bar.pack(side="bottom", fill="x")
        
        return status_bar
    
    def get_company_info(self) -> Dict[str, str]:
        """Obtiene información de la empresa"""
        return {
            "name": self.brand_config["company_name"],
            "tagline": self.brand_config["tagline"],
            "version": "3.0",
            "author": "CajaCentral Team",
            "description": "Sistema completo de punto de venta con IA integrada"
        }
    
    def save_brand_config(self, config_path: str = "config/brand.json"):
        """Guarda la configuración de marca"""
        import json
        
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.brand_config, f, indent=2, ensure_ascii=False)
            print(f"✅ Configuración de marca guardada: {config_path}")
        except Exception as e:
            print(f"❌ Error guardando configuración: {e}")
    
    def load_brand_config(self, config_path: str = "config/brand.json"):
        """Carga la configuración de marca"""
        import json
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.brand_config.update(loaded_config)
                print(f"✅ Configuración de marca cargada: {config_path}")
            except Exception as e:
                print(f"❌ Error cargando configuración: {e}")

# Instancia global del gestor de marca
_brand_manager = None

def get_brand_manager() -> BrandManager:
    """Obtiene la instancia global del gestor de marca"""
    global _brand_manager
    if _brand_manager is None:
        _brand_manager = BrandManager()
    return _brand_manager

def test_brand_system():
    """Función de prueba para el sistema de branding"""
    print("🎨 Probando sistema de branding...")
    
    brand_manager = get_brand_manager()
    
    # Mostrar información de assets
    print(f"📋 Logos disponibles: {list(brand_manager.logos.keys())}")
    print(f"🎯 Iconos disponibles: {list(brand_manager.icons.keys())}")
    
    # Mostrar información de la empresa
    company_info = brand_manager.get_company_info()
    print(f"🏢 Empresa: {company_info['name']}")
    print(f"📝 Eslogan: {company_info['tagline']}")
    
    # Probar ventana de ejemplo
    try:
        window = brand_manager.create_branded_window("Prueba de Branding", (600, 400))
        
        # Crear header
        header = brand_manager.create_header_frame(window)
        
        # Contenido de ejemplo
        content_frame = tk.Frame(window)
        brand_manager.apply_theme_to_widget(content_frame, "frame")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        welcome_label = tk.Label(
            content_frame,
            text="¡Bienvenido a tu sistema POS personalizado!",
            font=("Arial", 14, "bold")
        )
        brand_manager.apply_theme_to_widget(welcome_label, "label")
        welcome_label.pack(pady=20)
        
        info_label = tk.Label(
            content_frame,
            text="Tu logo real está integrado en todo el sistema.\nSe ve profesional y representa tu marca correctamente.",
            font=("Arial", 11),
            justify="center"
        )
        brand_manager.apply_theme_to_widget(info_label, "label")
        info_label.pack(pady=10)
        
        # Botón de prueba
        test_button = tk.Button(
            content_frame,
            text="¡Perfecto! Mi logo se ve genial",
            command=window.destroy,
            padx=20,
            pady=10
        )
        brand_manager.apply_theme_to_widget(test_button, "button")
        test_button.pack(pady=20)
        
        # Status bar
        status = brand_manager.create_status_bar(window, "Sistema de branding funcionando correctamente")
        
        print("✅ Ventana de prueba creada. Ciérrala para continuar.")
        window.mainloop()
        
    except Exception as e:
        print(f"❌ Error en prueba de ventana: {e}")
    
    print("🎨 Prueba de branding completada")
    return True

if __name__ == "__main__":
    test_brand_system()
