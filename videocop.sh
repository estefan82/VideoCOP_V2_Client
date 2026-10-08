#!/bin/bash

# Directorio raíz del proyecto
cd "$(dirname "$0")" || exit 1

echo "[VIDEO COP] Directorio: $(pwd)"

# Activar entorno virtual
source venv/bin/activate

echo "[VIDEO COP] Entorno virtual activado"

# PID del proceso de control_client
CONTROL_PID=""

# Función para cerrar control_client
cleanup() {
    echo
    echo "[VIDEO COP] Cerrando control_client..."

    if [ -n "$CONTROL_PID" ] && kill -0 "$CONTROL_PID" 2>/dev/null; then
        kill "$CONTROL_PID" 2>/dev/null
        wait "$CONTROL_PID" 2>/dev/null
    fi

    echo "[VIDEO COP] VideoCOP cerrado."
}

# Si el script recibe Ctrl+C o termina la UI, limpiar
trap cleanup EXIT
trap 'exit 0' INT TERM

# ---------------------------------------------------------
# CONTROL CLIENT
# Se ejecuta en un loop y se reinicia si se cierra.
# ---------------------------------------------------------

(
    while true; do
        echo "[VIDEO COP] Iniciando control_client..."

        python -m control_client.control_client

        EXIT_CODE=$?

        echo "[VIDEO COP] control_client terminó (código $EXIT_CODE)."
        echo "[VIDEO COP] Reiniciando en 2 segundos..."

        sleep 2
    done
) &

CONTROL_PID=$!

echo "[VIDEO COP] control_client iniciado. PID supervisor: $CONTROL_PID"

# ---------------------------------------------------------
# UI CLIENT
# Se ejecuta en primer plano.
# Cuando termina, el script termina y cleanup() mata
# el supervisor de control_client.
# ---------------------------------------------------------

echo "[VIDEO COP] Iniciando ui_client..."

python -m ui_client.ui_client

UI_EXIT_CODE=$?

echo "[VIDEO COP] ui_client terminó con código $UI_EXIT_CODE."
echo "[VIDEO COP] Cerrando VideoCOP..."

exit "$UI_EXIT_CODE"