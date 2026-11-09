# DevOps Lab Mid — assignment submission portal

**Student:** Maha Ishaq  
**Registration number:** fa23-bai-037  
**Repository:** https://github.com/MahaIshaq04/devops-lab-mid

Python 3.10+ is required. No external Python packages are needed. The portal stores submissions persistently in SQLite.

## Run locally

```powershell
python app.py
```

Open http://127.0.0.1:8000. Enter name, registration number, assignment title and an HTTP/HTTPS submission link. Saved submissions appear below the form. The API validates requests independently of browser validation. `DATABASE` and `PORT` optionally configure the database path and port.

## Execute tests

```powershell
python scripts/run_tests.py
```

The runner executes HTTP integration tests against temporary SQLite databases. It covers valid submissions saved and listed, missing registration rejected, and invalid links rejected without saving. It writes `test-report.json`, containing repository, branch, SHA, run ID, UTC timestamp, individual outcomes and failure messages, totals and overall status. Failure returns exit code 1, causing CI to fail.

## Start the local receiver

In a separate PowerShell terminal, leave this running:

```powershell
$env:REPORT_TOKEN = 'choose-a-long-random-token'
python receiver.py
```

Reports are automatically saved to `received/test-report.json` (configure an absolute `REPORT_OUTPUT` path to save elsewhere). The default loopback endpoint is http://127.0.0.1:9000/reports. Run `python scripts/send_report.py` after tests to verify delivery, using the same `REPORT_TOKEN`. Delivery retries and fails visibly if the receiver is unavailable. The newest report atomically replaces the previous report.

## GitHub repository and CI setup

1. Create a GitHub repository and upload/push this project. From this folder:

   ```powershell
   git init -b main
   git add .
   git commit -m "Implement DevOps lab portal and test reporting"
   git remote add origin https://github.com/MahaIshaq04/devops-lab-mid.git
   git push -u origin main
   ```

2. In repository **Settings → Actions → Runners → New self-hosted runner**, select your operating system. Download and configure the runner in a separate directory using GitHub's generated commands. Add the custom label `lab-mid` during configuration, then start the runner (`.\run.cmd` on Windows). Ensure `python` is on the runner's PATH. Use a trusted repository: a self-hosted runner executes repository code on your computer.
3. Add repository Actions secret `REPORT_TOKEN` matching the receiver's environment. Optionally set Actions variable `REPORT_RECEIVER_URL` to your endpoint; when omitted it defaults to the loopback URL above. Keep the receiver and runner running on the same computer, with the receiver outside the runner checkout directory.
4. Push a change. The workflow checks out that exact pushed revision and runs its tests. Report delivery and report artifact steps use `always()` so they also execute after test failures. A report delivery error fails the job. GitHub-hosted runner localhost is not your computer; this project deliberately uses a local self-hosted runner for tests.

## Required passing → failing → corrected demonstration

1. With receiver and runner active, push the initial implementation. Open Actions and verify success; show `received/test-report.json` with the matching GitHub SHA/run ID. Preserve it outside the checkout and capture a screenshot of Actions and the file.
2. Introduce a defect in `app.py`: change `url.scheme in ('http', 'https')` to `url.scheme in ('ftp',)`. Commit and push. The valid-submission test must fail. Show the failed Actions run and automatically updated local JSON containing the failure message. Preserve this report and screenshot too.
3. Restore `url.scheme in ('http', 'https')`, commit and push. Show the passing run and the new local JSON with the corrected commit identifier. Preserve report and screenshot.

## Submission checklist and completion status

- Portal, required tests, CI configuration and local report receiver: supplied.
- GitHub repository URL: https://github.com/MahaIshaq04/devops-lab-mid
- Passing, failing, corrected GitHub Actions screenshots and matching automatically received JSON: collect using the demonstration steps.

GitHub push demonstrations and runner registration remain to be completed. Optional bonus deployment and email are outside this minimal implementation.
