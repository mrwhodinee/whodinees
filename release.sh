#!/usr/bin/env bash
set -euo pipefail
cd backend

# Run migrations
python manage.py migrate --noinput

# Note: Tests are run in CI/CD pipeline, not in Heroku release phase
# Heroku release phase has limited resources and database constraints
# Use GitHub Actions or run tests locally before pushing
echo "✅ Migrations complete - deployment continuing"
