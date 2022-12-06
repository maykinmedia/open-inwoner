from django.contrib.auth.models import BaseUserManager
from django.db.models import Q, QuerySet

from digid_eherkenning.managers import BaseDigidManager, BaseeHerkenningManager

from open_inwoner.utils.hash import generate_email_from_string

from .choices import LoginTypeChoices
from .query import UserQuerySet


class DigidManager(BaseDigidManager):
    def get_queryset(self):
        return super().get_queryset().filter(login_type=LoginTypeChoices.digid)

    def get_by_bsn(self, bsn):
        return self.get_queryset().get(bsn=bsn)

    def digid_create(self, bsn, **kwargs):
        email = generate_email_from_string(bsn)
        return super().create(
            email=email,
            login_type=LoginTypeChoices.digid,
            bsn=bsn,
        )


class eHerkenningManager(BaseeHerkenningManager):
    def get_queryset(self):
        return super().get_queryset().filter(login_type=LoginTypeChoices.eherkenning)

    def get_by_rsin(self, rsin):
        return self.get_queryset().get(rsin=rsin)

    def eherkenning_create(self, rsin, **kwargs):
        return super().create(
            email="user-{}@rsin.com".format(rsin),
            login_type=LoginTypeChoices.eherkenning,
            rsin=rsin,
        )


class UserManager(BaseUserManager.from_queryset(UserQuerySet)):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

    def get_pending_approvals(self, user):
        return self.filter(contacts_for_approval=user)


class ActionQueryset(QuerySet):
    def visible(self):
        return self.filter(is_deleted=False)

    def connected(self, user):
        return self.filter(Q(created_by=user) | Q(is_for=user)).distinct()
