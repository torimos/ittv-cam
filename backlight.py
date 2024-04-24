import sys
import RPi.GPIO as GPIO

def init_backlight():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(26, GPIO.OUT)

def set_backlight(state):
    GPIO.output(26, state == False);


if (len(sys.argv) > 0):
    init_backlight()
    set_backlight(sys.argv[1] == "1")