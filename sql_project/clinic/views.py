import io
from collections import Counter
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import Profile

from .forms import (DoctorAvailabilityForm, DoctorFilterForm,
                    HistoryFilterForm, PrescriptionForm, RescheduleForm)
from .models import (Appointment, DoctorAvailability, Notification,
                     Prescription)



def _profile_for(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    if user.is_staff or user.is_superuser:
        if profile.role != 'admin':
            profile.role = 'admin'
            profile.save(update_fields=['role'])
    return profile


def _notify(user, notif_type, message, appointment=None):
    Notification.objects.create(
        user=user,
        notif_type=notif_type,
        message=message,
        appointment=appointment,
    )



def home(request):
    featured_doctors = (
        Profile.objects.filter(role='doctor')
        .select_related('user')
        .order_by('user__username')[:4]
    )
    return render(request, 'home.html', {'featured_doctors': featured_doctors})



@login_required
def notifications(request):
    notifs = Notification.objects.filter(user=request.user)
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications.html', {'notifications': notifs})


@login_required
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('notifications')



@login_required
def doctor_list(request):
    form = DoctorFilterForm(request.GET or None)
    qs   = Profile.objects.filter(role='doctor').select_related('user')

    if form.is_valid():
        if form.cleaned_data.get('specialty'):
            qs = qs.filter(specialty__icontains=form.cleaned_data['specialty'])
        if form.cleaned_data.get('department'):
            qs = qs.filter(department__icontains=form.cleaned_data['department'])

    doctors = qs.order_by('user__username')
    return render(request, 'doctor_list.html', {'doctors': doctors, 'form': form})



@login_required
def doctor_profile(request, doctor_user_id):
    doctor  = get_object_or_404(User, id=doctor_user_id, profile__role='doctor')
    profile = doctor.profile
    slots   = DoctorAvailability.objects.filter(doctor=doctor, is_active=True)
    return render(request, 'doctor_profile.html', {
        'doctor': doctor,
        'profile': profile,
        'slots': slots,
    })


@login_required
def book_appointment(request, doctor_user_id):
    profile = _profile_for(request.user)
    if profile.role != 'student':
        messages.error(request, 'Only students can book appointments.')
        return redirect('home')

    doctor        = get_object_or_404(User, id=doctor_user_id, profile__role='doctor')
    slots         = DoctorAvailability.objects.filter(doctor=doctor, is_active=True)
    slot_by_day   = {}
    for s in slots:
        slot_by_day.setdefault(s.day_of_week, []).append(s)
    available_days = sorted(slot_by_day.keys())
    today = timezone.localdate()

    if request.method == 'POST':
        date     = request.POST.get('date')
        time_val = request.POST.get('time')
        reason   = request.POST.get('reason', '').strip()
        symptoms = request.POST.get('symptoms', '').strip()

        if not date or not time_val:
            messages.error(request, 'Date and time are required.')
        else:
            from datetime import date as date_cls, datetime, time as time_cls
            chosen_date = date_cls.fromisoformat(date)
            chosen_time = time_cls.fromisoformat(time_val)
            dow         = chosen_date.weekday()   # 0=Monday

            valid_slot = slots.filter(
                day_of_week=dow,
                start_time__lte=chosen_time,
                end_time__gt=chosen_time,
            ).exists()

            if not valid_slot:
                messages.error(request, 'This time is outside the doctor\'s available slots.')
            elif Appointment.objects.filter(
                doctor=doctor, date=chosen_date, time=chosen_time,
                status__in=['pending', 'approved']
            ).exists():
                messages.error(request, 'This slot is already booked. Please choose another time.')
            else:
                appt = Appointment.objects.create(
                    student=request.user, doctor=doctor,
                    date=chosen_date, time=chosen_time,
                    reason=reason, symptoms=symptoms, status='pending',
                )
               
                _notify(
                    doctor, 'approved',
                    f"New appointment request from {request.user.get_full_name() or request.user.username} on {chosen_date} at {chosen_time.strftime('%I:%M %p')}.",
                    appt,
                )
                messages.success(request, 'Appointment request sent!')
                return redirect('student_history')

    return render(request, 'book_appointment.html', {
        'doctor': doctor,
        'slots': slots,
        'slot_by_day': slot_by_day,
        'available_days': available_days,
        'today': today,
    })



@login_required
def student_history(request):
    profile = _profile_for(request.user)
    if profile.role != 'student':
        messages.error(request, 'Student history is only available for students.')
        return redirect('home')

    form = HistoryFilterForm(request.GET or None)
    qs   = Appointment.objects.filter(student=request.user).select_related('doctor')

    if form.is_valid():
        if form.cleaned_data.get('status'):
            qs = qs.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('date_from'):
            qs = qs.filter(date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'):
            qs = qs.filter(date__lte=form.cleaned_data['date_to'])

    appointments    = qs.order_by('-created_at')
    prescriptions   = Prescription.objects.filter(student=request.user).select_related('appointment', 'doctor')
    prescription_map = {p.appointment_id: p for p in prescriptions}

    for appt in appointments:
        appt.prescription_item = prescription_map.get(appt.id)

    return render(request, 'student_history.html', {
        'appointments': appointments,
        'form': form,
    })


@login_required
def reschedule_appointment(request, appointment_id):
    profile = _profile_for(request.user)
    if profile.role != 'student':
        return redirect('home')

    appt = get_object_or_404(Appointment, id=appointment_id, student=request.user, status='pending')

    if request.method == 'POST':
        form = RescheduleForm(request.POST, instance=appt)
        if form.is_valid():
            new_date = form.cleaned_data['date']
            new_time = form.cleaned_data['time']
            dow      = new_date.weekday()

            slots = DoctorAvailability.objects.filter(doctor=appt.doctor, is_active=True)
            valid = slots.filter(
                day_of_week=dow,
                start_time__lte=new_time,
                end_time__gt=new_time,
            ).exists()

            if not valid:
                messages.error(request, "Chosen time is outside the doctor's available hours.")
            elif Appointment.objects.filter(
                doctor=appt.doctor, date=new_date, time=new_time,
                status__in=['pending', 'approved']
            ).exclude(id=appt.id).exists():
                messages.error(request, 'That slot is already booked.')
            else:
                old_date = appt.date
                form.save()
                _notify(
                    appt.doctor, 'rescheduled',
                    f"{request.user.get_full_name() or request.user.username} rescheduled appointment from {old_date} to {new_date} at {new_time.strftime('%I:%M %p')}.",
                    appt,
                )
                messages.success(request, 'Appointment rescheduled successfully.')
                return redirect('student_history')
    else:
        form = RescheduleForm(instance=appt)

    return render(request, 'reschedule.html', {'form': form, 'appointment': appt})



@login_required
def health_card(request):
    profile = _profile_for(request.user)
    if profile.role != 'student':
        return redirect('home')

    prescriptions = (
        Prescription.objects.filter(student=request.user)
        .select_related('appointment', 'doctor')
        .order_by('-created_at')
    )
    return render(request, 'health_card.html', {
        'prescriptions': prescriptions,
        'profile': profile,
    })



@login_required
def prescription_pdf(request, prescription_id):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        HRFlowable, Paragraph, SimpleDocTemplate,
        Spacer, Table, TableStyle
    )

    presc = get_object_or_404(Prescription, id=prescription_id)
    appt = presc.appointment

    profile = _profile_for(request.user)

    if profile.role == 'student' and presc.student != request.user:
        messages.error(request, "You are not allowed to download this prescription.")
        return redirect('student_history')

    if profile.role == 'doctor' and presc.doctor != request.user:
        messages.error(request, "You are not allowed to download this prescription.")
        return redirect('doctor_dashboard')

    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm
    )

    styles = getSampleStyleSheet()
    teal = colors.HexColor('#2b8a78')
    dark = colors.HexColor('#14332f')
    muted = colors.HexColor('#5f7a75')
    light_line = colors.HexColor('#cce8e4')

    h1 = ParagraphStyle(
        'H1',
        parent=styles['Heading1'],
        textColor=teal,
        fontSize=20,
        leading=24,
        spaceAfter=2
    )

    h2 = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        textColor=dark,
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=4
    )

    body = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        leading=15,
        textColor=dark
    )

    small = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=muted
    )

    doctor_name = appt.doctor.get_full_name() or appt.doctor.username
    student_name = appt.student.get_full_name() or appt.student.username

    dr_profile = getattr(appt.doctor, 'profile', None)
    dr_specialty = getattr(dr_profile, 'specialty', '') or ''
    dr_dept = getattr(dr_profile, 'department', '') or ''

    story = [
        Paragraph("University Medical Center", h1),
        Paragraph("Official Student Prescription", small),
        Spacer(1, 4 * mm),
        HRFlowable(width="100%", thickness=1.5, color=teal),
        Spacer(1, 4 * mm),
    ]

    info_data = [
        ['Student', student_name, 'Doctor', f"Dr. {doctor_name}"],
        ['Date', str(appt.date), 'Specialty', dr_specialty or '-'],
        ['Time', appt.time.strftime('%I:%M %p'), 'Department', dr_dept or '-'],
    ]

    tbl = Table(info_data, colWidths=[30 * mm, 65 * mm, 30 * mm, 55 * mm])
    tbl.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), muted),
        ('TEXTCOLOR', (2, 0), (2, -1), muted),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    story += [
        tbl,
        Spacer(1, 4 * mm),
        HRFlowable(width="100%", thickness=0.5, color=light_line),
        Spacer(1, 4 * mm)
    ]

    def section(title, content):
        if content:
            story.append(Paragraph(title, h2))
            story.append(Paragraph(content.replace('\n', '<br/>'), body))
            story.append(Spacer(1, 3 * mm))

    section("Diagnosis", presc.diagnosis)
    section("Medicines", presc.medicines)
    section("Dose", presc.dose)
    section("Tests", presc.tests)
    section("Advice", presc.advice)

    if appt.doctor_notes:
        section("Doctor Notes", appt.doctor_notes)

    story += [
        Spacer(1, 12 * mm),
        HRFlowable(width="100%", thickness=0.5, color=light_line),
        Spacer(1, 8 * mm),
        Paragraph("Doctor Signature: ________________________________", body),
        Spacer(1, 6 * mm),
        Paragraph(
            f"Issued by Dr. {doctor_name} on {presc.created_at.strftime('%d %B %Y')}",
            small
        ),
        Paragraph(
            "This prescription is generated by the University Medical Center Portal.",
            small
        ),
        Paragraph(
            "University Medical Center - Confidential Student Medical Record",
            small
        ),
    ]

    doc.build(story)
    buf.seek(0)

    filename = f"prescription_{presc.id}_{appt.student.username}.pdf"
    response = HttpResponse(buf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def manage_availability(request):
    profile = _profile_for(request.user)
    if profile.role != 'doctor':
        return redirect('home')

    slots = DoctorAvailability.objects.filter(doctor=request.user)

    if request.method == 'POST':
        form = DoctorAvailabilityForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.doctor = request.user
            slot.save()
            messages.success(request, 'Availability slot added.')
            return redirect('manage_availability')
    else:
        form = DoctorAvailabilityForm()

    return render(request, 'manage_availability.html', {'form': form, 'slots': slots})


@login_required
def delete_availability(request, slot_id):
    profile = _profile_for(request.user)
    if profile.role != 'doctor':
        return redirect('home')
    slot = get_object_or_404(DoctorAvailability, id=slot_id, doctor=request.user)
    slot.delete()
    messages.success(request, 'Slot removed.')
    return redirect('manage_availability')



@login_required
def doctor_dashboard(request):
    profile = _profile_for(request.user)
    if profile.role != 'doctor':
        messages.error(request, 'Doctor dashboard is only available for doctors.')
        return redirect('home')

    appointments = (
        Appointment.objects.filter(doctor=request.user)
        .select_related('student')
        .order_by('-created_at')
    )
    pending_count = appointments.filter(status='pending').count()
    approved_count = appointments.filter(status='approved').count()
    completed_count = appointments.filter(status='completed').count()
    cancelled_count = appointments.filter(status='cancelled').count()
    return render(request, 'doctor_dashboard.html', {
        'appointments': appointments,
        'status_choices': Appointment.STATUS_CHOICES,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
    })


@login_required
def update_appointment_status(request, appointment_id):
    profile = _profile_for(request.user)
    if profile.role != 'doctor':
        return redirect('home')

    appt = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)

    if request.method == 'POST':
        status = request.POST.get('status')
        valid  = {c for c, _ in Appointment.STATUS_CHOICES}
        if status in valid:
            old_status  = appt.status
            appt.status = status
            appt.save(update_fields=['status'])

            
            msg_map = {
                'approved':  f"Your appointment with Dr. {request.user.get_full_name() or request.user.username} on {appt.date} has been APPROVED. ✅",
                'cancelled': f"Your appointment on {appt.date} was CANCELLED by the doctor. ❌",
                'completed': f"Your appointment on {appt.date} is marked COMPLETED. Check your prescription.",
            }
            if status in msg_map:
                _notify(appt.student, status, msg_map[status], appt)

            messages.success(request, 'Status updated.')
        else:
            messages.error(request, 'Invalid status.')

    return redirect('doctor_dashboard')


