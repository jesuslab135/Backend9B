"""
Custom middleware for WebSocket JWT authentication come
"""
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_string):
    """
    Obtiene el usuario desde un JWT token
    """
    try:
        # Validar el token
        access_token = AccessToken(token_string)
        user_id = access_token['user_id']
        
        # Obtener usuario de la base de datos
        user = User.objects.get(id=user_id)
        
        logger.info(f"✅ WebSocket auth: Usuario {user.username} (ID: {user_id}) autenticado")
        return user
        
    except (InvalidToken, TokenError) as e:
        logger.warning(f"⚠️ WebSocket auth: Token inválido - {e}")
        return AnonymousUser()
    except User.DoesNotExist:
        logger.warning(f"⚠️ WebSocket auth: Usuario ID {user_id} no existe")
        return AnonymousUser()
    except Exception as e:
        logger.error(f"❌ WebSocket auth: Error inesperado - {e}")
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Middleware para autenticar conexiones WebSocket con JWT tokens
    El token se espera en query parameters: ?token=xxx
    """
    
    async def __call__(self, scope, receive, send):
        # Obtener query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        
        # Extraer token del query string
        token = query_params.get('token', [None])[0]
        
        if token:
            # Autenticar usuario con el token
            scope['user'] = await get_user_from_token(token)
            logger.info(f"🔐 WebSocket: Autenticación JWT - Usuario: {scope['user']}")
        else:
            # Sin token, usuario anónimo
            scope['user'] = AnonymousUser()
            logger.warning("⚠️ WebSocket: Conexión sin token - Usuario anónimo")
        
        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    """
    Helper function para aplicar JWTAuthMiddleware
    Uso: JWTAuthMiddlewareStack(URLRouter(...))
    """
    return JWTAuthMiddleware(inner)
