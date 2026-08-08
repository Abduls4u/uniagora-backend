from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.common.response import success_response
from apps.core.permissions import IsAuthenticatedCustomer
from apps.users.serializers import UserSerializer

from .serializers import (
    EmailTokenObtainPairSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
)
from .services import AuthService


class RegisterView(APIView):
    """PRD §16: Register. Issues JWT tokens immediately on success — PRD
    §4 states customers "may browse the marketplace immediately after
    registration," and MVP has no email-verification gate (PRD §16), so
    requiring a *second* login call afterward would add friction with no
    corresponding product requirement. Engineering Implementation
    Decision — see EDD §10, assumption 5.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthService.register(**serializer.validated_data)
        refresh = RefreshToken.for_user(user)
        data = {
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
        return success_response(data=data, status=status.HTTP_201_CREATED)


class EmailTokenObtainPairView(TokenObtainPairView):
    """PRD §16: Login. Thin subclass — only the serializer differs (adds
    the `user` payload); token issuance itself is entirely SimpleJWT's,
    keyed off `User.USERNAME_FIELD` ("email") automatically.
    """

    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code < 400:
            return success_response(data=response.data)

        return response


class LogoutView(APIView):
    """PRD §16: Logout, via refresh-token blacklisting."""

    permission_classes = [IsAuthenticatedCustomer]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            message="Logged out successfully.", status=status.HTTP_205_RESET_CONTENT
        )


class PasswordResetRequestView(APIView):
    """PRD §16: Forgot Password."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.initiate_password_reset(email=serializer.validated_data["email"])
        return success_response(
            message="If an account with that email exists, a password reset link has been sent."
        )


class PasswordResetConfirmView(APIView):
    """PRD §16: Password Reset."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.confirm_password_reset(
            uidb64=serializer.validated_data["uid"],
            token=serializer.validated_data["token"],
            new_password=serializer.validated_data["new_password"],
        )
        return success_response(message="Password has been reset successfully.")
