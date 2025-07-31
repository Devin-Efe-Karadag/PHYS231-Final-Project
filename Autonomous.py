import cv2
import serial
import time
import numpy as np
from pynput import keyboard
from ultralytics import YOLO

# Initialize serial communication with Arduino
arduino = serial.Serial('/dev/cu.usbmodem101', 9600)
time.sleep(2)

# Load the pre-trained YOLOv8 face detection model
model = YOLO("yolov8n-face.pt")  # Ensure yolov8n-face.pt is available or downloaded

# Function to initialize the camera
def initialize_camera(preferred_index=1, max_attempts=4):
    # Try the preferred index first
    cap = cv2.VideoCapture(preferred_index)
    if cap.isOpened():
        print(f"Successfully opened camera at index {preferred_index}")
        return cap, preferred_index
    
    # If preferred index fails, try other indices
    print(f"Failed to open camera at index {preferred_index}. Trying other indices...")
    for index in range(max_attempts):
        if index != preferred_index:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                print(f"Successfully opened camera at index {index}")
                return cap, index
            cap.release()
    
    # If no camera is found, exit
    print("Error: Could not open any camera.")
    exit()

# Initialize video capture from USB camera (try index 1 first)
cap, camera_index = initialize_camera(preferred_index=1)

# Get the frame dimensions
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Define regions for face position detection
center_x = frame_width // 2
center_y = frame_height // 2
threshold_x = frame_width // 6  # Horizontal threshold for left/right
threshold_y = frame_height // 6  # Vertical threshold for up/down
center_threshold = frame_width // 8  # Threshold for center detection
min_face_size = 100  # Minimum face size (width and height) for confidence
confidence_threshold = 0.5  # Minimum confidence score for YOLO detection

# State variables
paused = False
exit_program = False
face_detected_count = 0  # Counter for consecutive face detections
required_frames = 5  # Number of frames to confirm a target
direction_commands = ['A', 'D', 'W', 'S']  # Ordered direction commands
current_direction_index = 0  # Index for cycling through directions
last_direction_change = time.time()  # Time of last direction change
direction_duration = 4.0  # Duration to hold each direction (seconds)

# Keyboard state management
key_states = {'q': False, 'c': False, 'f': False}

def on_press(key):
    global exit_program
    try:
        k = key.char
        if k in key_states:
            key_states[k] = True
        if k == 'f':
            print("Exit key pressed")
            exit_program = True
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
    while not exit_program:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        # Perform YOLOv8 face detection
        results = model(frame, conf=confidence_threshold, verbose=False)
        command = None
        faces_detected = False
        if not paused:
            # Process YOLO detections
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    confidence = box.conf.item()
                    if confidence > confidence_threshold:
                        # Extract bounding box coordinates
                        xyxy = box.xyxy[0].cpu().numpy()
                        x, y, x2, y2 = map(int, xyxy)
                        face_width = x2 - x
                        face_height = y2 - y

                        # Check minimum face size
                        if face_width >= min_face_size and face_height >= min_face_size:
                            faces_detected = True
                            face_center_x = x + face_width // 2
                            face_center_y = y + face_height // 2

                            # Draw green rectangle around the face
                            cv2.rectangle(frame, (x, y), (x2, y2), (0, 255, 0), 2)

                            # Increment face detection counter
                            face_detected_count += 1

                            # Determine the command based on face position
                            if face_detected_count >= required_frames:
                                # Check if face is centered for shooting
                                if abs(face_center_x - center_x) < center_threshold and abs(face_center_y - center_y) < center_threshold:
                                    command = 'E'
                                    print(f"Face centered after {face_detected_count} frames (confidence: {confidence:.2f}): Sending E")
                                    face_detected_count = 0  # Reset counter after shooting
                                else:
                                    # Send direction commands to align face
                                    if face_center_x > center_x + threshold_x:
                                        command = 'D'
                                        print(f"Face right (confidence: {confidence:.2f}): Sending D")
                                    elif face_center_x < center_x - threshold_x:
                                        command = 'A'
                                        print(f"Face left (confidence: {confidence:.2f}): Sending A")
                                    elif face_center_y < center_y - threshold_y:
                                        command = 'W'
                                        print(f"Face up (confidence: {confidence:.2f}): Sending W")
                                    elif face_center_y > center_y + threshold_y:
                                        command = 'S'
                                        print(f"Face down (confidence: {confidence:.2f}): Sending S")
                            else:
                                # Send direction commands to align face while building confidence
                                if face_center_x > center_x + threshold_x:
                                    command = 'D'
                                    print(f"Face right ({face_detected_count}/{required_frames}, confidence: {confidence:.2f}): Sending D")
                                elif face_center_x < center_x - threshold_x:
                                    command = 'A'
                                    print(f"Face left ({face_detected_count}/{required_frames}, confidence: {confidence:.2f}): Sending A")
                                elif face_center_y < center_y - threshold_y:
                                    command = 'W'
                                    print(f"Face up ({face_detected_count}/{required_frames}, confidence: {confidence:.2f}): Sending W")
                                elif face_center_y > center_y + threshold_y:
                                    command = 'S'
                                    print(f"Face down ({face_detected_count}/{required_frames}, confidence: {confidence:.2f}): Sending S")
                            break  # Process only the first valid face
                if faces_detected:
                    break  # Exit outer loop if a valid face is found

            if not faces_detected:
                # No face detected: reset counter and cycle through directions
                face_detected_count = 0
                current_time = time.time()
                if current_time - last_direction_change >= direction_duration:
                    # Move to the next direction
                    current_direction_index = (current_direction_index + 1) % len(direction_commands)
                    last_direction_change = current_time
                    print(f"No face detected: Switching to direction {direction_commands[current_direction_index]}")
                command = direction_commands[current_direction_index]
                print(f"No face detected: Sending direction {command}")

        # Draw a red circle at the center of the frame (target point)
        cv2.circle(frame, (center_x, center_y), 10, (0, 0, 255), 2)

        # Draw a red rectangle for the center threshold area
        top_left = (center_x - center_threshold, center_y - center_threshold)
        bottom_right = (center_x + center_threshold, center_y + center_threshold)
        cv2.rectangle(frame, top_left, bottom_right, (0, 0, 255), 1)

        # Display pause status, detection count, and current direction on the frame
        status_text = "Paused" if paused else f"Running (Detections: {face_detected_count}/{required_frames}, Dir: {command})"
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        # Send the command to Arduino if one was determined and not paused
        if command and not paused:
            arduino.write(command.encode())
            arduino.flush()  # Ensure command is sent immediately

        # Handle keyboard inputs
        if key_states['q'] and not paused:
            arduino.write('Q'.encode())
            arduino.flush()
            print("Paused: Sending Q to stop robot")
            paused = True
            key_states['q'] = False
        elif key_states['c'] and paused:
            print("Resuming operation")
            paused = False
            key_states['c'] = False

        # Display the frame with face detection and target visuals
        cv2.imshow('Face Detection with Target', frame)
        
        # Check for 'f' key press through OpenCV window
        key = cv2.waitKey(1) & 0xFF
        if key == ord('f'):
            print("Exit key pressed (through OpenCV)")
            exit_program = True

        # Small delay to prevent excessive CPU usage
        time.sleep(0.05)

finally:
    print("Cleaning up resources...")
    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    arduino.close()
    listener.stop()
    print("Program terminated.")