import logging

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


@deconstructible
class UntilNowValidator:
    """
    Validate a datetime to not be in the future.

    This means that `now` is included.
    """

    message = _("Ensure this value is not in the future.")
    code = "future_not_allowed"

    @property
    def limit_value(self):
        return timezone.now()

    def __call__(self, value):
        if value > self.limit_value:
            raise ValidationError(self.message, code=self.code)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.message == other.message
            and self.code == other.code
        )
