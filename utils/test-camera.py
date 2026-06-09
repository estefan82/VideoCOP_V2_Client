import cv2
import platform
import os

def get_best_camera_source(target_keyword="video-index0"):
    system = platform.system()

    if system == "Linux":
        path_by_id = "/dev/v4l/by-id/"
        if os.path.exists(path_by_id):
            devices = os.listdir(path_by_id)
            # Buscamos el que contenga tu cámara y termine en index0
            for d in devices:
                if target_keyword in d:
                    full_path = os.path.join(path_by_id, d)
                    print(f"[INFO] Cámara Linux detectada por ID: {d}")
                    return full_path

        print("[WARN] No se encontró cámara por ID, intentando /dev/video0")
        return "/dev/video0"

    elif system == "Windows":
        # En Windows siempre devolvemos el índice 0 (o podrías escanear)
        print("[INFO] Sistema Windows detectado. Usando índice 0.")
        return 0

    return 0


# --- Aplicación en tu clase o script ---

class MiCapturadora:
    def __init__(self):
        self.camera_device = get_best_camera_source()

        # Selección de Backend según el sistema
        if platform.system() == "Windows":
            self.cap = cv2.VideoCapture(self.camera_device, cv2.CAP_DSHOW)
        else:
            # En Linux, con el path de /dev/v4l/by-id/, usamos V4L2
            self.cap = cv2.VideoCapture(self.camera_device, cv2.CAP_V4L2)

    def mostrar(self):
        if not self.cap.isOpened():
            print("Error: No se pudo abrir la cámara.")
            return

        while True:
            ret, frame = self.cap.read()
            if not ret: break

            cv2.imshow('Feed', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break

        self.cap.release()
        cv2.destroyAllWindows()


# Ejecutar
app = MiCapturadora()
app.mostrar()