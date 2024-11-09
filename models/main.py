# Use a pipeline as a high-level helper
from transformers import pipeline
from PIL import Image

# Available models 
MODELS = {
    "trash1": "maixbach/swin-tiny-patch4-window7-224-finetuned-trash_classification",
    "trash2": "edwinpalegre/ee8225-group4-vit-trashnet-enhanced"
}
pipes = {name: pipeline("image-classification", model=model_id) for name, model_id in MODELS.items()}

pipe = pipes["trash1"]

# load image
image_path = "image1.png"
image = Image.open(image_path)

# classify
results = pipe(image)
print(results)
