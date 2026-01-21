from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils.functional import SimpleLazyObject


class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        return response

    def process_request(self, request):
        if not hasattr(request, "user") or request.user.is_anonymous:
            auth = JWTAuthentication()
            try:
                # authenticate returns tuple (user, token) or None
                auth_result = auth.authenticate(request)
                if auth_result is not None:
                    user, token = auth_result
                    request.user = user
            except Exception:
                # Authentication failed, user remains anonymous
                pass
