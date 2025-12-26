import os
from flask import Flask, send_file
app = Flask(__name__)

@app.route('/payload.py')
def download_payload():
 return send_file('payload.py')

if __name__ == '__main__':
 app.run(host='0.0.0.0', port=5000)
