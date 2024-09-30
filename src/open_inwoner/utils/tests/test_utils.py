from datetime import timedelta
from unittest import mock

from django.core.cache import caches
from django.core.cache.backends.dummy import DummyCache
from django.test import TestCase as DjangoTestCase, override_settings

import freezegun

from open_inwoner.utils.decorators import cache

MockCache = mock.create_autospec(DummyCache)


@override_settings(
    CACHES={"default": {"BACKEND": "open_inwoner.utils.tests.test_utils.MockCache"}}
)
class DynamicCacheKeyTest(DjangoTestCase):
    def setUp(self):
        self.cache = caches["default"]
        self.cache.reset_mock()

    def test_method_key_accepts_permutations_of_attr_and_kwarg_keys(self):
        class TestClass:

            foo = "bar"
            bar = "baz"

            @cache("alpha:{self.foo}:bravo:{baz}")
            def with_kwarg_and_attr(self, baz: int):
                pass

            @cache("alpha:{bar}:bravo:{baz}")
            def with_kwargs_only(self, bar: str, baz: int):
                pass

            @cache("alpha:{self.foo}:bravo:{self.bar}")
            def with_attrs_only(self):
                pass

            @cache("alpha:{self.foo}:bravo:{self.bar}:{bar}:charlie:{baz}")
            def with_multiple_attrs_and_kwargs(self, bar, baz):
                pass

            @cache("static")
            def with_static_key(self):
                pass

        instance = TestClass()
        instance.with_kwargs_only("charlie", 42)
        instance.with_attrs_only()
        instance.with_kwarg_and_attr(baz=5)
        instance.with_multiple_attrs_and_kwargs("charlie", 42)
        instance.with_static_key()

        self.cache.get.assert_has_calls(
            [
                mock.call("alpha:charlie:bravo:42", default=mock.ANY),
                mock.call("alpha:bar:bravo:baz", default=mock.ANY),
                mock.call("alpha:bar:bravo:5", default=mock.ANY),
                mock.call("alpha:bar:bravo:baz:charlie:charlie:42", default=mock.ANY),
                mock.call("static", default=mock.ANY),
            ]
        )


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class CacheBehaviorTest(DjangoTestCase):
    def setUp(self):
        caches["default"].clear()

    def test_static_cache_key_caches_value(self):
        m = mock.MagicMock()
        m.return_value = 42

        @cache("static")
        def func():
            return m()

        results = [
            # miss
            func(),
            # hit
            func(),
        ]
        m.assert_called_once()
        self.assertEqual(results, [42, 42])

    @freezegun.freeze_time("2024-05-31 12:00:00", as_kwarg="frozen_time")
    def test_timeout_expires_value(self, frozen_time):
        m = mock.Mock(side_effect=lambda x: x)

        @cache("dynamic:{x}", timeout=1)
        def func(x):
            return m(x)

        results = [
            # miss
            func(42),
            # hit
            func(42),
        ]

        frozen_time.tick(delta=timedelta(seconds=2))
        results.extend(
            [
                # miss due to expiry
                func(42),
                # hit
                func(42),
            ]
        )

        self.assertEqual(m.call_count, 2)
        self.assertEqual(results, [42, 42, 42, 42])

    def test_dynamic_cache_key_varies_value(self):
        m = mock.Mock(side_effect=lambda x: x)

        @cache("dynamic:{a}")
        def func(a: int):
            return m(a)

        results = [func(n) for n in [5, 5, 6]]  # 1 hit

        self.assertEqual(m.call_count, 2)
        self.assertEqual(results, [5, 5, 6])

    def test_method_cache_key_varies_by_value_and_attr(self):
        m = mock.Mock(side_effect=lambda x: x)

        class TestClass:
            foo = "bar"

            @cache("alpha:{self.foo}:bravo:{baz}")
            def with_kwarg_and_attr(self, baz: int):
                return m(baz)

        class DifferentAttrTestClass(TestClass):
            foo = "fubar"

        instance1, instance2 = TestClass(), DifferentAttrTestClass()
        results = []
        for instance in instance1, instance2:
            results.extend(
                [
                    instance.with_kwarg_and_attr(5),  # miss
                    instance.with_kwarg_and_attr(5),  # hit
                    instance.with_kwarg_and_attr(6),  # miss
                    instance.with_kwarg_and_attr(6),  # hit
                ]
            )

        self.assertEqual(
            m.call_count,
            4,
            msg="Same calls with varying instance attrs should lead to cache separation",
        )
        self.assertEqual(results, [5, 5, 6, 6, 5, 5, 6, 6])

    def test_non_existent_attr_key_raises(self):
        class TestClass:
            @cache("alpha:{self.non_existent_attr}")
            def missing_attr(self):
                pass

        instance = TestClass()

        with self.assertRaises(AttributeError):
            instance.missing_attr()

    def test_nested_attr_key_raises(self):
        m = mock.Mock()
        m.nested_foo = "Nested foo"

        class TestClass:
            foo = m

            @cache("alpha:{self.foo.nested_foo}")
            def nested_attr(self):
                pass

            @cache("alpha:{self.foo.nested_foo.nested_again.and_again}")
            def deeply_nested_attr(self):
                pass

        instance = TestClass()

        with self.assertRaises(ValueError):
            instance.nested_attr()

        with self.assertRaises(ValueError):
            instance.deeply_nested_attr()

    def test_attr_key_on_plain_function_raises(self):
        @cache("{self.foo}:bar:baz")
        def foo():
            pass

        with self.assertRaises(ValueError):
            foo()

    def test_returning_None_is_not_treated_as_a_cache_miss(self):
        m = mock.Mock()

        @cache("foo")
        def returns_none():
            m()
            return None

        # The second call should return the cached "None" from the first call,
        # which the cache decorator should interpret as a valid cached value,
        # not as a cache miss.
        returns_none()
        returns_none()

        m.assert_called_once()
