from datetime import timedelta
from logging import LogRecord  # noqa: TID251 -- needed for testing
from unittest import TestCase, mock

from django.core.cache import caches
from django.core.cache.backends.dummy import DummyCache
from django.test import TestCase as DjangoTestCase, override_settings

import freezegun
from requests import PreparedRequest, RequestException, Response

from open_inwoner.utils.decorators import _CACHE_MISS, _DEFAULT_CACHE_TIMEOUT, cache
from open_inwoner.utils.logging import StructlogOutgoingRequestsHandler

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
                mock.call("alpha:'charlie':bravo:42", default=mock.ANY),
                mock.call("alpha:'bar':bravo:'baz'", default=mock.ANY),
                mock.call("alpha:'bar':bravo:5", default=mock.ANY),
                mock.call(
                    "alpha:'bar':bravo:'baz':'charlie':charlie:42", default=mock.ANY
                ),
                mock.call("static", default=mock.ANY),
            ]
        )

    def test_missing_timeout_kwarg_uses_default_timeout(self):
        @cache("foo")
        def foo():
            return "bar"

        self.cache.get.return_value = _CACHE_MISS
        foo()

        self.cache.get.assert_has_calls(
            [
                mock.call("foo", default=_CACHE_MISS),
            ]
        )
        self.cache.set.assert_has_calls(
            [
                mock.call("foo", "bar", timeout=_DEFAULT_CACHE_TIMEOUT),
            ]
        )

    def test_timeout_value_must_be_an_integer(self):
        for timeout in (None, "1", 1.0, object()):
            with self.subTest(timeout):
                with self.assertRaises(ValueError):

                    @cache("foo", timeout=timeout)
                    def foo():
                        pass


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

    def test_returning_none_is_not_treated_as_a_cache_miss(self):
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

    def test_optional_parameters_with_none_values_are_handled(self):
        m = mock.Mock(side_effect=lambda x, y, c: f"{x}:{y}:{c}")

        @cache("dynamic:{a}:{b}:{c}")
        def func(a: str, b: str | None = None, *, c: str | None = None):
            return m(a, b, c)

        # Miss, initial cache
        result1 = func("foo")
        # Hit
        result2 = func("foo")
        # Miss, new cache key
        result3 = func("foo", "bar")
        # Hit, kwarg should not be treated differently
        result4 = func("foo", b="bar")
        # Hit
        result5 = func("foo", "bar", c="baz")

        self.assertEqual(m.call_count, 3)
        self.assertEqual(result1, "foo:None:None")
        self.assertEqual(result2, "foo:None:None")
        self.assertEqual(result3, "foo:bar:None")
        self.assertEqual(result4, "foo:bar:None")
        self.assertEqual(result5, "foo:bar:baz")

    def test_none_and_empty_string_produce_different_cache_keys(self):
        m = mock.Mock(side_effect=lambda x: f"result:{x}")

        @cache("dynamic:{a}")
        def func(a: str | None = None):
            return m(a)

        # All three calls should miss cache because they have different values
        result1 = func(None)  # cache key: "dynamic:None"
        result2 = func("")  # cache key: "dynamic:''"
        result3 = func("None")  # cache key: "dynamic:'None'"

        self.assertEqual(m.call_count, 3)
        self.assertEqual(result1, "result:None")
        self.assertEqual(result2, "result:")
        self.assertEqual(result3, "result:None")


@mock.patch("open_inwoner.utils.logging.logger")
class StructlogOutgoingRequestsHandlerTest(TestCase):
    @staticmethod
    def create_mock_request_response_record(
        method="POST",
        url="https://api.example.com/secure",
        request_headers=None,
        status_code=201,
        response_headers=None,
        response_content=None,
        elapsed_ms=200,
    ) -> tuple[PreparedRequest, Response, LogRecord]:
        request = PreparedRequest()
        request.method = method
        request.url = url
        request.headers = request_headers or {"Content-Type": "application/json"}

        response = Response()
        response.status_code = status_code
        response.headers = response_headers or {"Content-Type": "application/json"}
        if response_content is not None:
            response._content = response_content
        response.elapsed = timedelta(milliseconds=elapsed_ms)

        record = LogRecord(
            name="log_outgoing_requests",
            level=20,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        record.req = request
        record.res = response
        record._is_log_outgoing_requests = True

        return request, response, record

    def test_emit_with_non_request_log_record(self, mock_logger):
        handler = StructlogOutgoingRequestsHandler()
        record = LogRecord(
            name="test",
            level=20,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        record._is_log_outgoing_requests = False

        handler.emit(record)

        mock_logger.debug.assert_not_called()

    def test_emit_with_successful_request(self, mock_logger):
        handler = StructlogOutgoingRequestsHandler()

        request, response, record = self.create_mock_request_response_record(
            method="GET",
            url="https://example.com/api/endpoint?foo=bar",
            status_code=200,
            response_content=b'{"result": "success"}',
            elapsed_ms=150,
        )
        record._is_log_outgoing_requests = True

        handler.emit(record)

        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args
        self.assertEqual(call_args[0][0], "outgoing_request")

        kwargs = call_args[1]
        self.assertEqual(kwargs["status_code"], 200)
        self.assertEqual(kwargs["method"], "GET")
        self.assertEqual(kwargs["url"], "https://example.com/api/endpoint?foo=bar")
        self.assertEqual(kwargs["hostname"], "example.com")
        self.assertEqual(kwargs["response_ms"], 150)
        self.assertIsNone(kwargs["trace"])

    def test_emit_with_authorization_header_scrubbing(self, mock_logger):
        handler = StructlogOutgoingRequestsHandler()

        request, response, record = self.create_mock_request_response_record(
            request_headers={
                "Authorization": "Bearer secret-token-12345",
                "Content-Type": "application/json",
            }
        )
        record._is_log_outgoing_requests = True

        handler.emit(record)

        call_args = mock_logger.debug.call_args
        kwargs = call_args[1]

        self.assertNotIn("Bearer secret-token-12345", str(kwargs))

    def test_emit_with_request_exception(self, mock_logger):
        handler = StructlogOutgoingRequestsHandler()

        request, _, _ = self.create_mock_request_response_record(
            method="GET",
            url="https://example.com/api/endpoint",
        )

        exception = RequestException("Connection timeout")
        exception.request = request
        exception.response = None

        record = LogRecord(
            name="log_outgoing_requests",
            level=40,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=(RequestException, exception, None),
        )
        record._is_log_outgoing_requests = True

        handler.emit(record)

        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args
        kwargs = call_args[1]

        self.assertEqual(kwargs["method"], "GET")
        self.assertEqual(kwargs["url"], "https://example.com/api/endpoint")
        self.assertIsNone(kwargs["status_code"])
        self.assertIsNone(kwargs["response_ms"])
        self.assertIsNotNone(kwargs["trace"])

    def test_headers_to_dict(self, mock_logger):
        headers = {
            "Content-Type": "application/json",
            "X-Request-ID": "12345",
            "Accept-Encoding": "gzip, deflate",
        }

        result = StructlogOutgoingRequestsHandler._headers_to_dict(headers, "req")

        expected = {
            "req_header__content_type": "application/json",
            "req_header__x_request_id": "12345",
            "req_header__accept_encoding": "gzip, deflate",
        }

        self.assertEqual(result, expected)
