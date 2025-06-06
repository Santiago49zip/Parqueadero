import sqlite3
import os
from datetime import datetime
import logging

def get_db_connection():
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(BASE_DIR, '..', 'parqueadero.db')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def obtener_pagos_de_propietario(propietario_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, propietario_id, vehiculo_id, monto, metodo_pago, 
                   fecha_pago_esperado, fecha_pago_real, pagado, observacion
            FROM pagos
            WHERE propietario_id = ?
        ''', (propietario_id,))
        rows = cursor.fetchall()
        pagos_list = [dict(row) for row in rows]
        logging.debug(f"Pagos encontrados para propietario {propietario_id}: {len(pagos_list)}")
        return pagos_list
    except sqlite3.Error as e:
        logging.error(f"Error al obtener pagos para propietario {propietario_id}: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def registrar_pago(propietario_id, vehiculo_id, monto, metodo, fecha_pago_esperado, fecha_pago_real, pagado, observacion):
    try:
        conn = get_db_connection()
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
            ''', (monto, metodo, fecha_pago_real, pagado, observacion, pago_pendiente["id"]))
        else:
            cursor.execute('''
                INSERT INTO pagos (propietario_id, vehiculo_id, monto, metodo_pago, fecha_pago_esperado, fecha_pago_real, pagado, observacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (propietario_id, vehiculo_id, monto, metodo, fecha_pago_esperado, fecha_pago_real, pagado, observacion))
        
        conn.commit()
        logging.debug(f"Pago registrado para propietario {propietario_id}, vehículo {vehiculo_id}, monto {monto}")
    except (sqlite3.Error, ValueError) as e:
        logging.error(f"Error al registrar pago: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()