#!/bin/bash
# Script para iniciar VideoCOP

# Ir a la carpeta correcta (ojo con mayúsculas)
cd /home/admin/VideoCOP || { echo "❌ No se encontró la carpeta /home/admin/VideoCOP"; exit 1; }

# Activar entorno virtual si existe
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Entorno virtual activado."
else
    echo "⚠️  No se encontró el entorno virtual (venv). Continuando sin él..."
fi

# Ejecutar el script Python principal
echo "🚀 Iniciando gui-cliente.py..."
python3 gui-cliente.py
