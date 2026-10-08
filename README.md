# Create Snapshot for the fresh installation of debian64
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

# WM8960 Waveshare
git clone https://github.com/waveshare/WM8960-Audio-HAT
cd WM8960-Audio-HAT
sudo chmod +x install.sh
sudo ./install.sh 
sudo reboot

sudo dkms status

info: 
pi@raspberrypi:~ $ sudo dkms status 
wm8960-soundcard, 1.0, 4.19.58-v7l+, armv7l: installed

Check the Soundcard
Test playing：aplay -l
pi@raspberrypi:~ $ aplay -l
**** List of PLAYBACK Hardware Devices ****
card 0: wm8960soundcard [wm8960-soundcard], device 0: bcm2835-i2s-wm8960-hifi wm8960-hifi-0 []
  Subdevices: 1/1
  Subdevice #0: subdevice #0
Test recording：arecord -l
pi@raspberrypi:~ $ arecord -l
**** List of CAPTURE Hardware Devices ****
card 0: wm8960soundcard [wm8960-soundcard], device 0: bcm2835-i2s-wm8960-hifi wm8960-hifi-0 []
  Subdevices: 1/1
  Subdevice #0: subdevice #0
Test record/play
Record & Play
sudo arecord -f cd -Dhw:0 | aplay -Dhw:0

