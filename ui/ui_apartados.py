import tkinter as tk
from tkinter import messagebox

class InterfazLogin(tk.Toplevel):
    def __init__(self, master, callback_login, sistema_caja):
        super().__init__(master)
        self.title("Iniciar sesión")
        self.geometry("300x180")
        self.callback_login = callback_login
        self.sistema_caja = sistema_caja

        tk.Label(self, text="Usuario:").pack(pady=5)
        self.entry_usuario = tk.Entry(self)
        self.entry_usuario.pack()

        tk.Label(self, text="Contraseña:").pack(pady=5)
        self.entry_password = tk.Entry(self, show="*")
        self.entry_password.pack()

        tk.Button(self, text="Ingresar", command=self.intentar_login).pack(pady=15)

    def intentar_login(self):
        usuario = self.entry_usuario.get()
        password = self.entry_password.get()
        # Aquí deberías validar contra tu base de datos
        if usuario == "admin" and password == "admin":
            self.callback_login()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")