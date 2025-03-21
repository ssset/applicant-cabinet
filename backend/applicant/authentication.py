from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user_id = validated_token.get('user_id')
            if not user_id:
                raise InvalidToken('Token contained no recognizable user identification')

            user = User.objects.select_related('organization').get(id=user_id)

            if not user.is_active:
                raise InvalidToken('User in not active')

            return user
        except User.DoesNotExist:
            raise InvalidToken('User not found')
        except Exception as e:
            logger.error(f"Error in CustomJWTAuthentication: {str(e)}")
            raise InvalidToken('Error authenticating user')
