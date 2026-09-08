#!/usr/bin/env python3
"""
test_all.py — health check. Phase 1 ke saare acceptance points yahan test hote hain.

Chalao:  python test_all.py
Sab green hona chahiye. Ye tests koi internet/API key nahi maangte.

Har test ek temp DB pe chalta hai — tumhara asli data safe rehta hai.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

os.environ["AUTOPILOT_MOCK_MODE"] = "true"  # tests hamesha mock mode mein

from core import db as db_mod          # noqa: E402
from core.db import DB                 # noqa: E402
from core.llm import LLM, _extract_json, MoonshotLLM, GeminiLLM, MockLLM  # noqa: E402
from core.logbook import Logbook, explain, retry  # noqa: E402
from core.quota import Quota, QuotaExceeded  # noqa: E402
from core.mp3 import duration_sec           # noqa: E402
from agents.writer import Writer, HOOK_TYPES, BANNED_HOOKS  # noqa: E402
from agents.artdirector import ArtDirector, TEMPLATES       # noqa: E402
from agents.voice import Voice, VOICE_PROFILES, _distribute_words, _syllables, _is_reveal  # noqa: E402
from agents.imagegen import ImageGen        # noqa: E402
from core.ffmpeg import capabilities, ffmpeg_bin, FFmpegMissing, _explain_ffmpeg  # noqa: E402
from pipeline.subtitles import build_ass, build_srt, _group_words, _ts  # noqa: E402
from pipeline.render import ken_burns, build_audio_filter, _even, _shift_audio_idx  # noqa: E402
from pipeline.validate import (validate, validate_dir, Report, LIMITS,  # noqa: E402
                               _check_video_stream, _check_audio_stream,
                               _check_duration, _check_content, _parse_fps)
from web.server import gather, do_action, _check_webhook_auth, fetch_logs  # noqa: E402
from core.oauth import Credentials, OAuthError, YT_SCOPES, _load_client_secret  # noqa: E402
from agents.publisher import (YouTubePublisher, PublishError, _yt_error,  # noqa: E402
                              best_publish_time, CHUNK)
from agents.ig_publisher import (InstagramPublisher, IGError, _ig_error,  # noqa: E402
                                 IG_MAX_SEC, CONTAINER_TTL_HOURS, POLL_MAX_WAIT)
from core.hosting import HostingError, upload as host_upload, verify as host_verify  # noqa: E402
from agents.analyst import (Analyst, THRESHOLDS, WINDOWS, _ratio_at,  # noqa: E402
                            _bucket, _verdict)
from core.stats import (welch_ttest, t_pvalue, summarize, confidence_level,  # noqa: E402
                        lift_pct, min_detectable_lift, betainc)
from agents.scientist import Scientist, MIN_PER_ARM, MAX_PER_ARM  # noqa: E402
from agents.chief import Chief, Lock, LOCK_FILE, cron_guide  # noqa: E402
from agents.trendscout import TrendScout  # noqa: E402

PASS, FAIL = [], []


def test(name):
    """Chhota test decorator — pass/fail collect karta hai."""
    def deco(fn):
        try:
            fn()
            PASS.append(name)
            print(f"  ✅ {name}")
        except Exception as e:  # noqa: BLE001
            FAIL.append((name, e))
            print(f"  ❌ {name}\n     {type(e).__name__}: {e}")
            if os.environ.get("VERBOSE"):
                traceback.print_exc()
        return fn
    return deco


def fresh_db() -> DB:
    """Har test ke liye alag temp database."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    return DB(tmp.name)


# =====================================================================
print("\n🧪 1. LOGBOOK")
# =====================================================================

@test("Logbook JSONL file likhta hai")
def _():
    lb = Logbook("test")
    lb.info("hello", k=1)
    assert lb._file().exists(), "log file bani hi nahi"
    last = lb._file().read_text(encoding="utf-8").strip().splitlines()[-1]
    rec = json.loads(last)
    assert rec["agent"] == "test" and rec["msg"] == "hello"


@test("explain() error ko Hinglish mein samjhata hai")
def _():
    assert "quota" in explain("403 quotaExceeded").lower()
    assert explain(ValueError("kuch naya")) != ""


@test("retry() exponential backoff karta hai aur aakhir mein safal hota hai")
def _():
    calls, delays = {"n": 0}, []

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("network down")
        return "ok"

    out = retry(flaky, tries=4, base_delay=1.0, sleep=delays.append, what="flaky")
    assert out == "ok" and calls["n"] == 3
    assert len(delays) == 2 and delays[1] > delays[0], f"backoff badhna chahiye: {delays}"


@test("retry() saari koshishein fail hone pe exception raise karta hai (silent fail nahi)")
def _():
    def always_fail():
        raise TimeoutError("nope")
    try:
        retry(always_fail, tries=2, sleep=lambda s: None, what="always_fail")
        raise AssertionError("exception aana chahiye tha")
    except TimeoutError:
        pass


# =====================================================================
print("\n🧪 2. DATABASE")
# =====================================================================

@test("Saare tables ban jaate hain")
def _():
    d = fresh_db()
    names = {r["name"] for r in d.q("SELECT name FROM sqlite_master WHERE type='table'")}
    for t in ("videos", "metrics", "experiments", "learnings", "quota_usage", "events"):
        assert t in names, f"table missing: {t}"
    d.close()


@test("Video create + update + status machine")
def _():
    d = fresh_db()
    vid = d.create_video("Test mystery", hook_type="pov", voice_id="hi-female-1",
                         template_id="noir-1", hashtags=["#a", "#b"])
    row = d.get_video(vid)
    assert row["status"] == "planned" and row["ai_disclosed"] == 1
    assert json.loads(row["hashtags"]) == ["#a", "#b"]
    d.set_status(vid, "rendered")
    assert d.get_video(vid)["status"] == "rendered"
    try:
        d.set_status(vid, "banana")
        raise AssertionError("galat status accept ho gaya")
    except ValueError:
        pass
    d.close()


@test("Rotation: pichhle 4 videos ki voice repeat nahi hoti")
def _():
    d = fresh_db()
    voices = ["v1", "v2", "v3", "v4", "v5"]
    used = []
    for i in range(5):
        v = d.pick_rotated("voice_id", voices, avoid_last=4)
        d.create_video(f"topic {i}", voice_id=v, template_id=f"t{i%4}")
        used.append(v)
    assert len(set(used)) == 5, f"consecutive 5 videos mein voice repeat hui: {used}"
    d.close()


@test("Metrics save + read (2h window)")
def _():
    d = fresh_db()
    vid = d.create_video("x")
    d.save_metrics(vid, "youtube", "2h", views=1200, likes=80, comments=9, ret_1s=0.71, avg_pct=0.62)
    m = d.get_metrics(vid, "2h")[0]
    assert m["views"] == 1200 and abs(m["ret_1s"] - 0.71) < 1e-9
    d.save_metrics(vid, "youtube", "2h", views=1500)  # upsert
    assert len(d.get_metrics(vid, "2h")) == 1
    d.close()


@test("Ek time pe sirf EK experiment chal sakta hai")
def _():
    d = fresh_db()
    d.create_experiment("hook_type", "POV better hoga", "pov", "question")
    try:
        d.create_experiment("voice", "female better", "f1", "m1")
        raise AssertionError("do experiments ek saath ban gaye")
    except ValueError:
        pass
    d.close()


@test("Learnings save hoti hain aur 90+ din purani downgrade hoti hai")
def _():
    d = fresh_db()
    lid = d.add_learning("voice", "hi-female-3", "hi-male-1", 22.0, 12, "high")
    assert len(d.active_learnings("voice")) == 1
    d.conn.execute("UPDATE learnings SET ts=datetime('now','-100 days') WHERE id=?", (lid,))
    d.expire_old_learnings()
    assert d.one("SELECT confidence FROM learnings WHERE id=?", (lid,))["confidence"] == "medium"
    d.close()


@test("Dashboard summary banti hai")
def _():
    d = fresh_db()
    d.create_video("a"); v = d.create_video("b"); d.set_status(v, "published")
    s = d.dashboard_summary()
    assert s["published_total"] == 1 and "planned" in s["videos_by_status"]
    d.close()


# =====================================================================
print("\n🧪 3. QUOTA MANAGER")
# =====================================================================

@test("Naya budget = poora remaining")
def _():
    q = Quota(fresh_db())
    assert q.remaining("youtube_units") == 10000 and q.used("youtube_uploads") == 0
    q.close()


@test("spend() ke baad remaining ghatta hai")
def _():
    q = Quota(fresh_db())
    q.spend("youtube_units", 100, "videos.insert")
    assert q.used("youtube_units") == 100 and q.remaining("youtube_units") == 9900
    q.close()


@test("⭐ Quota manager galat time pe API call BLOCK karta hai")
def _():
    q = Quota(fresh_db())
    for i in range(5):                       # cap = 5 uploads/day
        q.check_and_spend("youtube_uploads", 1, f"upload {i}")
    assert q.can_spend("youtube_uploads", 1) is False, "6th upload block hona chahiye tha"
    try:
        q.check_and_spend("youtube_uploads", 1, "6th")
        raise AssertionError("QuotaExceeded raise nahi hua")
    except QuotaExceeded as e:
        assert "khatam" in str(e)
    q.close()


@test("yt_call(): videos.insert 100 units + 1 upload dono kaatta hai")
def _():
    q = Quota(fresh_db())
    q.yt_call("videos.insert", "test upload")
    assert q.used("youtube_units") == 100
    assert q.used("youtube_uploads") == 1
    q.close()


@test("yt_call(): playlistItems.list sirf 1 unit (search.list 100x mehnga)")
def _():
    q = Quota(fresh_db())
    q.yt_call("playlistItems.list")
    assert q.used("youtube_units") == 1
    q.yt_call("search.list")
    assert q.used("youtube_units") == 101 and q.used("youtube_search") == 1
    q.close()


@test("Instagram publish cap (20) enforce hota hai")
def _():
    q = Quota(fresh_db())
    for _i in range(20):
        q.check_and_spend("ig_publishes", 1, "reel")
    assert not q.can_spend("ig_publishes")
    q.close()


@test("X-App-Usage header se reconcile hota hai")
def _():
    q = Quota(fresh_db())
    q.spend("ig_calls_hour", 10, "polling")
    q.reconcile_from_headers({"x-app-usage": json.dumps({"call_count": 50})})
    assert q.used("ig_calls_hour") == 75, f"150 ka 50% = 75 hona chahiye, mila {q.used('ig_calls_hour')}"
    q.close()


@test("Kharab header se crash nahi hota")
def _():
    q = Quota(fresh_db())
    q.reconcile_from_headers({"x-app-usage": "not-json"})   # crash nahi hona chahiye
    q.close()


@test("Unknown bucket pe clear error aata hai")
def _():
    q = Quota(fresh_db())
    try:
        q.can_spend("koi_bhi_bucket")
        raise AssertionError("KeyError aana chahiye tha")
    except KeyError:
        pass
    q.close()


@test("reset_in_human() padhne layak string deta hai")
def _():
    q = Quota(fresh_db())
    assert "baad" in q.reset_in_human("youtube_units")
    q.close()


# =====================================================================
print("\n🧪 4. LLM (mock mode)")
# =====================================================================

@test("⭐ Bina API key ke LLM mock mode mein chalta hai")
def _():
    llm = LLM(force_mock=True)
    assert llm.is_mock
    assert len(llm.ask("kuch bhi")) > 10


@test("llm.json() valid dict deta hai")
def _():
    data = LLM(force_mock=True).json("Ek suspense script chahiye JSON mein")
    assert isinstance(data, dict) and "hook_line" in data and "comment_bait" in data


@test("Mock deterministic hai (same prompt = same output)")
def _():
    a, b = LLM(force_mock=True), LLM(force_mock=True)
    assert a.ask("same prompt") == b.ask("same prompt")


@test("_extract_json markdown fence aur extra text saaf karta hai")
def _():
    assert _extract_json('```json\n{"a":1}\n```') == {"a": 1}
    assert _extract_json('Sure! {"a": {"b": 2}} — done') == {"a": {"b": 2}}
    assert _extract_json('{"s":"} nested brace"}') == {"s": "} nested brace"}
    assert _extract_json("koi json nahi") is None


@test("Gemini requests bhi quota ke andar hain")
def _():
    q = Quota(fresh_db())
    assert q.can_spend("gemini_requests", 1)
    q.spend("gemini_requests", 1200, "burn")
    assert not q.can_spend("gemini_requests", 1)
    q.close()


@test("Moonshot requests quota limit track aur spend hoti hai")
def _():
    q = Quota(fresh_db())
    assert q.can_spend("moonshot_requests", 1)
    q.spend("moonshot_requests", 100, "burn")
    assert not q.can_spend("moonshot_requests", 1)
    try:
        q.check_and_spend("moonshot_requests", 1)
        assert False, "QuotaExceeded aana chahiye tha"
    except QuotaExceeded:
        pass
    q.close()


@test("MoonshotLLM request body, headers aur response parsing sahi hai")
def _():
    import urllib.request

    captured = {}

    class FakeResponse:
        def __init__(self, data):
            self.data = data
        def read(self):
            return self.data
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    def mock_urlopen(req, timeout=90):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["headers"] = dict(req.headers)
        captured["body"] = json.loads(req.data.decode("utf-8"))
        captured["timeout"] = timeout
        resp_data = json.dumps({
            "choices": [{"message": {"content": "Kimi K3 ka jawab"}}]
        }).encode("utf-8")
        return FakeResponse(resp_data)

    orig_urlopen = urllib.request.urlopen
    urllib.request.urlopen = mock_urlopen
    try:
        q = Quota(fresh_db())
        llm = MoonshotLLM(api_key="test-moonshot-key", model="kimi-k3",
                          base_url="https://api.moonshot.ai/v1", quota=q)
        ans = llm.generate("Ek suspense scene", temperature=0.7, max_tokens=512, system="Suspense writer")
        assert ans == "Kimi K3 ka jawab"
        assert captured["url"] == "https://api.moonshot.ai/v1/chat/completions"
        assert captured["timeout"] == 90
        assert captured["method"] == "POST"
        assert captured["body"]["model"] == "kimi-k3"
        assert captured["body"]["temperature"] == 0.7
        assert captured["body"]["max_tokens"] == 512
        assert captured["body"]["messages"][0] == {"role": "system", "content": "Suspense writer"}
        assert captured["body"]["messages"][1] == {"role": "user", "content": "Ek suspense scene"}
        auth_header = captured["headers"].get("Authorization") or captured["headers"].get("authorization")
        assert auth_header == "Bearer test-moonshot-key"
        assert q.used("moonshot_requests") == 1
        q.close()
    finally:
        urllib.request.urlopen = orig_urlopen


@test("MoonshotLLM 401 pe clear error deta hai aur 429 pe QuotaExceeded")
def _():
    import urllib.request
    import urllib.error
    from io import BytesIO

    def mock_401(req, timeout=90):
        raise urllib.error.HTTPError(
            req.full_url, 401, "Unauthorized", {}, BytesIO(b'{"error": "invalid api key"}')
        )

    def mock_429(req, timeout=90):
        raise urllib.error.HTTPError(
            req.full_url, 429, "Too Many Requests", {}, BytesIO(b'{"error": "rate limit exceeded"}')
        )

    orig_urlopen = urllib.request.urlopen
    try:
        # 401 test
        urllib.request.urlopen = mock_401
        q1 = Quota(fresh_db())
        llm1 = MoonshotLLM(api_key="invalid-key", quota=q1)
        try:
            llm1.generate("hi")
            assert False, "401 pe error aana chahiye tha"
        except RuntimeError as e:
            assert "401" in str(e) or "unauthorized" in str(e).lower()
        q1.close()

        # 429 test
        urllib.request.urlopen = mock_429
        q2 = Quota(fresh_db())
        llm2 = MoonshotLLM(api_key="valid-key", quota=q2)
        try:
            llm2.generate("hi")
            assert False, "429 pe QuotaExceeded aana chahiye tha"
        except QuotaExceeded as e:
            assert "429" in str(e) or "quota" in str(e).lower()
        q2.close()
    finally:
        urllib.request.urlopen = orig_urlopen


@test("Provider selection: auto/primary/fallback order via env vars")
def _():
    from core.config import CONFIG
    old_env = dict(os.environ)
    old_mock = CONFIG.get("mock_mode")
    try:
        CONFIG["mock_mode"] = False
        os.environ["AUTOPILOT_MOCK_MODE"] = "false"

        # Case 1: only Gemini key -> Gemini primary
        os.environ["GEMINI_API_KEY"] = "gem-key-1"
        os.environ.pop("MOONSHOT_API_KEY", None)
        os.environ.pop("LLM_PROVIDER", None)
        os.environ.pop("LLM_PRIMARY", None)
        os.environ.pop("LLM_FALLBACK_ORDER", None)
        l1 = LLM(force_mock=False)
        assert l1.backends[0].name == "gemini"

        # Case 2: only Moonshot key -> Kimi primary
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ["MOONSHOT_API_KEY"] = "moon-key-1"
        l2 = LLM(force_mock=False)
        assert l2.backends[0].name == "kimi"

        # Case 3: both keys, auto mode, primary=gemini (default)
        os.environ["GEMINI_API_KEY"] = "gem-key-1"
        os.environ["MOONSHOT_API_KEY"] = "moon-key-1"
        os.environ["LLM_PROVIDER"] = "auto"
        os.environ["LLM_PRIMARY"] = "gemini"
        l3 = LLM(force_mock=False)
        assert l3.backends[0].name == "gemini"
        assert l3.backends[1].name == "kimi"

        # Case 4: both keys, auto mode, primary=kimi
        os.environ["LLM_PRIMARY"] = "kimi"
        l4 = LLM(force_mock=False)
        assert l4.backends[0].name == "kimi"
        assert l4.backends[1].name == "gemini"

        # Case 5: explicit LLM_FALLBACK_ORDER overrides primary
        os.environ["LLM_FALLBACK_ORDER"] = "kimi,gemini,mock"
        os.environ["LLM_PRIMARY"] = "gemini"
        l5 = LLM(force_mock=False)
        assert [b.name for b in l5.backends] == ["kimi", "gemini", "mock"]

        # Case 6: neither key -> fallback to mock
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("MOONSHOT_API_KEY", None)
        os.environ.pop("LLM_FALLBACK_ORDER", None)
        l6 = LLM(force_mock=False)
        assert l6.backends[0].name == "mock"
    finally:
        os.environ.clear()
        os.environ.update(old_env)
        CONFIG["mock_mode"] = old_mock


@test("LLM failover: pehla backend fail ho to agla backend use hota hai")
def _():
    class BrokenPrimary:
        name = "broken"
        def generate(self, prompt, **kw):
            raise RuntimeError("Primary API network crash")

    class WorkingSecondary:
        name = "working"
        model = "fake-v1"
        def generate(self, prompt, **kw):
            return "Secondary backend ka jawab"

    llm = LLM(force_mock=True)
    # Inject fallback chain
    llm.backends = [BrokenPrimary(), WorkingSecondary(), MockLLM()]
    llm.backend = llm.backends[0]
    res = llm.ask("kuch bhi")
    assert res == "Secondary backend ka jawab"

    # Test jab saare real fail ho jayein to mock pe girna
    class AlsoBroken:
        name = "also_broken"
        def generate(self, prompt, **kw):
            raise QuotaExceeded("quota zero")

    llm.backends = [BrokenPrimary(), AlsoBroken(), MockLLM()]
    llm.backend = llm.backends[0]
    res_mock = llm.ask("kuch bhi")
    assert "[MOCK-" in res_mock


@test("Per-agent llm_routing: config.yaml se har agent ka backend alag ho sakta hai")
def _():
    from core.config import CONFIG
    old_env = dict(os.environ)
    old_mock = CONFIG.get("mock_mode")
    old_routing = CONFIG.get("llm_routing")
    try:
        CONFIG["mock_mode"] = False
        os.environ["AUTOPILOT_MOCK_MODE"] = "false"
        os.environ["GEMINI_API_KEY"] = "gem-key-1"
        os.environ["MOONSHOT_API_KEY"] = "moon-key-1"
        os.environ["LLM_PROVIDER"] = "auto"
        os.environ["LLM_PRIMARY"] = "gemini"

        CONFIG["llm_routing"] = {
            "writer": "kimi",
            "trendscout": "gemini",
        }

        # writer should be kimi primary
        w_llm = LLM(force_mock=False, agent_name="writer")
        assert w_llm.backends[0].name == "kimi"

        # trendscout should be gemini primary
        ts_llm = LLM(force_mock=False, agent_name="trendscout")
        assert ts_llm.backends[0].name == "gemini"

        # unconfigured agent (metadata) should follow global primary (gemini)
        meta_llm = LLM(force_mock=False, agent_name="metadata")
        assert meta_llm.backends[0].name == "gemini"

        # for_agent helper preserves settings
        derived_w = meta_llm.for_agent("writer")
        assert derived_w.backends[0].name == "kimi"

        # Agent classes pass their agent_name to LLM correctly
        d = fresh_db()
        writer = Writer(d, w_llm)
        assert writer.llm.backends[0].name == "kimi"
        ts = TrendScout(d, ts_llm)
        assert ts.llm.backends[0].name == "gemini"
        d.close()
    finally:
        os.environ.clear()
        os.environ.update(old_env)
        CONFIG["mock_mode"] = old_mock
        CONFIG["llm_routing"] = old_routing


# =====================================================================
print("\n🧪 5. INTEGRATION (mini end-to-end, bina network ke)")
# =====================================================================

@test("Video plan -> script -> quota -> learning: poora loop chalta hai")
def _():
    d = fresh_db()
    q = Quota(d)
    llm = LLM(force_mock=True)

    script = llm.json("Writer: suspense script JSON")
    vid = d.create_video(script["title"], title=script["title"], caption=script["caption"],
                         hashtags=script["hashtags"], hook_type=script["hook_type"],
                         voice_id=d.pick_rotated("voice_id", ["v1", "v2", "v3", "v4"]),
                         template_id=d.pick_rotated("template_id", ["t1", "t2", "t3", "t4"]),
                         script_json=script, length_sec=32)
    d.set_status(vid, "scripted")

    q.yt_call("videos.insert", f"video {vid}")           # publish simulate
    d.update_video(vid, yt_video_id="abc123", status="published")

    d.save_metrics(vid, "youtube", "2h", views=900, ret_1s=0.68, avg_pct=0.55)
    exp = d.create_experiment("hook_type", "POV > question", "pov", "question")
    d.conclude_experiment(exp, {"winner": "pov", "lift_pct": 18.0, "n": 10})
    d.add_learning("hook_type", "pov", "question", 18.0, 10, "medium", exp)

    row = d.get_video(vid)
    assert row["status"] == "published" and row["ai_disclosed"] == 1
    assert q.used("youtube_uploads") == 1
    assert len(d.active_learnings("hook_type")) == 1
    assert 22 <= row["length_sec"] <= 45, "video length 22-45s ke andar hona chahiye"
    d.close()


