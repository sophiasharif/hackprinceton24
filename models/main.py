# Use a pipeline as a high-level helper
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from transformers import pipeline
from PIL import Image
import cv2
import numpy as np
import time
import os
import serial
import serial.tools.list_ports
import torch

class Disposable(Enum):
    RECYCLE = 0
    COMPOST = 1
    TRASH = 2

class Metal(Enum):
    RECYCLE = 0
    METAL = 1
    TRASH = 2

class Fruits(Enum):
    QUICK_COMPOST = 0
    SLOW_COMPOST = 1
    REUSEABLE = 2

# Available models 
MODELS = {
    "trash1": "maixbach/swin-tiny-patch4-window7-224-finetuned-trash_classification",
    "trash2": "edwinpalegre/ee8225-group4-vit-trashnet-enhanced",
    "fruits": "jazzmacedo/fruits-and-vegetables-detector-36",
}

def try_connect_arduino() -> Optional[serial.Serial]:
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No ports found!")
        return None
    
    print("\nAvailable ports:")
    for i, port in enumerate(ports):
        print(f"{i}: {port.device} - {port.description}")

    try:
        selection = int(input("\nSelect port number: "))
        if 0 <= selection < len(ports):
            arduino = serial.Serial(ports[selection].device, 9600, timeout=1)
            time.sleep(2)  # Wait for Arduino to initialize
            print("Successfully connected to Arduino")
            return arduino
    except (ValueError, IndexError, serial.SerialException) as e:
        print(f"Error connecting to Arduino: {str(e)}")
        return None

def test_arduino_motors(arduino: serial.Serial):
    """Test all motors to identify their functions"""
    print("\nTesting all motors...")
    try:
        # Test each gate position
        for gate in ['0', '1', '2']:
            print(f"\nTesting gate position {gate}")
            arduino.write(gate.encode())
            time.sleep(2)
            
        # Test string controls
        print("\nTesting string forward (+)")
        arduino.write(b'+')
        time.sleep(2)
        arduino.write(b'/')  # Stop
        
        print("Testing string reverse (-)")
        arduino.write(b'-')
        time.sleep(2)
        arduino.write(b'/')  # Stop
        
        print("Motor testing complete!")
            
    except Exception as e:
        print(f"Error during motor testing: {e}")
    

class ArduinoController:
    def __init__(self):
        self.arduino = try_connect_arduino()
        if self.arduino:
            self.test_motors()
    
    def test_motors(self):
        test_arduino_motors(self.arduino)
    
    def run_motors(self, category_value: int):
        """Run motors for sorting sequence"""
        if not self.arduino:
            return
            
        try:
            # Send the gate command (0, 1, or 2)
            self.arduino.write(str(category_value).encode())
            time.sleep(2)  # Wait for gates to position
            
            # Let out string
            self.arduino.write(b'+')
            time.sleep(3)
            self.arduino.write(b'/')
            time.sleep(1)
            
            # Pull string back in
            self.arduino.write(b'-')
            time.sleep(3)
            self.arduino.write(b'/')
            
        except Exception as e:
            print(f"Error controlling motors: {e}")

class Model:
    def __init__(self, model_id, class_to_label_map, arduino_controller=None):
        self.pipe = pipeline("image-classification", model=model_id, device="cuda" if torch.cuda.is_available() else "cpu")
        self.class_to_label_map = class_to_label_map
        # self.arduino_controller = arduino_controller
    
    def classify(self, image, return_all=False):
        if isinstance(image, str):
            image = Image.open(image)
        elif isinstance(image, np.ndarray):
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
            
        results = self.pipe(image, top_k=None)  # Get all possible classifications
        print(results)
        
        if return_all:
            # Return all classifications with their mapped categories and scores
            return [(self.class_to_label_map.get(r["label"], None), r["label"], r["score"]) 
                   for r in results 
                   if r["label"] in self.class_to_label_map]
        
        # Original behavior - just return top result
        label = self.class_to_label_map[results[0]["label"]]
        
        # if self.arduino_controller:
        #     print(f"Sending to {label}")
        #     self.arduino_controller.run_motors(label.value)
        
        return label

# Initialize Arduino controller (can be shared between models)
# arduino_controller = ArduinoController()

# Initialize models
trash1 = Model(
    MODELS["trash1"], 
    {
        'Paper': Disposable.RECYCLE,
        'Other': Disposable.TRASH,
        'Plastic': Disposable.RECYCLE,
        'G_M': Disposable.RECYCLE,
        'Organic': Disposable.COMPOST,
    }
    # arduino_controller
)

trash2 = Model(
    MODELS["trash2"], 
    {
        'paper': Metal.RECYCLE,
        'cardboard': Metal.RECYCLE,
        'plastic': Metal.RECYCLE,
        'trash': Metal.TRASH,
        'metal': Metal.METAL,
    }
    # arduino_controller
)

fruits = Model(
    MODELS["fruits"],
    {
        #Quick compost: Soft, moist items that break down quickly
        # Slow compost: Dense, starchy, or fibrous items that take longer to break down
        # Reuseable: Items that can be replanted or have valuable seeds
        
        # Quick composting items (soft, moist items that break down quickly)
        **{fruit: Fruits.QUICK_COMPOST for fruit in [
            'banana', 'spinach', 'lettuce', 'cabbage', 'peas', 'cucumber', 'tomato',
            'bellpepper', 'chilipepper', 'jalepeno', 'capsicum', 'paprika',
            'radish', 'turnip', 'grapes', 'kiwi', 'apple', 'pear', 'watermelon', 'soybean'
        ]},
        # Slow composting items (dense, starchy, or fibrous items that take longer to break down)
        **{fruit: Fruits.SLOW_COMPOST for fruit in [
            'corn', 'sweetcorn', 'cauliflower', 'eggplant', 'potato', 'sweetpotato',
            'onion', 'garlic', 'beetroot', 'carrot'
        ]},
        # Reuseable items (items that can be replanted or have valuable seeds)
        **{fruit: Fruits.REUSEABLE for fruit in [
            'pineapple', 'mango', 'ginger', 'lemon', 'orange', 'pomegranate'
        ]}
    }
    # arduino_controller
)

# class WebcamClassifier:
#     def __init__(self, model, camera_index=1, save_dir="captured_images"):
#         self.model = model
#         self.save_dir = save_dir
#         self.camera_index = camera_index
#         if not os.path.exists(save_dir):
#             os.makedirs(save_dir)
            
#     def start(self):
#         cap = cv2.VideoCapture(self.camera_index)
#         if not cap.isOpened():
#             raise IOError(f"Cannot open camera at index {self.camera_index}")
            
#         print("Webcam active. Press 'k' to classify current frame, 'q' to quit")
        
#         while True:
#             ret, frame = cap.read()
#             if not ret:
#                 break
                
#             # Show the frame
#             cv2.imshow('Webcam', frame)
            
#             # Check for keypress
#             key = cv2.waitKey(1)
#             if key == ord('k'):
#                 # Save image and classify
#                 timestamp = time.strftime("%Y%m%d-%H%M%S")
#                 save_path = os.path.join(self.save_dir, f"capture_{timestamp}.jpg")
#                 cv2.imwrite(save_path, frame)
                
#                 # Classify the frame
#                 result = self.model.classify(frame)
#                 print(f"Classification result: {result}")
                
#             elif key == ord('q'):
#                 break
                
#         cap.release()
#         cv2.destroyAllWindows()

# # Start webcam classifier with trash2 model
# classifier = WebcamClassifier(fruits)
# classifier.start()
