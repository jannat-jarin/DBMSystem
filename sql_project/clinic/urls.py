from django.urls import path
from . import views

urlpatterns = [
    path('',                                                     views.home,                      name='home'),
    path('doctors/',                                             views.doctor_list,               name='doctor_list'),
    path('doctors/<int:doctor_user_id>/',                        views.doctor_profile,            name='doctor_profile'),
    path('book/<int:doctor_user_id>/',                           views.book_appointment,          name='book_appointment'),
    path('history/',                                             views.student_history,           name='student_history'),
    path('health-card/',                                         views.health_card,               name='health_card'),
    path('reschedule/<int:appointment_id>/',                     views.reschedule_appointment,    name='reschedule_appointment'),
    path('prescription/<int:prescription_id>/pdf/',              views.prescription_pdf,          name='prescription_pdf'),

    # Doctor
    path('doctor/dashboard/',                                    views.doctor_dashboard,          name='doctor_dashboard'),
    path('doctor/availability/',                                 views.manage_availability,       name='manage_availability'),
    path('doctor/availability/<int:slot_id>/delete/',            views.delete_availability,       name='delete_availability'),
    path('doctor/appointments/<int:appointment_id>/status/',     views.update_appointment_status, name='update_appointment_status'),
    path('doctor/appointments/<int:appointment_id>/prescription/', views.prescribe,              name='prescribe'),
    path('doctor/patient/<int:student_id>/',                     views.doctor_patient_history,    name='doctor_patient_history'),

    # Notifications
    path('notifications/',                                       views.notifications,             name='notifications'),
    path('notifications/mark-all-read/',                         views.mark_all_read,             name='mark_all_read'),

    # Admin reports
    path('admin-reports/',                                       views.admin_reports,             name='admin_reports'),
]
