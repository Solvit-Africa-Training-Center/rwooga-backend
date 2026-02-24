from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, BasePermission
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from .models import Order, Refund, Return
from .serializers import (
    OrderSerializer,
    RefundSerializer,
    RefundCompleteSerializer,
    ReturnApproveSerializer,
    ReturnRejectSerializer,
    ReturnSerializer,
)


class IsAdminOrStaff(BasePermission):
    """Allow access only to admin or staff users."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_staff or getattr(request.user, 'is_admin', False))
        )


@extend_schema(tags=["Orders"])
class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()

        user = self.request.user

        if user.is_staff:
            return Order.objects.prefetch_related('items__product').all()

        return Order.objects.prefetch_related('items__product').filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status != 'PENDING':
            return Response(
                {"detail": "Only PENDING orders can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = 'CANCELLED'
        order.save(update_fields=['status'])
        return Response({"detail": "Order cancelled successfully."}, status=status.HTTP_200_OK)

    @extend_schema(summary="Apply discount to an order")
    @action(detail=True, methods=['post'], url_path='apply-discount')
    def apply_discount(self, request, pk=None):
        order = self.get_object()
        if order.status != 'PENDING':
            return Response(
                {"detail": "Discount can only be applied to PENDING orders."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not order.discount:
            return Response(
                {"detail": "No discount linked to this order."},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.apply_discount()
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Get order summary")
    @action(detail=True, methods=['get'], url_path='summary')
    def summary(self, request, pk=None):
        order = self.get_object()
        return Response({
            "order_id": order.id,
            "status": order.status,
            "subtotal": order.subtotal,
            "discount_amount": order.discount_amount,
            "total_amount": order.total_amount,
            "items_count": order.items.count(),
        })


@extend_schema(tags=["Returns"])
class ReturnViewSet(viewsets.ModelViewSet):
    serializer_class = ReturnSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['return_number', 'reason', 'detailed_reason']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Return.objects.none()
        if not self.request.user.is_authenticated:
            return Return.objects.none()

        user = self.request.user

        if user.is_staff or getattr(user, 'is_admin', False):
            return Return.objects.all().select_related('order', 'user')

        return Return.objects.filter(user=user).select_related('order')

    def get_permissions(self):
        if self.action in ('approve', 'reject', 'complete'):
            return [IsAdminOrStaff()]
        return [permissions.IsAuthenticated()]

    @extend_schema(summary="Approve a return request (admin/staff only)")
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a return request. Admin/staff only."""
        return_obj = self.get_object()

        if return_obj.status != 'REQUESTED':
            return Response(
                {'error': f'Cannot approve a return with status "{return_obj.get_status_display()}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ReturnApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approved_amount = serializer.validated_data.get('approved_refund_amount')
        return_obj.approve(amount=approved_amount)

        return Response(ReturnSerializer(return_obj, context={'request': request}).data)

    @extend_schema(summary="Reject a return request (admin/staff only)")
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a return request with a reason. Admin/staff only."""
        return_obj = self.get_object()

        if return_obj.status != 'REQUESTED':
            return Response(
                {'error': f'Cannot reject a return with status "{return_obj.get_status_display()}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ReturnRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return_obj.reject(reason=serializer.validated_data['rejection_reason'])

        return Response(ReturnSerializer(return_obj, context={'request': request}).data)

    @extend_schema(summary="Mark a return as completed (admin/staff only)")
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a return as completed. Admin/staff only."""
        return_obj = self.get_object()

        if return_obj.status != 'APPROVED':
            return Response(
                {'error': f'Cannot complete a return with status "{return_obj.get_status_display()}". Only APPROVED returns can be completed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return_obj.status = 'COMPLETED'
        return_obj.save()

        return Response(ReturnSerializer(return_obj, context={'request': request}).data)

    @extend_schema(summary="Cancel your own return request")
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_return(self, request, pk=None):
        """Cancel a return request. Only the owner can cancel their own REQUESTED return."""
        return_obj = self.get_object()

        if return_obj.user != request.user and not (request.user.is_staff or getattr(request.user, 'is_admin', False)):
            return Response(
                {'error': 'You do not have permission to cancel this return.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if return_obj.status != 'REQUESTED':
            return Response(
                {'error': f'Cannot cancel a return with status "{return_obj.get_status_display()}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return_obj.status = 'CANCELLED'
        return_obj.save()

        return Response(ReturnSerializer(return_obj, context={'request': request}).data)


@extend_schema(tags=["Refunds"])
class RefundViewSet(viewsets.ModelViewSet):
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['refund_number', 'reason']
    ordering_fields = ['created_at', 'amount', 'status']
    ordering = ['-created_at']
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Refund.objects.none()
        if not self.request.user.is_authenticated:
            return Refund.objects.none()

        user = self.request.user

        if user.is_staff or getattr(user, 'is_admin', False):
            return Refund.objects.all().select_related('order', 'user')

        return Refund.objects.filter(user=user).select_related('order')

    def get_permissions(self):
        if self.action in ('complete', 'fail'):
            return [IsAdminOrStaff()]
        return [permissions.IsAuthenticated()]

    @extend_schema(summary="Mark a refund as completed (admin/staff only)")
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark refund as completed. Admin/staff only."""
        refund = self.get_object()

        if refund.status != 'PENDING':
            return Response(
                {'error': f'Cannot complete a refund with status "{refund.get_status_display()}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RefundCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        transaction_id = serializer.validated_data.get('transaction_id', '')
        refund.mark_completed(transaction_id=transaction_id or None)

        return Response(RefundSerializer(refund, context={'request': request}).data)

    @extend_schema(summary="Mark a refund as failed (admin/staff only)")
    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """Mark a refund as failed. Admin/staff only."""
        refund = self.get_object()

        if refund.status != 'PENDING':
            return Response(
                {'error': f'Cannot fail a refund with status "{refund.get_status_display()}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refund.status = 'FAILED'
        refund.save()

        return Response(RefundSerializer(refund, context={'request': request}).data)