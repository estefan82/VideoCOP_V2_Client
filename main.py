import subprocess
import sys
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ws_script = os.path.join(BASE_DIR, "control-client.py")
ui_script = os.path.join(BASE_DIR, "ui-client.py")

ws_script = os.path.join(BASE_DIR, "control-client.exe")
ui_script = os.path.join(BASE_DIR, "ui-client.exe")

# Lista de client_ids
client_ids = ["A-113-local",
              "A-114-local",
              "A01",
              "A02",
              "A03",
              "A04",
              "A-115-local",
              "A-115",
              "A-113"]

client_id = ["A-113"]


# Lanzar n clientes websocket
ws_clients = []

# change client_id or client_ids

for cid in client_id:
    p = subprocess.Popen([sys.executable, ws_script, cid], cwd=BASE_DIR)
    ws_clients.append(p)

# Lanzar la UI (una sola instancia)
ui = subprocess.Popen([sys.executable, ui_script], cwd=BASE_DIR)
ui.wait()

print("Cerrando websockets...")
for p in ws_clients:
    p.terminate()