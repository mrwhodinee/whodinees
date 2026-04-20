#!/bin/bash
cd /root/.openclaw/workspace/whodinees/backend
source ../venv/bin/activate

python manage.py shell <<'PYEOF'
import json
from pathlib import Path
from portraits.services import meshy_portrait

showcase = Path("/root/.openclaw/workspace/whodinees/showcase")
photos = ["golden-retriever.jpg", "tabby-cat.jpg", "corgi.jpg"]
results = {}

for photo in photos:
    photo_path = showcase / photo
    print(f"\n📸 {photo}")
    try:
        task_id = meshy_portrait.submit_portrait_task(str(photo_path), seed=2000)
        print(f"✅ task_id: {task_id}")
        results[photo] = {"task_id": task_id, "status": "PENDING"}
    except Exception as e:
        print(f"❌ {e}")
        results[photo] = {"error": str(e)}

with open(showcase / "meshy_tasks.json", "w") as f:
    json.dump(results, f, indent=2)

print("\n💾 Saved to meshy_tasks.json")
PYEOF
