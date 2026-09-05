"""
core/hosting.py — Video ko ek PUBLIC URL pe daalna.

⚠️ KYUN ZAROORI HAI: Instagram local file upload NAHI leta. Tum sirf ek
`video_url` bhejte ho aur **Meta ke server khud usse download karte hain**.
Matlab video ko internet pe kahin publicly reachable hona hi padega.

Free options (₹0 constraint):

  1. github_release  ✅ RECOMMENDED
     GitHub Releases pe file attach karo. 2 GB per file, unlimited bandwidth,
     hamesha ke liye free. Sirf ek GitHub token chahiye.

  2. cloudflare_r2
     10 GB free storage + ZERO egress fees. Setup thoda lamba hai
     (S3-compatible signing khud likhni padti hai), isliye abhi sirf
     manual mode support hai.

  3. catbox
     Koi account nahi chahiye. 200 MB limit. Par ye ek volunteer-run free
     service hai — reliability ki koi guarantee nahi. Testing ke liye theek.

  4. manual
     Tum khud kahin upload karke URL de do.

Har upload ke baad URL DB mein save hota hai taaki dobara upload na ho.

⚠️ PRIVACY WARNING: ye URLs public hote hain. Jo bhi URL jaane le, wo video
dekh sakta hai. Ye theek hai kyunki video waise bhi publish hone wala hai.
Par unpublished/rejected videos ke URLs share mat karna.
"""

from __future__ import annotations

import json
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from .config import CONFIG
from .logbook import Logbook, retry

log = Logbook("hosting")

UA = "AUTOPILOT/1.0"


class HostingError(RuntimeError):
    pass


# =====================================================================
def upload(video_path: str | Path, mode: str | None = None) -> str:
    """
    Video ko public URL pe daalo aur URL lautao.
    mode: github_release | catbox | manual | r2  (default .env se)
    """
    p = Path(video_path)
    if not p.exists():
        raise HostingError(f"Video file nahi mili: {p}")

    mode = mode or os.environ.get("PUBLIC_HOST_MODE", "github_release")
    size_mb = p.stat().st_size / 1024 / 1024
    log.info(f"Video host kar rahe hain via '{mode}' ({size_mb:.1f} MB)")

    fn = {
        "github_release": _github_release,
        "catbox": _catbox,
        "manual": _manual,
        "r2": _r2_manual,
    }.get(mode)

    if not fn:
        raise HostingError(
            f"Unknown PUBLIC_HOST_MODE '{mode}'. "
            f"Allowed: github_release | catbox | manual | r2")

    url = fn(p)
    if not url or not url.startswith("http"):
        raise HostingError(f"'{mode}' ne valid URL nahi diya: {url!r}")

    verify(url, expected_mb=size_mb)
    log.ok(f"Video ab public URL pe hai", url=url)
    return url


# =====================================================================
def verify(url: str, expected_mb: float | None = None) -> bool:
    """
    URL sach mein publicly reachable hai ya nahi, HEAD request se check karo.
    Ye ZAROORI hai — Meta ko galat URL bhejna ek bekaar API call barbaad karta hai
    (aur wo rate limit mein ginti hai).
    """
    def _head():
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, dict(r.headers)

    try:
        status, headers = retry(_head, tries=3, base_delay=2.0, log=log,
                                what="URL verify")
    except Exception as e:  # noqa: BLE001
        raise HostingError(
            f"Public URL reachable nahi hai: {url}\n"
            f"Reason: {str(e)[:200]}\n"
            f"→ Instagram bhi isse fetch nahi kar payega. Hosting check karo.") from e

    ctype = headers.get("Content-Type", "")
    clen = int(headers.get("Content-Length", 0) or 0)

    if clen and expected_mb and abs(clen / 1024 / 1024 - expected_mb) > 1.0:
        log.warn(f"Hosted file ka size alag hai ({clen/1024/1024:.1f} MB vs "
                 f"{expected_mb:.1f} MB) — upload adhoora ho sakta hai")

    # HTML mila = ye ek landing page hai, seedha video file nahi
    if "text/html" in ctype:
        raise HostingError(
            f"URL video nahi, HTML page de raha hai (Content-Type: {ctype}).\n"
            f"→ Instagram ko SEEDHA video file ka URL chahiye, download page ka nahi.\n"
            f"   Google Drive / Dropbox ke normal share links kaam NAHI karte.")

    log.debug("URL verify ho gaya", status=status, ctype=ctype, mb=round(clen/1024/1024, 1))
    return True


