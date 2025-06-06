import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "backend", "parqueadero.db")

def obtener_todos_los_vehiculos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehiculos")
    resultado = cursor.fetchall()
    conn.close()
    return resultado

def obtener_vehiculo_por_placa(placa):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehiculos WHERE placa = ?", (placa,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado
