import sqlite3
from datetime import datetime
from backend.db import get_connection


def obtener_pagos_de_propietario(propietario_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, propietario_id, vehiculo_id, monto, metodo_pago, 
                   fecha_pago_esperado, fecha_pago_real, pagado, observacion
            FROM pagos
            WHERE propietario_id = ?
            ORDER BY fecha_pago_esperado DESC, fecha_pago_real DESC
        ''', (propietario_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def registrar_pago(propietario_id, vehiculo_id, monto, metodo, fecha_pago_esperado, fecha_pago_real, pagado, observacion):
    conn = get_connection()
    try:
        cursor = conn.cursor()

        if not fecha_pago_real:
            fecha_pago_real = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('SELECT id FROM propietarios WHERE id = ?', (propietario_id,))
        if not cursor.fetchone():
            raise ValueError(f"Propietario con ID {propietario_id} no existe")

        cursor.execute('SELECT id FROM vehiculos WHERE id = ? AND propietario_id = ?', (vehiculo_id, propietario_id))
        if not cursor.fetchone():
            raise ValueError(f"Vehículo con ID {vehiculo_id} no pertenece al propietario {propietario_id}")

        cursor.execute('''
            SELECT id FROM pagos
            WHERE vehiculo_id = ? AND strftime('%Y-%m', fecha_pago_esperado) = strftime('%Y-%m', ?)
            AND pagado = 0
        ''', (vehiculo_id, fecha_pago_esperado))
        pago_pendiente = cursor.fetchone()

        if pago_pendiente:
            cursor.execute('''
                UPDATE pagos
                SET monto = ?, metodo_pago = ?, fecha_pago_real = ?, pagado = ?, observacion = ?
                WHERE id = ?
            ''', (monto, metodo, fecha_pago_real, pagado, observacion, pago_pendiente['id']))
        else:
            cursor.execute('''
                INSERT INTO pagos (propietario_id, vehiculo_id, monto, metodo_pago, fecha_pago_esperado, fecha_pago_real, pagado, observacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (propietario_id, vehiculo_id, monto, metodo, fecha_pago_esperado, fecha_pago_real, pagado, observacion))

        conn.commit()
    finally:
        conn.close()