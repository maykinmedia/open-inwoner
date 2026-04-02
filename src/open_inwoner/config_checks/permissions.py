from abc import ABC, abstractmethod
from typing import Type

from django.contrib.auth import get_permission_codename
from django.db.models import Model
from django.http import HttpRequest


class BasePermission(ABC):
    @abstractmethod
    def has_permission(
        self,
        request: HttpRequest,
    ) -> bool:
        pass

    @abstractmethod
    def has_object_permission(
        self,
        request: HttpRequest,
        obj: Model,
    ) -> bool:
        pass

    @abstractmethod
    def get_error_message(
        self,
        obj: Model | Type[Model] | None,
    ) -> str:
        pass


class IsActiveAdminUser(BasePermission):
    def has_permission(self, request: HttpRequest) -> bool:
        user = request.user
        return user.is_authenticated and user.is_active and user.is_staff

    def has_object_permission(self, request: HttpRequest, obj: Model) -> bool:
        return True

    def get_error_message(self, obj=None) -> str:
        return "You must be an active staff member to perform this check."


class IsSuperUser(BasePermission):
    def has_permission(self, request: HttpRequest) -> bool:
        user = request.user
        return user.is_authenticated and user.is_active and user.is_superuser

    def has_object_permission(
        self,
        request: HttpRequest,
        obj: Model,
    ) -> bool:
        return True

    def get_error_message(self, obj=None) -> str:
        return "You must be a superuser to perform this check."


class HasModelPermission(BasePermission):
    def __init__(
        self,
        model: Type[Model],
        action: str,
    ):
        self.model = model
        self.action = action

    def _get_perm_string(self, obj: Model | Type[Model]) -> str:
        opts = obj._meta
        codename = get_permission_codename(self.action, opts)
        return f"{opts.app_label}.{codename}"

    def has_permission(self, request: HttpRequest) -> bool:
        perm_string = self._get_perm_string(self.model)
        return request.user.has_perm(perm_string)

    def has_object_permission(
        self,
        request: HttpRequest,
        obj: Model,
    ) -> bool:
        perm_string = self._get_perm_string(obj)
        return request.user.has_perm(perm_string, obj)

    def get_error_message(self, obj) -> str:
        if obj is None:
            return "Missing model context for permission check."

        perm_string = self._get_perm_string(obj)
        return f"User lacks the required model permission: {perm_string}"


class HasModelRead(HasModelPermission):
    def __init__(self, model: Type[Model]):
        super().__init__(model=model, action="view")

    def get_error_message(self, obj) -> str:
        if obj is None:
            return "You need view permission for this model."

        opts = obj._meta
        return f"You need 'View' permissions for {opts.verbose_name} to run this."


class HasModelWrite(HasModelPermission):
    def __init__(self, model: Type[Model]):
        super().__init__(model=model, action="change")

    def get_error_message(self, obj) -> str:
        if obj is None:
            return "You need change permission for this model."

        opts = obj._meta
        return f"You need 'Change' permissions for {opts.verbose_name} to run this."
