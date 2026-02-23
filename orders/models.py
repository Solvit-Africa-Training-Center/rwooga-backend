import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from products.models import Product, Discount  
User = get_user_model()


class Order(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')

    discount = models.ForeignKey(
        Discount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        help_text="Order-level discount applied at checkout"
    )
  
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def apply_discount(self):
      
        if self.discount and self.discount.is_valid():
            subtotal = self.subtotal
            if self.discount.discount_type == Discount.PERCENTAGE:
                self.discount_amount = subtotal * (self.discount.discount_value / Decimal("100"))
            elif self.discount.discount_type == Discount.FIXED:
                self.discount_amount = self.discount.discount_value
        else:
            self.discount_amount = Decimal("0.00")
        self.save(update_fields=['discount_amount'])

    @property
    def subtotal(self):
       
        return sum(item.total_cost for item in self.items.all())

    @property
    def total_amount(self):
        return max(self.subtotal - self.discount_amount, Decimal("0.00"))

    def __str__(self):
        return f"Order {self.id} - {self.user.email}"


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['order']
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    @property
    def total_cost(self):
        return self.price_at_purchase * self.quantity

    def save(self, *args, **kwargs):
       
        if self.product and not self.price_at_purchase:
            self.price_at_purchase = self.product.get_final_price()
        super().save(*args, **kwargs)

    def __str__(self):
        product_name = self.product.name if self.product else "Deleted Product"
        return f"{self.quantity} x {product_name}"