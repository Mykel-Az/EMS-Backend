from django.db import connection, transaction
from ems_shared.auth.jwt import verify_token, TokenError


class TenantScopeMiddleware:
    """
    Sets the Postgres session variable `app.current_school_id` for the
    duration of each request, so the RLS policies in school_core/rls.py
    can enforce tenant isolation at the DB layer.

    No-op on SQLite (local dev) — RLS doesn't exist there, matching the
    vendor check already used in rls.py's enable_rls/disable_rls.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if connection.vendor != "postgresql":
            return self.get_response(request)

        school_id = self._extract_school_id(request)

        # SET LOCAL only holds for the current transaction. Autocommit
        # mode treats each statement as its own transaction, so without
        # wrapping the whole request in atomic(), the setting would
        # vanish before the view's queries ever ran.
        with transaction.atomic():
            with connection.cursor() as cursor:
                if school_id is not None:
                    cursor.execute(
                        "SET LOCAL app.current_school_id = %s", [str(school_id)]
                    )
                else:
                    # No usable tenant context (unauthenticated request,
                    # register/login, or a user with no school). Set an
                    # impossible id rather than leaving it unset — any
                    # RLS-protected table then just returns zero rows
                    # instead of throwing "unrecognized configuration
                    # parameter". Fail closed, not open.
                    cursor.execute("SET LOCAL app.current_school_id = '-1'")

            response = self.get_response(request)

        return response

    def _extract_school_id(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1]

        try:
            payload = verify_token(token)
        except TokenError:
            return None

        if payload.get("token_type") != "access":
            return None

        return payload.get("school_id")