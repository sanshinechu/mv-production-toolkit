import os, json, urllib.request
from google.oauth2 import service_account
import google.auth.transport.requests

env = {}
for line in open(os.path.expanduser('~/.vertexai.env'), encoding='utf-8'):
    if '=' in line and not line.lstrip().startswith('#'):
        k, v = line.strip().split('=', 1)
        env[k] = v.strip().strip('"')

cred = service_account.Credentials.from_service_account_file(
    env['GOOGLE_APPLICATION_CREDENTIALS'], scopes=['https://www.googleapis.com/auth/cloud-platform'])
cred.refresh(google.auth.transport.requests.Request())
token = cred.token
project = env['GOOGLE_CLOUD_PROJECT']

req = urllib.request.Request(
    'https://texttospeech.googleapis.com/v1/voices?languageCode=cmn-TW',
    headers={'Authorization': 'Bearer ' + token, 'x-goog-user-project': project}
)
with urllib.request.urlopen(req, timeout=30) as r:
    voices = json.load(r)['voices']
    print(f"Total cmn-TW voices: {len(voices)}")
    for v in voices:
        print(f"  {v['name']:<25} {v['ssmlGender']}")
