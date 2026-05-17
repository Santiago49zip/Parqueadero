import sqlite3
from backend.db import get_connection


def obtener_todos_los_vehiculos():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, propietario_id, placa, tipo, valor_mensual, puesto FROM vehiculos")
        return cursor.fetchall()
    finally:
        conn.close()


def obtener_vehiculo_por_placa(placa):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, propietario_id, placa, tipo, marca, modelo, anio, color, valor_mensual, puesto FROM vehiculos WHERE UPPER(REPLACE(placa, ' ', '')) = ?", (placa.upper().replace(' ', ''),))
        return cursor.fetchone()
    finally:
        conn.close()


def obtener_vehiculos_por_propietario(propietario_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, propietario_id, placa, marca, modelo, anio, color, tipo, valor_mensual, puesto
            FROM vehiculos
            WHERE propietario_id = ?
        ''', (propietario_id,))
        return cursor.fetchall()
    finally:
        conn.close()