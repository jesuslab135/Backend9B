
import logging
from typing import Dict, Tuple
from django.db import transaction
from api.models import Usuario, Consumidor, Administrador, RolChoices, GeneroChoices

logger = logging.getLogger(__name__)

class UserFactory:
    
    @staticmethod
    @transaction.atomic
    def create_user(user_data: Dict) -> Tuple[Usuario, bool, str]:
        try:
            rol = user_data.get('rol', RolChoices.CONSUMIDOR)
            
            if rol not in [RolChoices.CONSUMIDOR, RolChoices.ADMINISTRADOR]:
                return None, False, f"Invalid role: {rol}"
            
            usuario = Usuario(
                nombre=user_data['nombre'],
                email=user_data['email'],
                telefono=user_data.get('telefono', ''),
                rol=rol
            )
            usuario.set_password(user_data['password'])
            usuario.save()
            
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
        genero = data.get('genero', None)
        
        consumidor = Consumidor.objects.create(
            usuario=usuario,
            edad=None,
            peso=None,
            altura=None,
            genero=genero
        )
        return consumidor
    
    @staticmethod
    def _create_administrador_profile(usuario: Usuario, data: Dict) -> Administrador:
        administrador = Administrador.objects.create(
            usuario=usuario
        )
        return administrador
    
    @staticmethod
    def update_user(usuario: Usuario, update_data: Dict) -> Tuple[bool, str]:
        try:
            with transaction.atomic():
                if 'nombre' in update_data:
                    usuario.nombre = update_data['nombre']
                if 'telefono' in update_data:
                    usuario.telefono = update_data['telefono']
                if 'password' in update_data:
                    usuario.set_password(update_data['password'])
                
                usuario.save()
                
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

