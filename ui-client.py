import json
import os
import sys
import platform
import time

import customtkinter as ctk
import configparser

class VideoCopUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        #configparser
        # --- Detectar ruta base correctamente ---
        if getattr(sys, 'frozen', False):
            # Si está ejecutándose como ejecutable PyInstaller
            self.base_path = os.path.dirname(sys.executable)
        else:
            # Si está ejecutándose como script normal (python3)
            self.base_path = os.path.dirname(os.path.abspath(__file__))

        # --- Construir rutas ---
        self.config_path = os.path.join(self.base_path, "ui-client.ini")
        self.output_path = os.path.join(self.base_path, "output.json")
        self.input_path = os.path.join(self.base_path, "input.json")

        # --- Leer configuración ---
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)

        """# Ruta base del script
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Archivos en la misma carpeta
        config_path = os.path.join(self.base_dir, "gui-cliente.ini")
        self.output_path = os.path.join(self.base_dir, "output.json")
        self.input_path = os.path.join(self.base_dir, "input.json")

        # Leer configuración
        self.config = configparser.ConfigParser()
        self.config.read(config_path)"""

        #self.config = configparser.ConfigParser()
        #self.config.read("gui-cliente.ini")

        self.window_title = self.config["appearance"]["window_title"]
        self.theme = self.config["appearance"]["theme"]
        self.color_theme = self.config["appearance"]["color_theme"]
        self.window_width = self.config.getint("appearance","window_width")
        self.window_height = self.config.getint("appearance","window_height")
        self.fullscreen = self.config.getboolean("appearance", "fullscreen")
        self.zoomed = self.config.getboolean("appearance", "zoomed")
        self.call_countdown = self.config.getint("setup", "call_countdown")

        # Configuración global de apariencia y tema
        ctk.set_appearance_mode("light")  # "light", "dark", "system"
        ctk.set_default_color_theme("dark-blue")  # "blue", "green", "dark-blue"

        self.title(self.window_title)
        #self.geometry(f"{self.window_width}x{self.window_height}")

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"{self.window_width}x{self.window_height}")
        #self.attributes("-fullscreen", True)

        print(screen_w)
        print(screen_h)

        # Detectar sistema operativo
        is_windows = platform.system() == "Windows"
        is_linux = platform.system() == "Linux"

        if is_windows:
            print ("windows")
            if self.zoomed:
                self.after(300, lambda: self.state('zoomed'))
            if self.fullscreen:
                self.after(300, lambda: self.state('zoomed'))
                self.after(300, lambda: self.attributes("-fullscreen", True))
        elif is_linux:
            print("linux")
            if self.fullscreen:
                # Pantalla completa en Linux
                #self.after(100, lambda: self.state('zoomed'))
                self.after(100, lambda: self.attributes("-fullscreen", True))
                #self.after(100, lambda: self.update())
            else:
                # Usa tamaño fijo desde el ini
                #self.geometry(f"{self.window_width}x{self.window_height}")
                # o si quieres llenar toda la pantalla sin ocultar barra de título:
                screen_w = self.winfo_screenwidth()
                screen_h = self.winfo_screenheight()
                self.geometry(f"{screen_w}x{screen_h}")

        #self.output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output.json")
        self.json_data = {}
        self.call_timer = None
        #self.call_count = 3  # cuenta regresiva inicial

        # --- Etiquetas principales ---
        self.id_label = ctk.CTkLabel(self, text="ID: ---", font=("Arial", 28, "bold"))
        self.id_label.pack(pady=(40, 20))

        self.message_label = ctk.CTkLabel(
            self,
            text="waiting for message...",
            wraplength=screen_w - 200,
            justify="center",
            font=("Arial", 56, "bold")
        )
        self.message_label.pack(pady=40, expand=True, fill="both")

        # --- Botones ---
        self.buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.pack(pady=60)

        button_font = ("Arial", 36, "bold")

        self.btn_yes = ctk.CTkButton(
            self.buttons_frame, text="YES", width=260, height=120,
            font=button_font, command=lambda: self.on_button("YES")
        )
        self.btn_call = ctk.CTkButton(
            self.buttons_frame, text="Call", width=300, height=120,
            font=("Arial", 40, "bold")
        )
        self.btn_no = ctk.CTkButton(
            self.buttons_frame, text="NO", width=260, height=120,
            font=button_font, command=lambda: self.on_button("NO")
        )

        # Vincular presionar / soltar para cuenta regresiva
        if self.call_countdown>0:
            self.btn_call.bind("<ButtonPress-1>", self.start_call_countdown)
            self.btn_call.bind("<ButtonRelease-1>", self.cancel_call_countdown)
        else:
            self.btn_call.configure(command=self.call_asap)

        # Mostrar solo "Call" al inicio
        self.btn_call.pack(side="left", padx=30)
        self.btn_call.focus_set()

        self.update_json_loop()
        self.bind("<Escape>", lambda e: self.destroy())

    def refresh(self):
        self.btn_call.pack_forget()
        #self.id_label.configure(text="Starting ui client ...")
        time.sleep(0.1)
        self.btn_yes.pack(side="left", padx=30)
        self.btn_no.pack(side="left", padx=30)
        time.sleep(0.1)
        self.btn_yes.pack_forget()
        self.btn_no.pack_forget()
        time.sleep(0.1)
        self.btn_call.pack(side="left", padx=30)

    # -------------------- COUNTDOWN fo call --------------------
    def start_call_countdown(self, event=None):
        self.update_call_button_text()
    def update_call_button_text(self):
        if self.call_countdown > 0:
            self.btn_call.configure(text=f"{self.call_countdown}...")
            self.call_countdown -= 1
            self.call_timer = self.after(1000, self.update_call_button_text)
        else:
            self.btn_call.configure(text="Call")
            self.after_cancel(self.call_timer)
            self.call_timer = None
            self.input_json(call=True)
            self.call_countdown = self.config.getint("setup", "call_countdown")
    def cancel_call_countdown(self, event=None):
        if self.call_timer:
            self.after_cancel(self.call_timer)
            self.call_timer = None
            self.btn_call.configure(text="Call")
    def call_asap(self):
        self.input_json(call=True)

    # -------------------- UI LOGIC --------------------
    def on_call(self):
        self.btn_call.pack_forget()
        self.btn_yes.pack(side="left", padx=30)
        self.btn_no.pack(side="left", padx=30)
        print("[INFO] Llamada iniciada")
    def end_call(self):
        """Finaliza la llamada"""
        self.btn_yes.pack_forget()
        self.btn_no.pack_forget()
        self.btn_call.pack(side="left", padx=30)
        #print("[INFO] Llamada finalizada automáticamente call reset")
        print("[INFO] Call ended, call reset")
    def on_button(self, name):
        self.input_json(response=name)
        print(f"[BUTTON] {name} pressed")
        time.sleep(1)
    def update_json_loop(self):
        try:
            if os.path.exists(self.output_path):
                with open(self.output_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data != self.json_data:
                    self.json_data = data
                    self.update_ui_from_json(data)
            else:
                self.message_label.configure(text="output.json not found...")
        except Exception as e:
            self.message_label.configure(text=f"[Error reading JSON]\n{e}")
        self.after(500, self.update_json_loop)
    def update_ui_from_json(self, data):
        print (data)
        self.id_label.configure(text=f"ID: {data.get('id', '---')}")
        msg = data.get("server_message", "")
        if not msg:
            msg = "Welcome to VideoCOP"
        self.message_label.configure(text=msg)
        if data.get("audio_stream") or data.get("video_stream") or data.get("only_text"):
            self.on_call()
        if data.get("audio_stream")==False and data.get("video_stream")==False and data.get("only_text")==False:
            self.end_call()

    # -------------------- EXCHANGE JSON --------------------
    def input_json(self, call=None, response=None):
        """
                Crea o actualiza un archivo input JSON con el estado actual del cliente WebSocket.
                Solo actualiza los campos que reciban un valor distinto de None.

                Parámetros:
                    call bool
                    response str or None
                """
        """Create or update json file, actual websocket status
        None enter values, will not update
        Parameteres
            call bool
            response str ar None
        """
        try:
            # Leer archivo existente si existe
            if os.path.exists(self.input_path):
                with open(self.input_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"call": "", "response": ""}

            # Actualizar solo los valores que no son None
            if call is not None:
                data["call"] = bool(call)
            if response is not None:
                data["response"] = response

            # Guardar cambios
            with open(self.input_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            print(f"[✓] input.json updated in {self.input_path}")
        except Exception as e:
            print(f"[!] Error updating input.json: {e}")

if __name__ == "__main__":
    app = VideoCopUI()
    app.after(600, lambda: app.refresh())
    app.mainloop()
