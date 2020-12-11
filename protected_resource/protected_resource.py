#pip install flask python-dotenv

from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    return render_template('index.html', content="HELLO PROTECTED RESOURCE")