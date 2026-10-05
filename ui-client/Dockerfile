FROM python:3.10-slim

# Instalar dependencias del sistema para Tkinter y soporte gráfico en ARM64
RUN apt-get update && apt-get install -y \
    python3-tk \
    libgl1-mesa-glx \
    libx11-xcb1 \
    libxcb-randr0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "ui-client.py"]