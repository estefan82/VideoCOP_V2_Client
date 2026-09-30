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
    server_sock.bind((self.host, self.port))
    server_sock.listen(1)

    # Bloquea hasta que el otro script se conecte
    self.conn, _ = server_sock.accept()
    self._listen_socket(on_message)

  def _run_client(self, on_message):
    self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Reintenta conectar si el servidor aún no está encendido
    while self.running:
      try:
        self.conn.connect((self.host, self.port))
        break
      except ConnectionRefusedError:
        time.sleep(0.5)
    self._listen_socket(on_message)

  def _listen_socket(self, on_message):
    while self.running:
      try:
        data = self.conn.recv(1024)
        if not data:
          break
        packet = json.loads(data.decode("utf-8"))
        on_message(packet.get("message", ""))
      except Exception:
        break

  def send(self, msg):
    """Envía datos por el mismo socket bidireccional"""
    if self.conn:
      threading.Thread(target=self._send_async, args=(msg,), daemon=True).start()

  def _send_async(self, msg):
    try:
      packet = json.dumps({"message": msg}).encode("utf-8")
      self.conn.sendall(packet)
    except Exception:
      print("\n[-] Error al enviar mensaje.")
      print("Tú: ", end="", flush=True)

  def close(self):
    self.running = False
    if self.conn:
      try:
        self.conn.close()
      except:
        pass