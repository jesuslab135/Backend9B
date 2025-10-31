"""
Reusable Mixins
===============
Provides common functionality that can be mixed into ViewSets.

Design Pattern: Mixin Pattern
Enables code reuse across multiple classes without inheritance chains.
"""

from rest_framework.response import Response
from rest_framework import status
from utils.logger import Logger, log_request, log_exception


class LoggingMixin:
    """
    Mixin to add automatic logging to ViewSet actions
    
    Logs all CRUD operations automatically.
    
    Usage:
        class MyViewSet(LoggingMixin, ModelViewSet):
            pass
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = Logger.get_logger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )
    
    def initialize_request(self, request, *args, **kwargs):
        """Override to log incoming requests"""
        req = super().initialize_request(request, *args, **kwargs)
        self.logger.info(
            f"📥 {request.method} {request.path} | "
            f"Action: {getattr(self, 'action', 'unknown')}"
        )
        return req
    
    def finalize_response(self, request, response, *args, **kwargs):
        """Override to log outgoing responses"""
        response = super().finalize_response(request, response, *args, **kwargs)
        
        status_emoji = "✓" if 200 <= response.status_code < 300 else "✗"
        self.logger.info(
            f"📤 {status_emoji} Response: {response.status_code} | "
            f"Action: {getattr(self, 'action', 'unknown')}"
        )
        
        return response
    
    def handle_exception(self, exc):
        """Override to log exceptions"""
        log_exception(self.logger, exc, {
            'action': getattr(self, 'action', 'unknown'),
            'view': self.__class__.__name__
        })
        return super().handle_exception(exc)


class ConsumerFilterMixin:
    """
    Mixin to automatically filter querysets by current consumer
    
    Assumes the model has a 'consumidor_id' field.
    
    Usage:
        class FormularioViewSet(ConsumerFilterMixin, ModelViewSet):
            pass
    """
    
    def get_queryset(self):
        """
        Filter queryset by consumidor_id from request
        
        Expects: ?consumidor_id=123 in query params
        """
        queryset = super().get_queryset()
        
        # Get consumidor_id from query params
        consumidor_id = self.request.query_params.get('consumidor_id')
        
        if consumidor_id:
            # Check if model has consumidor_id field
            if hasattr(queryset.model, 'consumidor_id'):
                queryset = queryset.filter(consumidor_id=consumidor_id)
                
                if hasattr(self, 'logger'):
                    self.logger.debug(
                        f"🔍 Filtering by consumidor_id: {consumidor_id}"
                    )
        
        return queryset


class TimestampMixin:
    """
    Mixin to handle timestamp fields in serializers
    
    Makes created_at and updated_at read-only.
    """
    
    def get_extra_kwargs(self):
        """Set timestamp fields as read-only"""
        extra_kwargs = super().get_extra_kwargs() if hasattr(
            super(), 'get_extra_kwargs'
        ) else {}
        
        extra_kwargs.update({
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True}
        })
        
        return extra_kwargs


class BulkActionMixin:
    """
    Mixin to add bulk actions to ViewSets
    
    Provides bulk_delete, bulk_update actions.
    
    Usage:
        class MyViewSet(BulkActionMixin, ModelViewSet):
            pass
        
        # DELETE /api/my-resource/bulk_delete/
        # Body: {"ids": [1, 2, 3]}
    """
    
    def bulk_delete(self, request):
        """
        Bulk delete multiple objects
        
        Request Body:
            {"ids": [1, 2, 3, ...]}
        """
        ids = request.data.get('ids', [])
        
        if not ids:
            return Response(
                {'error': 'No IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(id__in=ids)
        count = queryset.count()
        queryset.delete()
        
        if hasattr(self, 'logger'):
            self.logger.info(f"🗑️  Bulk deleted {count} objects")
        
        return Response(
            {'message': f'{count} objects deleted'},
            status=status.HTTP_204_NO_CONTENT
        )
    
    def bulk_update(self, request):
        """
        Bulk update multiple objects
        
        Request Body:
            {
                "ids": [1, 2, 3],
                "data": {"field": "value"}
            }
        """
        ids = request.data.get('ids', [])
        update_data = request.data.get('data', {})
        
        if not ids or not update_data:
            return Response(
                {'error': 'IDs and data required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(id__in=ids)
        count = queryset.update(**update_data)
        
        if hasattr(self, 'logger'):
            self.logger.info(f"✏️  Bulk updated {count} objects")
        
        return Response(
            {'message': f'{count} objects updated'},
            status=status.HTTP_200_OK
        )


class ReadOnlyMixin:
    """
    Mixin to make a ViewSet read-only
    
    Disables create, update, delete actions.
    
    Usage:
        class DashboardViewSet(ReadOnlyMixin, ModelViewSet):
            pass
    """
    
    def create(self, request, *args, **kwargs):
        return Response(
            {'error': 'Create operation not allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def update(self, request, *args, **kwargs):
        return Response(
            {'error': 'Update operation not allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def partial_update(self, request, *args, **kwargs):
        return Response(
            {'error': 'Update operation not allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def destroy(self, request, *args, **kwargs):
        return Response(
            {'error': 'Delete operation not allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


class PaginationMixin:
    """
    Mixin to add custom pagination info to responses
    
    Adds total count, page info to paginated responses.
    """
    
    def get_paginated_response(self, data):
        """Override to add extra pagination info"""
        response = super().get_paginated_response(data)
        
        # Add extra info
        if hasattr(self, 'paginator') and self.paginator:
            response.data['total_pages'] = self.paginator.page.paginator.num_pages
            response.data['current_page'] = self.paginator.page.number
            response.data['page_size'] = self.paginator.page_size
        
        return response