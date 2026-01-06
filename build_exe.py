# build_exe.py - Build script for Screen Monitor
import subprocess
import sys
import os

def get_customtkinter_path():
    """Get the path to customtkinter package"""
    import customtkinter
    return os.path.dirname(customtkinter.__file__)

def build():
    ctk_path = get_customtkinter_path()
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--onefile',
        '--windowed',
        '--name', 'ScreenMonitor',
        f'--add-data={ctk_path};customtkinter',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image', 
        '--hidden-import=PIL.ImageGrab',
        '--hidden-import=numpy',
        '--hidden-import=customtkinter',
        '--hidden-import=pywintypes',
        '--collect-all=customtkinter',
        'screen_monitor.py'
    ]
    
    print("Building ScreenMonitor.exe...")
    print(f"CustomTkinter path: {ctk_path}")
    print()
    
    subprocess.run(cmd)
    
    print()
    print("=" * 50)
    print("Build complete! Check the 'dist' folder for ScreenMonitor.exe")
    print("=" * 50)

if __name__ == "__main__":
    build()
