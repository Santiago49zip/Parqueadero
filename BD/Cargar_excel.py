import sqlite3
import pandas as pd
import os


# Ruta al archivo Excel (ajústala si lo pusiste en otro lugar)
archivo_excel = 'Data/Parqueadero.xlsx'

# Conectamos a la base de datos (usar la DB centralizada en backend)
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'backend', 'parqueadero.db'))
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Nombres de las hojas que quieres importar
hojas = ['MOTOS', 'CARROS', 'TURBO']

for hoja in hojas:
    df = pd.read_excel(archivo_excel, sheet_name=hoja)

    for _, fila in df.iterrows():
        # Extraemos datos, reemplazamos NaN por string vacío o cero según el tipo
        nombre = str(fila.get('NOMBRE', '') or '').strip()
        celular = str(fila.get('CELULAR', '') or '')
        celular2 = str(fila.get('CELULAR2', '') or '')
        placa = str(fila.get('PLACA', '') or '').strip().upper()
        marca = str(fila.get('MARCA', '') or '')
        modelo = str(fila.get('MODELO', '') or '')
        anio = fila.get('ANIO', 0) if not pd.isna(fila.get('ANIO')) else 0
        color = str(fila.get('COLOR', '') or '')
        puesto = str(fila.get('No/SITIO', '') or '')
        dia_pago = int(fila.get('DIA PAGO', 1)) if not pd.isna(fila.get('DIA PAGO')) else 1
        valor = int(fila.get('VALOR', 0)) if not pd.isna(fila.get('VALOR')) else 0
        # Determinar tipo según la hoja
        tipo = 'moto' if hoja.upper().startswith('MOTO') else 'carro'
        observacion = str(fila.get('OBSERVACION', '') or '')

        # Insertamos o recuperamos propietario
        cursor.execute('''
            SELECT id FROM propietarios WHERE nombre = ? AND celular = ?
        ''', (nombre, celular))
        propietario = cursor.fetchone()

        if propietario:
            propietario_id = propietario[0]
        else:
            cursor.execute('''
                INSERT INTO propietarios (nombre, celular, celular_alternativo)
                VALUES (?, ?, ?)
            ''', (nombre, celular, celular2))
            propietario_id = cursor.lastrowid

        # Insertamos vehículo (incluye tipo, valor_mensual y puesto)
        cursor.execute('''
            INSERT INTO vehiculos (propietario_id, placa, marca, modelo, anio, color, tipo, valor_mensual, puesto)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (propietario_id, placa, marca, modelo, anio, color, tipo, valor, puesto))
        vehiculo_id = cursor.lastrowid

        # Insertamos pago
        cursor.execute('''
            INSERT INTO pagos (propietario_id, vehiculo_id, puesto, fecha_pago_esperado, fecha_pago_real, pagado, metodo_pago, observacion)
            VALUES (?, ?, ?, NULL, NULL, 0, '', ?)
        ''', (propietario_id, vehiculo_id, puesto, observacion))

# Guardamos y cerramos
conn.commit()
conn.close()
print("Datos cargados con éxito desde Excel.")

