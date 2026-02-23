from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import Order
from .serializers import OrderSerializer


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