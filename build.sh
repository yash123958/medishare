#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Automatically provision demo accounts on deploy
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(username__iexact='admin').exists():
    User.objects.create_superuser('admin', 'admin@medishare.org', 'Admin@12345')

if not User.objects.filter(username__iexact='donor').exists():
    User.objects.create_user(username='donor', email='donor@medishare.org', password='Donor@12345', role='DONOR')

if not User.objects.filter(username__iexact='ngo_demo').exists():
    User.objects.create_user(
        username='ngo_demo',
        email='ngo@medishare.org',
        password='Ngo@12345',
        role='NGO',
        ngo_name='Hope Healthcare NGO',
        is_verified_ngo=True,
        ngo_verification_status='APPROVED',
        ngo_reg_number='DARPAN-DL-2026-9812'
    )
"
