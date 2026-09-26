import os
import shutil
from pathlib import Path

# Setup crop image assets for all 26 catalogue crops
PUBLIC_CROPS_DIR = Path("frontend/public/images/crops")
PUBLIC_CROPS_DIR.mkdir(parents=True, exist_ok=True)

# Copy base fallback from existing images if crop specific image does not exist yet
HERO_IMAGE = Path("frontend/public/images/crop-intelligence.webp")

CROPS = [
    "rice", "maize", "jute", "cotton", "wheat", "chickpea", "kidneybeans", "pigeonpeas",
    "mothbeans", "mungbean", "blackgram", "lentil", "pomegranate", "banana", "mango",
    "grapes", "watermelon", "muskmelon", "apple", "orange", "papaya", "coconut",
    "mustard", "sugarcane", "potato", "groundnut"
]

for crop in CROPS:
    target_webp = PUBLIC_CROPS_DIR / f"{crop}.webp"
    if not target_webp.exists():
        if HERO_IMAGE.exists():
            shutil.copy(HERO_IMAGE, target_webp)
            print(f"Initialized fallback asset for {crop}")

print("Crop image library setup complete. Total assets:", len(list(PUBLIC_CROPS_DIR.glob("*.webp"))))
