import cv2
import serial
import time
import numpy as np
from pynput import keyboard

# Initialize serial communication with Arduino
arduino = serial.Serial('/dev/cu.usbmodem101', 9600)
time.sleep(2)

# Load the pre-trained Haar Cascade classifier for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Initialize video capture from the default camera (usually 0)
cap = cv2.VideoCapture(0)

# Check if the camera opened successfully
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Get the frame dimensions
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Define regions for face position detection
center_x = frame_width // 2
center_y = frame_height // 2
threshold_x = frame_width // 6  # Horizontal threshold for left/right
threshold_y = frame_height // 6  # Vertical threshold for up/down
center_threshold = frame_width // 8  # Threshold for center detection

# State variable to track if the system is paused
paused = False

# Keyboard state management
key_states = {'q': False, 'c': False}

def on_press(key):
    try:
        k = key.char
        if k in key_states:
            key_states[k] = True
    except AttributeError:
        pass

def on_release(key):
    try:
        k = key.char
        if k in key_states:
            key_states[k] = False
    except AttributeError:
        pass

# Start the keyboard listener
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

try:
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        # Convert frame to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces in the frame
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        command = None
        if not paused and len(faces) > 0:
            # Get the first detected face
            (x, y, w, h) = faces[0]
            face_center_x = x + w // 2
            face_center_y = y + h // 2

            # Draw green rectangle around the face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Determine the command based on face position
            if abs(face_center_x - center_x) < center_threshold and abs(face_center_y - center_y) < center_threshold:
                command = 'E'
                print("Face centered: Sending E")
            elif face_center_x > center_x + threshold_x:
                command = 'D'
                print("Face right: Sending D")
            elif face_center_x < center_x - threshold_x:
                command = 'A'
                print("Face left: Sending A")
            elif face_center_y < center_y - threshold_y:
                command = 'W'
                print("Face up: Sending W")
            elif face_center_y > center_y + threshold_y:
                command = 'S'
                print("Face down: Sending S")

        # Draw a red circle at the center of the frame (target point)
        cv2.circle(frame, (center_x, center_y), 10, (0, 0, 255), 2)

        # Draw a red rectangle for the center threshold area
        top_left = (center_x - center_threshold, center_y - center_threshold)
        bottom_right = (center_x + center_threshold, center_y + center_threshold)
        cv2.rectangle(frame, top_left, bottom_right, (0, 0, 255), 1)

        # Display pause status on the frame
        status_text = "Paused" if paused else "Running"
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        # Send the command to Arduino if one was determined and not paused
        if command and not paused:
            arduino.write(command.encode())

        # Handle keyboard inputs
        if key_states['q'] and not paused:
            arduino.write('Q'.encode())  # Send stop command
            print("Paused: Sending Q to stop robot")
            paused = True
            key_states['q'] = False  # Reset to prevent repeated triggering
        elif key_states['c'] and paused:
            print("Resuming operation")
            paused = False
            key_states['c'] = False  # Reset to prevent repeated triggering

        # Display the frame with face detection and target visuals
        cv2.imshow('Face Detection with Target', frame)

        # Small delay to prevent excessive CPU usage
        time.sleep(0.05)

finally:
    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    arduino.close()
    listener.stop()