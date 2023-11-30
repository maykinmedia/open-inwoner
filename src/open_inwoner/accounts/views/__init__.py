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
    MyDataView,
    MyNotificationsView,
    MyProfileExportView,
    MyProfileView,
)
from .registration import CustomRegistrationView, NecessaryFieldsUserView
