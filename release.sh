#!/usr/bin/env bash
set -euo pipefail
cd backend
# Note: collectstatic runs in bin/post_compile during the build (changes persist
# in the slug). Here we only apply DB migrations, which is safe to rerun.
python manage.py migrate --noinput
