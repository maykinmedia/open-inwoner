from django.contrib.auth import get_user_model

from digid_eherkenning.backends import eHerkenningBackend as _eHerkenningBackend
from digid_eherkenning.exceptions import eHerkenningError
from digid_eherkenning.utils import get_client_ip

UserModel = get_user_model()


class eHerkenningBackend(_eHerkenningBackend):
    """
    Custom backend to identify users based on the KvK number instead of RSIN
    """

    def get_or_create_user(self, request, saml_response, saml_attributes):
        kvk = self.get_kvk_number(saml_attributes)
        if kvk == "":
            error_message = "Login failed due to no KvK being returned by eHerkenning."
            raise eHerkenningError(error_message)

        created = False
        try:
            user = UserModel.eherkenning_objects.get_by_kvk(kvk)
        except UserModel.DoesNotExist:
            user = UserModel.eherkenning_objects.eherkenning_create(kvk)
            created = True

        success_message = self.error_messages["login_success"] % {
            "user": str(user),
            "user_info": " (new account)" if created else "",
            "ip": get_client_ip(request),
            "service": self.service_name,
        }

        self.log_success(request, success_message)

        return user, created
