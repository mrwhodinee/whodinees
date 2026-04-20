#!/bin/bash
cd /root/.openclaw/workspace/whodinees/backend
source ../venv/bin/activate

python manage.py shell <<'PYEOF'
import json
import requests
from pathlib import Path
from portraits.services import meshy_portrait

showcase = Path("/root/.openclaw/workspace/whodinees/showcase")
tasks_file = showcase / "meshy_tasks.json"

with open(tasks_file) as f:
    tasks = json.load(f)

print("🔍 Checking Meshy tasks...\n")

all_done = True
for photo, data in tasks.items():
    if "error" in data:
        continue
    
    task_id = data["task_id"]
    try:
        info = meshy_portrait.poll_task(task_id)
        status = info["status"]
        progress = info.get("progress", 0)
        
        print(f"{photo}: {status} ({progress}%)")
        
        data["status"] = status
        data["progress"] = progress
        
        if status in ("SUCCEEDED", "SUCCESS", "COMPLETED"):
            # Download preview image
            preview_url = info.get("preview_url") or info.get("raw", {}).get("thumbnail_url")
            glb_url = info.get("glb_url")
            
            data["preview_url"] = preview_url
            data["glb_url"] = glb_url
            
            if preview_url:
                preview_path = showcase / f"{Path(photo).stem}_3d_preview.png"
                if not preview_path.exists():
                    print(f"  ⬇️  Downloading preview...")
                    r = requests.get(preview_url, timeout=60)
                    if r.status_code == 200:
                        preview_path.write_bytes(r.content)
                        print(f"  ✅ Saved: {preview_path.name}")
                else:
                    print(f"  ✅ Preview exists: {preview_path.name}")
        else:
            all_done = False
            
    except Exception as e:
        print(f"{photo}: ERROR - {e}")
        data["error"] = str(e)

with open(tasks_file, "w") as f:
    json.dump(tasks, f, indent=2)

if all_done:
    print("\n🎉 All models generated!")
else:
    print("\n⏳ Some models still generating. Run again in 1-2 minutes.")
PYEOF
