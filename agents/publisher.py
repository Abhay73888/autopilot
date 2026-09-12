"""
agents/publisher.py — YouTube pe upload (Phase 5). Instagram Phase 6 mein.

Section 6 ke rules jo yahan enforce hote hain:
  * RESUMABLE upload (simple upload nahi) — bada file beech mein toote to resume ho
  * privacyStatus = private + publishAt (scheduling)
  * ⭐ AI DISCLOSURE FLAG ON — status.containsSyntheticMedia = true
    (ye API se supported hai, Oct 2024 se. Hard constraint #4)
  * Quota check PEHLE — budget nahi to queue mein daalo, call mat karo
  * Publish ke baad pinned first comment (comment bait)
  * Har response ke rate-limit signals padho aur log karo

⚠️ HIDDEN LIMIT: docs 100 uploads/day kehte hain par practice mein ~7/day pe
429 aata hai. quota.py ka cap 5/day hai — hum usse pehle hi ruk jaate hain.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from core.config import CONFIG
from core.db import DB
from core.logbook import Logbook, retry
from core.oauth import Credentials, api_request, authorize
from core.quota import Quota, QuotaExceeded

log = Logbook("publisher")

UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
API = "https://www.googleapis.com/youtube/v3"

# Resumable upload chunk size. 256KB ka multiple hona ZAROORI hai (Google ki requirement).
CHUNK = 1024 * 1024 * 4     # 4 MB

# YouTube category IDs. 24 = Entertainment, 27 = Education, 22 = People & Blogs
DEFAULT_CATEGORY = "24"


class PublishError(RuntimeError):
    pass


# YouTube jo container/extension accept karta hai (upload_file() ke liye)
ALLOWED_EXTS = {".mp4", ".mov", ".m4v"}


def upload_result(status: str, *, yt_video_id: str | None = None,
                  privacy: str | None = None, upload_secs: float | None = None,
                  **extra) -> dict:
    """
    Har upload ka standard return contract — Video ID, URL, Status, Upload Time.
    Dict hi rakha (dataclass nahi) kyunki poora codebase dicts pe chalta hai.
    """
    return {
        "status": status,
        "yt_video_id": yt_video_id,
        "url": f"https://youtube.com/shorts/{yt_video_id}" if yt_video_id else None,
        "privacy": privacy,
        "upload_secs": round(upload_secs, 1) if upload_secs is not None else None,
        "uploaded_at": _now_iso() if yt_video_id else None,
        **extra,
    }


class YouTubePublisher:
    def __init__(self, db: DB | None = None, quota: Quota | None = None,
                 creds: Credentials | None = None, dry_run: bool = False):
        self.db = db or DB()
        self.quota = quota or Quota(self.db)
        self.dry_run = dry_run
        self._creds = creds

    @property
    def creds(self) -> Credentials:
        """Pehli zaroorat pe authorize karo (dry-run mein kabhi nahi)."""
        if self._creds is None:
            self._creds = authorize()
        return self._creds

    # ==================================================================
    def publish(self, video_id: int, *, privacy: str = "private",
                publish_at: str | None = None, pin_comment: bool = True) -> dict:
        """
        Ek video YouTube pe daalo.

        privacy: 'private' | 'unlisted' | 'public'
                 ⚠️ Pehle hamesha 'private' — dekh kar khud public karna.
        publish_at: ISO 8601 UTC ('2026-08-01T14:30:00Z'). Sirf private ke saath chalta hai.
        """
        row = self.db.get_video(video_id)
        if not row:
            raise PublishError(f"Video #{video_id} DB mein nahi hai")

        # ---------- GATE 1: approval (review_first) ----------
        # Ye sabse pehle — agar insaan ne approve nahi kiya to file check karne ka
        # matlab hi nahi. (Pehle order ulta tha, test ne pakda.)
        autonomy = CONFIG.get("autonomy", "review_first")
        if autonomy == "review_first" and row["status"] != "approved":
            raise PublishError(
                f"Video #{video_id} ka status '{row['status']}' hai, 'approved' nahi.\n"
                f"→ autonomy 'review_first' hai. Dashboard se approve karo: "
                f"python -m web.server\n"
                f"→ Ya config.yaml mein autonomy: auto_publish kar do")

        # ---------- GATE 2: file ----------
        path = Path(row["video_path"] or "")
        if not path.exists():
            raise PublishError(f"Video file nahi mili: {path}\n"
                               f"→ python run.py --render-only {video_id}")

        # ---------- GATE 3: validate ----------
        from pipeline.validate import validate_dir
        rep = validate_dir(path.parent)
        yt_fatals = [i for i in rep.fatals if i.code != "IG_TOO_LONG"]
        if yt_fatals:
            fatal = "; ".join(f"[{i.code}] {i.msg}" for i in yt_fatals)
            raise PublishError(f"Video validate fail — publish nahi karenge:\n  {fatal}")

        # ---------- GATE 4: quota ----------
        # ⚠️ dry-run mein SIRF check karo, kharch mat karo — warna test chalane se
        #    hi asli budget khatam ho jayega (ye bug maine khud pakda tha).
        if self.dry_run:
            if not self.quota.can_spend("youtube_uploads", 1):
                log.warn("DRY RUN: asli upload abhi block hota (quota khatam)")
            else:
                log.info("DRY RUN: quota check pass (kuch kharch nahi hua)")
        else:
            try:
                self.quota.yt_call("videos.insert", reason=f"upload video #{video_id}")
            except QuotaExceeded as e:
                self.db.set_status(video_id, "approved", note=f"quota wait: {e}")
                self.db.log_event("publish_deferred", "publisher", video_id, reason=str(e))
                log.warn("Upload aaj nahi hoga — quota khatam. Video queue mein hai.",
                         reset=self.quota.reset_in_human("youtube_uploads"))
                return {"status": "queued", "reason": str(e)}

        # ---------- metadata ----------
        meta = self._build_metadata(row, privacy, publish_at)

        if self.dry_run:
            log.info("DRY RUN — asli upload nahi ho raha")
            print(json.dumps(meta, ensure_ascii=False, indent=2))
            return {"status": "dry_run", "metadata": meta}

        # ---------- upload ----------
        self.db.set_status(video_id, "publishing")
        try:
            yt_id = self._resumable_upload(path, meta)
        except Exception as e:
            self.db.set_status(video_id, "approved",
                               note=f"upload fail: {str(e)[:180]}")
            self.db.log_event("publish_failed", "publisher", video_id, error=str(e)[:500])
            raise

        url = f"https://youtube.com/shorts/{yt_id}"
        self.db.update_video(video_id, yt_video_id=yt_id, status="published",
                             published_ts=_now_iso(), scheduled_ts=publish_at)
        self.db.log_event("published", "publisher", video_id,
                          platform="youtube", yt_video_id=yt_id, privacy=privacy)
        log.ok(f"✅ YouTube pe chala gaya: {url}", video_id=video_id, privacy=privacy)

        # ---------- thumbnail (thumbnail.jpg ya cover frame, agar bana ho) ----------
        out_dir = path.parent
        thumb = out_dir / "thumbnail.jpg"
        if not thumb.exists():
            thumb = Path(row["cover_path"] or "") if "cover_path" in row.keys() else None
        if thumb and Path(thumb).exists():
            self.set_thumbnail(yt_id, thumb)

        # ---------- pinned first comment (Section 8: comment seeding) ----------
        if pin_comment and privacy != "private":
            self._first_comment(video_id, yt_id, row)
        elif pin_comment:
            log.info("Comment abhi nahi — video private hai. "
                     "Public karne ke baad comment post karo.")

        return {"status": "published", "yt_video_id": yt_id, "url": url,
                "privacy": privacy, "publish_at": publish_at}

    # ==================================================================
    def upload_file(self, path: str | Path, *, title: str | None = None,
                    description: str = "", tags: list[str] | None = None,
                    privacy: str = "private", publish_at: str | None = None,
                    thumbnail: str | Path | None = None,
                    category: str = DEFAULT_CATEGORY,
                    language: str | None = None,
                    playlist: str | None = None) -> dict:
        """
        KOI BHI MP4 seedha YouTube pe daalo — DB row zaroori nahi (Phase 4).

        publish() DB-driven pipeline ke liye hai; ye ad-hoc files ke liye.
        Wahi safety yahan bhi: quota gate, AI disclosure, retry, resumable.

        path:       video file (.mp4/.mov/.m4v)
        title:      na do to filename use hoga
        privacy:    'private' | 'unlisted' | 'public'
        publish_at: ISO 8601 UTC — sirf private ke saath
        thumbnail:  na do to video ke folder mein cover.jpg dhoondha jayega
        language:   BCP-47 code ('hi'/'en') — Phase 5 detect karke deta hai
        playlist:   playlist NAAM — mil gayi to usme, nahi to ban ke usme (Phase 5)

        Return: upload_result() dict — status, yt_video_id, url, privacy,
                upload_secs, uploaded_at.
        Errors: PublishError (invalid file / API fail), QuotaExceeded kabhi
                raise NAHI hota — status='queued' milta hai.
        """
        # ---------- GATE: file ----------
        p = Path(path)
        if not p.is_absolute():
            p = Path(CONFIG["_root"]) / p
        if not p.exists():
            raise PublishError(f"Video file nahi mili: {p}")
        if p.suffix.lower() not in ALLOWED_EXTS:
            raise PublishError(
                f"'{p.suffix}' file YouTube pe nahi jaati — "
                f"{'/'.join(sorted(ALLOWED_EXTS))} chahiye. "
                f"Convert: ffmpeg -i \"{p.name}\" -c:v libx264 -c:a aac out.mp4")
        if p.stat().st_size == 0:
            raise PublishError(f"File khaali (0 bytes) hai: {p}")

        # ---------- GATE: quota (publish() jaisa hi pattern) ----------
        if self.dry_run:
            if not self.quota.can_spend("youtube_uploads", 1):
                log.warn("DRY RUN: asli upload abhi block hota (quota khatam)")
        else:
            try:
                self.quota.yt_call("videos.insert", reason=f"upload_file {p.name}")
            except QuotaExceeded as e:
                log.warn("Upload aaj nahi hoga — quota khatam.",
                         reset=self.quota.reset_in_human("youtube_uploads"))
                return upload_result("queued", reason=str(e))

        # ---------- metadata ----------
        title = (title or p.stem.replace("_", " "))[:95]
        tags = tags or []
        status: dict = {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
            # ⭐ HARD CONSTRAINT #4 — AI disclosure yahan bhi non-negotiable
            "containsSyntheticMedia": True,
            "license": "youtube",
            "embeddable": True,
        }
        if publish_at:
            if privacy != "private":
                log.warn("publishAt sirf private ke saath chalta hai — ignore")
            else:
                status["publishAt"] = publish_at
        meta = {
            "snippet": {
                "title": title,
                "description": description[:4900],
                "tags": [t.lstrip("#") for t in tags][:30],  # Phase 5: 15-30 tags
                "categoryId": category,
            },
            "status": status,
        }
        if language:                       # Phase 5: language detection ka result
            meta["snippet"]["defaultLanguage"] = language
            meta["snippet"]["defaultAudioLanguage"] = language

        if self.dry_run:
            log.info("DRY RUN — asli upload nahi ho raha")
            return upload_result("dry_run", privacy=privacy, metadata=meta)

        # ---------- upload (resumable + retry, progress log ke saath) ----------
        t0 = time.time()
        yt_id = self._resumable_upload(p, meta)
        elapsed = time.time() - t0

        # ---------- thumbnail (fail hua to upload phir bhi success hai) ----------
        thumb = Path(thumbnail) if thumbnail else (p.parent / "thumbnail.jpg" if (p.parent / "thumbnail.jpg").exists() else p.parent / "cover.jpg")
        if thumb.exists():
            self.set_thumbnail(yt_id, thumb)

        # ---------- playlist (Phase 5; fail hua to bhi upload success hai) ----------
        playlist_id = None
        if playlist:
            try:
                playlist_id = self.add_to_playlist(yt_id, playlist, privacy=privacy)
            except (PublishError, QuotaExceeded) as e:
                log.warn(f"Playlist mein nahi daal paye (upload phir bhi OK): {e}")

        res = upload_result("published", yt_video_id=yt_id, privacy=privacy,
                            upload_secs=elapsed, publish_at=publish_at,
                            playlist_id=playlist_id)
        self.db.log_event("published", "publisher", None, platform="youtube",
                          yt_video_id=yt_id, privacy=privacy, file=str(p),
                          upload_secs=res["upload_secs"])
        log.ok(f"✅ Upload ho gaya: {res['url']}", secs=res["upload_secs"])
        return res

    # ==================================================================
    def _build_metadata(self, row, privacy: str, publish_at: str | None) -> dict:
        script = json.loads(row["script_json"] or "{}")
        tags = json.loads(row["hashtags"] or "[]")
        hashtags = " ".join(t if t.startswith("#") else f"#{t}" for t in tags)

        # Shorts ke liye #shorts description mein helpful hai
        desc_parts = [
            script.get("caption") or row["caption"] or "",
            "",
            script.get("comment_bait", ""),
            "",
            f"{hashtags} #shorts",
            "",
            "⚠️ Ye video AI se banaya gaya hai (cartoon illustration + AI narration).",
        ]
        description = "\n".join(p for p in desc_parts if p is not None)[:4900]

        title = (row["title"] or row["topic"] or "Untitled")[:95]
        if "#shorts" not in title.lower() and len(title) < 88:
            title = f"{title} #shorts"

        status = {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
            # ⭐ HARD CONSTRAINT #4 — AI disclosure. Ye NON-NEGOTIABLE hai.
            # Undisclosed AI content = reduced recommendations ya removal.
            "containsSyntheticMedia": True,
            "license": "youtube",
            "embeddable": True,
        }
        # publishAt sirf private ke saath chalta hai (Section 2)
        if publish_at:
            if privacy != "private":
                log.warn("publishAt sirf privacyStatus='private' ke saath chalta hai — "
                         "ignore kar rahe hain")
            else:
                status["publishAt"] = publish_at

        return {
            "snippet": {
                "title": title,
                "description": description,
                "tags": [t.lstrip("#") for t in tags][:15],
                "categoryId": DEFAULT_CATEGORY,
                "defaultLanguage": "hi" if str(CONFIG.get("language", "")).lower()
                                   .startswith("hi") else "en",
            },
            "status": status,
        }

    # ==================================================================
    def _resumable_upload(self, path: Path, meta: dict) -> str:
        """
        Resumable upload — 2 steps:
          1. Session shuru karo (metadata bhejo) -> upload URL milta hai
          2. File chunks mein bhejo. Beech mein toote to wahin se resume.
        """
        size = path.stat().st_size
        log.info(f"Upload shuru: {path.name} ({size/1024/1024:.1f} MB)")

        # ---- STEP 1: session ----
        def _start():
            body = json.dumps(meta).encode("utf-8")
            req = urllib.request.Request(
                f"{UPLOAD_URL}?uploadType=resumable&part=snippet,status",
                data=body, method="POST",
                headers={**self.creds.auth_header(),
                         "Content-Type": "application/json; charset=UTF-8",
                         "X-Upload-Content-Length": str(size),
                         "X-Upload-Content-Type": "video/mp4"})
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    loc = r.headers.get("Location")
                    if not loc:
                        raise PublishError("Upload session URL nahi mila")
                    return loc
            except urllib.error.HTTPError as e:
                raise _yt_error(e) from e

        upload_url = retry(_start, tries=3, base_delay=3.0, log=log,
                           what="upload session start")

        # ---- STEP 2: chunks ----
        uploaded = 0
        with path.open("rb") as f:
            while uploaded < size:
                f.seek(uploaded)
                chunk = f.read(CHUNK)
                end = uploaded + len(chunk) - 1

                def _send(c=chunk, s=uploaded, e=end):
                    req = urllib.request.Request(
                        upload_url, data=c, method="PUT",
                        headers={"Content-Length": str(len(c)),
                                 "Content-Range": f"bytes {s}-{e}/{size}"})
                    try:
                        with urllib.request.urlopen(req, timeout=300) as r:
                            return r.status, json.loads(r.read() or b"{}")
                    except urllib.error.HTTPError as err:
                        if err.code == 308:      # "Resume Incomplete" — ye NORMAL hai
                            rng = (err.headers or {}).get("Range", "")
                            return 308, {"range": rng}
                        raise _yt_error(err) from err

                status, payload = retry(_send, tries=4, base_delay=4.0, log=log,
                                        what=f"chunk {uploaded//CHUNK + 1}")

                if status == 308:
                    rng = payload.get("range", "")
                    uploaded = int(rng.split("-")[-1]) + 1 if "-" in rng else uploaded + len(chunk)
                    pct = 100 * uploaded / size
                    bar = "█" * int(pct // 5) + "░" * (20 - int(pct // 5))
                    print(f"\r  📤 [{bar}] {pct:5.1f}%  "
                          f"{uploaded/1024/1024:.1f}/{size/1024/1024:.1f} MB",
                          end="", flush=True)
                    log.debug(f"upload {pct:.0f}%", bytes=uploaded)
                elif status in (200, 201):
                    print(f"\r  📤 [{'█' * 20}] 100.0%  "
                          f"{size/1024/1024:.1f}/{size/1024/1024:.1f} MB")
                    vid = payload.get("id")
                    if not vid:
                        raise PublishError(f"Upload complete par video id nahi mila: {payload}")
                    log.ok("Upload 100% ho gaya", yt_video_id=vid)
                    return vid
                else:
                    raise PublishError(f"Upload pe anokha status {status}: {payload}")

        raise PublishError("Upload loop khatam par video id nahi mila")

    # ==================================================================
    def _first_comment(self, video_id: int, yt_id: str, row):
        """
        Pinned first comment — Section 8 ka "comment seeding".
        Specific sawaal jo 5+ shabd ka jawab maange (chhote comments ignore hote hain).
        ⚠️ Pin karna API se possible NAHI hai — wo manually Studio mein karna padega.
        """
        script = json.loads(row["script_json"] or "{}")
        text = script.get("comment_bait", "").strip()
        if not text:
            return
        try:
            self.quota.yt_call("commentThreads.insert", reason=f"first comment #{video_id}")
        except QuotaExceeded as e:
            log.warn(f"Comment ke liye quota nahi: {e}")
            return

        st, data, _ = api_request(
            self.creds, f"{API}/commentThreads?part=snippet", method="POST",
            body={"snippet": {"videoId": yt_id,
                              "topLevelComment": {"snippet": {"textOriginal": text}}}})
        if st in (200, 201):
            log.ok("First comment post ho gaya", text=text[:60])
            log.warn("⚠️ Comment ko PIN karna API se nahi hota — "
                     "YouTube Studio mein manually pin karo (30 second ka kaam, "
                     "par early engagement ke liye important hai)")
            self.db.log_event("first_comment", "publisher", video_id, yt_id=yt_id)
        else:
            log.warn(f"First comment fail: {st}", detail=json.dumps(data)[:200])

    # ==================================================================
    def channel_info(self) -> dict:
        """Channel ki basic info + uploads playlist id (TrendScout ke liye chahiye)."""
        self.quota.yt_call("channels.list", reason="channel info")
        st, data, _ = api_request(
            self.creds,
            f"{API}/channels?part=snippet,contentDetails,statistics&mine=true")
        if st != 200 or not data.get("items"):
            raise PublishError(f"Channel info nahi mili: {st} {json.dumps(data)[:200]}")
        it = data["items"][0]
        return {
            "channel_id": it["id"],
            "title": it["snippet"]["title"],
            "uploads_playlist": it["contentDetails"]["relatedPlaylists"]["uploads"],
            "subscribers": it.get("statistics", {}).get("subscriberCount"),
            "video_count": it.get("statistics", {}).get("videoCount"),
        }

    # ==================================================================
    # PLAYLIST (Phase 5)
    # ==================================================================
    def find_playlist(self, name: str) -> str | None:
        """Apni playlists mein naam se dhoondho (case-insensitive). Milte hi id."""
        page = ""
        for _ in range(10):                      # max 500 playlists — kaafi hai
            self.quota.yt_call("playlists.list", reason=f"find '{name}'")
            st, data, _ = api_request(
                self.creds,
                f"{API}/playlists?part=snippet&mine=true&maxResults=50&pageToken={page}")
            if st != 200:
                raise PublishError(f"Playlist list fail: {st} {json.dumps(data)[:200]}")
            for it in data.get("items", []):
                if it["snippet"]["title"].strip().lower() == name.strip().lower():
                    return it["id"]
            page = data.get("nextPageToken", "")
            if not page:
                break
        return None

    def create_playlist(self, name: str, description: str = "",
                        privacy: str = "public") -> str:
        """Nayi playlist banao. Return: playlist id."""
        self.quota.yt_call("playlists.insert", reason=f"create '{name}'")
        st, data, _ = api_request(
            self.creds, f"{API}/playlists?part=snippet,status", method="POST",
            body={"snippet": {"title": name[:150], "description": description[:5000]},
                  "status": {"privacyStatus": privacy}})
        if st not in (200, 201):
            raise PublishError(f"Playlist banane mein fail: {st} {json.dumps(data)[:200]}")
        log.ok(f"Nayi playlist bani: '{name}'", playlist_id=data["id"])
        return data["id"]

    def add_to_playlist(self, yt_video_id: str, playlist_name: str,
                        privacy: str = "public") -> str:
        """
        Video ko naam wali playlist mein daalo — playlist na ho to BANA do.
        Return: playlist id. Fail = PublishError (caller decide kare).
        """
        pl_id = self.find_playlist(playlist_name)
        if not pl_id:
            log.info(f"Playlist '{playlist_name}' nahi mili — bana rahe hain")
            # playlist khud private video se match nahi hoti — public hi rakho
            pl_id = self.create_playlist(
                playlist_name, description=f"{CONFIG.get('brand_name', 'AUTOPILOT')} videos",
                privacy="public" if privacy != "private" else "unlisted")
        self.quota.yt_call("playlistItems.insert", reason=f"add to '{playlist_name}'")
        st, data, _ = api_request(
            self.creds, f"{API}/playlistItems?part=snippet", method="POST",
            body={"snippet": {"playlistId": pl_id,
                              "resourceId": {"kind": "youtube#video",
                                             "videoId": yt_video_id}}})
        if st not in (200, 201):
            raise PublishError(f"Playlist mein add fail: {st} {json.dumps(data)[:200]}")
        log.ok(f"Video playlist '{playlist_name}' mein chala gaya", playlist_id=pl_id)
        return pl_id

    def set_thumbnail(self, yt_id: str, image_path: str | Path) -> bool:
        """Cover frame / thumbnail.jpg ko thumbnail banao (50 units). Shorts search carousel mein ye dikhta hai."""
        p = Path(image_path)
        if not p.exists() or p.stat().st_size == 0:
            return False
        if p.stat().st_size > 2 * 1024 * 1024:
            log.warn("Thumbnail 2MB se bada hai — YouTube reject karega")
            return False

        if not self.quota.can_spend("youtube_units", 50):
            log.warn("Thumbnail upload skip — youtube_units quota kam hai (50 units chahiye)")
            return False

        if self.dry_run:
            log.info(f"DRY RUN: set_thumbnail({yt_id}, {p.name}) [50 units]")
            return True

        try:
            self.quota.yt_call("thumbnails.set", reason="thumbnail")
        except QuotaExceeded:
            return False

        content_type = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
        req = urllib.request.Request(
            f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={yt_id}",
            data=p.read_bytes(), method="POST",
            headers={**self.creds.auth_header(), "Content-Type": content_type})
        try:
            with urllib.request.urlopen(req, timeout=120):
                log.ok("Thumbnail set ho gaya", yt_id=yt_id)
                return True
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:200]
            if "thumbnailsNotAvailable" in body or e.code == 403:
                log.warn("Thumbnail set nahi hua — channel verified nahi hai. "
                         "youtube.com/verify pe phone verify karo (2 min).")
            else:
                log.warn(f"Thumbnail fail: {e.code} {body}")
            return False
        except Exception as e:
            log.warn(f"Thumbnail upload error: {str(e)[:150]}")
            return False


# =====================================================================
def _yt_error(e: urllib.error.HTTPError) -> Exception:
    """YouTube ka HTTP error -> Hinglish samajh wala exception."""
    try:
        body = json.loads(e.read())
        err = body.get("error", {})
        reason = (err.get("errors") or [{}])[0].get("reason", "")
        msg = err.get("message", "")
    except Exception:  # noqa: BLE001
        reason, msg = "", ""

    hints = {
        "quotaExceeded": "Daily quota khatam. Midnight Pacific Time pe reset hoga.",
        "uploadLimitExceeded": "⚠️ YE WAHI HIDDEN LIMIT HAI (~7 uploads/day). "
                               "Kal try karo. quota.py ka cap 5 hai — usse mat badhana.",
        "rateLimitExceeded": "Bahut tez calls gaye. Backoff retry chal raha hai.",
        "forbidden": "Permission nahi. OAuth scope 'youtube.upload' hai? "
                     "token.json delete karke dobara authorize karo.",
        "youtubeSignupRequired": "Is Google account pe YouTube channel hi nahi hai. "
                                 "Pehle channel banao.",
        "invalidVideoMetadata": "Metadata galat hai — title 100 char se bada ya "
                                "description 5000 se bada to nahi?",
        "videoNotFound": "Video id galat hai.",
        "authorizationRequired": "Token expire. `python authorize_youtube.py` chalao.",
    }
    hint = hints.get(reason, "")
    if e.code == 401:
        hint = hint or "Token invalid. token.json delete karke dobara authorize karo."
    if e.code == 429:
        hint = hint or "Rate limit. Thoda ruk kar retry hoga."

    return PublishError(f"YouTube API {e.code} [{reason}] {msg}"
                        + (f"\n→ Matlab: {hint}" if hint else ""))


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# =====================================================================
def best_publish_time(db: DB, default_hour_ist: int = 20) -> str:
    """
    Section 8: "Velocity engineering — audience ke peak window mein publish karo
    (apne hi analytics se seekho, guess mat karo)."

    Abhi analytics nahi hai (Phase 7 mein aayegi), isliye:
      - agar published videos ka data hai to jis ghante ne best 2h views diye wo
      - warna India ka general peak: 8 PM IST
    """
    from datetime import datetime, timedelta, timezone
    rows = db.q("""
        SELECT strftime('%H', v.published_ts) AS hr, AVG(m.views) AS avg_views, COUNT(*) n
        FROM videos v JOIN metrics m ON m.video_id = v.id
        WHERE v.published_ts IS NOT NULL AND m.window='2h' AND m.platform='youtube'
        GROUP BY hr HAVING n >= 2 ORDER BY avg_views DESC LIMIT 1""")
    now = datetime.now(timezone.utc)
    if rows and rows[0]["hr"] is not None:
        hour_utc = int(rows[0]["hr"])
        log.info(f"Apne data se seekha: {hour_utc}:00 UTC best hai "
                 f"(avg {rows[0]['avg_views']:.0f} views @2h, n={rows[0]['n']})")
    else:
        hour_utc = (default_hour_ist - 5) % 24   # IST = UTC+5:30, approx
        log.info(f"Abhi apna data nahi hai — default {default_hour_ist}:00 IST use kar rahe hain")

    target = now.replace(hour=hour_utc, minute=30, second=0, microsecond=0)
    if target <= now + timedelta(minutes=20):
        target += timedelta(days=1)
    return target.strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="YouTube pe video publish karo")
    ap.add_argument("video_id", type=int, nargs="?", help="DB ka video id")
    ap.add_argument("--file", help="koi bhi MP4 seedha upload karo (DB ke bina)")
    ap.add_argument("--title", help="--file ke saath: video ka title")
    ap.add_argument("--thumbnail", help="--file ke saath: thumbnail image path")
    ap.add_argument("--privacy", default="private",
                    choices=["private", "unlisted", "public"])
    ap.add_argument("--schedule", action="store_true", help="peak time pe schedule karo")
    ap.add_argument("--schedule-at", help="Phase 5: '2026-08-06 18:30' | '+3h' | ISO")
    ap.add_argument("--ai", action="store_true",
                    help="Phase 5: title/desc/tags/category AI se banao")
    ap.add_argument("--topic", help="--ai ke saath: topic (na do to title/filename)")
    ap.add_argument("--playlist", help="Phase 5: is naam ki playlist mein daalo (banegi agar nahi hai)")
    ap.add_argument("--dry-run", action="store_true", help="metadata dikhao, upload mat karo")
    ap.add_argument("--info", action="store_true", help="channel info dikhao")
    a = ap.parse_args()

    with DB() as db:
        pub = YouTubePublisher(db, dry_run=a.dry_run)
        if a.info:
            print(json.dumps(pub.channel_info(), indent=2, ensure_ascii=False))
        elif a.file:
            # ---- publish time: --schedule-at (Phase 5) > --schedule (peak) ----
            if a.schedule_at:
                from agents.metadata import MetadataAgent
                at = MetadataAgent.schedule_time(a.schedule_at)
            else:
                at = best_publish_time(db) if a.schedule else None

            kw: dict = {}
            title = a.title
            if a.ai:                                # ---- Phase 5: AI packaging ----
                from agents.metadata import MetadataAgent
                agent = MetadataAgent(db)
                topic = a.topic or a.title or Path(a.file).stem.replace("_", " ")
                pkg = agent.build(topic)
                print(agent.seo_report(pkg))
                if pkg["validation"]:
                    raise SystemExit("\n❌ Validation fail — upar ki problems pehle theek karo.")
                title = a.title or pkg["title"]
                kw = {"description": pkg["description"], "tags": pkg["tags"],
                      "category": pkg["category_id"], "language": pkg["language"]}

            print(json.dumps(
                pub.upload_file(a.file, title=title, privacy=a.privacy,
                                publish_at=at, thumbnail=a.thumbnail,
                                playlist=a.playlist, **kw),
                indent=2, ensure_ascii=False))
        elif a.video_id:
            at = best_publish_time(db) if a.schedule else None
            print(json.dumps(pub.publish(a.video_id, privacy=a.privacy, publish_at=at),
                             indent=2, ensure_ascii=False))
        else:
            ready = db.videos_by_status("approved") or db.videos_by_status("validated")
            print("Approved videos:" if ready else "Koi approved video nahi.")
            for r in ready:
                print(f"  #{r['id']}  {r['title']}")
            print("\nUpload: python -m agents.publisher <id> --dry-run")
