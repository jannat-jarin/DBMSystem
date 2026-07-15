"""
Migration: accounts/0003_profile_doctor_fields.py

Add doctor-specific fields (specialty, department, bio, qualifications,
experience_years) to the existing Profile model.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = []
