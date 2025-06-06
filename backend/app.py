from flask import Flask, jsonify, request, render_template, send_from_directory
from consultas import propietarios, vehiculos, pagos
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
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Directorio de app.py: C:\Proyectos\Parqueadero\backend
    DB_PATH = os.path.join(BASE_DIR, "parqueadero.db")    # Ruta: C:\Proyectos\Parqueadero\backend\parqueadero.db
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        logging.debug(f"Conexión a la base de datos establecida: {DB_PATH}")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error al conectar con la base de datos: {str(e)}")
        raise

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

@app.route("/buscar", methods=["GET"])
def buscar():
    try:
        # Verificar pagos del mes actual antes de buscar
        verificar_pagos_mes_actual()
        
        tipo = request.args.get('tipo')
        query = request.args.get('query', '')
        hoy = datetime.now().strftime("%Y-%m-%d")

        logging.debug(f"Parámetros recibidos: tipo={tipo}, query={query}, hoy={hoy}")

        if not tipo:
            return jsonify({"error": "Tipo de búsqueda no proporcionado"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        resultados = []
        if tipo in ['placa', 'persona']:
            query_base = '''
                SELECT A.id AS propietario_id, A.nombre, A.celular, 
                       B.id AS vehiculo_id, B.placa, B.marca, B.modelo, B.anio, B.color, B.tipo, B.valor_mensual, B.puesto
                FROM propietarios A
                INNER JOIN vehiculos B ON A.id = B.propietario_id
            '''
            if tipo == 'placa':
                sql_query = query_base + ' WHERE UPPER(REPLACE(B.placa, " ", "")) LIKE ?'
                params = (f'%{query.upper().replace(" ", "")}%',)
            elif tipo == 'persona':
                sql_query = query_base + ' WHERE A.nombre LIKE ?'
                params = (f'%{query}%',)

            cursor.execute(sql_query, params)
            rows = cursor.fetchall()

            for row in rows:
                cursor.execute('''
                    SELECT monto, fecha_pago_esperado, fecha_pago_real, pagado, metodo_pago
                    FROM pagos
                    WHERE vehiculo_id = ? AND strftime('%Y-%m', fecha_pago_esperado) = strftime('%Y-%m', ?)
                    ORDER BY fecha_pago_real DESC LIMIT 1
                ''', (row["vehiculo_id"], hoy))
                pago = cursor.fetchone()

                valor_mensual = row["valor_mensual"] if row["valor_mensual"] is not None else 0
                monto_pagado = pago["monto"] if pago and pago["pagado"] else 0
                deuda = valor_mensual - monto_pagado
                estado = "al día" if pago and pago["pagado"] and deuda <= 0 else "en mora"

                resultados.append({
                    "propietario_id": row["propietario_id"],
                    "nombre": row["nombre"],
                    "celular": row["celular"],
                    "vehiculo_id": row["vehiculo_id"],
                    "placa": row["placa"],
                    "marca": row["marca"],
                    "modelo": row["modelo"],
                    "anio": row["anio"],
                    "color": row["color"],
                    "tipo": row["tipo"],
                    "valor_mensual": valor_mensual,
                    "puesto": row["puesto"],
                    "estado": estado,
                    "monto_pagado": monto_pagado,
                    "deuda": deuda,
                    "fecha_pago_esperado": pago["fecha_pago_esperado"] if pago else None,
                    "fecha_pago_real": pago["fecha_pago_real"] if pago else None,
                    "metodo_pago": pago["metodo_pago"] if pago else None
                })

        elif tipo in ['deudores', 'aldia']:
            query_base = '''
                SELECT A.id AS propietario_id, A.nombre, A.celular, 
                       B.id AS vehiculo_id, B.placa, B.marca, B.modelo, B.anio, B.color, B.tipo, B.valor_mensual, B.puesto
                FROM propietarios A
                INNER JOIN vehiculos B ON A.id = B.propietario_id
            '''
            cursor.execute(query_base)
            rows = cursor.fetchall()

            for row in rows:
                cursor.execute('''
                    SELECT monto, fecha_pago_esperado, fecha_pago_real, pagado, metodo_pago
                    FROM pagos
                    WHERE vehiculo_id = ? AND strftime('%Y-%m', fecha_pago_esperado) = strftime('%Y-%m', ?)
                    ORDER BY fecha_pago_real DESC LIMIT 1
                ''', (row["vehiculo_id"], hoy))
                pago = cursor.fetchone()

                valor_mensual = row["valor_mensual"] if row["valor_mensual"] is not None else 0
                monto_pagado = pago["monto"] if pago and pago["pagado"] else 0
                deuda = valor_mensual - monto_pagado
                estado = "al día" if pago and pago["pagado"] and deuda <= 0 else "en mora"

                if (tipo == 'deudores' and estado == 'en mora') or (tipo == 'aldia' and estado == 'al día'):
                    resultados.append({
                        "propietario_id": row["propietario_id"],
                        "nombre": row["nombre"],
                        "celular": row["celular"],
                        "vehiculo_id": row["vehiculo_id"],
                        "placa": row["placa"],
                        "marca": row["marca"],
                        "modelo": row["modelo"],
                        "anio": row["anio"],
                        "color": row["color"],
                        "tipo": row["tipo"],
                        "valor_mensual": valor_mensual,
                        "puesto": row["puesto"],
                        "estado": estado,
                        "monto_pagado": monto_pagado,
                        "deuda": deuda,
                        "fecha_pago_esperado": pago["fecha_pago_esperado"] if pago else None,
                        "fecha_pago_real": pago["fecha_pago_real"] if pago else None,
                        "metodo_pago": pago["metodo_pago"] if pago else None
                    })

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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, placa, marca, modelo, anio, color, tipo, valor_mensual
            FROM vehiculos
            WHERE propietario_id = ?
        ''', (id_propietario,))
        rows = cursor.fetchall()
        conn.close()
        vehiculos_list = [
            {
                "id": row["id"],
                "placa": row["placa"],
                "marca": row["marca"],
                "modelo": row["modelo"],
                "anio": row["anio"],
                "color": row["color"],
                "tipo": row["tipo"],
                "valor_mensual": row["valor_mensual"] if row["valor_mensual"] is not None else 0
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