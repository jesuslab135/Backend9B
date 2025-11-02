"""
Service Layer
=============
Business logic layer separating concerns from views.

Design Patterns:
- Service Layer Pattern: Business logic separate from controllers
- Dependency Injection: Services injected into views
"""

from .auth_service import AuthenticationService
from .user_factory import UserFactory

__all__ = ['AuthenticationService', 'UserFactory']
