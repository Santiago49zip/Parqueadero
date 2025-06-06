import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "backend", "parqueadero.db")

def obtener_todos_los_propietarios():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM propietarios")
    resultado = cursor.fetchall()
    conn.close()
    return resultado

def obtener_propietario_por_id(propietario_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM propietarios WHERE id = ?", (propietario_id,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado
