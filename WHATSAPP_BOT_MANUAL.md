# 📱 Bot de WhatsApp con IA - CajaCentral POS

## 🚀 ¿Qué es?

El Bot de WhatsApp integra tu **asistente de IA existente** con WhatsApp Web para brindar **atención automatizada 24/7** a tus clientes a través de mensajería instantánea.

## ✨ Características Principales

### 🤖 Inteligencia Artificial Integrada
- **Usa tu AI Assistant actual** (ChatterBot, Transformers, Llama)
- **Respuestas contextuales** específicas para tu negocio
- **Aprendizaje continuo** basado en conversaciones
- **Múltiples engines** de IA para diferentes tipos de consultas

### 📱 Funcionalidades WhatsApp
- **Monitoreo automático** de mensajes entrantes
- **Respuestas instantáneas** con IA
- **Horarios configurables** (ej: 8 AM - 8 PM)
- **Mantiene sesión** de WhatsApp Web
- **Interfaz de administración** integrada en el POS

### 🎯 Casos de Uso
- **Consultas sobre productos**: "¿Tienen el producto X en stock?"
- **Información del negocio**: "¿A qué hora abren?"
- **Soporte técnico**: "¿Cómo hago una devolución?"
- **Seguimiento de pedidos**: "¿Mi factura está lista?"

## 🔧 Instalación

### 1. Ejecutar Configurador Automático
```powershell
python setup_whatsapp_bot.py
```

Este script:
- ✅ Verifica que Chrome esté instalado
- ✅ Instala dependencias (selenium, webdriver-manager)
- ✅ Configura carpetas necesarias
- ✅ Prueba tu AI Assistant
- ✅ Crea scripts de inicio

### 2. Instalación Manual (Si Prefieres)
```powershell
# Instalar dependencias
pip install selenium webdriver-manager

# Verificar Chrome instalado
# Descargar desde: https://www.google.com/chrome/
```

## 🎮 Uso

### Opción 1: Desde la Interfaz POS
1. Abrir sistema POS principal
2. Ir a **Ayuda** → **📱 Bot WhatsApp**
3. Hacer clic en **🚀 Iniciar Bot**
4. Escanear código QR en WhatsApp Web
5. ¡Listo! El bot monitoreará automáticamente

### Opción 2: Ejecución Independiente
```powershell
# Opción A: Script directo
python whatsapp_bot_simple.py

# Opción B: Script de inicio
start_whatsapp_bot.bat
```

## ⚙️ Configuración

### Horarios de Atención
- **Por defecto**: 8:00 AM - 8:00 PM
- **Fuera de horario**: Mensaje automático de no disponibilidad
- **Configurable** desde la interfaz

### Respuestas Automáticas
El bot reconoce automáticamente:

#### 👋 Saludos
- **Entrada**: "Hola", "Buenos días", "Hi"
- **Respuesta**: "¡Hola [Nombre]! 👋 Soy el asistente virtual de CajaCentral POS. ¿En qué puedo ayudarte?"

#### 🙏 Despedidas
- **Entrada**: "Gracias", "Chau", "Adiós"
- **Respuesta**: "¡De nada! 😊 Que tengas un excelente día. Estamos aquí cuando nos necesites."

#### 🤖 Consultas con IA
- **Entrada**: Cualquier pregunta sobre el sistema POS
- **Procesamiento**: Tu AI Assistant genera respuesta contextual
- **Respuesta**: Respuesta personalizada con emojis apropiados

## 🧠 Integración con IA

### Engines Soportados
El bot usa automáticamente los engines disponibles en tu sistema:

1. **ChatterBot** (Local, entrenado)
   - Ideal para: Preguntas frecuentes del POS
   - Entrenado con: Datos específicos de tu sistema

2. **Transformers** (Local, QA)
   - Ideal para: Análisis de texto y contexto
   - Modelo: DistilBERT para español

3. **Llama API** (Cloud/Local)
   - Ideal para: Respuestas complejas y detalladas
   - Configurable: Endpoints locales o cloud

4. **Sistema de Reglas** (Fallback)
   - Siempre disponible como respaldo
   - Respuestas básicas pero funcionales

### Selección Automática de Engine
El bot elige inteligentemente qué engine usar:

```python
# Preguntas complejas → Llama
"Explicar paso a paso cómo hacer una venta"

# Preguntas específicas POS → ChatterBot  
"¿Cómo busco un producto?"

# Análisis de contexto → Transformers
"Basado en mi historial, ¿qué me recomiendas?"

# Fallback → Reglas básicas
Cualquier consulta no clasificada
```

## 📊 Monitoreo y Control

### Panel de Administración
- **Estado en tiempo real**: 🟢 Ejecutándose / 🔴 Detenido
- **Log de actividad**: Registro de mensajes procesados
- **Configuración**: Horarios, mensajes automáticos
- **Estadísticas**: Mensajes procesados, clientes atendidos

