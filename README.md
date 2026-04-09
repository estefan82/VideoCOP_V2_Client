# create Snapshot for the fresh installation of debian64
1. timeshift for snapshot, after debian64 installation
   sudo timeshift --create --comments "New installation"
   sudo timeshift --restore, in case needed

# Library for souddevice
2. pre venv library installation
  sudo apt update
  sudo apt install portaudio19-dev libportaudio2

# Create venv
3. python -m venv venv

# Activate venv
4. source venv/bin/activate

# install requirements
5. pip install -r requirements.txt

# Deactivate venv
6. deactivate
