import tkinter as tk
from tkinter import messagebox
from controllers import registro_controller

def registrar():
    descripcion = descripcion_entry.get()
    monto = float(monto_entry.get())
    tipo = tipo_var.get()
    registro_controller.registrar_ingreso(descripcion, monto, tipo)
    messagebox.showinfo("Éxito", "Registro guardado")

root = tk.Tk()
root.title("Caja Registradora")

tk.Label(root, text="Descripción").grid(row=0)
tk.Label(root, text="Monto").grid(row=1)

descripcion_entry = tk.Entry(root)
monto_entry = tk.Entry(root)
descripcion_entry.grid(row=0, column=1)
monto_entry.grid(row=1, column=1)

tipo_var = tk.StringVar(value="Ingreso")
tk.OptionMenu(root, tipo_var, "Ingreso", "Gasto").grid(row=2, column=1)

tk.Button(root, text="Registrar", command=registrar).grid(row=3, columnspan=2)

root.mainloop()