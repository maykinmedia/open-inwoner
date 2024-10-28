from datetime import date
from uuid import uuid4

from django.core.files import File as DjangoFile

from filer.models.filemodels import File as FilerFile

from open_inwoner.openproducten import models as op_models
from open_inwoner.openproducten.api_models import (
    Category,
    Condition,
    Contact,
    File,
    Link,
    Location,
    Neighbourhood,
    Organisation,
    OrganisationType,
    Price,
    PriceOption,
    ProductType,
    Question,
    Tag,
    TagType,
)
from open_inwoner.pdc import models as pdc_models


def create_django_file_object(content):
    return DjangoFile(content)


def create_filer_file_instance(content):
    file = create_django_file_object(content)
    return FilerFile.objects.create(file=file)


def create_tag_type(uuid):
    return TagType(id=uuid, name="test tag type")


def create_tag(tag_uuid, tag_type_uuid):
    return Tag(
        id=tag_uuid, name="test tag", type=create_tag_type(tag_type_uuid), icon=None
    )


def create_condition(uuid):
    return Condition(
        id=uuid, question="?", positive_text="+", negative_text="-", name="test"
    )


def create_link(uuid):
    return Link(id=uuid, name="test tag type", url="https://example.com")


def create_file(uuid):
    return File(id=uuid, file="None")


def create_product_type(uuid, name="product type"):
    return ProductType(
        id=uuid,
        published=False,
        name=name,
        summary="abc",
        icon=None,
        image=None,
        content="str",
        uniform_product_name="upn",
        form_link="a",
        keywords=[],
        conditions=[],
        tags=[],
        links=[],
        categories=[],
        files=[],
        prices=[],
        questions=[],
        locations=[],
        organisations=[],
        contacts=[],
        related_product_types=[],
    )


def create_question(uuid):
    return Question(id=uuid, question="?", answer="a")


def create_category(uuid, name="category"):
    return Category(
        id=uuid,
        published=False,
        name=name,
        description="description",
        icon=None,
        image=None,
        parent_category=None,
        questions=[],
    )


def create_price_option(uuid):
    return PriceOption(
        id=uuid,
        amount="10.00",
        description="description",
    )


def create_price(price_uuid, option_uuid):
    return Price(
        id=price_uuid,
        valid_from=date.today(),
        options=[
            create_price_option(option_uuid).__dict__
        ],  # __dict__ is needed for zgw_consumers.api_models.Model _type_cast
    )


def create_location(uuid):
    return Location(
        id=uuid,
        name="Maykin Media",
        email="test@gmail.com",
        phone_number="",
        street="Kingsfortweg",
        house_number="151",
        postcode="1111 AA",
        city="Amsterdam",
        coordinates=[4.86687019, 52.08613284],
    )


def create_organisation_type(uuid):
    return OrganisationType(id=uuid, name="test organisation type")


def create_neighbourhood(uuid):
    return Neighbourhood(id=uuid, name="test neighbourhood")


def create_organisation(org_uuid, type_uuid, neighbourhood_uuid):
    return Organisation(
        id=org_uuid,
        name="Maykin Media",
        email="test@gmail.com",
        phone_number="",
        street="Kingsfortweg",
        house_number="151",
        postcode="1111 AA",
        city="Amsterdam",
        coordinates=[4.86687019, 52.08613284],
        type=create_organisation_type(type_uuid),
        neighbourhood=create_neighbourhood(neighbourhood_uuid),
        logo=None,
    )


def create_contact(contact_uuid, org_uuid):
    return Contact(
        id=contact_uuid,
        first_name="Bob",
        last_name="de Vries",
        email="test@mail.com",
        phone_number="",
        role="",
        organisation_id=org_uuid,
    )


def create_complete_product_type(name):
    product_type = create_product_type(uuid4(), name=name)
    product_type.conditions.append(create_condition(uuid4()))
    product_type.tags.append(create_tag(uuid4(), uuid4()))
    product_type.links.append(create_link(uuid4()))
    product_type.files.append(create_file(uuid4()))
    product_type.prices.append(create_price(uuid4(), uuid4()))
    product_type.questions.append(create_question(uuid4()))
    product_type.locations.append(create_location(uuid4()))

    org_uuid = uuid4()
    product_type.organisations.append(create_organisation(org_uuid, uuid4(), uuid4()))
    product_type.contacts.append(create_contact(uuid4(), org_uuid))
    return product_type


def get_all_product_type_objects():
    return (
        list(pdc_models.ProductCondition.objects.all())
        + list(pdc_models.Tag.objects.all())
        + list(pdc_models.TagType.objects.all())
        + list(pdc_models.ProductLink.objects.all())
        + list(pdc_models.ProductFile.objects.all())
        + list(op_models.Price.objects.all())
        + list(op_models.PriceOption.objects.all())
        + list(pdc_models.Question.objects.all())
        + list(pdc_models.Product.objects.all())
        + list(pdc_models.ProductLocation.objects.all())
        + list(pdc_models.ProductContact.objects.all())
        + list(pdc_models.Organization.objects.all())
        + list(pdc_models.OrganizationType.objects.all())
        + list(pdc_models.Neighbourhood.objects.all())
    )


def create_complete_category(name):
    category = create_category(uuid4(), name)
    category.questions.append(create_question(uuid4()))
    return category


def get_all_category_objects():
    return list(pdc_models.Question.objects.all()) + list(
        pdc_models.Category.objects.all()
    )
