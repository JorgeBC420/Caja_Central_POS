from escpos.printer import Usb

def imprimir_ticket(datos_venta_finalizada, usuario_actual, config_tienda=None):
    try:
        p = Usb(0x04b8, 0x0e15, 0)  # Cambia por tu impresora

        # --- Encabezado Personalizable ---
        p.set(align='center', text_type='B')
        if config_tienda:
            p.text(f"{config_tienda.nombre}\n")
            if config_tienda.direccion:
                p.text(f"{config_tienda.direccion}\n")
            if config_tienda.telefono:
                p.text(f"Tel: {config_tienda.telefono}\n")
            if config_tienda.cedula_juridica:
                p.text(f"Cédula Jurídica: {config_tienda.cedula_juridica}\n")
            if config_tienda.resolucion_hacienda:
                p.text(f"Resolución MH: {config_tienda.resolucion_hacienda}\n")
        else:
            p.text("CajaCentralPOS\nSucursal Centro\nTel: 2222-2222\n")
        p.text("\n")
        p.set(align='left', text_type='A')
        p.text(f"Fecha: {datos_venta_finalizada['fecha']}\n")
        p.text(f"Cajero: {usuario_actual.nombre}\n")
        p.text("------------------------------------------------\n")

        # --- Detalle de productos ---
        for item in datos_venta_finalizada['items_vendidos']:
            nombre = item['producto'].nombre[:20]
            cantidad = item['cantidad']
            subtotal = item['subtotal']
            linea = f"{cantidad}x {nombre:<20} ₡{subtotal:>8.2f}\n"
            p.text(linea)

        p.text("------------------------------------------------\n")
        totales = datos_venta_finalizada['totales_calculados']
        p.set(align='right')
        p.text(f"Subtotal: ₡{totales['subtotal_base_items']:.2f}\n")
        p.text(f"IVA: ₡{totales['total_iva_items']:.2f}\n")
        p.set(text_type='B')
        p.text(f"TOTAL: ₡{totales['gran_total_venta']:.2f}\n")
        p.set(text_type='A')

        # --- Métodos de pago ---
        if 'pagos' in datos_venta_finalizada and datos_venta_finalizada['pagos']:
            p.text("\nFormas de pago:\n")
            for pago in datos_venta_finalizada['pagos']:
                metodo = pago.get('method', 'Método')
                monto = pago.get('amount', 0)
                referencia = pago.get('reference', '')
                linea_pago = f"  {metodo}: ₡{monto:.2f}"
                if referencia:
                    linea_pago += f" (Ref: {referencia})"
                p.text(linea_pago + "\n")

        p.text("\n¡Gracias por su compra!\n\n")

        p.cut()
        p.cashdraw(2)
    except Exception as e:
        raise RuntimeError(f"No se pudo imprimir el ticket: {e}")