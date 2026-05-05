import os
import sys
import requests
import zipfile
import io
import shutil

GITHUB_ZIP_URL = "https://github.com/yasiyorum/ChessGame/archive/refs/heads/main.zip"

def get_base_path():
    """Uygulama base path'ini döndür (PyInstaller uyumlu)"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    else:
        return os.path.dirname(__file__)

def get_appdata_dir():
    """Kalıcı veri klasörü (%APPDATA%/ChessPro)"""
    if getattr(sys, 'frozen', False) or sys.platform == "win32":
        base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "ChessPro")
    else:
        base = os.path.join(os.path.dirname(__file__), "ChessPro_Data")
    os.makedirs(base, exist_ok=True)
    return base

def sync_from_github(target_folder_name: str):
    """
    Belirtilen klasörü (themes veya stockfish) GitHub'dan indirip
    AppData/ChessPro altına yerleştirir. Klasör varsa dokunmaz.
    """
    appdata_dir = get_appdata_dir()
    target_path = os.path.join(appdata_dir, target_folder_name)
    
    # Klasör var ve içi boş değilse bir şey yapma
    if os.path.exists(target_path) and os.listdir(target_path):
        return target_path
        
    print(f"{target_folder_name} bulunamadı. GitHub'dan indiriliyor...")
    os.makedirs(target_path, exist_ok=True)
    
    try:
        response = requests.get(GITHUB_ZIP_URL, timeout=30)
        
        # Eğer main branch bulunamazsa (404) master branch'i dene
        if response.status_code == 404:
            fallback_url = GITHUB_ZIP_URL.replace("main.zip", "master.zip")
            print(f"main.zip bulunamadı, master.zip deneniyor: {fallback_url}")
            response = requests.get(fallback_url, timeout=30)
            
        response.raise_for_status()
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            # Zip içindeki repo_adı-main/ klasörü altındaki hedefleri bul
            for zip_info in zip_ref.filelist:
                # Örn: ChessGame-main/themes/default/bK.png
                parts = zip_info.filename.split('/')
                if len(parts) > 2 and parts[1] == target_folder_name:
                    # Ana repo klasörünü (parts[0]) at
                    relative_path = os.path.join(*parts[1:])
                    extracted_path = os.path.join(appdata_dir, relative_path)
                    
                    if zip_info.is_dir():
                        os.makedirs(extracted_path, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(extracted_path), exist_ok=True)
                        with zip_ref.open(zip_info) as source, open(extracted_path, "wb") as target:
                            shutil.copyfileobj(source, target)
                            
        print(f"{target_folder_name} başarıyla indirildi.")
    except Exception as e:
        print(f"{target_folder_name} indirme hatası: {e}")
        # Hata durumunda local projeden kopyalamayı dene (fallback)
        local_path = os.path.join(os.path.dirname(__file__), target_folder_name)
        if os.path.exists(local_path):
            print(f"Lokal klasör kopyalanıyor: {local_path} -> {target_path}")
            shutil.copytree(local_path, target_path, dirs_exist_ok=True)
            
    return target_path
