from tkinter import simpledialog, messagebox
import sqlite3
from datetime import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.api.database import get_connection

def create_new_sale(user):
    item = simpledialog.askstring("Nueva venta", "Nombre del producto:")
    amount = simpledialog.askfloat("Nueva venta", "Monto:")
    if item and amount:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sales (user_id, item, amount, date) VALUES (?, ?, ?, ?)",
                       (user['id'], item, amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        messagebox.showinfo("Venta registrada", "Venta guardada exitosamente.")