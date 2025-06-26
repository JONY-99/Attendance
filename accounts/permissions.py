from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    

    def has_object_permission(self, request, view, obj):
        # Har doim GET, HEAD yoki OPTIONS so'rovlariga ruxsat beriladi
        if request.method in permissions.SAFE_METHODS:
            return True

        # Faqat obyekt egasi uchun yozish ruxsat etiladi
        return obj.owner == request.user