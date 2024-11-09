# Use a pipeline as a high-level helper
from dataclasses import dataclass
from enum import Enum
from transformers import pipeline
from PIL import Image
import cv2
import numpy as np
import time
import os
import serial
import serial.tools.list_ports

class Disposable(Enum):
    RECYCLE = 0
    COMPOST = 1
    TRASH = 2

class Metal(Enum):
    RECYCLE = 0
    METAL = 1
    TRASH = 2

# Available models 
MODELS = {
    "trash1": "maixbach/swin-tiny-patch4-window7-224-finetuned-trash_classification",
    "trash2": "edwinpalegre/ee8225-group4-vit-trashnet-enhanced"
}

class Model:
    def __init__(self, model_id, class_to_label_map):
        self.pipe = pipeline("image-classification", model=model_id)
        self.class_to_label_map = class_to_label_map
        self.arduino_connected = self.connect_arduino()
        if self.arduino_connected:
            self.test_motors()  # Test all motors on startup
    
    def connect_arduino(self):
        # List all available ports
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            print("No ports found!")
            return False
            
        print("\nAvailable ports:")
        for i, port in enumerate(ports):
            print(f"{i}: {port.device} - {port.description}")
            
        try:
            selection = int(input("\nSelect port number: "))
            if 0 <= selection < len(ports):
                self.arduino = serial.Serial(ports[selection].device, 9600, timeout=1)
                time.sleep(2)  # Wait for Arduino to initialize
                print("Successfully connected to Arduino")
                return True
        except (ValueError, IndexError, serial.SerialException) as e:
            print(f"Error connecting to Arduino: {str(e)}")
            
        return False
    
    def test_motors(self):
        """Test all motors to identify their functions"""
        print("\nTesting all motors...")
        if self.arduino_connected:
            try:
                # Test each gate position
                for gate in ['0', '1', '2']:
                    print(f"\nTesting gate position {gate}")
                    self.arduino.write(gate.encode())
                    time.sleep(2)
                
                # Test string controls
                print("\nTesting string forward (+)")
                self.arduino.write(b'+')
                time.sleep(2)
                self.arduino.write(b'/')  # Stop
                
                print("Testing string reverse (-)")
                self.arduino.write(b'-')
                time.sleep(2)
                self.arduino.write(b'/')  # Stop
                
                print("Motor testing complete!")
                
            except Exception as e:
                print(f"Error during motor testing: {e}")
    
    def classify(self, image):
        if isinstance(image, str):
            image = Image.open(image)
        elif isinstance(image, np.ndarray):
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
            
        results = self.pipe(image)
        print(results)
        label = self.class_to_label_map[results[0]["label"]]
        
        # Only try to communicate with Arduino if it's connected
        if self.arduino_connected:
            print(f"Sending to {label}")
            if label == Disposable.RECYCLE:
                self.run_motors('0')  # Send to recycle gate
            elif label == Disposable.COMPOST:
                self.run_motors('1')  # Send to compost gate
            elif label == Disposable.TRASH:
                self.run_motors('2')  # Send to trash gate
        
        return label

    def run_motors(self, command):
        """Run motors for sorting sequence"""
        if self.arduino_connected:
            try:
                # Send the gate command (0, 1, or 2)
                self.arduino.write(command.encode())
                time.sleep(2)  # Wait for gates to position
                
                # Let out string
                self.arduino.write(b'+')
                time.sleep(3)  # Let string run for 3 seconds
                
                # Stop string
                self.arduino.write(b'/')
                time.sleep(1)  # Brief pause
                
                # Pull string back in
                self.arduino.write(b'-')
                time.sleep(3)  # Pull string for 3 seconds
                
                # Stop string
                self.arduino.write(b'/')
                
            except Exception as e:
                print(f"Error controlling motors: {e}")

class WebcamClassifier:
    def __init__(self, model, camera_index=1, save_dir="captured_images"):
        self.model = model
        self.save_dir = save_dir
        self.camera_index = camera_index
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
    def start(self):
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise IOError(f"Cannot open camera at index {self.camera_index}")
            
        print("Webcam active. Press 'k' to classify current frame, 'q' to quit")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Show the frame
            cv2.imshow('Webcam', frame)
            
            # Check for keypress
            key = cv2.waitKey(1)
            if key == ord('k'):
                # Save image and classify
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                save_path = os.path.join(self.save_dir, f"capture_{timestamp}.jpg")
                cv2.imwrite(save_path, frame)
                
                # Classify the frame
                result = self.model.classify(frame)
                print(f"Classification result: {result}")
                
            elif key == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()

# Initialize models
trash1 = Model(MODELS["trash1"], {
    'Paper': Disposable.RECYCLE,
    'Other': Disposable.TRASH,
    'Plastic': Disposable.RECYCLE,
    'G_M': Disposable.RECYCLE,
    'Organic': Disposable.COMPOST,
})

trash2 = Model(MODELS["trash2"], {
    'paper': Metal.RECYCLE,
    'cardboard': Metal.RECYCLE,
    'plastic': Metal.RECYCLE,
    'trash': Metal.TRASH,
    'metal': Metal.METAL,
})

# Start webcam classifier with trash2 model
classifier = WebcamClassifier(trash1)
classifier.start()