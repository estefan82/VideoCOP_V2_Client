import os
import sys
import json
import configparser
import time
from time import sleep
from gpiozero import Button
from signal import pause

json_data = {}

# --- Detectar ruta base correctamente ---
if getattr(sys, 'frozen', False):
    # Si está ejecutándose como ejecutable PyInstaller
    base_path = os.path.dirname(sys.executable)
else:
    # Si está ejecutándose como script normal (python3)
    base_path = os.path.dirname(os.path.abspath(__file__))

# --- Construir rutas ---
config_path = os.path.join(base_path, "button-client.ini")
input_path = os.path.join(base_path, "input.json")

config = configparser.ConfigParser()
config.read(config_path)


# Configura los pines GPIO donde conectaste los botones
call_btn = Button(config.getint("setup", "call_btn_sw"))
yes_btn = Button(config.getint("setup", "yes_btn_sw"))
no_btn = Button(config.getint("setup", "no_btn_sw"))

# Define las funciones que se ejecutarán al presionar cada botón
def call_btn_fun():
    print("Button Call press")
    input_json(call=True)
    time.sleep(1)
    clean_input_json()

def yes_btn_fun():
    print("Button YES press")
    input_json(response="YES")
    time.sleep(1)
    clean_input_json()

def no_btn_fun():
    print("Button NO press")
    input_json(response="NO")
    time.sleep(1)
    clean_input_json()

def input_json(call=None, response=None):
    try:
        # Leer archivo existente si existe
        if os.path.exists(input_path):
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"call": "", "response": ""}

        # Actualizar solo los valores que no son None
        if call is not None:
            data["call"] = bool(call)
        if response is not None:
            data["response"] = response

        # Guardar cambios
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"[✓] input.json updated in {input_path}")
    except Exception as e:
        print(f"[!] Error updating input.json: {e}")

def clean_input_json():
    if os.path.exists(input_path):
        try:
            # Puedes dejarlo como un objeto vacío o con una estructura base
            with open(input_path, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)
            print(f"File {input_path} correctly cleaned")
        except Exception as e:
            print(f"Error cleaning input file: {e}")
    else:
        print(f"Input file  {input_path} not present.")

# Asocia las funciones a los botones
call_btn.when_pressed = call_btn_fun
yes_btn.when_pressed = yes_btn_fun
no_btn.when_pressed = no_btn_fun

# Mantiene el script corriendo
pause()
