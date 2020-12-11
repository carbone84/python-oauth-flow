#pip install flask python-dotenv

from flask import Flask
from flask import redirect, render_template, request
import secrets, urllib.parse

app = Flask(__name__)

# OAuth Client Information
client = {
  'client_id': 'client',
  'client_secret': 'client-secret',
  'redirect_uris': ['http://localhost:5000/callback'],
  'scope': 'blog'
}

# Authorization Server Information
authorization_server = {
  'authorization_endpoint': 'http://localhost:5001/authorize',
  'token_endpoint': 'http://localhost:5001/token'
}

# Protected Resource
protected_resource = 'http://localhost:5002/resource'

access_token = ''
scope = ''
state = ''

@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
  return render_template('index.html', access_token=access_token, scope=scope)

@app.route('/authorize')
def authorize():
  state = secrets.token_urlsafe(32)
  authorize_url = build_url(authorization_server['authorization_endpoint'], {
    'response_type': 'code',
    'client_id': client['client_id'],
    'redirect_uri': client['redirect_uris'][0],
    'scope': client['scope'],
    'state': state
  })
  return redirect(authorize_url)

@app.route('/fetch_resource')
def fetch_resource():
  global access_token
  if not access_token:
    return render_template('index.html', content="Missing access token")
    
  print(f"Making request with access token: {access_token}")
    
  headers = {
    'Authorization': f"Bearer {access_token}"
  }
  resource = requests.post(protected_resource, headers=headers)

  if resource.status_code >= 200 and resource.status_code < 300:
    body = resource.json()
    return render_template('index.html', content=body)
  else:
    access_token = ''
    return render_template('index.html', content=resource.status_code)

@app.route('/callback')
def callback():
  if request.args.get('error', ''):
    return render_template('index.html', content=request.args.get('error', ''))
  
  if request.args.get('state', '') != state:
    return render_template('index.html', content=f"State value did not match, expected {state} got {request.args.get('state', '')}")

  code = request.args.get('code', '')
  data = {
    'grant_type': 'authorization_code',
    'code': code,
    'redirect_uri': client['redirect_uris'][0]
  }
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': f"Basic {encode_client_credentials(client['client_id'], client['client_secret'])}"
  }
  token_response = requests.post(authorization_server['token_endpoint'], data=data, headers=headers)
  if token_response.status_code >= 200 and token_response.status_code < 300:
    body = token_response.json()
    access_token = body['access_token']
    return render_template('index.html', access_token=access_token, scope=scope)
  else:
    return render_template('index.html', content=f"Unable to fetch access token, server response: {token_response.status_code}")


def build_url(base, options):
    url = urllib.parse.urlsplit(base)
    query_string = urllib.parse.urlencode(options)
    new_url = urllib.parse.urlunsplit((url.scheme, url.netloc, url.path, query_string, ""))
    print(f"authorize_url: {new_url}")
    return new_url