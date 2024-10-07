from datetime import date
from uuid import uuid4

from django.core.files import File as DjangoFile
from django.core.files.temp import NamedTemporaryFile

from filer.models.filemodels import File as FilerFile

from open_inwoner.openproducten import models as op_models
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
from open_inwoner.pdc import models as pdc_models


def create_file_object(content):
    temp_file = NamedTemporaryFile(delete=True)
    temp_file.write(content)
    return DjangoFile(temp_file)


def _create_file_instance(content):
    file = create_file_object(content)
    return FilerFile.objects.create(file=file)


def create_tag_type(uuid):
    return TagType(id=uuid, name="test tag type")


def create_tag(uuid):
    return Tag(id=uuid, name="test tag", type=create_tag_type(uuid4()), icon=None)


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


def create_price(uuid):
    return Price(
        id=uuid,
        valid_from=date.today(),
        options=[
            create_price_option(uuid4()).__dict__
        ],  # __dict__ is needed for zgw_consumers.api_models.Model _type_cast
    )


def create_complete_product_type(name):
    product_type = create_product_type(uuid4(), name=name)
    product_type.conditions.append(create_condition(uuid4()))
    product_type.tags.append(create_tag(uuid4()))
    product_type.links.append(create_link(uuid4()))
    product_type.prices.append(create_price(uuid4()))
    product_type.questions.append(create_question(uuid4()))
    return product_type


def get_all_product_type_objects():
    return [
        pdc_models.ProductCondition.objects.first(),
        pdc_models.Tag.objects.first(),
        pdc_models.TagType.objects.first(),
        pdc_models.ProductLink.objects.first(),
        op_models.Price.objects.first(),
        op_models.PriceOption.objects.first(),
        pdc_models.Question.objects.first(),
    ] + list(pdc_models.Product.objects.all())


def create_complete_category(name):
    category = create_category(uuid4(), name)
    category.questions.append(create_question(uuid4()))
    return category


def get_all_category_objects():
    return [
        pdc_models.Question.objects.first(),
    ] + list(pdc_models.Category.objects.all())
