
from rest_framework.response import Response
from rest_framework import status
from utils.logger import Logger, log_request, log_exception

class LoggingMixin:
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = Logger.get_logger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )
    
    def initialize_request(self, request, *args, **kwargs):
        req = super().initialize_request(request, *args, **kwargs)
        self.logger.info(
            f"📥 {request.method} {request.path} | "
            f"Action: {getattr(self, 'action', 'unknown')}"
        )
        return req
    
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        
        status_emoji = "✓" if 200 <= response.status_code < 300 else "✗"
        self.logger.info(
            f"📤 {status_emoji} Response: {response.status_code} | "
            f"Action: {getattr(self, 'action', 'unknown')}"
        )
        
        return response
    
    def handle_exception(self, exc):
        log_exception(self.logger, exc, {
            'action': getattr(self, 'action', 'unknown'),
            'view': self.__class__.__name__
        })
        return super().handle_exception(exc)

class ConsumerFilterMixin:
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        consumidor_id = self.request.query_params.get('consumidor_id')
        
        if consumidor_id:
            if hasattr(queryset.model, 'consumidor_id'):
                queryset = queryset.filter(consumidor_id=consumidor_id)
                
                if hasattr(self, 'logger'):
                    self.logger.debug(
                        f"🔍 Filtering by consumidor_id: {consumidor_id}"
                    )
        
        return queryset

class TimestampMixin:
    
    def get_extra_kwargs(self):
        extra_kwargs = super().get_extra_kwargs() if hasattr(
            super(), 'get_extra_kwargs'
        ) else {}
        
        extra_kwargs.update({
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True}
        })
        
        return extra_kwargs

class BulkActionMixin:
    
    def bulk_delete(self, request):
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
    
    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        
        if hasattr(self, 'paginator') and self.paginator:
            response.data['total_pages'] = self.paginator.page.paginator.num_pages
            response.data['current_page'] = self.paginator.page.number
            response.data['page_size'] = self.paginator.page_size
        
        return response

