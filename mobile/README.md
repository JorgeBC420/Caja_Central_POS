# Caja Central POS - Interfaz Móvil

## 📱 Sistema de Punto de Venta Móvil

Una interfaz web móvil moderna y responsiva para el sistema de punto de venta, optimizada para dispositivos móviles y tablets.

### ✨ Características

- **Diseño Responsivo**: Optimizado para móviles, tablets y desktop
- **PWA (Progressive Web App)**: Instalable como aplicación nativa
- **Interfaz Táctil**: Diseñada para interacción táctil
- **Offline Ready**: Funcionalidad básica sin conexión
- **Tiempo Real**: Actualizaciones en tiempo real
- **Bootstrap 5**: UI moderna y profesional

### 🚀 Inicio Rápido

1. **Ejecutar el servidor móvil:**
   ```bash
   # Desde la carpeta mobile/
   python app.py
   
   # O usar el script batch
   start-mobile.bat
   ```

2. **Acceder desde dispositivos:**
   - **Local**: http://localhost:5000
   - **Móvil**: http://[tu-ip]:5000

3. **Credenciales de prueba:**
   - Usuario: `admin`
   - Contraseña: `admin123`

### 📱 Funcionalidades Móviles

#### 🏪 Dashboard
- Resumen de ventas del día
- Estadísticas en tiempo real
- Productos destacados
- Accesos rápidos

#### 💰 Punto de Venta (POS)
- Búsqueda de productos en tiempo real
- Carrito de compras
- Múltiples métodos de pago
- Confirmación de ventas

#### 📦 Productos
- Catálogo completo
- Búsqueda y filtros
- Información de stock
- Agregar al carrito rápido

#### 📊 Historial de Ventas
- Lista de transacciones
- Filtros por fecha
- Detalles de cada venta
- Impresión de recibos

### 🛠️ Instalación como PWA

1. **En Android (Chrome):**
   - Visita la aplicación en Chrome
   - Toca el menú (3 puntos)
   - Selecciona "Agregar a pantalla de inicio"

2. **En iOS (Safari):**
   - Visita la aplicación en Safari
   - Toca el botón de compartir
   - Selecciona "Agregar a pantalla de inicio"

### 🎨 Personalización

#### Colores y Tema
Edita `static/css/mobile.css` para personalizar:
- Colores primarios
- Esquemas de color
- Animaciones
- Diseño responsivo

#### Iconos PWA
Reemplaza los iconos en `static/icons/` con tu logo:
- Tamaños: 72x72 hasta 512x512 pixels
- Formato PNG recomendado
- Fondo transparente o sólido

### 📡 API Endpoints

- `GET /api/dashboard` - Datos del dashboard
- `GET /api/products` - Lista de productos
- `POST /api/sales` - Procesar venta
- `GET /api/sales` - Historial de ventas
- `GET /api/receipt/<id>` - Imprimir recibo

### 🔧 Configuración de Red

#### Para usar en la red local:

1. **Encontrar tu IP:**
   ```cmd
   ipconfig
   ```

2. **Configurar firewall (Windows):**
   - Permitir Python en el firewall
   - Abrir puerto 5000

3. **Conectar dispositivos:**
   - Conectar móvil/tablet a la misma WiFi
   - Acceder a: `http://[tu-ip]:5000`

### 🔐 Seguridad

- Autenticación de usuarios
- Sesiones seguras
- Validación de datos
- Protección CSRF

### 📱 Compatibilidad

- **Navegadores:** Chrome 80+, Safari 13+, Firefox 75+
- **Sistemas:** Android 7+, iOS 13+
- **Resoluciones:** 320px - 2560px

### 🐛 Solución de Problemas

#### No se conecta desde móvil:
1. Verificar que estén en la misma red
2. Comprobar firewall de Windows
3. Usar IP correcta (no localhost)

#### PWA no se instala:
1. Usar HTTPS (para producción)
2. Verificar manifest.json
3. Comprobar service worker

#### Productos no cargan:
1. Verificar base de datos
2. Comprobar conexión de red
3. Revisar logs del servidor

### 📈 Próximas Características

- [ ] Modo oscuro
- [ ] Sincronización offline
- [ ] Notificaciones push
- [ ] Múltiples idiomas
- [ ] Reportes avanzados
- [ ] Integración con cámara (códigos de barras)

### 🤝 Soporte

Para soporte técnico o consultas:
- Revisar logs en la consola del navegador
- Verificar conexión a la base de datos
- Comprobar configuración de red

---

**Caja Central POS Mobile** - Sistema de punto de venta moderno para Costa Rica 🇨🇷
