from Be_men_user.models import User
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializer import AdminUserSerializer


class AdminUserListView(generics.ListAPIView):
    queryset = User.objects.filter(is_staff=False)
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]


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
