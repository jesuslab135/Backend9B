"""
User Factory
============
Factory pattern for creating users with different roles.

Design Pattern: Factory Pattern
Creates different types of users (Consumidor, Administrador) based on role.
"""

import logging
from typing import Dict, Tuple
from django.db import transaction
from api.models import Usuario, Consumidor, Administrador, RolChoices, GeneroChoices

logger = logging.getLogger(__name__)


class UserFactory:
    """
    Factory for creating users with role-specific profiles.
    
    Design Pattern: Factory Pattern
    Encapsulates object creation logic based on user role.
    
    Benefits:
    - Single place for user creation logic
    - Easy to extend with new roles
    - Ensures atomic transactions
    """
    
    @staticmethod
    @transaction.atomic
    def create_user(user_data: Dict) -> Tuple[Usuario, bool, str]:
        """
        Create a new user with role-specific profile.
        
        Args:
            user_data: Dictionary with user information
                Required: nombre, email, password, rol
                Optional: telefono, edad, peso, altura, genero, area_responsable
        
        Returns:
            Tuple of (usuario: Usuario, success: bool, message: str)
        
        Example:
            >>> data = {
            >>>     'nombre': 'John Doe',
            >>>     'email': 'john@example.com',
            >>>     'password': 'secure123',
            >>>     'rol': 'consumidor',
            >>>     'edad': 30,
            >>>     'genero': 'masculino'
            >>> }
            >>> usuario, success, msg = UserFactory.create_user(data)
        """
        try:
            rol = user_data.get('rol', RolChoices.CONSUMIDOR)
            
            # Validate role
            if rol not in [RolChoices.CONSUMIDOR, RolChoices.ADMINISTRADOR]:
                return None, False, f"Invalid role: {rol}"
            
            # Create base Usuario
            usuario = Usuario(
                nombre=user_data['nombre'],
                email=user_data['email'],
                telefono=user_data.get('telefono', ''),
                rol=rol
            )
            usuario.set_password(user_data['password'])
            usuario.save()
            
            # Create role-specific profile
            if rol == RolChoices.CONSUMIDOR:
                profile = UserFactory._create_consumidor_profile(usuario, user_data)
                logger.info(f"Created Consumidor: {usuario.email} (ID: {usuario.id}, Profile ID: {profile.id})")
            
            elif rol == RolChoices.ADMINISTRADOR:
                profile = UserFactory._create_administrador_profile(usuario, user_data)
                logger.info(f"Created Administrador: {usuario.email} (ID: {usuario.id}, Profile ID: {profile.id})")
            
            return usuario, True, f"User created successfully with role: {rol}"
        
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            return None, False, f"User creation failed: {str(e)}"
    
    @staticmethod
    def _create_consumidor_profile(usuario: Usuario, data: Dict) -> Consumidor:
        """
        Create Consumidor profile for a user.
        Profile is created with NULL values for edad, peso, altura, genero.
        These fields will be filled later via a separate form/endpoint.
        
        Args:
            usuario: Usuario instance
            data: Dictionary (edad, peso, altura, genero not used during registration)
        
        Returns:
            Consumidor: Created consumidor profile with NULL health data
        """
        consumidor = Consumidor.objects.create(
            usuario=usuario,
            edad=None,
            peso=None,
            altura=None,
            genero=GeneroChoices.MASCULINO  # Default value required by database
        )
        return consumidor
    
    @staticmethod
    def _create_administrador_profile(usuario: Usuario, data: Dict) -> Administrador:
        """
        Create Administrador profile for a user.
        No additional fields required.
        
        Args:
            usuario: Usuario instance
            data: Dictionary (not used, no extra fields for administrador)
        
        Returns:
            Administrador: Created administrador profile
        """
        administrador = Administrador.objects.create(
            usuario=usuario
        )
        return administrador
    
    @staticmethod
    def update_user(usuario: Usuario, update_data: Dict) -> Tuple[bool, str]:
        """
        Update user information.
        
        Args:
            usuario: Usuario instance to update
            update_data: Dictionary with fields to update
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with transaction.atomic():
                # Update base usuario fields
                if 'nombre' in update_data:
                    usuario.nombre = update_data['nombre']
                if 'telefono' in update_data:
                    usuario.telefono = update_data['telefono']
                if 'password' in update_data:
                    usuario.set_password(update_data['password'])
                
                usuario.save()
                
                # Update role-specific profile
                if usuario.is_consumidor and hasattr(usuario, 'consumidor'):
                    consumidor = usuario.consumidor
                    if 'edad' in update_data:
                        consumidor.edad = update_data['edad']
                    if 'peso' in update_data:
                        consumidor.peso = update_data['peso']
                    if 'altura' in update_data:
                        consumidor.altura = update_data['altura']
                    if 'genero' in update_data:
                        consumidor.genero = update_data['genero']
                    consumidor.save()
                
                elif usuario.is_administrador and hasattr(usuario, 'administrador'):
                    admin = usuario.administrador
                    if 'area_responsable' in update_data:
                        admin.area_responsable = update_data['area_responsable']
                    admin.save()
                
                logger.info(f"Updated user: {usuario.email}")
                return True, "User updated successfully"
        
        except Exception as e:
            logger.error(f"Failed to update user {usuario.id}: {str(e)}")
            return False, f"Update failed: {str(e)}"
