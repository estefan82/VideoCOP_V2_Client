import os
import sys
import platform
import time
import customtkinter as ctk
import configparser
import datetime
from core import metadata as metadata
from core import TcpPeer

class VideoCopUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.new_host_client = None
        self.new_id_client = None

        self.ui_status = {
            "id": "",
            "status": "disconnected",
            "call_status": False,
            "audio_stream": False,
            "video_stream": False,
            "server_message": "",
            "only_text": False
        }

        # --- Detectar ruta base y de configuración correctamente ---
        if getattr(sys, 'frozen', False):
            # Si está ejecutándose como ejecutable PyInstaller
            self.base_path = os.path.dirname(sys.executable)
            self.config_path = os.path.join(self.base_path, "core", "ui-client.ini")
            self.control_client_config_path = os.path.join(self.base_path, "core", "control-client.ini")
        else:
            # Si está ejecutándose como script normal (en tu carpeta ui-client/)
            self.base_path = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(self.base_path)
            self.config_path = os.path.join(root_dir, "core", "ui-client.ini")
            self.control_client_config_path = os.path.join(root_dir, "core", "control-client.ini")

        # --- Leer configuración ---
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)

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

        # --- Leer ID de cliente ---
        self.control_client_config = configparser.ConfigParser()
        self.control_client_config.read(self.control_client_config_path)

        self.id_from_ini = self.control_client_config.get("client", "id", fallback="").strip()
        self.host_from_ini = self.control_client_config.get("client", "host", fallback="").strip()
        print(f"ID from control-client.ini: '{self.id_from_ini}'")
        print(f"Host from control-client.ini: '{self.host_from_ini}'")

        # --- Etiquetas principales ---
        self.main_label = ctk.CTkLabel(
            self,
            text="SEES",
            font=ctk.CTkFont(family="Arial", size=56, weight="bold", slant="italic"),
            text_color=("#3a7ebf", "#1f538d")
        )
        # Reducimos el margen inferior a 2 px
        self.main_label.pack(pady=(20, 2))

        self.id_label = ctk.CTkLabel(self, text="ID: ---", font=("Arial", 28, "bold"))
        # Reducimos el margen superior a 2 px
        self.id_label.pack(pady=(2, 20))

        """
        Si los quieres aún más pegados: Cambia ambos a 0, quedando pady=(20, 0) y pady=(0, 20).
        Si los quieres un poco más separados: Ajusta los valores intermedios (por ejemplo, 5 y 5 para lograr 10 px de separación).
        """

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

        #self.update_json_loop()
        self.bind("<Escape>", lambda e: self.destroy())

        # Etiqueta en el extremo inferior IZQUIERDO
        self.left_footer = ctk.CTkLabel(
            self,
            text=f"V: ... ",  # Cambia según tu necesidad
            font=("Arial", 14)
        )
        #self.left_footer.place(relx=0.0, rely=1.0, anchor="sw", x=10, y=-10)

        # Etiqueta en el extremo inferior DERECHO
        self.right_footer = ctk.CTkLabel(
            self,
            text="Powered by Logic Automation",  # Cambia según tu necesidad
            font=("Arial", 14)
        )
        #self.right_footer.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

        self.left_footer.pack(side="left", padx=30)
        self.right_footer.pack(side="right", padx=30)

        # --- VERIFICACIÓN Y APERTURA DE DIÁLOGO ---


        """if not self.id_from_ini:
            self.after(200, self.check_and_prompt_id)

        if not self.host_from_ini:
            self.after(200, self.check_and_prompt_host)"""

        self.after(400, self.check_configuration_flow)

        self.update_clock()

        # ___________  UDP_PEER ______________
        self.intercom_port = 1001
        self.peer = TcpPeer(port=self.intercom_port, role="client", host="videocop-server")
        #self.peer = TcpPeer(port=self.intercom_port, role="client", host="127.0.0.1")

        self.peer.start(on_message=self.incoming_message)
        #self.peer.send("Prueba desde ui-client")

    # -------------------- Exchange funtion --------------------
    def incoming_message00(self, data):
        print(f"Message from target: {data}")

        # Actualizar etiquetas de la interfaz
        self.id_label.configure(text=f"ID: {data.get('id', '---')}")
        msg = data.get("server_message", "")
        if not msg:
            msg = "Welcome to VideoCOP"
        self.message_label.configure(text=msg)

        # Actualizar self.ui_status de forma más limpia usando las claves que lleguen
        keys_to_update = [
            "id", "status", "call_status", "audio_stream",
            "video_stream", "server_message", "only_text"
        ]
        for key in keys_to_update:
            if key in data:
                self.ui_status[key] = data[key]

        print (self.ui_status)


        # Comprobar si hay alguna señal activa de llamada/streaming
        has_active_stream = (
                data.get("audio_stream") or
                data.get("video_stream") or
                data.get("only_text")
        )

        if has_active_stream:
            self.btn_call.pack_forget()
            self.btn_yes.pack(side="left", padx=30)
            self.btn_no.pack(side="left", padx=30)
            print("[INFO] Llamada iniciada")

        # Corregido: añadido self.ui_status (faltaba el self antes)
        elif (
                not self.ui_status.get("audio_stream", True) and
                not self.ui_status.get("video_stream", True) and
                not self.ui_status.get("only_text", True)
        ):
            """Finaliza la llamada"""
            self.btn_yes.pack_forget()
            self.btn_no.pack_forget()
            self.btn_call.pack(side="left", padx=30)
            print("[INFO] Call ended, call reset")

        keys_to_update = [
            "id", "status", "call_status", "audio_stream",
            "video_stream", "server_message", "only_text"
        ]
        for key in keys_to_update:
            if key in data:
                self.ui_status[key] = data[key]

        print(self.ui_status)

    def incoming_message01(self, data):
        print(f"Message from target: {data}")

        if data.get("id", "") and data.get("status", "") == "connected":
            self.id_label.configure(text=f"ID: {data.get('id', '---')}")
            self.ui_status["id"] = data.get("id", "")
            self.ui_status["status"] = data.get("status", "")
        else:
            self.id_label.configure(text=f"ID: ---")
            self.ui_status["id"] = data.get("id", "")
            self.ui_status["status"] = data.get("status", "")

        if data.get("audio_stream", True) or data.get("video_stream", True) or data.get("only_text", True):
            self.btn_call.pack_forget()
            self.btn_yes.pack(side="left", padx=30)
            self.btn_no.pack(side="left", padx=30)
            print("[INFO] Llamada iniciada")

        # Corregido: añadido self.ui_status (faltaba el self antes)
        if not data.get("only_text", False):
            """Finaliza la llamada"""
            self.btn_yes.pack_forget()
            self.btn_no.pack_forget()
            self.btn_call.pack(side="left", padx=30)
            print("[INFO] Call ended, call reset")

        keys_to_update = [
            "id", "status", "call_status", "audio_stream",
            "video_stream", "server_message", "only_text"
        ]
        for key in keys_to_update:
            if key in data:
                self.ui_status[key] = data[key]

        print(self.ui_status)

    def incoming_message(self, data):
        print(f"Message from target: {data}")

        # 1. Actualizar self.ui_status de forma inteligente (resguardando id y status si no vienen)
        for key, value in data.items():
            if key in self.ui_status:
                # Solo actualizamos si el valor que viene no está vacío (o si es una clave booleana/texto normal)
                if key in ("id", "status") and not value:
                    continue  # Si viene vacío, ignoramos para no borrar el estado anterior
                self.ui_status[key] = value

        print("Estado actual:", self.ui_status)  # Para depurar en consola

        # 2. Evaluar la condición usando el estado acumulado protegido
        current_status = self.ui_status.get("status")
        current_id = self.ui_status.get("id")

        if current_status == "connected" and current_id:
            self.id_label.configure(text=f"ID: {current_id}")
        else:
            self.id_label.configure(text="ID: ---")

        # 3. Actualizar el mensaje de texto de la interfaz
        msg = self.ui_status.get("server_message", "")
        if not msg:
            msg = "Welcome to VideoCOP"
        self.message_label.configure(text=msg)

        # 4. Comprobar llamadas o streams activos
        has_active_stream = (
                self.ui_status.get("audio_stream") or
                self.ui_status.get("video_stream") or
                self.ui_status.get("only_text")
        )

        if has_active_stream:
            self.btn_call.pack_forget()
            self.btn_yes.pack(side="left", padx=30)
            self.btn_no.pack(side="left", padx=30)
            print("[INFO] Llamada iniciada")

        elif (
                not self.ui_status.get("audio_stream", True) and
                not self.ui_status.get("video_stream", True) and
                not self.ui_status.get("only_text", True)
        ):
            """Finaliza la llamada"""
            self.btn_yes.pack_forget()
            self.btn_no.pack_forget()
            self.btn_call.pack(side="left", padx=30)
            print("[INFO] Call ended, call reset")

    def outgoing_message(self, msg):
        self.peer.send(msg)

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

        self.left_footer.configure(text=f"V: {metadata.__version__}")
        self.left_footer.pack(side="left", padx=30)

        self.right_footer.configure(text=f"Powered by Logic Automation")
        self.right_footer.pack(side="right", padx=30)
    def check_configuration_flow(self):
        self.update()
        """Orquesta la apertura secuencial de los diálogos."""
        # 1. Comprueba y pide la ID si no existe
        if not self.id_from_ini:
            self.check_and_prompt_id()

        # 2. Comprueba y pide el Host si no existe (se ejecutará DESPUÉS de cerrar el diálogo de ID)
        if not self.host_from_ini:
            self.check_and_prompt_host()
    def check_and_prompt_id(self):
        """Abre la ventana emergente si no hay un ID válido."""
        dialog = ClientIDDialog(self, self.control_client_config_path)
        self.wait_window(dialog)

        if dialog.new_id_client:
            self.new_id_client = dialog.new_id_client
            self.id_from_ini = dialog.new_id_client
            #self.id_label.configure(text=f"ID: {self.new_id_client}")
            print(f"Nuevo ID asignado y guardado: {self.new_id_client}")
    def check_and_prompt_host(self):
        """Abre la ventana emergente si no hay un ID válido."""
        dialog = ClientHostDialog(self, self.control_client_config_path)
        self.wait_window(dialog)

        if dialog.new_host_client:
            self.new_host_client = dialog.new_host_client
            self.host_from_ini = dialog.new_host_client
            print(f"Nuevo HOST asignado y guardado: {self.new_host_client}")

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
            #self.input_json(call=True)
            self.outgoing_message("sos")
            self.call_countdown = self.config.getint("setup", "call_countdown")
    def cancel_call_countdown(self, event=None):
        if self.call_timer:
            self.after_cancel(self.call_timer)
            self.call_timer = None
            self.btn_call.configure(text="Call")
    def call_asap(self):
        #self.input_json(call=True)
        self.outgoing_message("sos")
        return

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
        #self.input_json(response=name)
        self.outgoing_message(name)
        print(f"[BUTTON] {name} pressed")
        time.sleep(1)

    def update_clock(self):
        """Actualiza la hora actual en el footer cada 1 segundo"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        version_text = getattr(metadata, "__version__", "...")
        self.left_footer.configure(text=f"V: {version_text}  |  {current_time}")
        self.after(1000, self.update_clock)

# --- VENTANA MODAL PARA SOLICITAR ID CLIENTE ---
class ClientIDDialog(ctk.CTkToplevel):
    def __init__(self, parent, ini_path):
        super().__init__(parent)
        self.ini_path = ini_path
        self.new_id_client = None

        self.title("Initial configuration")
        self.geometry("380x220")
        self.resizable(False, False)

        # Deshabilitar la funcionalidad del botón de cerrar (X)
        self.protocol("WM_DELETE_WINDOW", lambda: None)


        # Modalidad: Congela la ventana principal e impide interacción
        self.transient(parent)
        self.grab_set()

        # UI Layout
        self.label = ctk.CTkLabel(
            self,
            text="New client.\nSet ID:",
            font=ctk.CTkFont(family="Arial", size=16, weight="bold")
        )
        self.label.pack(padx=20, pady=(20, 10))

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text="Ex: CAB-01",
            width=260,
            height=35,
            font=("Arial", 14)
        )
        self.entry.pack(padx=20, pady=10)
        self.entry.focus()
        self.entry.bind("<Return>", lambda e: self._save_and_close())

        self.btn_save = ctk.CTkButton(
            self,
            text="Save ID",
            width=140,
            height=35,
            font=("Arial", 14, "bold"),
            command=self._save_and_close
        )
        self.btn_save.pack(padx=20, pady=(10, 20))

        # --- APLICAR FOCO CORRECTAMENTE ---
        self.focus_force()  # Trae el Toplevel al frente en el SO
        self.after(100, self.entry.focus)
    def _save_and_close(self):
        val = self.entry.get().strip()
        if val:
            self.new_id_client = val
            self._write_to_ini(val)
            self.destroy()
    def _write_to_ini(self, client_id):
        """Guarda la clave 'id' en el archivo INI especificado"""
        config = configparser.ConfigParser()
        if os.path.exists(self.ini_path):
            config.read(self.ini_path)

        if "client" not in config:
            config["client"] = {}

        config["client"]["id"] = client_id

        with open(self.ini_path, "w", encoding="utf-8") as f:
            config.write(f)

# --- VENTANA MODAL PARA SOLICITAR HOST ---
class ClientHostDialog(ctk.CTkToplevel):
    def __init__(self, parent, ini_path):
        super().__init__(parent)
        self.ini_path = ini_path
        self.new_host_client = None

        self.title("Initial configuration")
        self.geometry("380x220")
        self.resizable(False, False)

        # Deshabilitar la funcionalidad del botón de cerrar (X)
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        # Modalidad: Congela la ventana principal e impide interacción
        self.transient(parent)
        self.grab_set()

        # UI Layout
        self.label = ctk.CTkLabel(
            self,
            text="New client.\nSet HOST:",
            font=ctk.CTkFont(family="Arial", size=16, weight="bold")
        )
        self.label.pack(padx=20, pady=(20, 10))

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text="Ex: Server01 or 192.168.1.2",
            width=260,
            height=35,
            font=("Arial", 14)
        )
        self.entry.pack(padx=20, pady=10)
        self.entry.focus()
        self.entry.bind("<Return>", lambda e: self._save_and_close())

        self.btn_save = ctk.CTkButton(
            self,
            text="Save HOST",
            width=140,
            height=35,
            font=("Arial", 14, "bold"),
            command=self._save_and_close
        )
        self.btn_save.pack(padx=20, pady=(10, 20))

        # --- APLICAR FOCO CORRECTAMENTE ---
        self.focus_force()  # Trae el Toplevel al frente en el SO
        self.after(100, self.entry.focus)
    def _save_and_close(self):
        val = self.entry.get().strip()
        if val:
            self.new_host_client = val
            self._write_to_ini(val)
            self.destroy()
    def _write_to_ini(self, client_host):
        """Guarda la clave 'id' en el archivo INI especificado"""
        config = configparser.ConfigParser()
        if os.path.exists(self.ini_path):
            config.read(self.ini_path)

        if "client" not in config:
            config["client"] = {}

        config["client"]["host"] = client_host

        with open(self.ini_path, "w", encoding="utf-8") as f:
            config.write(f)

if __name__ == "__main__":
    app = VideoCopUI()
    app.after(300, lambda: app.refresh())
    app.outgoing_message("Hello i am client")
    app.mainloop()
