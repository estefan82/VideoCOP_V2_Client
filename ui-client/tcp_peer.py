from collections import deque
import json
import socket
import threading
import time
import traceback


class TcpPeer:

  def __init__(self, port=5000, role="server", host="127.0.0.1", max_pending=100):
    self.port = port
    self.role = role  # "server" o "client"
    self.host = host
    self.conn = None
    self.running = True
    self.lock = threading.Lock()
    self.pending_messages = deque(
        maxlen=max_pending
    )  # Cola con límite para mensajes pendientes

  def start(self, on_message):
    """Inicia el hilo de red según el rol (servidor o cliente)"""
    if self.role == "server":
      threading.Thread(
          target=self._run_server, args=(on_message,), daemon=True
      ).start()
    else:
      threading.Thread(
          target=self._run_client, args=(on_message,), daemon=True
      ).start()

  def _run_server(self, on_message):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
      server_sock.bind((self.host, self.port))
      server_sock.listen(1)
      print(f"[DEBUG] Servidor escuchando en {self.host}:{self.port}...")

      while self.running:
        try:
          print(f"[DEBUG] Esperando conexión de cliente...")
          self.conn, addr = server_sock.accept()
          print(f"[DEBUG] ¡Conexión aceptada del cliente en {addr}!")

          self.flush_pending_messages()
          self._listen_socket(on_message)

        except Exception as e:
          print(f"[DEBUG] Error en la conexión actual del servidor: {e}")
        finally:
          if self.conn:
            try:
              self.conn.close()
            except:
              pass
            self.conn = None

    except Exception as e:
      print(f"[DEBUG] Error crítico en el socket servidor: {e}")
    finally:
      server_sock.close()

  def _run_client00(self, on_message):
    while self.running:
      try:
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"[DEBUG] Intentando conectar al servidor en {self.host}:{self.port}...")
        self.conn.connect((self.host, self.port))
        print(f"[DEBUG] ¡Conectado exitosamente con el servidor!")

        self.flush_pending_messages()
        self._listen_socket(on_message)

      except (ConnectionRefusedError, socket.error):
        print(
            "[DEBUG] Servidor no disponible o conexión perdida. Reintentando en"
            " 1s..."
        )
      except Exception as e:
        print(f"[DEBUG] Error inesperado en cliente: {e}")
      finally:
        if self.conn:
          try:
            self.conn.close()
          except:
            pass
          self.conn = None

      time.sleep(1.0)

  def _run_client(self, on_message):
    while self.running:
      sock = None
      try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"[DEBUG] Intentando conectar al servidor en {self.host}:{self.port}...")
        sock.connect((self.host, self.port))

        with self.lock:
          self.conn = sock

        print(f"[DEBUG] ¡Conectado exitosamente con el servidor!")
        self.flush_pending_messages()
        self._listen_socket(on_message)

      except (ConnectionRefusedError, socket.error):
        print("[DEBUG] Servidor no disponible o conexión perdida. Reintentando en 1s...")
        if sock:
          try:
            sock.close()
          except:
            pass
      except Exception as e:
        print(f"[DEBUG] Error inesperado en cliente: {e}")
        if sock:
          try:
            sock.close()
          except:
            pass
      finally:
        with self.lock:
          if self.conn:
            try:
              self.conn.close()
            except:
              pass
            self.conn = None

      time.sleep(1.0)

  def _listen_socket(self, on_message):
    buffer = ""
    while self.running:
      try:
        data = self.conn.recv(1024)
        if not data:
          print(
              "[DEBUG] El otro extremo cerró la conexión limpiamente (EOF recibido)."
          )
          break

        chunk = data.decode("utf-8")
        buffer += chunk

        while "\n" in buffer:
          line, buffer = buffer.split("\n", 1)
          if line.strip():
            # Parseamos el JSON completo
            packet = json.loads(line)
            # CORRECCIÓN: Pasamos el diccionario completo al callback
            # Si el remitente envió un dict, packet ya es el dict.
            # Si envió un texto simple empaquetado, packet será {"message": "texto"}
            on_message(packet)

      except json.JSONDecodeError as jde:
        print(f"[DEBUG] Error de JSON (datos corruptos o mezclados): {jde}")
      except ConnectionResetError:
        print("[DEBUG] Conexión reiniciada por la fuerza por el otro peer.")
        break
      except Exception as e:
        print(f"[DEBUG] Excepción inesperada en _listen_socket: {e}")
        break

    print("[DEBUG] Saliendo del bucle de escucha del socket actual.")

  def send(self, msg):
    """Envía datos (dict o string) o los encola si el socket aún no está conectado"""
    if self.conn:
      threading.Thread(target=self._send_async, args=(msg,), daemon=True).start()
    else:
      print(
          "[DEBUG] Socket no conectado aún. Mensaje guardado en cola (máx"
          f" {self.pending_messages.maxlen}MSGs)."
      )
      self.pending_messages.append(msg)

  def flush_pending_messages(self):
    """Envía todos los mensajes acumulados al establecer la conexión"""
    if self.pending_messages:
      print(
          f"[DEBUG] Vaciando cola: enviando {len(self.pending_messages)}"
          f" mensajes pendientes..."
      )
      while self.pending_messages:
        msg = self.pending_messages.popleft()
        threading.Thread(
            target=self._send_async, args=(msg,), daemon=True
        ).start()

  def _send_async00(self, msg):
    try:
      if self.conn:
        # Si pasas un diccionario, se envía tal cual. Si pasas un string, se envuelve.
        if isinstance(msg, dict):
          packet = json.dumps(msg) + "\n"
        else:
          packet = json.dumps({"message": msg}) + "\n"

        self.conn.sendall(packet.encode("utf-8"))
      else:
        print("\n[DEBUG] Intento de envío fallido: socket desconectado.")
    except Exception as e:
      print(f"\n[DEBUG] Error al enviar mensaje por el socket: {e}")
      print("Tú: ", end="", flush=True)

  def _send_async01(self, msg):
    with self.lock:
      current_conn = self.conn

    if current_conn:
      try:
        if isinstance(msg, dict):
          packet = json.dumps(msg) + "\n"
        else:
          packet = json.dumps({"message": msg}) + "\n"
        current_conn.sendall(packet.encode("utf-8"))
      except Exception as e:
        print(f"\n[DEBUG] Error al enviar mensaje, re-encolando: {e}")
        # Si falla el envío, devolvemos el mensaje a la cola para no perderlo
        self.pending_messages.appendleft(msg)
    else:
      print("\n[DEBUG] Socket desconectado. Guardando en cola.")
      self.pending_messages.append(msg)

  def _send_async02(self, msg):
    with self.lock:
      if self.conn:
        try:
          if isinstance(msg, dict):
            packet = json.dumps(msg) + "\n"
          else:
            packet = json.dumps({"message": msg}) + "\n"
          self.conn.sendall(packet.encode("utf-8"))
        except Exception as e:
          print(f"\n[DEBUG] Error al enviar mensaje, re-encolando: {e}")
          self.pending_messages.appendleft(msg)
      else:
        print("\n[DEBUG] Socket desconectado. Guardando en cola.")
        self.pending_messages.append(msg)

  def _send_async(self, msg):
    with self.lock:
      if self.conn:
        try:
          if isinstance(msg, dict):
            packet = json.dumps(msg) + "\n"
          else:
            packet = json.dumps({"message": msg}) + "\n"
          self.conn.sendall(packet.encode("utf-8"))
        except Exception as e:
          print(f"\n[DEBUG] Error al enviar mensaje por el socket: {e}")
          # --- AQUÍ AÑADIMOS EL TRACEBACK ---
          traceback.print_exc()
          # -----------------------------------
          self.pending_messages.appendleft(msg)
      else:
        print("\n[DEBUG] Socket desconectado. Guardando en cola.")
        self.pending_messages.append(msg)

  def close(self):
    print("[DEBUG] Cerrando conexión y apagando peer...")
    self.running = False
    if self.conn:
      try:
        self.conn.close()
      except:
        pass