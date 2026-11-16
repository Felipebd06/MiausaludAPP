
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "database/miausalud.db"
GATO_ID = 7

random.seed(42)

def generar_historial():
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    inicio = datetime.now() - timedelta(days=180)

    peso = 4.50
    fecha = inicio

    print("Generando historial de 6 meses para Lorde...")

    # Alimentación diaria
    for dia in range(180):
        fecha = inicio + timedelta(days=dia)

        gramos = random.choice([30, 30, 30, 60])

        cursor.execute("""
            INSERT INTO alimentaciones
            (gato_id, cantidad_gramos, fecha)
            VALUES (?, ?, ?)
        """, (
            GATO_ID,
            gramos,
            fecha.strftime("%Y-%m-%d %H:%M:%S")
        ))

    # Pesajes cada 7 días
    for dia in range(0, 180, 7):
        fecha = inicio + timedelta(days=dia)

        peso += random.uniform(-0.02, 0.03)

        cursor.execute("""
            INSERT INTO pesajes
            (gato_id, peso_kg, fecha)
            VALUES (?, ?, ?)
        """, (
            GATO_ID,
            round(peso, 2),
            fecha.strftime("%Y-%m-%d %H:%M:%S")
        ))

    # Temperaturas periódicas
    for dia in range(180):
        fecha = inicio + timedelta(days=dia)

        temperatura = random.uniform(24, 28)

        cursor.execute("""
            INSERT INTO temperaturas
            (gato_id, temperatura, fecha)
            VALUES (?, ?, ?)
        """, (
            GATO_ID,
            round(temperatura, 2),
            fecha.strftime("%Y-%m-%d %H:%M:%S")
        ))

    conexion.commit()
    conexion.close()

    print("Historial de 6 meses generado correctamente.")

if __name__ == "__main__":
    generar_historial()
