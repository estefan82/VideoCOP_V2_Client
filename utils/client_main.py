import subprocess
import sys
import os

# Detectar si está compilado
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ws_script = os.path.join(BASE_DIR, "control-client.exe")
ui_script = os.path.join(BASE_DIR, "ui-client.exe")

client_id = ["A-113"]

ws_clients = []

for cid in client_id:
    p = subprocess.Popen([ws_script, cid], cwd=BASE_DIR)
    ws_clients.append(p)

ui = subprocess.Popen([ui_script], cwd=BASE_DIR)
ui.wait()

print("Cerrando websockets...")
for p in ws_clients:
    p.terminate()