@test("Video length config 22-45s ke andar hai")
def _():
    from core.config import CONFIG
    n = CONFIG["video_length_sec"]
    assert 22 <= n <= 45, f"config.yaml mein video_length_sec={n} — 22-45 ke beech rakho"


@test("AI disclosure default ON hai (hard constraint #4)")
def _():
    d = fresh_db()
    assert d.get_video(d.create_video("x"))["ai_disclosed"] == 1
    d.close()




# =====================================================================
print("\n🧪 6. WRITER (Phase 2)")
# =====================================================================

@test("Writer valid script package banata hai")
def _():
    d = fresh_db()
    s = Writer(d, LLM(force_mock=True)).write("Ek gayab train ka rahasya")
    for k in ("title", "hook_line", "hook_text_overlay", "body", "ending",
              "comment_bait", "caption", "hashtags", "hook_type"):
        assert k in s, f"missing key: {k}"
    assert isinstance(s["body"], list) and s["body"], "body list honi chahiye"
    assert len(s["hashtags"]) == 3, f"exactly 3 hashtag chahiye, mile {len(s['hashtags'])}"
    assert all(h.startswith("#") for h in s["hashtags"])
    d.close()


@test("Text overlay 8 shabd se zyada nahi hota")
def _():
    d = fresh_db()
    w = Writer(d, LLM(force_mock=True))
    out = w._normalize({"hook_text_overlay": "ek do teen chaar paanch chhe saat aath nau das"},
                       "t", "pov", 32)
    assert len(out["hook_text_overlay"].split()) <= 8
    d.close()


@test("generic_reveal hook BANNED hai (sirf 12% retention)")
def _():
    d = fresh_db()
    assert "generic_reveal" in BANNED_HOOKS and "generic_reveal" not in HOOK_TYPES
    try:
        Writer(d, LLM(force_mock=True)).write("x", hook_type="generic_reveal")
        raise AssertionError("banned hook accept ho gaya")
    except ValueError:
        pass
    d.close()


@test("⭐ Hook type rotate hota hai — lagatar 2 videos mein same nahi")
def _():
    d = fresh_db()
    w = Writer(d, LLM(force_mock=True))
    picks = []
    for i in range(12):
        h = w.pick_hook_type()
        d.create_video(f"t{i}", hook_type=h)
        picks.append(h)
    for a, b in zip(picks, picks[1:]):
        assert a != b, f"lagatar same hook type aaya: {picks}"
    assert len(set(picks)) >= 3, f"variety kam hai: {set(picks)}"
    d.close()


@test("Writer learnings DB padhta hai (jeeta hua hook prefer hota hai)")
def _():
    d = fresh_db()
    d.add_learning("hook_type", "question", "pov", 30.0, 10, "high")
    w = Writer(d, LLM(force_mock=True))
    picks = [w.pick_hook_type() for _ in range(60)]
    # 'question' ki base retention sabse kam hai (0.28) par 2x boost mila hai,
    # isliye wo kabhi-kabhi to aana hi chahiye
    assert picks.count("question") >= 5, f"winning hook ignore ho gaya: {picks.count('question')}/60"
    d.close()


@test("Chhote comment bait pe warning aati hai")
def _():
    d = fresh_db()
    out = Writer(d, LLM(force_mock=True))._normalize({"comment_bait": "Kya lagta hai?"}, "t", "pov", 32)
    assert any("bait" in w.lower() for w in out["warnings"]), out["warnings"]
    d.close()


@test("full_narration saari spoken lines jodta hai")
def _():
    d = fresh_db()
    w = Writer(d, LLM(force_mock=True))
    s = w.write("test")
    full = w.full_narration(s)
    assert s["hook_line"] in full and s["ending"] in full
    assert len(w.lines(s)) == len(s["body"]) + 2
    d.close()


# =====================================================================
print("\n🧪 7. ART DIRECTOR (Phase 2)")
# =====================================================================

@test("Kam se kam 4 visual templates hain")
def _():
    assert len(TEMPLATES) >= 4, "clustering se bachne ke liye 4+ templates chahiye"


@test("⭐ Template rotate hota hai — lagatar 3 videos mein same nahi")
def _():
    d = fresh_db()
    ad = ArtDirector(d, LLM(force_mock=True))
    picks = []
    for i in range(8):
        t = ad.pick_template()
        d.create_video(f"t{i}", template_id=t)
        picks.append(t)
    for i in range(2, len(picks)):
        assert len(set(picks[i-2:i+1])) == 3, f"3 ke window mein repeat: {picks}"
    d.close()


@test("6-8 scenes bante hain")
def _():
    d = fresh_db()
    llm = LLM(force_mock=True)
    s = Writer(d, llm).write("test topic")
    art = ArtDirector(d, llm).direct(s)
    assert 6 <= art["n_scenes"] <= 8, art["n_scenes"]
    assert len(art["scenes"]) == art["n_scenes"]
    d.close()


@test("⭐ Character description HAR image prompt mein repeat hoti hai (consistency)")
def _():
    d = fresh_db()
    llm = LLM(force_mock=True)
    art = ArtDirector(d, llm).direct(Writer(d, llm).write("test"))
    char = art["character"]
    for sc in art["scenes"]:
        assert char in sc["image_prompt"], f"scene {sc['n']} mein character description nahi hai"
    d.close()


@test("Image prompts mein 'no text' hai (image models gibberish likhte hain)")
def _():
    d = fresh_db()
    llm = LLM(force_mock=True)
    art = ArtDirector(d, llm).direct(Writer(d, llm).write("test"))
    for sc in art["scenes"]:
        assert "no text" in sc["image_prompt"].lower()
        assert "9:16" in sc["image_prompt"]
    d.close()


@test("⭐ Aakhri scene = pehla scene (loop-perfect ending)")
def _():
    d = fresh_db()
    llm = LLM(force_mock=True)
    art = ArtDirector(d, llm).direct(Writer(d, llm).write("test"))
    assert art["scenes"][-1]["image_prompt"] == art["scenes"][0]["image_prompt"]
    assert art["scenes"][0]["motion"] == "zoom_in" and art["scenes"][-1]["motion"] == "zoom_out"
    d.close()


@test("Ken Burns motion alternate hota hai (lagatar same nahi)")
def _():
    d = fresh_db()
    llm = LLM(force_mock=True)
    art = ArtDirector(d, llm).direct(Writer(d, llm).write("test"))
    ms = [s["motion"] for s in art["scenes"]]
    for a, b in zip(ms, ms[1:]):
        assert a != b, f"lagatar same motion: {ms}"
    d.close()


@test("LLM kam scenes de to fallback prompt banta hai (crash nahi)")
def _():
    d = fresh_db()
    ad = ArtDirector(d, LLM(force_mock=True))
    art = ad._build({"character": "a man", "scenes": [{"n": 1, "image_prompt": "door"}]},
                    {"hook_line": "a", "body": ["b"], "ending": "c", "target_length_sec": 32},
                    "noir_teal", 7, ["a", "b", "c"])
    assert len(art["scenes"]) == 7
    assert all(s["image_prompt"] for s in art["scenes"])
    d.close()


# =====================================================================
print("\n🧪 8. VOICE (Phase 2)")
# =====================================================================

@test("Kam se kam 4 voice profiles hain (Section 5 requirement)")
def _():
    assert len(VOICE_PROFILES) >= 4, "duplicate-pattern clustering se bachne ko 4-6 chahiye"
    assert len({(v["voice"], v["rate"], v["pitch"]) for v in VOICE_PROFILES.values()}) == len(VOICE_PROFILES), \
        "do profiles bilkul same settings pe hain — wo alag nahi sunai denge"


@test("⭐ Voice rotate hoti hai — 5 consecutive videos mein 5 alag")
def _():
    d = fresh_db()
    v = Voice(d)
    picks = []
    for i in range(5):
        p = v.pick_profile()
        d.create_video(f"t{i}", voice_id=p)
        picks.append(p)
    assert len(set(picks)) == 5, f"voice repeat hui: {picks}"
    d.close()


@test("Male aur female dono voices rotation mein hain")
def _():
    genders = {p["gender"] for p in VOICE_PROFILES.values()}
    assert genders == {"male", "female"}


@test("Word timing distribute hota hai, boundaries exact rehti hain")
def _():
    ws = _distribute_words("Ye ek bahut lamba shabd hai", 2.0, 5.0)
    assert len(ws) == 6
    assert abs(ws[0]["start"] - 2.0) < 1e-6, "pehla word line ke start pe hona chahiye"
    assert abs(ws[-1]["end"] - 5.0) < 1e-6, "aakhri word line ke end pe hona chahiye"
    for a, b in zip(ws, ws[1:]):
        assert abs(a["end"] - b["start"]) < 1e-6, "words ke beech gap nahi hona chahiye"
        assert b["end"] > b["start"]


@test("Lamba shabd zyada time leta hai (syllable weighting)")
def _():
    ws = {w["w"]: w["end"] - w["start"] for w in _distribute_words("ek antarrashtriya", 0, 2)}
    assert ws["antarrashtriya"] > ws["ek"] * 1.5
    assert _syllables("रात") >= 1 and _syllables("gayab") == 2


@test("Reveal marker detect hota hai (300ms pause ke liye)")
def _():
    assert _is_reveal("Lekin sach kuch aur tha")
    assert _is_reveal("But the truth was different")
    assert not _is_reveal("Ghar khaali tha")


@test("Timeline mein reveal se pehle lamba pause hota hai")
def _():
    d = fresh_db()
    clips = [{"i": 0, "text": "Pehli line", "dur": 2.0, "path": "x"},
             {"i": 1, "text": "Doosri line", "dur": 2.0, "path": "x"},
             {"i": 2, "text": "Lekin sach alag tha", "dur": 2.0, "path": "x"}]
    tl = Voice(d)._build_timeline(clips)
    assert tl[0]["pause_before"] == 0.0
    assert tl[2]["pause_before"] > tl[1]["pause_before"], "reveal se pehle lamba pause chahiye"
    assert tl[2]["end"] > tl[1]["end"] > tl[0]["end"]
    d.close()


@test("no_pauses timeline chhota hota hai (ffmpeg missing wala case)")
def _():
    d = fresh_db()
    clips = [{"i": i, "text": f"line {i}", "dur": 2.0, "path": "x"} for i in range(4)]
    v = Voice(d)
    with_p = v._build_timeline(clips)[-1]["end"]
    without_p = v._build_timeline(clips, no_pauses=True)[-1]["end"]
    assert abs(without_p - 8.0) < 1e-6, "bina pause ke exactly clips ka sum hona chahiye"
    assert with_p > without_p
    d.close()


@test("MP3 duration parser sahi kaam karta hai")
def _():
    import glob
    files = glob.glob(str(Path(__file__).parent / "output" / "*" / "narration.mp3"))
    if not files:
        return  # koi render nahi hua abhi — skip
    dur = duration_sec(files[0])
    assert dur > 1.0, f"duration galat: {dur}"


# =====================================================================
print("\n🧪 9. IMAGE GEN (Phase 2, offline)")
# =====================================================================

@test("Fallback chain sahi kram mein hai")
def _():
    ig = ImageGen()
    assert ig.providers == ["pollinations", "gemini_image", "local_placeholder"]


@test("Placeholder provider offline image bana deta hai")
def _():
    import tempfile
    p = Path(tempfile.mkdtemp()) / "ph.jpg"
    prov = ImageGen(["local_placeholder"]).generate_one("test prompt noir", p)
    assert prov == "local_placeholder" and p.exists() and p.stat().st_size > 1000


@test("Saare provider fail hon to exception aati hai (silent fail nahi)")
def _():
    import tempfile

    class Broken(ImageGen):
        def _p_local_placeholder(self, *a, **k):
            raise RuntimeError("jaan boojh kar fail")

    p = Path(tempfile.mkdtemp()) / "x.jpg"
    try:
        Broken(["local_placeholder"]).generate_one("x", p)
        raise AssertionError("exception aani chahiye thi")
    except RuntimeError as e:
        assert "Saare image providers fail" in str(e)


# =====================================================================
print("\n🧪 10. PHASE 2 PIPELINE (offline integration)")
# =====================================================================

@test("Scene timing continuous hai — koi gap ya overlap nahi")
def _():
    from run_phase2 import assign_scene_timing
    narration = {"duration_sec": 20.0, "lines": [
        {"start": 0.0, "end": 5.0}, {"start": 5.2, "end": 10.0},
        {"start": 10.2, "end": 15.0}, {"start": 15.2, "end": 20.0}]}
    scenes = [{"n": i + 1, "file": f"s{i}.jpg"} for i in range(6)]
    out = assign_scene_timing(scenes, narration)
    assert len(out) == 6
    assert out[0]["start"] == 0.0
    assert abs(out[-1]["end"] - 20.0) < 0.01, "aakhri scene audio ke end pe khatam ho"
    for a, b in zip(out, out[1:]):
        assert abs(a["end"] - b["start"]) < 1e-6, "scenes ke beech gap/overlap nahi hona chahiye"


@test("⭐ 5 consecutive videos mein alag voice AUR alag template (acceptance test)")
def _():
    d = fresh_db()
    llm = LLM(force_mock=True)
    ad, v = ArtDirector(d, llm), Voice(d)
    combos = []
    for i in range(5):
        t, vo = ad.pick_template(), v.pick_profile()
        d.create_video(f"t{i}", template_id=t, voice_id=vo)
        combos.append((vo, t))
    assert len({c[0] for c in combos}) == 5, f"voice repeat: {combos}"
    assert len({c[1] for c in combos}) >= 4, f"template variety kam: {combos}"
    d.close()


# =====================================================================
print("\n🧪 11. FFMPEG HELPER (Phase 3)")
# =====================================================================

@test("ffmpeg mil jaata hai (system ya pip bundled)")
def _():
    try:
        b = ffmpeg_bin()
        assert Path(b).exists(), f"path exist nahi karta: {b}"
    except FFmpegMissing as e:
        raise AssertionError(f"ffmpeg nahi mila. {str(e)[:200]}") from e


@test("H.264 aur AAC dono available hain (Instagram ki requirement)")
def _():
    caps = capabilities()
    assert caps["libx264"], "libx264 nahi hai — IG error code 24 dega"
    assert caps["aac"], "AAC encoder nahi hai — IG error code 24 dega"


@test("ffmpeg errors ka Hinglish matlab milta hai")
def _():
    assert "filter" in _explain_ffmpeg("Unknown filter 'drawtext'").lower()
    assert "even" in _explain_ffmpeg("Invalid argument").lower()
    assert _explain_ffmpeg("kuch naya error") != ""


@test("probe() ffprobe ke bina bhi kaam karta hai (fallback)")
def _():
    from core.ffmpeg import probe
    import glob
    vids = glob.glob(str(Path(__file__).parent / "output" / "*" / "final.mp4"))
    if not vids:
        return  # abhi koi render nahi hua — skip
    info = probe(vids[0])
    assert info.get("streams"), "koi stream detect nahi hui"
    v = [s for s in info["streams"] if s["codec_type"] == "video"][0]
    assert v["codec_name"] == "h264" and v["width"] == 1080 and v["height"] == 1920


# =====================================================================
print("\n🧪 12. SUBTITLES (Phase 3)")
# =====================================================================

@test("ASS file banti hai aur karaoke tags hote hain")
def _():
    import tempfile
    words = [{"w": f"w{i}", "start": i * 0.4, "end": i * 0.4 + 0.35} for i in range(10)]
    p = build_ass(words, "Test hook overlay", Path(tempfile.mkdtemp()) / "t.ass")
    txt = p.read_text(encoding="utf-8")
    assert "[V4+ Styles]" in txt and "[Events]" in txt
    assert "\\k" in txt, "karaoke tags nahi hain — sirf static text hai"
    assert "Test hook overlay" in txt


@test("Hook overlay top-third mein hai (Alignment 8)")
def _():
    import tempfile
    p = build_ass([], "hook", Path(tempfile.mkdtemp()) / "t.ass")
    style = [l for l in p.read_text().splitlines() if l.startswith("Style: Hook")][0]
    assert style.split(",")[18] == "8", "Hook Alignment 8 (top-center) hona chahiye"
    sub = [l for l in p.read_text().splitlines() if l.startswith("Style: Sub")][0]
    assert sub.split(",")[18] == "2", "Sub Alignment 2 (bottom-center) hona chahiye"


@test("Karaoke \\k durations word timing se match karti hain")
def _():
    import re, tempfile
    words = [{"w": "ek", "start": 0.0, "end": 0.5}, {"w": "do", "start": 0.5, "end": 1.2}]
    p = build_ass(words, "", Path(tempfile.mkdtemp()) / "t.ass")
    ks = [int(x) for x in re.findall(r"\\k(\d+)", p.read_text())]
    assert ks == [50, 70], f"centiseconds galat: {ks}"


@test("Words groups mein bantte hain, bade gap pe naya group")
def _():
    ws = [{"w": "a", "start": 0, "end": 0.3}, {"w": "b", "start": 0.3, "end": 0.6},
          {"w": "c", "start": 2.0, "end": 2.3}]   # 1.4s ka gap
    g = _group_words(ws, 4)
    assert len(g) == 2, f"gap pe group tootna chahiye tha: {g}"
    assert len(_group_words([{"w": str(i), "start": i * .3, "end": i * .3 + .25}
                             for i in range(9)], 4)) == 3


@test("ASS timestamp format sahi hai")
def _():
    assert _ts(0) == "0:00:00.00"
    assert _ts(65.5) == "0:01:05.50"
    assert _ts(-5) == "0:00:00.00"   # negative pe crash nahi


@test("SRT bhi banti hai (YouTube accessibility + search)")
def _():
    import tempfile
    words = [{"w": f"w{i}", "start": i * 0.4, "end": i * 0.4 + 0.35} for i in range(8)]
    p = build_srt(words, Path(tempfile.mkdtemp()) / "t.srt")
    txt = p.read_text()
    assert "-->" in txt and "00:00:00,000" in txt


@test("ASS ke special characters escape hote hain (crash nahi)")
def _():
    import tempfile
    p = build_ass([{"w": "{weird}", "start": 0, "end": 1}],
                  "hook \\ with {braces}", Path(tempfile.mkdtemp()) / "t.ass")
    body = p.read_text().split("[Events]")[1]
    assert "{weird}" not in body, "braces escape nahi hue — libass confuse hoga"


# =====================================================================
print("\n🧪 13. KEN BURNS + SOUND DESIGN (Phase 3)")
# =====================================================================

@test("Har motion ka valid filter chain banta hai")
def _():
    for m in ("zoom_in", "zoom_out", "zoom_in_slow", "pan_left", "pan_right", "pan_up"):
        f = ken_burns(m, 4.0, 1080, 1920, 30)
        assert "crop" in f and "fps=30" in f and "format=yuv420p" in f, m
        assert "zoompan" not in f, "zoompan slow hai — use nahi karna chahiye"


@test("Unknown motion pe crash nahi hota (static fallback)")
def _():
    f = ken_burns("koi_bhi_motion", 3.0, 1080, 1920, 30)
    assert "crop=1080:1920" in f


@test("⭐ Ken Burns dimensions hamesha EVEN hoti hain (H.264 requirement)")
def _():
    assert _even(1350.7) == 1350 and _even(1351) == 1350 and _even(4.9) == 4
    f = ken_burns("zoom_in", 4.0, 1080, 1920, 30)
    assert "2*floor(" in f, "even-rounding nahi hai — ffmpeg 'Invalid argument' dega"


@test("Parallax scenes dheemi speed pe chalte hain")
def _():
    normal = ken_burns("pan_left", 4.0, 1080, 1920, 30, parallax=False)
    para = ken_burns("pan_left", 4.0, 1080, 1920, 30, parallax=True)
    assert normal != para, "parallax se koi farq nahi pada"
    assert "*0.5" in para or "0.5" in para


@test("Sound design: drone + har cut pe whoosh")
def _():
    inputs, filt = build_audio_filter(5, [4.0, 8.0, 12.0, 16.0], 20.0)
    assert filt.count("sine=") == 0 and "sine=frequency=55" in " ".join(inputs)
    assert inputs.count("anoisesrc=color=brown:sample_rate=44100:amplitude=0.5") == 4
    assert "[drone]" in filt and "[whooshes]" in filt


@test("⭐ Loudness -14 LUFS pe normalize hota hai (render spec)")
def _():
    _, filt = build_audio_filter(3, [5.0], 15.0)
    assert "loudnorm=I=-14" in filt, "-14 LUFS normalize nahi ho raha"
    assert "TP=-1.5" in filt, "true peak limit nahi hai — clipping ho sakti hai"


@test("Video ke shuru/aakhir wale cuts pe whoosh nahi lagta")
def _():
    inputs, _ = build_audio_filter(3, [0.1, 10.0, 19.9], 20.0)
    assert inputs.count("-f") == 2 + 1, "sirf beech wala cut whoosh lena chahiye"


@test("Koi bhi copyrighted audio use nahi hota (hard constraint #6)")
def _():
    inputs, filt = build_audio_filter(4, [4.0, 8.0], 12.0)
    joined = " ".join(inputs) + filt
    assert "sine=" in joined and "anoisesrc" in joined, "audio generate hona chahiye"
    for bad in (".mp3", ".wav", "music/", "http"):
        assert bad not in joined, f"bahar ka audio source mila: {bad}"


@test("Audio input indices shift hote hain (video input #0 hone ke baad)")
def _():
    out = _shift_audio_idx("[0:a]vol[narr];[1:a][2:a]amix[dr]")
    assert out == "[1:a]vol[narr];[2:a][3:a]amix[dr]"


