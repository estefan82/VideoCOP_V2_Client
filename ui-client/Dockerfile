FROM python:3.10-slim

# Instalar dependencias con nombres de paquetes actualizados para Debian moderno
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    libgl1 \
    libx11-xcb1 \
    libxcb-randr0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "ui-client.py"]