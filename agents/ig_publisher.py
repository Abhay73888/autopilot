"""
agents/ig_publisher.py — Instagram Reels publishing (Phase 6).

Section 2 ke verified facts jo yahan enforce hote hain:

  * 3-STEP FLOW: POST /media (container) -> poll status tak FINISHED -> POST /media_publish
  * Video ek PUBLIC URL pe hona chahiye — Meta khud fetch karta hai (local upload nahi)
  * ⚠️ Container 24 GHANTE mein expire hota hai. Isliye pehle se container bana kar
    schedule NAHI kar sakte. Schedule apni DB mein rakho, publish time pe container banao.
  * Reel max 90 SECONDS — API strictly enforce karta hai (app mein 3 min chalta hai)
  * MP4 + H.264 + AAC. Error code 24 = format reject.
  * 200 calls/hour per user+app (polling BHI isi mein ginta hai)
  * Business ya Creator account + Facebook Page se linked
  * X-App-Usage headers har response mein — inhe padho, 80% pe slow down

  * Instagram ki native music library API se NAHI lag sakti — audio video ke
    andar hona chahiye (hamara already hai)

Naya (2026): GET /{ig-user-id}/content_publishing_limit se Meta ka apna
counter mil jaata hai — hum apne DB counter ko usse reconcile karte hain.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from core.config import CONFIG
from core.db import DB
from core.hosting import upload as host_upload
from core.logbook import Logbook, retry
from core.quota import Quota, QuotaExceeded

log = Logbook("ig")

GRAPH = "https://graph.facebook.com"
API_VERSION = os.environ.get("IG_API_VERSION", "v21.0")

# Container polling — video processing 30s se kuch minute le sakta hai
POLL_INTERVAL = 8          # second
POLL_MAX_WAIT = 300        # 5 minute — isse zyada matlab kuch gadbad hai
CONTAINER_TTL_HOURS = 24   # Meta ki limit

IG_MAX_SEC = 90


class IGError(RuntimeError):
    pass


# =====================================================================
class InstagramPublisher:
    def __init__(self, db: DB | None = None, quota: Quota | None = None,
                 dry_run: bool = False):
        self.db = db or DB()
        self.quota = quota or Quota(self.db)
        self.dry_run = dry_run
        self.token = os.environ.get("IG_LONG_LIVED_TOKEN", "").strip()
        self.ig_user_id = os.environ.get("IG_BUSINESS_ACCOUNT_ID", "").strip()

    # ------------------------------------------------------------------
    def _require_creds(self):
        if not self.token or not self.ig_user_id:
            raise IGError(
                "Instagram credentials nahi mile. .env mein ye chahiye:\n"
                "  IG_LONG_LIVED_TOKEN=EAAxxxx...\n"
                "  IG_BUSINESS_ACCOUNT_ID=1784xxxxxxxxx\n"
                "\nInhe kaise laayein: SETUP.md STEP 6c dekho.\n"
                "⚠️ Yaad rahe: Instagram account **Business ya Creator** hona chahiye\n"
                "   aur ek Facebook Page se linked hona chahiye. Personal account\n"
                "   API se post nahi kar sakta — ye hard block hai.")

    # ==================================================================
    def publish(self, video_id: int, *, public_url: str | None = None,
                first_comment: bool = True) -> dict:
        """
        Ek video Instagram Reel ke roop mein publish karo.

        ⚠️ Ye ABHI publish karta hai. Schedule karne ke liye scheduler (Phase 9)
        publish time pe isse call karega — kyunki container 24h mein expire hota hai.
        """
        row = self.db.get_video(video_id)
        if not row:
            raise IGError(f"Video #{video_id} DB mein nahi hai")

        # ---------- GATE 1: approval ----------
        if CONFIG.get("autonomy", "review_first") == "review_first" \
                and row["status"] not in ("approved", "published"):
            raise IGError(
                f"Video #{video_id} ka status '{row['status']}' hai, 'approved' nahi.\n"
                f"→ Dashboard se approve karo: python -m web.server")

        # ---------- GATE 2: file ----------
        path = Path(row["video_path"] or "")
        if not path.exists():
            raise IGError(f"Video file nahi mili: {path}")

        # ---------- GATE 3: validate ----------
        from pipeline.validate import validate_dir
        rep = validate_dir(path.parent)
        if not rep.ok:
            raise IGError("Validate fail — publish nahi karenge:\n  " +
                          "; ".join(f"[{i.code}] {i.msg}" for i in rep.fatals))

        dur = rep.facts.get("duration_sec", row["length_sec"] or 0)
        if dur > IG_MAX_SEC:
            raise IGError(f"Video {dur}s ka hai. Instagram API ki HARD limit "
                          f"{IG_MAX_SEC}s hai (app mein 3 min chalta hai, API mein nahi).")

        # ---------- GATE 4: quota ----------
        if self.dry_run:
            ok = self.quota.can_spend("ig_publishes", 1)
            log.info(f"DRY RUN: quota check {'pass' if ok else 'FAIL'} "
                     f"(kuch kharch nahi hua)")
        else:
            self._require_creds()
            try:
                self.quota.check_and_spend("ig_publishes", 1,
                                           reason=f"reel video #{video_id}")
            except QuotaExceeded as e:
                self.db.log_event("publish_deferred", "ig", video_id, reason=str(e))
                log.warn("IG publish aaj nahi — quota khatam. Queue mein hai.",
                         reset=self.quota.reset_in_human("ig_publishes"))
                return {"status": "queued", "reason": str(e)}

        # ---------- video ko public URL pe daalo ----------
        url = public_url or row["public_url"]
        if url:
            # purana URL 24h+ purana ho sakta hai — verify karo
            try:
                from core.hosting import verify
                verify(url)
                log.info("Pehle se hosted URL use kar rahe hain", url=url[:70])
            except Exception:  # noqa: BLE001
                log.warn("Purana public URL kaam nahi kar raha — dobara upload")
                url = None
        if not url:
            if self.dry_run:
                url = "https://example.com/DRY_RUN_placeholder.mp4"
            else:
                url = host_upload(path)
                self.db.update_video(video_id, public_url=url)

        caption = self._build_caption(row)

        if self.dry_run:
            out = {"status": "dry_run", "video_url": url, "caption": caption,
                   "media_type": "REELS", "share_to_feed": True}
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return out

        # ---------- STEP 1: container ----------
        container_id = self._create_container(url, caption)
        created_at = time.time()
        self.db.log_event("ig_container", "ig", video_id, container_id=container_id)

        # ---------- STEP 2: poll ----------
        self._poll_container(container_id, created_at)

        # ---------- STEP 3: publish ----------
        media_id = self._publish_container(container_id)

        permalink = self._permalink(media_id)
        self.db.update_video(video_id, ig_media_id=media_id, status="published",
                             published_ts=_now_iso())
        self.db.log_event("published", "ig", video_id, platform="instagram",
                          ig_media_id=media_id, permalink=permalink)
        log.ok(f"✅ Instagram pe chala gaya: {permalink or media_id}")

        if first_comment:
            self._first_comment(video_id, media_id, row)

        return {"status": "published", "ig_media_id": media_id,
                "permalink": permalink, "video_url": url}

    # ==================================================================
    def _build_caption(self, row) -> str:
        script = json.loads(row["script_json"] or "{}")
        tags = json.loads(row["hashtags"] or "[]")
        parts = [
            script.get("caption") or row["caption"] or row["topic"] or "",
            "",
            script.get("comment_bait", ""),
            "",
            " ".join(t if t.startswith("#") else f"#{t}" for t in tags),
            "",
            "🤖 AI-generated (cartoon illustration + AI narration)",
        ]
        # IG caption limit 2200 characters
        return "\n".join(p for p in parts if p is not None)[:2190]

    # ==================================================================
    def _create_container(self, video_url: str, caption: str) -> str:
        """STEP 1: media container banao."""
        params = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",   # Reel feed pe bhi dikhe = zyada reach
            "access_token": self.token,
        }
        log.info("IG container bana rahe hain...", url=video_url[:70])
        data = self._call(f"/{self.ig_user_id}/media", params, method="POST",
                          what="container create")
        cid = data.get("id")
        if not cid:
            raise IGError(f"Container id nahi mila: {json.dumps(data)[:300]}")
        log.ok(f"Container bana: {cid}")
        return cid

    # ==================================================================
    def _poll_container(self, container_id: str, created_at: float):
        """
        STEP 2: status FINISHED hone tak poll karo.

        ⚠️ Har poll ek API call hai aur 200/hour limit mein ginta hai.
        Isliye exponential-ish backoff: pehle jaldi, phir dheere.
        """
        waited = 0.0
        interval = 5.0
        attempt = 0

        while waited < POLL_MAX_WAIT:
            attempt += 1
            # container expiry ka check (24h)
            if time.time() - created_at > CONTAINER_TTL_HOURS * 3600:
                raise IGError("Container 24 ghante mein expire ho gaya. "
                              "Naya banana padega.")

            data = self._call(f"/{container_id}",
                              {"fields": "status_code,status", "access_token": self.token},
                              method="GET", what=f"poll #{attempt}", quota_bucket=None)
            code = data.get("status_code", "UNKNOWN")

            if code == "FINISHED":
                log.ok(f"Container ready ({waited:.0f}s mein, {attempt} polls)")
                return
            if code == "ERROR":
                detail = data.get("status", "")
                raise IGError(
                    f"Instagram ne video reject kar diya.\n"
                    f"Detail: {detail}\n"
                    f"→ Common wajah: format galat (H.264+AAC chahiye), "
                    f"video URL reachable nahi, ya duration 90s se zyada.\n"
                    f"→ `python -m pipeline.validate` chala kar dekho.")
            if code == "EXPIRED":
                raise IGError("Container expire ho gaya (24h). Naya banao.")

            log.debug(f"container {code}, {interval:.0f}s baad phir dekhenge",
                      waited=f"{waited:.0f}s")
            time.sleep(interval)
            waited += interval
            interval = min(interval * 1.3, 20.0)   # dheere-dheere gap badhao

        raise IGError(
            f"Container {POLL_MAX_WAIT}s mein bhi ready nahi hua ({attempt} polls).\n"
            f"→ Video bahut bada hai ya Meta ka processing slow hai.\n"
            f"→ Container abhi bhi valid ho sakta hai — thodi der baad "
            f"manually publish kar sakte ho: container_id={container_id}")

    # ==================================================================
    def _publish_container(self, container_id: str) -> str:
        """STEP 3: publish."""
        data = self._call(f"/{self.ig_user_id}/media_publish",
                          {"creation_id": container_id, "access_token": self.token},
                          method="POST", what="media_publish")
        mid = data.get("id")
        if not mid:
            raise IGError(f"Publish response mein media id nahi: {json.dumps(data)[:300]}")
        return mid

    # ==================================================================
    def _permalink(self, media_id: str) -> str | None:
        try:
            data = self._call(f"/{media_id}",
                              {"fields": "permalink", "access_token": self.token},
                              method="GET", what="permalink", quota_bucket=None)
            return data.get("permalink")
        except Exception:  # noqa: BLE001
            return None

    # ==================================================================
    def _first_comment(self, video_id: int, media_id: str, row):
        """
        Section 8: comment seeding — apna hi pehla comment jo SPECIFIC sawaal poochhe.
        Chhote comments (<5 shabd) algorithm ginta hi nahi, isliye lamba jawab invite karo.
        """
        script = json.loads(row["script_json"] or "{}")
        text = (script.get("comment_bait") or "").strip()
        if not text:
            return
        try:
            data = self._call(f"/{media_id}/comments",
                              {"message": text, "access_token": self.token},
                              method="POST", what="first comment")
            log.ok("First comment post ho gaya", text=text[:60])
            self.db.log_event("first_comment", "ig", video_id, comment_id=data.get("id"))
        except Exception as e:  # noqa: BLE001
            log.warn(f"First comment fail: {str(e)[:160]}",
                     hint="'instagram_manage_comments' permission approved hai?")

    # ==================================================================
    def _call(self, endpoint: str, params: dict, *, method: str = "GET",
              what: str = "IG call", quota_bucket: str | None = "ig_calls_hour") -> dict:
        """
        Graph API call + rate limit tracking + Hinglish errors.
        Har call (polling bhi) ig_calls_hour budget mein ginti hai.
        """
        if quota_bucket:
            try:
                self.quota.check_and_spend(quota_bucket, 1, reason=what)
            except QuotaExceeded as e:
                raise IGError(f"IG hourly call limit hit: {e}") from e
        else:
            # polling bhi ginna hai, par block nahi karna (beech mein ruk gaye to
            # container waste ho jayega). Isliye sirf record karo.
            self.quota.spend("ig_calls_hour", 1, reason=what)

        url = f"{GRAPH}/{API_VERSION}{endpoint}"
        body = urllib.parse.urlencode(params).encode()

        def _do():
            if method == "GET":
                req = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}")
            else:
                req = urllib.request.Request(url, data=body, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    payload = json.loads(r.read() or b"{}")
                    self.quota.reconcile_from_headers(dict(r.headers))
                    return payload
            except urllib.error.HTTPError as e:
                raw = e.read()
                self.quota.reconcile_from_headers(dict(e.headers or {}))
                raise _ig_error(e.code, raw) from e

        return retry(_do, tries=3, base_delay=4.0, log=log, what=what)

    # ==================================================================
    def account_info(self) -> dict:
        """Account check — publish se pehle ye chala kar confirm karo."""
        self._require_creds()
        data = self._call(f"/{self.ig_user_id}",
                          {"fields": "id,username,name,followers_count,media_count,"
                                     "account_type",
                           "access_token": self.token}, what="account info")
        acct = data.get("account_type")
        if acct and acct not in ("BUSINESS", "MEDIA_CREATOR", "CREATOR"):
            log.error(f"Account type '{acct}' hai — API se publish nahi kar paoge. "
                      f"Instagram app mein Business/Creator pe switch karo.")
        return data

    def publishing_limit(self) -> dict:
        """
        Meta ka APNA counter — kitne posts 24h window mein ho chuke.
        Ye hamare DB counter se zyada bharosemand hai (Section 2: headers padho).
        """
        self._require_creds()
        data = self._call(f"/{self.ig_user_id}/content_publishing_limit",
                          {"fields": "config,quota_usage", "access_token": self.token},
                          what="publishing limit")
        items = data.get("data") or [{}]
        info = items[0]
        used = info.get("quota_usage", 0)
        cap = (info.get("config") or {}).get("quota_total", 100)

        # ---- reconcile: Meta ka hisaab hamare DB se milao ----
        ours = self.quota.used("ig_publishes")
        if used > ours:
            gap = used - ours
            self.quota.spend("ig_publishes", gap,
                             reason=f"reconcile: Meta says {used}")
            log.warn(f"Meta ke hisaab se {used} posts ho chuke, hamare DB mein {ours} the "
                     f"— {gap} adjust kar diya")
        return {"used": used, "cap": cap, "our_count": ours,
                "our_cap": self.quota.budgets["ig_publishes"]["limit"]}


# =====================================================================
def _ig_error(code: int, raw: bytes) -> IGError:
    """Meta ka error -> Hinglish matlab. Ye codes maine docs se verify kiye hain."""
    try:
        body = json.loads(raw)
        err = body.get("error", {})
        msg = err.get("message", "")
        etype = err.get("type", "")
        ecode = err.get("code")
        sub = err.get("error_subcode")
    except Exception:  # noqa: BLE001
        msg, etype, ecode, sub = raw.decode("utf-8", "replace")[:300], "", None, None

    hints = {
        24: "FORMAT REJECT. Video MP4 + H.264 + AAC hona chahiye. "
            "`python -m pipeline.validate` chalao — wo ye pehle hi pakad leta hai.",
        190: "Access token invalid ya expire. Naya long-lived token banao "
             "(SETUP.md STEP 6c). Long-lived token 60 din chalta hai.",
        200: "Permission nahi hai. 'instagram_content_publish' App Review se "
             "approve hua hai? Ya tum test user ho?",
        4: "Application-level rate limit. Ek ghanta ruko.",
        17: "User-level rate limit. Ruk kar retry.",
        9: "Publishing rate limit (100 posts/24h). Kal try karo.",
        100: "Parameter galat hai. video_url publicly reachable hai? "
             "HEAD request se check karo.",
        2207001: "Meta ke server pe upload fail hua. 1-2 baar retry karo, "
                 "phir naya container banao.",
        2207026: "Video format supported nahi. Duration 90s se kam, "
                 "H.264 + AAC, 9:16 hona chahiye.",
        2207042: "Publishing rate limit exceeded. content_publishing_limit check karo.",
        2207050: "Video ka aspect ratio galat hai. 9:16 chahiye.",
        2207052: "Video URL fetch nahi ho paaya. Public hai? HTML page to nahi de raha?",
    }
    hint = hints.get(sub) or hints.get(ecode) or ""
    if code == 400 and not hint:
        hint = ("Aksar iska matlab: container abhi FINISHED nahi hua, ya "
                "video_url reachable nahi hai.")

    return IGError(f"Instagram API {code} [{etype} code={ecode} sub={sub}] {msg}"
                   + (f"\n→ Matlab: {hint}" if hint else ""))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# =====================================================================
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Instagram Reel publish karo")
    ap.add_argument("video_id", type=int, nargs="?")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--info", action="store_true", help="account info")
    ap.add_argument("--limit", action="store_true", help="Meta ka publishing counter")
    ap.add_argument("--host-only", action="store_true", help="sirf public URL banao")
    a = ap.parse_args()

    with DB() as db:
        ig = InstagramPublisher(db, dry_run=a.dry_run)
        if a.info:
            print(json.dumps(ig.account_info(), indent=2, ensure_ascii=False))
        elif a.limit:
            print(json.dumps(ig.publishing_limit(), indent=2, ensure_ascii=False))
        elif a.host_only and a.video_id:
            row = db.get_video(a.video_id)
            url = host_upload(row["video_path"])
            db.update_video(a.video_id, public_url=url)
            print(url)
        elif a.video_id:
            print(json.dumps(ig.publish(a.video_id), indent=2, ensure_ascii=False))
        else:
            ready = db.videos_by_status("approved")
            print("Approved videos:" if ready else "Koi approved video nahi.")
            for r in ready:
                print(f"  #{r['id']}  {r['title']}")
            print("\nPublish: python -m agents.ig_publisher <id> --dry-run")