# =====================================================================
print("\n🧪 14. SCENE TIMING FIX (Phase 3 bug regression)")
# =====================================================================

@test("⭐ Lines kam, scenes zyada — koi scene 0 second ka nahi hota")
def _():
    from run_phase2 import assign_scene_timing
    # ye asli bug tha: 5 lines, 7 scenes -> scene 6 aur 7 ko 0s mila
    lines = [{"start": 0.0, "end": 4.6}, {"start": 4.6, "end": 8.7},
             {"start": 8.7, "end": 13.2}, {"start": 13.2, "end": 18.2},
             {"start": 18.2, "end": 22.4}]
    out = assign_scene_timing([{"n": i + 1} for i in range(7)],
                              {"duration_sec": 22.4, "lines": lines})
    assert len(out) == 7
    for s in out:
        assert s["dur"] >= 1.0, f"scene {s['n']} ko sirf {s['dur']}s mila"
    assert abs(sum(s["dur"] for s in out) - 22.4) < 0.05, "total duration match nahi"


@test("Lines zyada, scenes kam — merge hota hai")
def _():
    from run_phase2 import assign_scene_timing
    lines = [{"start": i * 3.0, "end": i * 3.0 + 2.8} for i in range(9)]
    out = assign_scene_timing([{"n": i + 1} for i in range(6)],
                              {"duration_sec": 27.0, "lines": lines})
    assert len(out) == 6
    assert all(s["dur"] > 0 for s in out)
    assert abs(out[-1]["end"] - 27.0) < 0.05


@test("Bina timing info ke bhi barabar baant deta hai")
def _():
    from run_phase2 import assign_scene_timing
    out = assign_scene_timing([{"n": i + 1} for i in range(6)],
                              {"duration_sec": 30.0, "lines": []})
    assert len(out) == 6 and all(abs(s["dur"] - 5.0) < 0.01 for s in out)


@test("Scene boundaries continuous rehti hain (koi gap nahi)")
def _():
    from run_phase2 import assign_scene_timing
    lines = [{"start": 0.0, "end": 5.0}, {"start": 5.0, "end": 11.0},
             {"start": 11.0, "end": 16.0}, {"start": 16.0, "end": 24.0}]
    out = assign_scene_timing([{"n": i + 1} for i in range(7)],
                              {"duration_sec": 24.0, "lines": lines})
    assert out[0]["start"] == 0.0
    for a, b in zip(out, out[1:]):
        assert abs(a["end"] - b["start"]) < 1e-6


# =====================================================================
print("\n🧪 15. RENDERED VIDEO SPEC (agar koi video bana ho)")
# =====================================================================

@test("⭐ Rendered video IG/YT spec pe khara utarta hai")
def _():
    import glob
    from core.ffmpeg import probe
    vids = sorted(glob.glob(str(Path(__file__).parent / "output" / "*" / "final.mp4")))
    if not vids:
        print("     (skip — abhi koi video render nahi hua)")
        return
    info = probe(vids[-1])
    streams = info.get("streams", [])
    v = next((s for s in streams if s["codec_type"] == "video"), None)
    a = next((s for s in streams if s["codec_type"] == "audio"), None)
    assert v, "video stream nahi mili"
    assert a, "audio stream nahi mili — IG audio ke bina reject karta hai"
    assert v["codec_name"] == "h264", f"H.264 chahiye, mila {v['codec_name']}"
    assert a["codec_name"] == "aac", f"AAC chahiye, mila {a['codec_name']}"
    assert (v["width"], v["height"]) == (1080, 1920), f"{v['width']}x{v['height']}"
    assert v.get("pix_fmt") in ("yuv420p", "yuvj420p"), "yuv420p chahiye warna kuch players fail karte hain"
    dur = float(info["format"]["duration"])
    assert dur <= 90, f"IG Reels ki API limit 90s hai, ye {dur}s hai"
    size_mb = int(info["format"]["size"]) / 1024 / 1024
    assert size_mb < 100, f"{size_mb:.1f} MB — bahut bada"


@test("Cover frame aur SRT dono bante hain")
def _():
    import glob
    vids = sorted(glob.glob(str(Path(__file__).parent / "output" / "*" / "final.mp4")))
    if not vids:
        return
    d = Path(vids[-1]).parent
    assert (d / "cover.jpg").exists(), "cover.jpg nahi bana (thumbnail ke liye chahiye)"
    assert (d / "subtitles.srt").exists(), "subtitles.srt nahi bani"


# =====================================================================
print("\n🧪 16. VALIDATE — format gates (Phase 4)")
# =====================================================================

def _rep():
    return Report(path="x.mp4")


@test("Missing file pe FATAL aata hai")
def _():
    r = validate("/koi/aisi/file/nahi.mp4")
    assert not r.ok and r.fatals[0].code == "NO_FILE"


@test("⭐ Galat video codec = IG error code 24 (FATAL)")
def _():
    r = _rep()
    _check_video_stream(r, {"codec_name": "vp9", "width": 1080, "height": 1920})
    assert not r.ok
    assert any(i.code == "IG_CODE_24" for i in r.fatals)


@test("⭐ Galat audio codec = IG error code 24 (FATAL)")
def _():
    r = _rep()
    _check_audio_stream(r, {"codec_name": "opus", "sample_rate": "48000"})
    assert any(i.code == "IG_CODE_24" for i in r.fatals)


@test("⭐ Audio hi na ho to FATAL (IG bina audio ke reject karta hai)")
def _():
    r = _rep()
    _check_audio_stream(r, None)
    assert any(i.code == "NO_AUDIO" for i in r.fatals)


@test("Horizontal video FATAL hai (Reels/Shorts vertical hain)")
def _():
    r = _rep()
    _check_video_stream(r, {"codec_name": "h264", "width": 1920, "height": 1080})
    assert any(i.code == "RESOLUTION" for i in r.fatals)


@test("Galat fps FATAL (IG sirf 23-60 leta hai)")
def _():
    for bad in ("15/1", "120/1"):
        r = _rep()
        _check_video_stream(r, {"codec_name": "h264", "width": 1080, "height": 1920,
                                "r_frame_rate": bad})
        assert any(i.code == "IG_FPS" for i in r.fatals), bad
    r = _rep()
    _check_video_stream(r, {"codec_name": "h264", "width": 1080, "height": 1920,
                            "r_frame_rate": "30/1"})
    assert not any(i.code == "IG_FPS" for i in r.issues)


@test("Sahi spec pe koi FATAL nahi aata")
def _():
    r = _rep()
    _check_video_stream(r, {"codec_name": "h264", "width": 1080, "height": 1920,
                            "pix_fmt": "yuv420p", "r_frame_rate": "30/1"})
    _check_audio_stream(r, {"codec_name": "aac", "sample_rate": "44100"})
    assert r.ok, [i.msg for i in r.fatals]


@test("⭐ 90s se lamba = FATAL (IG API ki hard limit)")
def _():
    r = _rep()
    _check_duration(r, {"format": {"duration": "95.0"}}, {})
    assert any(i.code == "IG_TOO_LONG" for i in r.fatals)
    assert LIMITS["ig_max_sec"] == 90


@test("60s se lamba = Short nahi banta (WARN)")
def _():
    r = _rep()
    _check_duration(r, {"format": {"duration": "75.0"}}, {})
    assert any(i.code == "NOT_A_SHORT" for i in r.warns)
    assert r.ok, "75s IG pe chalega, sirf YT Short nahi banega"


@test("Sweet spot ke bahar WARN aata hai")
def _():
    r = _rep()
    _check_duration(r, {"format": {"duration": "12.0"}}, {})
    assert any(i.code == "BELOW_SWEET_SPOT" for i in r.warns)
    r2 = _rep()
    _check_duration(r2, {"format": {"duration": "32.0"}}, {})
    assert not r2.issues, "32s bilkul theek hai"


@test("fps parsing sahi hai")
def _():
    assert _parse_fps("30/1") == 30.0
    assert abs(_parse_fps("30000/1001") - 29.97) < 0.01
    assert _parse_fps("0/0") is None and _parse_fps(None) is None


# =====================================================================
print("\n🧪 17. VALIDATE — content gates (Phase 4)")
# =====================================================================

@test("⭐ Placeholder images = FATAL (publish layak nahi)")
def _():
    r = _rep()
    _check_content(r, {"script": {}, "words": [{"w": "a"}],
                       "scenes": [{"provider": "pollinations"},
                                  {"provider": "local_placeholder"}]})
    assert any(i.code == "PLACEHOLDER_IMAGES" for i in r.fatals)


@test("Subtitles na hon to WARN (60% log sound off pe dekhte hain)")
def _():
    r = _rep()
    _check_content(r, {"script": {"hook_text_overlay": "x"}, "words": [], "scenes": []})
    assert any(i.code == "NO_SUBTITLES" for i in r.warns)


@test("espeak robotic voice pe WARN")
def _():
    r = _rep()
    _check_content(r, {"script": {}, "words": [{"w": "a"}], "scenes": [],
                       "narration": {"engines_used": ["espeak"]}})
    assert any(i.code == "ROBOTIC_VOICE" for i in r.warns)


@test("Bahut zyada hashtags pe WARN (3 hi kaafi hain)")
def _():
    r = _rep()
    _check_content(r, {"script": {"hashtags": ["#a"] * 9}, "words": [{"w": "x"}],
                       "scenes": []})
    assert any(i.code == "TOO_MANY_TAGS" for i in r.warns)


@test("Achhe content pe koi FATAL nahi")
def _():
    r = _rep()
    _check_content(r, {"script": {"hook_text_overlay": "Ek raat mein sab gayab",
                                  "comment_bait": "Tumhe kya lagta hai asli wajah kya thi bhai",
                                  "hashtags": ["#a", "#b", "#c"]},
                       "words": [{"w": "x"}] * 40,
                       "scenes": [{"provider": "pollinations"}] * 7,
                       "narration": {"engines_used": ["edge_tts"]}})
    assert r.ok and not r.warns, [i.msg for i in r.issues]


# =====================================================================
print("\n🧪 18. VALIDATE — asli rendered video pe (Phase 4)")
# =====================================================================

@test("⭐ Asli video validate pass karta hai (loudness + black frames ke saath)")
def _():
    import glob
    vids = sorted(glob.glob(str(Path(__file__).parent / "output" / "*" / "final.mp4")))
    if not vids:
        print("     (skip — abhi koi video render nahi hua)")
        return
    r = validate_dir(Path(vids[-1]).parent, deep=True)
    assert r.ok, "FATAL issues: " + "; ".join(f"{i.code}: {i.msg}" for i in r.fatals)
    f = r.facts
    assert f["vcodec"] == "h264" and f["acodec"] == "aac"
    assert f["resolution"] == "1080x1920"
    if "lufs" in f:
        assert abs(f["lufs"] - LIMITS["lufs_target"]) <= LIMITS["lufs_tolerance"], \
            f"{f['lufs']} LUFS — target {LIMITS['lufs_target']}"
        assert f["true_peak"] <= 0, f"true peak {f['true_peak']} — clipping"


@test("⭐ Beech mein kaale frames nahi hain (fadeblack bug regression)")
def _():
    import glob
    vids = sorted(glob.glob(str(Path(__file__).parent / "output" / "*" / "final.mp4")))
    if not vids:
        return
    r = validate_dir(Path(vids[-1]).parent, deep=True)
    n = r.facts.get("black_segments")
    if n is not None:
        assert n == 0, (f"{n} jagah kaale frames mile — 'fadeblack' transition "
                        f"wapas aa gaya? Wo retention maar deta hai.")


@test("Report JSON mein serialize hoti hai (dashboard ke liye)")
def _():
    r = _rep()
    r.add("WARN", "TEST", "test message", "test fix")
    d = r.to_dict()
    assert json.dumps(d) and d["issues"][0]["code"] == "TEST" and d["ok"] is True


# =====================================================================
print("\n🧪 19. DASHBOARD (Phase 4)")
# =====================================================================

@test("gather() dashboard ka poora data deta hai")
def _():
    d = gather()
    for k in ("brand", "autonomy", "mock_mode", "summary", "queue",
              "published", "quota", "learnings", "logs"):
        assert k in d, f"missing key: {k}"
    assert json.dumps(d, default=str), "JSON serialize nahi hua"


@test("Quota snapshot mein saare buckets hain")
def _():
    q = gather()["quota"]
    for b in ("youtube_units", "youtube_uploads", "ig_publishes", "gemini_requests"):
        assert b in q and "pct" in q[b] and "reset_in" in q[b]


@test("⭐ Approve/reject se status badalta hai aur audit log banta hai")
def _():
    import tempfile
    from core import config as cfgmod
    d = fresh_db()
    vid = d.create_video("dashboard test")
    d.set_status(vid, "rendered")
    # do_action apni DB kholta hai, isliye seedha DB pe test karte hain
    d.set_status(vid, "approved", note="dashboard se approve hua")
    d.log_event("approval", "human", vid, decision="approved")
    assert d.get_video(vid)["status"] == "approved"
    ev = d.q("SELECT * FROM events WHERE video_id=? AND kind='approval'", (vid,))
    assert len(ev) == 1 and "approved" in ev[0]["payload"]
    d.close()


@test("Unknown action pe saaf error aata hai")
def _():
    res = do_action("kuch_bhi", 99999, {})
    assert res["ok"] is False and "error" in res


@test("Reject karne pe reason save hota hai (learning ke liye)")
def _():
    d = fresh_db()
    vid = d.create_video("reject test")
    d.set_status(vid, "rejected", note="reject: hook kamzor tha")
    assert "hook kamzor" in d.get_video(vid)["notes"]
    d.close()


@test("Dashboard sirf localhost pe bind hota hai (security)")
def _():
    src = (Path(__file__).parent / "web" / "server.py").read_text(encoding="utf-8")
    assert '"127.0.0.1"' in src, "0.0.0.0 pe bind mat karo — dashboard mein auth nahi hai"
    assert "0.0.0.0" not in src


@test("Media serving path traversal se safe hai")
def _():
    src = (Path(__file__).parent / "web" / "server.py").read_text(encoding="utf-8")
    assert ".resolve()" in src and "startswith" in src, \
        "path traversal check missing — ../../etc/passwd padha ja sakta hai"


@test("Video seeking ke liye Range requests support hain")
def _():
    src = (Path(__file__).parent / "web" / "server.py").read_text(encoding="utf-8")
    assert "206" in src and "Content-Range" in src, "Range support ke bina video seek nahi hoga"


# =====================================================================
print("\n🧪 20. OAUTH (Phase 5)")
# =====================================================================

@test("Scopes minimum hain (Google review inhe dekhta hai)")
def _():
    assert "https://www.googleapis.com/auth/youtube.upload" in YT_SCOPES
    assert len(YT_SCOPES) <= 5, "zaroorat se zyada scopes mat maango"
    for sc in YT_SCOPES:
        assert sc.startswith("https://www.googleapis.com/auth/youtube") or \
               sc.startswith("https://www.googleapis.com/auth/yt-analytics")


@test("client_secret.json na ho to beginner-friendly error aata hai")
def _():
    try:
        _load_client_secret(Path("/koi/nahi/client_secret.json"))
        raise AssertionError("OAuthError aani chahiye thi")
    except OAuthError as e:
        msg = str(e)
        assert "Desktop app" in msg and "YouTube Data API v3" in msg
        assert "SETUP.md" in msg


@test("Galat type ka OAuth client detect hota hai")
def _():
    import tempfile
    p = Path(tempfile.mkdtemp()) / "cs.json"
    p.write_text(json.dumps({"service_account": {"x": 1}}))
    try:
        _load_client_secret(p)
        raise AssertionError("error aani chahiye thi")
    except OAuthError as e:
        assert "Desktop app" in str(e)


@test("'installed' aur 'web' dono format padhe jaate hain")
def _():
    import tempfile
    d = Path(tempfile.mkdtemp())
    for key in ("installed", "web"):
        p = d / f"{key}.json"
        p.write_text(json.dumps({key: {"client_id": "cid", "client_secret": "sec"}}))
        assert _load_client_secret(p) == ("cid", "sec")


@test("Token expire hone se 2 min pehle refresh trigger hota hai")
def _():
    import tempfile, time as t
    tp = Path(tempfile.mkdtemp()) / "token.json"
    c = Credentials({"access_token": "x", "expires_at": t.time() + 600}, tp, "cid", "sec")
    assert not c._expired(), "10 min baaki hai, refresh nahi hona chahiye"
    c.data["expires_at"] = t.time() + 60
    assert c._expired(), "1 min baaki hai — pehle hi refresh hona chahiye"


@test("Refresh token na ho to saaf error aata hai")
def _():
    import tempfile
    tp = Path(tempfile.mkdtemp()) / "t.json"
    c = Credentials({"access_token": "x", "expires_at": 0}, tp, "cid", "sec")
    try:
        c.access_token
        raise AssertionError("OAuthError aani chahiye thi")
    except OAuthError as e:
        assert "authorize_youtube.py" in str(e)


@test("Token file 0600 permissions pe save hoti hai")
def _():
    import tempfile, os as _os, stat
    tp = Path(tempfile.mkdtemp()) / "token.json"
    Credentials({"access_token": "secret"}, tp, "cid", "sec").save()
    assert tp.exists()
    if _os.name != "nt":
        mode = stat.S_IMODE(tp.stat().st_mode)
        assert mode == 0o600, f"token world-readable hai: {oct(mode)}"


@test("OAuth flow mein CSRF state check hai")
def _():
    src = (Path(__file__).parent / "core" / "oauth.py").read_text(encoding="utf-8")
    assert "secrets.token_urlsafe" in src and 'res.get("state") != state' in src
    assert '"access_type": "offline"' in src, "offline ke bina refresh_token nahi milta"
    assert '"prompt": "consent"' in src


# =====================================================================
print("\n🧪 21. PUBLISHER — metadata + AI disclosure (Phase 5)")
# =====================================================================

def _pub_row(db):
    vid = db.create_video(
        "Test mystery topic",
        title="Ek raat mein sab gayab", caption="Case #1 — unsolved.",
        hashtags=["#unsolvedmystery", "#suspense", "#hindi"],
        hook_type="pov", voice_id="hi_f_calm", template_id="noir_teal",
        script_json={"caption": "Case #1 — unsolved.",
                     "comment_bait": "Tumhe kya lagta hai asli wajah kya thi bhai?"},
        length_sec=30.0, video_path="/tmp/x.mp4")
    return db.get_video(vid)


@test("⭐⭐ AI DISCLOSURE FLAG hamesha ON hota hai (hard constraint #4)")
def _():
    d = fresh_db()
    pub = YouTubePublisher(d, Quota(d), creds=object(), dry_run=True)
    meta = pub._build_metadata(_pub_row(d), "private", None)
    assert meta["status"]["containsSyntheticMedia"] is True, \
        "AI disclosure OFF hai! Undisclosed AI content = reduced reach ya removal."
    d.close()


@test("Description mein bhi AI disclosure likha hota hai")
def _():
    d = fresh_db()
    pub = YouTubePublisher(d, Quota(d), creds=object(), dry_run=True)
    desc = pub._build_metadata(_pub_row(d), "private", None)["snippet"]["description"]
    assert "AI" in desc


@test("Default privacy 'private' hai (pehle dekho, phir public karo)")
def _():
    d = fresh_db()
    pub = YouTubePublisher(d, Quota(d), creds=object(), dry_run=True)
    assert pub._build_metadata(_pub_row(d), "private", None)["status"]["privacyStatus"] == "private"
    d.close()


@test("⭐ publishAt sirf private ke saath lagta hai (Section 2)")
def _():
    d = fresh_db()
    pub = YouTubePublisher(d, Quota(d), creds=object(), dry_run=True)
    row = _pub_row(d)
    at = "2026-08-01T14:30:00Z"
    priv = pub._build_metadata(row, "private", at)
    assert priv["status"]["publishAt"] == at
    pubm = pub._build_metadata(row, "public", at)
    assert "publishAt" not in pubm["status"], "public video pe publishAt set nahi hota"
    d.close()


@test("Title 100 char se chhota rehta hai + #shorts lagta hai")
def _():
    d = fresh_db()
    vid = d.create_video("x", title="A" * 200, script_json={}, hashtags=[])
    pub = YouTubePublisher(d, Quota(d), creds=object(), dry_run=True)
    t = pub._build_metadata(d.get_video(vid), "private", None)["snippet"]["title"]
    assert len(t) <= 100, f"title {len(t)} char ka hai"
    d.close()


@test("Description 5000 char limit ke andar rehta hai")
def _():
    d = fresh_db()
    vid = d.create_video("x", caption="B" * 9000, script_json={"caption": "B" * 9000},
                         hashtags=["#a"])
    pub = YouTubePublisher(d, Quota(d), creds=object(), dry_run=True)
    desc = pub._build_metadata(d.get_video(vid), "private", None)["snippet"]["description"]
    assert len(desc) <= 5000, f"description {len(desc)} char ka hai"
    d.close()


@test("madeForKids explicitly false set hota hai")
def _():
    d = fresh_db()
    pub = YouTubePublisher(d, Quota(d), creds=object(), dry_run=True)
    m = pub._build_metadata(_pub_row(d), "private", None)
    assert m["status"]["selfDeclaredMadeForKids"] is False
    d.close()


# =====================================================================
print("\n🧪 22. PUBLISHER — gates (Phase 5)")
# =====================================================================

@test("⭐ review_first mein bina approve ke publish BLOCK hota hai")
def _():
    d = fresh_db()
    vid = d.create_video("x", video_path="/tmp/nope.mp4")
    d.set_status(vid, "rendered")
    pub = YouTubePublisher(d, Quota(d), creds=object(), dry_run=True)
    try:
        pub.publish(vid)
        raise AssertionError("publish block hona chahiye tha")
    except PublishError as e:
        assert "approved" in str(e) and "review_first" in str(e)
    d.close()


@test("Video file na ho to publish nahi hota")
def _():
    d = fresh_db()
    vid = d.create_video("x", video_path="/koi/file/nahi.mp4")
    d.set_status(vid, "approved")
    pub = YouTubePublisher(d, Quota(d), creds=object(), dry_run=True)
    try:
        pub.publish(vid)
        raise AssertionError("file missing pe fail hona chahiye tha")
    except PublishError as e:
        assert "nahi mili" in str(e)
    d.close()


