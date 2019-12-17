from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)


class TokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()

class TokenErrorSerializer(serializers.Serializer):
    details = serializers.CharField()

# Override method to fix swagger schema
class JWTAuthToken(TokenObtainPairView):
    @swagger_auto_schema(responses={201: TokenSerializer, 491: TokenErrorSerializer})
    def post(self, *args, **kwargs):
        return super(JWTAuthToken, self).post(*args, **kwargs)