### Controles Disponibles
- **🚀 Iniciar Bot**: Abre WhatsApp Web y comienza monitoreo
- **🛑 Detener Bot**: Detiene el monitoreo (mantiene Chrome abierto)
- **🔄 Reiniciar**: Reinicia completamente el bot
- **⚙️ Configurar**: Ajustes de horarios y mensajes

## 🛡️ Seguridad y Privacidad

### Datos Locales
- **Sesión WhatsApp**: Se guarda localmente en `./whatsapp_session/`
- **Conversaciones**: Se procesan en tiempo real, no se almacenan por defecto
- **IA Local**: ChatterBot y Transformers funcionan completamente offline

### Configuración Segura
- **Sin tokens expuestos**: No requiere API keys de WhatsApp
- **Conexión directa**: Usa WhatsApp Web oficial
- **Control total**: Tienes acceso completo al código fuente

## 🚨 Solución de Problemas

### Chrome no se abre
```
❌ Error: Chrome no encontrado
✅ Solución: Instalar Google Chrome oficial
```

### Selenium no funciona
```powershell
# Reinstalar dependencias
pip uninstall selenium webdriver-manager
pip install selenium>=4.15.0 webdriver-manager>=4.0.0
```

### WhatsApp no conecta
1. **Verificar**: Que WhatsApp Web funcione manualmente
2. **Limpiar**: Carpeta `whatsapp_session` y volver a escanear QR
3. **Reiniciar**: Chrome completamente

### AI Assistant no responde
```python
# Verificar engines disponibles
from core.ai_assistant import POSAIAssistant
ai = POSAIAssistant()
print(ai.get_engine_status())
```

### Mensajes no se procesan
- **Verificar**: Que el elemento de chat no haya cambiado
- **Actualizar**: Selectores CSS si WhatsApp Web cambió interfaz
- **Tiempo**: Aumentar delays entre acciones

## 🔄 Actualizaciones y Mantenimiento

### Actualizar Bot
```powershell
# Obtener última versión
git pull origin main

# Reinstalar dependencias si es necesario
python setup_whatsapp_bot.py
```

### Monitoreo de Rendimiento
- **Mensajes por hora**: Visible en panel de administración
- **Tiempo de respuesta**: Configurable (por defecto 2 segundos)
- **Uso de memoria**: Chrome consume ~100-200MB

### Respaldo de Configuración
```python
# Las configuraciones se guardan en:
# - whatsapp_session/ (sesión WhatsApp)
# - Configuración del AI Assistant en core/
```

## 🎯 Casos de Uso Avanzados

### 1. Soporte 24/7
```
Cliente (3 AM): "¿Están abiertos?"
Bot: "🕐 Estamos fuera del horario de atención (8:00 AM - 8:00 PM). 
      Te responderemos en cuanto abramos. ¡Gracias!"
```

### 2. Consultas de Productos
```
Cliente: "¿Tienen arroz disponible?"
Bot: "📦 Consultando inventario... Sí, tenemos arroz de 1kg 
      disponible a ₡1.200. ¿Te interesa?"
```

### 3. Soporte Técnico
```
Cliente: "No puedo hacer una venta"
Bot: "🔧 Para realizar una venta: 1) Busca el producto con F2, 
      2) Agrega cantidad, 3) Presiona F3 para cobrar. 
      ¿En qué paso tienes dificultad?"
```

### 4. Información de Negocio
```
Cliente: "¿Cuáles son sus horarios?"
Bot: "🕐 Nuestro horario de atención es de 8:00 AM a 8:00 PM, 
      de lunes a sábado. ¡Te esperamos!"
```

## 🔮 Próximas Funcionalidades

### En Desarrollo
- [ ] **Integración con Base de Datos**: Consultas en tiempo real de inventario
- [ ] **Mensajes Multimedia**: Envío de imágenes de productos
- [ ] **Webhooks**: Notificaciones para ordenes importantes
- [ ] **Multi-idioma**: Soporte para inglés y otros idiomas
- [ ] **Analytics Avanzados**: Dashboard de métricas de atención

### Roadmap
- [ ] **WhatsApp Business API**: Migración a API oficial
- [ ] **Telegram Bot**: Soporte para múltiples plataformas
- [ ] **Voice Messages**: Respuestas por audio
- [ ] **Integración CRM**: Vinculación con sistemas de clientes

## 📞 Soporte

### Documentación
- **Manual Principal**: `ASISTENTE_IA_MANUAL.md`
- **Setup Guide**: `setup_whatsapp_bot.py --help`
- **Ejemplos**: Ver carpeta `examples/`

### Contacto
- **Issues**: GitHub Issues para reportar bugs
- **Mejoras**: Pull requests son bienvenidos
- **Soporte**: Documentación incluida en el sistema

---

**💡 Recuerda**: El bot es una extensión de tu AI Assistant existente. Mientras mejor entrenes tu asistente de IA, mejores serán las respuestas automáticas en WhatsApp.

**🚀 ¡Disfruta de la atención automatizada 24/7 para tu negocio!**
