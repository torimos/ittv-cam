import asyncio
import requests
import subprocess
import time
from datetime import datetime
import os
import RPi.GPIO as GPIO
from evdev import InputDevice, ecodes, categorize, list_devices
import pygame.mixer

#sys.exit(1)

#su pi -c '/usr/bin/python /home/pi/main.py'
global vlc_path
global file_path
vlc_path = "/usr/bin/cvlc"
file_path = "/home/pi/camera.m3u"

def play_mp3(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    pygame.mixer.music.set_volume(0.6)
    #while pygame.mixer.music.get_busy():
    #    time.sleep(1)


def is_cnx_active(timeout):
    try:
        requests.head("http://www.google.com/", timeout=timeout)
        return True
    except requests.ConnectionError:
        return False

def wait_for_net():
    while True:
        if is_cnx_active(300) is True:
            print("The internet connection is active")
            break
        else:
            pass

def init_backlight():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(26, GPIO.OUT)

def set_backlight(state):
    GPIO.output(26, state == False);

def download_m3u(fname, login, password, compact = 0):
    base_url = os.environ.get('CAM_URL')
    url_path = "/stat/index.php?p=camera&stream=1&camera_id=1605"
    if compact:
        url_path = url_path + "&sec=1"
    print("Downloading to " + fname + " from " + url_path)
    response = requests.post(base_url, data = {"action":"auth_request", "U":url_path, "L":login, "P":password})
    if response.status_code == 200:
        if response.headers["content-type"] == "audio/x-mpegurl":
            print(response.headers["content-disposition"]) #'inline; filename=camera.m3u'
            print(response.headers["content-transfer-encoding"]) #binary
            print(response.headers["content-length"]) #128
            print(response.headers["content-type"]) #'audio/x-mpegurl'
            print(response.text)
            m3u_file = open(fname, "w")
            m3u_file.write(response.text)
            m3u_file.close()

async def start_subprocess(is_test = 0):
    if is_test:
        proc = subprocess.Popen([
            str(vlc_path), str("/home/pi/samples/sample.avi"),
            '-I', 'dummy',  # Use dummy interface
            '--aout', 'dummy',
            '--no-dbus',
            '--no-osd',  # Disable on-screen display
            '--no-xlib',  # In case VLC tries to use X
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:  
        if os.path.isfile(file_path) == False or time.time()-os.path.getmtime(file_path) >= 2340:
            download_m3u(file_path, os.environ.get('CAM_ID'), os.environ.get('CAM_KEY'))
        print("Opening " + file_path)
        proc = subprocess.Popen([
            str(vlc_path), str(file_path),
            '-I', 'dummy',  # Use dummy interface
            '--aout', 'dummy',
            '--no-dbus',
            '--no-osd',  # Disable on-screen display
            '--no-xlib',  # In case VLC tries to use X
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.system('clear')
    print("Loading camera stream...")
    set_backlight(True)
    await asyncio.sleep(3)
    print("Stream ready")
    return proc

def find_device_by_name(name):
    devices = [InputDevice(path) for path in list_devices()]
    for device in devices:
        if device.name == name:
            print(f"Device '{name}' found at '{device.path}'")
            return device.path
    print(f"Device '{name}' not found")
    return None

async def read_input_device(queue, device_path):
    device = InputDevice(device_path)
    print(f"Listening to device: {device.name}")
    last_event_time = 0
    while True:
        async for input_event in device.async_read_loop():
            if input_event.type == ecodes.EV_KEY and input_event.code == ecodes.BTN_TOUCH:
                key_event = categorize(input_event)
                if key_event.keystate == key_event.key_down:
                    time_diff = time.time()-last_event_time
                    print(f"[{time.time()}] {key_event.keycode} released. Last event timediff: {time_diff}")
                    await queue.put((1,time_diff))
                    last_event_time = time.time()

async def monitor_task(queue, timeout = 60*5):
    proc = None
    start_time = time.time()
    while True:
        #print(f"[{time.time()}] State: {proc}")
        e = 0
        if queue.qsize()>0:
            if (queue.qsize()==2):
                queue.get()
            e, td = await queue.get()
        if proc == None:
            if e == 1:
                print(f"[{time.time()}] Starting process")
                play_mp3("assets/cam_on.mp3")
                proc = await start_subprocess()
                start_time = time.time()
        elif time.time() - start_time > timeout or (e == 1 and td < 0.2):
            if td < 0.2:
                print(f"[{time.time()}] Double touch event, terminating the process")
            else:
                print(f"[{time.time()}] Timeout reached without touch event, terminating the process")
            set_backlight(False)
            play_mp3("assets/cam_off.mp3")
            proc.terminate()
            proc = None
        else:
            if e == 1:
                print(f"[{time.time()}] Restarting timer")
                start_time = time.time()
            print(f"{timeout - int(time.time() - start_time)}")
        await asyncio.sleep(1)


# Asyncio main function
async def main():
    init_backlight()
    set_backlight(False)
    wait_for_net()
    device_path = find_device_by_name("WaveShare WaveShare Touchscreen")
    if device_path != None:
        queue = asyncio.Queue()
        device_task = asyncio.create_task(read_input_device(queue, device_path))
        another_task_instance = asyncio.create_task(monitor_task(queue))
        # Wait for tasks to complete (they won't in this example, as they loop indefinitely)
        await asyncio.gather(device_task, another_task_instance)

# Run the asynchronous main function
asyncio.run(main())