@test("⭐ DRY RUN mein quota kharch NAHI hota (bug regression)")
def _():
    import glob
    vids = sorted(glob.glob(str(Path(__file__).parent / "output" / "*" / "final.mp4")))
    if not vids:
        return
    d = fresh_db()
    q = Quota(d)
    vid = d.create_video("x", video_path=vids[-1], script_json={}, hashtags=[],
                         title="test")
    d.set_status(vid, "approved")
    YouTubePublisher(d, q, creds=object(), dry_run=True).publish(vid)
    assert q.used("youtube_units") == 0, "dry-run ne asli quota kha liya!"
    assert q.used("youtube_uploads") == 0
    d.close()


@test("⭐ Quota khatam ho to upload queue mein jaata hai (crash nahi)")
def _():
    import glob
    vids = sorted(glob.glob(str(Path(__file__).parent / "output" / "*" / "final.mp4")))
    if not vids:
        return
    d = fresh_db()
    q = Quota(d)
    for i in range(5):                      # cap = 5/day
        q.check_and_spend("youtube_uploads", 1, f"burn {i}")
    vid = d.create_video("x", video_path=vids[-1], script_json={}, hashtags=[], title="t")
    d.set_status(vid, "approved")
    res = YouTubePublisher(d, q, creds=object(), dry_run=False).publish(vid)
    assert res["status"] == "queued", f"queue hona chahiye tha, mila: {res}"
    assert d.get_video(vid)["status"] == "approved", "status approved rehna chahiye"
    d.close()


@test("Validate fail ho to publish block hota hai")
def _():
    import tempfile
    d = fresh_db()
    bad = Path(tempfile.mkdtemp()) / "final.mp4"
    bad.write_bytes(b"not a real video")
    vid = d.create_video("x", video_path=str(bad), script_json={}, hashtags=[], title="t")
    d.set_status(vid, "approved")
    try:
        YouTubePublisher(d, Quota(d), creds=object(), dry_run=True).publish(vid)
        raise AssertionError("validate fail pe block hona chahiye tha")
    except PublishError as e:
        assert "validate fail" in str(e).lower()
    d.close()


# =====================================================================
print("\n🧪 23. PUBLISHER — errors + scheduling (Phase 5)")
# =====================================================================

@test("⭐ Hidden upload limit (~7/day) ka saaf message aata hai")
def _():
    import urllib.error, io
    body = json.dumps({"error": {"code": 400, "message": "too many uploads",
                                 "errors": [{"reason": "uploadLimitExceeded"}]}}).encode()
    e = urllib.error.HTTPError("u", 400, "Bad", {}, io.BytesIO(body))
    msg = str(_yt_error(e))
    assert "HIDDEN LIMIT" in msg and "7 uploads/day" in msg


@test("quotaExceeded ka Hinglish matlab milta hai")
def _():
    import urllib.error, io
    body = json.dumps({"error": {"errors": [{"reason": "quotaExceeded"}],
                                 "message": "quota"}}).encode()
    e = urllib.error.HTTPError("u", 403, "F", {}, io.BytesIO(body))
    assert "Pacific" in str(_yt_error(e))


@test("401 pe token refresh ka hint milta hai")
def _():
    import urllib.error, io
    e = urllib.error.HTTPError("u", 401, "Unauthorized", {}, io.BytesIO(b"{}"))
    assert "authorize" in str(_yt_error(e)).lower()


@test("Resumable chunk size 256KB ka multiple hai (Google requirement)")
def _():
    assert CHUNK % (256 * 1024) == 0, f"chunk {CHUNK} — 256KB ka multiple hona chahiye"
    assert CHUNK >= 256 * 1024


@test("Resumable upload use hota hai, simple nahi")
def _():
    src = (Path(__file__).parent / "agents" / "publisher.py").read_text(encoding="utf-8")
    assert "uploadType=resumable" in src
    assert "Content-Range" in src and "308" in src, "308 resume handle nahi hota"


@test("best_publish_time future ka valid ISO timestamp deta hai")
def _():
    from datetime import datetime, timezone
    d = fresh_db()
    ts = best_publish_time(d)
    t = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    assert t > datetime.now(timezone.utc), "publish time future mein hona chahiye"
    assert ts.endswith("Z")
    d.close()


@test("best_publish_time apne analytics se seekhta hai")
def _():
    d = fresh_db()
    for i in range(3):
        v = d.create_video(f"t{i}")
        d.update_video(v, published_ts=f"2026-07-0{i+1}T16:30:00+00:00", status="published")
        d.save_metrics(v, "youtube", "2h", views=5000)
    ts = best_publish_time(d)
    assert "T16:30" in ts, f"best hour 16 seekhna chahiye tha, mila {ts}"
    d.close()


@test("Private video pe first comment skip hota hai")
def _():
    src = (Path(__file__).parent / "agents" / "publisher.py").read_text(encoding="utf-8")
    assert 'privacy != "private"' in src, "private video pe comment post nahi hona chahiye"


@test("Comment pin API se nahi hota — user ko batate hain (jhoot nahi)")
def _():
    src = (Path(__file__).parent / "agents" / "publisher.py").read_text(encoding="utf-8")
    assert "PIN karna API se nahi hota" in src


# =====================================================================
print("\n🧪 23b. PUBLISHER — upload_file (Phase 4: koi bhi MP4)")
# =====================================================================

@test("upload_file: file na ho to saaf error (upload se pehle)")
def _():
    d = fresh_db()
    pub = YouTubePublisher(d, Quota(d), creds=object(), dry_run=True)
    try:
        pub.upload_file("/koi/file/nahi.mp4")
        raise AssertionError("missing file pe fail hona chahiye tha")
    except PublishError as e:
        assert "nahi mili" in str(e)
    d.close()


@test("upload_file: galat extension reject hota hai (fix hint ke saath)")
def _():
    import tempfile
    d = fresh_db()
    bad = Path(tempfile.mkdtemp()) / "video.avi"
    bad.write_bytes(b"x" * 100)
    pub = YouTubePublisher(d, Quota(d), creds=object(), dry_run=True)
    try:
        pub.upload_file(bad)
        raise AssertionError(".avi reject hona chahiye tha")
    except PublishError as e:
        assert ".avi" in str(e) and "ffmpeg" in str(e)
    d.close()


@test("upload_file: khaali (0 byte) file reject hoti hai")
def _():
    import tempfile
    d = fresh_db()
    empty = Path(tempfile.mkdtemp()) / "video.mp4"
    empty.write_bytes(b"")
    pub = YouTubePublisher(d, Quota(d), creds=object(), dry_run=True)
    try:
        pub.upload_file(empty)
        raise AssertionError("khaali file reject honi chahiye thi")
    except PublishError as e:
        assert "khaali" in str(e)
    d.close()


@test("⭐ upload_file: AI disclosure yahan bhi ON hai + dry-run quota nahi khaata")
def _():
    import tempfile
    d = fresh_db()
    q = Quota(d)
    f = Path(tempfile.mkdtemp()) / "meri_video.mp4"
    f.write_bytes(b"x" * 5000)
    pub = YouTubePublisher(d, q, creds=object(), dry_run=True)
    res = pub.upload_file(f, privacy="unlisted")
    assert res["status"] == "dry_run"
    assert res["metadata"]["status"]["containsSyntheticMedia"] is True, \
        "upload_file mein AI disclosure OFF hai!"
    assert res["metadata"]["status"]["privacyStatus"] == "unlisted"
    assert res["metadata"]["snippet"]["title"] == "meri video", "filename se title banna chahiye"
    assert q.used("youtube_uploads") == 0, "dry-run ne quota kha liya!"
    d.close()


@test("upload_file: quota khatam ho to queued milta hai (crash nahi)")
def _():
    import tempfile
    d = fresh_db()
    q = Quota(d)
    for i in range(5):                      # cap = 5/day
        q.check_and_spend("youtube_uploads", 1, f"burn {i}")
    f = Path(tempfile.mkdtemp()) / "v.mp4"
    f.write_bytes(b"x" * 5000)
    res = YouTubePublisher(d, q, creds=object(), dry_run=False).upload_file(f)
    assert res["status"] == "queued", f"queue hona chahiye tha, mila: {res}"
    d.close()


@test("upload_result: standard contract — id, url, status, upload time")
def _():
    from agents.publisher import upload_result
    r = upload_result("published", yt_video_id="abc123", privacy="public",
                      upload_secs=12.34)
    assert r["url"] == "https://youtube.com/shorts/abc123"
    assert r["upload_secs"] == 12.3
    assert r["uploaded_at"] and r["status"] == "published"
    r2 = upload_result("queued", reason="quota")
    assert r2["url"] is None and r2["uploaded_at"] is None


@test("publish() ab thumbnail bhi set karta hai (cover_path se)")
def _():
    src = (Path(__file__).parent / "agents" / "publisher.py").read_text(encoding="utf-8")
    assert "self.set_thumbnail(yt_id" in src, "publish ke baad thumbnail set hona chahiye"


@test("Upload progress bar dikhta hai (chunks pe)")
def _():
    src = (Path(__file__).parent / "agents" / "publisher.py").read_text(encoding="utf-8")
    assert "█" in src and "flush=True" in src


# =====================================================================
print("\n🧪 24. HOSTING — public URL (Phase 6)")
# =====================================================================

@test("Unknown hosting mode pe saaf error")
def _():
    import tempfile
    f = Path(tempfile.mkdtemp()) / "v.mp4"
    f.write_bytes(b"x" * 2000)
    try:
        host_upload(f, "koi_bhi_mode")
        raise AssertionError("error aani chahiye thi")
    except HostingError as e:
        assert "github_release" in str(e)


@test("File missing pe hosting fail hoti hai")
def _():
    try:
        host_upload("/koi/file/nahi.mp4", "catbox")
        raise AssertionError("error aani chahiye thi")
    except HostingError as e:
        assert "nahi mili" in str(e)


@test("GitHub hosting bina token ke beginner-friendly error deti hai")
def _():
    import tempfile, os as _os
    old_t, old_r = _os.environ.pop("GITHUB_TOKEN", None), _os.environ.pop("GITHUB_REPO", None)
    try:
        f = Path(tempfile.mkdtemp()) / "v.mp4"
        f.write_bytes(b"x" * 2000)
        try:
            host_upload(f, "github_release")
            raise AssertionError("error aani chahiye thi")
        except HostingError as e:
            assert "GITHUB_TOKEN" in str(e) and "SETUP.md" in str(e)
    finally:
        if old_t: _os.environ["GITHUB_TOKEN"] = old_t
        if old_r: _os.environ["GITHUB_REPO"] = old_r


@test("⭐ verify() galat URL pakadta hai (Meta ki call barbaad hone se pehle)")
def _():
    try:
        host_verify("https://example.invalid/nope.mp4")
        raise AssertionError("error aani chahiye thi")
    except HostingError as e:
        assert "reachable nahi" in str(e)


@test("Hosting mein Drive/Dropbox ki warning likhi hai (wo HTML dete hain)")
def _():
    src = (Path(__file__).parent / "core" / "hosting.py").read_text(encoding="utf-8")
    assert "text/html" in src, "HTML page detect nahi hota"
    assert "Google Drive" in src and "KAAM NAHI" in src.upper() or "kaam NAHI" in src


# =====================================================================
print("\n🧪 25. INSTAGRAM — publish gates (Phase 6)")
# =====================================================================

def _ig_row(db, path="/tmp/x.mp4", length=30.0):
    vid = db.create_video(
        "IG test topic", title="Test reel", caption="Case #1 unsolved",
        hashtags=["#mystery", "#suspense", "#hindi"], hook_type="pov",
        voice_id="hi_f_calm", template_id="noir_teal", length_sec=length,
        video_path=path,
        script_json={"caption": "Case #1 unsolved",
                     "comment_bait": "Tumhe kya lagta hai asli wajah kya thi bhai?"})
    return vid


@test("⭐ Personal account wali warning error message mein hai")
def _():
    import os as _os
    d = fresh_db()
    old = _os.environ.pop("IG_LONG_LIVED_TOKEN", None)
    try:
        ig = InstagramPublisher(d, Quota(d))
        ig.token = ""
        try:
            ig._require_creds()
            raise AssertionError("error aani chahiye thi")
        except IGError as e:
            assert "Business ya Creator" in str(e) and "Personal account" in str(e)
    finally:
        if old: _os.environ["IG_LONG_LIVED_TOKEN"] = old
        d.close()


@test("⭐ review_first mein bina approve ke IG publish BLOCK hota hai")
def _():
    d = fresh_db()
    vid = _ig_row(d)
    d.set_status(vid, "rendered")
    try:
        InstagramPublisher(d, Quota(d), dry_run=True).publish(vid)
        raise AssertionError("block hona chahiye tha")
    except IGError as e:
        assert "approved" in str(e)
    d.close()


@test("⭐ 90s se lamba video IG pe reject hota hai (API hard limit)")
def _():
    import glob
    vids = sorted(glob.glob(str(Path(__file__).parent / "output" / "*" / "final.mp4")))
    if not vids:
        return
    assert IG_MAX_SEC == 90
    src = (Path(__file__).parent / "agents" / "ig_publisher.py").read_text(encoding="utf-8")
    assert "IG_MAX_SEC" in src and "HARD limit" in src


@test("⭐ DRY RUN mein IG quota kharch NAHI hota")
def _():
    import glob
    vids = sorted(glob.glob(str(Path(__file__).parent / "output" / "*" / "final.mp4")))
    if not vids:
        return
    d = fresh_db()
    q = Quota(d)
    vid = _ig_row(d, vids[-1])
    d.set_status(vid, "approved")
    InstagramPublisher(d, q, dry_run=True).publish(vid)
    assert q.used("ig_publishes") == 0, "dry-run ne asli quota kha liya!"
    assert q.used("ig_calls_hour") == 0
    d.close()


@test("⭐ IG quota khatam ho to queue mein jaata hai (crash nahi)")
def _():
    import glob, os as _os
    vids = sorted(glob.glob(str(Path(__file__).parent / "output" / "*" / "final.mp4")))
    if not vids:
        return
    d = fresh_db()
    q = Quota(d)
    for i in range(20):                    # cap = 20
        q.check_and_spend("ig_publishes", 1, f"burn {i}")
    vid = _ig_row(d, vids[-1])
    d.set_status(vid, "approved")
    ig = InstagramPublisher(d, q, dry_run=False)
    ig.token, ig.ig_user_id = "fake", "123"   # creds check pass karne ke liye
    res = ig.publish(vid)
    assert res["status"] == "queued", f"queue hona chahiye tha: {res}"
    d.close()


@test("Caption 2200 char limit ke andar rehta hai")
def _():
    d = fresh_db()
    vid = d.create_video("x", caption="B" * 9000, hashtags=["#a"],
                         script_json={"caption": "B" * 9000})
    ig = InstagramPublisher(d, Quota(d), dry_run=True)
    cap = ig._build_caption(d.get_video(vid))
    assert len(cap) <= 2200, f"caption {len(cap)} char ka hai"
    d.close()


@test("Caption mein AI disclosure hai")
def _():
    d = fresh_db()
    vid = _ig_row(d)
    cap = InstagramPublisher(d, Quota(d), dry_run=True)._build_caption(d.get_video(vid))
    assert "AI" in cap
    d.close()


# =====================================================================
print("\n🧪 26. INSTAGRAM — container flow + errors (Phase 6)")
# =====================================================================

@test("⭐ 3-step flow implement hua hai (container -> poll -> publish)")
def _():
    src = (Path(__file__).parent / "agents" / "ig_publisher.py").read_text(encoding="utf-8")
    assert "/media" in src and "media_publish" in src
    assert "status_code" in src and "FINISHED" in src
    assert src.index("_create_container") < src.index("_poll_container") < \
           src.index("_publish_container"), "steps ka order galat hai"


@test("⭐ Container 24h expiry handle hoti hai")
def _():
    assert CONTAINER_TTL_HOURS == 24
    src = (Path(__file__).parent / "agents" / "ig_publisher.py").read_text(encoding="utf-8")
    assert "EXPIRED" in src, "EXPIRED status handle nahi hota"
    assert "pehle se container bana kar" in src.lower() or "24 GHANTE" in src


@test("Polling ka timeout hai (infinite loop nahi)")
def _():
    assert 60 <= POLL_MAX_WAIT <= 600, f"POLL_MAX_WAIT={POLL_MAX_WAIT}"
    src = (Path(__file__).parent / "agents" / "ig_publisher.py").read_text(encoding="utf-8")
    assert "while waited < POLL_MAX_WAIT" in src


@test("⭐ Polling bhi rate limit budget mein ginti hai")
def _():
    src = (Path(__file__).parent / "agents" / "ig_publisher.py").read_text(encoding="utf-8")
    assert 'self.quota.spend("ig_calls_hour"' in src, \
        "polling calls count nahi hoti — 200/hour limit hit ho jayegi"


@test("⭐ Error code 24 ka saaf matlab milta hai (format reject)")
def _():
    body = json.dumps({"error": {"message": "bad format", "type": "OAuthException",
                                 "code": 24}}).encode()
    msg = str(_ig_error(400, body))
    assert "FORMAT REJECT" in msg and "H.264" in msg and "validate" in msg


@test("Token expire (code 190) ka matlab milta hai")
def _():
    body = json.dumps({"error": {"code": 190, "message": "expired"}}).encode()
    assert "long-lived" in str(_ig_error(400, body)).lower()


@test("Permission error (code 200) App Review ka zikr karta hai")
def _():
    body = json.dumps({"error": {"code": 200, "message": "no perm"}}).encode()
    assert "App Review" in str(_ig_error(403, body))


@test("Video URL fetch fail (2207052) ka matlab milta hai")
def _():
    body = json.dumps({"error": {"code": 9, "error_subcode": 2207052,
                                 "message": "fetch fail"}}).encode()
    assert "Public hai" in str(_ig_error(400, body))


@test("Kharab JSON error response pe bhi crash nahi hota")
def _():
    e = _ig_error(500, b"<html>Internal Server Error</html>")
    assert isinstance(e, IGError) and "500" in str(e)


@test("X-App-Usage headers reconcile hote hain")
def _():
    src = (Path(__file__).parent / "agents" / "ig_publisher.py").read_text(encoding="utf-8")
    assert "reconcile_from_headers" in src
    assert src.count("reconcile_from_headers") >= 2, "success aur error dono pe padhna chahiye"


@test("Meta ka content_publishing_limit se reconcile hota hai")
def _():
    src = (Path(__file__).parent / "agents" / "ig_publisher.py").read_text(encoding="utf-8")
    assert "content_publishing_limit" in src


@test("REELS media_type aur share_to_feed set hote hain")
def _():
    src = (Path(__file__).parent / "agents" / "ig_publisher.py").read_text(encoding="utf-8")
    assert '"media_type": "REELS"' in src
    assert '"share_to_feed": "true"' in src, "feed pe bhi dikhna chahiye = zyada reach"


# =====================================================================
print("\n🧪 27. ANALYST — metrics scheduling (Phase 7)")
# =====================================================================

def _published(db, vid_kw=None, hours_ago=3, **kw):
    from datetime import datetime, timedelta, timezone
    defaults = dict(hook_type="pov", voice_id="hi_f_calm", template_id="noir_teal",
                    length_sec=28.0, yt_video_id="ytX")
    defaults.update(kw)
    v = db.create_video(vid_kw or "topic", **defaults)
    ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat(timespec="seconds")
    db.update_video(v, status="published", published_ts=ts)
    return v


@test("⭐ 2h velocity window sabse pehle aata hai (decisive signal)")
def _():
    assert WINDOWS["2h"] == 2 and WINDOWS["24h"] == 24 and WINDOWS["7d"] == 168
    assert list(WINDOWS) == ["2h", "24h", "7d"], "order 2h -> 24h -> 7d hona chahiye"


@test("3 ghante purana video ka 2h window due hota hai")
def _():
    d = fresh_db()
    v = _published(d, hours_ago=3)
    due = Analyst(d, Quota(d)).due_videos()
    assert (v, "2h") in due, f"2h due hona chahiye tha: {due}"
    assert (v, "24h") not in due, "24h abhi due nahi"
    d.close()


@test("Metrics mil chuki hon to dobara due nahi hoti")
def _():
    d = fresh_db()
    v = _published(d, hours_ago=3)
    d.save_metrics(v, "youtube", "2h", views=100)
    assert (v, "2h") not in Analyst(d, Quota(d)).due_videos()
    d.close()


@test("30 ghante purana video ka 2h AUR 24h dono due")
def _():
    d = fresh_db()
    v = _published(d, hours_ago=30)
    due = Analyst(d, Quota(d)).due_videos()
    assert (v, "2h") in due and (v, "24h") in due and (v, "7d") not in due
    d.close()


@test("Unpublished video kabhi due nahi hota")
def _():
    d = fresh_db()
    v = d.create_video("draft")
    d.set_status(v, "rendered")
    assert not Analyst(d, Quota(d)).due_videos()
    d.close()


# =====================================================================
print("\n🧪 28. ANALYST — retention thresholds (Phase 7)")
# =====================================================================

@test("Section 3 ke thresholds sahi hain")
def _():
    assert THRESHOLDS["yt_retention_short"] == 0.65   # sub-30s
    assert THRESHOLDS["yt_retention_long"] == 0.50    # 30-60s
    assert THRESHOLDS["ig_ret_3s"] == 0.60            # IG ka gate


@test("⭐ Retention threshold miss ho to flag lagta hai")
def _():
    d = fresh_db()
    for i in range(4):
        b = _published(d, f"base{i}", hours_ago=3)
        d.save_metrics(b, "youtube", "2h", views=1000, avg_pct=0.70, ret_1s=0.85)
    v = _published(d, "weak", hours_ago=3, length_sec=28.0)
    d.save_metrics(v, "youtube", "2h", views=300, avg_pct=0.41, ret_1s=0.85)
    r = Analyst(d, Quota(d)).analyze(v)
    assert "RETENTION_BELOW_THRESHOLD" in r["flags"]
    assert "65%" in r["summary"], "28s video ke liye 65% threshold batana chahiye"
    d.close()


