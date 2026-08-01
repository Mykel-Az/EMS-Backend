from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from ems_shared.auth.jwt import verify_token, TokenError

User = get_user_model()


class SharedJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None  # no credentials provided — let other auth classes/permissions handle it

        token = auth_header.split(" ", 1)[1]

        try:
            payload = verify_token(token)
        except TokenError as e:
            raise AuthenticationFailed(str(e))

        if payload.get("token_type") != "access":
            raise AuthenticationFailed("Not an access token")

        try:
            user = User.objects.get(pk=payload["user_id"])
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found")

        return (user, payload)  # payload available as request.auth if needed