# =====================================================================
# 1. GITHUB RELEASES — recommended
# =====================================================================
def _github_release(p: Path) -> str:
    """
    GitHub Release pe asset upload karo.
    Chahiye: GITHUB_TOKEN (repo scope) + GITHUB_REPO (owner/repo format)

    Kyun ye best hai:
      - 2 GB per file, unlimited bandwidth, permanently free
      - CDN pe serve hota hai (Meta ko fetch karne mein tez)
      - Tumhare control mein hai, koi third party nahi
    """
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    repo = os.environ.get("GITHUB_REPO", "").strip()
    tag = os.environ.get("GITHUB_RELEASE_TAG", "videos").strip()

    if not token or not repo:
        raise HostingError(
            "GitHub hosting ke liye .env mein ye chahiye:\n"
            "  GITHUB_TOKEN=ghp_xxxx      <- github.com/settings/tokens\n"
            "                                (classic token, 'repo' scope tick karo)\n"
            "  GITHUB_REPO=username/repo  <- ek PRIVATE repo bhi chalega\n"
            "                                (releases public rehte hain)\n"
            "Poora guide: SETUP.md STEP 6b")

    if "/" not in repo:
        raise HostingError(f"GITHUB_REPO format galat: '{repo}'. "
                           f"'username/reponame' hona chahiye.")

    hdr = {"Authorization": f"Bearer {token}",
           "Accept": "application/vnd.github+json",
           "X-GitHub-Api-Version": "2022-11-28",
           "User-Agent": UA}

    # ---- release dhoondho ya banao ----
    rel_id = _gh_get_release(repo, tag, hdr) or _gh_create_release(repo, tag, hdr)

    # ---- asset upload ----
    # naam unique rakho, warna "already_exists" error aata hai
    name = f"{p.stem}_{uuid.uuid4().hex[:8]}{p.suffix}"
    data = p.read_bytes()
    up_url = (f"https://uploads.github.com/repos/{repo}/releases/{rel_id}/assets"
              f"?name={urllib.parse.quote(name)}")

    def _upload():
        req = urllib.request.Request(
            up_url, data=data, method="POST",
            headers={**hdr, "Content-Type": "video/mp4",
                     "Content-Length": str(len(data))})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            if e.code == 401:
                raise HostingError("GITHUB_TOKEN galat ya expire ho gaya. "
                                   "Naya banao: github.com/settings/tokens") from e
            if e.code == 404:
                raise HostingError(f"Repo '{repo}' nahi mila, ya token ke paas "
                                   f"'repo' scope nahi hai.") from e
            if e.code == 422:
                raise HostingError(f"GitHub ne file reject ki: {body}") from e
            raise RuntimeError(f"{e.code}: {body}") from e

    asset = retry(_upload, tries=3, base_delay=5.0, log=log, what="GitHub asset upload")
    url = asset.get("browser_download_url")
    if not url:
        raise HostingError(f"GitHub ne download URL nahi diya: {json.dumps(asset)[:200]}")
    return url


