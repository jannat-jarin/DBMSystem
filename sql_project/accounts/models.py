from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    ROLE_CHOICES = (
        ('student', 'Patient'),
        ('doctor',  'Doctor'),
        ('admin',   'Admin'),
    )

    user       = models.OneToOneField(User, on_delete=models.CASCADE)
    role       = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    age        = models.IntegerField(null=True, blank=True)
    photo      = models.ImageField(upload_to='profiles/', null=True, blank=True)

    # Doctor-specific fields (ignored for students)
    specialty   = models.CharField(max_length=100, blank=True, default='')
    department  = models.CharField(max_length=100, blank=True, default='')
    bio         = models.TextField(blank=True, default='')
    qualifications = models.CharField(max_length=255, blank=True, default='')
    experience_years = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} ({self.role})"
