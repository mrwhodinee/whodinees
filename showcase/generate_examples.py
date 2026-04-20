#!/usr/bin/env python3
"""Generate showcase examples: pet photo → 3D model via Meshy."""
import os
import sys
import json
import time
from pathlib import Path

# Add backend to path so we can import Django services
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "whodinees.settings")

import django
django.setup()

from portraits.services import meshy_portrait

SHOWCASE_DIR = Path(__file__).parent
PHOTOS = [
    "golden-retriever.jpg",
    "tabby-cat.jpg",
    "corgi.jpg",
]

def main():
    results = {}
    
    for photo in PHOTOS:
        photo_path = SHOWCASE_DIR / photo
        if not photo_path.exists():
            print(f"⚠️  {photo} not found, skipping")
            continue
        
        print(f"\n📸 Processing {photo}...")
        try:
            # Submit to Meshy (single variant for showcase)
            task_id = meshy_portrait.submit_portrait_task(str(photo_path), seed=2000)
            print(f"✅ Submitted → task_id: {task_id}")
            
            results[photo] = {
                "task_id": task_id,
                "status": "PENDING",
                "submitted_at": time.time(),
            }
            
            # Don't poll here - let them complete async
            # We'll check status in a follow-up script
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            results[photo] = {"error": str(e)}
    
    # Save results
    results_file = SHOWCASE_DIR / "meshy_tasks.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Saved task IDs to {results_file}")
    print("\n⏳ Models will take ~3-5 minutes to generate.")
    print("Run check_examples.py to poll status and download previews.")

if __name__ == "__main__":
    main()
