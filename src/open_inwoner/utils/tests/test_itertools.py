from django.test import SimpleTestCase

from open_inwoner.utils.iteration import batched, split


class ItertoolTestCase(SimpleTestCase):
    def test_batched(self):
        batches = list(batched([1, 2, 3, 4, 5], 2))
        self.assertEquals(batches[0], (1, 2))
        self.assertEquals(batches[1], (3, 4))
        self.assertEquals(batches[2], (5,))

        batches = list(batched([], 2))
        self.assertEquals(batches, [])

    def test_split(self):
        batches = list(split([1, 2, 3, 4, 5], 2))
        self.assertEquals(batches[0], (1, 2, 3))
        self.assertEquals(batches[1], (4, 5))
