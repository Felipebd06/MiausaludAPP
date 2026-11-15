import sqlite3
from pathlib import Path

# =========================================================
# CONFIGURACIÓN
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "miausalud.db"


def conectar():
    conexion = sqlite3.connect(DB_PATH)
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.row_factory = sqlite3.Row
    return conexion


# =========================================================
# CREACIÓN / ACTUALIZACIÓN DE TABLAS
# =========================================================
def inicializar_db():
    with conectar() as conexion:
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS gatos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                uid_nfc TEXT UNIQUE,
                foto TEXT,
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                activo INTEGER DEFAULT 1
            )
        """)

        conexion.execute("""
            CREATE TABLE IF NOT EXISTS pesajes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gato_id INTEGER NOT NULL,
                peso_kg REAL NOT NULL,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (gato_id) REFERENCES gatos(id)
            )
        """)

        conexion.execute("""
            CREATE TABLE IF NOT EXISTS alimentaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gato_id INTEGER NOT NULL,
                cantidad_gramos REAL NOT NULL,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (gato_id) REFERENCES gatos(id)
            )
        """)

        conexion.execute("""
            CREATE TABLE IF NOT EXISTS temperaturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                temperatura REAL NOT NULL,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conexion.execute("""
            CREATE TABLE IF NOT EXISTS dispositivo (
                id INTEGER PRIMARY KEY,
                nombre TEXT,
                estado TEXT DEFAULT 'desconectado',
                ultima_actualizacion DATETIME
            )
        """)

        # Columnas adicionales para gatos existentes
        columnas_gatos = [
            ("fecha_nacimiento", "DATE"),
            ("sexo", "TEXT"),
            ("tipo_alimento", "TEXT"),
            ("nombre_alimento", "TEXT"),
            ("gramos_racion", "REAL"),
            ("raciones_dia", "INTEGER"),
            ("peso_inicial", "REAL")
        ]
        existentes = {
            fila["name"] for fila in conexion.execute("PRAGMA table_info(gatos)")
        }
        for nombre, tipo in columnas_gatos:
            if nombre not in existentes:
                conexion.execute(f"ALTER TABLE gatos ADD COLUMN {nombre} {tipo}")

        # Agregar gato_id a temperaturas en bases de datos existentes
        columnas_temp = {
            fila["name"] for fila in conexion.execute("PRAGMA table_info(temperaturas)")
        }
        if "gato_id" not in columnas_temp:
            conexion.execute("ALTER TABLE temperaturas ADD COLUMN gato_id INTEGER")

        # Agregar IP a dispositivo si la tabla ya existía
        columnas_disp = {
            fila["name"] for fila in conexion.execute("PRAGMA table_info(dispositivo)")
        }
        if "ip" not in columnas_disp:
            conexion.execute("ALTER TABLE dispositivo ADD COLUMN ip TEXT")

        conexion.execute("""
            INSERT OR IGNORE INTO dispositivo (id, nombre, estado)
            VALUES (1, 'ESP32 MiauSalud', 'desconectado')
        """)

    print("Base de datos MiauSalud inicializada correctamente.")


