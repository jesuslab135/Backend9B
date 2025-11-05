from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from api.models.user import Usuario

class CustomJWTAuthentication(JWTAuthentication):
    
    def get_user(self, validated_token):
        try:
            user_id = validated_token['user_id']
            user = Usuario.objects.get(id=user_id)
            return user
        except Usuario.DoesNotExist:
            raise InvalidToken('User not found')
        except KeyError:
            raise InvalidToken('Token contained no recognizable user identification')

