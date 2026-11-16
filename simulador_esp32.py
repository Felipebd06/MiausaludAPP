
import requests
import time
import random
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"
GATO_ID = 7  # Lorde

def enviar(endpoint, datos):
    try:
        r = requests.post(
            BASE_URL + endpoint,
            json=datos,
            timeout=5
        )
        print(f"{endpoint} -> HTTP {r.status_code}: {r.text}")
    except requests.exceptions.RequestException as e:
        print("Error:", e)

def registrar_pruebas_lorde():
    print("\n=== REGISTROS INICIALES DE LORDE ===")

    # Alimentación: una ración
    enviar("/api/registro/alimentacion", {
        "gato_id": GATO_ID,
        "cantidad_gramos": 30
    })

    # Peso inicial
    enviar("/api/registro/peso", {
        "gato_id": GATO_ID,
        "peso_kg": 4.50
    })

    # Temperatura del alimento
    enviar("/api/registro/temperatura", {
    "gato_id": GATO_ID,
    "temperatura_c": 25.5
})
    

def generar_telemetria():
    return {
        "temp1_c": round(random.uniform(24, 27), 2),
        "temp2_c": round(random.uniform(25, 28), 2),
        "temp3_c": round(random.uniform(23, 26), 2),
        "hx1_kg": round(random.uniform(1.0, 1.5), 3),
        "hx2_kg": round(random.uniform(0.5, 1.0), 3),
        "peltier_pct": random.randint(0, 100),
        "ventilador_pct": random.randint(0, 100),
        "bomba_pct": random.randint(0, 100),
        "servo_pct": random.randint(0, 100),
        "stepper_moviendo": False,
        "sw1": False,
        "sw2": False,
        "sw3": False,
        "sw4": False,
        "sw5": False,
        "sw6": False
    }

def ejecutar():
    print("=== SIMULADOR ESP32 MIAUSALUD ===")

    registrar_pruebas_lorde()

    print("\n=== TELEMETRIA CONTINUA ===")

    while True:
        datos = generar_telemetria()
        enviar("/api/telemetria", datos)
        time.sleep(5)

if __name__ == "__main__":
    ejecutar()
