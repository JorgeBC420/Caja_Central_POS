import sqlite3
from tkinter import Toplevel, ttk
from modules.api.database import get_connection

def show_user_history(user):
    conn = get_connection()
    cursor = conn.cursor()
    if user['role'] == 'admin':
        cursor.execute("SELECT * FROM sales")
    else:
        cursor.execute("SELECT * FROM sales WHERE user_id = ?", (user['id'],))
    rows = cursor.fetchall()
    conn.close()

    window = Toplevel()
    window.title("Historial de ventas")
    tree = ttk.Treeview(window, columns=("ID", "User ID", "Producto", "Monto", "Fecha"), show="headings")
    for col in tree["columns"]:
        tree.heading(col, text=col)
    for row in rows:
        tree.insert("", "end", values=row)
    tree.pack(expand=True, fill='both')