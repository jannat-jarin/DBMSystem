from django.contrib import admin
from .models import Appointment, DoctorAvailability, Notification, Prescription


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display   = ('student', 'doctor', 'date', 'time', 'status', 'created_at')
    list_filter    = ('status', 'date', 'doctor')
    search_fields  = ('student__username', 'doctor__username', 'reason', 'symptoms')
    list_editable  = ('status',)
    ordering       = ('-created_at',)
    autocomplete_fields = ('student', 'doctor')
    actions        = ('mark_approved', 'mark_completed', 'mark_cancelled')

    @admin.action(description='Mark selected as Approved')
    def mark_approved(self, request, queryset):
        queryset.update(status='approved')
        for appt in queryset:
            from .models import Notification
            Notification.objects.create(
                user=appt.student, notif_type='approved',
                message=f"Your appointment on {appt.date} has been approved.",
                appointment=appt,
            )

    @admin.action(description='Mark selected as Completed')
    def mark_completed(self, request, queryset):
        queryset.update(status='completed')

    @admin.action(description='Mark selected as Cancelled')
    def mark_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        for appt in queryset:
            from .models import Notification
            Notification.objects.create(
                user=appt.student, notif_type='cancelled',
                message=f"Your appointment on {appt.date} has been cancelled.",
                appointment=appt,
            )


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display  = ('student', 'doctor', 'diagnosis', 'created_at')
    list_filter   = ('doctor', 'created_at')
    search_fields = ('student__username', 'doctor__username', 'diagnosis')
    ordering      = ('-created_at',)


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display  = ('doctor', 'get_day', 'start_time', 'end_time', 'is_active')
    list_filter   = ('doctor', 'day_of_week', 'is_active')
    list_editable = ('is_active',)

    def get_day(self, obj):
        return obj.get_day_of_week_display()
    get_day.short_description = 'Day'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ('user', 'notif_type', 'is_read', 'created_at')
    list_filter   = ('notif_type', 'is_read')
    search_fields = ('user__username', 'message')
    ordering      = ('-created_at',)
