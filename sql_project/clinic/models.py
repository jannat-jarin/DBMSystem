from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


# ─────────────────────────────────────────────
# 1. DOCTOR AVAILABILITY / TIME SLOTS
# ─────────────────────────────────────────────
class DoctorAvailability(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]
    doctor     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time  = models.TimeField()
    end_time    = models.TimeField()
    is_active   = models.BooleanField(default=True)

    class Meta:
        unique_together = ('doctor', 'day_of_week', 'start_time')
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.doctor.username} – {self.get_day_of_week_display()} {self.start_time}–{self.end_time}"


# ─────────────────────────────────────────────
# 2. DOCTOR PROFILE (extended)
# ─────────────────────────────────────────────
class DoctorProfile(models.Model):
    doctor      = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialty   = models.CharField(max_length=100, blank=True, default='')
    department  = models.CharField(max_length=100, blank=True, default='')
    bio         = models.TextField(blank=True, default='')
    qualifications = models.CharField(max_length=255, blank=True, default='')
    experience_years = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Dr. {self.doctor.get_full_name() or self.doctor.username}"


# ─────────────────────────────────────────────
# 3. APPOINTMENT
# ─────────────────────────────────────────────
class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending',   'Pending'),
        ('approved',  'Approved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    student      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_appointments')
    doctor       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_appointments')
    date         = models.DateField()
    time         = models.TimeField()
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reason       = models.TextField(blank=True, default='')
    symptoms     = models.TextField(blank=True, default='')
    meeting_link = models.URLField(blank=True, default='')
    doctor_notes = models.TextField(blank=True, default='')
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} → {self.doctor.username} ({self.date} {self.time})"


# ─────────────────────────────────────────────
# 4. PRESCRIPTION
# ─────────────────────────────────────────────
class Prescription(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='prescription')
    student     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescriptions')
    doctor      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='written_prescriptions')
    diagnosis   = models.CharField(max_length=255)
    medicines   = models.TextField()
    dose        = models.TextField(blank=True, default='')
    tests       = models.TextField(blank=True, default='')
    advice      = models.TextField(blank=True, default='')
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prescription for {self.student.username} by {self.doctor.username}"


# ─────────────────────────────────────────────
# 5. NOTIFICATION
# ─────────────────────────────────────────────
class Notification(models.Model):
    TYPE_CHOICES = [
        ('approved',   'Appointment Approved'),
        ('cancelled',  'Appointment Cancelled'),
        ('completed',  'Appointment Completed'),
        ('prescribed', 'Prescription Ready'),
        ('rescheduled','Appointment Rescheduled'),
    ]
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notif_type  = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message     = models.TextField()
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, null=True, blank=True)
    is_read     = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notif_type}] → {self.user.username}"