def _gh_get_release(repo: str, tag: str, hdr: dict) -> int | None:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases/tags/{urllib.parse.quote(tag)}",
        headers=hdr)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["id"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def _gh_create_release(repo: str, tag: str, hdr: dict) -> int:
    body = json.dumps({
        "tag_name": tag, "name": "AUTOPILOT videos",
        "body": "Auto-generated videos ka hosting bucket. "
                "Ye files Instagram ke fetch karne ke liye hain.",
        "draft": False, "prerelease": True,
    }).encode()
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases",
                                 data=body, method="POST", headers=hdr)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            rel = json.loads(r.read())
            log.info(f"Naya GitHub release bana: {tag}")
            return rel["id"]
    except urllib.error.HTTPError as e:
        raise HostingError(f"GitHub release nahi bana: {e.code} "
                           f"{e.read().decode('utf-8','replace')[:200]}") from e


# =====================================================================
# 2. CATBOX — no account, par volunteer-run
# =====================================================================
def _catbox(p: Path) -> str:
    """
    catbox.moe pe upload. Koi account nahi chahiye.
    ⚠️ 200 MB limit, aur ye ek free volunteer service hai — down ho sakti hai.
       Testing ke liye theek, production ke liye github_release use karo.
    """
    size_mb = p.stat().st_size / 1024 / 1024
    if size_mb > 200:
        raise HostingError(f"Catbox ki limit 200 MB hai, ye {size_mb:.0f} MB hai")

    boundary = f"----autopilot{uuid.uuid4().hex}"
    ctype = mimetypes.guess_type(p.name)[0] or "video/mp4"

    parts = []
    for k, v in (("reqtype", "fileupload"), ("userhash", "")):
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; "
                     f'name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; '
                 f'name="fileToUpload"; filename="{p.name}"\r\n'
                 f"Content-Type: {ctype}\r\n\r\n".encode())
    parts.append(p.read_bytes())
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(parts)

    def _post():
        req = urllib.request.Request(
            "https://catbox.moe/user/api.php", data=body, method="POST",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                     "User-Agent": UA, "Content-Length": str(len(body))})
        with urllib.request.urlopen(req, timeout=600) as r:
            return r.read().decode("utf-8").strip()

    url = retry(_post, tries=3, base_delay=5.0, log=log, what="catbox upload")
    if not url.startswith("http"):
        raise HostingError(f"Catbox ne URL nahi diya, ye mila: {url[:200]}")
    log.warn("Catbox use hua — ye free volunteer service hai, reliability ki "
             "guarantee nahi. Production ke liye github_release behtar hai.")
    return url


# =====================================================================
# 3 & 4. MANUAL / R2
# =====================================================================
def _manual(p: Path) -> str:
    """Tum khud upload karke URL do."""
    print("\n" + "=" * 68)
    print("  📤 MANUAL HOSTING")
    print("=" * 68)
    print(f"  Is file ko kahin public upload karo:\n     {p.resolve()}\n")
    print("  Options:")
    print("    - GitHub Release (repo -> Releases -> attach file)")
    print("    - Cloudflare R2 public bucket")
    print("    - Koi bhi web host jo SEEDHA .mp4 serve kare")
    print("\n  ⚠️ Google Drive / Dropbox ke normal share links KAAM NAHI karte —")
    print("     wo HTML page dete hain, video file nahi.")
    print("=" * 68)
    url = input("\n  Public video URL paste karo: ").strip()
    if not url:
        raise HostingError("Koi URL nahi diya")
    return url


def _r2_manual(p: Path) -> str:
    """
    Cloudflare R2. Abhi manual mode.
    (S3 SigV4 signing khud likhna 200+ line hai aur R2 ka `wrangler` CLI
     ye kaam 1 command mein kar deta hai — isliye wahi suggest karte hain.)
    """
    bucket = os.environ.get("R2_BUCKET", "").strip()
    public = os.environ.get("R2_PUBLIC_URL", "").strip().rstrip("/")
    if bucket and public:
        print(f"\n  Ye command chalao:\n     wrangler r2 object put "
              f"{bucket}/{p.name} --file={p.resolve()}\n"
              f"  Phir URL hoga: {public}/{p.name}\n")
        input("  Ho jaye to Enter dabao... ")
        return f"{public}/{p.name}"
    return _manual(p)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m core.hosting <video.mp4> [mode]")
        sys.exit(1)
    print(upload(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
