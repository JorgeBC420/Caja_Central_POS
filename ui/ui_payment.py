from tkinter import messagebox
from ui.ui_payment import PaymentWindow

def finalizar_venta_ui(self, event=None):
    # 1. Validar que haya productos en la venta
    if not self.sistema.venta_actual['items']:
        messagebox.showwarning("Sin productos", "Agrega productos antes de finalizar la venta.", parent=self)
        return

    # 2. Calcular el total y abrir la ventana de pagos
    total = self.sistema.calcular_total_venta_actual()
    win = PaymentWindow(self, total, self.sistema.payment_processor, self.sistema.currency_manager)
    self.wait_window(win)

    # 3. Procesar los pagos si existen
    if not hasattr(win, "result") or not win.result:
        messagebox.showwarning("Sin pagos", "No se registraron pagos para esta venta.", parent=self)
        return

    pagos = win.result
    # Aquí puedes procesar los pagos con tu MultiPaymentHandler si lo deseas
    # self.sistema.multi_payment_handler.process_mixed_payment(pagos)

    # 4. Generar los datos de la venta finalizada
    datos_venta_finalizada = self.sistema.generar_datos_venta_finalizada()

    # 5. Imprimir el ticket físico
    self.imprimir_ticket_fisico(datos_venta_finalizada)

    # 6. Guardar la venta en la base de datos (si aplica)
    self.sistema.guardar_venta(datos_venta_finalizada)

    # 7. Limpiar la venta actual y actualizar la UI
    self.sistema.nueva_venta()
    self.actualizar_treeview_productos_tabla()
    self.actualizar_info_venta_ui()

    # 8. Notificar al usuario
    messagebox.showinfo("Venta finalizada", "La venta se completó y el ticket fue impreso.", parent=self)