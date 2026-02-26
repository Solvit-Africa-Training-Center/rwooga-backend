from rest_framework import serializers
from .models import Order, OrderItem, Refund, Return
from products.models import Product, Discount


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price_at_purchase', 'total_cost']
        read_only_fields = ['price_at_purchase', 'total_cost']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'discount', 'discount_amount',
            'subtotal', 'total_amount', 'status',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'discount_amount', 'subtotal', 'total_amount', 'status']

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("An order must have at least one item.")
        return items

    def validate(self, attrs):
       
        for item in attrs.get('items', []):
            product = item.get('product')
            if not product:
                raise serializers.ValidationError("Each item must have a valid product.")
            if product.unit_price is None:
                raise serializers.ValidationError(f"'{product.name}' does not have a price set.")
        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        discount = validated_data.get('discount', None)
      
        order = Order.objects.create(**validated_data)
     
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        if discount:
            order.apply_discount()

        return order
class ReturnSerializer(serializers.ModelSerializer):
    """Serializer for return requests"""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Return
        fields = [
            'id',
            'return_number',
            'order',
            'order_number',
            'user',
            'user_name',
            'reason',
            'detailed_reason',
            'rejection_reason',
            'status',
            'status_display',
            'is_active',
            'requested_refund_amount',
            'approved_refund_amount',
            'created_at',
            'approved_at',
        ]
        read_only_fields = [
            'id',
            'return_number',
            'user',
            'status',
            'rejection_reason',
            'approved_refund_amount',
            'created_at',
            'approved_at',
        ]
    
    def validate_order(self, value):
        """Validate order is eligible for return"""
        user = self.context['request'].user
        
        if value.user != user:
            raise serializers.ValidationError("You can only request returns for your own orders.")
        
        if not value.can_be_returned:
            raise serializers.ValidationError(
                "This order is not eligible for return. Orders can only be returned within 30 days of delivery."
            )
        
        active_returns = Return.objects.filter(
            order=value,
            status__in=['REQUESTED', 'APPROVED']
        )
        if active_returns.exists():
            raise serializers.ValidationError("There is already an active return request for this order.")
        
        return value
    
    def validate_requested_refund_amount(self, value):
        """Validate refund amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Refund amount must be greater than zero.")
        return value
    
    def create(self, validated_data):
        """Create return request with current user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ReturnApproveSerializer(serializers.Serializer):
    """Serializer for approving returns (admin only)"""
    approved_refund_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )
    
    def validate_approved_refund_amount(self, value):
        """Validate approved amount is positive"""
        if value and value <= 0:
            raise serializers.ValidationError("Approved refund amount must be greater than zero.")
        return value


class ReturnRejectSerializer(serializers.Serializer):
    """Serializer for rejecting returns (admin only)"""
    rejection_reason = serializers.CharField(required=True)
    
    def validate_rejection_reason(self, value):
        """Validate rejection reason is provided"""
        if not value.strip():
            raise serializers.ValidationError("Rejection reason is required.")
        return value


class RefundSerializer(serializers.ModelSerializer):
    """Serializer for refunds"""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Refund
        fields = [
            'id',
            'refund_number',
            'order',
            'order_number',
            'user',
            'user_name',
            'amount',
            'status',
            'status_display',
            'transaction_id',
            'reason',
            'created_at',
            'completed_at',
        ]
        read_only_fields = [
            'id',
            'refund_number',
            'user',
            'status',
            'transaction_id',
            'created_at',
            'completed_at',
        ]
    
    def validate_amount(self, value):
        """Validate refund amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Refund amount must be greater than zero.")
        return value
    
    def validate_order(self, value):
        """Validate user owns the order"""
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError("You can only request refunds for your own orders.")
        return value
    
    def create(self, validated_data):
        """Create refund with current user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class RefundCompleteSerializer(serializers.Serializer):
    """Serializer for completing refunds (admin only)"""
    transaction_id = serializers.CharField(required=False, allow_blank=True)