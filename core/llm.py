"""
core/llm.py — Gemini free tier client (sirf stdlib: urllib + json).

Design:
  * Koi google-generativeai package nahi — REST endpoint seedha hit karte hain.
    (Hard constraint #2: dependencies minimum)
  * Har call se pehle quota.can_spend("gemini_requests")
  * Fail / no-key / mock_mode -> MockLLM chalu ho jata hai, system crash nahi hota
    (Acceptance test: "Poora system bina kisi API key ke mock mode mein chalta ho")
  * json() helper — LLM se structured JSON nikalta hai aur galat JSON ko repair karta hai
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request

from .config import CONFIG
from .logbook import Logbook, retry
from .quota import Quota, QuotaExceeded

log = Logbook("llm")

def _read_env_file():
    """.env file ko manually padho (python-dotenv install karne ki zaroorat nahi)."""
    env_path = os.path.join(CONFIG["_root"], ".env")
    if not os.path.exists(env_path):
        return
    for line in open(env_path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_read_env_file()

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")


# =====================================================================
# MOCK — bina API key ke poora system chalane ke liye
# =====================================================================
class MockLLM:
    """
    Deterministic fake LLM. Same prompt = same output (hash se seed).
    Isse tests reproducible rehte hain aur pipeline bina internet ke chalti hai.
    """

    name = "mock"

    def generate(self, prompt: str, **_) -> str:
        h = hashlib.sha256(prompt.encode()).hexdigest()[:8]
        if _wants_json(prompt):
            return json.dumps(self._fake_json(prompt, h), ensure_ascii=False)
        return (f"[MOCK-{h}] Ye mock LLM ka jawab hai. Asli output ke liye "
                f".env mein GEMINI_API_KEY daalo aur config.yaml mein mock_mode: false karo.")

    def _fake_json(self, prompt: str, h: str) -> dict:
        p = prompt.lower()
        # ⚠️ Order maayne rakhta hai: sabse SPECIFIC check pehle.
        # (TrendScout ke prompt mein "hook_angle" hota hai, isliye agar
        #  "hook" wala check pehle aa jaye to galat shape return hoti hai.)
        if "content strategist" in p or '"topics"' in p:
            return {"topics": [
                {"topic": f"Wo {n} log jo ek hi raat mein ek gaon se gayab ho gaye",
                 "why": "concrete number + ek raat ka time frame = curiosity gap",
                 "hook_angle": f"{n} log, zero saboot"}
                for n in (14, 7, 23, 5, 31)]}
        # ---- Phase 5: metadata agent ke shapes (specific checks pehle) ----
        if '"titles"' in p:
            return {"titles": [
                f"Wo Raaz Jo 14 Saal Chhupa Raha — Mock Title {h[:4]}",
                "3 Sabooton Ne Poora Case Palat Diya",
                "Ek Raat, 14 Log, Zero Jawab — Asli Kahani",
                "Police File Mein Dabi Wo Kahani Jo Ab Bahar Aayi",
                "Is Gaon Ka Sach Aaj Tak Koi Nahi Jaan Paya"]}
        if '"tags"' in p and "youtube tags" in p:
            return {"tags": [
                "unsolved mystery", "hindi kahani", "suspense story", "true crime hindi",
                "mystery video", "rahasya", "hindi story", "crime story", "dark stories",
                "unsolved case", "mystery hindi", "kahani", "suspense", "thriller story",
                "real story hindi", "shorts story", "viral kahani", "puri kahani"]}
        if '"thumbnail_title"' in p:
            return {"thumbnail_title": "14 LOG GAYAB", "thumbnail_subtitle": "Ek hi raat mein",
                    "colors": ["#0d1117", "#e05d2d", "#2da3a8"],
                    "visual_concept": "flat 2D cartoon — khaali gaon, ek jalti lantern",
                    "emotion": "curiosity", "hook": "number + mystery = click"}
        if '"category"' in p and "options:" in p:
            return {"category": "entertainment"}
        if '"opening"' in p:
            return {"opening": f"Ye kahani {h[:4]} — ek aisi raat ki hai jiska "
                               f"jawab aaj tak nahi mila. Poora sach is video mein."}
        if "hook" in p or "script" in p or "writer" in p:
            return {
                "title": f"Wo raat jab sab kuch badal gaya #{h}",
                "hook_type": "specific_outcome",
                "hook_line": "Is gaon ke 14 log ek hi raat mein gayab ho gaye.",
                "hook_text_overlay": "14 log. Ek raat. Zero saboot.",
                "body": ["Police pahunchi to darwaze andar se band the.",
                         "Chai abhi bhi garam thi, par ghar khaali tha.",
                         "Ek hi cheez mili thi — deewar pe likha ek number."],
                "ending": "Aur wo number aaj bhi kisi ka phone number hai.",
                "comment_bait": "Tumhe kya lagta hai us number ke peeche asli wajah kya thi?",
                "caption": f"Case #{h} — abhi tak unsolved.",
                "hashtags": ["#unsolvedmystery", "#suspensestory", "#hindistory"],
            }
        if "scene" in p or "image" in p or "art" in p:
            return {"scenes": [
                {"n": i, "prompt": f"flat 2D cartoon, noir shadows, teal-orange, scene {i}",
                 "motion": ["zoom_in", "pan_left", "zoom_out", "pan_right"][i % 4]}
                for i in range(1, 7)]}
        return {"mock": True, "hash": h}


def _wants_json(prompt: str) -> bool:
    return "json" in prompt.lower()


# =====================================================================
# GEMINI (real)
# =====================================================================
class GeminiLLM:
    name = "gemini"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, quota: Quota | None = None):
        self.api_key = api_key
        self.model = model
        self.quota = quota or Quota()

    def generate(self, prompt: str, *, temperature: float = 0.9, max_tokens: int = 2048,
                 system: str | None = None) -> str:
        # STEP 1: quota check — hard constraint
        self.quota.check_and_spend("gemini_requests", 1, reason=f"generate:{self.model}")

        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}

        url = f"{API_BASE}/{self.model}:generateContent?key={self.api_key}"

        def _call():
            req = urllib.request.Request(
                url, data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", "replace")[:400]
                raise RuntimeError(f"{e.code} {e.reason} :: {detail}") from e

        data = retry(_call, tries=4, base_delay=2.0, log=log, what="Gemini generateContent")

        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            reason = data.get("promptFeedback", {}).get("blockReason")
            raise RuntimeError(
                f"Gemini ne text nahi diya. {'Safety block: ' + reason if reason else ''} "
                f"Raw: {json.dumps(data)[:300]}")


# =====================================================================
# LLM — wrapper jo fallback chain sambhalta hai
# =====================================================================
class LLM:
    """
    Yahi class agents use karte hain.
        llm = LLM()
        text = llm.ask("...")
        data = llm.json("... JSON mein jawab do ...")
    """

    def __init__(self, quota: Quota | None = None, force_mock: bool | None = None):
        self.quota = quota
        key = os.environ.get("GEMINI_API_KEY", "").strip()
        mock = CONFIG.get("mock_mode", True) if force_mock is None else force_mock

        if mock:
            self.backend = MockLLM()
            log.info("LLM MOCK mode mein hai (config.yaml -> mock_mode: false karke real karo)")
        elif not key:
            self.backend = MockLLM()
            log.warn("GEMINI_API_KEY nahi mili — mock pe gir gaye. "
                     ".env mein GEMINI_API_KEY=... daalo (aistudio.google.com/apikey, free)")
        else:
            self.backend = GeminiLLM(key, quota=quota)
            log.ok(f"Gemini connected: {DEFAULT_MODEL}")

    @property
    def is_mock(self) -> bool:
        return isinstance(self.backend, MockLLM)

    def ask(self, prompt: str, **kw) -> str:
        """Plain text jawab. Real backend fail ho to mock se graceful degrade."""
        try:
            return self.backend.generate(prompt, **kw)
        except QuotaExceeded as e:
            log.warn(f"Gemini quota khatam, mock se kaam chalate hain: {e}")
        except Exception as e:  # noqa: BLE001
            log.error("Gemini call fail — mock fallback", e)
        fallback = MockLLM().generate(prompt)
        log.warn("⚠️  Ye output MOCK hai, asli LLM ka nahi. Quality kam hogi.")
        return fallback

    def json(self, prompt: str, *, schema_hint: str = "", tries: int = 2, **kw) -> dict:
        """
        Structured output. LLM aksar ```json fences ya extra text daal deta hai —
        _extract_json usse saaf karta hai. Phir bhi fail ho to mock JSON.
        """
        full = prompt
        if schema_hint:
            full += f"\n\nSirf valid JSON return karo, ye shape:\n{schema_hint}\nKoi extra text nahi."
        elif "json" not in prompt.lower():
            full += "\n\nSirf valid JSON return karo. Koi markdown fence nahi, koi extra text nahi."

        for attempt in range(tries):
            raw = self.ask(full, **kw)
            parsed = _extract_json(raw)
            if parsed is not None:
                return parsed
            log.warn(f"LLM ne galat JSON diya (koshish {attempt+1}/{tries}), dobara poochhte hain",
                     sample=raw[:160])
            full = prompt + "\n\nPICHHLI BAAR JSON INVALID THA. Sirf raw JSON object bhejo."
        log.error("JSON parse har baar fail — mock JSON use kar rahe hain")
        return json.loads(MockLLM().generate(prompt + " json"))


def _extract_json(text: str) -> dict | None:
    """```json fence hatao, phir pehla balanced {...} block nikalo."""
    if not text:
        return None
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.MULTILINE).strip()
    try:
        v = json.loads(t)
        return v if isinstance(v, dict) else {"data": v}
    except json.JSONDecodeError:
        pass
    start = t.find("{")
    if start == -1:
        return None
    depth, in_str, esc = 0, False, False
    for i, ch in enumerate(t[start:], start):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(t[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


if __name__ == "__main__":
    llm = LLM()
    print("mock?", llm.is_mock)
    print(json.dumps(llm.json("Ek suspense script JSON mein do"), indent=2, ensure_ascii=False))
