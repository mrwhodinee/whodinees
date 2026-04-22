#!/usr/bin/env bash
set -euo pipefail
cd backend

# Run migrations
python manage.py migrate --noinput

# Run tests before deploying
echo "Running test suite..."
python manage.py test portraits --noinput --parallel

if [ $? -ne 0 ]; then
    echo "❌ Tests failed - deployment aborted"
    exit 1
fi

echo "✅ All tests passed - deployment continuing"