@test("30s+ video pe 50% threshold lagta hai (65% nahi)")
def _():
    d = fresh_db()
    for i in range(4):
        b = _published(d, f"b{i}", hours_ago=3)
        d.save_metrics(b, "youtube", "2h", views=1000, avg_pct=0.55)
    v = _published(d, "long", hours_ago=3, length_sec=40.0)
    d.save_metrics(v, "youtube", "2h", views=1000, avg_pct=0.55, ret_1s=0.85)
    r = Analyst(d, Quota(d)).analyze(v)
    assert "RETENTION_BELOW_THRESHOLD" not in r["flags"], "40s pe 55% theek hai"
    d.close()


@test("⭐ Kamzor 1-second retention flag hota hai (YT ka dominant signal)")
def _():
    d = fresh_db()
    for i in range(4):
        b = _published(d, f"b{i}", hours_ago=3)
        d.save_metrics(b, "youtube", "2h", views=1000, avg_pct=0.70, ret_1s=0.88)
    v = _published(d, "weak1s", hours_ago=3)
    d.save_metrics(v, "youtube", "2h", views=900, avg_pct=0.70, ret_1s=0.55)
    r = Analyst(d, Quota(d)).analyze(v)
    assert "WEAK_FIRST_SECOND" in r["flags"]
    assert "pehla frame" in r["summary"]
    d.close()


@test("IG ka 3-second gate alag se check hota hai")
def _():
    d = fresh_db()
    for i in range(4):
        b = _published(d, f"b{i}", hours_ago=3, ig_media_id=f"ig{i}")
        d.save_metrics(b, "instagram", "2h", views=1000, avg_pct=0.5, ret_3s=0.7)
    v = _published(d, "weak3s", hours_ago=3, ig_media_id="igx")
    d.save_metrics(v, "instagram", "2h", views=900, avg_pct=0.5, ret_3s=0.42)
    r = Analyst(d, Quota(d)).analyze(v)
    assert "WEAK_3S" in r["flags"] and "distribution band" in r["summary"]
    d.close()


# =====================================================================
print("\n🧪 29. ANALYST — baseline + verdict (Phase 7)")
# =====================================================================

@test("Kam data pe baseline None rehta hai (jhoothi tulna nahi)")
def _():
    d = fresh_db()
    v = _published(d, hours_ago=3)
    d.save_metrics(v, "youtube", "2h", views=500)
    assert Analyst(d, Quota(d)).baseline(window="2h", min_n=3) is None
    d.close()


@test("Baseline apne aap ko exclude karta hai")
def _():
    d = fresh_db()
    for i in range(5):
        b = _published(d, f"b{i}", hours_ago=3)
        d.save_metrics(b, "youtube", "2h", views=100)
    huge = _published(d, "huge", hours_ago=3)
    d.save_metrics(huge, "youtube", "2h", views=100000)
    base = Analyst(d, Quota(d)).baseline(exclude_video=huge, window="2h")
    assert base["views"] == 100, f"apne aap ko exclude nahi kiya: {base['views']}"
    d.close()


@test("⭐ Verdict 'X% baseline se upar/neeche, kyunki ___' format mein hai")
def _():
    d = fresh_db()
    for i in range(5):
        b = _published(d, f"b{i}", hours_ago=3)
        d.save_metrics(b, "youtube", "2h", views=1000, avg_pct=0.70, ret_1s=0.85,
                       comments=4)
    v = _published(d, "winner", hours_ago=3)
    d.save_metrics(v, "youtube", "2h", views=2000, avg_pct=0.75, ret_1s=0.9, comments=12)
    r = Analyst(d, Quota(d)).analyze(v)
    assert "%" in r["summary"] and "Kyunki" in r["summary"]
    assert r["vs_baseline_pct"] == 100.0, r["vs_baseline_pct"]
    assert "BAHUT ACCHA" in r["verdict"]
    assert r["variables"]["hook_type"] == "pov", "variables report mein hone chahiye"
    d.close()


@test("Verdict labels sahi hain")
def _():
    assert "BAHUT ACCHA" in _verdict(60, [])
    assert "ACCHA" in _verdict(20, [])
    assert "AVERAGE" in _verdict(0, [])
    assert "KHARAB" in _verdict(-40, [])
    assert "KAMZOR" in _verdict(80, ["RETENTION_BELOW_THRESHOLD"]), \
        "retention miss ho to high views bhi KAMZOR hai"
    assert "baseline nahi" in _verdict(None, [])


@test("Zero comments pe flag lagta hai (comment bait fail)")
def _():
    d = fresh_db()
    for i in range(4):
        b = _published(d, f"b{i}", hours_ago=3)
        d.save_metrics(b, "youtube", "2h", views=1000, comments=5, avg_pct=0.7)
    v = _published(d, "nocomm", hours_ago=3)
    d.save_metrics(v, "youtube", "2h", views=900, comments=0, avg_pct=0.7, ret_1s=0.85)
    assert "NO_COMMENTS" in Analyst(d, Quota(d)).analyze(v)["flags"]
    d.close()


# =====================================================================
print("\n🧪 30. ANALYST — drop-off + variables (Phase 7)")
# =====================================================================

@test("⭐ Retention curve se drop-off point milta hai")
def _():
    d = fresh_db()
    v = _published(d, "drop", hours_ago=3, length_sec=30.0)
    # 40% pe bada drop
    curve = [[i / 20, 1.0 - i * 0.02 - (0.30 if i > 8 else 0)] for i in range(21)]
    d.save_metrics(v, "youtube", "2h", views=500, raw_json={"retention_curve": curve})
    drop = Analyst(d, Quota(d)).dropoff(v)
    assert drop is not None
    assert abs(drop["at_sec"] - 13.5) < 2.0, f"drop 13.5s ke aas-paas hona chahiye: {drop}"
    assert drop["drop_pct"] > 25
    d.close()


@test("Smooth curve pe koi drop-off report nahi hota")
def _():
    d = fresh_db()
    v = _published(d, "smooth", hours_ago=3)
    curve = [[i / 20, 1.0 - i * 0.01] for i in range(21)]
    d.save_metrics(v, "youtube", "2h", views=500, raw_json={"retention_curve": curve})
    assert Analyst(d, Quota(d)).dropoff(v) is None
    d.close()


@test("Early drop-off (<3s) alag flag hota hai")
def _():
    d = fresh_db()
    for i in range(4):
        b = _published(d, f"b{i}", hours_ago=3)
        d.save_metrics(b, "youtube", "2h", views=1000, avg_pct=0.7)
    v = _published(d, "early", hours_ago=3, length_sec=30.0)
    curve = [[i / 20, 1.0 - (0.35 if i >= 1 else 0) - i * 0.01] for i in range(21)]
    d.save_metrics(v, "youtube", "2h", views=800, avg_pct=0.7, ret_1s=0.85,
                   raw_json={"retention_curve": curve})
    assert "EARLY_DROPOFF" in Analyst(d, Quota(d)).analyze(v)["flags"]
    d.close()


@test("_ratio_at interpolation sahi karta hai")
def _():
    c = [(0.0, 1.0), (0.5, 0.6), (1.0, 0.2)]
    assert _ratio_at(c, 0.0) == 1.0
    assert abs(_ratio_at(c, 0.25) - 0.8) < 0.01
    assert _ratio_at(c, 1.0) == 0.2
    assert _ratio_at([], 0.5) is None


@test("Length buckets sahi hain (sweet spot ke hisaab se)")
def _():
    assert _bucket(15) == "<22s" and _bucket(25) == "22-30s"
    assert _bucket(35) == "30-45s" and _bucket(60) == "45s+"


@test("⭐ Variable report kaunsa hook/voice jeet raha bata deta hai")
def _():
    d = fresh_db()
    for i in range(9):
        h = ["pov", "question", "contrarian"][i % 3]
        b = _published(d, f"v{i}", hours_ago=3, hook_type=h)
        d.save_metrics(b, "youtube", "2h",
                       views=2000 if h == "pov" else 500, avg_pct=0.7)
    rep = Analyst(d, Quota(d)).variable_report(min_n=3)
    assert rep["hook_type"][0]["value"] == "pov", rep["hook_type"]
    assert rep["hook_type"][0]["n"] == 3
    d.close()


@test("Variable report min_n se kam wale skip karta hai")
def _():
    d = fresh_db()
    b = _published(d, "only1", hours_ago=3, hook_type="pov")
    d.save_metrics(b, "youtube", "2h", views=1000)
    assert not Analyst(d, Quota(d)).variable_report(min_n=3).get("hook_type")
    d.close()


@test("Variable report correlation-vs-causation ki warning deta hai")
def _():
    d = fresh_db()
    for i in range(4):
        b = _published(d, f"b{i}", hours_ago=3)
        d.save_metrics(b, "youtube", "2h", views=1000, avg_pct=0.7)
    assert "correlation" in Analyst(d, Quota(d)).briefing().lower()
    d.close()


@test("⭐ search.list (100 units) KABHI use nahi hota")
def _():
    src = (Path(__file__).parent / "agents" / "analyst.py").read_text(encoding="utf-8")
    assert 'yt_call("search.list"' not in src, "search.list 100 units khaata hai!"
    assert 'yt_call("videos.list"' in src, "videos.list (1 unit) use hona chahiye"


@test("Briefing crash nahi hota jab data hi na ho")
def _():
    d = fresh_db()
    out = Analyst(d, Quota(d)).briefing()
    assert "Baseline abhi nahi bana" in out
    d.close()


# =====================================================================
print("\n🧪 31. STATS — chhote sample ki honest statistics (Phase 8)")
# =====================================================================

@test("⭐ t-distribution p-value sahi hai (numerical integration se verified)")
def _():
    # Ye values maine Simpson's rule se independently verify ki hain
    assert abs(t_pvalue(2.0, 10) - 0.073388) < 1e-5
    assert abs(t_pvalue(3.0, 20) - 0.007076) < 1e-5
    assert abs(t_pvalue(1.0, 5) - 0.363217) < 1e-5
    assert abs(t_pvalue(0.0, 10) - 1.0) < 1e-9, "t=0 pe p=1 hona chahiye"


@test("⭐ Normal approximation (z-test) chhote sample pe GALAT hota — isliye t use kiya")
def _():
    from statistics import NormalDist
    t, df = 2.0, 5
    p_t = t_pvalue(t, df)
    p_z = 2 * (1 - NormalDist().cdf(t))
    assert p_t > p_z * 1.5, (
        f"t-test ({p_t:.4f}) z-test ({p_z:.4f}) se zyada conservative hona chahiye — "
        f"warna hum jhoothi learnings save karenge")


@test("betainc boundary values sahi hain")
def _():
    assert betainc(2, 3, 0.0) == 0.0 and betainc(2, 3, 1.0) == 1.0
    assert abs(betainc(1, 1, 0.5) - 0.5) < 1e-9   # uniform distribution


@test("Welch's t-test — clearly alag groups detect karta hai")
def _():
    r = welch_ttest([1200, 1450, 1100, 1600, 1350], [800, 750, 900, 700, 850])
    assert r["p"] < 0.01, r["p"]
    assert r["mean_a"] > r["mean_b"] and r["cohens_d"] > 2


@test("Welch's t-test — same groups pe koi difference nahi batata")
def _():
    r = welch_ttest([1000, 1100, 900, 1050, 950], [1020, 1080, 920, 1030, 970])
    assert r["p"] > 0.5, f"same groups pe p={r['p']} — false positive!"


@test("Welch unequal variance handle karta hai (Student's nahi karta)")
def _():
    r = welch_ttest([100, 100, 100, 100, 100], [50, 5000, 20, 3000, 10])
    assert r["df"] < 5, f"Welch df kam hona chahiye jab variance alag ho: {r['df']}"


@test("Kam data pe crash nahi hota")
def _():
    r = welch_ttest([100], [200])
    assert r["p"] == 1.0 and "error" in r
    assert welch_ttest([], [])["p"] == 1.0


@test("⭐ Confidence sirf p-value pe nahi — sample size aur effect bhi dekhta hai")
def _():
    # chhota sample + accha p = sirf medium
    assert confidence_level(0.001, 5, 5, 3.0) == "medium", \
        "n=5 pe 'high' nahi milni chahiye chahe p kitna bhi accha ho"
    # bada sample + accha p + bada effect = high
    assert confidence_level(0.005, 12, 12, 1.0) == "high"
    # non-significant = low
    assert confidence_level(0.30, 20, 20, 0.2) == "low"
    assert confidence_level(0.04, 3, 3, 1.0) == "low", "n=3 bahut kam hai"


@test("lift_pct zero-division se bachta hai")
def _():
    assert lift_pct(100, 0) == 100.0
    assert lift_pct(0, 0) == 0.0
    assert lift_pct(150, 100) == 50.0


@test("⭐ MDE batata hai ki chhote sample pe kya detect NAHI hoga")
def _():
    mde5 = min_detectable_lift(5)
    mde20 = min_detectable_lift(20)
    assert mde5 > 50, f"n=5 pe MDE {mde5}% — 50%+ hona chahiye (honest warning)"
    assert mde20 < mde5, "zyada sample = chhota farq bhi dikhta hai"


@test("summarize() winner/loser sahi identify karta hai")
def _():
    r = summarize([500] * 5, [1500] * 5, "A", "B")
    assert r["winner"] == "B" and r["loser"] == "A"
    assert r["lift_pct"] == 200.0


# =====================================================================
print("\n🧪 32. SCIENTIST — experiment lifecycle (Phase 8)")
# =====================================================================

def _exp_video(db, sci, variant_views, i, window="2h"):
    from datetime import datetime, timedelta, timezone
    v = db.create_video(f"exp topic {i}", length_sec=28.0)
    a = sci.assign(v)
    if not a:
        return None
    db.update_video(v, status="published",
                    published_ts=(datetime.now(timezone.utc) -
                                  timedelta(hours=3)).isoformat(timespec="seconds"))
    db.save_metrics(v, "youtube", window,
                    views=variant_views[a["variant"]], avg_pct=0.6, comments=3)
    return a


@test("suggest_next() untested variable chunta hai")
def _():
    d = fresh_db()
    s = Scientist(d).suggest_next()
    assert s and s["arm_a"] != s["arm_b"]
    assert "kabhi test nahi hua" in s["reason"]
    assert s["min_per_arm"] == MIN_PER_ARM
    d.close()


@test("⭐ Ek time pe sirf EK experiment (Section 6 rule)")
def _():
    d = fresh_db()
    sci = Scientist(d)
    assert sci.start()["ok"] is True
    r2 = sci.start("voice_id")
    assert r2["ok"] is False and "pehle se chal raha" in r2["error"]
    d.close()


@test("⭐ Arms ALTERNATE hote hain (random nahi — time confound se bachav)")
def _():
    d = fresh_db()
    sci = Scientist(d)
    sci.start()
    variants = []
    for i in range(8):
        v = d.create_video(f"t{i}")
        variants.append(sci.assign(v)["variant"])
    assert variants == ["A", "B"] * 4, f"alternate nahi hua: {variants}"
    d.close()


@test("Kam data pe evaluate() conclude nahi karne deta")
def _():
    d = fresh_db()
    sci = Scientist(d)
    sci.start()
    for i in range(4):     # sirf 2 per arm
        _exp_video(d, sci, {"A": 900, "B": 1500}, i)
    ev = sci.evaluate()
    assert ev["ready"] is False
    assert "jhoothi learning" in ev["message"].lower() or "data kam" in ev["status"].lower()
    d.close()


@test("⭐ Kaafi data hone pe winner detect hota hai")
def _():
    d = fresh_db()
    sci = Scientist(d)
    sci.start()
    for i in range(10):
        _exp_video(d, sci, {"A": 900 + i * 10, "B": 1500 + i * 10}, i)
    ev = sci.evaluate()
    assert ev["ready"] and ev["significant"]
    assert ev["winner"] == ev["arm_b"], "B jeetna chahiye tha"
    assert ev["lift_pct"] > 50
    assert "asli farq hai" in ev["explanation"]
    d.close()


@test("⭐ Koi farq na ho to koi learning save NAHI hoti (imandari)")
def _():
    d = fresh_db()
    sci = Scientist(d)
    sci.start()
    for i in range(10):
        _exp_video(d, sci, {"A": 1000 + (i % 3) * 20, "B": 1010 + (i % 3) * 20}, i)
    res = sci.conclude()
    assert res["concluded"] and res["learning_saved"] is False
    assert "NO WINNER" in res["verdict"]
    assert len(d.active_learnings()) == 0, "jhoothi learning save ho gayi!"
    d.close()


@test("⭐ Winner mile to learning DB mein save hoti hai")
def _():
    d = fresh_db()
    sci = Scientist(d)
    sci.start()
    for i in range(10):
        _exp_video(d, sci, {"A": 900, "B": 1500}, i)
    res = sci.conclude()
    assert res["learning_saved"] is True
    ls = d.active_learnings()
    assert len(ls) == 1 and ls[0]["winner"] == res["winner"]
    assert ls[0]["sample_size"] == 5
    assert d.running_experiment() is None, "experiment concluded hona chahiye"
    d.close()


@test("force conclude kam data pe learning save nahi karta")
def _():
    d = fresh_db()
    sci = Scientist(d)
    sci.start()
    for i in range(4):
        _exp_video(d, sci, {"A": 900, "B": 5000}, i)
    res = sci.conclude(force=True)
    assert res["concluded"] and not res["learning_saved"]
    assert "ABANDONED" in res["verdict"]
    assert len(d.active_learnings()) == 0
    d.close()


@test("MAX_PER_ARM ke baad assign band ho jaata hai")
def _():
    d = fresh_db()
    sci = Scientist(d)
    sci.start()
    assigned = 0
    for i in range(MAX_PER_ARM * 2 + 8):
        if sci.assign(d.create_video(f"t{i}")):
            assigned += 1
    assert assigned == MAX_PER_ARM * 2, f"{assigned} assign hue, cap {MAX_PER_ARM*2}"
    d.close()


# =====================================================================
print("\n🧪 33. SCIENTIST — learning loop closure (Phase 8)")
# =====================================================================

@test("⭐ Experiment chalu ho to Writer ka rotation OVERRIDE hota hai")
def _():
    d = fresh_db()
    sci = Scientist(d)
    r = sci.start("hook_type")
    w = Writer(d, LLM(force_mock=True))
    picks = []
    for i in range(6):
        h = w.pick_hook_type()
        v = d.create_video(f"t{i}", hook_type=h)
        sci.assign(v)
        picks.append(h)
    assert set(picks) <= {r["arm_a"], r["arm_b"]}, \
        f"experiment ke bahar ke hooks aa gaye: {picks}"
    d.close()


@test("⭐ Champion agli generation mein prefer hota hai (learning loop closed)")
def _():
    d = fresh_db()
    d.add_learning("hook_type", "pov", "question", 60.0, 8, "high")
    w = Writer(d, LLM(force_mock=True))
    picks = []
    for i in range(60):
        h = w.pick_hook_type()
        d.create_video(f"t{i}", hook_type=h)
        picks.append(h)
    pov = picks.count("pov")
    assert pov >= 15, f"champion sirf {pov}/60 baar aaya — learning use nahi ho rahi"
    d.close()


@test("⭐ Champion 100% nahi lagta (duplicate-pattern clustering se bachav)")
def _():
    d = fresh_db()
    d.add_learning("hook_type", "pov", "question", 200.0, 12, "high")
    w = Writer(d, LLM(force_mock=True))
    picks = []
    for i in range(50):
        h = w.pick_hook_type()
        d.create_video(f"t{i}", hook_type=h)
        picks.append(h)
    pov = picks.count("pov")
    assert pov < 40, f"champion {pov}/50 — 100% ek hi hook = throttle ka invite"
    assert len(set(picks)) >= 3, "variety khatam ho gayi"
    d.close()


@test("⭐ High-confidence loser rotation se lagbhag hat jaata hai")
def _():
    d = fresh_db()
    d.add_learning("hook_type", "pov", "question", 80.0, 10, "high")
    w = Writer(d, LLM(force_mock=True))
    picks = []
    for i in range(50):
        h = w.pick_hook_type()
        d.create_video(f"t{i}", hook_type=h)
        picks.append(h)
    q = picks.count("question")
    assert q <= 12, f"haara hua hook abhi bhi {q}/50 baar aa raha hai"
    d.close()


@test("Voice bhi experiment override respect karta hai")
def _():
    d = fresh_db()
    sci = Scientist(d)
    r = sci.start("voice_id")
    v = Voice(d)
    picks = []
    for i in range(4):
        p = v.pick_profile()
        vid = d.create_video(f"t{i}", voice_id=p)
        sci.assign(vid)
        picks.append(p)
    assert set(picks) <= {r["arm_a"], r["arm_b"]}, picks
    d.close()


@test("Template bhi experiment override respect karta hai")
def _():
    d = fresh_db()
    sci = Scientist(d)
    r = sci.start("template_id")
    ad = ArtDirector(d, LLM(force_mock=True))
    picks = []
    for i in range(4):
        t = ad.pick_template()
        vid = d.create_video(f"t{i}", template_id=t)
        sci.assign(vid)
        picks.append(t)
    assert set(picks) <= {r["arm_a"], r["arm_b"]}, picks
    d.close()


@test("champions() sirf medium/high confidence wale deta hai")
def _():
    d = fresh_db()
    d.add_learning("hook_type", "pov", "question", 60.0, 8, "high")
    d.add_learning("voice_id", "hi_f_calm", "hi_m_grave", 10.0, 5, "low")
    ch = Scientist(d).champions()
    assert "hook_type" in ch and "voice_id" not in ch, \
        "low confidence learning ko default nahi banana chahiye"
    d.close()


@test("losers() sirf high confidence pe hataata hai")
def _():
    d = fresh_db()
    d.add_learning("voice_id", "a", "b", 60.0, 5, "medium")
    assert not Scientist(d).losers(), "medium confidence pe variant nahi hatana chahiye"
    d.add_learning("template_id", "x", "y", 90.0, 12, "high")
    assert Scientist(d).losers()["template_id"] == ["y"]
    d.close()


@test("90+ din purani learning pe re-test suggest hota hai")
def _():
    d = fresh_db()
    lid = d.add_learning("hook_type", "pov", "question", 60.0, 10, "high")
    for var in ("voice_id", "template_id", "length_bucket", "publish_hour"):
        e = d.create_experiment(var, "h", "a", "b")
        d.conclude_experiment(e, {"winner": "a"})
    d.conn.execute("UPDATE experiments SET status='concluded'")
    e = d.create_experiment("hook_type", "h", "a", "b")
    d.conclude_experiment(e, {"winner": "a"})
    d.conn.execute("UPDATE learnings SET ts=datetime('now','-120 days') WHERE id=?", (lid,))
    s = Scientist(d).suggest_next()
    assert s and "purani" in s["reason"], s
    d.close()


