from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

from django.test import TestCase

import open_inwoner.pdc.models as pdc_models
from open_inwoner.openproducten.producttypes_imports import ProductTypeImporter
from open_inwoner.pdc.tests.factories import (
    CategoryFactory,
    OrganizationFactory,
    ProductConditionFactory,
    ProductFactory,
    QuestionFactory,
    TagFactory,
)

from ..api_models import BaseCategory
from ..models import Price, PriceOption
from .factories import PriceOptionFactory
from .helpers import (
    create_complete_product_type,
    create_condition,
    create_contact,
    create_file,
    create_filer_file_instance,
    create_link,
    create_location,
    create_neighbourhood,
    create_organisation,
    create_organisation_type,
    create_price,
    create_product_type,
    create_question,
    create_tag,
    create_tag_type,
    get_all_product_type_objects,
)


@patch(
    "open_inwoner.openproducten.producttypes_imports.OpenProductenImporterMixin._get_image",
    new=Mock(return_value=None),
)
@patch(
    "open_inwoner.openproducten.producttypes_imports.OpenProductenImporterMixin._get_file",
    new=Mock(side_effect=lambda _: create_filer_file_instance(b"mocked file")),
)
class TestProductTypeImporter(TestCase):
    def setUp(self):
        self.client = MagicMock()

    def test_update_or_create_tag_type(self):
        uuid = uuid4()
        importer = ProductTypeImporter(self.client)

        for create in (True, False):
            with self.subTest(
                "should create instance if uuid does not exist"
                if create
                else "should update instance if uuid exists"
            ):

                tag_type = create_tag_type(uuid)
                instance = importer._update_or_create_tag_type(tag_type)

                self.assertEqual(pdc_models.TagType.objects.count(), 1)
                self.assertEqual(instance.open_producten_uuid, uuid)
                self.assertEqual(instance.name, tag_type.name)

    def test_update_or_create_tag(self):
        tag_uuid = uuid4()
        tag_type_uuid = uuid4()
        importer = ProductTypeImporter(self.client)

        for create in (True, False):
            with self.subTest(
                "should create instance if uuid does not exist"
                if create
                else "should update instance if uuid exists"
            ):

                tag = create_tag(tag_uuid, tag_type_uuid)
                instance = importer._update_or_create_tag(tag)

                self.assertEqual(pdc_models.Tag.objects.count(), 1)
                self.assertEqual(pdc_models.TagType.objects.count(), 1)
                self.assertEqual(instance.open_producten_uuid, tag_uuid)
                self.assertEqual(instance.name, tag.name)

    def test_update_or_create_condition(self):
        uuid = uuid4()
        importer = ProductTypeImporter(self.client)
        for create in (True, False):
            with self.subTest(
                "should create instance if uuid does not exist"
                if create
                else "should update instance if uuid exists"
            ):

                condition = create_condition(uuid)
                instance = importer._update_or_create_condition(condition)

                self.assertEqual(pdc_models.ProductCondition.objects.count(), 1)
                self.assertEqual(instance.open_producten_uuid, uuid)
                self.assertEqual(instance.name, condition.name)

    def test_update_or_create_location(self):
        uuid = uuid4()
        importer = ProductTypeImporter(self.client)
        for create in (True, False):
            with self.subTest(
                "should create instance if uuid does not exist"
                if create
                else "should update instance if uuid exists"
            ):

                location = create_location(uuid)
                instance = importer._update_or_create_location(location)

                self.assertEqual(pdc_models.ProductLocation.objects.count(), 1)
                self.assertEqual(instance.open_producten_uuid, uuid)
                self.assertEqual(instance.name, location.name)

    def test_update_or_create_organisation_type(self):
        uuid = uuid4()
        importer = ProductTypeImporter(self.client)

        for create in (True, False):
            with self.subTest(
                "should create instance if uuid does not exist"
                if create
                else "should update instance if uuid exists"
            ):

                organisation_type = create_organisation_type(uuid)
                instance = importer._update_or_create_organisation_type(
                    organisation_type
                )

                self.assertEqual(pdc_models.OrganizationType.objects.count(), 1)
                self.assertEqual(instance.open_producten_uuid, uuid)
                self.assertEqual(instance.name, organisation_type.name)

    def test_update_or_create_neighbourhood(self):
        uuid = uuid4()
        importer = ProductTypeImporter(self.client)

        for create in (True, False):
            with self.subTest(
                "should create instance if uuid does not exist"
                if create
                else "should update instance if uuid exists"
            ):

                neighbourhood = create_neighbourhood(uuid)
                instance = importer._update_or_create_neighbourhood(neighbourhood)

                self.assertEqual(pdc_models.Neighbourhood.objects.count(), 1)
                self.assertEqual(instance.open_producten_uuid, uuid)
                self.assertEqual(instance.name, neighbourhood.name)

    def test_update_or_create_organisation(self):
        organisation_uuid = uuid4()
        organisation_type_uuid = uuid4()
        neighbourhood_uuid = uuid4()
        importer = ProductTypeImporter(self.client)

        for create in (True, False):
            with self.subTest(
                "should create instance if uuid does not exist"
                if create
                else "should update instance if uuid exists"
            ):

                organisation = create_organisation(
                    organisation_uuid, organisation_type_uuid, neighbourhood_uuid
                )
                instance = importer._update_or_create_organisation(organisation)

                self.assertEqual(pdc_models.Organization.objects.count(), 1)
                self.assertEqual(pdc_models.OrganizationType.objects.count(), 1)
                self.assertEqual(pdc_models.Neighbourhood.objects.count(), 1)
                self.assertEqual(instance.open_producten_uuid, organisation_uuid)
                self.assertEqual(instance.name, organisation.name)

    def test_update_or_create_contact(self):
        uuid = uuid4()
        org = OrganizationFactory.create(open_producten_uuid=uuid4())
        importer = ProductTypeImporter(self.client)
        for create in (True, False):
            with self.subTest(
                "should create instance if uuid does not exist"
                if create
                else "should update instance if uuid exists"
            ):
                contact = create_contact(uuid, org.open_producten_uuid)
                instance = importer._update_or_create_contact(contact)

                self.assertEqual(pdc_models.ProductContact.objects.count(), 1)
                self.assertEqual(instance.open_producten_uuid, uuid)
                self.assertEqual(instance.first_name, contact.first_name)

    def test_update_or_create_link(self):
        uuid = uuid4()
        product = ProductFactory()
        importer = ProductTypeImporter(self.client)
        for create in (True, False):
            with self.subTest(
                "should create instance if uuid does not exist"
                if create
                else "should update instance if uuid exists"
            ):

                link = create_link(uuid)
                importer._update_or_create_link(link, product)
                instance = pdc_models.ProductLink.objects.first()

                self.assertEqual(pdc_models.ProductLink.objects.count(), 1)
                self.assertEqual(instance.open_producten_uuid, uuid)
                self.assertEqual(instance.name, link.name)

    def test_update_or_create_file(self):
        uuid = uuid4()
        product = ProductFactory()
        importer = ProductTypeImporter(self.client)
        for create in (True, False):
            with self.subTest(
                "should create instance if uuid does not exist"
                if create
                else "should update instance if uuid exists"
            ):

                file = create_file(uuid)
                importer._update_or_create_file(file, product)
                instance = pdc_models.ProductFile.objects.first()

                self.assertEqual(pdc_models.ProductFile.objects.count(), 1)
                self.assertEqual(instance.open_producten_uuid, uuid)

    def test_update_or_create_price(self):
        price_uuid = uuid4()
        option_uuid = uuid4()
        product = ProductFactory()
        importer = ProductTypeImporter(self.client)
        for create in (True, False):
            with self.subTest(
                "should create instance if uuid does not exist"
                if create
                else "should update instance if uuid exists"
            ):

                price = create_price(price_uuid, option_uuid)
                importer._update_or_create_price(price, product)
                instance = Price.objects.first()

                self.assertEqual(Price.objects.count(), 1)
                self.assertEqual(PriceOption.objects.count(), 1)
                self.assertEqual(instance.open_producten_uuid, price_uuid)
                self.assertEqual(
                    instance.options.first().amount, Decimal(price.options[0].amount)
                )

    def test_update_or_create_product_type(self):
        uuid = uuid4()
        importer = ProductTypeImporter(self.client)

        for create in (True, False):
            with self.subTest(
                "should create instance if uuid does not exist"
                if create
                else "should update instance if uuid exists"
            ):

                product_type = create_product_type(uuid)
                instance = importer._update_or_create_product_type(product_type)

                self.assertEqual(pdc_models.Product.objects.count(), 1)
                self.assertEqual(instance.open_producten_uuid, uuid)
                self.assertEqual(instance.name, product_type.name)

    def test_update_or_create_question(self):
        uuid = uuid4()
        product = ProductFactory()
        importer = ProductTypeImporter(self.client)

        for create in (True, False):
            with self.subTest(
                "should create instance if uuid does not exist"
                if create
                else "should update instance if uuid exists"
            ):

                question = create_question(uuid)
                importer._update_or_create_question(question, product)
                instance = pdc_models.Question.objects.first()

                self.assertEqual(pdc_models.Question.objects.count(), 1)
                self.assertEqual(instance.open_producten_uuid, uuid)
                self.assertEqual(instance.question, question.question)

    def test_handle_relations_adds_adds_all_relations_to_product_type(self):
        product_type_uuid = uuid4()
        category_uuid = uuid4()

        tag = create_tag(uuid4(), uuid4())
        condition = create_condition(uuid4())

        link = create_link(uuid4())
        question = create_question(uuid4())
        file = create_file(uuid4())

        product_type_instance = ProductFactory.create(
            open_producten_uuid=product_type_uuid
        )
        CategoryFactory.create(open_producten_uuid=category_uuid)

        product_type = create_product_type(product_type_uuid)
        product_type.tags = [tag]
        product_type.conditions = [condition]
        product_type.categories = [BaseCategory(id=category_uuid)]
        product_type.links = [link]
        product_type.questions = [question]
        product_type.files = [file]

        importer = ProductTypeImporter(self.client)
        importer._handle_relations(product_type, product_type_instance)
        product_type_instance.save()

        self.assertEqual(product_type_instance.tags.first().open_producten_uuid, tag.id)
        self.assertEqual(
            product_type_instance.conditions.first().open_producten_uuid, condition.id
        )
        self.assertEqual(
            product_type_instance.categories.first().open_producten_uuid, category_uuid
        )
        self.assertEqual(
            product_type_instance.links.first().open_producten_uuid, link.id
        )
        self.assertEqual(
            product_type_instance.question_set.first().open_producten_uuid, question.id
        )
        self.assertEqual(
            product_type_instance.files.first().open_producten_uuid, file.id
        )

    @patch(
        "open_inwoner.openproducten.producttypes_imports.ProductTypeImporter._handle_product_type"
    )
    def test_handle_related_product_types_where_related_type_has_not_been_handled(
        self, mock_handle_product_type
    ):
        related_type_uuid = uuid4()

        ProductFactory(open_producten_uuid=related_type_uuid)
        product_type_instance = ProductFactory.create(open_producten_uuid=uuid4())
        related_product_type = create_product_type(related_type_uuid)

        importer = ProductTypeImporter(self.client)
        importer.product_types = [related_product_type]
        importer._handle_related_product_types(
            [related_product_type.id], product_type_instance
        )

        mock_handle_product_type.assert_called_once()

    @patch(
        "open_inwoner.openproducten.producttypes_imports.ProductTypeImporter._handle_product_type"
    )
    def test_handle_related_product_types_where_related_type_has_been_handled(
        self, mock_handle_product_type
    ):
        related_type_uuid = uuid4()

        ProductFactory(open_producten_uuid=related_type_uuid)
        product_type_instance = ProductFactory.create(open_producten_uuid=uuid4())
        related_product_type = create_product_type(related_type_uuid)

        importer = ProductTypeImporter(self.client)
        importer.product_types = [related_product_type]
        importer.handled_product_types = {
            related_product_type.id,
        }
        importer._handle_related_product_types(
            [related_product_type.id], product_type_instance
        )

        mock_handle_product_type.assert_not_called()

    @patch(
        "open_inwoner.openproducten.producttypes_imports.ProductTypeImporter._handle_relations"
    )
    @patch(
        "open_inwoner.openproducten.producttypes_imports.ProductTypeImporter._handle_related_product_types"
    )
    def test_handle_product_type_type_is_handled_when_not_in_handled_product_types(
        self, mock_handle_related_product_types, mock_handle_relations
    ):
        importer = ProductTypeImporter(self.client)

        product_type = create_product_type(uuid4())
        importer._handle_product_type(product_type)

        mock_handle_related_product_types.assert_called_once()
        mock_handle_relations.assert_called_once()
        self.assertEqual(importer.handled_product_types, {product_type.id})

    @patch(
        "open_inwoner.openproducten.producttypes_imports.ProductTypeImporter._handle_relations"
    )
    @patch(
        "open_inwoner.openproducten.producttypes_imports.ProductTypeImporter._handle_related_product_types"
    )
    def test_handle_product_type_type_is_not_handled_when_in_handled_product_types(
        self, mock_handle_related_product_types, mock_handle_relations
    ):
        uuid = uuid4()

        importer = ProductTypeImporter(self.client)
        importer.handled_product_types = {uuid}
        product_type = create_product_type(uuid)
        importer._handle_product_type(product_type)

        mock_handle_related_product_types.assert_not_called()
        mock_handle_relations.assert_not_called()

    def test_circular_product_type_dependency(self):
        importer = ProductTypeImporter(self.client)
        product_type_a = create_product_type(uuid4(), "a")
        product_type_b = create_product_type(uuid4(), "b")
        product_type_a.related_product_types.append(product_type_b.id)
        product_type_b.related_product_types.append(product_type_a.id)

        self.client.fetch_producttypes_no_cache.return_value = [
            product_type_a,
            product_type_b,
        ]

        with patch.object(
            ProductTypeImporter,
            "_handle_product_type",
            wraps=importer._handle_product_type,
        ) as mock_handle_product_type:
            with patch.object(
                ProductTypeImporter,
                "_update_or_create_product_type",
                wraps=importer._update_or_create_product_type,
            ) as mock_update_or_create:
                importer.import_producttypes()
                self.assertEqual(mock_handle_product_type.call_count, 3)
                self.assertEqual(mock_update_or_create.call_count, 2)
                self.assertEqual(
                    importer.handled_product_types,
                    {product_type_a.id, product_type_b.id},
                )

        self.assertEqual(pdc_models.Product.objects.count(), 2)

    def test_updated_objects_are_not_deleted(self):
        tag = TagFactory.create(open_producten_uuid=uuid4())
        condition = ProductConditionFactory.create(open_producten_uuid=uuid4())
        product = ProductFactory.create(open_producten_uuid=uuid4())

        importer = ProductTypeImporter(self.client)

        importer.handled_m2m_instances.add(tag.open_producten_uuid)
        importer.handled_m2m_instances.add(condition.open_producten_uuid)
        importer.handled_product_types.add(product.open_producten_uuid)
        importer._delete_non_updated_objects()
        self.assertEqual(importer.deleted_count, 0)

    def test_non_updated_objects_are_deleted(self):
        TagFactory.create(open_producten_uuid=uuid4())
        ProductConditionFactory.create(open_producten_uuid=uuid4())
        ProductFactory.create(open_producten_uuid=uuid4())

        importer = ProductTypeImporter(self.client)

        importer._delete_non_updated_objects()
        self.assertEqual(importer.deleted_count, 3)

    def test_non_updated_objects_without_open_producten_uuid_are_kept(self):
        product = ProductFactory.create()
        TagFactory.create()
        pdc_models.TagType.objects.create(name="test")
        ProductConditionFactory.create()
        QuestionFactory.create()
        PriceOptionFactory.create()
        pdc_models.ProductLink.objects.create(product=product)

        importer = ProductTypeImporter(self.client)

        importer._delete_non_updated_objects()
        self.assertEqual(importer.deleted_count, 0)

    def test_complete_import_with_new_objects(self):
        related_product_type = create_product_type(uuid4())
        product_type = create_complete_product_type("test2")
        product_type.related_product_types.append(related_product_type.id)

        self.client.fetch_producttypes_no_cache.return_value = [
            product_type,
            related_product_type,
        ]
        importer = ProductTypeImporter(self.client)
        created, updated, deleted = importer.import_producttypes()

        self.assertEqual(pdc_models.Product.objects.count(), 2)
        self.assertEqual(pdc_models.ProductCondition.objects.count(), 1)
        self.assertEqual(pdc_models.Tag.objects.count(), 1)
        self.assertEqual(pdc_models.TagType.objects.count(), 1)
        self.assertEqual(pdc_models.ProductLink.objects.count(), 1)
        self.assertEqual(pdc_models.ProductFile.objects.count(), 1)
        self.assertEqual(Price.objects.count(), 1)
        self.assertEqual(PriceOption.objects.count(), 1)
        self.assertEqual(pdc_models.Question.objects.count(), 1)

        all_objects = get_all_product_type_objects()

        self.assertEqual(updated, [])
        self.assertEqual(deleted, 0)
        self.assertEqual(
            sorted({obj.open_producten_uuid for obj in created}),
            sorted({obj.open_producten_uuid for obj in all_objects}),
        )

    def test_complete_import_with_existing_objects(self):
        related_product_type = create_product_type(uuid4())
        product_type = create_complete_product_type("test2")
        product_type.related_product_types.append(related_product_type.id)

        self.client.fetch_producttypes_no_cache.return_value = [
            product_type,
            related_product_type,
        ]

        for _ in range(2):
            importer = ProductTypeImporter(self.client)
            created, updated, deleted = importer.import_producttypes()

            self.assertEqual(pdc_models.Product.objects.count(), 2)
            self.assertEqual(pdc_models.ProductCondition.objects.count(), 1)
            self.assertEqual(pdc_models.Tag.objects.count(), 1)
            self.assertEqual(pdc_models.TagType.objects.count(), 1)
            self.assertEqual(pdc_models.ProductLink.objects.count(), 1)
            self.assertEqual(pdc_models.ProductFile.objects.count(), 1)
            self.assertEqual(Price.objects.count(), 1)
            self.assertEqual(PriceOption.objects.count(), 1)
            self.assertEqual(pdc_models.Question.objects.count(), 1)

        all_objects = get_all_product_type_objects()

        self.assertEqual(created, [])
        self.assertEqual(deleted, 0)
        self.assertEqual(
            sorted({obj.open_producten_uuid for obj in updated}),
            sorted({obj.open_producten_uuid for obj in all_objects}),
        )

    def test_complete_import_without_objects(self):
        related_product_type = create_product_type(uuid4())
        product_type = create_complete_product_type("test2")
        product_type.related_product_types.append(related_product_type.id)

        for return_value in (
            [
                product_type,
                related_product_type,
            ],
            [],
        ):
            self.client.fetch_producttypes_no_cache.return_value = return_value
            importer = ProductTypeImporter(self.client)
            created, updated, deleted = importer.import_producttypes()

        self.assertEqual(created, [])
        self.assertEqual(updated, [])
        self.assertEqual(deleted, 15)
