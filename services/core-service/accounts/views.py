from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework_simplejwt.tokens import RefreshToken
from ems_shared.auth.jwt import verify_token, TokenError
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializer import *

# Create your views here.

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh["school_id"] = str(user.school_id) if user.school_id else None
    refresh["email"] = user.email
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }

class RegisterUserView(generics.CreateAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = get_tokens_for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "token": token,
            },
            status=status.HTTP_201_CREATED,
        )

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        tokens = get_tokens_for_user(user)

        return Response({"user": UserSerializer(user).data, **tokens})


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "refresh token required"}, status=400)

        try:
            payload = verify_token(refresh_token)
        except TokenError as e:
            return Response({"detail": str(e)}, status=401)

        if payload.get("token_type") != "refresh":
            return Response({"detail": "Not a refresh token"}, status=401)

        # Re-mint an access token from the still-valid refresh token
        refresh = RefreshToken(refresh_token)
        access = str(refresh.access_token)

        return Response({"access": access})


class UserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserSerializer


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = UserPasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password updated successfully"})