@login_required
def prescribe(request, appointment_id):
    profile = _profile_for(request.user)
    if profile.role != 'doctor':
        return redirect('home')

    appt = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)
    prescription = getattr(appt, 'prescription', None)

    if request.method == 'POST':
        form = PrescriptionForm(request.POST, instance=prescription)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.appointment = appt
            obj.student = appt.student
            obj.doctor = request.user
            obj.save()

            appt.meeting_link = request.POST.get('meeting_link', '').strip()
            appt.doctor_notes = request.POST.get('doctor_notes', '').strip()

            if appt.status == 'approved':
                appt.status = 'completed'

            appt.save()

            _notify(
                appt.student,
                'prescribed',
                f"Dr. {request.user.get_full_name() or request.user.username} has written a prescription for your appointment on {appt.date}.",
                appt,
            )

            messages.success(request, 'Prescription saved successfully.')
            return redirect('doctor_dashboard')

    else:
        form = PrescriptionForm(instance=prescription)

    return render(request, 'prescription_form.html', {
        'appointment': appt,
        'form': form
    })


@login_required
def doctor_patient_history(request, student_id):
    profile = _profile_for(request.user)
    if profile.role != 'doctor':
        return redirect('home')

    student = get_object_or_404(User, id=student_id)

    appointments = (
        Appointment.objects.filter(doctor=request.user, student=student)
        .select_related('doctor', 'student')
        .order_by('-created_at')
    )

    if not appointments.exists():
        messages.error(request, 'No appointment history found for this student.')
        return redirect('doctor_dashboard')

    prescriptions = (
        Prescription.objects.filter(doctor=request.user, student=student)
        .select_related('appointment')
    )

    prescription_map = {p.appointment_id: p for p in prescriptions}

    for appt in appointments:
        appt.prescription_item = prescription_map.get(appt.id)

    return render(request, 'doctor_patient_history.html', {
        'student': student,
        'appointments': appointments,
    })



