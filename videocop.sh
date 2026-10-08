#!/bin/bash

# ============================================================
# VideoCOP Launcher
# ============================================================
#
# Estructura esperada:
#
#   VideoCOP_V2_Client/
#   ├── venv/
#   ├── core/
#   ├── ui_client/
#   │   └── ui_client.py
#   ├── control_client/
#   │   └── control_client.py
#   └── videocop.sh
#
# ============================================================


# ------------------------------------------------------------
# CONFIGURACIÓN
# ------------------------------------------------------------

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

VENV_DIR="$PROJECT_DIR/venv"

PYTHON="$VENV_DIR/bin/python"

UI_MODULE="ui_client.ui_client"
CONTROL_MODULE="control_client.control_client"

RESTART_DELAY=2

SHUTTING_DOWN=false

SUPERVISOR_PID=""

# ------------------------------------------------------------
# IR AL DIRECTORIO DEL PROYECTO
# ------------------------------------------------------------

cd "$PROJECT_DIR" || {
    echo "[VIDEO COP] ERROR: No se puede acceder a:"
    echo "$PROJECT_DIR"
    exit 1
}

echo
echo "============================================================"
echo "                 VideoCOP Launcher"
echo "============================================================"
echo
echo "[VIDEO COP] Proyecto:"
echo "             $PROJECT_DIR"
echo


# ------------------------------------------------------------
# COMPROBAR VENV
# ------------------------------------------------------------

if [ ! -f "$VENV_DIR/bin/activate" ]; then

    echo "[VIDEO COP] ERROR: No existe el entorno virtual:"
    echo "$VENV_DIR"

    exit 1
fi


# ------------------------------------------------------------
# ACTIVAR VENV
# ------------------------------------------------------------

source "$VENV_DIR/bin/activate"

echo "[VIDEO COP] Virtual environment activado."
echo "[VIDEO COP] Python: $PYTHON"
echo


# ------------------------------------------------------------
# COMPROBAR PYTHON
# ------------------------------------------------------------

if [ ! -x "$PYTHON" ]; then

    echo "[VIDEO COP] ERROR: No existe Python en:"
    echo "$PYTHON"

    exit 1
fi


# ------------------------------------------------------------
# FUNCIÓN PARA MATAR UN GRUPO DE PROCESOS
# ------------------------------------------------------------

kill_process_group() {

    local PID="$1"

    if [ -z "$PID" ]; then
        return
    fi

    # Comprobar si el proceso existe
    if ! kill -0 "$PID" 2>/dev/null; then
        return
    fi

    echo "[VIDEO COP] Cerrando supervisor PID=$PID..."

    # Obtener Process Group ID
    local PGID

    PGID=$(ps -o pgid= -p "$PID" 2>/dev/null | tr -d ' ')

    if [ -n "$PGID" ]; then

        echo "[VIDEO COP] Grupo de procesos: PGID=$PGID"

        # ----------------------------------------------------
        # PRIMER INTENTO: SIGTERM
        # ----------------------------------------------------

        echo "[VIDEO COP] Enviando SIGTERM..."

        kill -TERM -- "-$PGID" 2>/dev/null

        # Esperar hasta 3 segundos
        for i in 1 2 3; do

            sleep 1

            if ! kill -0 "$PID" 2>/dev/null; then
                echo "[VIDEO COP] Supervisor cerrado correctamente."
                return
            fi

        done

        # ----------------------------------------------------
        # SEGUNDO INTENTO: SIGKILL
        # ----------------------------------------------------

        if kill -0 "$PID" 2>/dev/null; then

            echo "[VIDEO COP] El proceso sigue activo."
            echo "[VIDEO COP] Forzando cierre con SIGKILL..."

            kill -KILL -- "-$PGID" 2>/dev/null

            sleep 1
        fi

    else

        # ----------------------------------------------------
        # FALLBACK
        # ----------------------------------------------------

        echo "[VIDEO COP] No se pudo obtener PGID."
        echo "[VIDEO COP] Cerrando PID directamente..."

        kill -TERM "$PID" 2>/dev/null

        sleep 1

        if kill -0 "$PID" 2>/dev/null; then
            kill -KILL "$PID" 2>/dev/null
        fi
    fi
}


# ------------------------------------------------------------
# CLEANUP GENERAL
# ------------------------------------------------------------

cleanup() {

    # Evitar ejecutar cleanup varias veces
    if [ "$SHUTTING_DOWN" = true ]; then
        return
    fi

    SHUTTING_DOWN=true

    echo
    echo "============================================================"
    echo "[VIDEO COP] Cerrando VideoCOP..."
    echo "============================================================"
    echo

    # --------------------------------------------------------
    # CERRAR SUPERVISOR + CONTROL CLIENT + HIJOS
    # --------------------------------------------------------

    if [ -n "$SUPERVISOR_PID" ]; then

        kill_process_group "$SUPERVISOR_PID"

    fi


    # --------------------------------------------------------
    # ESPERAR AL SUPERVISOR
    # --------------------------------------------------------

    if [ -n "$SUPERVISOR_PID" ]; then

        wait "$SUPERVISOR_PID" 2>/dev/null

    fi


    echo
    echo "[VIDEO COP] Todos los procesos de VideoCOP cerrados."
    echo
}


# ------------------------------------------------------------
# SEÑALES
# ------------------------------------------------------------

trap cleanup EXIT

trap 'exit 0' INT TERM


# ============================================================
# CONTROL CLIENT SUPERVISOR
# ============================================================

echo "[VIDEO COP] Iniciando supervisor de control_client..."
echo


setsid bash -c '

PROJECT_DIR="'"$PROJECT_DIR"'"
PYTHON="'"$PYTHON"'"
CONTROL_MODULE="'"$CONTROL_MODULE"'"
RESTART_DELAY="'"$RESTART_DELAY"'"

cd "$PROJECT_DIR" || exit 1

while true; do

    echo
    echo "------------------------------------------------------------"
    echo "[VIDEO COP] Iniciando control_client..."
    echo "------------------------------------------------------------"

    "$PYTHON" -m "$CONTROL_MODULE"

    EXIT_CODE=$?

    echo
    echo "[VIDEO COP] control_client terminó."
    echo "[VIDEO COP] Código de salida: $EXIT_CODE"

    # Si terminó normalmente o por error, se reinicia.
    echo "[VIDEO COP] Reiniciando en ${RESTART_DELAY}s..."

    sleep "$RESTART_DELAY"

done

' &


SUPERVISOR_PID=$!


echo "[VIDEO COP] Supervisor iniciado."
echo "[VIDEO COP] Supervisor PID: $SUPERVISOR_PID"
echo


# ============================================================
# ESPERAR UN MOMENTO PARA QUE CONTROL ARRANQUE
# ============================================================

sleep 1


# ============================================================
# UI CLIENT
# ============================================================

echo "============================================================"
echo "[VIDEO COP] Iniciando UI Client..."
echo "============================================================"
echo


"$PYTHON" -m "$UI_MODULE"

UI_EXIT_CODE=$?


# ============================================================
# UI TERMINÓ
# ============================================================

echo
echo "[VIDEO COP] UI Client terminó."
echo "[VIDEO COP] Código de salida: $UI_EXIT_CODE"
echo


# ============================================================
# SALIR
#
# Al hacer exit se ejecuta:
#
#     trap cleanup EXIT
#
# que cerrará control_client.
# ============================================================

exit "$UI_EXIT_CODE"