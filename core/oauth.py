"""
core/oauth.py — Google OAuth 2.0, sirf stdlib se.

Kyun apna likha, google-auth-oauthlib kyun nahi?
  Maine pehle socha tha ki security-critical code borrow karna behtar hai.
  Par wo package 8+ transitive dependencies laata hai (google-auth, oauthlib,
  requests, requests-oauthlib, cachetools, pyasn1, pyasn1-modules, rsa).
  Hamein sirf 3 cheezein chahiye:
     1. Browser mein consent kholna
     2. localhost pe redirect pakadna
     3. Refresh token se access token lena
  Ye teeno stdlib se 150 line mein ho jaate hain aur code transparent rehta hai.

  ⚠️ SECURITY NOTE: Hum khud crypto nahi likh rahe. Google ka OAuth "authorization
  code" flow use kar rahe hain jisme saara crypto Google ke HTTPS endpoint pe hota hai.
  Hum sirf HTTP requests bhej rahe hain. Isliye ye safe hai.

Flow (pehli baar):
  1. Browser khulta hai -> tum Google account se login karte ho -> "Allow" dabate ho
  2. Google localhost:PORT pe redirect karta hai ek `code` ke saath
  3. Hum wo code Google ko wapas bhejte hain -> refresh_token milta hai
  4. refresh_token token.json mein save (ye HAMESHA ke liye kaam karta hai)

Uske baad har baar:
  refresh_token se naya access_token milta hai (1 ghanta valid), browser nahi khulta.
"""

from __future__ import annotations

import json
import os
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from .config import CONFIG
from .logbook import Logbook, retry

log = Logbook("oauth")

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

# Scopes — sirf utne maango jitne chahiye (Google review mein bhi ye dekha jaata hai)
YT_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",      # video upload
    "https://www.googleapis.com/auth/youtube.readonly",    # analytics/playlist padhna
    "https://www.googleapis.com/auth/youtube.force-ssl",   # comments post karna
    # ⚠️ Ye scope Phase 7 mein add hua. Agar tumne pehle authorize kiya tha to
    #    code khud bata dega ki dobara authorize karna hai (scope check hota hai).
    "https://www.googleapis.com/auth/yt-analytics.readonly",  # retention curve
]


class OAuthError(RuntimeError):
    """OAuth fail — message mein Hinglish fix likha hota hai."""


