#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Automatically create admin superuser on first deploy
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username__iexact='admin').exists() or User.objects.create_superuser('admin', 'admin@medishare.org', 'Admin@12345')"
