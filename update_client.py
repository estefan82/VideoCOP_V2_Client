import paramiko
from pathlib import Path

def actualizar_cliente_raspi():
    # --- CONFIGURACIÓN ---
    host = "raspi5.local"
    usuario = "admin"
    password = "1234"
    directorio_destino = "/home/admin/videocop/"
    nombre_archivo = "control-client.py"

    # --- LOCALIZACIÓN LOCAL ---
    directorio_script = Path(__file__).parent.absolute()
    archivo_origen = directorio_script / nombre_archivo

    # Si no está en la carpeta del script, buscar en el CWD (donde PyCharm ejecuta)
    if not archivo_origen.exists():
        archivo_origen = Path.cwd() / nombre_archivo

    if not archivo_origen.exists():
        print(f"❌ Error: No se encuentra localmente '{nombre_archivo}'")
        return

    try:
        # 1. Conexión SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        print(f"📡 Conectando a {usuario}@{host}...")
        ssh.connect(hostname=host, username=usuario, password=password)

        # 2. Iniciar SFTP
        sftp = ssh.open_sftp()
        ruta_remota = f"{directorio_destino}{nombre_archivo}".replace('\\', '/')

        # --- BORRADO EN DESTINO SI EXISTE ---
        try:
            sftp.stat(ruta_remota)  # Verifica si el archivo existe
            print(f"🗑️  El archivo ya existe en la Raspi. Borrando antes de actualizar...")
            sftp.remove(ruta_remota)
        except IOError:
            # Si sftp.stat falla, es que el archivo no existe, no hacemos nada
            print(f"ℹ️  El archivo no existe en el destino. Procediendo con subida limpia.")

        # 3. Subir el nuevo archivo
        print(f"🚀 Enviando nuevo '{nombre_archivo}'...")
        sftp.put(str(archivo_origen), ruta_remota)

        sftp.close()
        ssh.close()

        print("---------------------------------------")
        print("✅ ¡Proceso terminado con éxito en la Raspberry!")

    except Exception as e:
        print("---------------------------------------")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    actualizar_cliente_raspi()