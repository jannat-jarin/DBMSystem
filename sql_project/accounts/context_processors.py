from accounts.models import Profile


def user_role(request):
    role = None
    role_label = None
    unread_count = 0

    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            role = 'admin'
            role_label = 'Admin'
        else:
            try:
                profile = request.user.profile
                role = profile.role
                role_label = profile.get_role_display()
            except Profile.DoesNotExist:
                pass

        try:
            from clinic.models import Notification
            unread_count = Notification.objects.filter(
                user=request.user, is_read=False
            ).count()
        except Exception:
            pass

    return {
        'user_role': role,
        'user_role_label': role_label,
        'unread_notifications': unread_count,
    }
