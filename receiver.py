"""Local CI report receiver. Run alongside the self-hosted runner."""
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def make_handler(output, token):
    class Receiver(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != '/reports':
                self.send_error(404)
                return
            if token and not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + token):
                self.send_error(401)
                return
            try:
                length = int(self.headers.get('Content-Length', 0))
                if not 0 < length <= 2_000_000:
                    raise ValueError('Invalid report size')
                report = json.loads(self.rfile.read(length))
                required = ('repository', 'branch', 'commit_sha', 'pipeline_run_id', 'execution_timestamp', 'tests', 'total', 'passed', 'failed', 'overall_status')
                if not isinstance(report, dict) or any(key not in report for key in required):
                    raise ValueError('Missing report fields')
                if not isinstance(report['tests'], list) or report['total'] != len(report['tests']):
                    raise ValueError('Invalid test count')
                output.parent.mkdir(parents=True, exist_ok=True)
                temporary = output.with_suffix('.tmp')
                temporary.write_text(json.dumps(report, indent=2), encoding='utf-8')
                temporary.replace(output)
            except (ValueError, UnicodeDecodeError) as exc:
                self.send_error(400, str(exc))
                return
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Report saved')
    return Receiver


if __name__ == '__main__':
    output = Path(os.getenv('REPORT_OUTPUT', 'received/test-report.json')).resolve()
    server = ThreadingHTTPServer(('127.0.0.1', int(os.getenv('RECEIVER_PORT', '9000'))), make_handler(output, os.getenv('REPORT_TOKEN', '')))
    print(f'Receiver: http://127.0.0.1:{server.server_port}/reports -> {output}', flush=True)
    server.serve_forever()
