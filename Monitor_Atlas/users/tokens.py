from rest_framework_simplejwt.tokens import (
    AccessToken,
    RefreshToken,
    BlacklistMixin,
    TokenError,
)
from django.utils.translation import gettext_lazy as _


class SessionAccessToken(BlacklistMixin, AccessToken):
    token_type = "access"

    def verify(self, *args, **kwargs) -> None:
        super().verify(*args, **kwargs)
        session_id = self.payload.get("session_id")
        if session_id:
            from users.models import UserSession

            if not UserSession.objects.filter(id=session_id, is_active=True).exists():
                raise TokenError(_("Session has been revoked"))


RefreshToken.access_token_class = SessionAccessToken
