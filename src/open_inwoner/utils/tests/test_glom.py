from django.test import SimpleTestCase

from open_inwoner.utils.glom import glom_multiple


class GlomTestCase(SimpleTestCase):
    def test_glom_multiple(self):
        obj = {
            "aa": {"bb": 1},
            "cc": {"dd": 2},
        }
        self.assertEquals(glom_multiple(obj, ("aa.bb", "cc.dd")), 1)
        self.assertEquals(glom_multiple(obj, ("aa.xyz", "cc.dd")), 2)
        self.assertEquals(glom_multiple(obj, ("aa.xyz", "cc.xyz"), default=999), 999)
