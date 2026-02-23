from rest_framework import serializers
from .models import Order, OrderItem
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
            if not product.is_for_sale:
                raise serializers.ValidationError(f"'{product.name}' is not available for sale.")
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