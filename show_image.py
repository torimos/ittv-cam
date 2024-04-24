import time
import RPi.GPIO as GPIO
import subprocess

def init_backlight():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(26, GPIO.OUT)

def set_backlight(state):
    GPIO.output(26, state == False);

def show_image(path):
    command = ['sudo', 'fbi', '-T', '1', '--noverbose', '-a', path]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running fbi: {e}")

image_path1 = 'assets/fallout-please-stand-by.jpg'
image_path2 = 'assets/FalloutShelterMenu.jpg'

show_image(image_path2)
init_backlight()
set_backlight(True)
time.sleep(3)
show_image(image_path1)
time.sleep(1)