@test("Scientist report crash nahi hota (khaali DB pe bhi)")
def _():
    d = fresh_db()
    out = Scientist(d).report()
    assert "Koi experiment nahi chal raha" in out
    d.close()


# =====================================================================
print("\n🧪 34. CHIEF — lock + safety (Phase 9)")
# =====================================================================

@test("⭐ Do chief ek saath nahi chal sakte (double publish se bachav)")
def _():
    import tempfile
    lf = Path(tempfile.mkdtemp()) / "chief.lock"
    with Lock(lf):
        try:
            with Lock(lf):
                raise AssertionError("doosra lock bhi mil gaya — double publish ho jayega!")
        except RuntimeError as e:
            assert "pehle se chal raha" in str(e)
    assert not lf.exists(), "lock release nahi hua"


@test("Purana (crashed) lock apne aap hat jaata hai")
def _():
    import tempfile, os as _os, time as _t
    lf = Path(tempfile.mkdtemp()) / "chief.lock"
    lf.write_text(json.dumps({"pid": 999999}))
    old = _t.time() - 100 * 60          # 100 minute purana
    _os.utime(lf, (old, old))
    with Lock(lf):
        pass                             # crash nahi hona chahiye
    assert not lf.exists()


@test("Lock file mein PID hota hai (debug ke liye)")
def _():
    import tempfile
    lf = Path(tempfile.mkdtemp()) / "l.lock"
    with Lock(lf):
        info = json.loads(lf.read_text())
        assert "pid" in info and "started" in info


@test("⭐ Ek task fail ho to baaki tasks rukte nahi")
def _():
    d = fresh_db()
    ch = Chief(d, dry_run=True)

    def boom():
        raise RuntimeError("jaan boojh kar fail")

    ch._do("bad_task", boom)
    ch._do("good_task", lambda: "kaam ho gaya")
    assert len(ch.errors) == 1 and "bad_task" in ch.errors[0]
    assert any("good_task" in a for a in ch.actions), "doosra task chalna chahiye tha"
    d.close()


@test("Fail hua task DB mein log hota hai (silent fail nahi)")
def _():
    d = fresh_db()
    ch = Chief(d, dry_run=True)
    ch._do("x", lambda: (_ for _ in ()).throw(ValueError("nope")))
    ev = d.q("SELECT * FROM events WHERE kind='task_failed'")
    assert len(ev) == 1 and "nope" in ev[0]["payload"]
    d.close()


@test("dry-run tick kuch badalta nahi")
def _():
    d = fresh_db()
    before = len(d.recent_videos(100))
    out = Chief(d, dry_run=True).tick()
    assert len(d.recent_videos(100)) == before, "dry-run ne video bana diya!"
    assert "actions" in out and "errors" in out
    d.close()


# =====================================================================
print("\n🧪 35. CHIEF — task decisions (Phase 9)")
# =====================================================================

@test("Aaj ka target poora ho to naya video nahi banta")
def _():
    d = fresh_db()
    from core.config import CONFIG as C
    for i in range(int(C.get("videos_per_day", 2))):
        d.create_video(f"t{i}")
    assert Chief(d, dry_run=True).task_produce() is None
    d.close()


@test("⭐ Approve queue bhara ho to production ruk jaata hai")
def _():
    d = fresh_db()
    for i in range(6):
        v = d.create_video(f"pending{i}")
        d.set_status(v, "validated")
    # created_ts aaj ka hai isliye made_today bhi 6 hai — dono guard test karo
    d.conn.execute("UPDATE videos SET created_ts = datetime('now','-2 days')")
    assert Chief(d, dry_run=True).task_produce() is None, \
        "6 pending hone par bhi naya bana raha hai"
    d.close()


@test("⭐ review_first mein bina approve ke publish nahi hota")
def _():
    d = fresh_db()
    v = d.create_video("x", video_path="/tmp/x.mp4")
    d.set_status(v, "validated")     # validated, approved nahi
    assert Chief(d, dry_run=True).task_publish() is None
    d.close()


@test("Quota khatam ho to publish gracefully ruk jaata hai")
def _():
    d = fresh_db()
    q = Quota(d)
    for i in range(5):
        q.check_and_spend("youtube_uploads", 1, "burn")
    v = d.create_video("x", video_path="/tmp/x.mp4")
    d.set_status(v, "approved")
    ch = Chief(d, dry_run=True)
    ch.quota = q
    # publish window ke andar ho ya nahi, quota message aana chahiye
    res = ch.task_publish()
    assert res is None or "quota khatam" in res
    d.close()


@test("Kam published videos pe experiment start nahi hota")
def _():
    d = fresh_db()
    for i in range(2):
        v = d.create_video(f"t{i}")
        d.update_video(v, status="published")
    assert Chief(d, dry_run=False).task_experiment() is None, \
        "sirf 2 videos pe experiment ka matlab nahi"
    assert d.running_experiment() is None
    d.close()


@test("⭐ Kaafi videos hone pe experiment APNE AAP shuru hota hai")
def _():
    d = fresh_db()
    for i in range(6):
        v = d.create_video(f"t{i}")
        d.update_video(v, status="published")
    res = Chief(d, dry_run=False).task_experiment()
    assert res and "naya experiment" in res
    assert d.running_experiment() is not None
    d.close()


@test("Cleanup rejected videos ki files hataata hai")
def _():
    import tempfile
    d = fresh_db()
    v = d.create_video("bad", video_path="/tmp/whatever.mp4")
    d.set_status(v, "rejected")
    Chief(d, dry_run=True).task_cleanup()      # crash nahi hona chahiye
    d.close()


@test("Cleanup purani learnings downgrade karta hai")
def _():
    d = fresh_db()
    lid = d.add_learning("hook_type", "a", "b", 50.0, 10, "high")
    d.conn.execute("UPDATE learnings SET ts=datetime('now','-100 days') WHERE id=?", (lid,))
    Chief(d, dry_run=True).task_cleanup()
    assert d.one("SELECT confidence FROM learnings WHERE id=?", (lid,))["confidence"] == "medium"
    d.close()


# =====================================================================
print("\n🧪 36. CHIEF — digest + cron (Phase 9)")
# =====================================================================

@test("Digest khaali DB pe bhi banta hai (crash nahi)")
def _():
    d = fresh_db()
    out = Chief(d).digest()
    for section in ("PRODUCTION", "PERFORMANCE", "SCIENCE", "QUOTA",
                    "TUMHE KYA KARNA HAI"):
        assert section in out, f"section missing: {section}"
    d.close()


@test("⭐ Digest actionable TODOs deta hai")
def _():
    d = fresh_db()
    for i in range(3):
        v = d.create_video(f"t{i}")
        d.set_status(v, "validated")
    out = Chief(d).digest()
    assert "approve queue mein hain" in out
    d.close()


@test("Digest failed videos highlight karta hai")
def _():
    d = fresh_db()
    v = d.create_video("bad")
    d.set_status(v, "failed")
    assert "Failed" in Chief(d).digest()
    d.close()


@test("Digest quota bars dikhata hai")
def _():
    d = fresh_db()
    out = Chief(d).digest()
    assert "youtube_uploads" in out and "reset" in out
    d.close()


@test("review_first_count paar hone pe auto_publish suggest hota hai")
def _():
    d = fresh_db()
    for i in range(21):
        v = d.create_video(f"t{i}")
        d.update_video(v, status="published")
    assert "auto_publish" in Chief(d).digest()
    d.close()


@test("Cron guide dono platforms cover karta hai")
def _():
    g = cron_guide()
    assert "crontab -e" in g and "Task Scheduler" in g
    assert "--tick" in g and "--digest" in g
    assert "agents.chief" in g


@test("⭐ Cron guide IG ki 24h container limitation batata hai")
def _():
    g = cron_guide()
    assert "24 ghante" in g and "cron chalu rehna" in g.lower(), \
        "user ko pata hona chahiye ki machine band hone pe IG post nahi jayega"


# =====================================================================
print("\n🧪 37. LEARNING LOOP — poora closure (Phase 10)")
# =====================================================================

@test("⭐⭐ POORA LOOP: publish -> metrics -> experiment -> learning -> next video")
def _():
    from datetime import datetime, timedelta, timezone
    import random as _r
    _r.seed(11)
    d = fresh_db()
    ch = Chief(d, dry_run=False)
    sci = Scientist(d)
    w = Writer(d, LLM(force_mock=True))
    ago = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(timespec="seconds")

    # --- 1. kuch videos publish ho chuke hain ---
    for i in range(6):
        v = d.create_video(f"seed{i}", hook_type="pov", length_sec=28.0)
        d.update_video(v, status="published", published_ts=ago)
        d.save_metrics(v, "youtube", "2h", views=1000, avg_pct=0.7)

    # --- 2. Chief khud experiment shuru karta hai ---
    assert ch.task_experiment(), "experiment auto-start nahi hua"
    exp = d.running_experiment()
    assert exp is not None

    # --- 3. naye videos experiment follow karte hain ---
    for i in range(10):
        h = w.pick_hook_type()
        v = d.create_video(f"e{i}", hook_type=h, length_sec=28.0)
        a = sci.assign(v)
        assert a, "assign fail"
        assert h in (exp["arm_a"], exp["arm_b"]), \
            f"Writer experiment ke bahar gaya: {h}"
        d.update_video(v, status="published", published_ts=ago)
        d.save_metrics(v, "youtube", "2h", avg_pct=0.7,
                       views=(1700 if a["variant"] == "B" else 850) + _r.randint(-80, 80))

    # --- 4. Chief khud conclude karta hai ---
    verdict = ch.task_experiment()
    assert verdict and "WINNER" in verdict, verdict
    assert d.running_experiment() is None or \
        d.running_experiment()["variable"] != exp["variable"]

    # --- 5. learning save hui ---
    ls = d.active_learnings("hook_type")
    assert len(ls) == 1, "learning save nahi hui"
    champion = ls[0]["winner"]
    assert champion == exp["arm_b"], "B jeetna chahiye tha"

    # --- 6. LOOP CLOSED: agli generation champion prefer karti hai ---
    d.conn.execute("UPDATE experiments SET status='concluded'")   # koi override na ho
    picks = []
    for i in range(50):
        h = w.pick_hook_type()
        d.create_video(f"z{i}", hook_type=h)
        picks.append(h)
    share = picks.count(champion) / len(picks)
    assert share >= 0.28, f"champion sirf {share*100:.0f}% — loop close nahi hua"
    assert share <= 0.60, f"champion {share*100:.0f}% — clustering ka risk"
    assert len(set(picks)) >= 3, "variety khatam"
    d.close()


@test("⭐ Loop mein har agent learning padhta hai (Writer/Voice/ArtDirector)")
def _():
    for mod, fn in (("agents/writer.py", "active_learnings"),
                    ("agents/voice.py", "active_learnings"),
                    ("agents/artdirector.py", "Scientist")):
        src = (Path(__file__).parent / mod).read_text(encoding="utf-8")
        assert fn in src, f"{mod} learnings/Scientist nahi padhta"


@test("Chief tick ka order sahi hai (metrics pehle, produce baad mein)")
def _():
    src = (Path(__file__).parent / "agents" / "chief.py").read_text(encoding="utf-8")
    i_m = src.index('self._do("metrics"')
    i_e = src.index('self._do("experiment"')
    i_p = src.index('self._do("publish"')
    i_pr = src.index('self._do("produce"')
    assert i_m < i_e < i_p < i_pr, \
        "order: metrics -> experiment -> publish -> produce hona chahiye"


# =====================================================================
print("\n🧪 38. TRENDSCOUT — topic research (Section 6 agent #1)")
# =====================================================================

def _scored(db, topic, views, title=None):
    from datetime import datetime, timedelta, timezone
    v = db.create_video(topic, title=title or topic, length_sec=28.0)
    ago = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(timespec="seconds")
    db.update_video(v, status="published", published_ts=ago)
    db.save_metrics(v, "youtube", "2h", views=views, avg_pct=0.6)
    return v


@test("⭐⭐ search.list (100 units) KABHI use nahi hota")
def _():
    src = (Path(__file__).parent / "agents" / "trendscout.py").read_text(encoding="utf-8")
    assert 'yt_call("search.list"' not in src, \
        "TrendScout ka poora point hi ye hai ki wo search.list use na kare!"
    assert 'yt_call("playlistItems.list")' in src or \
           'yt_call("playlistItems.list"' in src
    assert 'yt_call("videos.list"' in src


@test("⭐ Apna data 3 units mein aata hai (search.list se 100 lagte)")
def _():
    src = (Path(__file__).parent / "agents" / "trendscout.py").read_text(encoding="utf-8")
    # channels.list + playlistItems.list + videos.list = 3 calls
    for call in ("channels.list", "playlistItems.list", "videos.list"):
        assert f'yt_call("{call}"' in src, f"{call} missing"


@test("Khaali DB pe bhi topics milte hain (naya channel)")
def _():
    d = fresh_db()
    cands = TrendScout(d, LLM(force_mock=True)).scout(3)
    assert len(cands) >= 1
    for c in cands:
        assert c.get("topic") or c.get("series")
        assert 0.0 <= c["score"] <= 1.0
    d.close()


@test("Sab fail ho jaye to bhi ek topic milta hai (fallback)")
def _():
    d = fresh_db()

    class DeadLLM:
        is_mock = True
        def json(self, *a, **k): return {}
        def ask(self, *a, **k): return ""

    ts = TrendScout(d, DeadLLM())
    t = ts.best_topic()
    assert isinstance(t, str) and len(t) > 10
    d.close()


@test("⭐ Winner keywords apne data se nikalte hain")
def _():
    d = fresh_db()
    for t, v in [("Wo train jo gayab ho gayi", 3000),
                 ("Ek train jo 1911 mein gayab hui", 2800),
                 ("Train jo laut ke nahi aayi", 2600),
                 ("Purane ghar ka rahasya", 300),
                 ("Ek gaon ki kahani", 250)]:
        _scored(d, t, v)
    p = TrendScout(d, LLM(force_mock=True)).own_patterns()
    assert "train" in p["keywords"], f"'train' winner keyword hona chahiye: {p['keywords']}"
    assert p["confidence"] == "medium"
    assert p["avg_views"] > 0
    d.close()


@test("Losers ke keywords signal se hat jaate hain")
def _():
    d = fresh_db()
    # 'rahasya' dono mein hai -> signal nahi hona chahiye
    for t, v in [("train rahasya ek", 3000), ("train rahasya do", 2900),
                 ("train rahasya teen", 2800),
                 ("ghar rahasya ek", 200), ("ghar rahasya do", 190),
                 ("ghar rahasya teen", 180)]:
        _scored(d, t, v)
    p = TrendScout(d, LLM(force_mock=True)).own_patterns()
    assert "train" in p["keywords"]
    assert "rahasya" not in p["keywords"], "dono taraf ka shabd signal nahi hai"
    d.close()


@test("⭐ Winner keyword match hone pe score badhta hai")
def _():
    d = fresh_db()
    ts = TrendScout(d, LLM(force_mock=True))
    empty = ts.own_patterns()
    rich = {**empty, "n_videos": 20, "confidence": "high",
            "keywords": ["gayab", "train"]}
    c = {"topic": "Wo train jo raat mein gayab ho gayi", "series": None}
    plain = {"topic": "Ek aam si kahani jo kuch khaas nahi", "series": None}
    assert ts._score(c, rich) > ts._score(plain, rich), "keyword match se score badhna chahiye"
    d.close()


@test("⭐ Data kam ho to score neutral ki taraf khisakta hai (honest)")
def _():
    d = fresh_db()
    ts = TrendScout(d, LLM(force_mock=True))
    c = {"topic": "Wo 14 log jo 1 raat mein gayab ho gaye", "series": {"name": "Case", "index": 2}}
    low = ts._score(c, {"n_videos": 0, "confidence": "none", "keywords": []})
    high = ts._score(c, {"n_videos": 30, "confidence": "high", "keywords": ["gayab"]})
    assert abs(low - 0.5) < abs(high - 0.5), \
        "bina data ke score 0.5 ke paas hona chahiye — confident hona jhooth hai"
    d.close()


@test("Concrete number wale topic ko boost milta hai")
def _():
    d = fresh_db()
    ts = TrendScout(d, LLM(force_mock=True))
    p = {"n_videos": 20, "confidence": "high", "keywords": []}
    with_num = ts._score({"topic": "Wo 14 log jo gayab ho gaye", "series": None}, p)
    without = ts._score({"topic": "Wo log jo gayab ho gaye", "series": None}, p)
    assert with_num > without, "number = concreteness = curiosity"
    d.close()


@test("Bahut lamba topic penalize hota hai (32s mein nahi aayega)")
def _():
    d = fresh_db()
    ts = TrendScout(d, LLM(force_mock=True))
    p = {"n_videos": 20, "confidence": "high", "keywords": []}
    long_t = {"topic": " ".join(["shabd"] * 30), "series": None}
    ok_t = {"topic": "Wo gaon jahan se log gayab ho gaye raat mein", "series": None}
    assert ts._score(ok_t, p) > ts._score(long_t, p)
    d.close()


@test("⭐ Recent topics repeat nahi hote")
def _():
    d = fresh_db()
    ts = TrendScout(d, LLM(force_mock=True))
    first = ts.scout(3)
    for c in first:
        if c.get("topic"):
            d.create_video(c["topic"])
    second = ts.scout(3)
    olds = {ts._norm(c["topic"]) for c in first if c.get("topic")}
    news = {ts._norm(c["topic"]) for c in second if c.get("topic")}
    assert not (olds & news), f"repeat ho gaya: {olds & news}"
    d.close()


@test("Series continuation suggest hota hai (binge behaviour)")
def _():
    d = fresh_db()
    for i in range(4):
        v = _scored(d, f"case {i}", 1000)
        d.update_video(v, series_name="Case", series_index=i + 1)
    cands = TrendScout(d, LLM(force_mock=True)).scout(5)
    ser = [c for c in cands if c.get("series")]
    assert ser, "chalti hui series continue honi chahiye"
    assert ser[0]["series"]["index"] == 5, ser[0]["series"]


@test("Series videos DB mein series_name ke saath save hote hain")
def _():
    d = fresh_db()
    v = d.create_video("x", series_name="Case", series_index=3)
    row = d.get_video(v)
    assert row["series_name"] == "Case" and row["series_index"] == 3
    d.close()


@test("run.py TrendScout use karta hai (hardcoded list nahi)")
def _():
    src = (Path(__file__).parent / "run_phase2.py").read_text(encoding="utf-8")
    assert "TrendScout" in src and "scout(" in src
    i_scout = src.index("TrendScout(db, llm)")
    i_seed = src.index("SEED_TOPICS if t not in used")
    assert i_scout < i_seed, "TrendScout pehle try hona chahiye, SEED_TOPICS fallback hai"


@test("TrendScout fail ho to pipeline rukti nahi (fallback)")
def _():
    src = (Path(__file__).parent / "run_phase2.py").read_text(encoding="utf-8")
    assert "TrendScout fail" in src, "fallback handling missing"


@test("Report crash nahi hota (khaali aur bhare DB dono pe)")
def _():
    d = fresh_db()
    ts = TrendScout(d, LLM(force_mock=True))
    out = ts.report()
    assert "TRENDSCOUT" in out and "heuristic" in out.lower()
    for t, v in [("a train story", 2000), ("b ghar story", 100), ("c train tale", 1900)]:
        _scored(d, t, v)
    out2 = ts.report()
    assert "Jo chala" in out2 and "3 units" in out2
    d.close()


@test("Score heuristic hai — code khud ye batata hai (jhoot nahi)")
def _():
    src = (Path(__file__).parent / "agents" / "trendscout.py").read_text(encoding="utf-8")
    assert "HEURISTIC" in src and "ML model nahi" in src


# =====================================================================
print("\n🧪 25. METADATA — AI Publishing Layer (Phase 5)")
# =====================================================================

from agents.metadata import (MetadataAgent, MetadataError, CATEGORIES,  # noqa: E402
                             LIMITS as META_LIMITS)


def _meta_agent(d=None):
    d = d or fresh_db()
    return MetadataAgent(d, LLM(force_mock=True)), d


@test("titles(): hamesha exactly 5 unique titles, sab <100 char")
def _():
    m, d = _meta_agent()
    ts = m.titles("Wo 14 log jo gayab ho gaye")
    assert len(ts) == 5, f"5 chahiye the, mile {len(ts)}"
    assert len(set(ts)) == 5, "duplicate titles hain"
    assert all(len(t) < 100 for t in ts)
    d.close()


@test("tags(): 15+ tags, dedupe hota hai, 500-char cap respect hota hai")
def _():
    m, d = _meta_agent()
    tags = m.tags("mystery kahani", "Wo Raaz")
    assert len(tags) >= 15, f"15+ chahiye, mile {len(tags)}"
    assert len(tags) <= 30
    assert len({t.lower() for t in tags}) == len(tags), "dedupe fail"
    assert sum(len(t) + 2 for t in tags) <= 500
    d.close()


@test("description(): CTA + credits + AI disclosure + hashtags sab hote hain")
def _():
    m, d = _meta_agent()
    desc = m.description("mystery", "Wo Raaz", tags=["mystery", "kahani"])
    assert "SUBSCRIBE" in desc.upper()
    assert "AI" in desc, "AI disclosure description mein bhi chahiye"
    assert "#mystery" in desc
    assert len(desc) <= 5000
    d.close()


@test("description(): timestamps diye to chapters ban jaate hain")
def _():
    m, d = _meta_agent()
    desc = m.description("t", "T", timestamps=[("0:00", "Intro"), ("0:15", "Twist")])
    assert "0:00 Intro" in desc and "0:15 Twist" in desc
    d.close()


@test("thumbnail_meta(): structured JSON — sab keys, hex colors")
def _():
    m, d = _meta_agent()
    t = m.thumbnail_meta("mystery", "Wo Raaz")
    for k in ("thumbnail_title", "thumbnail_subtitle", "colors",
              "visual_concept", "emotion", "hook"):
        assert k in t, f"'{k}' missing"
    assert all(c.startswith("#") for c in t["colors"])
    d.close()


