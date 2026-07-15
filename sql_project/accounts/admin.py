from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'role', 'age', 'specialty', 'department')
    list_filter   = ('role',)
    search_fields = ('user__username', 'user__email', 'specialty', 'department')
    ordering      = ('user__username',)
    fieldsets = (
        (None, {
            'fields': ('user', 'role', 'age', 'photo')
        }),
        ('Doctor Info', {
            'classes': ('collapse',),
            'fields': ('specialty', 'department', 'bio', 'qualifications', 'experience_years'),
        }),
    )
