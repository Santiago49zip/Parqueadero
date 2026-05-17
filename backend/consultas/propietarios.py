import sqlite3
from backend.db import get_connection


def obtener_todos_los_propietarios():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, celular, celular_alternativo FROM propietarios")
        return cursor.fetchall()
    finally:
        conn.close()


def obtener_propietario_por_id(propietario_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, celular, celular_alternativo FROM propietarios WHERE id = ?", (propietario_id,))
        return cursor.fetchone()
    finally:
        conn.close()