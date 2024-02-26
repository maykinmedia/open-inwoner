import factory

from open_inwoner.openklant.api_models import ContactMoment


class ContactFormSubjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "openklant.ContactFormSubject"

    subject = factory.Faker("sentence")
    subject_code = factory.Faker("word")


def make_contactmoment(contact_moment_data: dict):
    return ContactMoment(
        url=contact_moment_data["url"],
        bronorganisatie=contact_moment_data["bronorganisatie"],
        registratiedatum=contact_moment_data.get("registratiedatum", None),
        kanaal=contact_moment_data.get("kanaal", ""),
        tekst=contact_moment_data.get("tekst", ""),
        medewerker_identificatie=contact_moment_data.get(
            "medewerker_identificatie", None
        ),
        identificatie=contact_moment_data.get("identificatie", ""),
        type=contact_moment_data.get("type", ""),
        onderwerp=contact_moment_data.get("onderwerp", ""),
        status=contact_moment_data.get("status", ""),
        antwoord=contact_moment_data.get("antwoord", ""),
        # open-klant OAS
        voorkeurskanaal=contact_moment_data.get("voorkeurskanaal", ""),
        voorkeurstaal=contact_moment_data.get("voorkeurstaal", ""),
        vorig_contactmoment=contact_moment_data.get("vorigContactmoment", None),
        volgend_contactmoment=contact_moment_data.get("volgendContactmoment", None),
        onderwerp_links=contact_moment_data.get("onderwerpLinks"),
        initiatiefnemer=contact_moment_data.get("initiatiefnemer", ""),
        medewerker=contact_moment_data.get("medewerker", ""),
    )
