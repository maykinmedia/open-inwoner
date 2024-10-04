from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory


def dummy_get_response(request):
    raise NotImplementedError()


def make_request_with_middleware():
    rf = RequestFactory()

    request = rf.get("/")
    SessionMiddleware(get_response=dummy_get_response).process_request(request)
    MessageMiddleware(get_response=dummy_get_response).process_request(request)
    return request
