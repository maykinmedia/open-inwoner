import logging
from typing import TypeVar

from django.db import models, transaction
from django.db.models import Q
from django.utils.text import slugify

from filer.models.filemodels import File
from filer.models.imagemodels import Image

import open_inwoner.openproducten.api_models as api_models
from open_inwoner.openproducten.models import Price, PriceOption
from open_inwoner.pdc.models import (
    Category,
    Product as ProductType,
    ProductCondition,
    ProductFile,
    ProductLink,
    Question,
    Tag,
    TagType,
)

logger = logging.getLogger(__name__)


def _update_instance(model, commit=False, **kwargs):
    """Update a model instance by a dict."""
    for key, value in kwargs.items():
        setattr(model, key, value)
    if commit:
        model.save()


T = TypeVar("T")


def _get_instance(model: T, uuid) -> T:
    """Returns a model instance by uuid or None."""
    return model.objects.filter(open_producten_uuid=uuid).first()


class OpenProductenImporterMixin:
    def __init__(self, client):
        self.client = client
        self.created_objects = []
        self.updated_objects = []
        self.deleted_count = 0

    def _get_image(self, url: str) -> Image | None:
        if not url:
            return None

        file = self.client.fetch_file(url)

        if not file:
            return None

        return Image.objects.create(original_filename=url.split("/")[-1], file=file)

    def _get_file(self, url: str) -> File | None:
        if not url:
            return None

        file = self.client.fetch_file(url)

        if not file:
            return None

        return File.objects.create(original_filename=url.split("/")[-1], file=file)

    def _add_to_log_list(self, instance: models.Model, created: bool):
        if created:
            self.created_objects.append(instance)
        else:
            self.updated_objects.append(instance)

    def _update_or_create_question(
        self,
        question: api_models.Question,
        product_type: ProductType | None = None,
        category: Category | None = None,
    ):

        relation_object = product_type if product_type else category
        relation_key = "product" if product_type else "category"

        question_instance, created = Question.objects.update_or_create(
            open_producten_uuid=question.id,
            defaults={
                "open_producten_uuid": question.id,
                "question": question.question,
                "answer": question.answer,
                relation_key: relation_object,
            },
        )
        self._add_to_log_list(question_instance, created)


