import logging

from django.db import transaction
from django.utils.text import slugify

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
    """Update a model instance by a dict"""
    for key, value in kwargs.items():
        setattr(model, key, value)
    if commit:
        model.save()


def _get_instance(model, uuid):
    """Returns an model instance by uuid or None"""
    return model.objects.filter(open_producten_uuid=uuid).first()


class OpenProductenImporter:
    def __init__(self, client):
        self.client = client
        self.created_objects = []
        self.updated_objects = []

    def _add_to_log_list(self, instance, created: bool):
        if created:
            self.created_objects.append(instance)
        else:
            self.updated_objects.append(instance)

    def _update_or_create_question(self, question, product_type=None, category=None):

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


class ProductTypeImporter(OpenProductenImporter):
    def __init__(self, client):
        super().__init__(client)
        self.product_types = None
        self.handled_product_types = set()

    @transaction.atomic()
    def import_producttypes(self):
        """
        generate a Product for every ProductType in the Open Producten API
        """

        self.product_types = self.client.fetch_producttypes_no_cache()

        for product_type in self.product_types:
            self._handle_product_type(product_type)

        return self.created_objects, self.updated_objects

    def _handle_product_type(self, product_type):

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
        related_product_types,
        product_type_instance,
    ):
        """recursively handles related product_types of the current type"""

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

    def _handle_relations(self, product_type, product_type_instance):

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

    def _update_or_create_tag_type(self, tag_type):
        tag_type_instance, created = TagType.objects.update_or_create(
            open_producten_uuid=tag_type.id,
            defaults={"open_producten_uuid": tag_type.id, "name": tag_type.name},
        )
        self._add_to_log_list(tag_type_instance, created)
        return tag_type_instance

    def _update_or_create_tag(self, tag):
        tag_type_instance = self._update_or_create_tag_type(tag.type)
        icon_object = self.client.get_image(tag.icon)

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
        return tag_instance

    def _update_or_create_condition(self, condition):
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
        return condition_instance

    def _update_or_create_link(self, link, product_type):
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

    def _update_or_create_file(self, file, product_type):
        file_object = self.client.get_file(file.file)

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

    def _update_or_create_price(self, price, product_type_instance):
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

    def _update_or_create_price_option(self, price_option, price_instance):
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

    def _update_or_create_product_type(self, product_type):
        icon_object = self.client.get_image(product_type.icon)
        image_object = self.client.get_image(product_type.image)

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
            "uniforme_productnaam": product_type.uniform_product_name.name,
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


class CategoryImporter(OpenProductenImporter):
    def __init__(self, client):
        super().__init__(client)
        self.categories = None
        self.handled_categories = set()

    @transaction.atomic()
    def import_categories(self):
        """
        generate a Category for every Category in the Open Producten API
        """

        self.categories = self.client.fetch_categories_no_cache()

        for category in self.categories:
            self._handle_category(category)

        return self.created_objects, self.updated_objects

    def _handle_category(self, category):
        if category.id not in self.handled_categories:
            self.handled_categories.add(category.id)

            self._handle_category_parent(category.parent_category)

            category_instance = self._update_or_create_category(category)

            for question in category.questions:
                self._update_or_create_question(question, category_instance)

    def _handle_category_parent(self, parent_uuid):
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

    def _update_or_create_category(self, category):
        icon_object = self.client.get_image(category.icon)
        image_object = self.client.get_image(category.image)

        data = {
            "open_producten_uuid": category.id,
            "name": category.name,
            "slug": slugify(category.name),
            "published": category.published,
            "description": category.description,
            "icon": icon_object,
            "image": image_object,
        }

        parent_instance = _get_instance(Category, category.parent_category)

        if category_instance := _get_instance(Category, category.id):
            if category_instance.icon:
                category_instance.icon.delete()
            if category_instance.image:
                category_instance.image.delete()
            self._update_category(category_instance, parent_instance, data)
            created = False
        else:
            category_instance = self._create_category(parent_instance, data)
            created = True
        self._add_to_log_list(category_instance, created)
        return category_instance

    def _update_category(self, category_instance, parent_instance, data):
        existing_parent = category_instance.get_parent()

        if parent_instance is None and existing_parent is not None:
            last_root = Category.get_last_root_node()
            category_instance.move(last_root, "last-sibling")

        elif parent_instance != existing_parent:
            category_instance.move(parent_instance, "last-child")

        category_instance.refresh_from_db()

        _update_instance(category_instance, True, **data)
        return category_instance

    def _create_category(self, parent_instance, data):
        if parent_instance:
            category_instance = parent_instance.add_child(**data)
        else:
            category_instance = Category.add_root(**data)
        return category_instance
