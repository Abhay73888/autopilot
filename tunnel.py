"""
tunnel.py — Make.com ke liye public URL banao
Ye script serveo.net use karta hai (free, no account needed)
"""
import io
import os
import subprocess
import time
import sys
from pathlib import Path

# Fix Windows cp1252 emoji crash
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

secret = os.environ.get("MAKE_WEBHOOK_SECRET", "").strip()
if not secret or len(secret) < 32:
    print("\n[!] SECURITY ERROR:")
    print("Bina secret ke public URL = koi bhi tumhara quota jala sakta hai.")
    print("Pehle .env mein MAKE_WEBHOOK_SECRET set karo (min 32 characters).")
    print("Secret generate karne ke liye chalao:")
    print('  python -c "import secrets; print(secrets.token_urlsafe(32))"')
    sys.exit(1)

print("=" * 50)
print("  AUTOPILOT -- Public URL bana raha hai...")
print("  (Ctrl+C se band karo)")
print("=" * 50)
print()

while True:
    print("Connecting to secure tunnel (localhost.run)...")
    try:
        proc = subprocess.Popen(
            ["ssh", 
             "-o", "StrictHostKeyChecking=no",
             "-o", "ServerAliveInterval=30",
             "-o", "ServerAliveCountMax=3",
             "-R", "80:127.0.0.1:8765",
             "nokey@localhost.run"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        for line in proc.stdout:
            if "tunneled with tls termination" in line or "https://" in line:
                import re
                m = re.search(r"https://[a-zA-Z0-9.\-_]+", line)
                if m:
                    u = m.group(0).rstrip(".")
                    try:
                        Path("data/tunnel_url.txt").write_text(u, encoding="utf-8")
                    except Exception:
                        pass
                    print("\n" + "=" * 60)
                    print(f"  [+] ACTIVE PUBLIC URL: {u}")
                    print(f"  [>] MAKE.COM WEBHOOK : {u}/api/webhook")
                    print("=" * 60 + "\n")
            elif "Welcome to localhost.run" in line or "authenticated as" in line:
                print(line, end="")
        proc.wait()
        print("\nConnection reset ho gaya, 3 seconds mein reconnect kar raha hai...")
        time.sleep(3)
    except KeyboardInterrupt:
        print("\nTunnel band ho gaya.")
        break
    except FileNotFoundError:
        print("SSH nahi mila! OpenSSH install karo:")
        print("Settings → Apps → Optional Features → OpenSSH Client")
        break
