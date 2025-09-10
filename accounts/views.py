from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .models import User


def set_refresh_cookie(response, refresh_token):
    """
    Helper function to set HttpOnly refresh token cookie.
    """
    response.set_cookie(
        'refresh_token',
        str(refresh_token),
        max_age=7 * 24 * 60 * 60,  # 7 days
        httponly=True,
        secure=not settings.DEBUG,
        samesite='None',
        path='/api/auth/refresh/'
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login endpoint that returns access token in JSON and sets refresh token as HttpOnly cookie.
    """
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response(
            {'detail': 'Email ve şifre gereklidir.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(request, username=email, password=password)
    if user is None:
        return Response(
            {'detail': 'Geçersiz giriş.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'detail': 'Hesap aktif değil.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token

    response = Response({
        'access': str(access_token),
        'user': {
            'id': user.id,
            'email': user.email,
            'role': user.role,
            'brand_id': user.brand.id if user.brand else None,
        }
    }, status=status.HTTP_200_OK)

    set_refresh_cookie(response, refresh)
    return response


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_view(request):
    """
    Refresh endpoint that reads refresh token from HttpOnly cookie and returns new access token.
    """
    refresh_token = request.COOKIES.get('refresh_token')
    if not refresh_token:
        return Response(
            {'detail': 'Refresh yok.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        refresh = RefreshToken(refresh_token)
        access_token = refresh.access_token

        response = Response({
            'access': str(access_token),
        }, status=status.HTTP_200_OK)

        # If rotation is enabled, set the new refresh token
        if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False):
            # Get user from token
            user_id = refresh.get('user_id')
            user = User.objects.get(id=user_id)
            new_refresh = RefreshToken.for_user(user)
            set_refresh_cookie(response, new_refresh)

        return response

    except (InvalidToken, TokenError, User.DoesNotExist):
        return Response(
            {'detail': 'Geçersiz refresh.'},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    """
    Logout endpoint that deletes refresh token cookie.
    """
    response = Response({
        'detail': 'Çıkış yapıldı.'
    }, status=status.HTTP_200_OK)

    response.delete_cookie(
        'refresh_token',
        path='/api/auth/refresh/'
    )
    return response
