# Use a pipeline as a high-level helper
from transformers import pipeline

pipe = pipeline("image-classification", model="maixbach/swin-tiny-patch4-window7-224-finetuned-trash_classification")