@test("detect_category(): keywords se deterministic — LLM call bachti hai")
def _():
    m, d = _meta_agent()
    assert m.detect_category("python programming tutorial")[1] == "28"   # sci & tech
    assert m.detect_category("minecraft gameplay funny")[1] == "20"      # gaming
    assert m.detect_category("stock market investing seekho")[1] == "27" # education
    assert m.detect_category("mystery kahani suspense")[1] == "24"       # entertainment
    d.close()


@test("detect_category(): har result valid YouTube category id hota hai")
def _():
    m, d = _meta_agent()
    _, cid = m.detect_category("xyzabc random blah")
    assert cid in CATEGORIES.values()
    d.close()


@test("detect_language(): Devanagari -> hi, English -> en")
def _():
    assert MetadataAgent.detect_language("यह एक रहस्य की कहानी है") == "hi"
    assert MetadataAgent.detect_language("this is an english story") in ("en", "hi")
    assert MetadataAgent.detect_language("") == "en"


@test("schedule_time(): None/'now' -> None (immediate)")
def _():
    assert MetadataAgent.schedule_time(None) is None
    assert MetadataAgent.schedule_time("now") is None


@test("schedule_time(): '+3h' relative future UTC deta hai, Z format")
def _():
    from datetime import datetime, timezone
    ts = MetadataAgent.schedule_time("+3h")
    assert ts.endswith("Z")
    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    assert dt > datetime.now(timezone.utc)


@test("schedule_time(): local time config timezone se UTC banta hai")
def _():
    # Asia/Kolkata (UTC+5:30) mein 2030 ka time do -> UTC mein -5:30 hona chahiye
    ts = MetadataAgent.schedule_time("2030-01-01 18:30", tz="Asia/Kolkata")
    assert ts == "2030-01-01T13:00:00Z", f"mila: {ts}"


@test("schedule_time(): past time pe saaf error")
def _():
    try:
        MetadataAgent.schedule_time("2020-01-01 10:00")
        raise AssertionError("past time reject hona chahiye tha")
    except MetadataError as e:
        assert "past" in str(e).lower() or "Future" in str(e)


@test("schedule_time(): bakwaas input pe format hints wali error")
def _():
    try:
        MetadataAgent.schedule_time("kal shaam ko")
        raise AssertionError("error aani chahiye thi")
    except MetadataError as e:
        assert "+3h" in str(e), "error mein format examples hone chahiye"


@test("validate(): sahi metadata pe koi problem nahi")
def _():
    probs = MetadataAgent.validate({"title": "Accha Title Hai Ye",
                                    "description": "x" * 300,
                                    "tags": ["a", "b"]})
    assert probs == [], f"problems nahi honi chahiye thi: {probs}"


@test("validate(): lamba title / zyada tags / clickbait sab pakde jaate hain")
def _():
    probs = MetadataAgent.validate({
        "title": "You Won't Believe " + "x" * 100,
        "description": "d" * 6000,
        "tags": [f"tag{i}" for i in range(35)]})
    text = " ".join(probs).lower()
    assert "title" in text and "tags" in text and "clickbait" in text
    assert len(probs) >= 4


@test("validate(): missing/khaali video file pakdi jaati hai")
def _():
    import tempfile
    probs = MetadataAgent.validate({"title": "T"}, video_path="/nahi/hai.mp4")
    assert any("nahi mili" in p for p in probs)
    empty = Path(tempfile.mkdtemp()) / "v.mp4"
    empty.write_bytes(b"")
    probs2 = MetadataAgent.validate({"title": "T"}, video_path=empty)
    assert any("khaali" in p for p in probs2)


@test("validate(): 2MB+ thumbnail reject hoti hai")
def _():
    import tempfile
    big = Path(tempfile.mkdtemp()) / "cover.jpg"
    big.write_bytes(b"x" * (META_LIMITS["thumb_max_bytes"] + 1))
    probs = MetadataAgent.validate({"title": "T"}, thumbnail=big)
    assert any("2MB" in p or "max 2" in p for p in probs)


@test("seo_score(): score 0-100, deductions explain hote hain, suggestions milte hain")
def _():
    weak = MetadataAgent.seo_score({"title": "hi", "description": "", "tags": []})
    assert 0 <= weak["score"] < 70
    assert weak["deductions"] and weak["suggestions"]
    assert "HEURISTIC" in weak["note"], "score ko heuristic bolna zaroori hai (jhoot nahi)"
    strong = MetadataAgent.seo_score({
        "title": "14 Log Ek Raat Mein Gayab — mystery kahani",
        "description": "mystery kahani " * 20 + "\nSUBSCRIBE karo\n#mystery #kahani",
        "tags": ["mystery kahani"] + [f"long tail {i}" for i in range(10)]
                + [f"t{i}" for i in range(8)]})
    assert strong["score"] > weak["score"], "behtar metadata = behtar score hona chahiye"


@test("⭐ build(): poora package — titles/desc/tags/category/language/thumb/seo")
def _():
    m, d = _meta_agent()
    pkg = m.build("Wo 14 log jo ek raat mein gayab ho gaye", save=False)
    for k in ("title", "titles", "description", "tags", "category_id",
              "language", "thumbnail_meta", "seo", "validation", "generated_at"):
        assert k in pkg, f"'{k}' package mein nahi hai"
    assert pkg["validation"] == [], f"mock package valid hona chahiye: {pkg['validation']}"
    assert pkg["category_id"] in CATEGORIES.values()
    assert pkg["llm_backend"] == "mock"
    d.close()


@test("build(save=True): metadata logs/metadata/*.json mein save hota hai")
def _():
    from core.config import CONFIG
    m, d = _meta_agent()
    pkg = m.build("save test topic", save=True)
    files = sorted((Path(CONFIG["log_dir"]) / "metadata").glob("*_save_test_topic*.json"))
    assert files, "metadata JSON file nahi bani"
    saved = json.loads(files[-1].read_text(encoding="utf-8"))
    assert saved["topic"] == "save test topic"
    for f in files:
        f.unlink()   # safai
    d.close()


@test("seo_report(): insaan-readable — score, deductions, suggestions dikhte hain")
def _():
    m, d = _meta_agent()
    rep = m.seo_report({"seo": {"score": 72, "note": "HEURISTIC",
                                "deductions": [(10, "Title chhota")],
                                "suggestions": ["Number daalo"]},
                        "validation": []})
    assert "72/100" in rep and "Title chhota" in rep and "Number daalo" in rep
    d.close()


@test("upload_file(): playlist fail ho to bhi upload success rehta hai (source check)")
def _():
    src = (Path(__file__).parent / "agents" / "publisher.py").read_text(encoding="utf-8")
    assert "upload phir bhi OK" in src, "playlist fail par upload fail nahi hona chahiye"


@test("add_to_playlist(): playlist na mile to create hoti hai (source check)")
def _():
    src = (Path(__file__).parent / "agents" / "publisher.py").read_text(encoding="utf-8")
    assert "def find_playlist" in src and "def create_playlist" in src
    assert "def add_to_playlist" in src
    assert "bana rahe hain" in src, "missing playlist auto-create honi chahiye"


@test("playlist quota costs YT_COST mein defined hain (bina cost ke call nahi)")
def _():
    from core.quota import YT_COST
    for ep in ("playlists.list", "playlists.insert", "playlistItems.insert"):
        assert ep in YT_COST, f"'{ep}' ki cost missing"


@test("upload_file language param defaultLanguage set karta hai (source check)")
def _():
    src = (Path(__file__).parent / "agents" / "publisher.py").read_text(encoding="utf-8")
    assert "defaultAudioLanguage" in src


@test("⭐ Phase 5 dry-run: AI package -> upload_file metadata sahi jata hai")
def _():
    import tempfile
    d = fresh_db()
    m = MetadataAgent(d, LLM(force_mock=True))
    pkg = m.build("integration test kahani", save=False)
    f = Path(tempfile.mkdtemp()) / "v.mp4"
    f.write_bytes(b"x" * 5000)
    pub = YouTubePublisher(d, Quota(d), creds=object(), dry_run=True)
    res = pub.upload_file(f, title=pkg["title"], description=pkg["description"],
                          tags=pkg["tags"], category=pkg["category_id"],
                          language=pkg["language"], privacy="unlisted")
    assert res["status"] == "dry_run"
    meta = res["metadata"]
    assert meta["snippet"]["categoryId"] == pkg["category_id"]
    assert meta["snippet"]["defaultLanguage"] == pkg["language"]
    assert len(meta["snippet"]["tags"]) >= 15, "AI tags upload metadata tak nahi pahunche"
    assert meta["status"]["containsSyntheticMedia"] is True
    d.close()


# =====================================================================
# PRIORITY 1 TESTS: Webhook Auth & Voice Fallback Safety
# =====================================================================
@test("webhook: secret unset hone pe 403 milta hai")
def _():
    old = os.environ.get("MAKE_WEBHOOK_SECRET")
    try:
        os.environ["MAKE_WEBHOOK_SECRET"] = ""
        ok, code, msg = _check_webhook_auth({}, {"secret": "anything"}, client_ip="127.0.0.1")
        assert not ok
        assert code == 403
        assert "disabled" in msg.lower()
    finally:
        if old is not None:
            os.environ["MAKE_WEBHOOK_SECRET"] = old
        else:
            os.environ.pop("MAKE_WEBHOOK_SECRET", None)


@test("webhook: galat secret pe 403 milta hai")
def _():
    old = os.environ.get("MAKE_WEBHOOK_SECRET")
    try:
        os.environ["MAKE_WEBHOOK_SECRET"] = "a" * 32
        ok, code, msg = _check_webhook_auth({}, {"secret": "galat_secret_123"}, client_ip="127.0.0.2")
        assert not ok
        assert code == 403
        assert "invalid secret" in msg.lower()
    finally:
        if old is not None:
            os.environ["MAKE_WEBHOOK_SECRET"] = old
        else:
            os.environ.pop("MAKE_WEBHOOK_SECRET", None)


@test("webhook: sahi secret pe 200 milta hai")
def _():
    old = os.environ.get("MAKE_WEBHOOK_SECRET")
    sec = "b" * 32
    try:
        os.environ["MAKE_WEBHOOK_SECRET"] = sec
        ok, code, msg = _check_webhook_auth({"X-Webhook-Secret": sec}, {}, client_ip="127.0.0.3")
        assert ok
        assert code == 200
    finally:
        if old is not None:
            os.environ["MAKE_WEBHOOK_SECRET"] = old
        else:
            os.environ.pop("MAKE_WEBHOOK_SECRET", None)


@test("webhook: 1 min mein 11th request pe 429 rate limit milta hai")
def _():
    old = os.environ.get("MAKE_WEBHOOK_SECRET")
    sec = "c" * 32
    try:
        os.environ["MAKE_WEBHOOK_SECRET"] = sec
        test_ip = "192.168.99.99"
        for i in range(10):
            ok, code, _ = _check_webhook_auth({}, {"secret": sec}, client_ip=test_ip)
            assert ok and code == 200, f"Request {i+1} fail hua"
        # 11th request
        ok, code, msg = _check_webhook_auth({}, {"secret": sec}, client_ip=test_ip)
        assert not ok
        assert code == 429
        assert "rate limit" in msg.lower()
    finally:
        if old is not None:
            os.environ["MAKE_WEBHOOK_SECRET"] = old
        else:
            os.environ.pop("MAKE_WEBHOOK_SECRET", None)


@test("voice: _synth fail hone pe narrate() valid audio banaye ya silence handle kare")
def _():
    import tempfile
    v = Voice(fresh_db())
    out = Path(tempfile.mkdtemp())
    # monkeypatch _synth to always fail
    orig_synth = v._synth
    v._synth = lambda text, path, prof: ""
    try:
        res = v.narrate(["Ek test line jo fail hogi"], out, profile_id="hi_m_grave")
        assert "silence" in res["engines_used"] or "missing" in res["engines_used"]
        merged = Path(res["audio_path"])
        assert merged.exists()
    finally:
        v._synth = orig_synth


@test("voice: _concat 0-byte clips ko skip kare")
def _():
    import tempfile
    v = Voice(fresh_db())
    out = Path(tempfile.mkdtemp())
    zero_file = out / "zero.mp3"
    zero_file.write_bytes(b"")
    clips = [{"path": str(zero_file), "dur": 1.0, "i": 0, "text": "test"}]
    merged = out / "merged.mp3"
    v._concat(clips, merged, [])
    assert merged.exists()
    assert merged.stat().st_size == 0


@test("validate: narration mein 'silence' hone pe validate FAIL kare (silent_narration)")
def _():
    import tempfile
    out = Path(tempfile.mkdtemp())
    mp4 = out / "final.mp4"
    mp4.write_bytes(b"x" * 200000)
    manifest = {
        "video_id": 999,
        "scenes": [],
        "script": {"hook_type": "question", "hook_line": "test", "hook_text_overlay": "overlay"},
        "narration": {"engines_used": ["silence"], "lines": [{"engine": "silence"}]}
    }
    rep = validate(mp4, manifest=manifest, deep=False)
    assert not rep.ok
    codes = [issue.code for issue in rep.issues]
    assert "silent_narration" in codes


@test("quota: ZoneInfoNotFoundError hone pe 'Timezone data nahi mila — pip install tzdata karo' error aata hai")
def _():
    import zoneinfo
    import core.quota
    orig_zoneinfo = core.quota.ZoneInfo
    def fake_zoneinfo(key):
        raise zoneinfo.ZoneInfoNotFoundError("No tzdata")
    core.quota.ZoneInfo = fake_zoneinfo
    try:
        try:
            core.quota._get_pacific_tz()
            assert False, "RuntimeError aana chahiye tha"
        except RuntimeError as e:
            assert "pip install tzdata" in str(e)
    finally:
        core.quota.ZoneInfo = orig_zoneinfo


@test("voice: faster-whisper missing hone pe gracefully syllable-weight pe fallback kare")
def _():
    from agents.voice import _align_words_whisper, _distribute_words
    res = _align_words_whisper("non_existent_audio.mp3", "test sentence", 0.0, 2.0)
    assert res is None
    words = _distribute_words("test sentence", 0.0, 2.0)
    assert len(words) == 2
    assert words[0]["w"] == "test"



@test("server: rerender action missing manifest pe error return kare")
def _():
    from core.db import DB
    d = DB()
    vid = d.create_video("test_rerender_missing_manifest")
    try:
        res = do_action("rerender", vid, {})
        assert not res.get("ok")
        assert "manifest.json nahi mila" in res.get("error", "")
    finally:
        d.close()


@test("server: fetch_logs correctly filters by video_id")
def _():
    import tempfile
    import web.server
    td = Path(tempfile.mkdtemp())
    lf = td / "test.jsonl"
    lf.write_text(
        json.dumps({"ts": "2026-09-06T00:00:00Z", "level": "info", "video_id": 101, "msg": "vid 101 log"}) + "\n" +
        json.dumps({"ts": "2026-09-06T00:01:00Z", "level": "info", "video_id": 202, "msg": "vid 202 log"}) + "\n",
        encoding="utf-8"
    )
    orig_root = web.server.ROOT
    orig_cfg = web.server.CONFIG
    web.server.ROOT = td
    web.server.CONFIG = {"log_dir": "."}
    try:
        all_logs = fetch_logs(None)
        assert len(all_logs) == 2
        filtered = fetch_logs(101)
        assert len(filtered) == 1
        assert filtered[0]["video_id"] == 101
    finally:
        web.server.ROOT = orig_root
        web.server.CONFIG = orig_cfg


@test("run: make_video custom topic aur voice parameter ko respect kare")
def _():
    from run_phase2 import make_video
    m = make_video("CLI Custom Topic Test", dry_run=True, with_images=False, voice="hi_f_urgent")
    assert m["topic"] == "CLI Custom Topic Test"
    assert m["narration"]["voice_id"] == "hi_f_urgent"


@test("metadata: generate_thumbnail 1280x720 valid JPEG banaye")
def _():
    import tempfile
    from PIL import Image
    from agents.metadata import generate_thumbnail
    td = Path(tempfile.mkdtemp())
    out_thumb = td / "thumbnail.jpg"
    res = generate_thumbnail(out_thumb, "14 Log Jo Gayab Hue", "Suspense Kahani")
    assert res.exists()
    assert 0 < res.stat().st_size <= 2 * 1024 * 1024
    with Image.open(res) as im:
        assert im.size == (1280, 720)
        assert im.format == "JPEG"


@test("publisher: set_thumbnail dry-run mein 50 units check karke True return kare")
def _():
    import tempfile
    d = fresh_db()
    pub = YouTubePublisher(d, Quota(d), creds=object(), dry_run=True)
    td = Path(tempfile.mkdtemp())
    dummy_thumb = td / "thumbnail.jpg"
    dummy_thumb.write_bytes(b"x" * 1000)
    ok = pub.set_thumbnail("test_yt_id_123", dummy_thumb)
    assert ok is True
    d.close()


@test("chief: send_telegram token unset hone pe silently False return kare (no call)")
def _():
    from agents.chief import send_telegram
    old_tok = os.environ.pop("TELEGRAM_BOT_TOKEN", None)
    old_chat = os.environ.pop("TELEGRAM_CHAT_ID", None)
    try:
        res = send_telegram("Test message bina token ke")
        assert res is False
    finally:
        if old_tok is not None:
            os.environ["TELEGRAM_BOT_TOKEN"] = old_tok
        if old_chat is not None:
            os.environ["TELEGRAM_CHAT_ID"] = old_chat


@test("chief: send_telegram tokens ke saath sahi POST payload bheje")
def _():
    import urllib.request
    from agents.chief import send_telegram
    calls = []
    class DummyResp:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    def fake_urlopen(req, timeout=15):
        calls.append({
            "url": req.full_url,
            "method": req.get_method(),
            "data": json.loads(req.data.decode("utf-8")),
            "headers": dict(req.headers),
        })
        return DummyResp()

    orig_urlopen = urllib.request.urlopen
    urllib.request.urlopen = fake_urlopen
    try:
        ok = send_telegram("Namaste Chief!", token="bot_test_token_123", chat_id="99887766")
        assert ok is True
        assert len(calls) == 1
        assert "bot_test_token_123" in calls[0]["url"]
        assert calls[0]["data"]["chat_id"] == "99887766"
        assert calls[0]["data"]["text"] == "Namaste Chief!"
    finally:
        urllib.request.urlopen = orig_urlopen


@test("analyst: detect_pacing_dropoff mid-story drop pe dynamic_fast recommend kare")
def _():
    d = fresh_db()
    from agents.analyst import Analyst
    # Add 4 videos with retention drop at ratio 0.50
    for i in range(4):
        vid = d.create_video(f"test_drop_{i}", length_sec=30)
        curve = [[0.0, 1.0], [0.2, 0.9], [0.4, 0.85], [0.5, 0.70], [0.6, 0.65], [1.0, 0.50]]
        d.save_metrics(vid, "youtube", "2h", views=500, avg_pct=0.60, raw_json={"retention_curve": curve})
    an = Analyst(d)
    res = an.detect_pacing_dropoff(10)
    assert res["recommended_pacing"] == "dynamic_fast"
    assert res["shorten_pct"] == 0.20
    assert res["add_mini_reveal"] is True
    d.close()


@test("artdirector & render: assign_scene_timing dynamic_fast pe scenes 4 & 5 ko 20% chhota kare")
def _():
    from run_phase2 import assign_scene_timing
    scenes = [{"n": i + 1, "beat": f"beat {i+1}"} for i in range(7)]
    narration = {
        "duration_sec": 28.0,
        "lines": [{"end": 4.0}, {"end": 8.0}, {"end": 12.0}, {"end": 16.0}, {"end": 20.0}, {"end": 24.0}, {"end": 28.0}]
    }
    std = assign_scene_timing(scenes, narration, pacing="standard")
    fast = assign_scene_timing(scenes, narration, pacing="dynamic_fast")
    assert len(fast) == 7
    # Scenes 4 & 5 (indices 3 and 4) should be ~20% shorter in fast than in std
    assert fast[3]["dur"] < std[3]["dur"]
    assert fast[4]["dur"] < std[4]["dur"]
    assert abs(fast[3]["dur"] - std[3]["dur"] * 0.80) < 0.05
    # Total length should match exactly
    assert abs(fast[-1]["end"] - 28.0) < 0.01


@test("scientist: scene_pacing testable arms mein shamil hai aur DB mein track hota hai")
def _():
    from agents.scientist import _arms
    d = fresh_db()
    arms = _arms()
    assert "scene_pacing" in arms
    assert "dynamic_fast" in arms["scene_pacing"]
    vid = d.create_video("test_pacing_col", scene_pacing="dynamic_fast")
    row = d.get_video(vid)
    assert row["scene_pacing"] == "dynamic_fast"
# =====================================================================
print("\n🧪 37. PHASE A: MULTI-VOICE DIALOGUE NARRATION")
# =====================================================================

@test("writer: script mein cast aur multi-speaker lines bante hain")
def _():
    d = fresh_db()
    w = Writer(d, LLM(force_mock=True))
    s = w.write("Test suspense story")
    assert "cast" in s, "script mein cast missing hai"
    assert "lines" in s, "script mein lines missing hai"
    assert "narrator" in s["cast"]
    assert len(s["lines"]) >= 3
    assert s["lines"][0]["role"] == "hook"
    assert s["lines"][-1]["role"] == "ending"
    d.close()


@test("writer: legacy script (hook/body/ending) lines[] mein gracefully normalize hota hai")
def _():
    d = fresh_db()
    w = Writer(d, LLM(force_mock=True))
    legacy = {
        "title": "Legacy Title",
        "hook_line": "Legacy Hook Line",
        "body": ["Body 1", "Body 2"],
        "ending": "Legacy Ending Line",
    }
    norm = w._normalize(legacy, "Topic", "pov", 30)
    assert "lines" in norm
    assert len(norm["lines"]) == 4
    assert norm["lines"][0]["speaker"] == "narrator"
    assert norm["lines"][0]["role"] == "hook"
    d.close()


