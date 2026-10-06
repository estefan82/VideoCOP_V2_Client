FROM python:3.10-slim

# Instalar dependencias con nombres de paquetes actualizados para Debian moderno
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    libgl1 \
    libx11-xcb1 \
    libxcb-randr0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar los requerimientos específicos de la interfaz desde su subcarpeta
COPY ui_client/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar la carpeta core compartida y el código de la UI
COPY core/ ./core/
COPY ui_client/ ./ui_client/

# Ejecutar el script apuntando a su ruta correcta dentro de la carpeta
CMD ["python", "ui_client/ui-client.py"]