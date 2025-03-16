from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import logging

logger = logging.getLogger(__name__)


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        logger.info(f"Attempting to authenticate with header: {request.headers.get('Authorization')}")
        raw_token = request.headers.get('Authorization')
        if not raw_token:
            logger.warning("No Authorization header provided")
            return None

        if not raw_token.startswith('Bearer '):
            logger.error("Invalid token header: Must start with 'Bearer '")
            return None

        token = raw_token.split(' ')[1]
        try:
            validated_token = self.get_validated_token(token)
            logger.info(f"Validated token: {validated_token}")
            user = self.get_user(validated_token)
            logger.info(f"Authenticated user: {user}, is_active: {user.is_active}")
            return (user, validated_token)

        except InvalidToken as e:
            logger.error(f"Invalid token error: {str(e)}")
            return None
        except TokenError as e:
            logger.error(f"Token error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
            return None
