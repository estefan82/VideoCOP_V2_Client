#!/bin/bash
# Script para iniciar VideoCOP con control_cliente.py y gui-control.py

# Ir a la carpeta correcta
cd /home/admin/VideoCOP || { echo "❌ No se encontró la carpeta /home/admin/VideoCOP"; exit 1; }

# Activar entorno virtual si existe
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Entorno virtual activado."
else
    echo "⚠️  No se encontró el entorno virtual (venv). Continuando sin él..."
fi

# Ejecutar control_cliente.py
echo "🚀 Iniciando control_cliente.py..."
python3 control_cliente.py &   # El & ejecuta en segundo plano

# Ejecutar gui-control.py
echo "🚀 Iniciando gui-control.py..."
python3 gui-control.py         # Se queda en primer plano para ver la GUI

