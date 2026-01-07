import os
import sys
import shutil
import urllib.request
import zipfile
import json
import subprocess
from pathlib import Path

REPO_URL = "https://api.github.com/repos/Casvt/Kapowarr/releases/latest"

ARCH_CONFIGS = {
    "x64": {
        "python_url": "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip",
        "nssm_url": "https://github.com/nssm-mirror/nssm/raw/master/release/nssm-2.24.zip",
        "nssm_exe_path": "nssm-2.24/win64/nssm.exe"
    },
    "x86": {
        "python_url": "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-win32.zip",
        "nssm_url": "https://github.com/nssm-mirror/nssm/raw/master/release/nssm-2.24.zip",
        "nssm_exe_path": "nssm-2.24/win32/nssm.exe"
    },
    "arm64": {
        "python_url": "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-arm64.zip",
        "nssm_url": "https://github.com/nssm-mirror/nssm/raw/master/release/nssm-2.24.zip",
        "nssm_exe_path": "nssm-2.24/win64/nssm.exe"
    }
}

BASE_DIR = Path(__file__).parent
BUILD_DIR = BASE_DIR / "build_temp"
INSTALLER_FILES = BASE_DIR / "installer_files"

def download_file(url, dest):
    print(f"Downloading {url}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response, open(dest, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)

def extract_zip(zip_path, extract_to):
    print(f"Extracting {zip_path}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def prepare(arch="x64"):
    if arch not in ARCH_CONFIGS:
        print(f"Unsupported architecture: {arch}")
        sys.exit(1)
    
    config = ARCH_CONFIGS[arch]
    print(f"\n--- Preparing build for {arch} ---")

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir()

    print("Fetching latest Kapowarr release info...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(REPO_URL, headers=headers)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        zip_url = data['zipball_url']
        version = data['tag_name']
    
    kapowarr_zip = BUILD_DIR / f"kapowarr_{version}.zip"
    download_file(zip_url, kapowarr_zip)
    
    kapowarr_extract = BUILD_DIR / "kapowarr_src"
    extract_zip(kapowarr_zip, kapowarr_extract)
    
    src_folder = next(kapowarr_extract.glob("Casvt-Kapowarr-*"))
    
    python_zip = BUILD_DIR / "python_portable.zip"
    download_file(config["python_url"], python_zip)
    python_dir = BUILD_DIR / "python"
    extract_zip(python_zip, python_dir)
    
    print("Configuring Python and installing pip...")
    pth_file = next(python_dir.glob("python*._pth"))
    with open(pth_file, "w") as f:
        f.write(f"{pth_file.stem}.zip\n.\nimport site\n")
    
    get_pip = BUILD_DIR / "get-pip.py"
    download_file("https://bootstrap.pypa.io/get-pip.py", get_pip)
    subprocess.run([str(python_dir / "python.exe"), str(get_pip), "--no-warn-script-location"], check=True)
    
    print("Installing dependencies into portable Python...")
    shutil.copy2(src_folder / "requirements.txt", BUILD_DIR / "requirements.txt")
    subprocess.run([str(python_dir / "python.exe"), "-m", "pip", "install", "-r", str(BUILD_DIR / "requirements.txt")], check=True)
    subprocess.run([str(python_dir / "python.exe"), "-m", "pip", "install", "pystray", "Pillow", "pywin32"], check=True)

    nssm_zip = BUILD_DIR / "nssm.zip"
    download_file(config["nssm_url"], nssm_zip)
    nssm_extract = BUILD_DIR / "nssm_src"
    extract_zip(nssm_zip, nssm_extract)
    nssm_exe = nssm_extract / config["nssm_exe_path"]

    print("Organizing files for installer...")
    dest_src = BUILD_DIR / "app_files"
    shutil.copytree(src_folder, dest_src)
    shutil.move(str(python_dir), str(dest_src / "python"))
    shutil.copy2(str(nssm_exe), str(INSTALLER_FILES / "nssm.exe"))

    with open(BASE_DIR / "version.nsh", "w") as f:
        f.write(f'!define APP_VERSION "{version}"\n')
        f.write(f'!define ARCH "{arch}"\n')

    print(f"\nPre-build complete for {arch}!")
    return version

if __name__ == "__main__":
    arch = sys.argv[1] if len(sys.argv) > 1 else "x64"
    prepare(arch)
