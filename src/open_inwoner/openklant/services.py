from open_inwoner.accounts.models import User
from open_inwoner.openklant.wrap import fetch_klant_for_bsn
from open_inwoner.utils.logentry import system_action


def update_user_from_klant(user: User):
    klant = fetch_klant_for_bsn(user.bsn)
    if not klant:
        return

    system_action("retrieved klant for BSN-user", content_object=user)

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