@login_required
def admin_reports(request):
    if not request.user.is_staff:
        return redirect('home')

    
    today = timezone.localdate()
    month_keys = []
    year = today.year
    month = today.month
    for _ in range(12):
        month_keys.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1

    month_keys.reverse()
    month_counts = Counter()
    for created_at in Appointment.objects.values_list('created_at', flat=True):
        if created_at is None:
            continue
        created_day = timezone.localtime(created_at).date() if timezone.is_aware(created_at) else created_at.date()
        month_counts[(created_day.year, created_day.month)] += 1

    monthly = [
        {
            'month': date(y, m, 1),
            'count': month_counts.get((y, m), 0),
        }
        for y, m in month_keys
    ]

    top_doctors = (
        Appointment.objects.values('doctor__username', 'doctor__id')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    status_stats = (
        Appointment.objects.values('status')
        .annotate(count=Count('id'))
    )

    total_appointments  = Appointment.objects.count()
    total_prescriptions = Prescription.objects.count()
    total_students      = Profile.objects.filter(role='student').count()
    total_doctors       = Profile.objects.filter(role='doctor').count()

    return render(request, 'admin_reports.html', {
        'monthly':             monthly,
        'top_doctors':         top_doctors,
        'status_stats':        status_stats,
        'total_appointments':  total_appointments,
        'total_prescriptions': total_prescriptions,
        'total_students':      total_students,
        'total_doctors':       total_doctors,
    })
