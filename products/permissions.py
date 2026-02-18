from rest_framework import permissions


class IsAdminOrStaffOrReadOnly(permissions.BasePermission):
    """
    Admin/Staff: Full access to products
    Customers: Read-only
    """
    def has_permission(self, request, view):
       
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsStaffOnly(permissions.BasePermission):
    """
    Only staff can create/update/delete products and categories
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class CustomerCanCreateFeedback(permissions.BasePermission):
    """
    Anyone can create feedback and view published ones
    Only staff can moderate (publish/unpublish)
    """
    def has_permission(self, request, view):
        if view.action in ['list', 'retrieve']:
            return True

        if view.action == 'create':
            return request.user and request.user.is_authenticated
        # Only staff can update/delete feedback
        return request.user and request.user.is_authenticated and request.user.is_staff


class AnyoneCanCreateRequest(permissions.BasePermission):
    
    def has_permission(self, request, view):
        # Anyone can create
        if view.action in ['create']:
            return True
        # Must be authenticated for anything else
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff can do anything
        if request.user.is_staff:
            return True
        # Owner can view and edit their own request
        if view.action in ['retrieve', 'update', 'partial_update']:
            return obj.user == request.user
        # Only staff can delete
        return False
    
class IsOwnerOnly(permissions.BasePermission):
    """
    Users can only access their own wishlist
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user