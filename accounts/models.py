from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):   

    def create_user(self, email, full_name, phone_number, password=None, **extra_fields):       
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not phone_number:
            raise ValueError(_('The Phone Number field must be set'))
        if not full_name:
            raise ValueError(_('Your Full names are needed'))
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            full_name=full_name,
            phone_number=phone_number,  
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, phone_number, password=None, **extra_fields):
       
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'ADMIN')  
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True'))
        
        return self.create_user(email, full_name, phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin): 
   
    STAFF = 'STAFF'
    ADMIN = 'ADMIN'
    CUSTOMER = 'CUSTOMER'
    
    USER_TYPE_CHOICES = [
        (STAFF, 'Staff Member'),
        (ADMIN, 'Administrator'),
        (CUSTOMER, 'Customer'),
    ]
    
  
    
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        }
    )
    
    phone_number = models.CharField(
       
        max_length=10,  
        unique=True,
       
    )
    
    full_name = models.CharField(_('full name'), max_length=50, )
    
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default=CUSTOMER 
    )    
    
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)  
    
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)  
    
    objects = UserManager()    
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'phone_number']  
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return self.full_name  
    
    @property
    def is_admin(self):        
        return self.user_type == self.ADMIN  
    
    @property
    def is_staff_member(self): 
        return self.user_type == self.STAFF
    
    @property
    def is_customer(self):
        return self.user_type == self.CUSTOMER  
    
    @property
    def display_name(self):
        return self.full_name if self.full_name else self.email


class VerificationCode(models.Model):    
    
    REGISTER = 'REGISTER'
    RESET_PASSWORD = 'RESET_PASSWORD'
    CHANGE_EMAIL = 'CHANGE_EMAIL'

    LABEL_CHOICES = [
        (REGISTER, 'Register'),
        (RESET_PASSWORD, 'Reset Password'),
        (CHANGE_EMAIL, 'Change Email'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='verification_codes'
    )
    code = models.CharField(max_length=6)
    label = models.CharField(
        max_length=30, 
        choices=LABEL_CHOICES, 
        default=REGISTER
    )
    email = models.EmailField(max_length=255, blank=True, null=True)
    is_pending = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'code', 'label']),
        ]
        unique_together = ('code', 'user')

    def __str__(self):
        email = self.user.email if self.user else (self.email or "No email") 
        return f"{email} - {self.label} - {self.code}"

    @property
    def is_valid(self):
        expiration_time = self.created_on + settings.VERIFICATION_CODE_LIFETIME
        return timezone.now() < expiration_time and self.is_pending