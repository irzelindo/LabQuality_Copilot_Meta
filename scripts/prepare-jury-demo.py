"""Prepare a fresh fictional jury case, optionally using the real Meta provider.

Run with the project's Python environment. The existing database and files are
never opened. A failed real inference is retained as failed, never simulated.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--directory', type=Path)
parser.add_argument('--run-meta', action='store_true', help='Send only this fictional case to the configured Meta API')
args = parser.parse_args()
target = (args.directory or PROJECT/'.jury-demo'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')).resolve()
target.mkdir(parents=True, exist_ok=False)
from dotenv import dotenv_values
local_config = dotenv_values(PROJECT/'.env')
model_config = {name: os.environ.get(name, local_config.get(name, '')) or ''
                for name in ('LQ_MODEL_API_KEY', 'LQ_MODEL_ID', 'LQ_MODEL_BASE_URL')}
model_config['LQ_MODEL_ID'] = model_config['LQ_MODEL_ID'] or 'muse-spark-1.3'
model_config['LQ_MODEL_BASE_URL'] = model_config['LQ_MODEL_BASE_URL'] or 'https://api.meta.ai/v1'
if args.run_meta and model_config['LQ_MODEL_BASE_URL'].rstrip('/') != 'https://api.meta.ai/v1':
    raise SystemExit('The jury demo allows only https://api.meta.ai/v1/responses.')
if args.run_meta and not model_config['LQ_MODEL_API_KEY']:
    raise SystemExit('Configure LQ_MODEL_API_KEY locally before requesting a real run.')
os.environ.update(LQ_DATABASE_URL='sqlite:///'+(target/'demo.db').as_posix(),
    LQ_STORAGE_DIR=str(target/'files'), LQ_SMTP_HOST='', LQ_ODK_URL='', LQ_COOKIE_SECURE='false',
    LQ_ALLOWED_ORIGINS='http://127.0.0.1:13300,http://localhost:13300',
    **{**model_config, 'LQ_MODEL_API_KEY':model_config['LQ_MODEL_API_KEY'] if args.run_meta else ''})
sys.path.insert(0, str(PROJECT/'backend'))
os.chdir(PROJECT/'backend')
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from app.database import session_factory
from app.demo import seed_demo
from app.main import app

password = 'Fictional-recording-only-2026!'
command.upgrade(Config('alembic.ini'), 'head')
with session_factory()() as db:
    seed_demo(db, password)
    db.commit()
with TestClient(app, headers={'X-LabQuality-Client':'web'}) as client:
    def request(method, path, **kwargs):
        response = client.request(method, '/api/v1'+path, **kwargs)
        response.raise_for_status()
        return response.json()
    def login(email):
        request('POST', '/auth/login', json={'email':email,'password':password})
    login('admin@labquality.local')
    users = request('GET', '/users')
    owner = next(u for u in users if u['role']=='quality')
    verifier = next(u for u in users if u['role']=='verifier')
    lab = next(l for l in request('GET', '/laboratories') if l['code']=='SUL')
    instrument = next(i for i in request('GET', '/instruments') if i['code']=='SLIPTA-ODK-PILOT')
    answers = {c['code']:{'value':c['maximum'], 'comment':'FICTIONAL software demonstration, not real laboratory evidence.'}
               for c in instrument['criteria']}
    answers['1.5'] = {'value':0,'comment':'FICTIONAL scenario: an obsolete work instruction was found at a bench. The cause is unknown.'}
    row = {'source':'demo','external_id':'PUBLIC-DEMO-REVIEW-001','laboratory_code':'SUL',
        'instrument_code':instrument['code'],'instrument_version':instrument['version'],
        'assessment_date':'2026-11-03','answers':answers,'reason':'Fictional public demonstration.'}
    request('POST','/imports/assessments',json={'assessments':[row]})
    row['answers']['1.5']['comment'] += ' Inspect the revision log and bench copies to confirm the observation.'
    row['reason'] = 'Fictional correction: clarify the evidence to inspect; retain the earlier revision.'
    assessment_id = request('POST','/imports/assessments',json={'assessments':[row]})['assessment_ids'][0]
    content = ('FICTIONAL TRAINING PROCEDURE. Not an official SLIPTA or institutional policy.\n'
        'Approve each new document revision before making it available for use.\n'
        'Identify and remove obsolete copies from work areas, and retain one identified historical copy.\n'
        'Record the revision, approval, withdrawal and replacement.\n'
        'Investigate the cause of an obsolete copy before selecting a corrective action.\n'
        'Have another authorized person check the updated records and work areas before closing the action.')
    document = request('POST','/documents',json={'code':'PUBLIC-FICTION-DOC',
        'title':'Fictional document control training procedure','content':content,'criterion_codes':['1.5']})
    document = request('POST',f"/documents/{document['id']}/transition",json={'status':'review','version':document['version']})
    login(verifier['email'])
    for status in ('approved','published'):
        document = request('POST',f"/documents/{document['id']}/transition",json={'status':status,'version':document['version']})
    login('admin@labquality.local')
    readiness = request('GET',f'/ai/readiness/{assessment_id}')
    assert readiness['ready'] and readiness['applicable_findings_count']==1
    assert len(request('GET',f'/assessments/{assessment_id}')['revisions'])==2
    receipt = {'fictional':True,'institutional_data_used':False,'directory':str(target),
        'database':str(target/'demo.db'),'assessment_id':assessment_id,'document_id':document['id'],
        'owner_id':owner['id'],'verifier_id':verifier['id'],'laboratory_id':lab['id'],
        'readiness':readiness,'run_id':None,'status':'prepared','action_id':None}
    if args.run_meta:
        from app.worker import process_one
        receipt['run_id'] = request('POST','/ai/runs',json={'assessment_id':assessment_id})['id']
        process_one()
        run = request('GET','/ai/runs/'+receipt['run_id'])
        receipt['status'] = run['status']
        if run['status']=='completed':
            receipt.update(model=run['model'],latency_ms=run['latency_ms'],usage=run['usage'])
            (target/'genuine-meta-response.json').write_text(json.dumps(run,ensure_ascii=False,indent=2),encoding='utf-8')
        else:
            receipt['error'] = run.get('error','Real model run did not complete.')
    (target/'demo-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    (target/'fictional-evidence.txt').write_text(
        'FICTIONAL TRAINING EVIDENCE. An obsolete bench copy was replaced after reviewing its revision log. '
        'The example team investigated the cause and checked other work areas. '
        'An independent reviewer must inspect this evidence before closing the example action. '
        'This file does not establish compliance in any real laboratory.\n',encoding='utf-8')
print(json.dumps({'directory':str(target),'status':receipt['status'],'fictional':True}),flush=True)
if args.run_meta and receipt['status']!='completed':
    raise SystemExit('Real inference did not complete. See the local receipt; do not present it as completed.')
