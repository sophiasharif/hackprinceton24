# Use a pipeline as a high-level helper
from transformers import pipeline
from PIL import Image

pipe = pipeline("image-classification", model="maixbach/swin-tiny-patch4-window7-224-finetuned-trash_classification")

# Load your image (replace with your image path)
image_path = "example_image.jpg"
image = Image.open(image_path)

# Use the pipeline to classify the image
results = pipe(image)

# Display the results
print(results)
