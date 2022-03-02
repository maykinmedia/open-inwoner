from django.test import TestCase

from ..mixins import UUIDAdminFirstInOrder


class MockRequest:
    pass


class MockObject:
    pass


class DjangoParentAdmin:
    def get_fields(self, request, obj=None):
        return ["field1", "field2", "uuid"]


class AModelAdmin(UUIDAdminFirstInOrder, DjangoParentAdmin):
    pass


request = MockRequest()
obj = MockObject()


class TestUUIDFirstInOrder(TestCase):
    def setUp(self):
        self.ma = AModelAdmin()

    def test_uuid_is_first_in_add_form(self):
        fields = self.ma.get_fields(request, obj=None)

        self.assertEquals(fields, ["uuid", "field1", "field2"])

    def test_uuid_is_first_in_change_form(self):
        fields = self.ma.get_fields(request, obj=obj)

        self.assertEquals(fields, ["uuid", "field1", "field2"])
