from django import forms
from django.contrib.auth.models import User
from .models import Appointment, DoctorAvailability, Prescription


class AppointmentStatusForm(forms.Form):
    status = forms.ChoiceField(choices=Appointment.STATUS_CHOICES)


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model  = Prescription
        fields = ('diagnosis', 'medicines', 'dose', 'tests', 'advice')
        widgets = {
            'diagnosis': forms.TextInput(attrs={'class': 'input'}),
            'medicines': forms.Textarea(attrs={'rows': 4, 'class': 'textarea'}),
            'dose':      forms.Textarea(attrs={'rows': 2, 'class': 'textarea'}),
            'tests':     forms.Textarea(attrs={'rows': 2, 'class': 'textarea'}),
            'advice':    forms.Textarea(attrs={'rows': 3, 'class': 'textarea'}),
        }


class DoctorAvailabilityForm(forms.ModelForm):
    class Meta:
        model  = DoctorAvailability
        fields = ('day_of_week', 'start_time', 'end_time', 'is_active')
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'input'}),
            'end_time':   forms.TimeInput(attrs={'type': 'time', 'class': 'input'}),
        }


class RescheduleForm(forms.ModelForm):
    class Meta:
        model  = Appointment
        fields = ('date', 'time')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'input'}),
        }


# Filter forms (not model forms)
class DoctorFilterForm(forms.Form):
    DEPT_CHOICES = [('', 'All Departments')]
    specialty  = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Specialty...'}))
    department = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Department...'}))


class HistoryFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'All Status')] + list(Appointment.STATUS_CHOICES)
    status     = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    date_from  = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'input'}))
    date_to    = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'input'}))
