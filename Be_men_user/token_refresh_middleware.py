from django.http import JsonResponse
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


class TokenRefreshMiddleware:
    """
    Middleware to automatically refresh access tokens if expired and refresh token is valid.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        access_token = request.COOKIES.get("access_token")
        refresh_token = request.COOKIES.get("refresh_token")

        # If access token exists, try to validate it
        if access_token:
            try:
                AccessToken(access_token)  # Valid token
            except TokenError:
                # Access token expired or invalid
                if refresh_token:
                    try:
                        new_access = str(RefreshToken(refresh_token).access_token)
                        # Attach the new access token to request for downstream usage
                        request.COOKIES["access_token"] = new_access
                    except TokenError:
                        # Refresh token invalid or expired
                        response = JsonResponse(
                            {"detail": "Session expired. Please log in again."},
                            status=401,
                        )
                        response.delete_cookie("access_token")
                        response.delete_cookie("refresh_token")
                        return response
                else:
                    # No refresh token
                    response = JsonResponse(
                        {"detail": "Session expired. Please log in again."}, status=401
                    )
                    response.delete_cookie("access_token")
                    response.delete_cookie("refresh_token")
                    return response

        # Call the next middleware/view
        response = self.get_response(request)

        # If new access token was generated, set it in cookie
        if access_token and refresh_token:
            try:
                new_access
            except NameError:
                # No new access generated
                pass
            else:
                response.set_cookie(
                    key="access_token",
                    value=new_access,
                    httponly=True,
                    secure=True,  # True only in HTTPS
                    samesite="None",  # Needed for cross-domain
                )

        return response
