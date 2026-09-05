"""
tunnel.py — Make.com ke liye public URL banao
Ye script serveo.net use karta hai (free, no account needed)
"""
import os
import subprocess
import time
import sys

secret = os.environ.get("MAKE_WEBHOOK_SECRET", "").strip()
if not secret or len(secret) < 32:
    print("\n❌ SECURITY ERROR:")
    print("Bina secret ke public URL = koi bhi tumhara quota jala sakta hai.")
    print("Pehle .env mein MAKE_WEBHOOK_SECRET set karo (min 32 characters).")
    print("Secret generate karne ke liye chalao:")
    print('  python -c "import secrets; print(secrets.token_urlsafe(32))"')
    sys.exit(1)

print("=" * 50)
print("  AUTOPILOT — Public URL bana raha hai...")
print("  (Ctrl+C se band karo)")
print("=" * 50)
print()

while True:
    print("Connecting to serveo.net...")
    try:
        proc = subprocess.Popen(
            ["ssh", 
             "-o", "StrictHostKeyChecking=no",
             "-o", "ServerAliveInterval=30",
             "-o", "ServerAliveCountMax=3",
             "-R", "80:localhost:8765",
             "serveo.net"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for line in proc.stdout:
            print(line, end="")
            if "Forwarding" in line or "http" in line.lower():
                print()
                print("👆 YE HAI TUMHARA BASE URL!")
                print("Make.com HTTP module URL mein '/api/webhook' add karke paste karo.")
                print()
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
