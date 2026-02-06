import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils.text import slugify

class ServiceCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, blank=True, null=True)
    description = models.TextField( unique=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    class Meta:
        ordering = [ "name"]
        verbose_name = "Service Category"
        verbose_name_plural = "Service Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, blank=True, null=True)
    short_description = models.CharField(max_length=255, unique=True)
    detailed_description = models.TextField(max_length=2000, null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
    currency = models.CharField(max_length=3, default="RWF", blank=True)
    material = models.CharField(max_length=100, blank=True)

    length = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
    width = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
    height = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)

    #product_volume = models.DecimalField(max_digits=10, decimal_places=2, editable=False, null=True, blank=True)
    measurement_unit = models.CharField(max_length=10, default="cm", blank=True)
 
    published = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # NEW: Product variations (simple text fields)
    available_sizes = models.CharField(max_length=200, blank=True, help_text="e.g., Small, Medium, Large")
    available_colors = models.CharField(max_length=200, blank=True, help_text="e.g., Red, Blue, Green")
    available_materials = models.CharField(max_length=200, blank=True, help_text="e.g., PLA, ABS, Resin")
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

    @property
    def product_volume(self):
        return self.length * self.width * self.height

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


def validate_image_size(file):
    limit_mb = 110
    if file.size > limit_mb * 1024 * 1024:
        raise ValidationError(f'Max file size is {limit_mb}MB')

def validate_video_size(file):
    limit_mb = 500
    if file.size > limit_mb * 1024 * 1024:
        raise ValidationError(f'Max file size is {limit_mb}MB')

class ProductMedia(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, related_name="media", on_delete=models.CASCADE)
    
    model_3d = models.FileField(upload_to="products/models/", blank=True, null=True)
    alt_text = models.CharField(max_length=200, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    video_url = models.URLField(max_length=200, blank=True)

    image = models.ImageField(
        upload_to="products/images/", 
        blank=True, 
        null=True,
        validators=[validate_image_size]
    )
    video_file = models.FileField(
        upload_to="products/videos/", 
        blank=True, 
        null=True,
        validators=[validate_video_size]
    )

    class Meta:
        ordering = ['display_order']
        verbose_name = "Product Media"
        verbose_name_plural = "Product Media"
    

class Feedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, related_name="feedbacks", on_delete=models.CASCADE)
    client_name = models.CharField(max_length=200)
    message = models.TextField()
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedbacks")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Feedback"
        verbose_name_plural = "Feedback"

#customer request
class CustomRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    

    client_name = models.CharField(max_length=200)
    client_email = models.EmailField()
    client_phone = models.CharField(max_length=20)
    
   
    service_category = models.ForeignKey(
        ServiceCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Optional: What service is this related to?"
    )
    title = models.CharField(max_length=200, help_text="Brief title of what you need")
    description = models.TextField(help_text="Detailed description of your request")
    
    
    reference_file = models.FileField(
        upload_to="custom_requests/", 
        blank=True, 
        null=True,
        help_text="Upload reference images or sketches"
    )
    
    budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Your approximate budget in RWF"
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Custom Request"
        verbose_name_plural = "Custom Requests"

    def __str__(self):
        return f"{self.client_name} - {self.title}"