class ProductTypeImporter(OpenProductenImporterMixin):
    def __init__(self, client):
        super().__init__(client)
        self.product_types = None
        self.handled_product_types = set()
        self.handled_tags = set()
        self.handled_tag_types = set()
        self.handled_conditions = set()

    def import_producttypes(self):
        """
        Generate a Product for every ProductType in the Open Producten API.
        """

        self.product_types = self.client.fetch_producttypes_no_cache()

        self._handle_transaction()
        self._delete_non_updated_objects()
        return self.created_objects, self.updated_objects, self.deleted_count

    @transaction.atomic()
    def _handle_transaction(self):
        for product_type in self.product_types:
            self._handle_product_type(product_type)

    def _handle_product_type(self, product_type: api_models.ProductType):

        if product_type.id not in self.handled_product_types:
            self.handled_product_types.add(product_type.id)
            product_type_instance = self._update_or_create_product_type(product_type)
            self._handle_relations(product_type, product_type_instance)

            self._handle_related_product_types(
                product_type.related_product_types, product_type_instance
            )
            product_type_instance.save()

    def _handle_related_product_types(
        self,
        related_product_types: list[str],
        product_type_instance: ProductType,
    ):
        """Recursively handles related product_types of the current type."""

        for related_product_type_uuid in related_product_types:
            if related_product_type_uuid not in self.handled_product_types:
                related_product_type = next(
                    (
                        product_type
                        for product_type in self.product_types
                        if product_type.id == related_product_type_uuid
                    ),
                    None,
                )

                self._handle_product_type(related_product_type)

            related_product_instance = ProductType.objects.get(
                open_producten_uuid=related_product_type_uuid
            )
            product_type_instance.related_products.add(related_product_instance.id)

    def _handle_relations(
        self, product_type: api_models.ProductType, product_type_instance: ProductType
    ):

        for tag in product_type.tags:
            tag_instance = self._update_or_create_tag(tag)
            product_type_instance.tags.add(tag_instance)

        for condition in product_type.conditions:
            condition_instance = self._update_or_create_condition(condition)
            product_type_instance.conditions.add(condition_instance)

        category_uuids = [category.id for category in product_type.categories]
        pdc_ids = list(
            Category.objects.filter(open_producten_uuid__in=category_uuids).values_list(
                "id", flat=True
            )
        )
        product_type_instance.categories.set(pdc_ids)

        # TODO location, contacts, organisations

        for link in product_type.links:
            self._update_or_create_link(link, product_type_instance)

        for question in product_type.questions:
            self._update_or_create_question(question, product_type_instance)

        for file in product_type.files:
            self._update_or_create_file(file, product_type_instance)

        for price in product_type.prices:
            self._update_or_create_price(price, product_type_instance)

    def _update_or_create_tag_type(self, tag_type: api_models.TagType):
        tag_type_instance, created = TagType.objects.update_or_create(
            open_producten_uuid=tag_type.id,
            defaults={"open_producten_uuid": tag_type.id, "name": tag_type.name},
        )
        self._add_to_log_list(tag_type_instance, created)
        self.handled_tag_types.add(tag_type.id)
        return tag_type_instance

    def _update_or_create_tag(self, tag: api_models.Tag):
        tag_type_instance = self._update_or_create_tag_type(tag.type)
        icon_object = self._get_image(tag.icon)

        data = {
            "open_producten_uuid": tag.id,
            "name": tag.name,
            "slug": slugify(tag.name),
            "icon": icon_object,
            "type": tag_type_instance,
        }

        if tag_instance := _get_instance(Tag, tag.id):
            if tag_instance.icon:
                tag_instance.icon.delete()
            _update_instance(tag_instance, True, **data)
            created = False
        else:
            tag_instance = Tag.objects.create(**data)
            created = True

        self._add_to_log_list(tag_instance, created)
        self.handled_tags.add(tag.id)
        return tag_instance

    def _update_or_create_condition(
        self, condition: api_models.Condition
    ) -> ProductCondition:
        condition_instance, created = ProductCondition.objects.update_or_create(
            open_producten_uuid=condition.id,
            defaults={
                "open_producten_uuid": condition.id,
                "name": condition.name,
                "question": condition.question,
                "positive_text": condition.positive_text,
                "negative_text": condition.negative_text,
            },
        )
        self._add_to_log_list(condition_instance, created)
        self.handled_conditions.add(condition.id)
        return condition_instance

    def _update_or_create_link(self, link: api_models.Link, product_type: ProductType):
        link_instance, created = ProductLink.objects.update_or_create(
            open_producten_uuid=link.id,
            defaults={
                "open_producten_uuid": link.id,
                "name": link.name,
                "url": link.url,
                "product": product_type,
            },
        )
        self._add_to_log_list(link_instance, created)

    def _update_or_create_file(self, file: api_models.File, product_type: ProductType):
        file_object = self._get_file(file.file)

        data = {
            "open_producten_uuid": file.id,
            "file": file_object,
            "product": product_type,
        }

        if file_instance := _get_instance(ProductFile, file.id):
            file_instance.file.delete()
            _update_instance(file_instance, True, **data)
            created = False
        else:
            file_instance = ProductFile.objects.create(**data)
            created = True
        self._add_to_log_list(file_instance, created)

    def _update_or_create_price(
        self, price: api_models.Price, product_type_instance: ProductType
    ):
        price_instance, created = Price.objects.update_or_create(
            open_producten_uuid=price.id,
            defaults={
                "open_producten_uuid": price.id,
                "valid_from": price.valid_from,
                "product_type": product_type_instance,
            },
        )
        self._add_to_log_list(price_instance, created)
        for option in price.options:
            self._update_or_create_price_option(option, price_instance)

    def _update_or_create_price_option(
        self, price_option: api_models.PriceOption, price_instance: ProductType
    ):
        price_option_instance, created = PriceOption.objects.update_or_create(
            open_producten_uuid=price_option.id,
            defaults={
                "open_producten_uuid": price_option.id,
                "description": price_option.description,
                "amount": price_option.amount,
                "price": price_instance,
            },
        )
        self._add_to_log_list(price_option_instance, created)

    def _update_or_create_product_type(
        self, product_type: api_models.ProductType
    ) -> ProductType:
        icon_object = self._get_image(product_type.icon)
        image_object = self._get_image(product_type.image)

        data = {
            "open_producten_uuid": product_type.id,
            "name": product_type.name,
            "slug": slugify(product_type.name),
            "published": product_type.published,
            "summary": product_type.summary,
            "content": product_type.content,
            "form": product_type.form_link,  # TODO product uses OpenFormsSlugField
            "icon": icon_object,
            "image": image_object,
            "uniforme_productnaam": product_type.uniform_product_name.split("/")[-1],
            "keywords": product_type.keywords,
        }

        if product_type_instance := _get_instance(ProductType, product_type.id):
            if product_type_instance.icon:
                product_type_instance.icon.delete()
            if product_type_instance.image:
                product_type_instance.image.delete()

            _update_instance(product_type_instance, True, **data)
            created = False
        else:
            product_type_instance = ProductType.objects.create(**data)
            created = True
        self._add_to_log_list(product_type_instance, created)
        return product_type_instance

    def _get_count_without_m2m_deletions(self, result):
        count = result[0]
        for k in result[1]:
            if k in ("pdc.Product_tags", "pdc.Product_conditions"):
                count -= result[1][k]
        return count

    def _delete_non_updated_objects(self):
        result = ProductType.objects.exclude(
            Q(open_producten_uuid__in=self.handled_product_types)
            | Q(open_producten_uuid__isnull=True)
        ).delete()

        self.deleted_count += self._get_count_without_m2m_deletions(result)

        self.deleted_count += Tag.objects.exclude(
            Q(open_producten_uuid__in=self.handled_tags)
            | Q(open_producten_uuid__isnull=True)
        ).delete()[0]

        self.deleted_count += TagType.objects.exclude(
            Q(open_producten_uuid__in=self.handled_tag_types)
            | Q(open_producten_uuid__isnull=True)
        ).delete()[0]

        self.deleted_count += ProductCondition.objects.exclude(
            Q(open_producten_uuid__in=self.handled_conditions)
            | Q(open_producten_uuid__isnull=True)
        ).delete()[0]


