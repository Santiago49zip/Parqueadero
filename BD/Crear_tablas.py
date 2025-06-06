import sqlite3

def crear_tablas():
    conexion = sqlite3.connect('parqueadero.db')
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
            FOREIGN KEY (propietario_id) REFERENCES propietarios(id)
        )
    ''')

    # Crear tabla pagos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            propietario_id INTEGER,
            vehiculo_id INTEGER,
            puesto TEXT,
            fecha_pago_esperado DATE,
            fecha_pago_real DATE,
            pagado BOOLEAN,
            metodo_pago TEXT,
            observacion TEXT,
            FOREIGN KEY (propietario_id) REFERENCES propietarios(id),
            FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id)
        )
    ''')

    conexion.commit()
    conexion.close()
    print("Tablas creadas con éxito")

if __name__ == '__main__':
    crear_tablas()
