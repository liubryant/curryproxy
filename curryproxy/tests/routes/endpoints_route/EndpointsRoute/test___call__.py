import json
import time
import uuid

from testtools import ExpectedException
import grequests
from mock import patch
from webob import Request
from testtools import TestCase

from curryproxy.routes import EndpointsRoute
from curryproxy.responses import ErrorResponse
from curryproxy.responses import MetadataResponse
from curryproxy.tests.utils import RequestsResponseMock

from curryproxy.helpers import ENVIRON_REQUEST_UUID_KEY


class Test__Call__(TestCase):
    def setUp(self):
        super(Test__Call__, self).setUp()

        self.patcher = patch.object(grequests, 'map')
        self.grequests_map = self.patcher.start()

        url_patterns = ['http://example.com/{Endpoint_IDs}/']
        endpoint = {'test': 'http://example.com/'}
        endpoints = {'1': 'http://1.example.com/',
                     '2': 'http://2.example.com/'}
        self.endpoint_route = EndpointsRoute(url_patterns, endpoint, [])
        self.endpoints_route = EndpointsRoute(url_patterns, endpoints, [])

    def test_error_response_400(self):
        request = Request.blank('http://example.com/1,2/path')

        response1 = RequestsResponseMock(status_code=200)
        response2 = RequestsResponseMock(status_code=400)
        self.grequests_map.return_value = [response1, response2]

        route_patcher___init__ = patch.object(ErrorResponse,
                                              '__init__',
                                              return_value=None)
        route_patcher___init__.start()

        mock_response = time.time()
        route_patcher_response = patch.object(ErrorResponse,
                                              'response',
                                              new=mock_response)
        route_patcher_response.start()

        response = self.endpoints_route(request)
        self.assertEqual(mock_response, response)

        route_patcher___init__.stop()
        route_patcher_response.stop()

    def test_error_response_500(self):
        request = Request.blank('http://example.com/1,2/path')

        response1 = RequestsResponseMock(status_code=200)
        response2 = RequestsResponseMock(status_code=500)
        self.grequests_map.return_value = [response1, response2]

        route_patcher___init__ = patch.object(ErrorResponse,
                                              '__init__',
                                              return_value=None)
        route_patcher___init__.start()

        mock_response = time.time()
        route_patcher_response = patch.object(ErrorResponse,
                                              'response',
                                              new=mock_response)
        route_patcher_response.start()

        response = self.endpoints_route(request)

        self.assertEqual(mock_response, response)

        route_patcher___init__.stop()
        route_patcher_response.stop()

    def test_error_response_priority_errors(self):
        request = Request.blank('http://example.com/1,2/path')

        response1 = RequestsResponseMock(status_code=200)
        response2 = RequestsResponseMock(status_code=500)
        self.grequests_map.return_value = [response1, response2]

        route_patcher___init__ = patch.object(ErrorResponse,
                                              '__init__',
                                              return_value=None)
        error_response = route_patcher___init__.start()

        mock_response = time.time()
        route_patcher_response = patch.object(ErrorResponse,
                                              'response',
                                              new=mock_response)
        route_patcher_response.start()

        self.endpoints_route(request)

        args, kwargs = error_response.call_args
        self.assertEqual(self.endpoints_route._priority_errors, args[2])

        route_patcher___init__.stop()
        route_patcher_response.stop()

    def test_metadata_response(self):
        request_headers = {'Proxy-Aggregator-Body': 'respOnse-Metadata'}
        request = Request.blank('http://example.com/1,2/path',
                                headers=request_headers)

        headers = {'Content-Type': 'application/json'}
        response1 = RequestsResponseMock(status_code=200, headers=headers)
        response2 = RequestsResponseMock(status_code=500, headers=headers)
        self.grequests_map.return_value = [response1, response2]

        route_patcher___init__ = patch.object(MetadataResponse,
                                              '__init__',
                                              return_value=None)
        metadata_response = route_patcher___init__.start()

        mock_response = time.time()
        route_patcher_response = patch.object(MetadataResponse,
                                              'response',
                                              new=mock_response)
        route_patcher_response.start()

        self.endpoints_route(request)

        self.assertTrue(metadata_response.called)

        route_patcher___init__.stop()
        route_patcher_response.stop()

    def test_grequests_streamed(self):
        request = Request.blank('http://example.com/test/path')

        with ExpectedException(TypeError):
            self.endpoint_route(request)

        self.assertTrue({'stream': True} in self.grequests_map.call_args)

    def test_timeout_body(self):
        request = Request.blank('http://example.com/1,2/path')
        request.environ[ENVIRON_REQUEST_UUID_KEY] = uuid.uuid4()

        headers = {'Content-Type': 'application/json'}
        response1 = None
        response2 = RequestsResponseMock(status_code=200,
                                         reason='OK',
                                         headers=headers)
        self.grequests_map.return_value = [response1, response2]

        response = self.endpoints_route(request)

        response_object = json.loads(response.body)
        self.assertTrue(None in response_object)
        response_200s = [i for i in response_object
                         if i is not None and i['status'] == '200 OK']
        self.assertTrue(len(response_200s) == 1)

    def test_timeout_logged(self):
        request = Request.blank('http://example.com/1,2/path')
        request.environ[ENVIRON_REQUEST_UUID_KEY] = uuid.uuid4()

        headers = {'Content-Type': 'application/json'}
        response1 = None
        response2 = RequestsResponseMock(status_code=200, headers=headers)
        self.grequests_map.return_value = [response1, response2]

        with patch('logging.error') as le:
            self.endpoints_route(request)

            self.assertTrue(le.called)

    def test_timeout_status_code(self):
        request = Request.blank('http://example.com/1,2/path')
        request.environ[ENVIRON_REQUEST_UUID_KEY] = uuid.uuid4()

        headers = {'Content-Type': 'application/json'}
        response1 = None
        response2 = RequestsResponseMock(status_code=200, headers=headers)
        self.grequests_map.return_value = [response1, response2]

        response = self.endpoints_route(request)

        self.assertEqual(504, response.status_code)

    def tearDown(self):
        super(Test__Call__, self).tearDown()

        self.patcher.stop()
