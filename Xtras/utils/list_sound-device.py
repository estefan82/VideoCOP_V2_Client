import sounddevice as sd

def listar_dispositivos_hw():
    devices = sd.query_devices()
    print("=== Dispositivos de audio detectados ===\n")
    for i, dev in enumerate(devices):
        # Si tiene canales de entrada o salida
        if dev['max_input_channels'] > 0 or dev['max_output_channels'] > 0:
            print(f"Índice [{i}]: {dev['name']}")
            print(f"    Input Channels : {dev['max_input_channels']}")
            print(f"    Output Channels: {dev['max_output_channels']}")
            print(f"    Default Sample Rate: {dev['default_samplerate']}")
            # Mostrar la forma hw:X,Y
            input_idx = i if dev['max_input_channels'] > 0 else 0
            output_idx = i if dev['max_output_channels'] > 0 else 0
            print(f"    Formato hw para sounddevice: sd.default.device = (\"hw:{input_idx},0\", \"hw:{output_idx},0\")\n")

if __name__ == "__main__":
    listar_dispositivos_hw()

