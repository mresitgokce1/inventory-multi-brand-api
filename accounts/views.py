from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.openapi import OpenApiResponse
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


@extend_schema(
    summary="User login",
    description="Authenticate with email and password. Returns access token in response body and sets HttpOnly refresh token cookie for secure token rotation.",
    tags=["authentication"],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email', 'example': 'user@example.com'},
                'password': {'type': 'string', 'example': 'password123'}
            },
            'required': ['email', 'password']
        }
    },
    responses={
        200: OpenApiResponse(
            description="Login successful",
            examples=[OpenApiExample(
                "Successful login",
                value={
                    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "user": {
                        "id": 1,
                        "email": "user@example.com",
                        "role": "BRAND_MANAGER",
                        "brand_id": 1
                    }
                }
            )]
        ),
        400: "Missing email or password",
        401: "Invalid credentials or inactive account"
    }
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


@extend_schema(
    summary="Refresh access token",
    description="Refresh access token using HttpOnly refresh token cookie. Returns new access token and rotates refresh token if configured.",
    tags=["authentication"],
    request=None,
    responses={
        200: OpenApiResponse(
            description="Token refreshed successfully",
            examples=[OpenApiExample(
                "Successful refresh",
                value={
                    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                }
            )]
        ),
        401: "Missing or invalid refresh token"
    }
)
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


@extend_schema(
    summary="User logout",
    description="Logout user by clearing the HttpOnly refresh token cookie. No authentication required.",
    tags=["authentication"],
    request=None,
    responses={
        200: OpenApiResponse(
            description="Logout successful",
            examples=[OpenApiExample(
                "Successful logout",
                value={
                    "detail": "Çıkış yapıldı."
                }
            )]
        )
    }
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
