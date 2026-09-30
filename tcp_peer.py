import json
import socket
import threading
import time


class TcpPeer:

  def __init__(self, port=5000, role="server", host="127.0.0.1"):
    self.port = port
    self.role = role  # "server" o "client"
    self.host = host
    self.conn = None
    self.running = True

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

      self.conn, addr = server_sock.accept()
      print(f"[DEBUG] ¡Conexión aceptada del cliente en {addr}!")
      self._listen_socket(on_message)
    except Exception as e:
      print(f"[DEBUG] Error crítico en _run_server: {e}")
    finally:
      server_sock.close()

  def _run_client(self, on_message):
    self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while self.running:
      try:
        print(f"[DEBUG] Intentando conectar al servidor en {self.host}:{self.port}...")
        self.conn.connect((self.host, self.port))
        print(f"[DEBUG] ¡Conectado exitosamente con el servidor!")
        break
      except ConnectionRefusedError:
        time.sleep(0.5)
      except Exception as e:
        print(f"[DEBUG] Error al intentar conectar: {e}")
        time.sleep(0.5)

    if self.running:
      self._listen_socket(on_message)

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

        # Decodificamos y acumulamos en el buffer (soluciona fragmentación TCP)
        chunk = data.decode("utf-8")
        buffer += chunk

        # Procesamos línea por línea (delimitadas por \n)
        while "\n" in buffer:
          line, buffer = buffer.split("\n", 1)
          if line.strip():
            packet = json.loads(line)
            msg = packet.get("message", "")
            on_message(msg)

      except json.JSONDecodeError as jde:
        print(f"[DEBUG] Error de JSON (datos corruptos o mezclados): {jde}")
      except ConnectionResetError:
        print("[DEBUG] Conexión reiniciada por la fuerza por el otro peer.")
        break
      except Exception as e:
        print(f"[DEBUG] Excepción inesperada en _listen_socket: {e}")
        break

    print("[DEBUG] Saliendo del bucle de escucha del socket.")

  def send(self, msg):
    """Envía datos por el mismo socket bidireccional"""
    if self.conn:
      threading.Thread(target=self._send_async, args=(msg,), daemon=True).start()
    else:
      print("[DEBUG] No se puede enviar: self.conn es None (no conectado).")

  def _send_async(self, msg):
    try:
      # Añadimos un salto de línea (\n) al final para delimitar el paquete en TCP
      packet = json.dumps({"message": msg}) + "\n"
      self.conn.sendall(packet.encode("utf-8"))
    except Exception as e:
      print(f"\n[DEBUG] Error al enviar mensaje por el socket: {e}")
      print("Tú: ", end="", flush=True)

  def close(self):
    print("[DEBUG] Cerrando conexión y apagando peer...")
    self.running = False
    if self.conn:
      try:
        self.conn.close()
      except:
        pass