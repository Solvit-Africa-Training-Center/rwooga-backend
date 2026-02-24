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
    Anyone (including guests) can create feedback and view published ones.
    Only staff can moderate (publish/unpublish) or delete.
    """
    def has_permission(self, request, view):
        if view.action in ['list', 'retrieve']:
            return True

        if view.action == 'create':
            return True  # Open to everyone — admin approves before publishing

        # Only staff can update/delete/moderate feedback
        return request.user and request.user.is_authenticated and request.user.is_staff

class AnyoneCanCreateRequest(permissions.BasePermission):
    """
    Anyone can create a custom request.
    Users can view and manage their own requests.
    Staff can view and manage all requests.
    """
    def has_permission(self, request, view):
        # Anyone can create
        if view.action == 'create':
            return True
        
        # Must be authenticated for other actions
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff can do anything
        if request.user.is_staff:
            return True
            
        # Users can only access their own requests
        # If the request has no user, it belongs to no one (only staff)
        return obj.user == request.user
    
class IsOwnerOnly(permissions.BasePermission):
    """
    Users can only access their own wishlist
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user