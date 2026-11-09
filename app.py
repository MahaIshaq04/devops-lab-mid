"""Assignment submission portal; Python standard library only."""
import json
import os
import sqlite3
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).parent


def save_submission(data, database):
    fields = ('name', 'registration_number', 'assignment_title', 'submission_url')
    cleaned = {}
    for field in fields:
        value = data.get(field, '')
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'{field.replace("_", " ").capitalize()} is required.')
        cleaned[field] = value.strip()
    try:
        url = urlsplit(cleaned['submission_url'])
        valid = url.scheme in ('http', 'https') and bool(url.hostname) and not any(c.isspace() for c in cleaned['submission_url'])
        _ = url.port
    except ValueError:
        valid = False
    if not valid:
        raise ValueError('Submission URL must be a valid HTTP or HTTPS URL.')
    with closing(sqlite3.connect(database)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS submissions (id INTEGER PRIMARY KEY, name TEXT, registration_number TEXT, assignment_title TEXT, submission_url TEXT)')
        cursor = db.execute('INSERT INTO submissions (name, registration_number, assignment_title, submission_url) VALUES (?, ?, ?, ?)', tuple(cleaned.values()))
        cleaned['id'] = cursor.lastrowid
    return cleaned


def list_submissions(database):
    with closing(sqlite3.connect(database)) as db, db:
        db.row_factory = sqlite3.Row
        db.execute('CREATE TABLE IF NOT EXISTS submissions (id INTEGER PRIMARY KEY, name TEXT, registration_number TEXT, assignment_title TEXT, submission_url TEXT)')
        return [dict(row) for row in db.execute('SELECT * FROM submissions ORDER BY id DESC')]


def make_handler(database):
    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, data):
            body = json.dumps(data).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == '/api/submissions':
                self.respond(200, list_submissions(database))
            elif self.path in ('/', '/index.html'):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write((ROOT / 'static/index.html').read_bytes())
            else:
                self.respond(404, {'error': 'Not found'})

        def do_POST(self):
            if self.path != '/api/submissions':
                return self.respond(404, {'error': 'Not found'})
            try:
                length = int(self.headers.get('Content-Length', 0))
                if not 0 < length <= 65536:
                    raise ValueError('Request must contain at most 64 KiB of JSON.')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError('Expected a JSON object.')
                self.respond(201, save_submission(data, database))
            except (ValueError, UnicodeDecodeError) as exc:
                self.respond(400, {'error': str(exc)})
    return Handler


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', int(os.getenv('PORT', '8000'))), make_handler(os.getenv('DATABASE', 'submissions.db')))
    print(f'Portal: http://127.0.0.1:{server.server_port}', flush=True)
    server.serve_forever()
