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
MOONSHOT_BASE_URL = os.environ.get("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1")
MOONSHOT_DEFAULT_MODEL = os.environ.get("MOONSHOT_MODEL", "kimi-k3")


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
                "cast": {
                    "narrator": {"gender": "male", "persona": "gambhir crime-doc narrator, dheemi awaaz"},
                    "char_a": {"name": "Ravi", "gender": "female", "persona": "darawani aawaz, ghabrahat"},
                },
                "lines": [
                    {"speaker": "narrator", "text": "Is gaon ke 14 log ek hi raat mein gayab ho gaye.", "emotion": "curious", "role": "hook"},
                    {"speaker": "char_a", "text": "Police pahunchi to darwaze andar se band the.", "emotion": "nervous", "role": "body"},
                    {"speaker": "narrator", "text": "Chai abhi bhi garam thi, par ghar khaali tha.", "emotion": "serious", "role": "body"},
                    {"speaker": "char_a", "text": "Ek hi cheez mili thi — deewar pe likha ek number.", "emotion": "whispers", "role": "reveal"},
                    {"speaker": "narrator", "text": "Aur wo number aaj bhi kisi ka phone number hai.", "emotion": "serious", "role": "ending"}
                ],
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

        def _call_model(model_name: str):
            req_url = f"{API_BASE}/{model_name}:generateContent?key={self.api_key}"
            req = urllib.request.Request(
                req_url, data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", "replace")[:400]
                if e.code == 429 and ("quota" in detail.lower() or "limit" in detail.lower()):
                    raise QuotaExceeded(f"Gemini API rate/quota limit: {detail}") from e
                raise RuntimeError(f"{e.code} {e.reason} :: {detail}") from e

        try:
            data = retry(lambda: _call_model(self.model), tries=3, base_delay=1.5, log=log,
                         what=f"Gemini {self.model} generateContent")
        except (QuotaExceeded, RuntimeError) as e:
            if self.model != "gemini-1.5-flash":
                log.warn(f"Model '{self.model}' unavailable or quota limit — falling back to gemini-1.5-flash",
                         reason=str(e)[:120])
                data = retry(lambda: _call_model("gemini-1.5-flash"), tries=3, base_delay=1.5,
                             log=log, what="Gemini gemini-1.5-flash fallback")
            else:
                raise

        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            reason = data.get("promptFeedback", {}).get("blockReason")
            raise RuntimeError(
                f"Gemini ne text nahi diya. {'Safety block: ' + reason if reason else ''} "
                f"Raw: {json.dumps(data)[:300]}")


# =====================================================================
# MOONSHOT / KIMI K3 (real)
# =====================================================================
class MoonshotLLM:
    """
    Moonshot AI (Kimi K3) client — OpenAI-compatible REST endpoint (stdlib urllib only).
    Har call se pehle quota.check_and_spend("moonshot_requests", 1).
    """

    name = "kimi"

    def __init__(self, api_key: str, model: str | None = None,
                 base_url: str | None = None, quota: Quota | None = None):
        self.api_key = api_key
        self.model = model or os.environ.get("MOONSHOT_MODEL") or MOONSHOT_DEFAULT_MODEL
        raw_url = base_url or os.environ.get("MOONSHOT_BASE_URL") or MOONSHOT_BASE_URL
        self.base_url = raw_url.rstrip("/")
        self.quota = quota or Quota()

    def generate(self, prompt: str, *, temperature: float = 0.9, max_tokens: int = 2048,
                 system: str | None = None) -> str:
        # STEP 1: quota check — hard constraint (Moonshot is PAID API, daily spend cap)
        self.quota.check_and_spend("moonshot_requests", 1, reason=f"generate:{self.model}")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        endpoint = f"{self.base_url}/chat/completions"
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        def _call_model():
            try:
                with urllib.request.urlopen(req, timeout=90) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", "replace")[:400]
                if e.code == 401:
                    raise RuntimeError(f"Moonshot API key invalid ya unauthorized (401): {detail}") from e
                if e.code == 429:
                    raise QuotaExceeded(f"Moonshot API rate/quota limit (429): {detail}") from e
                raise RuntimeError(f"Moonshot HTTP error {e.code} {e.reason}: {detail}") from e

        data = retry(_call_model, tries=3, base_delay=1.5, log=log,
                     what=f"Moonshot {self.model} chat/completions")

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise RuntimeError(f"Moonshot ne content nahi diya. Raw: {json.dumps(data)[:300]}")


def _normalize_provider(p: str) -> str:
    p = (p or "").strip().lower()
    if p in ("moonshot", "kimi", "kimi-k3"):
        return "kimi"
    if p in ("gemini", "google"):
        return "gemini"
    if p == "mock":
        return "mock"
    return p


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

    def __init__(self, quota: Quota | None = None, force_mock: bool | None = None,
                 agent_name: str | None = None):
        self.quota = quota
        self.force_mock = force_mock
        self.agent_name = agent_name
        self.backends = []

        mock = CONFIG.get("mock_mode", True) if force_mock is None else force_mock
        if mock:
            self.backends = [MockLLM()]
            self.backend = self.backends[0]
            log.info(f"LLM [{self.agent_name or 'global'}] MOCK mode mein hai (config.yaml -> mock_mode: false karke real karo)")
            return

        gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
        moonshot_key = os.environ.get("MOONSHOT_API_KEY", "").strip()

        order = self._resolve_order(agent_name)

        for name in order:
            if name == "kimi":
                if moonshot_key:
                    self.backends.append(MoonshotLLM(moonshot_key, quota=quota))
                else:
                    log.warn(f"MOONSHOT_API_KEY nahi mili — kimi backend skip ho raha hai")
            elif name == "gemini":
                if gemini_key:
                    self.backends.append(GeminiLLM(gemini_key, quota=quota))
                else:
                    log.warn(f"GEMINI_API_KEY nahi mili — gemini backend skip ho raha hai")
            elif name == "mock":
                self.backends.append(MockLLM())

        if not any(not isinstance(b, MockLLM) for b in self.backends):
            if not self.backends:
                self.backends = [MockLLM()]
            log.warn("Koi valid LLM API key nahi mili — mock pe gir gaye. "
                     ".env mein GEMINI_API_KEY ya MOONSHOT_API_KEY daalo")
        elif not any(isinstance(b, MockLLM) for b in self.backends):
            # Mock hamesha aakhri resort hona chahiye
            self.backends.append(MockLLM())

        self.backend = self.backends[0]
        chain_str = " -> ".join(b.name for b in self.backends)
        log.info(f"LLM [{self.agent_name or 'global'}] routing chain: {chain_str}")
        if isinstance(self.backend, GeminiLLM):
            log.ok(f"Gemini connected: {self.backend.model}")
        elif isinstance(self.backend, MoonshotLLM):
            log.ok(f"Moonshot connected: {self.backend.model} ({self.backend.base_url})")

    def _resolve_order(self, agent_name: str | None) -> list[str]:
        """Env vars aur config.yaml ke mutabiq providers ka order return karo."""
        # 1. LLM_FALLBACK_ORDER agar diya hai to sabse pehle usse maano
        fallback_order = os.environ.get("LLM_FALLBACK_ORDER", "").strip()
        if fallback_order:
            chain = [_normalize_provider(p) for p in fallback_order.split(",") if p.strip()]
            if "mock" not in chain:
                chain.append("mock")
            return chain

        # 2. Per-agent override in config.yaml (llm_routing)
        routing_cfg = CONFIG.get("llm_routing") or {}
        agent_pref = None
        if agent_name and isinstance(routing_cfg, dict):
            raw_pref = routing_cfg.get(agent_name)
            if raw_pref:
                agent_pref = _normalize_provider(str(raw_pref))

        # 3. Global LLM_PROVIDER
        global_provider = _normalize_provider(os.environ.get("LLM_PROVIDER", "auto"))

        # 4. Global LLM_PRIMARY
        global_primary = _normalize_provider(os.environ.get("LLM_PRIMARY", "gemini"))
        if global_primary not in ("kimi", "gemini"):
            global_primary = "gemini"

        target_pref = agent_pref or (global_provider if global_provider != "auto" else None)

        if target_pref == "kimi":
            return ["kimi", "gemini", "mock"]
        if target_pref == "gemini":
            return ["gemini", "kimi", "mock"]
        if target_pref == "mock":
            return ["mock"]

        # auto mode:
        gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
        moonshot_key = os.environ.get("MOONSHOT_API_KEY", "").strip()
        if gemini_key and moonshot_key:
            if global_primary == "kimi":
                return ["kimi", "gemini", "mock"]
            return ["gemini", "kimi", "mock"]
        elif moonshot_key and not gemini_key:
            return ["kimi", "gemini", "mock"]
        elif gemini_key and not moonshot_key:
            return ["gemini", "kimi", "mock"]
        else:
            if global_primary == "kimi":
                return ["kimi", "gemini", "mock"]
            return ["gemini", "kimi", "mock"]

    def for_agent(self, agent_name: str) -> "LLM":
        """Naya LLM instance banao is agent ke specific routing ke saath."""
        if self.agent_name == agent_name:
            return self
        return LLM(quota=self.quota, force_mock=self.force_mock, agent_name=agent_name)

    @property
    def is_mock(self) -> bool:
        return isinstance(self.backend, MockLLM)

    def ask(self, prompt: str, **kw) -> str:
        """Plain text jawab. Har provider koshish karega, fail ho to agla provider."""
        had_real_backend = any(not isinstance(b, MockLLM) for b in self.backends)
        for backend in self.backends:
            if isinstance(backend, MockLLM):
                if had_real_backend:
                    log.warn("⚠️  Saare real LLM fail ho gaye — ye output MOCK hai, asli LLM ka nahi. Quality kam hogi.")
                return backend.generate(prompt, **kw)
            try:
                ans = backend.generate(prompt, **kw)
                log.ok(f"LLM [{self.agent_name or 'global'}] served by {backend.name} ({getattr(backend, 'model', '')})")
                return ans
            except QuotaExceeded as e:
                log.warn(f"[{backend.name}] quota khatam, agla backend try karte hain: {e}")
            except Exception as e:  # noqa: BLE001
                log.error(f"[{backend.name}] call fail — agla backend try karte hain", e)

        fallback = MockLLM().generate(prompt)
        if had_real_backend:
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
        v = json.loads(t, strict=False)
        return v if isinstance(v, dict) else {"data": v}
    except Exception:
        pass
    try:
        clean = re.sub(r",\s*([\]}])", r"\1", t)
        v = json.loads(clean, strict=False)
        return v if isinstance(v, dict) else {"data": v}
    except Exception:
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
                sub = t[start:i + 1]
                try:
                    return json.loads(sub, strict=False)
                except Exception:
                    try:
                        clean_sub = re.sub(r",\s*([\]}])", r"\1", sub)
                        return json.loads(clean_sub, strict=False)
                    except Exception:
                        return None
    return None


if __name__ == "__main__":
    llm = LLM()
    print("mock?", llm.is_mock)
    print(json.dumps(llm.json("Ek suspense script JSON mein do"), indent=2, ensure_ascii=False))
