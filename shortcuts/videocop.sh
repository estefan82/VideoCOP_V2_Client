#!/bin/bash
# Script para iniciar VideoCOP con control_cliente.py y gui-control.py

# Ir a la carpeta correcta
cd /home/admin/videocop/ || { echo "No se encontró la carpeta /home/admin/VideoCOP/client_v1"; exit 1; }

# Función para mantener activo control-client
iniciar_control_cliente() {
  while true; do
    echo "Iniciando control-client..."
    ./control-client &  # ejecuta en segundo plano
    pid=$!
    wait $pid            # espera a que el proceso termine
    echo "control-client se cerró. Reiniciando en 3 segundos..."
    sleep 3
  done
}

# Ejecutar control-client en segundo plano con reinicio automático
iniciar_control_cliente &

# Ejecutar button-client.py (en segundo plano)
echo "Iniciando button-client..."
x-terminal-emulator -e python3 button-client.py &

# Ejecutar gui-control.py (en primer plano)
echo "Iniciando ui-client..."
./ui-client
