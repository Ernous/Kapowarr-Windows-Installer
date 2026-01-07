import os
import sys
import shutil
import urllib.request
import zipfile
import json
import subprocess
from pathlib import Path

import time

REPO_URL = "https://api.github.com/repos/Casvt/Kapowarr/releases/latest"

ARCH_CONFIGS = {
    "x64": {
        "python_url": "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip",
        "nssm_urls": [
            "https://github.com/dkxce/NSSM/releases/download/v2.25/NSSM_v2.25.zip",
            "https://nssm.cc/release/nssm-2.24.zip"
        ],
        "nssm_exe_path": "win64/nssm.exe"
    },
    "x86": {
        "python_url": "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-win32.zip",
        "nssm_urls": [
            "https://github.com/dkxce/NSSM/releases/download/v2.25/NSSM_v2.25.zip",
            "https://nssm.cc/release/nssm-2.24.zip"
        ],
        "nssm_exe_path": "win32/nssm.exe"
    },
    "arm64": {
        "python_url": "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-arm64.zip",
        "nssm_urls": [
            "https://github.com/dkxce/NSSM/releases/download/v2.25/NSSM_v2.25.zip",
            "https://nssm.cc/release/nssm-2.24.zip"
        ],
        "nssm_exe_path": "win64/nssm.exe"
    }
}

BASE_DIR = Path(__file__).parent
BUILD_DIR = BASE_DIR / "build_temp"
INSTALLER_FILES = BASE_DIR / "installer_files"

def download_file(url, dest, retries=3, delay=5):
    gh_token = os.environ.get("GH_TOKEN")
    
    for i in range(retries):
        print(f"Downloading {url} to {dest} (Attempt {i+1}/{retries})...")
        
        cmd = ["curl", "-L", "-s", "-f", url, "-o", str(dest)]
        if gh_token and "github.com" in url:
            cmd.extend(["-H", f"Authorization: token {gh_token}"])
        
        try:
            subprocess.run(cmd, check=True)
            if dest.exists() and dest.stat().st_size > 0:
                return # Success
            raise Exception("Downloaded file is empty or missing")
        except Exception as e:
            print(f"Attempt {i+1} failed: {e}")
            if i < retries - 1:
                print(f"Waiting {delay} seconds before retry...")
                time.sleep(delay)
            else:
                # Last attempt failed, try fallback to urllib
                print("All curl attempts failed, trying urllib fallback...")
                try:
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    if gh_token and "github.com" in url:
                        headers['Authorization'] = f'token {gh_token}'
                    
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=60) as response, open(dest, 'wb') as out_file:
                        shutil.copyfileobj(response, out_file)
                    return # Success
                except Exception as ue:
                    print(f"Urllib fallback also failed: {ue}")
                    if i == retries - 1:
                        raise Exception(f"Failed to download {url} after {retries} attempts")

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
    gh_token = os.environ.get("GH_TOKEN")
    
    cmd = ["curl", "-s", "-f", REPO_URL]
    if gh_token:
        cmd.extend(["-H", f"Authorization: token {gh_token}"])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        zip_url = data['zipball_url']
        version = data['tag_name']
    except Exception as e:
        print(f"Error fetching release info with curl: {e}, trying urllib...")
        headers = {'User-Agent': 'Mozilla/5.0'}
        if gh_token:
            headers['Authorization'] = f'token {gh_token}'
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
    
    print("Configuring Python and installing dependencies...")
    site_packages = python_dir / "site-packages"
    site_packages.mkdir(exist_ok=True)
    
    pth_file = next(python_dir.glob("python*._pth"))
    with open(pth_file, "w") as f:
        f.write(f"{pth_file.stem}.zip\n")
        f.write(".\n")
        f.write("site-packages\n")
        f.write("..\n")
        f.write("import site\n")
    
    print("Installing dependencies into site-packages...")
    shutil.copy2(src_folder / "requirements.txt", BUILD_DIR / "requirements.txt")
    
    try:
        pip_platform = {
            "x64": "win_amd64",
            "x86": "win32",
            "arm64": "win_arm64",
        }[arch]
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "--target", str(site_packages), 
            "--platform", pip_platform,
            "--python-version", "311",
            "--implementation", "cp",
            "--abi", "cp311",
            "--only-binary", ":all:",
            "--disable-pip-version-check",
            "--no-input",
            "--progress-bar", "off",
            "--upgrade",
            "--no-cache-dir",
            "-r", str(BUILD_DIR / "requirements.txt"),
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

    print("Downloading NSSM...")
    nssm_zip = BUILD_DIR / "nssm.zip"
    
    success = False
    for url in config["nssm_urls"]:
        try:
            download_file(url, nssm_zip)
            success = True
            break
        except Exception as e:
            print(f"Failed to download NSSM from {url}: {e}")
            continue
            
    if not success:
        print("Error: Could not download NSSM from any source")
        sys.exit(1)
    
    nssm_extract = BUILD_DIR / "nssm_src"
    extract_zip(nssm_zip, nssm_extract)
    
    nssm_exe = None
    search_path = "win64/nssm.exe" if "64" in arch else "win32/nssm.exe"
    
    if (nssm_extract / config["nssm_exe_path"]).exists():
        nssm_exe = nssm_extract / config["nssm_exe_path"]
    else:
        for p in nssm_extract.glob(f"**/{search_path}"):
            nssm_exe = p
            break
            
    if not nssm_exe:
        print(f"Error: Could not find nssm.exe for {arch} in extracted files")
        sys.exit(1)

    print(f"Found NSSM at: {nssm_exe}")
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
