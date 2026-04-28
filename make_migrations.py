#!/usr/bin/env python
import os
import sys
import django

os.chdir('backend')
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whodinees.settings')
django.setup()

from django.core.management import call_command
call_command('makemigrations')
