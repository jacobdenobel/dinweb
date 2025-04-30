from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.shortcuts import redirect

class DebugAutoLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEBUG and request.path.startswith('/admin/') and not request.user.is_authenticated:
            User = get_user_model()
            user, created = User.objects.get_or_create(username='devadmin', defaults={
                'is_staff': True,
                'is_superuser': True,
                'email': 'dev@local'
            })
            login(request, user)
            return redirect(request.get_full_path())  # reload to apply login
        return self.get_response(request)