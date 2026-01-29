from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
import random

from accounts.serializers import CustomTokenObtainPairSerializer, UserSerializer
from .permissions import IsAdmin, IsOwnerOrAdmin
from .serializers import (
    UserSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer,
    UserProfileSerializer
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
   
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_fields = [ 'is_active', 'is_staff']
    search_fields = ['email', 'full_name', 'phone_number']
    ordering_fields = ['date_joined', 'full_name', 'email']
    ordering = ['-date_joined']

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        elif self.action == "list":
            return [IsAuthenticated(), IsAdmin()]
        elif self.action in ["retrieve", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):       
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'status': 'User activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):      
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'status': 'User deactivated'})


class LoginMixin(viewsets.ViewSet):    
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):        
        serializer = self.serializer_class(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class AuthViewSet(viewsets.GenericViewSet):
    
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer  
    def get_serializer_class(self):        
        if self.action == 'register':
            return UserRegistrationSerializer
        elif self.action == 'login':
            return UserLoginSerializer
        elif self.action == 'password_reset_request':
            return PasswordResetRequestSerializer
        elif self.action == 'password_reset_confirm':
            return PasswordResetConfirmSerializer
        return UserLoginSerializer
    
    @action(detail=False, methods=['post'])
    def register(self, request):
     
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Login user with email/username and password"""
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout user by blacklisting refresh token"""
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'status': 'Successfully logged out'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        """Request password reset - sends verification code"""
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                code = str(random.randint(100000, 999999))
                
                # You'll need to implement VerificationCode model
                # VerificationCode.objects.create(
                #     user=user,
                #     email=email,
                #     code=code,
                #     label=VerificationCode.RESET_PASSWORD
                # )
                
                return Response({
                    'status': 'Verification code sent',
                })
            except User.DoesNotExist:
                return Response(
                    {'error': 'User with this email does not exist'},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request):
        """Confirm password reset with verification code"""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            new_password = serializer.validated_data['new_password']
            
            try:
                user = User.objects.get(email=email)
                # Verify code logic here
                # verification = VerificationCode.objects.get(...)
                
                user.set_password(new_password)
                user.save()
                
                return Response({'status': 'Password reset successful'})
            
            except User.DoesNotExist:
                return Response(
                    {'error': 'Invalid user'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileViewSet(viewsets.GenericViewSet):
    """
    ViewSet for user profile operations
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update current user profile"""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change current user password"""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'status': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)