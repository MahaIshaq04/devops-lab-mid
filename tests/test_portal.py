import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from app import make_handler


class PortalTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(str(Path(self.directory.name) / 'test.db')))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}/api/submissions'
        self.data = dict(name='Ayesha', registration_number='FA23-BCS-001', assignment_title='DevOps Lab', submission_url='https://github.com/student/lab')

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.directory.cleanup()

    def post(self, data):
        request = Request(self.url, json.dumps(data).encode(), {'Content-Type': 'application/json'})
        try:
            response = urlopen(request)
        except HTTPError as exc:
            response = exc
        with response:
            return response.status, json.load(response)

    def rows(self):
        with urlopen(self.url) as response:
            return json.load(response)

    def test_valid_submission_is_saved_and_listed(self):
        status, result = self.post(self.data)
        self.assertEqual(status, 201)
        self.assertEqual(self.rows(), [result])
        self.assertEqual(result['registration_number'], self.data['registration_number'])

    def test_missing_registration_is_rejected(self):
        self.data.pop('registration_number')
        status, result = self.post(self.data)
        self.assertEqual(status, 400)
        self.assertIn('Registration number is required', result['error'])
        self.assertEqual(self.rows(), [])

    def test_invalid_url_is_rejected_and_not_saved(self):
        for url in ('not-a-url', 'javascript:alert(1)', 'https://', 'https://bad host/a'):
            with self.subTest(url=url):
                self.data['submission_url'] = url
                status, result = self.post(self.data)
                self.assertEqual(status, 400)
                self.assertIn('URL', result['error'])
                self.assertEqual(self.rows(), [])
