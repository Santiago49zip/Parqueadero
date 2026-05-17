import sqlite3, os

base_dir = os.path.dirname(__file__)
db_path = os.path.abspath(os.path.join(base_dir, '..', 'backend', 'parqueadero.db'))
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Verificar columnas de pagos
cols = [r[1] for r in c.execute("PRAGMA table_info(pagos);").fetchall()]
if 'puesto' not in cols:
    print('Agregando columna puesto a pagos')
    c.execute("ALTER TABLE pagos ADD COLUMN puesto TEXT;")
    conn.commit()
else:
    print('La columna puesto ya existe en pagos')

conn.close()
print('Schema fix aplicado')
