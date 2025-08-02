@echo off
echo.
echo ========================================
echo 🏪 CAJA CENTRAL POS - INTERFAZ MOVIL
echo ========================================
echo.

cd /d "%~dp0"

echo 📱 Iniciando servidor web móvil...
echo.
echo 💻 Acceso local: http://localhost:5000
echo 📱 Acceso móvil: http://[tu-ip]:5000
echo.
echo 👤 Usuario: admin
echo 🔑 Contraseña: admin123
echo.
echo ⚠️  Para usar desde otro dispositivo:
echo    1. Conecta el móvil a la misma red WiFi
echo    2. Encuentra tu IP con: ipconfig
echo    3. Accede desde: http://[tu-ip]:5000
echo.
echo 🛑 Presiona Ctrl+C para detener el servidor
echo.

python app.py

pause
