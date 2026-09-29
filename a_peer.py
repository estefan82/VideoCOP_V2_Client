from udp_peer import UDPPeer

MY_PORT = 1001
TARGET_PORT = 1002

# Definimos aquí la función que gestiona el mensaje recibido
def manejar_mensaje_entrante(msg):
  print(f"\r[Otro]: {msg}")
  print("Tú: ", end="", flush=True)


# Pasamos la función al instanciar la clase
peer = UDPPeer(
    my_port=MY_PORT, target_port=TARGET_PORT, on_message=manejar_mensaje_entrante
)
peer.start_server()

print(f"[*] Peer UDP escuchando en puerto {MY_PORT}...")
print(f"[*] Enviando mensajes a puerto {TARGET_PORT}...")
print("--- Escribe 'salir' para terminar ---\n")

try:
  while True:
    texto = input("Tú: ")
    if not texto.strip():
      continue
    if texto.lower() == "salir":
      break

    # Si también quieres imprimir tu propio mensaje enviado desde aquí:
    print(f"\rTú: {texto}")
    peer.send(texto)

except KeyboardInterrupt:
  pass
finally:
  peer.close()
print("\n[*] Saliendo...")