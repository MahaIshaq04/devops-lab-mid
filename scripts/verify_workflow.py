"""Local pass/fail/fix proof using isolated source copies and a real HTTP receiver."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from receiver import make_handler


def main():
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        for name in ('app.py', 'tests', 'scripts'):
            source = ROOT / name
            if source.is_dir():
                shutil.copytree(source, work / name, ignore=shutil.ignore_patterns('__pycache__'))
            else:
                shutil.copy2(source, work / name)
        output = work / 'received/test-report.json'
        server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(output, 'local-verification'))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        env = dict(os.environ, REPORT_RECEIVER_URL=f'http://127.0.0.1:{server.server_port}/reports', REPORT_TOKEN='local-verification', GITHUB_REPOSITORY='local/lab-mid-verification', GITHUB_REF_NAME='local-verification', GITHUB_SHA='local-uncommitted')
        original = (work / 'app.py').read_text(encoding='utf-8')
        try:
            for label, expected in [('passing', 0), ('failing', 1), ('corrected', 0)]:
                source = original
                if label == 'failing':
                    source = original.replace("cleaned[field] = value.strip()", "cleaned[field] = value.strip()\n        if field == 'registration_number':\n            raise ValueError('Demonstration defect: registration rejected.')")
                (work / 'app.py').write_text(source, encoding='utf-8')
                shutil.rmtree(work / '__pycache__', ignore_errors=True)
                env['GITHUB_RUN_ID'] = 'local-' + label
                result = subprocess.run([sys.executable, '-B', 'scripts/run_tests.py'], cwd=work, env=env)
                assert result.returncode == expected, (label, result.returncode)
                subprocess.run([sys.executable, 'scripts/send_report.py'], cwd=work, env=env, check=True)
                report = json.loads(output.read_text(encoding='utf-8'))
                assert report['overall_status'] == ('failed' if expected else 'passed')
                assert report == json.loads((work / 'test-report.json').read_text(encoding='utf-8'))
                shutil.copy2(output, ROOT / 'evidence' / f'local-{label}.json')
                print(f'{label}: exit={result.returncode}, HTTP delivery verified, {report["passed"]}/{report["total"]} passed', flush=True)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    main()
