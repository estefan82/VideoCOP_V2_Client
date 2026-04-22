import cv2
import os
import platform
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk


class CameraCalibrator:
    def __init__(self, root):
        self.root = root
        self.root.title("Calibrador de Cámara V4L2 - OpenCV")

        self.cap = None
        self.device_path = tk.StringVar()

        # --- UI: Selección de Dispositivo ---
        frame_top = ttk.LabelFrame(root, text=" 1. Dispositivo ")
        frame_top.pack(fill="x", padx=10, pady=5)

        self.combo_cams = ttk.Combobox(frame_top, postcommand=self.update_cam_list, width=50)
        self.combo_cams.pack(side="left", padx=5, pady=5)
        ttk.Button(frame_top, text="Conectar", command=self.connect_camera).pack(side="left")

        # --- UI: Controles y Preview ---
        main_paned = ttk.PanedWindow(root, orient="horizontal")
        main_paned.pack(fill="both", expand=True, padx=10, pady=5)

        # Panel Izquierdo: Sliders
        self.controls_frame = ttk.LabelFrame(main_paned, text=" 2. Controles Manuales ")
        main_paned.add(self.controls_frame)

        # Panel Derecho: Imagen
        self.preview_frame = ttk.LabelFrame(main_paned, text=" 3. Preview ")
        main_paned.add(self.preview_frame)

        self.img_label = ttk.Label(self.preview_frame)
        self.img_label.pack(padx=5, pady=5)

        # --- Variables de Control ---
        self.sliders = {}
        self.setup_controls()

    def update_cam_list(self):
        path = "/dev/v4l/by-id/"
        if os.path.exists(path):
            self.combo_cams['values'] = [os.path.join(path, d) for d in os.listdir(path) if "video-index0" in d]
        else:
            self.combo_cams['values'] = ["0", "1", "2"]

    def setup_controls(self):
        # Definimos los controles según tu v4l2-ctl
        # (Nombre OpenCV, Min, Max, Default, Propiedad CV2)
        controls = [
            ("Exposición", 1, 5000, 156, cv2.CAP_PROP_EXPOSURE),
            ("Ganancia", 0, 100, 0, cv2.CAP_PROP_GAIN),
            ("Brillo", -64, 64, 0, cv2.CAP_PROP_BRIGHTNESS),
            ("Contraste", 0, 64, 32, cv2.CAP_PROP_CONTRAST),
            ("Saturación", 0, 128, 64, cv2.CAP_PROP_SATURATION)
        ]

        for name, mi, ma, de, prop in controls:
            frame = ttk.Frame(self.controls_frame)
            frame.pack(fill="x", padx=5, pady=2)
            ttk.Label(frame, text=name, width=12).pack(side="left")

            slider = ttk.Scale(frame, from_=mi, to=ma, orient="horizontal",
                               command=lambda v, p=prop: self.update_camera_prop(p, v))
            slider.set(de)
            slider.pack(side="left", fill="x", expand=True)
            self.sliders[prop] = slider

        # Botón para fijar Modo Manual
        ttk.Button(self.controls_frame, text="Forzar Modo Manual",
                   command=self.set_manual_mode).pack(pady=10)

        ttk.Button(self.controls_frame, text="Capturar Snapshot",
                   command=self.take_snapshot).pack(pady=5)

    def set_manual_mode(self):
        if self.cap:
            # 1 = Manual, 3 = Auto en V4L2
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
            self.cap.set(cv2.CAP_PROP_AUTO_WB, 0)
            print("Modo manual forzado.")

    def update_camera_prop(self, prop, value):
        if self.cap:
            self.cap.set(prop, float(value))

    def connect_camera(self):
        if self.cap: self.cap.release()
        path = self.combo_cams.get()
        source = int(path) if path.isdigit() else path
        self.cap = cv2.VideoCapture(source, cv2.CAP_V4L2)
        self.update_preview()

    def update_preview(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                # Convertir para Tkinter
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img = img.resize((640, 480))
                img_tk = ImageTk.PhotoImage(image=img)
                self.img_label.img_tk = img_tk
                self.img_label.configure(image=img_tk)

        self.root.after(30, self.update_preview)

    def take_snapshot(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                cv2.imwrite("test_snapshot.jpg", frame)
                print("Foto guardada como test_snapshot.jpg")


if __name__ == "__main__":
    root = tk.Tk()
    app = CameraCalibrator(root)
    root.mainloop()