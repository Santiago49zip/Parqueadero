import sqlite3
import pandas as pd
import os
# Conectar a la base de datos
conn = sqlite3.connect('backend/parqueadero.db')
cursor = conn.cursor()
# Insertar datos de prueba
cursor.executescript('''
    INSERT OR IGNORE INTO propietarios (id, nombre, celular, celular_alternativo) VALUES
    (1, 'Juan Pérez', '3001234567', '3009876543'),
    (2, 'María Gómez', '3012345678', NULL);

    INSERT OR IGNORE INTO vehiculos (id, propietario_id, placa, marca, modelo, anio, color, tipo, valor_mensual) VALUES
    (1, 1, 'ABC123', 'Toyota', 'Corolla', 2020, 'Rojo', 'Sedan', 100000),
    (2, 2, 'XYZ789', 'Honda', 'Civic', 2021, 'Azul', 'Sedan', 120000);

    INSERT OR IGNORE INTO pagos (propietario_id, vehiculo_id, puesto, fecha_pago_esperado, fecha_pago_real, pagado, metodo_pago, observacion, monto) VALUES
    (1, 1, 'A1', '2025-05-01', '2025-04-30', 1, 'Efectivo', 'Pago mensual', 100000),
    (2, 2, 'B2', '2025-05-01', NULL, 0, NULL, 'Pendiente', 120000);
''')

conn.commit()
conn.close()
print("Columna 'tipo' actualizada correctamente en la tabla vehiculos.")
