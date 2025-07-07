import tkinter as tk
from tkinter import ttk
from core.calculadora_caja import CalculadoraCaja

class SaleTab(ttk.Frame):
    def __init__(self, parent, system):
        super().__init__(parent)
        self.system = system
        self._setup_ui()
    
    def _setup_ui(self):
        # Interfaz de venta
        pass

class PaymentWindow(tk.Toplevel):
    def __init__(self, parent, amount, system):
        super().__init__(parent)
        self.amount = amount
        self.system = system
        self._setup_ui()
    
    def _setup_ui(self):
        # Interfaz de pago
        pass