class CategoryImporter(OpenProductenImporterMixin):
    def __init__(self, client):
        super().__init__(client)
        self.categories = None
        self.handled_categories = set()

    def import_categories(self):
        """
        Generate a Category for every Category in the Open Producten API.
        """

        self.categories = self.client.fetch_categories_no_cache()

        self._handle_transaction()
        self._delete_non_updated_objects()
        return self.created_objects, self.updated_objects, self.deleted_count

    @transaction.atomic()
    def _handle_transaction(self):
        for category in self.categories:
            self._handle_category(category)

    def _handle_category(self, category: api_models.Category):
        if category.id not in self.handled_categories:
            self.handled_categories.add(category.id)

            self._handle_category_parent(category.parent_category)

            category_instance = self._update_or_create_category(category)

            for question in category.questions:
                self._update_or_create_question(question, category=category_instance)

    def _handle_category_parent(self, parent_uuid: str):
        if parent_uuid is not None and parent_uuid not in self.handled_categories:
            category_parent = next(
                (
                    category
                    for category in self.categories
                    if category.id == parent_uuid
                ),
                None,
            )
            self._handle_category(category_parent)

    def _update_or_create_category(self, category: api_models.Category) -> Category:
        icon_object = self._get_image(category.icon)
        image_object = self._get_image(category.image)

        data = {
            "open_producten_uuid": category.id,
            "name": category.name,
            "slug": slugify(category.name),
            "published": category.published,
            "description": category.description,
            "icon": icon_object,
            "image": image_object,
        }

        parent_instance = (
            _get_instance(Category, category.parent_category)
            if category.parent_category
            else None
        )

        if category_instance := _get_instance(Category, category.id):
            if category_instance.icon:
                category_instance.icon.delete()
            if category_instance.image:
                category_instance.image.delete()
            self._update_category(category_instance, parent_instance, data)
        else:
            category_instance = self._create_category(parent_instance, data)
        return category_instance

    def _update_category(
        self, category_instance: Category, parent_instance: Category | None, data: dict
    ) -> Category:
        existing_parent = category_instance.get_parent()

        if parent_instance is None and existing_parent is not None:
            last_root = Category.get_last_root_node()
            category_instance.move(last_root, "last-sibling")

        elif parent_instance != existing_parent:
            category_instance.move(parent_instance, "last-child")

        category_instance.refresh_from_db()

        _update_instance(category_instance, True, **data)
        self._add_to_log_list(category_instance, False)
        return category_instance

    def _create_category(self, parent_instance: Category | None, data) -> Category:
        if parent_instance:
            category_instance = parent_instance.add_child(**data)
        else:
            category_instance = Category.add_root(**data)
        self._add_to_log_list(category_instance, True)
        return category_instance

    def get_object_count(self):
        return (
            Category.objects.filter(open_producten_uuid__isnull=False).count()
            + Question.objects.filter(
                open_producten_uuid__isnull=False, product__isnull=True
            ).count()
        )

    def _delete_non_updated_objects(self):
        old_count = self.get_object_count()
        # For some reason (Probably Treebeard) Category ... .delete() returns None.
        Category.objects.exclude(
            Q(open_producten_uuid__in=self.handled_categories)
            | Q(open_producten_uuid__isnull=True)
        ).delete()
        new_count = self.get_object_count()
        self.deleted_count += old_count - new_count
