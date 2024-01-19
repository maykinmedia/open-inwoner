from open_inwoner.accounts.models import User
from open_inwoner.openklant.wrap import fetch_klant
from open_inwoner.utils.logentry import system_action

from .wrap import get_fetch_parameters


def update_user_from_klant(request):
    if not hasattr(request, "user"):
        return

    user: User = request.user

    klant = fetch_klant(**get_fetch_parameters(request))
    if not klant:
        return

    system_action("retrieved klant for user", content_object=user)

    update_data = {}

    if klant.telefoonnummer and klant.telefoonnummer != user.phonenumber:
        update_data["phonenumber"] = klant.telefoonnummer

    if klant.emailadres and klant.emailadres != user.email:
        if not User.objects.filter(email__iexact=klant.emailadres).exists():
            update_data["email"] = klant.emailadres

    if update_data:
        for attr, value in update_data.items():
            setattr(user, attr, value)
        user.save(update_fields=update_data.keys())

        system_action(
            f"updated user from klant API with fields: {', '.join(sorted(update_data.keys()))}",
            content_object=user,
        )
