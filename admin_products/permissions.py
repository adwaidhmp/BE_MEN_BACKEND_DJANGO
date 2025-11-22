from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        # SAFE methods = GET, HEAD, OPTIONS → allow everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For POST, PUT, PATCH, DELETE → only admin users allowed
        return request.user and request.user.is_staff