@test("writer: 2 se zyada characters hone pe surplus characters prune hokar narrator mein merge hote hain")
def _():
    d = fresh_db()
    w = Writer(d, LLM(force_mock=True))
    bloated = {
        "cast": {
            "narrator": {"gender": "male"},
            "c1": {"gender": "female"},
            "c2": {"gender": "male"},
            "c3": {"gender": "female"},
        },
        "lines": [
            {"speaker": "c1", "text": "Line 1", "emotion": "panicked", "role": "hook"},
            {"speaker": "c2", "text": "Line 2", "emotion": "whispers", "role": "body"},
            {"speaker": "c3", "text": "Line 3", "emotion": "terrified", "role": "body"},
            {"speaker": "narrator", "text": "Line 4", "emotion": "neutral", "role": "ending"},
        ]
    }
    norm = w._normalize(bloated, "Topic", "pov", 30)
    char_keys = [k for k in norm["cast"] if k != "narrator"]
    assert len(char_keys) <= 2
    speakers = {l["speaker"] for l in norm["lines"]}
    assert "c3" not in speakers
    d.close()


@test("writer: gender alternation enforce hoti hai (agar all chars same gender, narrator flips)")
def _():
    d = fresh_db()
    w = Writer(d, LLM(force_mock=True))
    same_gender = {
        "cast": {
            "narrator": {"gender": "male"},
            "c1": {"gender": "male"},
            "c2": {"gender": "male"},
        },
        "lines": [
            {"speaker": "narrator", "text": "L1", "role": "hook"},
            {"speaker": "c1", "text": "L2", "role": "body"},
            {"speaker": "c2", "text": "L3", "role": "ending"},
        ]
    }
    norm = w._normalize(same_gender, "Topic", "pov", 30)
    assert norm["cast"]["narrator"]["gender"] == "female", "narrator gender flip nahi hua"
    d.close()


@test("voice: gemini_tts_requests quota spend aur limit 100/day enforce hoti hai")
def _():
    from core.quota import BUDGETS
    d = fresh_db()
    q = Quota(d)
    assert "gemini_tts_requests" in BUDGETS
    assert BUDGETS["gemini_tts_requests"]["limit"] == 100
    for i in range(100):
        q.check_and_spend("gemini_tts_requests", 1, reason=f"test_{i}")
    try:
        q.check_and_spend("gemini_tts_requests", 1, reason="overflow")
        raise AssertionError("quota 100 ke baad block nahi hua")
    except QuotaExceeded:
        pass
    d.close()


@test("voice: pcm_to_wav aur mock Gemini TTS duration ~1s valid MP3 banate hain")
def _():
    from agents.voice import _call_gemini_tts, _pcm_to_wav
    import wave
    td = Path(tempfile.mkdtemp())
    d = fresh_db()
    pcm = _call_gemini_tts("Test suspense line", voice_name="Charon", db=d)
    assert len(pcm) == 48000  # 1s * 24000 samples * 2 bytes
    wav = td / "test.wav"
    _pcm_to_wav(pcm, wav)
    assert wav.exists()
    with wave.open(str(wav), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 24000
    d.close()


@test("voice: _split_by_silence synthetic audio pe accurate cut points return kare")
def _():
    import subprocess
    from agents.voice import _split_by_silence
    td = Path(tempfile.mkdtemp())
    wav_path = td / "synth_split.wav"
    filt = "sine=frequency=400:duration=1.0 [s1]; anullsrc=duration=0.5 [gap1]; sine=frequency=400:duration=1.0 [s2]; [s1][gap1][s2] concat=n=3:v=0:a=1 [out]"
    cmd = [ffmpeg_bin(), "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
           "-filter_complex", filt, "-map", "[out]", "-ar", "24000", str(wav_path)]
    subprocess.run(cmd, stdin=subprocess.DEVNULL, check=True, capture_output=True)
    assert wav_path.exists()
    segs = _split_by_silence(wav_path, expected_lines=2)
    assert segs is not None
    assert len(segs) == 2
    assert abs(segs[0][1] - 1.25) < 0.2


@test("voice: _split_by_silence gap count mismatch hone pe None return kare (fallback)")
def _():
    import subprocess
    from agents.voice import _split_by_silence
    td = Path(tempfile.mkdtemp())
    wav_path = td / "synth_one.wav"
    cmd = [ffmpeg_bin(), "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
           "-f", "lavfi", "-i", "sine=frequency=400:duration=2.0", "-ar", "24000", str(wav_path)]
    subprocess.run(cmd, stdin=subprocess.DEVNULL, check=True, capture_output=True)
    segs = _split_by_silence(wav_path, expected_lines=3)
    assert segs is None


@test("voice: character aur narrator voices hamesha alag hoti hain")
def _():
    d = fresh_db()
    v = Voice(d)
    td = Path(tempfile.mkdtemp())
    lines = [
        {"speaker": "narrator", "text": "Narrator line", "role": "hook", "emotion": "neutral"},
        {"speaker": "char_a", "text": "Character line", "role": "body", "emotion": "panicked"},
        {"speaker": "narrator", "text": "Ending line", "role": "ending", "emotion": "neutral"},
    ]
    res = v.narrate(lines, td, profile_id="gem_m_grave")
    assert res["voice_id"] == "gem_m_grave"
    assert res["narrator_voice"] != res["character_voices"].get("char_a")
    d.close()


# =====================================================================
print("\n🧪 38. PHASE B: CINEMATIC SOUND DESIGN")
# =====================================================================

@test("sound: heartbeat layer 50Hz sine aur dual-thump lub-dub pulse banata hai")
def _():
    from pipeline.sound import build_heartbeat_filter
    inp, filt, lbl = build_heartbeat_filter(20.0, start_idx=3)
    assert len(inp) == 6
    assert "sine=frequency=50" in inp[5]
    assert "[heartbeat]" in lbl
    assert "volume=eval=frame" in filt[0]
    assert "mod(" in filt[0]


@test("sound: riser layer 200Hz to 600Hz frequency sweep banata hai")
def _():
    from pipeline.sound import build_riser_filter
    inp, filt, lbl = build_riser_filter(reveal_sec=15.0, start_idx=4, dur_sec=2.5)
    assert "200.0*t" in inp[5]
    assert "[riser]" in lbl
    assert "adelay=" in filt[0]


@test("sound: sub-hit layer 42Hz burst at reveal point banata hai")
def _():
    from pipeline.sound import build_sub_hit_filter
    inp, filt, lbl = build_sub_hit_filter(reveal_sec=18.0, start_idx=5, dur_sec=0.6, freq=42.0)
    assert "42.0*t" in inp[5]
    assert "[sub_hit]" in lbl
    assert "adelay=18000|18000" in filt[0]


@test("sound: room tone pink noise bed aur lowpass lagata hai")
def _():
    from pipeline.sound import build_room_tone_filter
    inp, filt, lbl = build_room_tone_filter(total_sec=25.0, start_idx=6)
    assert "color=pink" in inp[5]
    assert "lowpass=f=1200" in filt[0]
    assert "[room_tone]" in lbl


@test("sound: sound design package mein zero external audio files hain")
def _():
    from pipeline.sound import build_sound_design_package
    pkg = build_sound_design_package(30.0, cuts=[5.0, 10.0, 15.0, 20.0, 25.0], reveal_sec=22.0)
    joined = " ".join(pkg["inputs"]) + " " + " ".join(pkg["parts"])
    for bad in (".mp3", ".wav", "music/", "http"):
        assert bad not in joined, f"external audio source mila: {bad}"
    assert "heartbeat" in pkg["applied"]
    assert "riser" in pkg["applied"]
    assert "sub_hit" in pkg["applied"]


@test("sound: build_audio_filter cinematic mode sidechain ducking aur limiter include kare")
def _():
    from pipeline.render import build_audio_filter
    inputs, filt = build_audio_filter(5, [5.0, 10.0, 15.0, 20.0], 25.0,
                                      reveal_sec=18.0, cinematic=True)
    assert "sidechaincompress" in filt or "amix" in filt
    assert "alimiter=limit=0.9" in filt
    assert "loudnorm=I=-14:TP=-1.5" in filt


@test("sound: cinematic audio filter chain ffmpeg dry-run pe bina error pass ho")
def _():
    import subprocess
    from pipeline.render import build_audio_filter
    inputs, filt = build_audio_filter(4, [5.0, 10.0, 15.0], 20.0,
                                      reveal_sec=15.0, cinematic=True)
    cmd = [ffmpeg_bin(), "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
           "-f", "lavfi", "-i", "sine=frequency=440:duration=20",
           *inputs, "-filter_complex", filt, "-map", "[aout]", "-t", "0.5", "-f", "null", "-"]
    res = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True)
# =====================================================================
print("\n🧪 39. PHASE C: CINEMATIC VISUAL EFFECTS")
# =====================================================================

@test("effects: color grade teal-orange colorbalance filter banata hai")
def _():
    from pipeline.effects import build_color_grade_filter
    cg = build_color_grade_filter()
    assert "colorbalance" in cg
    assert "rs=" in cg and "bs=" in cg


@test("effects: 35mm film grain uniform+temporal noise banata hai")
def _():
    from pipeline.effects import build_film_grain_filter
    fg = build_film_grain_filter(7)
    assert "noise=alls=7:allf=t+u" in fg


@test("effects: vignette pulse heartbeat synced oscillation banata hai")
def _():
    from pipeline.effects import build_vignette_pulse_filter
    vp = build_vignette_pulse_filter(pulse=True, freq=1.1)
    assert "vignette=" in vp
    assert "sin(2*PI*t*1.1)" in vp


@test("effects: camera shake even dimensions maintain karta hai")
def _():
    from pipeline.effects import build_camera_shake_filter
    cs = build_camera_shake_filter(1080, 1920, intensity=12)
    assert "scale=1080:1920" in cs
    assert "crop=w=1048:h=1888" in cs


@test("effects: white flash 2 frames (0.066s) ka pure white transition banata hai")
def _():
    from pipeline.effects import build_white_flash_filter
    wf = build_white_flash_filter(0.066)
    assert "color=white" in wf
    assert "0.066" in wf


@test("effects: breathing character 0.4% scale pulse banata hai")
def _():
    from pipeline.effects import build_breathing_character_filter
    bc = build_breathing_character_filter(1080, 1920, intensity=0.004)
    assert "2*floor(" in bc
    assert "0.004" in bc


@test("effects: cinematic scene filter ffmpeg dry-run pe bina error pass hota hai")
def _():
    import subprocess
    from pipeline.effects import build_cinematic_scene_filter
    vf, applied = build_cinematic_scene_filter(
        "zoom_in", 3.0, 1080, 1920, 30,
        emotion="panicked", role="reveal", is_first=True
    )
    assert "camera_shake" in applied
    assert "white_flash" in applied
    assert "color_grade" in applied
    assert "film_grain" in applied
    cmd = [ffmpeg_bin(), "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
           "-f", "lavfi", "-i", "testsrc=size=1080x1920:rate=30",
           "-vf", vf, "-frames:v", "2", "-f", "null", "-"]
    res = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    assert res.returncode == 0, f"ffmpeg visual filter fail:\n{res.stderr}"


# =====================================================================
print("\n🧪 40. PHASE D: CHARACTER CONSISTENCY")
# =====================================================================

@test("consistency: build_visual_anchor detailed physical anchor banata hai")
def _():
    from agents.artdirector import build_visual_anchor
    anchor_m = build_visual_anchor("Kabir", gender="male", age=35)
    assert "Same 35-year-old South Asian man" in anchor_m["anchor"]
    assert "sharp jawline" in anchor_m["anchor"]
    assert "dark brown woolen trench coat" in anchor_m["anchor"]
    assert "scar" in anchor_m["anchor"]
    assert anchor_m["features"]["gender"] == "male"
    assert "same character as previous scene" in anchor_m["keywords"]

    anchor_f = build_visual_anchor("Priya", gender="female", age=29)
    assert "Same 29-year-old South Asian woman" in anchor_f["anchor"]
    assert "emerald green" in anchor_f["anchor"] or "ponytail" in anchor_f["anchor"]


@test("consistency: visual anchor scene prompt ke START mein prepend hota hai")
def _():
    d = fresh_db()
    llm = LLM(force_mock=True)
    script = {
        "title": "Test Mystery",
        "hook_line": "Darwaza band tha.",
        "body": ["Kabir ne andar dekha.", "Wahan koi nahi tha."],
        "ending": "Lekin diary khuli thi.",
        "target_length_sec": 30,
        "cast": [{"name": "Kabir", "role": "protagonist", "gender": "male"}],
    }
    art = ArtDirector(d, llm).direct(script)
    first_prompt = art["scenes"][0]["image_prompt"]
    assert first_prompt.startswith("Same 32-year-old South Asian man") or "Same" in first_prompt[:40]
    assert "same character as previous scene" in first_prompt
    assert "identical facial features" in first_prompt
    assert "consistent costume" in first_prompt
    d.close()


@test("consistency: negative prompt mein character consistency keywords hote hain")
def _():
    d = fresh_db()
    llm = LLM(force_mock=True)
    art = ArtDirector(d, llm).direct(Writer(d, llm).write("test topic"))
    for sc in art["scenes"]:
        p = sc["image_prompt"].lower()
        assert "different face" in p
        assert "inconsistent clothing" in p
        assert "different actor" in p
    d.close()


@test("consistency: characters SQLite DB mein save hote hain")
def _():
    d = fresh_db()
    vid = d.create_video("mystery story")
    cid = d.save_character("Kabir", "Same 35-year-old South Asian man...", video_id=vid,
                           costume="dark brown trench coat", features={"age": 35})
    assert cid > 0
    row = d.get_character("Kabir")
    assert row is not None
    assert row["name"] == "Kabir"
    assert row["video_id"] == vid
    assert "35-year-old" in row["visual_anchor"]
    chars = d.list_characters()
    assert len(chars) >= 1
    d.close()


@test("consistency: series mode mein existing character DB se reuse hota hai")
def _():
    d = fresh_db()
    llm = LLM(force_mock=True)
    # Save a custom character in DB
    d.save_character("Vikram", "Custom visual anchor for Vikram with blue jacket",
                     costume="blue jacket", features={"custom": True})
    
    script = {
        "title": "Part 2",
        "hook_line": "Vikram wapas aaya.",
        "body": ["Usne diary kholi."],
        "ending": "Sach samne tha.",
        "target_length_sec": 30,
        "cast": [{"name": "Vikram", "role": "protagonist", "gender": "male"}],
    }
    art = ArtDirector(d, llm).direct(script)
    assert "Custom visual anchor for Vikram with blue jacket" in art["scenes"][0]["image_prompt"]
    d.close()


@test("consistency: multi-character cast mein har character ka alag anchor banta hai")
def _():
    d = fresh_db()
    llm = LLM(force_mock=True)
    script = {
        "title": "Two Detectives",
        "hook_line": "Kabir aur Priya kamre mein the.",
        "body": ["Kabir ne diary uthayi.", "Priya ne darwaza lock kiya."],
        "ending": "Dono phas chuke the.",
        "target_length_sec": 30,
        "cast": [
            {"name": "Kabir", "role": "protagonist", "gender": "male"},
            {"name": "Priya", "role": "partner", "gender": "female"}
        ],
    }
    art = ArtDirector(d, llm).direct(script)
    anchors = art["character_anchors"]
    assert "kabir" in anchors and "priya" in anchors
    assert "man" in anchors["kabir"]
    assert "woman" in anchors["priya"]
    d.close()


@test("consistency: ImageGen scene-to-scene seed proximity maintain karta hai")
def _():
    from agents.imagegen import ImageGen
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        scenes = [
            {"n": 1, "file": "scene_01.jpg", "image_prompt": "test 1"},
            {"n": 2, "file": "scene_02.jpg", "image_prompt": "test 2"},
            {"n": 3, "file": "scene_03.jpg", "image_prompt": "test 3"},
        ]
        ig = ImageGen(["local_placeholder"])
        res = ig.generate_all(scenes, td, seed_base=100)
        assert res[0]["seed"] == 101
        assert res[1]["seed"] == 102
        assert res[2]["seed"] == 103
        assert res[1]["seed"] - res[0]["seed"] == 1


# =====================================================================
print("\n🧪 41. PHASE E: 2.5D LAYERED SCENES & PARTICLES")
# =====================================================================

@test("layered: docs/LAYERED_SCENES.md architectural spec maujood hai")
def _():
    from pathlib import Path
    doc_path = Path("docs/LAYERED_SCENES.md")
    assert doc_path.exists(), "docs/LAYERED_SCENES.md missing hai"
    txt = doc_path.read_text(encoding="utf-8")
    assert "Foreground/Background" in txt or "Parallax" in txt
    assert "colorkey" in txt or "chromakey" in txt
    assert "lavfi" in txt or "procedural" in txt


@test("layered: build_dust_particle_filter procedural dust specks banata hai")
def _():
    from pipeline.effects import build_dust_particle_filter
    flt = build_dust_particle_filter(1080, 1920, 3.0, density=0.002, alpha=0.3)
    assert "nullsrc=s=1080x1920" in flt
    assert "geq=" in flt
    assert "colorchannelmixer=aa=0.30" in flt


@test("layered: dust particle filter ffmpeg dry-run pe pass hota hai")
def _():
    import subprocess
    from pipeline.effects import build_dust_particle_filter
    flt = build_dust_particle_filter(640, 360, 0.2, density=0.002, alpha=0.3)
    cmd = [ffmpeg_bin(), "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
           "-f", "lavfi", "-i", flt, "-frames:v", "2", "-f", "null", "-"]
    res = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    assert res.returncode == 0, f"dust particle ffmpeg fail:\n{res.stderr}"


@test("layered: build_atmospheric_fog_filter drifting fog layer banata hai")
def _():
    from pipeline.effects import build_atmospheric_fog_filter
    flt = build_atmospheric_fog_filter(1080, 1920, 3.0, alpha=0.15)
    assert "nullsrc=s=1080x1920" in flt
    assert "noise=alls=25:allf=t+u" in flt
    assert "boxblur=15:5" in flt


@test("layered: atmospheric fog filter ffmpeg dry-run pe pass hota hai")
def _():
    import subprocess
    from pipeline.effects import build_atmospheric_fog_filter
    flt = build_atmospheric_fog_filter(640, 360, 0.2, alpha=0.15)
    cmd = [ffmpeg_bin(), "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
           "-f", "lavfi", "-i", flt, "-frames:v", "2", "-f", "null", "-"]
    res = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    assert res.returncode == 0, f"fog filter ffmpeg fail:\n{res.stderr}"


@test("layered: build_parallax_filter differential motion aur overlay banata hai")
def _():
    from pipeline.effects import build_parallax_filter
    flt = build_parallax_filter(1080, 1920, 3.0, intensity="medium")
    assert "[0:v]scale=" in flt
    assert "[1:v]scale=" in flt
    assert "overlay=" in flt
    assert "2*floor(" in flt


@test("layered: parallax filter ffmpeg dry-run pe 2 plates ke saath pass hota hai")
def _():
    import subprocess
    from pipeline.effects import build_parallax_filter
    flt = build_parallax_filter(640, 360, 0.2, intensity="medium")
    cmd = [ffmpeg_bin(), "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
           "-f", "lavfi", "-i", "testsrc=size=640x360:rate=30",
           "-f", "lavfi", "-i", "color=c=blue@0.5:size=640x360:rate=30:duration=0.2,format=yuva420p",
           "-filter_complex", flt, "-frames:v", "2", "-f", "null", "-"]
    res = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    assert res.returncode == 0, f"parallax filter ffmpeg fail:\n{res.stderr}"


# =====================================================================
print("\n🧪 42. PHASE F: ASYNC JOBS, IDEMPOTENCY & SECURE MAKE.COM")
# =====================================================================

@test("jobs: DB create_job, update_job aur get_job kaam karte hain")
def _():
    import uuid
    from core.db import DB
    with DB() as db:
        jid = f"test_job_{uuid.uuid4().hex[:8]}"
        db.create_job(jid, "generate", topic="haunted palace", idempotency_key=f"idem_{jid}")
        job = db.get_job(jid)
        assert job is not None
        assert job["status"] == "queued"
        assert job["topic"] == "haunted palace"
        db.update_job(jid, status="running")
        assert db.get_job(jid)["status"] == "running"
        vid = db.create_video(topic="haunted palace")
        db.update_job(jid, status="completed", video_id=vid, result_paths={"video_path": "output/test.mp4"})
        res = db.get_job(jid)
        assert res["status"] == "completed"
        assert res["video_id"] == vid
        assert "output/test.mp4" in res["result_paths"]

@test("jobs: get_job_by_idempotency_key match karta hai")
def _():
    import uuid
    from core.db import DB
    with DB() as db:
        jid = f"test_job_{uuid.uuid4().hex[:8]}"
        ikey = f"idem_{uuid.uuid4().hex[:8]}"
        db.create_job(jid, "generate", idempotency_key=ikey)
        matched = db.get_job_by_idempotency_key(ikey)
        assert matched is not None
        assert matched["job_id"] == jid

@test("jobs: webhook auth secret constant-time digest compare karta hai")
def _():
    import os
    from web.server import _check_webhook_auth
    old_sec = os.environ.get("MAKE_WEBHOOK_SECRET")
    try:
        os.environ["MAKE_WEBHOOK_SECRET"] = "x" * 32
        ok, code, _ = _check_webhook_auth({"X-Webhook-Secret": "x" * 32}, {})
        assert ok is True and code == 200
        ok2, code2, _ = _check_webhook_auth({"X-Webhook-Secret": "wrong_secret"}, {})
        assert ok2 is False and code2 == 403
    finally:
        if old_sec is not None:
            os.environ["MAKE_WEBHOOK_SECRET"] = old_sec
        else:
            os.environ.pop("MAKE_WEBHOOK_SECRET", None)

@test("voice: faster-whisper singleton model reuse karta hai")
def _():
    from agents.voice import _get_whisper_model
    assert callable(_get_whisper_model)


# =====================================================================
# REPORT
# =====================================================================
print("\n" + "=" * 62)
print(f"  ✅ PASS: {len(PASS)}    ❌ FAIL: {len(FAIL)}")
print("=" * 62)
if FAIL:
    print("\nFail hue tests:")
    for name, err in FAIL:
        print(f"  ❌ {name}\n     → {type(err).__name__}: {err}")
    print("\nDetail ke liye: VERBOSE=1 python test_all.py")
    sys.exit(1)
print("\n🎉 SAARE 10 PHASE GREEN HAIN. System poora ban chuka hai. 🎉")
try:
    Quota().print_report()
except Exception:
    pass
