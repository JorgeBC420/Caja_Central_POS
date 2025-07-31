import tkinter as tk
from tkinter import ttk, messagebox

class PaymentWindow(tk.Toplevel):
    def __init__(self, parent, total_a_pagar, payment_processor, currency_manager):
        super().__init__(parent)
        self.title("Procesar Pago")
        self.total_a_pagar = total_a_pagar
        self.payment_processor = payment_processor
        self.currency_manager = currency_manager
        self.payments = []

        self.geometry("420x480")
        self.resizable(False, False)

        ttk.Label(self, text=f"Total a pagar: ₡{self.total_a_pagar:.2f}", font=("Arial", 14, "bold")).pack(pady=10)

        self.method_var = tk.StringVar()
        self.amount_var = tk.DoubleVar()
        self.reference_var = tk.StringVar()

        methods = [(k, v['name']) for k, v in self.payment_processor.available_methods.items()]
        ttk.Label(self, text="Método de pago:").pack()
        self.method_combo = ttk.Combobox(self, values=[m[1] for m in methods], state="readonly", textvariable=self.method_var)
        self.method_combo.pack(pady=2)
        self.method_combo.current(0)

        ttk.Label(self, text="Monto:").pack()
        ttk.Entry(self, textvariable=self.amount_var).pack(pady=2)

        ttk.Label(self, text="Referencia (opcional):").pack()
        ttk.Entry(self, textvariable=self.reference_var).pack(pady=2)

        ttk.Button(self, text="Agregar pago", command=self.agregar_pago).pack(pady=5)

        self.tree = ttk.Treeview(self, columns=("Método", "Monto", "Referencia"), show="headings", height=6)
        for col in ("Método", "Monto", "Referencia"):
            self.tree.heading(col, text=col)
        self.tree.pack(pady=10, fill=tk.X, expand=True)

        ttk.Button(self, text="Eliminar pago seleccionado", command=self.eliminar_pago).pack(pady=2)

        self.label_pagado = ttk.Label(self, text=f"Pagado: ₡0.00", font=("Arial", 12))
        self.label_pagado.pack()
        self.label_restante = ttk.Label(self, text=f"Restante: ₡{self.total_a_pagar:.2f}", font=("Arial", 12))
        self.label_restante.pack(pady=5)

        ttk.Button(self, text="Finalizar pago", command=self.finalizar_pago).pack(pady=10)

    def agregar_pago(self):
        metodo = self.method_var.get()
        monto = self.amount_var.get()
        referencia = self.reference_var.get()
        if monto <= 0:
            messagebox.showwarning("Monto inválido", "Ingrese un monto mayor a cero.", parent=self)
            return
        if monto > self.restante():
            messagebox.showwarning("Exceso", "El monto excede el restante.", parent=self)
            return
        self.payments.append({
            "method": metodo,
            "amount": monto,
            "reference": referencia
        })
        self.tree.insert("", "end", values=(metodo, f"₡{monto:.2f}", referencia))
        self.actualizar_labels()
        self.amount_var.set(0)
        self.reference_var.set("")

    def eliminar_pago(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = self.tree.index(selected[0])
        self.tree.delete(selected[0])
        del self.payments[idx]
        self.actualizar_labels()

    def pagado(self):
        return sum(p["amount"] for p in self.payments)

    def restante(self):
        return self.total_a_pagar - self.pagado()

    def actualizar_labels(self):
        self.label_pagado.config(text=f"Pagado: ₡{self.pagado():.2f}")
        self.label_restante.config(text=f"Restante: ₡{self.restante():.2f}")

    def finalizar_pago(self):
        if self.restante() > 0:
            messagebox.showwarning("Pago incompleto", "Aún falta por pagar.", parent=self)
            return
        self.result = self.payments
        self.destroy()