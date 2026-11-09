import json
import os
from pathlib import Path
import smtplib
import ssl
from email.message import EmailMessage

if not os.getenv('SMTP_HOST') or not os.getenv('REPORT_EMAIL_TO'):
    print('Email bonus disabled: configure SMTP_HOST and REPORT_EMAIL_TO.')
    raise SystemExit(0)
payload = Path('test-report.json').read_bytes()
report = json.loads(payload)
message = EmailMessage()
message['From'] = os.environ['SMTP_FROM']
message['To'] = os.environ['REPORT_EMAIL_TO']
message['Subject'] = f"Lab tests {report['overall_status']}: {report['commit_sha'][:12]}"
message.set_content(f"Commit: {report['commit_sha']}\nResult: {report['overall_status']}\nTotal: {report['total']} Passed: {report['passed']} Failed: {report['failed']}\n\n" + '\n'.join(f"{test['name']}: {test['result']}" for test in report['tests']))
message.add_attachment(payload, maintype='application', subtype='json', filename='test-report.json')
with smtplib.SMTP(os.environ['SMTP_HOST'], int(os.getenv('SMTP_PORT') or '587'), timeout=30) as smtp:
    smtp.starttls(context=ssl.create_default_context())
    if os.getenv('SMTP_USERNAME'):
        smtp.login(os.environ['SMTP_USERNAME'], os.environ['SMTP_PASSWORD'])
    smtp.send_message(message)
