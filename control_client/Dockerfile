FROM python:3.11-slim-bookworm

# Instalar dependencias del sistema operativo para OpenCV y PortAudio/ALSA
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    portaudio19-dev \
    libasound2-dev \
    libv4l-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente de tu app
COPY . .

CMD ["python", "control-client.py"]