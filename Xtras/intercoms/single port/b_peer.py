from tcp_peer import TcpPeer

PORT = 5000

def manejar_mensaje(msg):
  print(f"\r[Otro]: {msg}")
  print("Tú: ", end="", flush=True)


# Este actúa de cliente y se conecta al puerto del servidor
peer = TcpPeer(port=PORT, role="client")
peer.start(on_message=manejar_mensaje)

print(f"[*] Conectándose al servidor TCP en puerto {PORT}...")
print("--- Escribe 'salir' para terminar ---\n")

try:
  while True:
    texto = input("Tú: ")
    if not texto.strip():
      continue
    if texto.lower() == "salir":
      break

    print(f"\rTú: {texto}")
    peer.send(texto)

except KeyboardInterrupt:
  pass
finally:
  peer.close()
print("\n[*] Saliendo...")