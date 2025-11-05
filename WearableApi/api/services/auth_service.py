
import logging
from typing import Dict, Optional, Tuple
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import Usuario, Consumidor, Administrador

logger = logging.getLogger(__name__)

class AuthenticationService:
    
    @staticmethod
    def generate_tokens(usuario: Usuario) -> Dict:
        refresh = RefreshToken.for_user(usuario)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    
    @staticmethod
    def authenticate(email: str, password: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        try:
            usuario = Usuario.objects.get(email=email)
            
            if not usuario.check_password(password):
                logger.warning(f"Failed login: {email} (invalid password)")
                return False, None, "Invalid credentials"
            
            tokens = AuthenticationService.generate_tokens(usuario)
            
            user_data = {
                'id': usuario.id,
                'user_id': usuario.id,
                'nombre': usuario.nombre,
                'email': usuario.email,
                'telefono': usuario.telefono,
                'rol': usuario.rol,
            }
            
            if usuario.is_consumidor:
                try:
                    consumidor = usuario.consumidor
                    user_data['consumidor_id'] = consumidor.id
                    user_data['edad'] = consumidor.edad
                    user_data['peso'] = consumidor.peso
                    user_data['altura'] = consumidor.altura
                    user_data['genero'] = consumidor.genero
                    user_data['bmi'] = consumidor.bmi
                except Consumidor.DoesNotExist:
                    logger.warning(f"Consumidor profile not found for user {usuario.id}")
            
            elif usuario.is_administrador:
                try:
                    admin = usuario.administrador
                    user_data['administrador_id'] = admin.id
                    user_data['area_responsable'] = admin.area_responsable
                except Administrador.DoesNotExist:
                    logger.warning(f"Administrador profile not found for user {usuario.id}")
            
            auth_data = {
                'token': tokens['access'],
                'refresh_token': tokens['refresh'],
                'expires_in': 3600,
                'user': user_data
            }
            
            logger.info(f"Successful login: {email} (rol: {usuario.rol})")
            return True, auth_data, None
        
        except Usuario.DoesNotExist:
            logger.warning(f"Failed login: {email} (user not found)")
            return False, None, "Invalid credentials"
        
        except Exception as e:
            logger.error(f"Authentication error for {email}: {str(e)}")
            return False, None, "Authentication failed"
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        
        if not any(c.isalpha() for c in password):
            return False, "Password must contain at least one letter"
        
        has_digit = any(c.isdigit() for c in password)
        if not has_digit:
            logger.info("Password created without digits (weak)")
        
        return True, None
    
    @staticmethod
    def email_exists(email: str) -> bool:
        return Usuario.objects.filter(email=email).exists()

