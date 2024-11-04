from .actions import (
    ActionCreateView,
    ActionExportView,
    ActionHistoryView,
    ActionListExportView,
    ActionListView,
    ActionPrivateMediaView,
    ActionUpdateStatusTagView,
    ActionUpdateView,
)
from .auth import (
    CustomDigiDAssertionConsumerServiceMockView,
    CustomDigiDAssertionConsumerServiceView,
    CustomeHerkenningAssertionConsumerServiceMockView,
    CustomeHerkenningAssertionConsumerServiceView,
    LogPasswordChangeView,
    LogPasswordResetConfirmView,
    LogPasswordResetView,
)
from .auth_oidc import (
    OIDCFailureView,
    digid_callback,
    digid_init,
    digid_logout,
    eherkenning_callback,
    eherkenning_init,
    eherkenning_logout,
)
from .contacts import (
    ContactApprovalView,
    ContactCreateView,
    ContactDeleteView,
    ContactListView,
)
from .csrf import csrf_failure
from .document import DocumentPrivateMediaView
from .documents import DocumentDeleteView
from .invite import InviteAcceptView
from .login import (
    AddPhoneNumberWizardView,
    CustomLoginView,
    ResendTokenView,
    VerifyTokenView,
)
from .password_reset import PasswordResetView
from .profile import (
    EditProfileView,
    MyCategoriesView,
    MyDataView,
    MyNotificationsView,
    MyProfileView,
    UserAppointmentsView,
)
from .registration import CustomRegistrationView, NecessaryFieldsUserView

__all__ = [
    "ActionCreateView",
    "ActionExportView",
    "ActionHistoryView",
    "ActionListExportView",
    "ActionListView",
    "ActionPrivateMediaView",
    "ActionUpdateStatusTagView",
    "ActionUpdateView",
    "CustomDigiDAssertionConsumerServiceMockView",
    "CustomDigiDAssertionConsumerServiceView",
    "CustomeHerkenningAssertionConsumerServiceMockView",
    "CustomeHerkenningAssertionConsumerServiceView",
    "LogPasswordChangeView",
    "LogPasswordResetConfirmView",
    "LogPasswordResetView",
    "ContactApprovalView",
    "ContactCreateView",
    "ContactDeleteView",
    "ContactListView",
    "csrf_failure",
    "DocumentPrivateMediaView",
    "DocumentDeleteView",
    "InviteAcceptView",
    "AddPhoneNumberWizardView",
    "CustomLoginView",
    "ResendTokenView",
    "VerifyTokenView",
    "PasswordResetView",
    "EditProfileView",
    "MyCategoriesView",
    "MyDataView",
    "MyNotificationsView",
    "MyProfileView",
    "UserAppointmentsView",
    "CustomRegistrationView",
    "NecessaryFieldsUserView",
    # OIDC
    "OIDCFailureView",
    "digid_init",
    "digid_callback",
    "digid_logout",
    "eherkenning_init",
    "eherkenning_callback",
    "eherkenning_logout",
]
