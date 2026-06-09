import cv2
import os
import platform
import configparser
import time

def list_cameras():
    cam_list = []
    system = platform.system()
    if system == "Linux":
        path_by_id = "/dev/v4l/by-id/"
        if os.path.exists(path_by_id):
            devices = sorted([d for d in os.listdir(path_by_id) if "video-index0" in d])
            for d in devices:
                cam_list.append(os.path.join(path_by_id, d))
    else:
        for i in range(3):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                cam_list.append(str(i))
                cap.release()
    return cam_list

def select_and_save_camera(file_path="control-client.ini"):
    config = configparser.ConfigParser()

    # 1. Cargamos lo que ya existe en el archivo (si existe)
    if os.path.exists(file_path):
        config.read(file_path)
        print(f"[INFO] Archivo {file_path} cargado. Se mantendrá la configuración existente.")

    cameras = list_cameras()

    if not cameras:
        print("Error: No se detectaron cámaras.")
        return None

    print("\n--- CÁMARAS DISPONIBLES ---")
    for idx, cam in enumerate(cameras):
        print(f"[{idx}] {cam}")

    if len(cameras) == 1:
        selected_path = cameras[0]
        print(f'Single camera detected in:\n{selected_path}')

    else:
        try:
            idx_sel = int(input("\nSelecciona el índice de la cámara: "))
            selected_path = cameras[idx_sel]
        except (ValueError, IndexError):
            print("Selección no válida.")
            return None

    # 2. Solo modificamos la sección [video] y la opción camera_device
    if not config.has_section('video'):
        config.add_section('video')

    config.set('video', 'camera_device', selected_path)

    # 3. Guardamos el contenido de nuevo (esto preserva las otras secciones)
    with open(file_path, 'w') as f:
        config.write(f)

    print(f"\n[OK] Se ha actualizado 'camera_device' en {file_path}")
    return selected_path

def camera_test(device):
    if device:
        print(f"\nProbando cámara: {device}")
        cap = cv2.VideoCapture(device, cv2.CAP_V4L2 if platform.system() == "Linux" else cv2.CAP_DSHOW)

        # Crear carpeta para fotos si no existe
        output_dir = "capturas_test"
        os.makedirs(output_dir, exist_ok=True)

        print(f"Capturando 5 frames de prueba en './{output_dir}'...")

        # Saltamos los primeros frames para que la cámara auto-ajuste el brillo
        for i in range(10): cap.read()

        for i in range(5):
            ret, frame = cap.read()
            if ret:
                filename = f"{output_dir}/test_frame_{i}.jpg"
                cv2.imwrite(filename, frame)
                print(f"  > Guardado: {filename}")
                time.sleep(0.5)  # Pausa breve entre fotos
            else:
                print(f"Error al capturar frame {i}")

        cap.release()
        print("\n--- PROCESO FINALIZADO ---")
        print(f"Ya puedes revisar las imágenes en la carpeta '{output_dir}'")

    else:
        print ('No camera device found')


if __name__ == "__main__":
    camera_test(select_and_save_camera())
