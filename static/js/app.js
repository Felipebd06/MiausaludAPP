
/* ==========================================
   MIAUSALUD - DASHBOARD DINAMICO
   ========================================== */

let graficaPeso = null;
let graficaConsumo = null;


// ==========================================
// INICIALIZAR DASHBOARD
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

    const selector = document.getElementById("selectorGato");

    if (selector) {

        selector.addEventListener("change", () => {
            cargarDashboard(selector.value);
        });

        if (selector.value) {
            cargarDashboard(selector.value);
        }
    }

});


// ==========================================
// CONSULTAR DATOS DE SQLITE
// ==========================================

async function cargarDashboard(gatoId) {

    if (!gatoId) return;

    try {

        const respuesta = await fetch(`/api/dashboard/${gatoId}`);

        if (!respuesta.ok) {
            throw new Error("No se pudieron consultar los datos");
        }

        const datos = await respuesta.json();

        actualizarTarjetas(datos);
        actualizarGraficas(datos);

    } catch (error) {

        console.error("Error en el dashboard:", error);

    }

}


// ==========================================
// ACTUALIZAR TARJETAS
// ==========================================

function actualizarTarjetas(datos) {

    const pesoActual = document.getElementById("pesoActual");
    const comidasHoy = document.getElementById("comidasHoy");
    const gramosHoy = document.getElementById("gramosHoy");

    const nombreMichi = document.getElementById("nombreMichi");
    const pesoInicial = document.getElementById("pesoInicial");
    const fechaPesaje = document.getElementById("fechaPesaje");
    const ultimaComida = document.getElementById("ultimaComida");


    if (pesoActual) {
        pesoActual.textContent =
            datos.peso_actual !== null
                ? `${datos.peso_actual} kg`
                : "-- kg";
    }

    if (comidasHoy) {
        comidasHoy.textContent = datos.comidas_hoy;
    }

    if (gramosHoy) {
        gramosHoy.textContent = `${datos.gramos_hoy} g`;
    }

    if (nombreMichi) {
        nombreMichi.textContent = datos.nombre;
    }

    if (pesoInicial) {
        pesoInicial.textContent =
            datos.peso_inicial !== null
                ? `${datos.peso_inicial} kg`
                : "-- kg";
    }

    if (fechaPesaje) {
        fechaPesaje.textContent =
            datos.fecha_pesaje || "Sin pesajes";
    }

    if (ultimaComida) {
        ultimaComida.textContent =
            datos.ultima_comida || "Sin alimentación";
    }

}


// ==========================================
// ACTUALIZAR GRAFICAS
// ==========================================

function actualizarGraficas(datos) {

    actualizarGraficaPeso(datos);
    actualizarGraficaConsumo(datos);

}


// ==========================================
// GRAFICA DE PESO
// ==========================================

function actualizarGraficaPeso(datos) {

    const canvas = document.getElementById("graficaPeso");

    if (!canvas) return;

    if (graficaPeso) {
        graficaPeso.destroy();
    }

    graficaPeso = new Chart(canvas, {

        type: "line",

        data: {

            labels: ["Peso actual"],

            datasets: [{

                label: "Peso (kg)",

                data: [
                    datos.peso_actual !== null
                        ? datos.peso_actual
                        : null
                ],

                borderColor: "#779BD5",
                backgroundColor: "#A9C6F3",
                borderWidth: 3,
                pointRadius: 5,
                tension: 0.3

            }]

        },

        options: {

            responsive: true,
            maintainAspectRatio: false,

            plugins: {
                legend: {
                    display: false
                }
            },

            scales: {

                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: "Peso (kg)"
                    }
                },

                x: {
                    grid: {
                        display: false
                    }
                }

            }

        }

    });

}


// ==========================================
// GRAFICA DE CONSUMO
// ==========================================

function actualizarGraficaConsumo(datos) {

    const canvas = document.getElementById("graficaConsumo");

    if (!canvas) return;

    if (graficaConsumo) {
        graficaConsumo.destroy();
    }

    graficaConsumo = new Chart(canvas, {

        type: "bar",

        data: {

            labels: ["Hoy"],

            datasets: [{

                label: "Consumo de alimento (g)",

                data: [datos.gramos_hoy],

                backgroundColor: ["#779BD5"],
                borderColor: "#222222",
                borderWidth: 1,
                borderRadius: 8

            }]

        },

        options: {

            responsive: true,
            maintainAspectRatio: false,

            plugins: {
                legend: {
                    display: false
                }
            },

            scales: {

                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Consumo (g)"
                    }
                },

                x: {
                    grid: {
                        display: false
                    }
                }

            }

        }

    });

}
