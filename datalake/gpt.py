import base64
import json
from openai import OpenAI

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
  
image_path = "../images/image1.jpg"

base64_image = encode_image(image_path)
client = OpenAI()

# completion = client.chat.completions.create(
#     model="gpt-4o-mini",
#     messages=[
#         {"role": "system", "content": "You are a helpful assistant."},
#         {
#             "role": "user",
#             "content": "Write a haiku about recursion in programming."
#         }
#     ]
# )

# print(completion.choices[0].message)
response = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Provide JSON-formatted metadata about the following image. Include 'is_recyclable' as a boolean, 'primary_colors' as an array of colors, and 'contains_text' as a boolean. Include just the JSON as a single string without extra formatting or explanation.",
        },
        {
          "type": "image_url",
          "image_url": {
            "url":  f"data:image/jpeg;base64,{base64_image}"
          },
        },
      ],
    }
  ],
)

metadata_json = response.choices[0].message.content.strip()
metadata = json.loads(metadata_json)  # Convert to Python dictionary
print(metadata)

