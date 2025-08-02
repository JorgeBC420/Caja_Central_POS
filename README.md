# 🏪 Caja Central POS - Sistema Integral de Punto de Venta

## 📋 Descripción
Sistema POS completo desarrollado en Python para pequeñas y medianas empresas en Costa Rica. Incluye facturación electrónica, gestión multi-tienda, sistema de restaurante y asistente de IA integrado.

## 🚀 Últimas Actualizaciones - Agosto 2025

### ✨ Nuevas Características
- **🎨 Interfaz Visual Mejorada**: Nuevos esquemas de color azul rey y verde turquesa
- **🤖 Asistente IA Híbrido**: Integración con múltiples engines de IA (Ollama, ChatterBot, Transformers)
- **📱 UI Optimizada**: Eliminación de problemas de contraste - texto blanco en fondos claros solucionado
- **🔧 Estabilidad Mejorada**: Corrección de errores de sintaxis y optimización de módulos

### 🎨 Esquemas de Color Implementados
- **Azul Rey (#1e3a8a)**: Módulos de configuración y ventas simples
- **Verde Turquesa (#14b8a6)**: Módulo de restaurante
- **Contraste Optimizado**: Texto blanco sobre fondos de colores para máxima legibilidad

## 🏗️ Módulos del Sistema

### 📊 Sistema Principal (POS Moderno)
- Ventas rápidas con código de barras
- Gestión de inventario en tiempo real
- Reportes avanzados y analytics
- Múltiples métodos de pago

### 🍽️ Sistema de Restaurante
- Gestión de mesas y cuentas activas
- Menú interactivo con categorías
- Control de órdenes de cocina
- **NUEVO**: Interfaz verde turquesa optimizada

### ⚙️ Sistema de Configuración
- Configuración multi-tienda
- Gestión de usuarios y roles
- Parámetros de facturación
- **NUEVO**: Interfaz azul rey profesional

### 💰 Sistema de Ventas Simples
- Apertura y cierre de cuentas
- Control básico de transacciones
- **NUEVO**: Footer verde turquesa y fondo azul rey

### 🤖 Asistente de IA
- Múltiples engines: Ollama, ChatterBot, Transformers
- Entrenamiento específico para funciones POS
- Ayuda contextual inteligente
- Base de conocimientos actualizada

## 🧾 Facturación Electrónica Costa Rica
- **XML v4.4** compatible con Hacienda
- Generación automática de PDFs
- Envío automático al Ministerio
- Cumplimiento normativo completo

## 📱 Características Técnicas

### Tecnologías Utilizadas
- **Frontend**: Python Tkinter con TTK styling
- **Backend**: SQLite con gestión avanzada
- **IA**: Ollama, ChatterBot, Transformers
- **Web**: HTML5, CSS3, JavaScript
- **Mobile**: Flask + Bootstrap

### Bases de Datos
- `caja_registradora_pos_cr.db` - Principal
- `multistore_data.db` - Multi-tienda
- `restaurant.db` - Restaurante
- `sales_history.db` - Historial
- `stability.db` - Monitoreo

### Archivos de Configuración
- `config/app.ini` - Configuración principal
- `config/multistore_config.json` - Multi-tienda
- `CREDENCIALES.txt` - APIs y conexiones

## 🚀 Instalación y Uso

### Requisitos
```bash
pip install -r requirements.txt
```

### Dependencias Principales
- `tkinter` - Interfaz gráfica
- `sqlite3` - Base de datos
- `requests` - APIs
- `Pillow` - Imágenes
- `chatterbot` - IA conversacional (opcional)
- `transformers` - IA avanzada (opcional)

### Ejecución
```bash
# Sistema principal
python main.py

# Sistema específico
python main_system.py

# Aplicación web
python web/app.py

# Aplicación móvil
python mobile/app.py
```

## 🎯 Casos de Uso

### 🏪 Tiendas de Conveniencia
- Ventas rápidas con código de barras
- Control de inventario automático
- Reportes de cierre de caja

### 🍽️ Restaurantes y Cafeterías
- Gestión de mesas digitales
- Menú interactivo por categorías
- Control de cuentas activas

### 🏢 Multi-Tienda
- Sincronización entre sucursales
- Transferencias de inventario
- Reportes consolidados

## 📊 Reportes y Analytics

### Disponibles
- ✅ Ventas diarias, semanales, mensuales
- ✅ Productos más vendidos
- ✅ Análisis de cajeros
- ✅ Estado de inventario
- ✅ Métricas de restaurante
- ✅ Análisis multi-tienda

### Formatos de Exportación
- 📊 Excel (.xlsx)
- 📄 PDF con gráficos
- 📋 CSV para análisis
- 🖨️ Impresión directa

## 🔒 Seguridad

### Características
- 🔐 Sistema de roles y permisos
- 🛡️ Encriptación de datos sensibles
- 📝 Auditoría completa de acciones
- 🔄 Respaldos automáticos
- 🌐 Conexiones seguras HTTPS

## 🛠️ Desarrollo y Personalización

### Estructura del Proyecto
```
caja_pos_cr/
├── core/           # Lógica principal
├── ui/             # Interfaces gráficas
├── modules/        # Módulos especializados
├── web/            # Aplicación web
├── mobile/         # Aplicación móvil
├── config/         # Configuraciones
├── data/           # Datos del sistema
└── logs/           # Registros
```

### Personalización
- 🎨 Temas de colores modificables
- 🏷️ Campos personalizados
- 📋 Reportes a medida
- 🔗 Integraciones API
- 🌍 Multi-idioma preparado

## 📞 Soporte

### Documentación
- `ASISTENTE_IA_MANUAL.md` - Guía del asistente IA
- `WHATSAPP_BOT_MANUAL.md` - Bot de WhatsApp
- `DOCKER_IMPLEMENTATION.md` - Despliegue Docker
- `ESTADO_SISTEMA.md` - Estado actual

### Ayuda Integrada
- 🤖 Asistente IA disponible 24/7
- ❓ Ayuda contextual (F9)
- 💡 Tips automáticos
- 📚 Base de conocimientos

## 🌟 Características Destacadas

### ✅ Implementado
- [x] Sistema POS completo
- [x] Facturación electrónica CR
- [x] Multi-tienda sincronizada
- [x] Sistema de restaurante
- [x] Asistente IA híbrido
- [x] **NUEVO**: Interfaz visual optimizada
- [x] **NUEVO**: Esquemas de color profesionales
- [x] Aplicaciones web y móvil
- [x] Reportes avanzados
- [x] Seguridad empresarial

### 🚀 Próximas Mejoras
- [ ] Integración con más pasarelas de pago
- [ ] App móvil nativa (Android/iOS)
- [ ] Dashboard ejecutivo en tiempo real
- [ ] Integración con contabilidad
- [ ] API REST completa

## 📄 Licencia
Desarrollado para el mercado costarricense. Todos los derechos reservados.

## 🇨🇷 Hecho en Costa Rica
Sistema diseñado específicamente para cumplir con la normativa fiscal de Costa Rica y las necesidades de las PyMEs nacionales.

---

**Última actualización**: 1 de Agosto, 2025 - Versión 2.5.0  
**Mejoras**: Interfaz visual optimizada, asistente IA mejorado, estabilidad aumentada
