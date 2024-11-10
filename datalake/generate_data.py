import json
from datetime import datetime, timedelta
import random

# Define the parameters for data generation
brands = ["Amazon", "Walmart", "Apple", "Nike", "Starbucks", "Other"]
brand_weights = [0.5, 0.2, 0.1, 0.05, 0.1, 0.05]  # Adjusted weights to make Amazon create more waste

cities = [("San Francisco", "CA"), ("New York", "NY"), ("Los Angeles", "CA"), ("Austin", "TX"), ("Chicago", "IL"), ("Princeton", "NJ")]
descriptions = ["cardboard box", "plastic cup", "aluminum can", "paper bag", "plastic bottle"]
waste_types = ["compostable", "recyclable", "trash"]

# Define the time range for waste items (e.g., the past week)
start_time = datetime.now() - timedelta(days=7)
end_time = datetime.now()
time_range = [start_time + timedelta(hours=i) for i in range(int((end_time - start_time).total_seconds() // 3600))]

# Define probabilities to make certain brands appear more wasteful
brand_recycling_weights = {
    "Amazon": 0.9, "Walmart": 0.25, "Apple": 0.15, "Nike": 0.1, "Starbucks": 0.7, "Other": 0.3
}

brand_compost_weights = {
    "Amazon": 0.1, "Walmart": 0.5, "Apple": 0, "Nike": 0.02, "Starbucks": 0.3, "Other": 0.2
}

hour_compost_weights = {
    0: 0.05, 1: 0.05, 2: 0.05, 3: 0.05, 4: 0.05, 5: 0.1, 6: 0.2, 7: 0.3, 8: 0.4, 9: 0.6, 10: 0.5, 11: 0.6,
    12: 0.7, 13: 0.6, 14: 0.3, 15: 0.2, 16: 0.2, 17: 0.4, 18: 0.6, 19: 0.6, 20: 0.5, 21: 0.4, 22: 0.3, 23: 0.1
}

data = []

max_hour_compost_weight = max(hour_compost_weights.values())  # which is 0.7

N = 1000  # Number of data entries to generate

for i in range(N):
    # Generate random time within time_range
    time = random.choice(time_range)
    hour = time.hour

    # Randomly select a city and state
    city, state = random.choice(cities)

    # Randomly select a brand using the adjusted weights
    brand = random.choices(brands, weights=brand_weights, k=1)[0]

    # Randomly select a description
    description = random.choice(descriptions)

    # Adjust description with random adjectives
    adjectives = ["tiny", "small", "medium", "large", "ultra large", "gigantic"]
    adjective = random.choice(adjectives)
    description = adjective + " " + description

    # Determine is_metal based on description
    is_metal = "aluminum can" in description

    # Determine is_recyclable
    recycling_prob = brand_recycling_weights.get(brand, 0.5)
    is_recyclable = random.random() < recycling_prob

    # Determine is_compostable
    compost_prob_brand = brand_compost_weights.get(brand, 0.1)
    compost_prob_hour = hour_compost_weights.get(hour, 0.1) / max_hour_compost_weight
    compost_prob = compost_prob_brand * compost_prob_hour
    is_compostable = random.random() < compost_prob

    # Generate filename based on description
    if "box" in description:
        filename = "box" + str(i) + ".jpg"
    elif "cup" in description:
        filename = "cup" + str(i) + ".jpg"
    elif "can" in description:
        filename = "can" + str(i) + ".jpg"
    elif "bag" in description:
        filename = "bag" + str(i) + ".jpg"
    elif "bottle" in description:
        filename = "bottle" + str(i) + ".jpg"
    else:
        filename = "item" + str(i) + ".jpg"

    # Create item
    item = {
        "filename": filename,
        "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "state": state,
        "city": city,
        "description": description,
        "is_recyclable": is_recyclable,
        "is_compostable": is_compostable,
        "is_metal": is_metal,
        "brand": brand
    }

    data.append(item)

# Output data to JSON
print(json.dumps(data, indent=2))
