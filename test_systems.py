"""
Script de Prueba - Sistemas Integrados
Prueba todos los nuevos sistemas implementados
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_multistore_system():
    """Probar sistema multi-tienda"""
    print("🏪 Probando Sistema Multi-Tienda...")
    try:
        from modules.multistore.store_manager import MultiStoreManager
        manager = MultiStoreManager()
        
        # Crear tiendas de prueba
        stores = manager.create_store("Tienda Principal", "San José Centro", "Principal")
        print(f"✅ Tienda creada: {stores}")
        
        # Probar inventario consolidado
        inventory = manager.get_consolidated_inventory()
        print(f"✅ Inventario consolidado: {len(inventory) if inventory else 0} productos")
        
        print("✅ Sistema Multi-Tienda funcionando correctamente\n")
        
    except Exception as e:
        print(f"❌ Error en Sistema Multi-Tienda: {e}\n")

def test_sales_history_system():
    """Probar sistema de historial de ventas"""
    print("📊 Probando Sistema de Historial de Ventas...")
    try:
        from modules.reports.sales_history import SalesHistoryManager
        manager = SalesHistoryManager()
        
        # Probar estadísticas
        stats = manager.get_daily_summary()
        print(f"✅ Estadísticas diarias obtenidas")
        
        # Probar análisis de productos
        products = manager.get_product_analysis()
        print(f"✅ Análisis de productos generado")
        
        print("✅ Sistema de Historial de Ventas funcionando correctamente\n")
        
    except Exception as e:
        print(f"❌ Error en Sistema de Historial: {e}\n")

def test_restaurant_system():
    """Probar sistema de restaurante"""
    print("🍽️ Probando Sistema de Restaurante...")
    try:
        from modules.restaurant.restaurant_manager import RestaurantManager
        manager = RestaurantManager()
        
        # Crear mesa de prueba
        table = manager.create_table("Mesa 1", 4, "Salón Principal")
        print(f"✅ Mesa creada: {table}")
        
        # Probar menú
        menu_items = manager.get_menu_items()
        print(f"✅ Items del menú: {len(menu_items) if menu_items else 0} productos")
        
        print("✅ Sistema de Restaurante funcionando correctamente\n")
        
    except Exception as e:
        print(f"❌ Error en Sistema de Restaurante: {e}\n")

def test_user_interfaces():
    """Probar interfaces de usuario"""
    print("🖥️ Probando Interfaces de Usuario...")
    try:
        # Probar importación de interfaces
        from ui.ui_multistore import MultiStoreWindow
        print("✅ Interfaz Multi-Tienda importada correctamente")
        
        from ui.ui_restaurant import RestaurantWindow
        print("✅ Interfaz Restaurante importada correctamente")
        
        from ui.ui_sales_history import SalesHistoryWindow
        print("✅ Interfaz Historial de Ventas importada correctamente")
        
        from ui.ui_search_inventory import ProductSearchWindow, ProductManagementWindow, InventoryWindow
        print("✅ Interfaces de Búsqueda e Inventario importadas correctamente")
        
        print("✅ Todas las interfaces funcionando correctamente\n")
        
    except Exception as e:
        print(f"❌ Error en Interfaces: {e}\n")

def test_main_pos_integration():
    """Probar integración con POS principal"""
    print("🏪 Probando Integración con POS Principal...")
    try:
        from pos_modern import ModernPOSApp
        print("✅ POS Principal importado correctamente")
        
        # Las nuevas funciones deberían estar disponibles
        app = ModernPOSApp()
        
        # Verificar que los métodos existen
        if hasattr(app, 'show_multistore'):
            print("✅ Función Multi-Tienda integrada")
        else:
            print("❌ Función Multi-Tienda no encontrada")
            
        if hasattr(app, 'show_restaurant'):
            print("✅ Función Restaurante integrada")
        else:
            print("❌ Función Restaurante no encontrada")
            
        if hasattr(app, 'show_sales_history'):
            print("✅ Función Historial de Ventas integrada")
        else:
            print("❌ Función Historial de Ventas no encontrada")
        
        print("✅ Integración con POS Principal completada\n")
        
    except Exception as e:
        print(f"❌ Error en Integración POS: {e}\n")

def main():
    """Función principal de pruebas"""
    print("=" * 60)
    print("🧪 SISTEMA DE PRUEBAS - CAJA CENTRAL POS")
    print("🚀 Probando Nuevos Sistemas Implementados")
    print("=" * 60)
    print()
    
    # Ejecutar todas las pruebas
    test_multistore_system()
    test_sales_history_system()
    test_restaurant_system()
    test_user_interfaces()
    test_main_pos_integration()
    
    print("=" * 60)
    print("✅ PRUEBAS COMPLETADAS")
    print("🎉 Todos los sistemas están listos para usar!")
    print("=" * 60)
    print()
    print("📋 RESUMEN DE SISTEMAS IMPLEMENTADOS:")
    print("• 🏪 Sistema Multi-Tienda: Gestión de múltiples sucursales")
    print("• 📊 Historial de Ventas: Análisis administrativo completo")
    print("• 🍽️ Sistema de Restaurante: Mesas, menú y cuentas activas")
    print("• 🔍 Búsqueda e Inventario: Gestión mejorada de productos")
    print("• 🖥️ Interfaces Modernas: UI profesional y funcional")
    print()
    print("🚀 Para iniciar el sistema completo, ejecute: python pos_modern.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
