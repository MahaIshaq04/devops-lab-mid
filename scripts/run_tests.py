"""Execute real tests and always serialize their outcomes before returning status."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = {}

    def startTest(self, test):
        super().startTest(test)
        self.records[test.id()] = dict(name=test.id(), result='passed', failure_message=None)

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.record_failure(test, err)

    def addError(self, test, err):
        super().addError(test, err)
        self.record_failure(test, err)

    def record_failure(self, test, err):
        self.records[test.id()].update(result='failed', failure_message=self._exc_info_to_string(err, test))

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err:
            self.record_failure(test, err)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.records[test.id()].update(result='skipped', failure_message=reason)


def git(*args):
    result = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else 'local'


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), top_level_dir=str(ROOT))
    result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(suite)
    records = list(result.records.values())
    report = dict(repository=os.getenv('GITHUB_REPOSITORY', ROOT.name), branch=os.getenv('GITHUB_REF_NAME', git('branch', '--show-current')), commit_sha=os.getenv('GITHUB_SHA', git('rev-parse', 'HEAD')), pipeline_run_id=os.getenv('GITHUB_RUN_ID', 'local'), run_attempt=os.getenv('GITHUB_RUN_ATTEMPT', '1'), execution_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(), tests=records, total=len(records), passed=sum(t['result'] == 'passed' for t in records), failed=sum(t['result'] == 'failed' for t in records), skipped=sum(t['result'] == 'skipped' for t in records), overall_status='passed' if result.wasSuccessful() and records else 'failed')
    (ROOT / 'test-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    sys.exit(0 if report['overall_status'] == 'passed' else 1)
