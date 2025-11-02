"""
Authentication Service
======================
Handles all authentication-related business logic.

Design Pattern: Service Layer Pattern
Separates authentication logic from view controllers.
"""

import logging
from typing import Dict, Optional, Tuple
from django.contrib.auth.hashers import check_password
from api.models import Usuario, Consumidor, Administrador

logger = logging.getLogger(__name__)


class AuthenticationService:
    """
    Service for handling user authentication.
    
    Responsibilities:
    - Validate credentials
    - Check user existence
    - Log authentication attempts
    - Return structured auth responses
    
    Design Pattern: Single Responsibility Principle
    """
    
    @staticmethod
    def authenticate(email: str, password: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User's email address
            password: Plain text password
        
        Returns:
            Tuple of (success: bool, user_data: dict, error: str)
        
        Example:
            >>> success, data, error = AuthenticationService.authenticate('user@example.com', 'password')
            >>> if success:
            >>>     print(f"Welcome {data['nombre']}")
        """
        try:
            usuario = Usuario.objects.get(email=email)
            
            if not usuario.check_password(password):
                logger.warning(f"Failed login: {email} (invalid password)")
                return False, None, "Invalid credentials"
            
            # Build response data
            user_data = {
                'user_id': usuario.id,
                'nombre': usuario.nombre,
                'email': usuario.email,
                'telefono': usuario.telefono,
                'rol': usuario.rol,
                'created_at': usuario.created_at.isoformat() if usuario.created_at else None
            }
            
            # Add role-specific data
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
            
            logger.info(f"Successful login: {email} (rol: {usuario.rol})")
            return True, user_data, None
        
        except Usuario.DoesNotExist:
            logger.warning(f"Failed login: {email} (user not found)")
            return False, None, "Invalid credentials"
        
        except Exception as e:
            logger.error(f"Authentication error for {email}: {str(e)}")
            return False, None, "Authentication failed"
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength.
        
        Args:
            password: Plain text password to validate
        
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        
        Rules:
        - Minimum 6 characters
        - At least one letter
        - At least one number (optional but recommended)
        """
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        
        if not any(c.isalpha() for c in password):
            return False, "Password must contain at least one letter"
        
        # Strong password recommendation (not enforced)
        has_digit = any(c.isdigit() for c in password)
        if not has_digit:
            logger.info("Password created without digits (weak)")
        
        return True, None
    
    @staticmethod
    def email_exists(email: str) -> bool:
        """
        Check if email is already registered.
        
        Args:
            email: Email address to check
        
        Returns:
            bool: True if email exists
        """
        return Usuario.objects.filter(email=email).exists()
