from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        from drf_spectacular.extensions import OpenApiAuthenticationExtension

        class SharedJWTAuthenticationScheme(OpenApiAuthenticationExtension):
            target_class = 'ems_shared.auth.authentication.SharedJWTAuthentication'
            name = 'SharedJWTAuth'

            def get_security_definition(self, auto_schema):
                return {
                    'type': 'http',
                    'scheme': 'bearer',
                    'bearerFormat': 'JWT',
                }
