#!/bin/bash
cd /root/.openclaw/workspace/whodinees/backend
source ../venv/bin/activate

python manage.py shell <<'PYEOF'
from store.models import Product

count = Product.objects.count()
print(f"Found {count} products in database")

if count > 0:
    print("Deleting all products...")
    Product.objects.all().delete()
    print("✅ All sculptural products removed")
else:
    print("No products to delete")
PYEOF
