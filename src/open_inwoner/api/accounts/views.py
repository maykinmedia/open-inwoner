from django.conf import settings

from dj_rest_auth.app_settings import TokenSerializer
from dj_rest_auth.views import TokenModel, create_token, sensitive_post_parameters_m
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class GetAuthTokenView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)
    token_model = TokenModel
    throttle_scope = "dj_rest_auth"

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {"request": self.request, "format": self.format_kwarg, "view": self}

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_response_serializer(self):
        return TokenSerializer

    def get_response(self):
        self.token = create_token(
            self.token_model,
            self.request.user,
            None,
        )

        serializer_class = self.get_response_serializer()
        serializer = serializer_class(
            instance=self.token,
            context=self.get_serializer_context(),
        )

        response = Response(serializer.data, status=status.HTTP_200_OK)
        return response

    def get(self, request, *args, **kwargs):
        self.request = request
        # Check that the token should be returned.
        return self.get_response()
