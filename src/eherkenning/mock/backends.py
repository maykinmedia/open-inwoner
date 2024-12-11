import logging
import re

from django.contrib.auth import get_user_model

from digid_eherkenning.backends import BaseBackend
from digid_eherkenning.utils import get_client_ip

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class eHerkenningBackend(BaseBackend):
    service_name = "eHerkenning"
    error_messages = dict(
        BaseBackend.error_messages,
        **{
            "eherkenning_no_kvk": "Login failed due to no KvK being returned by eHerkenning.",
            "eherkenning_len_kvk": "Login failed due to no KvK having more then 8 digits.",
            "eherkenning_num_kvk": "Login failed due to no KvK not being numerical.",
        }
    )

    def get_or_create_user(self, request, kvk):
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

    def authenticate(self, request, kvk=None):
        if kvk is None:
            return

        if kvk == "":
            self.log_error(request, self.error_messages["eherkenning_no_kvk"])
            return

        if not re.match(r"^[0-9]+$", kvk):
            self.log_error(request, self.error_messages["eherkenning_len_kvk"])
            return

        if len(kvk) > 8:
            self.log_error(request, self.error_messages["eherkenning_num_kvk"])
            return

        user, created = self.get_or_create_user(request, kvk)

        return user
