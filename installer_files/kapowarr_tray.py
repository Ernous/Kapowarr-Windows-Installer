#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import threading
import time
import webbrowser
import socket
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import pystray
from PIL import Image, ImageDraw
import winreg

class KapowarrTray:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.app_dir = Path(sys.executable).parent
        else:
            current_dir = Path(__file__).parent
            if current_dir.name == "installer_files":
                self.app_dir = current_dir.parent
            else:
                self.app_dir = current_dir
        self.log_dir = self.app_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.tray_log = self.log_dir / "kapowarr_tray.log"
        
        self.log(f"Initializing KapowarrTray in {self.app_dir}")
        self.kapowarr_process = None
        self.icon = None
        self.is_running = False
        self.root = None
        
        try:
            self.setup_tray()
            self.log("Tray setup complete")
        except Exception as e:
            self.log(f"CRITICAL ERROR in setup_tray: {e}")
            messagebox.showerror("Critical Error", f"Failed to initialize tray: {e}")
            sys.exit(1)
            
        self.check_thread = threading.Thread(target=self.status_checker, daemon=True)
        self.check_thread.start()
        self.log("Status checker thread started")

    def log(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{timestamp}] {message}\n"
        print(msg, end='')
        try:
            with open(self.tray_log, "a", encoding="utf-8") as f:
                f.write(msg)
        except:
            pass
        
    def get_root(self):
        if not self.root:
            self.root = tk.Tk()
            self.root.withdraw()
            self.root.attributes('-topmost', True)
        return self.root

    def create_icon_image(self, color='#6c757d'):
        icon_path = self.app_dir / "favicon.ico"
        
        if icon_path.exists():
            try:
                img = Image.open(icon_path).convert('RGBA')
                img = img.resize((64, 64), Image.Resampling.LANCZOS)
                
                overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(overlay)
                
                if color == '#28a745':
                    dot_color = (40, 167, 69, 255)
                elif color == '#dc3545':
                    dot_color = (220, 53, 69, 255)
                else:
                    dot_color = (108, 117, 125, 255)
                
                draw.ellipse([42, 42, 62, 62], fill=dot_color, outline=(255, 255, 255, 255), width=2)
                img = Image.alpha_composite(img, overlay)
                
                return img
            except Exception as e:
                print(f"Error loading icon: {e}")

        try:
            image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.ellipse([5, 5, 59, 59], fill=color)
            draw.text((18, 10), "K", fill='white')
            return image
        except:
            image = Image.new('RGB', (64, 64), color=color)
            return image
    
    def update_icon(self):
        status_text = "Running" if self.is_running else "Stopped"
        color = '#28a745' if self.is_running else '#dc3545'
        
        self.icon.icon = self.create_icon_image(color)
        self.icon.title = f"Kapowarr ({status_text})"

    def is_port_open(self, host="127.0.0.1", port=5656):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex((host, port)) == 0

    def status_checker(self):
        while True:
            was_running = self.is_running
            self.is_running = self.is_port_open()
            
            if was_running != self.is_running:
                self.update_icon()
            
            time.sleep(5)
    
    def setup_tray(self):
        def get_status_label(item):
            return f"Status: {'Running' if self.is_running else 'Stopped'}"

        menu = pystray.Menu(
            pystray.MenuItem(get_status_label, lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Web Interface", self.open_web_interface, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Start Server", self.start_server, enabled=lambda item: not self.is_running),
            pystray.MenuItem("Stop Server", self.stop_server, enabled=lambda item: self.is_running),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Start with Windows", self.toggle_autostart, checked=lambda item: self.is_autostart_enabled()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.quit_application)
        )
        
        self.icon = pystray.Icon(
            "kapowarr",
            self.create_icon_image('#6c757d'),
            "Kapowarr (Checking...)",
            menu
        )
    
    def find_python_executable(self):
        portable_python = self.app_dir / "python" / "python.exe"
        if portable_python.exists():
            return str(portable_python)

        python_cmds = ['python', 'python3']
        for cmd in python_cmds:
            try:
                result = subprocess.run([cmd, '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    return cmd
            except FileNotFoundError:
                continue
        return None
    
    def start_server(self, icon=None, item=None):
        if self.is_running:
            self.log("Server is already running, ignoring start request")
            return
        
        if self.is_port_open():
            self.log("Port 5656 is already open. Server must be running as service or another instance.")
            self.is_running = True
            self.update_icon()
            return

        self.log("Starting server...")
        python_cmd = self.find_python_executable()
        if not python_cmd:
            self.log("ERROR: Python executable not found")
            messagebox.showerror("Error", "Python not found. Please reinstall Kapowarr.", parent=self.get_root())
            return
        
        try:
            log_dir = self.app_dir / "logs"
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / "kapowarr_tray_server.log"
            
            kapowarr_script = self.app_dir / "Kapowarr.py"
            if not kapowarr_script.exists():
                self.log(f"ERROR: Kapowarr.py not found at {kapowarr_script}")
                messagebox.showerror("Error", f"Kapowarr.py not found at {kapowarr_script}", parent=self.get_root())
                return

            self.log(f"Python: {python_cmd}")
            self.log(f"Script: {kapowarr_script}")
            
            env = os.environ.copy()
            env["PYTHONPATH"] = str(self.app_dir) + os.pathsep + env.get("PYTHONPATH", "")
            env["PYTHONUNBUFFERED"] = "1"
            
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0
            
            try:
                self.server_log_handle = open(log_file, "a", encoding="utf-8")
                self.server_log_handle.write(f"\n--- Starting Kapowarr via Tray at {time.ctime()} ---\n")
                self.server_log_handle.flush()
            except PermissionError:
                self.log(f"ERROR: Permission denied writing to {log_file}")
                messagebox.showerror("Permission Error", 
                    f"Failed to write to log file: {log_file}\n\nPlease run Kapowarr Tray as Administrator or check folder permissions.", 
                    parent=self.get_root())
                return
            except Exception as e:
                self.log(f"ERROR: Failed to open log file: {e}")
                messagebox.showerror("Error", f"Failed to open log file: {e}", parent=self.get_root())
                return

            self.kapowarr_process = subprocess.Popen(
                [python_cmd, "-u", str(kapowarr_script)],
                cwd=str(self.app_dir),
                stdout=self.server_log_handle,
                stderr=self.server_log_handle,
                env=env,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            self.log(f"Process started with PID: {self.kapowarr_process.pid}")
            
            def wait_for_port():
                self.log("Waiting for port 5656 to open...")
                
                def get_last_log_lines(count=10):
                    try:
                        if log_file.exists():
                            with open(log_file, "r", encoding="utf-8") as f:
                                lines = f.readlines()
                                return "".join(lines[-count:])
                    except:
                        pass
                    return "Could not read log file."

                time.sleep(0.5) 
                if self.kapowarr_process.poll() is not None:
                    exit_code = self.kapowarr_process.returncode
                    last_error = get_last_log_lines()
                    self.log(f"ERROR: Server process exited immediately with code {exit_code}")
                    self.get_root().after(0, lambda: messagebox.showerror(
                        "Kapowarr Startup Error", 
                        f"Server failed to start (Code {exit_code}).\n\nLast log entries:\n{last_error}", 
                        parent=self.get_root()
                    ))
                    return

                for i in range(60):
                    if self.is_port_open():
                        self.log("Port 5656 is open! Server started.")
                        self.is_running = True
                        self.update_icon()
                        try:
                            self.icon.notify("Server is running at http://localhost:5656", "Kapowarr started successfully!")
                        except:
                            pass
                        return
                    
                    if self.kapowarr_process.poll() is not None:
                        exit_code = self.kapowarr_process.returncode
                        last_error = get_last_log_lines()
                        self.log(f"ERROR: Server process exited with code {exit_code}")
                        self.get_root().after(0, lambda: messagebox.showerror(
                            "Kapowarr Error", 
                            f"Server process stopped unexpectedly (Code {exit_code}).\n\nLast log entries:\n{last_error}", 
                            parent=self.get_root()
                        ))
                        return
                    
                    time.sleep(0.5)
                
                self.log("ERROR: Timeout waiting for port 5656")
                self.get_root().after(0, lambda: messagebox.showwarning(
                    "Kapowarr Timeout", 
                    f"Server process is still running, but port 5656 is not responding.\nCheck logs at: {log_file}", 
                    parent=self.get_root()
                ))

            threading.Thread(target=wait_for_port, daemon=True).start()
            
        except Exception as e:
            self.log(f"ERROR starting server: {e}")
            messagebox.showerror("Error", f"Failed to start server: {str(e)}", parent=self.get_root())
    
    def stop_server(self, icon=None, item=None):
        if self.kapowarr_process:
            try:
                self.kapowarr_process.terminate()
                self.kapowarr_process.wait(timeout=5)
            except:
                try:
                    self.kapowarr_process.kill()
                except:
                    pass
            self.kapowarr_process = None

        if os.name == 'nt':
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe', '/FI', f'WINDOWTITLE eq Kapowarr*'], capture_output=True)
        
        self.is_running = False
        self.update_icon()
        self.icon.notify("Server has been shut down.", "Kapowarr stopped")
    
    def open_web_interface(self, icon=None, item=None):
        webbrowser.open("http://localhost:5656")
    
    def is_autostart_enabled(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            try:
                value, _ = winreg.QueryValueEx(key, "Kapowarr")
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except WindowsError:
            return False
    
    def toggle_autostart(self, icon=None, item=None):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            
            if self.is_autostart_enabled():
                winreg.DeleteValue(key, "Kapowarr")
                self.icon.notify("Kapowarr will no longer start with Windows.", "Autostart Disabled")
            else:
                if getattr(sys, 'frozen', False):
                    tray_path = sys.executable
                else:
                    tray_path = str(Path(__file__).absolute())
                
                winreg.SetValueEx(key, "Kapowarr", 0, winreg.REG_SZ, f'"{tray_path}"')
                self.icon.notify("Kapowarr will now start with Windows.", "Autostart Enabled")
            
            winreg.CloseKey(key)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle autostart: {str(e)}", parent=self.get_root())
    
    def quit_application(self, icon=None, item=None):
        if self.is_running:
            if messagebox.askyesno("Kapowarr", "Server is still running. Stop it and exit?", parent=self.get_root()):
                self.stop_server()
            else:
                return
        
        if self.icon:
            self.icon.stop()
        if self.root:
            self.root.destroy()
        sys.exit(0)
    
    def run(self):
        self.is_running = self.is_port_open()
        self.update_icon()
        
        if not self.is_running:
            threading.Thread(target=self.start_server, daemon=True).start()
            
        self.icon.run()

def main():
    try:
        app = KapowarrTray()
        app.run()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start tray application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
