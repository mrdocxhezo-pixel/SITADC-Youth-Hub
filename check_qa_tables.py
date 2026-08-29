import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
import django
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT * FROM sqlite_master WHERE type='table' AND name LIKE 'qa_%'")
tables = cursor.fetchall()
for t in tables:
    print(t)