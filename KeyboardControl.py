import serial
import time
from pynput import keyboard

arduino = serial.Serial('/dev/cu.usbmodem101', 9600)
time.sleep(2)

key_states = {'d': False, 'a': False, 'w': False, 's': False, 'return': False}

def on_press(key):
    try:
        k = key.char
        if k in key_states:
            key_states[k] = True
    except AttributeError:
        if key == keyboard.Key.enter:
            key_states['return'] = True

def on_release(key):
    try:
        k = key.char
        if k in key_states:
            key_states[k] = False
    except AttributeError:
        if key == keyboard.Key.enter:
            key_states['return'] = False

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

while True:
    if key_states['d']:
        print("Pressed d")
        arduino.write('D'.encode())
    elif key_states['a']:
        print("Pressed a")
        arduino.write('A'.encode())
    elif key_states['w']:
        print("Pressed w")
        arduino.write('W'.encode())
    elif key_states['s']:
        print("Pressed s")
        arduino.write('S'.encode())
    elif key_states['return']:
        print("Pressed return")
        arduino.write('E'.encode())
    time.sleep(0.05)