# =========================================================
# GATOS
# =========================================================
def guardar_gato(nombre, uid_nfc, foto, fecha_nacimiento, sexo,
                 tipo_alimento, nombre_alimento, gramos_racion,
                 raciones_dia, peso_inicial):
    with conectar() as conexion:
        cursor = conexion.execute("""
            INSERT INTO gatos (
                nombre, uid_nfc, foto, fecha_nacimiento, sexo,
                tipo_alimento, nombre_alimento, gramos_racion,
                raciones_dia, peso_inicial
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nombre, uid_nfc, foto, fecha_nacimiento, sexo,
              tipo_alimento, nombre_alimento, gramos_racion,
              raciones_dia, peso_inicial))

        gato_id = cursor.lastrowid
        if peso_inicial is not None:
            conexion.execute("""
                INSERT INTO pesajes (gato_id, peso_kg)
                VALUES (?, ?)
            """, (gato_id, peso_inicial))
    return gato_id


def obtener_gatos():
    with conectar() as conexion:
        return conexion.execute("""
            SELECT * FROM gatos
            WHERE activo = 1
            ORDER BY fecha_registro DESC
        """).fetchall()


def obtener_gato(gato_id):
    with conectar() as conexion:
        return conexion.execute("""
            SELECT * FROM gatos
            WHERE id = ? AND activo = 1
        """, (gato_id,)).fetchone()


def actualizar_gato(gato_id, nombre, uid_nfc, foto, fecha_nacimiento,
                    sexo, tipo_alimento, nombre_alimento,
                    gramos_racion, raciones_dia, peso_inicial):
    with conectar() as conexion:
        conexion.execute("""
            UPDATE gatos
            SET nombre = ?, uid_nfc = ?, foto = COALESCE(?, foto),
                fecha_nacimiento = ?, sexo = ?, tipo_alimento = ?,
                nombre_alimento = ?, gramos_racion = ?, raciones_dia = ?,
                peso_inicial = ?
            WHERE id = ? AND activo = 1
        """, (nombre, uid_nfc, foto, fecha_nacimiento, sexo, tipo_alimento,
              nombre_alimento, gramos_racion, raciones_dia, peso_inicial, gato_id))


def eliminar_gato(gato_id):
    with conectar() as conexion:
        conexion.execute("""
            UPDATE gatos SET activo = 0, uid_nfc = NULL
            WHERE id = ?
        """, (gato_id,))


# =========================================================
# PESAJES
# =========================================================
def registrar_pesaje(gato_id, peso_kg, fecha=None):
    with conectar() as conexion:
        if fecha:
            conexion.execute("""
                INSERT INTO pesajes (gato_id, peso_kg, fecha)
                VALUES (?, ?, ?)
            """, (gato_id, peso_kg, fecha))
        else:
            conexion.execute("""
                INSERT INTO pesajes (gato_id, peso_kg)
                VALUES (?, ?)
            """, (gato_id, peso_kg))


def obtener_pesajes_gato(gato_id, limite=None):
    with conectar() as conexion:
        if limite:
            return conexion.execute("""
                SELECT id, peso_kg, fecha FROM pesajes
                WHERE gato_id = ?
                ORDER BY fecha DESC, id DESC LIMIT ?
            """, (gato_id, limite)).fetchall()
        return conexion.execute("""
            SELECT id, peso_kg, fecha FROM pesajes
            WHERE gato_id = ?
            ORDER BY fecha ASC, id ASC
        """, (gato_id,)).fetchall()


def obtener_ultimo_pesaje(gato_id):
    with conectar() as conexion:
        return conexion.execute("""
            SELECT id, peso_kg, fecha FROM pesajes
            WHERE gato_id = ?
            ORDER BY fecha DESC, id DESC LIMIT 1
        """, (gato_id,)).fetchone()


def obtener_pesajes_periodo(gato_id, fecha_inicio, fecha_fin):
    with conectar() as conexion:
        return conexion.execute("""
            SELECT id, peso_kg, fecha FROM pesajes
            WHERE gato_id = ?
              AND datetime(fecha) >= datetime(?)
              AND datetime(fecha) <= datetime(?)
            ORDER BY fecha ASC, id ASC
        """, (gato_id, fecha_inicio, fecha_fin)).fetchall()


# =========================================================
# ALIMENTACIONES
# =========================================================
def registrar_alimentacion(gato_id, cantidad_gramos, fecha=None):
    with conectar() as conexion:
        if fecha:
            conexion.execute("""
                INSERT INTO alimentaciones (gato_id, cantidad_gramos, fecha)
                VALUES (?, ?, ?)
            """, (gato_id, cantidad_gramos, fecha))
        else:
            conexion.execute("""
                INSERT INTO alimentaciones (gato_id, cantidad_gramos)
                VALUES (?, ?)
            """, (gato_id, cantidad_gramos))


def obtener_alimentaciones_gato(gato_id, limite=None):
    with conectar() as conexion:
        if limite:
            return conexion.execute("""
                SELECT id, cantidad_gramos, fecha FROM alimentaciones
                WHERE gato_id = ?
                ORDER BY fecha DESC, id DESC LIMIT ?
            """, (gato_id, limite)).fetchall()
        return conexion.execute("""
            SELECT id, cantidad_gramos, fecha FROM alimentaciones
            WHERE gato_id = ?
            ORDER BY fecha DESC, id DESC
        """, (gato_id,)).fetchall()


def obtener_alimentaciones_periodo(gato_id, fecha_inicio, fecha_fin):
    with conectar() as conexion:
        return conexion.execute("""
            SELECT id, cantidad_gramos, fecha FROM alimentaciones
            WHERE gato_id = ?
              AND datetime(fecha) >= datetime(?)
              AND datetime(fecha) <= datetime(?)
            ORDER BY fecha ASC, id ASC
        """, (gato_id, fecha_inicio, fecha_fin)).fetchall()


def obtener_resumen_alimentacion(gato_id, dias=7):
    with conectar() as conexion:
        return conexion.execute("""
            SELECT date(fecha, 'localtime') AS dia,
                   COUNT(*) AS comidas,
                   COALESCE(SUM(cantidad_gramos), 0) AS gramos,
                   COALESCE(AVG(cantidad_gramos), 0) AS promedio_gramos
            FROM alimentaciones
            WHERE gato_id = ?
              AND date(fecha, 'localtime') >= date('now', 'localtime', ?)
            GROUP BY date(fecha, 'localtime')
            ORDER BY dia ASC
        """, (gato_id, f"-{dias - 1} days")).fetchall()


def obtener_datos_alimentacion_hoy(gato_id):
    with conectar() as conexion:
        resumen = conexion.execute("""
            SELECT COUNT(*) AS comidas,
                   COALESCE(SUM(cantidad_gramos), 0) AS gramos,
                   COALESCE(AVG(cantidad_gramos), 0) AS promedio_gramos
            FROM alimentaciones
            WHERE gato_id = ?
              AND date(fecha, 'localtime') = date('now', 'localtime')
        """, (gato_id,)).fetchone()

        ultima = conexion.execute("""
            SELECT cantidad_gramos, fecha FROM alimentaciones
            WHERE gato_id = ?
            ORDER BY fecha DESC, id DESC LIMIT 1
        """, (gato_id,)).fetchone()

    return {
        "comidas": resumen["comidas"],
        "gramos": resumen["gramos"],
        "promedio_gramos": resumen["promedio_gramos"],
        "ultima_comida": ultima["fecha"] if ultima else None,
        "ultimo_consumo": ultima["cantidad_gramos"] if ultima else None
    }


# =========================================================
# TEMPERATURAS
# =========================================================
def registrar_temperatura(temperatura, gato_id=None, fecha=None):
    with conectar() as conexion:
        if fecha:
            conexion.execute("""
                INSERT INTO temperaturas (gato_id, temperatura, fecha)
                VALUES (?, ?, ?)
            """, (gato_id, temperatura, fecha))
        else:
            conexion.execute("""
                INSERT INTO temperaturas (gato_id, temperatura)
                VALUES (?, ?)
            """, (gato_id, temperatura))


def obtener_temperaturas_gato(gato_id, limite=None):
    with conectar() as conexion:
        if limite:
            return conexion.execute("""
                SELECT id, temperatura, fecha FROM temperaturas
                WHERE gato_id = ?
                ORDER BY fecha DESC, id DESC LIMIT ?
            """, (gato_id, limite)).fetchall()
        return conexion.execute("""
            SELECT id, temperatura, fecha FROM temperaturas
            WHERE gato_id = ?
            ORDER BY fecha DESC, id DESC
        """, (gato_id,)).fetchall()


def obtener_ultima_temperatura(gato_id=None):
    with conectar() as conexion:
        if gato_id is None:
            return conexion.execute("""
                SELECT id, gato_id, temperatura, fecha FROM temperaturas
                ORDER BY fecha DESC, id DESC LIMIT 1
            """).fetchone()
        return conexion.execute("""
            SELECT id, gato_id, temperatura, fecha FROM temperaturas
            WHERE gato_id = ?
            ORDER BY fecha DESC, id DESC LIMIT 1
        """, (gato_id,)).fetchone()


# =========================================================
# ESTADO ESP32
# =========================================================
def actualizar_estado_dispositivo(estado, ip=None, nombre="ESP32 MiauSalud"):
    with conectar() as conexion:
        conexion.execute("""
            INSERT INTO dispositivo
                (id, nombre, estado, ip, ultima_actualizacion)
            VALUES (1, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                nombre = excluded.nombre,
                estado = excluded.estado,
                ip = excluded.ip,
                ultima_actualizacion = CURRENT_TIMESTAMP
        """, (nombre, estado, ip))


def obtener_estado_dispositivo():
    with conectar() as conexion:
        return conexion.execute("""
            SELECT id, nombre, estado, ip, ultima_actualizacion
            FROM dispositivo WHERE id = 1
        """).fetchone()


# =========================================================
# DASHBOARD
# =========================================================
def obtener_datos_dashboard(gato_id):
    with conectar() as conexion:
        gato = conexion.execute("""
            SELECT nombre, peso_inicial FROM gatos
            WHERE id = ? AND activo = 1
        """, (gato_id,)).fetchone()

        if gato is None:
            return None

        pesaje = conexion.execute("""
            SELECT peso_kg, fecha FROM pesajes
            WHERE gato_id = ?
            ORDER BY fecha DESC, id DESC LIMIT 1
        """, (gato_id,)).fetchone()

        alimentacion = conexion.execute("""
            SELECT COUNT(*) AS comidas,
                   COALESCE(SUM(cantidad_gramos), 0) AS gramos
            FROM alimentaciones
            WHERE gato_id = ?
              AND date(fecha, 'localtime') = date('now', 'localtime')
        """, (gato_id,)).fetchone()

        ultima_comida = conexion.execute("""
            SELECT fecha FROM alimentaciones
            WHERE gato_id = ?
            ORDER BY fecha DESC, id DESC LIMIT 1
        """, (gato_id,)).fetchone()

        temperatura = conexion.execute("""
            SELECT temperatura, fecha FROM temperaturas
            WHERE gato_id = ?
            ORDER BY fecha DESC, id DESC LIMIT 1
        """, (gato_id,)).fetchone()

        return {
            "nombre": gato["nombre"],
            "peso_inicial": gato["peso_inicial"],
            "peso_actual": pesaje["peso_kg"] if pesaje else None,
            "fecha_pesaje": pesaje["fecha"] if pesaje else None,
            "comidas_hoy": alimentacion["comidas"],
            "gramos_hoy": alimentacion["gramos"],
            "ultima_comida": ultima_comida["fecha"] if ultima_comida else None,
            "temperatura": temperatura["temperatura"] if temperatura else None,
            "fecha_temperatura": temperatura["fecha"] if temperatura else None
        }


# =========================================================
# ESTADÍSTICAS
# =========================================================
def obtener_estadisticas_gato(gato_id):
    with conectar() as conexion:
        peso = conexion.execute("""
            SELECT MIN(peso_kg) AS peso_minimo,
                   MAX(peso_kg) AS peso_maximo,
                   AVG(peso_kg) AS peso_promedio,
                   COUNT(*) AS total_pesajes
            FROM pesajes WHERE gato_id = ?
        """, (gato_id,)).fetchone()

        comida = conexion.execute("""
            SELECT COUNT(*) AS total_comidas,
                   COALESCE(SUM(cantidad_gramos), 0) AS consumo_total,
                   COALESCE(AVG(cantidad_gramos), 0) AS consumo_promedio
            FROM alimentaciones WHERE gato_id = ?
        """, (gato_id,)).fetchone()

        temperatura = conexion.execute("""
            SELECT AVG(temperatura) AS temperatura_promedio,
                   MIN(temperatura) AS temperatura_minima,
                   MAX(temperatura) AS temperatura_maxima
            FROM temperaturas WHERE gato_id = ?
        """, (gato_id,)).fetchone()

    return {
        "peso_minimo": peso["peso_minimo"],
        "peso_maximo": peso["peso_maximo"],
        "peso_promedio": peso["peso_promedio"],
        "total_pesajes": peso["total_pesajes"],
        "total_comidas": comida["total_comidas"],
        "consumo_total": comida["consumo_total"],
        "consumo_promedio": comida["consumo_promedio"],
        "temperatura_promedio": temperatura["temperatura_promedio"],
        "temperatura_minima": temperatura["temperatura_minima"],
        "temperatura_maxima": temperatura["temperatura_maxima"]
    }


# =========================================================
# EJECUCIÓN DIRECTA
# =========================================================
if __name__ == "__main__":
    inicializar_db()
def registrar_alimentacion(gato_id, cantidad_gramos, fecha=None):
    """
    Registra una alimentación de un gato.
    """

    with conectar() as conexion:

        if fecha:
            conexion.execute("""
                INSERT INTO alimentaciones (
                    gato_id,
                    cantidad_gramos,
                    fecha
                )
                VALUES (?, ?, ?)
            """, (gato_id, cantidad_gramos, fecha))

        else:
            conexion.execute("""
                INSERT INTO alimentaciones (
                    gato_id,
                    cantidad_gramos
                )
                VALUES (?, ?)
            """, (gato_id, cantidad_gramos))    
