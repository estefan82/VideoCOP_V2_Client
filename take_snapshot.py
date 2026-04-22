import cv2

def take_manual_snapshot(device_path):
    cap = cv2.VideoCapture(device_path, cv2.CAP_V4L2)

    if not cap.isOpened():
        return False

    # --- CONFIGURACIÓN MANUAL ---

    # 1. Exposición: Cambiar de 3 (Auto) a 1 (Manual)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
    # Ahora fijamos el tiempo (según tu v4l2, el min es 1 y el max 5000)
    # Prueba con 150-200 para luz de interior normal
    cap.set(cv2.CAP_PROP_EXPOSURE, 156)

    # 2. Ganancia (Gain): Según tu lista, el max es 100.
    # Si la foto sale oscura, sube este valor.
    cap.set(cv2.CAP_PROP_GAIN, 30)

    # 3. Balance de Blancos: Desactivar auto (0) y fijar temperatura
    cap.set(cv2.CAP_PROP_AUTO_WB, 0)
    cap.set(cv2.CAP_PROP_WB_TEMPERATURE, 4600)

    # --- CAPTURA ---

    # Leemos un par de frames para limpiar el buffer interno
    for _ in range(5):
        cap.read()

    ret, frame = cap.read()
    if ret:
        cv2.imwrite("snapshot_manual.jpg", frame)
        print("Snapshot guardado con éxito.")

    cap.release()

#Uso

#device for fernan pi
# discover device in linux by id: ls -l /dev/v4l/by-id/
# show camera control: v4l2-ctl -d /dev/v4l/by-id/TU_ID_AQUI --list-ctrls

device = "/dev/v4l/by-id/usb-VGA_USB_Camera_VGA_USB_Camera_2024022001-video-index0"
take_manual_snapshot(device)

