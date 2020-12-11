#pip install flask python-dotenv

from flask import Flask
from flask import redirect, render_template, request
import secrets

app = Flask(__name__)

clients = [
    {
        'client_id': 'client',
        'client_secret': 'client-secret',
        'redirect_uris': ['http://localhost:5000/callback'],
        'scope': 'blog'
    }
]
codes = {}
requests = {}

@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
  return render_template('index.html', content="HELLO AUTH SERVER!")

@app.route('/authorize', methods=['GET'])
def authorize():
  client = get_client(request.args.get('client_id'))

  if not client:
    print(f"Unknown client {request.args.get('client_id')}")
    return render_template('index.html', content="Unknown client")
  elif request.args.get('redirect_uri', '') not in client['redirect_uris']:
    print(f"Mismatched redirect URI, expected {client.redirect_uris} got {request.args.get('redirect_uri', '')}")
    return render_template('index.html', content="Invalid redirect URI")
  else:
    rscope = set(request.args.get('scope', '').split(' ')) if request.args.get('scope', '') else set()
    cscope = set(client['scope'].split(' ')) if client['scope'] else set()
    if len(rscope.difference(cscope)) > 0:
      # look into url.parse in js>py
      redirect_url = request.args.get('redirect_uri') + "?error=invalid_scope"
      return redirect(redirect_url)
    
    request_id = secrets.token_urlsafe(8)
    requests[request_id] = request.args
    return render_template('approve.html', client=client, request_id=request_id, scope=rscope)

@app.route('/approve', methods=['POST'])
def approve():
  request_id = request.form.get('request_id')
  query = requests[request_id]
  del requests[request_id]

  if not query:
    return render_template('index.html', content="No matching authorization request")
  
  if request.form.get('approve'):
    if query['response_type'] == 'code':
      code = secrets.token_urlsafe(8)
      client = get_client(query['client_id'])
      rscope = set({r.replace("scope_", "") for r in dict(filter(lambda s: 'scope_' in s[0], request.form.items())).keys()})
      cscope = set(client['scope'].split(' ')) if client['scope'] else set()
      if len(rscope.difference(cscope)) > 0:
        # look into url.parse in js>py
        redirect_url = query['redirect_uri'] + "?error=invalid_scope"
        return redirect(redirect_url)
      
      codes[code] = {
        'authorization_endpoint_request': query,
        'scope': rscope
      }
      # look into url.parse in js>py
      callback_url = query['redirect_uri'] + f"?code={code}&state={query['state']}"
      return redirect(callback_url)
    else:
      callback_url = query['redirect_uri'] + "?error=unsupported_response_type"
      return redirect(callback_url)
  else:
    callback_url = query['redirect_uri'] + "?error=access_denied"
    return redirect(callback_url)

def get_client(client_id):
  for client in clients:
    if client['client_id'] == client_id:
      return client
  return "Client not found"