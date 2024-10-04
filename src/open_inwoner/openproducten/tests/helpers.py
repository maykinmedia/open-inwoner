from datetime import date
from uuid import uuid4

from django.core.files import File as DjangoFile
from django.core.files.temp import NamedTemporaryFile

from filer.models.filemodels import File as FilerFile

from open_inwoner.openproducten.api_models import (
    Category,
    Condition,
    File,
    Link,
    Price,
    PriceOption,
    ProductType,
    Question,
    Tag,
    TagType,
)


def _create_file_object(content):
    temp_file = NamedTemporaryFile(delete=True)
    temp_file.write(content)
    return DjangoFile(temp_file)


def _create_file_instance(content):
    file = _create_file_object(content)
    return FilerFile.objects.create(file=file)


def _create_tag_type(uuid):
    return TagType(id=uuid, name="test tag type")


def _create_tag(uuid):
    return Tag(id=uuid, name="test tag", type=_create_tag_type(uuid4()), icon=None)


def _create_condition(uuid):
    return Condition(
        id=uuid, question="?", positive_text="+", negative_text="-", name="test"
    )


def _create_link(uuid):
    return Link(id=uuid, name="test tag type", url="https://example.com")


def _create_file(uuid):
    return File(id=uuid, file="None")


def _create_product_type(uuid):
    return ProductType(
        id=uuid,
        published=False,
        name="abc",
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
        related_product_types=[],
    )


def _create_question(uuid):
    return Question(id=uuid, question="?", answer="a")


def _create_category(uuid):
    return Category(
        id=uuid,
        published=False,
        name="category",
        description="description",
        icon=None,
        image=None,
        parent_category=None,
        questions=[],
    )


def _create_price_option(uuid):
    return PriceOption(
        id=uuid,
        amount="10",
        description="description",
    )


def _create_price(uuid):
    return Price(
        id=uuid,
        valid_from=date.today(),
        options=[_create_price_option(uuid4()).__dict__],
    )