# =====================================================================
class Credentials:
    """Access token sambhalne wali class. Expire hone pe khud refresh karti hai."""

    def __init__(self, data: dict, token_path: Path, client_id: str, client_secret: str):
        self.data = data
        self.token_path = token_path
        self.client_id = client_id
        self.client_secret = client_secret

    @property
    def access_token(self) -> str:
        """Hamesha valid token do — zaroorat ho to refresh karke."""
        if self._expired():
            self.refresh()
        return self.data["access_token"]

    def _expired(self) -> bool:
        # 120 second pehle hi refresh kar lo — beech mein expire na ho jaye
        return time.time() > self.data.get("expires_at", 0) - 120

    def refresh(self):
        rt = self.data.get("refresh_token")
        if not rt:
            raise OAuthError(
                "Refresh token nahi hai. token.json delete karke dobara authorize karo:\n"
                "  python authorize_youtube.py")

        body = urllib.parse.urlencode({
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": rt,
            "grant_type": "refresh_token",
        }).encode()

        def _call():
            req = urllib.request.Request(TOKEN_URL, data=body, method="POST")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    return json.loads(r.read())
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", "replace")
                if "invalid_grant" in detail:
                    raise OAuthError(
                        "Refresh token invalid ho gaya. Ye tab hota hai jab:\n"
                        "  - tumne Google account ka password badla\n"
                        "  - app ka access revoke kiya\n"
                        "  - OAuth app 'Testing' mode mein hai (7 din baad token expire hota hai!)\n"
                        "Fix: token.json delete karo, phir `python authorize_youtube.py`.\n"
                        "Permanent fix: OAuth consent screen ko 'Production' mein publish karo."
                    ) from e
                raise RuntimeError(f"{e.code} {e.reason} :: {detail[:300]}") from e

        fresh = retry(_call, tries=3, base_delay=2.0, log=log, what="token refresh")
        self.data["access_token"] = fresh["access_token"]
        self.data["expires_at"] = time.time() + int(fresh.get("expires_in", 3600))
        if "refresh_token" in fresh:      # kabhi-kabhi naya refresh token bhi aata hai
            self.data["refresh_token"] = fresh["refresh_token"]
        self.save()
        log.debug("Access token refresh ho gaya")

    def save(self):
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        try:
            os.chmod(self.token_path, 0o600)   # sirf tum padh sako
        except OSError:
            pass   # Windows pe chmod kaam nahi karta — koi baat nahi

    def auth_header(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"}


# =====================================================================
class _CallbackHandler(BaseHTTPRequestHandler):
    """Localhost pe Google ka redirect pakadne wala mini server."""

    result: dict = {}

    def log_message(self, *a):
        pass

    def do_GET(self):  # noqa: N802
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        _CallbackHandler.result = {k: v[0] for k, v in q.items()}
        ok = "code" in _CallbackHandler.result
        msg = ("✅ Ho gaya! Ye tab band kar do aur terminal pe wapas jao."
               if ok else
               f"❌ Fail: {_CallbackHandler.result.get('error', 'pata nahi')}")
        html = f"""<html><head><meta charset="utf-8"><title>AUTOPILOT</title></head>
<body style="font-family:system-ui;background:#0d1117;color:#e6edf3;
display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
<div style="text-align:center"><h1 style="font-size:44px">{msg}</h1>
<p style="color:#7d8590">AUTOPILOT — YouTube authorization</p></div></body></html>"""
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _load_client_secret(path: Path) -> tuple[str, str]:
    """client_secret.json padho. Google do format deta hai: 'installed' ya 'web'."""
    if not path.exists():
        raise OAuthError(
            f"client_secret.json nahi mila: {path}\n"
            "Ye Google Cloud Console se milta hai:\n"
            "  1. console.cloud.google.com -> naya project banao\n"
            "  2. APIs & Services -> Library -> 'YouTube Data API v3' -> ENABLE\n"
            "  3. OAuth consent screen -> External -> apni email test user mein daalo\n"
            "  4. Credentials -> Create Credentials -> OAuth client ID -> **Desktop app**\n"
            "  5. JSON download karke is folder mein `client_secret.json` naam se rakho\n"
            "Poora guide: SETUP.md STEP 3")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise OAuthError(f"client_secret.json kharab hai (valid JSON nahi): {e}") from e

    node = data.get("installed") or data.get("web")
    if not node:
        raise OAuthError(
            "client_secret.json mein 'installed' ya 'web' key nahi hai.\n"
            "Galat type ka OAuth client banaya hoga. **Desktop app** type chahiye.")
    cid, csec = node.get("client_id"), node.get("client_secret")
    if not cid or not csec:
        raise OAuthError("client_secret.json mein client_id/client_secret missing hai")
    return cid, csec


# =====================================================================
def authorize(scopes: list[str] | None = None,
              client_secret_file: str | Path | None = None,
              token_file: str | Path | None = None,
              port: int = 8910, force: bool = False) -> Credentials:
    """
    Credentials do. token.json ho to usse padho, warna browser khol kar naya lo.
    """
    root = Path(CONFIG["_root"])
    scopes = scopes or YT_SCOPES
    cs_path = Path(client_secret_file or os.environ.get(
        "YT_CLIENT_SECRET_FILE", root / "client_secret.json"))
    if not cs_path.is_absolute():
        cs_path = root / cs_path
    tok_path = Path(token_file or os.environ.get("YT_TOKEN_FILE", root / "token.json"))
    if not tok_path.is_absolute():
        tok_path = root / tok_path

    client_id, client_secret = _load_client_secret(cs_path)

    # ---------- pehle se saved token? ----------
    if tok_path.exists() and not force:
        try:
            saved = json.loads(tok_path.read_text(encoding="utf-8"))
            creds = Credentials(saved, tok_path, client_id, client_secret)
            missing = set(scopes) - set(saved.get("scopes", []))
            if missing:
                log.warn(f"Saved token mein ye scopes nahi hain: {missing} — "
                         f"dobara authorize kar rahe hain")
            else:
                creds.access_token   # refresh test — fail hua to niche naya flow
                log.ok("YouTube authorization mil gayi (saved token se)")
                return creds
        except OAuthError:
            raise
        except Exception as e:  # noqa: BLE001
            log.warn(f"Saved token use nahi ho paaya ({str(e)[:100]}) — naya le rahe hain")

    # ---------- naya authorization flow ----------
    redirect_uri = f"http://localhost:{port}"
    state = secrets.token_urlsafe(16)   # CSRF protection
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",       # refresh_token ke liye ZAROORI
        "prompt": "consent",            # hamesha refresh_token bhejo
        "state": state,
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    try:
        server = HTTPServer(("localhost", port), _CallbackHandler)
    except OSError as e:
        raise OAuthError(
            f"Port {port} pehle se busy hai. Koi aur AUTOPILOT process chal raha hai?\n"
            f"Ya dusra port use karo: authorize(port=8911)") from e

    _CallbackHandler.result = {}
    threading.Thread(target=server.handle_request, daemon=True).start()

    print("\n" + "=" * 68)
    print("  🔐 YOUTUBE AUTHORIZATION")
    print("=" * 68)
    print("  Browser khul raha hai. Wahan ye karo:")
    print("    1. Apne YouTube channel wale Google account se login karo")
    print("    2. ⚠️  'Google hasn't verified this app' aaye to:")
    print("         Advanced -> Go to <app name> (unsafe)  pe click karo")
    print("         (Ye tumhara HI app hai, isliye safe hai — Google ne bas verify")
    print("          nahi kiya kyunki wo public app nahi hai)")
    print("    3. Saari permissions pe 'Allow' dabao")
    print("\n  Agar browser khud na khule to ye link copy karke kholo:\n")
    print(f"  {url}\n")
    print("=" * 68)

    try:
        webbrowser.open(url)
    except Exception:  # noqa: BLE001
        pass

    # ---------- redirect ka intezaar ----------
    deadline = time.time() + 300      # 5 minute
    while not _CallbackHandler.result and time.time() < deadline:
        time.sleep(0.4)
    server.server_close()

    res = _CallbackHandler.result
    if not res:
        raise OAuthError("5 minute mein koi response nahi aaya. Dobara chalao.")
    if "error" in res:
        err = res["error"]
        hint = ("Tumne 'Allow' ki jagah 'Cancel' dabaya hoga."
                if err == "access_denied" else
                "OAuth consent screen mein apni email 'Test users' mein add ki hai?")
        raise OAuthError(f"Google ne mana kar diya: {err}\n→ {hint}")
    if res.get("state") != state:
        raise OAuthError("State mismatch — security check fail. Dobara try karo.")

    # ---------- code -> tokens ----------
    body = urllib.parse.urlencode({
        "code": res["code"],
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            tokens = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise OAuthError(f"Token exchange fail: {e.code} "
                         f"{e.read().decode('utf-8','replace')[:300]}") from e

    if "refresh_token" not in tokens:
        raise OAuthError(
            "Google ne refresh_token nahi diya. Iska matlab is app ko pehle se "
            "authorize kiya hua hai.\n"
            "Fix: myaccount.google.com/permissions pe jao, is app ka access hatao, "
            "phir dobara chalao.")

    tokens["expires_at"] = time.time() + int(tokens.get("expires_in", 3600))
    tokens["scopes"] = scopes
    creds = Credentials(tokens, tok_path, client_id, client_secret)
    creds.save()
    log.ok(f"Authorization ho gayi! Token save hua: {tok_path.name}")
    print(f"\n  ✅ Ho gaya. Token save hua: {tok_path}")
    print("     Ye file KABHI GitHub pe mat daalna (.gitignore mein already hai)\n")
    return creds


# =====================================================================
def api_request(creds: Credentials, url: str, *, method: str = "GET",
                body: dict | bytes | None = None, headers: dict | None = None,
                timeout: int = 60) -> tuple[int, dict, dict]:
    """
    Authenticated API call.
    Return: (status_code, response_json, response_headers)
    HTTP errors raise nahi karte — caller decide kare (quota vs rate limit alag hain).
    """
    h = {"Content-Type": "application/json", **creds.auth_header(), **(headers or {})}
    if isinstance(body, (bytes, bytearray)):
        data = body
    elif body is not None:
        data = json.dumps(body).encode()
    else:
        data = None
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {}), dict(r.headers)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            payload = {"raw": raw.decode("utf-8", "replace")[:500]}
        return e.code, payload, dict(e.headers or {})


if __name__ == "__main__":
    c = authorize()
    st, data, _ = api_request(
        c, "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true")
    if st == 200 and data.get("items"):
        ch = data["items"][0]["snippet"]
        print(f"\n✅ Connected channel: {ch['title']}")
    else:
        print(f"\n❌ Channel fetch fail: {st} {json.dumps(data)[:300]}")
