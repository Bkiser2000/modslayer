import sys
import subprocess
import os
import platform

REQUIRED_PYTHON = (3, 7)
REQUIRED_PACKAGES = [
    # Tkinter is included with Python, but pywin32 is needed for Windows shortcuts
    "pywin32; platform_system=='Windows'"
]

def check_python_version():
    if sys.version_info < REQUIRED_PYTHON:
        print(f"Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]} or newer is required.")
        sys.exit(1)

def pip_install(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except Exception as e:
        print(f"Failed to install {package}: {e}")
        sys.exit(1)

def install_requirements():
    for pkg in REQUIRED_PACKAGES:
        if "; platform_system=='Windows'" in pkg:
            if platform.system() == "Windows":
                pkg = pkg.split(";")[0]
                pip_install(pkg)
        else:
            pip_install(pkg)

def create_windows_shortcut():
    try:
        import win32com.client
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        shortcut = os.path.join(desktop, "ModSlayer.lnk")
        target = sys.executable
        script = os.path.abspath("mod_manager.py")
        icon = script

        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut_obj = shell.CreateShortCut(shortcut)
        shortcut_obj.Targetpath = target
        shortcut_obj.Arguments = f'"{script}"'
        shortcut_obj.WorkingDirectory = os.path.dirname(script)
        shortcut_obj.IconLocation = icon
        shortcut_obj.save()
        print("Desktop shortcut created: ModSlayer.lnk")
    except Exception as e:
        print(f"Could not create desktop shortcut: {e}")

def main():
    print("Checking Python version...")
    check_python_version()
    print("Installing required packages...")
    install_requirements()

    print("\nInstallation complete!")
    print("To run ModSlayer, use:")
    print(f"    python mod_manager.py")
    if platform.system() == "Windows":
        create_windows_shortcut()
        print("You can also use the desktop shortcut if created.")

if __name__ == "__main__":
    main()
