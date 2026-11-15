
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename
from pathlib import Path
from uuid import uuid4

from database.db import (
    inicializar_db,
    guardar_gato,
    obtener_gatos,
    obtener_gato,
    actualizar_gato,
    eliminar_gato,
    obtener_datos_dashboard,
    registrar_alimentacion,
    obtener_alimentaciones_gato,
    obtener_datos_alimentacion_hoy,
    obtener_resumen_alimentacion,
    registrar_temperatura,
    obtener_temperaturas_gato,
    obtener_ultima_temperatura,
    registrar_pesaje,
    obtener_pesajes_gato,
    obtener_estadisticas_gato,
    actualizar_estado_dispositivo,
    obtener_estado_dispositivo
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "miausalud-clave-local"

CARPETA_GATOS = Path(app.root_path) / "static" / "img" / "gatos"
CARPETA_GATOS.mkdir(parents=True, exist_ok=True)

socketio = SocketIO(app, cors_allowed_origins="*")

inicializar_db()


# =========================================================
# UTILIDADES
# =========================================================

def guardar_fotografia(archivo):
    if archivo and archivo.filename:
        extension = Path(secure_filename(archivo.filename)).suffix.lower()

        if extension not in [".jpg", ".jpeg", ".png", ".webp"]:
            return None

        nombre_archivo = f"{uuid4().hex}{extension}"
        archivo.save(CARPETA_GATOS / nombre_archivo)

        return f"img/gatos/{nombre_archivo}"

    return None


def convertir_numero(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


# =========================================================
# INICIO / DASHBOARD
# =========================================================

@app.route("/")
def inicio():
    gatos = obtener_gatos()
    return render_template("index.html", gatos=gatos)


@app.route("/api/dashboard/<int:gato_id>")
def api_dashboard(gato_id):
    datos = obtener_datos_dashboard(gato_id)

    if datos is None:
        return jsonify({"error": "Gato no encontrado"}), 404

    return jsonify(datos)


# =========================================================
# MIS GATOS
# =========================================================

@app.route("/mis-gatos")
def mis_gatos():
    gatos = obtener_gatos()
    return render_template("mis_gatos.html", gatos=gatos)


@app.route("/eliminar-gato/<int:gato_id>", methods=["POST"])
def eliminar_gato_ruta(gato_id):
    gato = obtener_gato(gato_id)

    if gato is None:
        return redirect(url_for("mis_gatos"))

    eliminar_gato(gato_id)

    return redirect(url_for("mis_gatos"))


# =========================================================
# REGISTRAR GATO
# =========================================================

@app.route("/gatos", methods=["GET", "POST"])
def registrar_gato():

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        fecha_nacimiento = request.form.get("fecha_nacimiento") or None
        sexo = request.form.get("sexo") or None
        uid_nfc = request.form.get("uid_nfc", "").strip() or None

        tipo_alimento = request.form.get("tipo_alimento") or None
        nombre_alimento = request.form.get("nombre_alimento", "").strip() or None

        gramos_racion = convertir_numero(
            request.form.get("gramos_racion")
        )

        raciones_dia = request.form.get("raciones_dia") or None

        peso_inicial = convertir_numero(
            request.form.get("peso_inicial")
        )

        foto = guardar_fotografia(request.files.get("foto"))

        guardar_gato(
            nombre,
            uid_nfc,
            foto,
            fecha_nacimiento,
            sexo,
            tipo_alimento,
            nombre_alimento,
            gramos_racion,
            raciones_dia,
            peso_inicial
        )

        return redirect(url_for("mis_gatos"))

    return render_template("gatos.html")


# =========================================================
# EDITAR GATO
# =========================================================

@app.route("/editar-gato/<int:gato_id>", methods=["GET", "POST"])
def editar_gato(gato_id):

    gato = obtener_gato(gato_id)

    if gato is None:
        return redirect(url_for("mis_gatos"))

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        fecha_nacimiento = request.form.get("fecha_nacimiento") or None
        sexo = request.form.get("sexo") or None
        uid_nfc = request.form.get("uid_nfc", "").strip() or None

        tipo_alimento = request.form.get("tipo_alimento") or None
        nombre_alimento = request.form.get("nombre_alimento", "").strip() or None

        gramos_racion = convertir_numero(
            request.form.get("gramos_racion")
        )

        raciones_dia = request.form.get("raciones_dia") or None

        peso_inicial = convertir_numero(
            request.form.get("peso_inicial")
        )

        foto = guardar_fotografia(request.files.get("foto"))

        actualizar_gato(
            gato_id,
            nombre,
            uid_nfc,
            foto,
            fecha_nacimiento,
            sexo,
            tipo_alimento,
            nombre_alimento,
            gramos_racion,
            raciones_dia,
            peso_inicial
        )

        return redirect(url_for("mis_gatos"))

    return render_template("editar_gato.html", gato=gato)


# =========================================================
# ALIMENTACIÓN
# =========================================================

@app.route("/alimentacion")
def alimentacion():
    gatos = obtener_gatos()

    return render_template(
        "alimentacion.html",
        gatos=gatos
    )


@app.route("/api/alimentacion/<int:gato_id>")
def api_alimentacion(gato_id):

    gato = obtener_gato(gato_id)

    if gato is None:
        return jsonify({"error": "Gato no encontrado"}), 404

    historial = obtener_alimentaciones_gato(
        gato_id,
        limite=100
    )

    resumen_hoy = obtener_datos_alimentacion_hoy(gato_id)

    resumen_semanal = obtener_resumen_alimentacion(
        gato_id,
        dias=7
    )

    temperatura = obtener_ultima_temperatura(gato_id)

    return jsonify({
        "gato": gato["nombre"],
        "resumen": resumen_hoy,
        "historial": [dict(fila) for fila in historial],
        "semanal": [dict(fila) for fila in resumen_semanal],
        "temperatura": dict(temperatura) if temperatura else None
    })


# =========================================================
# HISTORIAL DE PESO
# =========================================================

@app.route("/historial-peso")
def historial_peso():
    gatos = obtener_gatos()

    return render_template(
        "historial_peso.html",
        gatos=gatos
    )


@app.route("/api/pesajes/<int:gato_id>")
def api_pesajes(gato_id):

    gato = obtener_gato(gato_id)

    if gato is None:
        return jsonify({"error": "Gato no encontrado"}), 404

    pesajes = obtener_pesajes_gato(gato_id)

    return jsonify({
        "gato": gato["nombre"],
        "peso_inicial": gato["peso_inicial"],
        "historial": [dict(fila) for fila in pesajes]
    })


# =========================================================
# ESTADÍSTICAS
# =========================================================

@app.route("/estadisticas")
def estadisticas():
    gatos = obtener_gatos()

    return render_template(
        "estadisticas.html",
        gatos=gatos
    )


@app.route("/api/estadisticas/<int:gato_id>")
def api_estadisticas(gato_id):

    gato = obtener_gato(gato_id)

    if gato is None:
        return jsonify({"error": "Gato no encontrado"}), 404

    return jsonify(
        obtener_estadisticas_gato(gato_id)
    )


# =========================================================
# SISTEMA / ESP32
# =========================================================

@app.route("/sistema")
def sistema():
    dispositivo = obtener_estado_dispositivo()

    return render_template(
        "sistema.html",
        dispositivo=dispositivo
    )


@app.route("/api/sistema")
def api_sistema():

    dispositivo = obtener_estado_dispositivo()

    if dispositivo:
        return jsonify(dict(dispositivo))

    return jsonify({
        "estado": "desconectado",
        "nombre": "ESP32 MiauSalud",
        "ip": None,
        "ultima_actualizacion": None
    })


# =========================================================
# REGISTRO DE ALIMENTACIÓN DESDE ESP32
# =========================================================

@app.route("/api/registro/alimentacion", methods=["POST"])
def api_registrar_alimentacion():

    datos = request.get_json(silent=True) or request.form

    gato_id = datos.get("gato_id")
    gramos = convertir_numero(
        datos.get("cantidad_gramos")
    )

    if not gato_id or gramos is None or gramos < 0:
        return jsonify({
            "ok": False,
            "error": "Se requiere gato_id y cantidad_gramos válida"
        }), 400

    gato = obtener_gato(int(gato_id))

    if gato is None:
        return jsonify({
            "ok": False,
            "error": "Gato no encontrado"
        }), 404

    registrar_alimentacion(
        int(gato_id),
        gramos,
        datos.get("fecha")
    )

    socketio.emit("actualizacion_alimentacion", {
        "gato_id": int(gato_id),
        "cantidad_gramos": gramos
    })

    return jsonify({
        "ok": True,
        "mensaje": "Alimentación registrada"
    }), 201


# =========================================================
# REGISTRO DE TEMPERATURA DESDE ESP32
# =========================================================

@app.route("/api/registro/temperatura", methods=["POST"])
def api_registrar_temperatura():

    datos = request.get_json(silent=True) or request.form

    temperatura = convertir_numero(
        datos.get("temperatura")
    )

    gato_id = datos.get("gato_id")

    if temperatura is None:
        return jsonify({
            "ok": False,
            "error": "Se requiere una temperatura válida"
        }), 400

    if gato_id is not None:

        gato = obtener_gato(int(gato_id))

        if gato is None:
            return jsonify({
                "ok": False,
                "error": "Gato no encontrado"
            }), 404

        gato_id = int(gato_id)

    registrar_temperatura(
        temperatura,
        gato_id,
        datos.get("fecha")
    )

    socketio.emit("actualizacion_temperatura", {
        "gato_id": gato_id,
        "temperatura": temperatura
    })

    return jsonify({
        "ok": True,
        "mensaje": "Temperatura registrada"
    }), 201


# =========================================================
# REGISTRO DE PESO DESDE ESP32
# =========================================================

@app.route("/api/registro/peso", methods=["POST"])
def api_registrar_peso():

    datos = request.get_json(silent=True) or request.form

    gato_id = datos.get("gato_id")
    peso = convertir_numero(
        datos.get("peso_kg")
    )

    if not gato_id or peso is None or peso <= 0:
        return jsonify({
            "ok": False,
            "error": "Se requiere gato_id y peso_kg válido"
        }), 400

    gato = obtener_gato(int(gato_id))

    if gato is None:
        return jsonify({
            "ok": False,
            "error": "Gato no encontrado"
        }), 404

    registrar_pesaje(
        int(gato_id),
        peso,
        datos.get("fecha")
    )

    socketio.emit("actualizacion_peso", {
        "gato_id": int(gato_id),
        "peso_kg": peso
    })

    return jsonify({
        "ok": True,
        "mensaje": "Pesaje registrado"
    }), 201


# =========================================================
# ACTUALIZAR ESTADO DE ESP32
# =========================================================

@app.route("/api/registro/estado-esp32", methods=["POST"])
def api_estado_esp32():

    datos = request.get_json(silent=True) or request.form

    estado = datos.get("estado", "desconectado")
    ip = datos.get("ip")
    nombre = datos.get(
        "nombre",
        "ESP32 MiauSalud"
    )

    if estado not in ["conectado", "desconectado"]:
        return jsonify({
            "ok": False,
            "error": "Estado no válido"
        }), 400

    actualizar_estado_dispositivo(
        estado,
        ip,
        nombre
    )

    return jsonify({
        "ok": True,
        "mensaje": "Estado actualizado"
    })


# =========================================================
# EJECUTAR APLICACIÓN
# =========================================================

if __name__ == "__main__":

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True
    )
