from rest_framework import permissions

class IsSameSchool(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return getattr(obj, "school_id", None) == getattr(request.user, "school_id", None)