"""
app.py — AUTOPILOT Desktop Application Launcher.

Runs the local dashboard server and opens a dedicated Desktop App GUI window.
Can be executed directly via Python, or double-clicked via Autopilot.bat / launch_app.vbs.
"""

import os
import sys
import time
import subprocess
import threading
import webbrowser
from urllib.request import urlopen

from core.config import CONFIG
from web.server import serve, PORT

APP_URL = f"http://127.0.0.1:{PORT}"

def wait_for_server(url: str, timeout: float = 5.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False

def open_desktop_window(url: str):
    """Try pywebview or system app mode, falling back to default browser."""
    # 1. Try pywebview if installed
    try:
        import webview
        print("🚀 Opening native desktop window (pywebview)...")
        webview.create_window("🎬 AUTOPILOT - Autonomous Content Swarm", url, width=1280, height=850)
        webview.start()
        return
    except ImportError:
        pass

    # 2. Try Chrome app mode on Windows
    if sys.platform == "win32":
        chrome_paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        ]
        for cp in chrome_paths:
            if os.path.exists(cp):
                print(f"🚀 Opening Desktop App window via {os.path.basename(cp)}...")
                subprocess.Popen([cp, f"--app={url}", "--window-size=1280,850"])
                return

    # 3. Fallback to default browser
    print("🚀 Opening in default browser...")
    webbrowser.open(url)

def main():
    print("\n" + "=" * 60)
    print("  🎬 AUTOPILOT DESKTOP APPLICATION")
    print("  Starting background swarm server and GUI window...")
    print("=" * 60 + "\n")

    # Start backend HTTP server in background thread
    server_thread = threading.Thread(target=serve, kwargs={"port": PORT, "open_browser": False}, daemon=True)
    server_thread.start()

    # Wait for server readiness
    wait_for_server(APP_URL)

    # Open App Window
    open_desktop_window(APP_URL)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 AUTOPILOT App closed.")

if __name__ == "__main__":
    main()
