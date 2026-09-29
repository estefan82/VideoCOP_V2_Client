import json
import socket
import threading


class UDPPeer:

  def __init__(self, my_port, target_port, on_message=None):
    self.my_port = my_port
    self.target_port = target_port
    self.on_message = on_message  # <- Guardamos la función callback
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.sock.bind(("127.0.0.1", self.my_port))
    self.running = True

  def start_server(self):
    threading.Thread(target=self._receive_loop, daemon=True).start()

  def _receive_loop(self):
    while self.running:
      try:
        data, addr = self.sock.recvfrom(1024)
        packet = json.loads(data.decode("utf-8"))
        msg = packet.get("message", "")

        # Si el usuario definió una función callback, la ejecutamos pasándole el mensaje
        if self.on_message:
          self.on_message(msg)

      except Exception:
        break

  def send(self, msg):
    threading.Thread(target=self._send_async, args=(msg,), daemon=True).start()

  def _send_async(self, msg):
    packet = json.dumps({"message": msg}).encode("utf-8")
    try:
      self.sock.sendto(packet, ("127.0.0.1", self.target_port))
    except Exception:
      print("\n[-] Error al enviar mensaje.")
      print("Tú: ", end="", flush=True)

  def close(self):
    self.running = False
    self.sock.close()