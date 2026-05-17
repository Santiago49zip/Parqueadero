from flask import Flask, jsonify, request, render_template, send_from_directory
try:
    from backend.consultas import propietarios, vehiculos, pagos
    from backend.db import get_connection
except ImportError:
    from consultas import propietarios, vehiculos, pagos
    from db import get_connection
from datetime import datetime
import urllib.parse
import os
import sqlite3
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__,
            template_folder="../frontend/templates",
            static_folder="../frontend/static")

def get_db_connection():
    try:
        conn = get_connection()
        logging.debug("Conexión a la base de datos establecida")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error al conectar con la base de datos: {str(e)}")
        raise


def normalizar_placa(placa):
    return placa.strip().upper().replace(' ', '') if placa else ''


def obtener_pagos_mes_actual(cursor, mes_actual):
    cursor.execute('''
        SELECT vehiculo_id, monto, fecha_pago_esperado, fecha_pago_real, pagado, metodo_pago
        FROM pagos
        WHERE strftime('%Y-%m', fecha_pago_esperado) = ?
        ORDER BY vehiculo_id, fecha_pago_real DESC
    ''', (mes_actual,))
    pagos = {}
    for pago in cursor.fetchall():
        if pago['vehiculo_id'] not in pagos:
            pagos[pago['vehiculo_id']] = pago
    return pagos


def construir_resultado(row, pago):
    valor_mensual = row['valor_mensual'] if row['valor_mensual'] is not None else 0
    monto_pagado = float(pago['monto']) if pago and pago['pagado'] else 0
    deuda = max(valor_mensual - monto_pagado, 0)
    estado = 'al día' if pago and pago['pagado'] and deuda <= 0 else 'en mora'
    return {
        'propietario_id': row['propietario_id'],
        'nombre': row['nombre'],
        'celular': row['celular'],
        'vehiculo_id': row['vehiculo_id'],
        'placa': row['placa'],
        'marca': row['marca'],
        'modelo': row['modelo'],
        'anio': row['anio'],
        'color': row['color'],
        'tipo': row['tipo'],
        'valor_mensual': valor_mensual,
        'puesto': row['puesto'],
        'estado': estado,
        'monto_pagado': monto_pagado,
        'deuda': deuda,
        'fecha_pago_esperado': pago['fecha_pago_esperado'] if pago else None,
        'fecha_pago_real': pago['fecha_pago_real'] if pago else None,
        'metodo_pago': pago['metodo_pago'] if pago else None
    }


def obtener_resumen_general():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM propietarios')
        total_propietarios = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM vehiculos')
        total_vehiculos = cursor.fetchone()[0]
        mes_actual = datetime.now().strftime('%Y-%m')
        pagos_mes = obtener_pagos_mes_actual(cursor, mes_actual)

        deudores = 0
        al_dia = 0
        for vehiculo_id in [row['id'] for row in cursor.execute('SELECT id FROM vehiculos').fetchall()]:
            row = {'valor_mensual': 0}
            cursor.execute('SELECT valor_mensual FROM vehiculos WHERE id = ?', (vehiculo_id,))
            valor = cursor.fetchone()
            if valor and valor[0] is not None:
                row['valor_mensual'] = valor[0]
            pago = pagos_mes.get(vehiculo_id)
            resultado = construir_resultado({'propietario_id': None, 'nombre': None, 'celular': None, 'vehiculo_id': vehiculo_id, 'placa': None, 'marca': None, 'modelo': None, 'anio': None, 'color': None, 'tipo': None, 'valor_mensual': row['valor_mensual'], 'puesto': None}, pago)
            if resultado['estado'] == 'en mora':
                deudores += 1
            else:
                al_dia += 1

        return {
            'total_propietarios': total_propietarios,
            'total_vehiculos': total_vehiculos,
            'deudores': deudores,
            'aldia': al_dia
        }
    finally:
        conn.close()

