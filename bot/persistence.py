# bot/persistence.py

import os
import json

THUMBNAIL_DATA_FILE = "thumbnails.json"

def load_thumbnail_data():
    """Load thumbnail data from a JSON file."""
    if os.path.exists(THUMBNAIL_DATA_FILE):
        with open(THUMBNAIL_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_thumbnail_data(data):
    """Save thumbnail data to a JSON file."""
    with open(THUMBNAIL_DATA_FILE, "w") as f:
        json.dump(data, f)
