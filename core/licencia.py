from tkinter import messagebox

def verificar_licencia(self):
    licencia = self.sistema.config_manager.get_licencia()
    if not licencia or not self.validar_licencia(licencia):
        messagebox.showerror(
            "Licencia requerida",
            "La licencia no es válida o no está presente. Por favor, contacte a soporte para activar su sistema."
        )
        # Intenta cerrar la ventana principal si existe el método destroy
        if hasattr(self, "destroy") and callable(self.destroy):
            self.destroy()
        # Si no es posible cerrar, deshabilita todos los widgets de la UI
        elif hasattr(self, "winfo_children"):
            for widget in self.winfo_children():
                try:
                    widget.configure(state="disabled")
                except Exception:
                    pass