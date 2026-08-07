import os
import jwt as pyjwt  # alias the real PyJWT library to avoid clashing with this file's own name

try:
    from django.conf import settings
    PUBLIC_KEY = settings.JWT_PUBLIC_KEY
except Exception:
    PUBLIC_KEY = os.environ["JWT_PUBLIC_KEY"]

ALGORITHM = "RS256"


class TokenError(Exception):
    pass


def verify_token(token: str) -> dict:
    try:
        payload = pyjwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
    except pyjwt.ExpiredSignatureError:
        raise TokenError("Token has expired")
    except pyjwt.InvalidTokenError as e:
        raise TokenError(str(e))
    return payload