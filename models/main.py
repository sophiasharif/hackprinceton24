# Use a pipeline as a high-level helper
from dataclasses import dataclass
from enum import Enum
from transformers import pipeline
from PIL import Image

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

# Test to find possible outputs of model
# pipes = {name: pipeline("image-classification", model=model_id) for name, model_id in MODELS.items()}
# print(pipes["trash2"]("image1.png"))


class Model:
    def __init__(self, model_id, class_to_label_map):
        self.pipe = pipeline("image-classification", model=model_id)
        self.class_to_label_map = class_to_label_map
    
    def classify(self, image_path):
        image = Image.open(image_path)
        results = self.pipe(image)
        print(results)
        label = self.class_to_label_map[results[0]["label"]]
        return label

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

print(trash2.classify("image1.png"))

