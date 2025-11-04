from Be_men_user.models import User
from rest_framework import generics, status, filters
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from .serializer import AdminUserSerializer
from django.db.models import Q  # ✅ imported Q properly


class AdminUserListView(generics.ListAPIView):
    queryset = User.objects.filter(is_staff=False)
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()

        # ✅ Case-insensitive search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone_number__icontains=search)
            )

        return queryset.order_by('-id')



class AdminUserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.filter(is_staff=False)
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]


class AdminBanUserView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk, is_staff=False)
            user.is_banned = not user.is_banned
            user.save()
            status_msg = "banned" if user.is_banned else "unbanned"
            return Response({"message": f"User {status_msg} successfully"})
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )
