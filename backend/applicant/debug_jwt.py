from rest_framework_simplejwt.authentication import JWTAuthentication
import logging

logger = logging.getLogger(__name__)


class DebugJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        logger.info(f"JWT Authenticate called for path: {request.path}")
        logger.info(f"Headers: {request.headers}")
        try:
            user, jwt = super().authenticate(request)
            logger.info(f"JWT Auth successful: user={user}, jwt={jwt}")
            return user, jwt
        except Exception as e:
            logger.error(f"JWT Auth failed: {str(e)}")
            raise