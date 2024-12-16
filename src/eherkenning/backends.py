from django.contrib.auth import get_user_model

from digid_eherkenning.backends import eHerkenningBackend as _eHerkenningBackend
from digid_eherkenning.exceptions import eHerkenningError
from digid_eherkenning.utils import get_client_ip

from open_inwoner.kvk.branches import KVK_BRANCH_SESSION_VARIABLE

UserModel = get_user_model()


class eHerkenningBackend(_eHerkenningBackend):
    """
    Custom backend to identify users based on the KvK number instead of RSIN
    """

    def get_company_branch_number(self, attributes):
        company_branch_number = attributes.get(
            "urn:etoegang:1.9:ServiceRestriction:Vestigingsnr", None
        )
        return company_branch_number

    def get_or_create_user(self, request, saml_response, saml_attributes):
        kvk = self.get_kvk_number(saml_attributes)
        if kvk == "":
            raise eHerkenningError(
                "Login failed due to no KvK being returned by eHerkenning."
            )

        created = False
        try:
            user = UserModel.eherkenning_objects.get_by_kvk(kvk)
        except UserModel.DoesNotExist:
            user = UserModel.eherkenning_objects.eherkenning_create(kvk)
            created = True

        if vestigingsnummer := self.get_company_branch_number(saml_attributes):
            self.request.session[KVK_BRANCH_SESSION_VARIABLE] = vestigingsnummer
            self.request.session.save()

        success_message = self.error_messages["login_success"] % {
            "user": str(user),
            "user_info": " (new account)" if created else "",
            "ip": get_client_ip(request),
            "service": self.service_name,
        }

        self.log_success(request, success_message)

        return user, created
