from django.contrib.auth import get_user_model

from digid_eherkenning.backends import eHerkenningBackend as _eHerkenningBackend
from digid_eherkenning.exceptions import eHerkenningError
from digid_eherkenning.utils import get_client_ip

from open_inwoner.accounts.eherkenning_session import EHerkenningSessionContext

UserModel = get_user_model()


class eHerkenningBackend(_eHerkenningBackend):
    """
    Custom backend to identify users based on the KvK number instead of RSIN
    """

    def _persist_eherkenning_params_to_session(self, request, user):
        session_context = EHerkenningSessionContext(request)
        session_context.persist_eherkenning_state_for_user(
            user=user,
            is_branch_restricted=bool(user.vestiging),
            initial_branch_selection_done=False,
        )

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

        vestigingsnummer = self.get_company_branch_number(saml_attributes)

        created = False
        try:
            user = UserModel.eherkenning_objects.get_by_kvk_and_vestiging(
                kvk=kvk, vestiging=vestigingsnummer
            )
        except UserModel.DoesNotExist:
            user = UserModel.eherkenning_objects.create(
                kvk=kvk, vestiging=vestigingsnummer
            )
            created = True

        self._persist_eherkenning_params_to_session(request, user)

        success_message = self.error_messages["login_success"] % {
            "user": str(user),
            "user_info": " (new account)" if created else "",
            "ip": get_client_ip(request),
            "service": self.service_name,
        }

        self.log_success(request, success_message)

        return user, created
