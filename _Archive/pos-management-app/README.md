# CAJA POS CR

## Overview
CAJA POS CR es un sistema de punto de venta modular de lenguaje Python, con gestión de inventario, ventas, usuarios, auditoría, facturación electrónica y notificaciones.

## Features
- **Respaldo y restauración de base de datos**
- **Auditoría de movimientos**
- **Parámetros de facturación**
- **Gestión avanzada de roles y permisos** (admin, subadmin, cajero, vendedor)
- **Configuración de correo para notificaciones**
- **Facturación electrónica y multi-pago**
- **Gestión de inventario y reportes**

## Project Structure
```
CAJA_POS_CR/
├── .venv/
├── .vscode/
├── assets/
│   ├── barcode_icon.png
│   └── logo.png
├── controllers/
│   └── registro_controller.py
├── core/
│   ├── app_controller.py
│   ├── calculadora_caja.py
│   ├── config.py
│   ├── database.py
│   ├── licencia.py
│   ├── models.py
│   ├── printer_utils.py
│   └── sistema.py
├── models/
│   └── registro.py
├── pos-management-app/
│   └── README.md
├── schemas/
│   └── registro.py
├── services/
│   ├── db.py
│   └── registro.py
├── ui/
│   ├── main_tkinter.py
│   ├── ui_apartados.py
│   ├── ui_clients.py
│   ├── ui_inventory.py
│   ├── ui_lector_barras.py
│   ├── ui_login.py
│   ├── ui_main.py
│   ├── ui_payment.py
│   ├── ui_reports.py
│   ├── ui_sale.py
│   └── ui_users.py
├── app.py
├── main.py
├── requirements.txt
└── caja_registradora_pos_cr.db
```

## Installation
1. Clona el repositorio:
   ```
   git clone <repository-url>
   ```
2. Ve al directorio del proyecto:
   ```
   cd CAJA_POS_CR
   ```
3. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

## Usage
Para ejecutar la aplicación:
```
python main.py
```

## Contributing
Contribuciones son bienvenidas. Por favor, abre un pull request o un issue para mejoras o corrección de errores. Contacto: jorgebravo92@gmail.com

## License
Todos los derechos reservados. Este software es propietario y no puede ser copiado, distribuido ni utilizado sin permiso expreso del autor.