def verificar_pagos_mes_actual():
    try:
        hoy = datetime.now()
        mes_actual = hoy.strftime("%Y-%m")
        primer_dia_mes = hoy.replace(day=1).strftime("%Y-%m-%d")
        conn = get_db_connection()
        cursor = conn.cursor()

        # Obtener todos los vehículos
        cursor.execute('SELECT id, propietario_id, valor_mensual FROM vehiculos')
        vehiculos = cursor.fetchall()

        for vehiculo in vehiculos:
            vehiculo_id = vehiculo["id"]
            propietario_id = vehiculo["propietario_id"]
            valor_mensual = vehiculo["valor_mensual"] if vehiculo["valor_mensual"] is not None else 0

            # Verificar si existe un registro de pago para el mes actual
            cursor.execute('''
                SELECT id, pagado FROM pagos
                WHERE vehiculo_id = ? AND strftime('%Y-%m', fecha_pago_esperado) = ?
            ''', (vehiculo_id, mes_actual))
            pago_existente = cursor.fetchone()

            if not pago_existente:
                # No hay registro para el mes actual: crear uno con pagado = 0
                cursor.execute('''
                    INSERT INTO pagos (propietario_id, vehiculo_id, monto, metodo_pago, fecha_pago_esperado, pagado, observacion)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (propietario_id, vehiculo_id, valor_mensual, 'pendiente', primer_dia_mes, 0, 'Pago mensual pendiente'))
            elif pago_existente["pagado"] == 0:
                # Existe un registro con pagado = 0: no es necesario actualizar
                continue
            else:
                # Registro con pagado = 1: no hacer nada
                continue

        conn.commit()
        logging.debug("Estado de pagos del mes actual verificado y actualizado")
    except sqlite3.Error as e:
        logging.error(f"Error al verificar pagos del mes actual: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

@app.route("/")
def interfaz_web():
    return render_template("index.html")


@app.route('/resumen', methods=['GET'])
def resumen():
    try:
        data = obtener_resumen_general()
        return jsonify(data), 200
    except Exception as e:
        logging.error(f"Error al obtener resumen: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@app.route("/buscar", methods=["GET"])
def buscar():
    try:
        # Verificar pagos del mes actual antes de buscar
        verificar_pagos_mes_actual()
        tipo = request.args.get('tipo', '').strip()
        query = request.args.get('query', '').strip()
        mes_actual = datetime.now().strftime("%Y-%m")

        logging.debug(f"Parámetros recibidos: tipo={tipo}, query={query}, mes_actual={mes_actual}")

        if not tipo:
            return jsonify({"error": "Tipo de búsqueda no proporcionado"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        query_base = '''
            SELECT
                A.id AS propietario_id,
                A.nombre,
                A.celular,
                B.id AS vehiculo_id,
                B.placa,
                B.marca,
                B.modelo,
                B.anio,
                B.color,
                B.tipo,
                B.valor_mensual,
                B.puesto,
                (SELECT monto FROM pagos
                   WHERE vehiculo_id = B.id AND strftime('%Y-%m', fecha_pago_esperado) = ?
                   ORDER BY fecha_pago_real DESC
                   LIMIT 1) AS monto,
                (SELECT fecha_pago_esperado FROM pagos
                   WHERE vehiculo_id = B.id AND strftime('%Y-%m', fecha_pago_esperado) = ?
                   ORDER BY fecha_pago_real DESC
                   LIMIT 1) AS fecha_pago_esperado,
                (SELECT fecha_pago_real FROM pagos
                   WHERE vehiculo_id = B.id AND strftime('%Y-%m', fecha_pago_esperado) = ?
                   ORDER BY fecha_pago_real DESC
                   LIMIT 1) AS fecha_pago_real,
                (SELECT pagado FROM pagos
                   WHERE vehiculo_id = B.id AND strftime('%Y-%m', fecha_pago_esperado) = ?
                   ORDER BY fecha_pago_real DESC
                   LIMIT 1) AS pagado,
                (SELECT metodo_pago FROM pagos
                   WHERE vehiculo_id = B.id AND strftime('%Y-%m', fecha_pago_esperado) = ?
                   ORDER BY fecha_pago_real DESC
                   LIMIT 1) AS metodo_pago
            FROM propietarios A
            INNER JOIN vehiculos B ON A.id = B.propietario_id
        '''

        base_params = [mes_actual] * 5
        if tipo == 'placa':
            sql_query = query_base + ' WHERE UPPER(REPLACE(B.placa, " ", "")) LIKE ?'
            params = base_params + [f'%{normalizar_placa(query)}%']
        elif tipo == 'persona':
            sql_query = query_base + ' WHERE LOWER(A.nombre) LIKE ?'
            params = base_params + [f'%{query.lower()}%']
        elif tipo == 'deudores':
            sql_query = query_base + '''
                WHERE COALESCE((SELECT pagado FROM pagos
                        WHERE vehiculo_id = B.id AND strftime('%Y-%m', fecha_pago_esperado) = ?
                        ORDER BY fecha_pago_real DESC LIMIT 1), 0) = 0
                OR COALESCE((SELECT monto FROM pagos
                        WHERE vehiculo_id = B.id AND strftime('%Y-%m', fecha_pago_esperado) = ?
                        ORDER BY fecha_pago_real DESC LIMIT 1), 0) < COALESCE(B.valor_mensual, 0)
            '''
            params = base_params + [mes_actual, mes_actual]
        elif tipo == 'aldia':
            sql_query = query_base + '''
                WHERE COALESCE((SELECT pagado FROM pagos
                        WHERE vehiculo_id = B.id AND strftime('%Y-%m', fecha_pago_esperado) = ?
                        ORDER BY fecha_pago_real DESC LIMIT 1), 0) = 1
                AND COALESCE((SELECT monto FROM pagos
                        WHERE vehiculo_id = B.id AND strftime('%Y-%m', fecha_pago_esperado) = ?
                        ORDER BY fecha_pago_real DESC LIMIT 1), 0) >= COALESCE(B.valor_mensual, 0)
            '''
            params = base_params + [mes_actual, mes_actual]
        else:
            return jsonify({"error": "Tipo de búsqueda inválido"}), 400

        cursor.execute(sql_query, params)
        rows = cursor.fetchall()
        resultados = []
        for row in rows:
            pago = {
                'monto': row['monto'],
                'fecha_pago_esperado': row['fecha_pago_esperado'],
                'fecha_pago_real': row['fecha_pago_real'],
                'pagado': row['pagado'],
                'metodo_pago': row['metodo_pago']
            } if row['monto'] is not None or row['pagado'] is not None else None

            resultados.append(construir_resultado(row, pago))

        conn.close()
        logging.debug(f"Resultados finales: {len(resultados)}")
        return jsonify(resultados)
    except Exception as e:
        logging.error(f"Error en /buscar: {str(e)}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
    
@app.route("/propietarios", methods=["GET"])
def listar_propietarios():
    data = propietarios.obtener_todos_los_propietarios()
    propietarios_list = [{"id": p[0], "nombre": p[1], "telefono": p[2]} for p in data]
    return jsonify(propietarios_list)

@app.route("/vehiculos", methods=["GET"])
def listar_vehiculos():
    data = vehiculos.obtener_todos_los_vehiculos()
    vehiculos_list = [{"id": v[0], "id_propietario": v[1], "placa": v[2], "tipo": v[3]} for v in data]
    return jsonify(vehiculos_list)

@app.route("/vehiculo/<placa>", methods=["GET"])
def buscar_vehiculo(placa):
    data = vehiculos.obtener_vehiculo_por_placa(placa.upper())
    if not data:
        return jsonify({}), 404
    vehiculo = {
        "id": data[0],
        "id_propietario": data[1],
        "placa": data[2],
        "tipo": data[3]
    }
    return jsonify(vehiculo)

@app.route("/propietario/<int:id_propietario>", methods=["GET"])
def buscar_propietario(id_propietario):
    data = propietarios.obtener_propietario_por_id(id_propietario)
    if not data:
        return jsonify({}), 404
    propietario = {
        "id": data[0],
        "nombre": data[1],
        "telefono": data[2]
    }
    return jsonify(propietario)

@app.route("/pagos/<int:id_propietario>", methods=["GET"])
def pagos_de_propietario(id_propietario):
    try:
        data = pagos.obtener_pagos_de_propietario(id_propietario)
        pagos_list = [
            {
                "id": pago["id"],
                "propietario_id": pago["propietario_id"],
                "vehiculo_id": pago["vehiculo_id"],
                "monto": float(pago["monto"]) if pago["monto"] is not None else 0.0,
                "metodo": pago["metodo_pago"],
                "fecha": pago["fecha_pago_real"] or pago["fecha_pago_esperado"],
                "pagado": bool(pago["pagado"]),
                "observacion": pago["observacion"]
            }
            for pago in data
        ]
        return jsonify(pagos_list), 200
    except sqlite3.Error as e:
        logging.error(f"Error al obtener pagos para propietario {id_propietario}: {str(e)}")
        return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500
    except Exception as e:
        logging.error(f"Error inesperado al obtener pagos para propietario {id_propietario}: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@app.route("/vehiculos/<int:id_propietario>", methods=["GET"])
def vehiculos_de_propietario(id_propietario):
    try:
        rows = vehiculos.obtener_vehiculos_por_propietario(id_propietario)
        vehiculos_list = [
            {
                "id": row["id"],
                "placa": row["placa"],
                "marca": row["marca"],
                "modelo": row["modelo"],
                "anio": row["anio"],
                "color": row["color"],
                "tipo": row["tipo"],
                "valor_mensual": row["valor_mensual"] if row["valor_mensual"] is not None else 0,
                "puesto": row["puesto"]
            } for row in rows
        ]
        logging.debug(f"Vehículos encontrados para propietario {id_propietario}: {len(vehiculos_list)}")
        return jsonify(vehiculos_list)
    except Exception as e:
        logging.error(f"Error al obtener vehículos: {str(e)}")
        return jsonify({"error": f"Error al obtener los vehículos: {str(e)}"}), 500

@app.route("/registrar_pago", methods=["POST"])
def registrar_pago():
    try:
        datos = request.get_json()
        if not datos:
            return jsonify({"error": "No se proporcionaron datos en la solicitud"}), 400

        propietario_id = datos.get("id_propietario")
        vehiculo_id = datos.get("id_vehiculo")
        monto = datos.get("monto")
        metodo = datos.get("metodo")
        fecha_pago_esperado = datos.get("fecha_pago_esperado", datetime.now().strftime("%Y-%m-%d"))
        fecha_pago_real = datos.get("fecha_pago_real", None)
        pagado = datos.get("pagado", 0)
        observacion = datos.get("observacion", None)

        # Validar campos obligatorios
        if not all([propietario_id, vehiculo_id, monto, metodo, fecha_pago_esperado]):
            return jsonify({"error": "Faltan campos obligatorios (id_propietario, id_vehiculo, monto, metodo, fecha_pago_esperado)"}), 400

        # Validar tipos de datos
        try:
            monto = float(monto)
            propietario_id = int(propietario_id)
            vehiculo_id = int(vehiculo_id)
            pagado = int(pagado)
        except (ValueError, TypeError):
            return jsonify({"error": "Tipos de datos inválidos para id_propietario, id_vehiculo, monto o pagado"}), 400

        if monto <= 0:
            return jsonify({"error": "El monto debe ser mayor que cero"}), 400

        pagos.registrar_pago(propietario_id, vehiculo_id, monto, metodo, fecha_pago_esperado, fecha_pago_real, pagado, observacion)
        return jsonify({"mensaje": "Pago registrado correctamente."}), 200
    except (sqlite3.Error, ValueError) as e:
        logging.error(f"Error en registrar_pago: {str(e)}")
        return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500
    except Exception as e:
        logging.error(f"Error inesperado en registrar_pago: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@app.route("/whatsapp/<int:id_propietario>", methods=["GET"])
def generar_enlace_whatsapp(id_propietario):
    propietario = propietarios.obtener_propietario_por_id(id_propietario)
    if not propietario:
        return jsonify({"error": "Propietario no encontrado"}), 404
    nombre = propietario[1]
    telefono = str(propietario[2]).split('.')[0]
    mensaje = f"Hola {nombre}, recuerde que tiene pendiente el pago del parqueadero. Gracias."
    mensaje_encoded = urllib.parse.quote_plus(mensaje)
    link = f"https://wa.me/57{telefono}?text={mensaje_encoded}"
    return jsonify({"enlace_whatsapp": link})


@app.route('/components/<filename>')
def serve_components(filename):
    components_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'components'))
    return send_from_directory(components_dir, filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
 