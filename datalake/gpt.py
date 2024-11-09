import base64
import json
from openai import OpenAI

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
  

def get_metadata(filename):
    image_path = f"../images/{filename}"
    base64_image = encode_image(image_path)
    client = OpenAI()

    # print(completion.choices[0].message)
    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": "Provide JSON-formatted metadata about the following image. Include 'is_recyclable', 'is_compostable', and 'is_metal' as booleans; 'brand' as a string if applicable, but otherwise the empty string; and a 'description' field with a 3-8 word description of the item. Include just the JSON as a single string without extra formatting or explanation.",
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
    metadata = json.loads(metadata_json)
    return metadata


print(get_metadata("image2.jpg"))