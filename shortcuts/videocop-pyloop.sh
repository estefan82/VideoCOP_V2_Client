#!/bin/bash
# Script para iniciar VideoCOP con control_cliente.py y gui-control.py

# Ir a la carpeta correcta
cd /home/admin/videocop/ || { echo "No se encontró la carpeta /home/admin/VideoCOP/"; exit 1; }

# ---- EJECUCIÓN FUERA DEL VENV ----
# Ejecutar button-client.py (en segundo plano) usando el Python global del sistema
echo "Iniciando button-client fuera del venv..."
/usr/bin/python3 button-client.py &
PID_BUTTON=$! # Guardamos el PID de button-client

# ---- EJECUCIÓN DENTRO DEL VENV ----
# Activar el entorno virtual venv para los demás scripts
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
  echo "Entorno virtual 'venv' activado con éxito."
else
  echo "Error: No se encontró el entorno virtual en /home/admin/VideoCOP/venv"
  # Si falla el venv, cerramos button-client para no dejar procesos huérfanos
  kill $PID_BUTTON 2>/dev/null
  exit 1
fi

# Función para mantener activo control-client
iniciar_control_cliente() {
  while true; do
    echo "Iniciando control-client.py..."
    python3 control-client.py &  # Ejecuta usando el Python del venv activo
    pid=$!
    wait $pid                    # Espera a que el proceso termine
    echo "control-client.py se cerró. Reiniciando en 3 segundos..."
    sleep 3
  done
}

# Ejecutar control-client en segundo plano con reinicio automático
iniciar_control_cliente &
PID_CONTROL_LOOP=$! # Guardamos el PID del bucle de control-client por seguridad

# ---- PROCESO PRINCIPAL (PRIMER PLANO) ----
# Ejecutar gui-control.py usando el Python del venv activo
echo "Iniciando ui-client..."
python3 ui-client.py

# ---- LIMPIEZA AL CERRAR UI-CLIENT ----
# Esta sección se ejecuta INMEDIATAMENTE después de que ui-client.py se cierra
echo "ui-client se ha cerrado. Limpiando procesos secundarios..."

# Matar button-client
if kill -0 $PID_BUTTON 2>/dev/null; then
  echo "Deteniendo button-client (PID: $PID_BUTTON)..."
  kill $PID_BUTTON
fi

# Matar el bucle infinito de control-client para que no se quede corriendo en background
if kill -0 $PID_CONTROL_LOOP 2>/dev/null; then
  echo "Deteniendo bucle de control-client..."
  kill $PID_CONTROL_LOOP
  # Intentar matar también el proceso de python3 control-client.py que esté activo en ese instante
  pkill -f control-client.py
fi

echo "Todos los procesos limpios. Script finalizado."