#!/bin/bash
cd /root/.openclaw/workspace/whodinees/backend
python3 manage.py test portraits 2>&1
