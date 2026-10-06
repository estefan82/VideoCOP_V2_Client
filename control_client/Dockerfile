FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias (audio, video, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar los requerimientos e instalarlos
COPY control_client/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar la carpeta core y el código del cliente
COPY core/ ./core/
COPY control_client/ ./control_client/

# Comando para ejecutar el script de control
CMD ["python", "control_client/control-client.py"]