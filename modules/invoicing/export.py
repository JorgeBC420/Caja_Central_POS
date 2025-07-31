import sqlite3
import pandas as pd
from api.database import DB_NAME

def export_to_excel(user):
    conn = sqlite3.connect(DB_NAME)
    if user['role'] == 'admin':
        query = "SELECT * FROM sales"
    else:
        query = "SELECT * FROM sales WHERE user_id = ?"
    df = pd.read_sql_query(query, conn, params=(user['id'],) if user['role'] != 'admin' else ())
    df.to_excel(f"{user['username']}_ventas.xlsx", index=False)
    conn.close()