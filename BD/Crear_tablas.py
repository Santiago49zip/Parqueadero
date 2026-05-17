import sqlite3
import os


def crear_tablas():
    # Usar la base de datos central del backend (ruta calculada desde este script)
    base_dir = os.path.dirname(__file__)
    db_path = os.path.abspath(os.path.join(base_dir, '..', 'backend', 'parqueadero.db'))
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()

    # Crear tabla propietarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS propietarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            celular TEXT,
            celular_alternativo TEXT
        )
    ''')

    # Crear tabla vehiculos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            propietario_id INTEGER,
            placa TEXT NOT NULL,
            marca TEXT,
            modelo TEXT,
            anio INTEGER,
            color TEXT,
            tipo TEXT,
            valor_mensual REAL,
            puesto TEXT,
            FOREIGN KEY (propietario_id) REFERENCES propietarios(id)
        )
    ''')

    # Crear tabla pagos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            propietario_id INTEGER,
            vehiculo_id INTEGER,
            fecha_pago_esperado DATE,
            fecha_pago_real DATE,
            pagado BOOLEAN,
            metodo_pago TEXT,
            observacion TEXT,
            monto REAL,
            puesto TEXT,
            FOREIGN KEY (propietario_id) REFERENCES propietarios(id),
            FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id)
        )
    ''')

    conexion.commit()
    conexion.close()
    print("Tablas creadas con éxito")

if __name__ == '__main__':
    crear_tablas()
