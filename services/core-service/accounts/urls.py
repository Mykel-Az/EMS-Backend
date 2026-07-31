from django.urls import path
from .views import *

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("user-details/", UserDetailView.as_view(), name="user-details"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
]