import os
import sys
import subprocess
from pathlib import Path

def install_requirements():
    requirements = [
        "pystray",
        "pillow",
        "pyinstaller"
    ]
    
    for req in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", req])
            print(f"✓ Installed {req}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {req}")
            return False
    
    return True

def build_executable():
    tray_script = Path(__file__).parent / "kapowarr_tray.py"
    output_dir = Path(__file__).parent
    
    if not tray_script.exists():
        print(f"Error: {tray_script} not found!")
        return False

    if os.name == 'nt':
        try:
            print("Closing running tray application if any...")
            subprocess.run(["taskkill", "/F", "/IM", "kapowarr_tray.exe", "/T"], 
                         capture_output=True, text=True)
        except Exception:
            pass
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name=kapowarr_tray",
        f"--distpath={output_dir}",
        f"--workpath={output_dir / 'build'}",
        "--specpath=" + str(output_dir),
        str(tray_script)
    ]
    
    try:
        print("Building tray application...")
        subprocess.check_call(cmd)
        print("✓ Build completed successfully!")
        
        build_dir = output_dir / "build"
        if build_dir.exists():
            import shutil
            shutil.rmtree(build_dir)
        
        spec_file = output_dir / "kapowarr_tray.spec"
        if spec_file.exists():
            spec_file.unlink()
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        return False

def main():
    print("Kapowarr Tray Application Builder")
    print("=" * 40)
    
    if not Path("kapowarr_tray.py").exists():
        print("Error: kapowarr_tray.py not found in current directory!")
        sys.exit(1)
    
    print("\n1. Installing build requirements...")
    if not install_requirements():
        print("Failed to install requirements!")
        sys.exit(1)
    
    print("\n2. Building executable...")
    if not build_executable():
        print("Build failed!")
        sys.exit(1)
    
    print("\n✓ Tray application built successfully!")
    print(f"Executable location: {Path.cwd() / 'kapowarr_tray.exe'}")

if __name__ == "__main__":
    main()
