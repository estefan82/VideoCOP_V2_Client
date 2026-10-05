#!/bin/bash

# 1. Entrar al directorio
TARGET_DIR="videocop"

if [ -d "$TARGET_DIR" ]; then
    cd "$TARGET_DIR" || exit
    echo "Carpeta: $PWD"

    # 2. Activar el entorno virtual
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "Entorno virtual activado."

        # 3. Ejecutar el script de Python
        if [ -f "control-client.py" ]; then
            echo "Iniciando control-client.py..."
            python3 control-client.py
        else
            echo "Error: No se encontró 'control-client.py'."
        fi
    else
        echo "Error: No se encontró el entorno virtual en 'venv/bin/activate'."
    fi
else
    echo "Error: La carpeta '$TARGET_DIR' no existe."
    exit 1
fi
