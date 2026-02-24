import uuid
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
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
  
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

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
        return max(self.subtotal - Decimal(str(self.discount_amount)), Decimal("0.00"))

    @property
    def can_be_returned(self):
        """Orders can be returned within 30 days of delivery"""
        if self.status != 'DELIVERED':
            return False
        if not self.updated_at:
            return False
        days_since_delivery = (timezone.now() - self.updated_at).days
        return days_since_delivery <= 30

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
    
class Return(models.Model):
    """Return requests for orders"""
    STATUS_CHOICES = [
        ('REQUESTED', 'Return Requested'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    return_number = models.CharField(max_length=50, unique=True, editable=False, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='returns')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='returns')
    reason = models.CharField(max_length=50)
    detailed_reason = models.TextField()
    rejection_reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    requested_refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    approved_refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['return_number']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        if not self.return_number:
            timestamp = timezone.now().strftime('%Y%m%d')
            self.return_number = f"RTN-{timestamp}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """Check if return is still active (not completed, cancelled, or rejected)"""
        return self.status not in ['COMPLETED', 'CANCELLED', 'REJECTED']

    def approve(self, amount=None):
        """Approve the return request"""
        self.status = 'APPROVED'
        self.approved_at = timezone.now()
        self.approved_refund_amount = amount or self.requested_refund_amount
        self.save()

    def reject(self, reason):
        """Reject the return request with a reason"""
        self.status = 'REJECTED'
        self.rejection_reason = reason
        self.save()

    def __str__(self):
        return f"{self.return_number} - Order {self.order.id}"


class Refund(models.Model):
    """Refund transactions"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    refund_number = models.CharField(max_length=50, unique=True, editable=False, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refunds')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    transaction_id = models.CharField(max_length=100, blank=True)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['refund_number']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        if not self.refund_number:
            timestamp = timezone.now().strftime('%Y%m%d')
            self.refund_number = f"REF-{timestamp}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def mark_completed(self, transaction_id=None):
        """Mark refund as completed"""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        if transaction_id:
            self.transaction_id = transaction_id
        self.save()

    def __str__(self):
        return f"{self.refund_number} - {self.amount}"