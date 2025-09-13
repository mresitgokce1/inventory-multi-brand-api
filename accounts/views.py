# auth/views.py
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .models import User

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_KWARGS_DEV = dict(
    max_age=30 * 24 * 60 * 60,  # 30 gün
    httponly=True,
    samesite="Lax",  # dev: aynı origin
    secure=False,  # prod: True + HTTPS
    path="/api/auth/",  # auth yolları
)
REFRESH_COOKIE_KWARGS_PROD = dict(
    max_age=30 * 24 * 60 * 60,
    httponly=True,
    samesite="None",  # cross-site ise zorunlu
    secure=True,  # HTTPS zorunlu
    path="/api/auth/",
)


def set_refresh_cookie(response, refresh_token: RefreshToken):
    kwargs = (
        REFRESH_COOKIE_KWARGS_PROD if not settings.DEBUG else REFRESH_COOKIE_KWARGS_DEV
    )
    response.set_cookie(REFRESH_COOKIE_NAME, str(refresh_token), **kwargs)


def delete_refresh_cookie(response: Response):
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/auth/")


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get("email")
    password = request.data.get("password")
    if not email or not password:
        return Response({"detail": "Email ve şifre gereklidir."}, status=400)

    from django.contrib.auth import authenticate

    user = authenticate(request, username=email, password=password)
    if not user or not user.is_active:
        return Response({"detail": "Geçersiz giriş."}, status=401)

    refresh = RefreshToken.for_user(user)
    access = refresh.access_token

    resp = Response(
        {
            "access": str(access),
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "brand_id": user.brand.id if user.brand else None,
            },
        },
        status=200,
    )
    set_refresh_cookie(resp, refresh)
    return resp


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_view(request):
    cookie_val = request.COOKIES.get(REFRESH_COOKIE_NAME)
    if not cookie_val:
        return Response({"detail": "Refresh yok."}, status=401)
    try:
        refresh = RefreshToken(cookie_val)
        new_access = refresh.access_token
        resp = Response({"access": str(new_access)}, status=200)

        # ROTATE_REFRESH_TOKENS=True ise yeni refresh üret ve cookie’yi güncelle
        if settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS", False):
            user_id = refresh.get("user_id")
            user = User.objects.get(id=user_id)
            new_refresh = RefreshToken.for_user(user)
            set_refresh_cookie(resp, new_refresh)
        return resp
    except (InvalidToken, TokenError, User.DoesNotExist):
        return Response({"detail": "Geçersiz refresh."}, status=401)


@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    resp = Response({"detail": "Çıkış yapıldı."}, status=200)
    delete_refresh_cookie(resp)
    return resp
