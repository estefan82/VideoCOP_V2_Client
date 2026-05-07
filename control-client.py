import asyncio
import json
import inspect
import cv2
import base64
import queue
import io
import os
import sounddevice as sd
import numpy as np
import sys
import signal
import configparser
import metadata as metadata
from datetime import datetime
from websockets.asyncio.client import connect

""" Important
for pi 3 or 4

remove input on:
async def connect(self):
"""


"""
Prueba de configuración por ID de cámara para la pi 4 de fernan


To do
- version control
- list audio video device
- send audio video device info
list-camera ready to save on .ini
to do 

"""

class WebSocketClient:
    def __init__(self, ext_client_id=None):
        print(f">>> Starting {metadata.__name__} v: {metadata.__version__} <<<")
        # configparser
        # --- Detectar ruta base correctamente ---
        if getattr(sys, 'frozen', False):
            # Si está ejecutándose como ejecutable PyInstaller
            self.base_path = os.path.dirname(sys.executable)
        else:
            # Si está ejecutándose como script normal (python3)
            self.base_path = os.path.dirname(os.path.abspath(__file__))

        # --- Build Paths ---
        self.config_path = os.path.join(self.base_path, "control-client.ini")
        self.output_path = os.path.join(self.base_path, "output.json")
        self.input_path = os.path.join(self.base_path, "input.json")

        # --- Read configuration ---
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)

        # --- Read parameters ---
        self.host = self.config["client"]["host"]
        self.port = self.config.getint("client","port")

        #config general
        self.config_version = self.config.get("general","version")

        # check ini version
        if metadata.__version__ != self.config_version:
            self.config_version = metadata.__version__
            self.config.set("general","version", self.config_version)
            self.save_config_file()

        # config client
        if ext_client_id:
            self.client_id = ext_client_id
            print ('[✓] Client ID set from argument:', self.client_id)
        else:
            self.client_id = self.config["client"]["id"]

        # config client
        self.websocket = None
        self.uri = f"ws://{self.host}:{self.port}"

        # config audio
        self.SAMPLE_RATE = self.config.getint("audio","sample_rate")
        self.CHANNELS = self.config.getint("audio","channels")
        self.FRAME_SIZE = self.config.getint("audio","frame_size")
        self.heartbeat = 0 #tiempo de heartbeat, 0 disable
        self.input_hw = self.config["audio"]["input_hw"]
        self.output_hw = self.config["audio"]["output_hw"]

        # --- device configuration  ---
        if self.config.getboolean("audio","mange_dev_by_os"):
            print ("Audio device OS default")
        else:
            #sd.default.device = ("hw:0,0", "hw:0,0")
            sd.default.device = (self.input_hw, self.output_hw )
            print (f"Selected audio device: {self.input_hw},{self.output_hw}")

        self.camera_device = self.config.get("video", "camera_device", fallback='No video device selected')
        print (f'Video device: {self.camera_device}')
        #camera device para fernan pi4
        #self.camera_device = "/dev/v4l/by-id/usb-VGA_USB_Camera_VGA_USB_Camera_2024022001-video-index0"

        self.video_width = self.config.getint("video","video_width")
        self.video_height = self.config.getint("video","video_height")
        self.video_fps = self.config.getint("video","frames_second")

        # status
        self.json_data = {}
        self.last_call_state = False
        self.cooldown = 10 # segundos de cooldown para evitar múltiples llamadas seguidas

        # audio queue
        self.audio_queue = queue.Queue(maxsize=20) # Cola para audio entrante (bytes -> numpy float32 arrays)
        self.audio_stream = None # guard para el stream
        self.audio_active = False # Control del estado de audio full duplex

        #video flags
        self.video_active = False
        self.video_task = None

        self.msg_type_server = {
            0: 'server_message',
            1: 'client_message',
            2: 'ping',
            3: 'pong',
            4: 'audio_chunk',
            5: 'video_chunk',
            6: 'id_request',
            7: 'echo',
            8: 'only_text_on',
            9: 'only_text_off',
            10: 'server_audio_chunk',
            11: 'client_audio_chunk',
            12: 'audio_start',
            13: 'audio_stop',
            14: 'snapshot_request',
            15: 'snapshot_response',
            16: 'video_start',
            17: 'video_stop',
            18: 'config_request',
            19: 'config_send'
        }

        # data JSON example, (for better comp)
        self.data_example = {
            "id": "client_id",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": self.msg_type_server[0],
            "text": str("text")
        }

        self.clean_output_json()

    async def listen_messages(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                if data.get("type") == "pong":
                    print(f"<<< Heartbeat OK ({data['time']})")

                elif data.get("type") == "server_message":
                    self.output_json(server_message=data['text'])
                    print(f"<<< server_message: {data['text']}")

                elif data.get("type") == "audio_start":
                    print("Orden recibida: iniciar transmisión de audio")
                    await self.start_audio_stream()
                    self.output_json(audio_stream=True)
                    #asyncio.create_task(self.start_audio_stream())
                    continue

                elif data.get("type") == "server_audio_chunk":
                    base64_chunk = data.get("message", "")
                    #  print(f"Audio chunk recibido ({len(base64_chunk)} bytes)")
                    self.play_audio_chunk(base64_chunk)
                    continue

                elif data.get("type") == "audio_stop":
                    print("Orden recibida: detener transmisión de audio")
                    self.output_json(audio_stream=False)
                    self.audio_active = False  # Detiene callback inmediatamente
                    if self.audio_stream:
                        try:
                            self.audio_stream.stop()
                            self.audio_stream.close()
                            print("Stream detenido correctamente")
                        except Exception as e:
                            print(f"[!] Error deteniendo stream: {e}")
                        finally:
                            self.audio_stream = None
                    # Limpiar la cola por seguridad
                    while not self.audio_queue.empty():
                        try:
                            self.audio_queue.get_nowait()
                        except queue.Empty:
                            break

                elif data.get("type") == "video_start":
                    print("Orden recibida: iniciar transmisión de video")
                    self.output_json(video_stream=True)
                    await self.start_video()
                    continue

                elif data.get("type") == "snapshot_request":
                    print("Orden recibida: enviar snapshot")
                    await self.send_snapshot(width=self.video_width, height=self.video_height)
                    continue

                elif data.get("type") == "video_stop":
                    print("Orden recibida: detener transmisión de video")
                    self.output_json(video_stream=False)
                    await self.stop_video()
                    continue

                elif data.get("type") == "id_request":
                    print ("ID request from server")
                    await self.send_json("id_request", self.client_id)

                elif data.get("type") == self.msg_type_server[7]:
                    print(f"Echo from server [text]: {data['text']}")

                elif data.get("type") == self.msg_type_server[8]:
                    print ("Only text mode On")
                    self.output_json(only_text=True)

                elif data.get("type") == self.msg_type_server[9]:
                    print ("Only text mode Off")
                    self.output_json(only_text=False)

                else:
                    print(f"data {data}")

        except Exception as e:
            print(f"[!] Error escuchando mensajes: {e}")

    #Exchange JSON
    def clean_output_json(self):
        # Estructura base
        data = {
            "id": "---",
            "status": "disconnected",
            "call_status": False,
            "audio_stream": False,
            "video_stream": False,
            "server_message": "",
            "only_text": False
        }

        # Crear el archivo inmediatamente
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return

    def output_json(self, id_str=None, status=None, audio_stream=None, video_stream=None, server_message=None, only_text=None):
        """
        Crea o actualiza un archivo JSON con el estado actual del cliente WebSocket.
        Solo actualiza los campos que reciban un valor distinto de None.

        Parámetros:
            id_str (str | None): Identificador del cliente.
            status (bool | None): True si conectado, False si desconectado.
            call_status (bool | None): True si conectado, False si desconectado.
            audio_stream (bool | None): True si conectado, False si desconectado.
            video_stream (bool | None): True si conectado, False si desconectado.
            server_message (str | None): Último mensaje del servidor.
            only text mode (bool | None): Only text mode On (True)
        """
        try:

            # Leer archivo existente si existe
            if os.path.exists(self.output_path):
                with open(self.output_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                # Estructura base
                data = {
                    "id": "",
                    "status": "disconnected",
                    "call_status": False,
                    "audio_stream": False,
                    "video_stream": False,
                    "server_message": "",
                    "only_text": False
                }

            # Actualizar solo los valores que no son None
            if id_str is not None:
                data["id"] = id_str
            if status is not None:
                data["status"] = "connected" if status else "disconnected"
            if audio_stream is not None:
                data["audio_stream"] = bool(audio_stream)
            if video_stream is not None:
                data["video_stream"] = bool(video_stream)
            if server_message is not None:
                data["server_message"] = server_message
            if only_text is not None:
                data["only_text"] = bool(only_text)

            # Guardar cambios
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            print(f"[✓] output.json actualizado en {self.output_path}")

        except Exception as e:
            print(f"[!] Error actualizando output.json: {e}")
    async def clean_input_json(self):
        """Vacía el contenido del archivo JSON sin eliminarlo."""

        if os.path.exists(self.input_path):
            try:
                # Puedes dejarlo como un objeto vacío o con una estructura base
                with open(self.input_path, "w", encoding="utf-8") as f:
                    json.dump({}, f, indent=4)
                print(f"Archivo {self.input_path} limpiado correctamente.")
            except Exception as e:
                print(f"Error al limpiar el archivo: {e}")
        else:
            print(f"El archivo {self.input_path} no existe.")
    async def update_json_loop00(self, interval=0.5):
        """Lee y muestra el JSON cada 'interval' segundos, sin bloquear."""
        input_path = self.input_path
        previous_data = {}

        while True:
            try:
                if os.path.exists(input_path):
                    with open(input_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if data != previous_data:
                        previous_data = data
                        #print(data)
                        # Acciones según valores del JSON
                        if data.get("call"):
                            await self.send_json(self.msg_type_server[1], "Emergency Call")
                            await self.clean_input_json()
                            previous_data = {}
                        elif data.get("response") == "NO":
                            await self.send_json(self.msg_type_server[1], "NO")
                            await self.clean_input_json()
                            previous_data = {}
                        elif data.get("response") == "YES":
                            await self.send_json(self.msg_type_server[1], "YES")
                            await self.clean_input_json()
                            previous_data = {}
                else:
                    print("output.json not found")

            except Exception as e:
                print(f"[Error leyendo JSON] {e}")

            await asyncio.sleep(interval)
    async def update_json_loop(self, interval=1):
        """
        Monitoriza input.json y envía eventos al servidor sin debounce.

        ✔ Envía Emergency Call cada vez que call=True
        ✔ Envía respuestas YES/NO cada vez que aparecen
        ✔ Limpia input.json tras procesar cada evento
        """
        input_path = self.input_path
        last_response = None
        self.sending_cooldown = False  # flag para cooldown
        while True:
            try:
                if os.path.exists(input_path):
                    with open(input_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # =========================
                    # EMERGENCY CALL
                    # =========================
                    if data.get("call", False):
                        print("EMERGENCY SENT", datetime.now())
                        await self.send_json(
                            self.msg_type_server[1],
                            "Emergency Call"
                        )
                        await self.clean_input_json()

                    # =========================
                    # RESPUESTAS YES / NO
                    # =========================
                    response = data.get("response")
                    if response in ("YES", "NO"):
                        print(f"📨 Response detected: {response}")
                        await self.send_json(
                            self.msg_type_server[1],
                            response
                        )
                        await self.clean_input_json()

                else:
                    print("input.json not found")

            except Exception as e:
                print(f"[Error leyendo JSON] {e}")

            await asyncio.sleep(interval)
    async def _cooldown_timer(self, cooldown):
        """Timer para desbloquear cooldown después de X segundos."""
        await asyncio.sleep(cooldown)
        self.sending_cooldown = False

    # Connect block
    async def connect(self):
        print(f"OS detected: {os.name}")

        while True:
            try:
                print(f" Conectando a {self.uri} ...")

                async with connect(self.uri, ping_interval=20) as websocket:
                    self.websocket = websocket

                    if os.name != "nt":
                        # Close the connection when receiving SIGTERM only in linux
                        loop = asyncio.get_running_loop()
                        loop.add_signal_handler(signal.SIGTERM, loop.create_task, websocket.close_timeout)

                    print(" Conectado al servidor.")
                    self.output_json(self.client_id, True, audio_stream=False, video_stream=False, only_text=False)

                    #clean input JSON once
                    asyncio.create_task(self.clean_input_json())

                    # start loop for input JSON
                    json_task = asyncio.create_task(self.update_json_loop())

                    await asyncio.gather(
                        self.listen_messages(),
                        self.send_json(self.msg_type_server[0], "Hello"),
                        self.send_config(self.client_id),
                        #self.user_input() #for manual input from terminal
                    )

                    # end loop for input json
                    json_task.cancel()
                    try:
                        await json_task
                    except asyncio.CancelledError:
                        pass

            except Exception as e:
                print(f"Error de conexión: {e}, exiting in 1s...")
                self.output_json(id_str="---",status=False, server_message="", audio_stream=False, video_stream=False, only_text=False)
                await asyncio.sleep(1)
                sys.exit(0)

    # Audio block
    def play_audio_chunk(self, base64_data):
        """Recibe un chunk base64, decodifica y lo agrega a la cola."""
        try:
            audio_bytes = base64.b64decode(base64_data)
            audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
            # Iniciar el stream de salida en el bucle asyncio si aún no existe
            loop = asyncio.get_running_loop()
            if self.audio_stream is None:
                asyncio.run_coroutine_threadsafe(self.start_audio_stream(), loop)
            self.audio_queue.put(audio_array)
        except Exception as e:
            print(f"[!] Error reproduciendo audio: {e}")
    def stop_audio_output(self):
        """Detiene el stream de salida y limpia la cola de audio."""
        if self.audio_stream is not None:
            try:

                self.audio_stream.stop()
                self.audio_stream.close()
                print("Stream de salida detenido")
            except Exception as e:
                print(f"Error cerrando stream de audio: {e}")
            finally:
                self.audio_stream = None

        # Limpiar la cola de audio
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
    async def start_audio_stream(self):
        if self.audio_active:
            print("Stream de audio ya activo.")
            return

        print("Iniciando audio stream...")
        loop = asyncio.get_running_loop()
        self.audio_active = True

        if self.audio_stream is None:
            def callback(indata, outdata, frames, time, status):
                if not self.audio_active:
                    outdata[:] = np.zeros((frames, self.CHANNELS), np.float32)
                    return  # Si se detuvo, no seguir procesando

                try:
                    if status:
                        print("Status", status)
                    # Captura micrófono → envía al servidor
                    # Codificar el chunk en base64
                    encoded = base64.b64encode(indata.tobytes()).decode('utf-8')
                    msg = {
                        "type": self.msg_type_server[11],
                        "message": encoded
                    }
                    asyncio.run_coroutine_threadsafe(
                        self.websocket.send(json.dumps(msg)),
                        loop
                    )
                    # Reproduce desde la cola (audio recibido del servidor)
                    try:
                        data = self.audio_queue.get_nowait()
                        outdata[:] = data.reshape(-1, self.CHANNELS)
                    except queue.Empty:
                        outdata[:] = np.zeros((frames, self.CHANNELS), np.float32)

                except Exception as e:
                    print(f"Error en callback: {e}")

            # Crear stream
            self.audio_stream = sd.Stream(
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                blocksize=self.FRAME_SIZE,
                dtype='float32',
                callback=callback
            )

            # Iniciar stream
            self.audio_stream.start()
            print("Transmitiendo y recibiendo audio...")

        else:
            print("⚠️ Stream ya está activo.")

    # Video block
    async def video_sender(self, width=640, height=480, fps=20):
        """Captura video y lo envía como JSON por el WebSocket existente."""
        try:
            #cap = cv2.VideoCapture(0)
            cap = cv2.VideoCapture(self.camera_device,cv2.CAP_V4L2)

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_FPS, fps)

            interval = 1.0 / fps
            print("Sending video frames...")

            while self.video_active:
                ret, frame = cap.read()
                if not ret:
                    await asyncio.sleep(0.1)
                    continue

                _, buffer = cv2.imencode('.jpg', frame)
                jpg_as_text = base64.b64encode(buffer).decode('utf-8')

                msg = {
                    "id": self.client_id,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "video_chunk",
                    "message": jpg_as_text
                }

                try:
                    await self.websocket.send(json.dumps(msg))
                except Exception as e:
                    print(f"Error sending frame: {e}")
                    break

                await asyncio.sleep(interval)

            cap.release()
            print("Stop video capture...")

        except Exception as e:
            print(f"Error in video_sender: {e}")
            await asyncio.sleep(3)
            if self.video_active:
                await self.video_sender(width, height, fps)
    async def start_video(self):
        """Inicia la transmisión de video si no está activa."""
        if self.video_active:
            print("Video already active.")
            return
        self.video_active = True
        self.video_task = asyncio.create_task(self.video_sender(width=self.video_width,
                                                                height=self.video_height,
                                                                fps=self.video_fps))
    async def stop_video(self):
        """Detiene la transmisión de video."""
        if not self.video_active:
            print("Video no está activo.")
            return
        self.video_active = False
        if self.video_task:
            self.video_active = False
            self.video_task.cancel()
            self.video_task = None
        print("Transmisión de video detenida.")

    # Snapshot block
    async def send_snapshot(self, width=640, height=480):
        """Captura una sola imagen y la envía por el WebSocket."""
        try:
            #cap = cv2.VideoCapture(0)
            cap = cv2.VideoCapture(self.camera_device, cv2.CAP_V4L2)

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

            # Esperar un momento para que la cámara se estabilice
            await asyncio.sleep(1)

            ret, frame = cap.read()
            cap.release()

            if not ret:
                print("No se pudo capturar la imagen")
                return

            # Codificar a JPG
            _, buffer = cv2.imencode('.jpg', frame)
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')

            msg = {
                "id": self.client_id,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "snapshot_response",  # 👈 tipo distinto para identificar imagen única
                "message": jpg_as_text
            }

            await self.websocket.send(json.dumps(msg))
            print("Snapshot enviado")

        except Exception as e:
            print(f"Error enviando snapshot: {e}")

    # Send JSON to server
    async def send_json(self, msg_type, text):
        #print ("sending json...")
        data = {
            "id": self.client_id,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": msg_type,
            "text": text
        }
        print (data)
        await self.websocket.send(json.dumps(data))

    # Send heartbeat not in use
    async def send_heartbeat(self):
        while True:
            if self.heartbeat > 0:
                try:
                    await asyncio.sleep(self.heartbeat)
                    await self.send_json("ping", "keepalive")
                except Exception:
                    print ("heartbeat reised and error")
                    await self.websocket_close()
                    break
            else:
                print ("heartbeat disable")

    # Send config file
    async def send_config(self, client_id):
        """
        Extrae la configuración de self.config, la empaqueta en el formato
        JSON definido y la envía a través del websocket.
        """
        try:
            # 1. Convertimos el objeto ConfigParser a una cadena de texto (String)
            # Usamos StringIO para "engañar" al config.write y que escriba en memoria
            string_stream = io.StringIO()
            self.config.write(string_stream)
            ini_content = string_stream.getvalue()

            # 2. Preparamos el diccionario con tu estructura
            # El contenido del .ini va en el campo "text"
            payload = {
                "id": self.client_id,  # O self.client_id si lo tienes dinámico
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": self.msg_type_server[19],
                "text": ini_content
            }

            # 3. Convertimos el diccionario a una cadena JSON
            json_message = json.dumps(payload)

            # 4. Enviamos a través del websocket
            # Asumiendo que 'self.websocket' es tu conexión activa
            await self.websocket.send(json_message)

            print("--- Configuración enviada con éxito ---")
            print(ini_content)  # Esto te permite ver exactamente qué enviaste
            print("---------------------------------------")

        except Exception as e:
            print(f"Error al enviar la configuración: {e}")
    def save_config_file(self):
        """Escribe el estado actual de self.config en el archivo .ini"""
        with open(self.config_path, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    # Keyboard user input in console for test
    async def user_input(self):
        loop = asyncio.get_event_loop()
        while True:
            text = await loop.run_in_executor(None, input, "Mensaje ('exit' para salir): ")

            if text.lower() == "exit":
                await self.websocket_close()
                print("Conexión cerrada correctamente.")
                break

            elif text.lower() == "ping":
                print ("ping sending ...")
                await self.send_json("ping", "keepalive")
                continue

            elif text.lower() == "video_start":
                await self.start_video()
                continue

            elif text.lower() == "video_stop":
                await self.stop_video()
                continue

            elif text.lower() == "sos":
                await self.send_json(self.msg_type_server[1], "Emergency Call")

            else:
                await self.send_json(self.msg_type_server[1], text)
                print(f">>> Enviado: {text}")

    # Websocket close
    async def websocket_close(self):
        """
        Cierra de forma segura una conexión WebSocket y termina el script.
        Compatible con websockets.asyncio.client.ClientConnection.
        """
        try:
            if self.websocket is not None:
                print("Cerrando WebSocket...")

                # Try the close method...
                if hasattr(self.websocket, "close"):
                    close_method = self.websocket.close
                    if inspect.iscoroutinefunction(close_method):
                        await close_method()
                    else:
                        close_method()
                    await asyncio.sleep(0.1)
                    print("WebSocket cerrado correctamente.")
                else:
                    print("El objeto WebSocket no tiene método 'close'.")

            else:
                print("El WebSocket no está inicializado.")

        except Exception as e:
            print(f"Error al cerrar el WebSocket: {e}")
        finally:
            print("Finalizando script...")
            # Cancelar todas las tareas pendientes excepto esta
            for task in asyncio.all_tasks():
                if task is not asyncio.current_task():
                    task.cancel()
            self.output_json(id_str="---",status=False, server_message="", audio_stream=False, video_stream=False, only_text=False)
            await asyncio.sleep(0.3)
            sys.exit(0)

if __name__ == "__main__":
    # Leer client_id del primer argumento
    ext_client_id = sys.argv[1] if len(sys.argv) > 1 else None
    print (f"Client ID from argument: {ext_client_id}")
    client = WebSocketClient(ext_client_id)
    print(f"Iniciando cliente con ID: {client.client_id}")

    #client = WebSocketClient()
    try:
        asyncio.run(client.connect())
    except asyncio.CancelledError:
        pass
