"""
core/config.py — config.yaml padhne wala chhota loader.

Kyun apna parser? Kyunki hard constraint hai: "Python stdlib prefer karo".
Hamari config.yaml flat hai (nested nahi), isliye 30 line ka parser kaafi hai.
Agar tumne PyYAML install kiya hua hai to wo automatically use ho jayega
(better, kyunki nested config bhi handle karega).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Windows console encoding fix for Unicode/emojis
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# ROOT = autopilot/ folder ka absolute path (core/ ke ek level upar)
ROOT = Path(__file__).resolve().parent.parent


def _load_env():
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        pass
    try:
        with open(env_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                os.environ.setdefault(k, v)
    except Exception:
        pass


_load_env()


def _coerce(value: str):
    """String ko sahi Python type mein badlo: true -> True, 32 -> 32, "x" -> x"""
    v = value.strip()
    # inline comment hatao — but quoted string ke andar wala # nahi hatana
    if v.startswith('"') or v.startswith("'"):
        quote = v[0]
        end = v.find(quote, 1)
        if end != -1:
            return v[1:end]
    if "#" in v:
        v = v.split("#", 1)[0].strip()
    low = v.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("null", "none", "~", ""):
        return None
    if v.startswith("{") and v.endswith("}"):
        inner = v[1:-1].strip()
        parsed = {}
        if inner:
            for part in inner.split(","):
                if ":" in part:
                    ik, _, iv = part.partition(":")
                    parsed[ik.strip()] = _coerce(iv.strip())
        return parsed
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v


def _mini_yaml(text: str) -> dict:
    """Robust YAML parser supporting arbitrary indentation nesting."""
    out = {}
    stack = [(-1, out)]  # (indent_level, dict_ref)
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        key, _, value = stripped.partition(":")
        key = key.strip()
        val_str = value.strip()
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if not val_str or val_str.startswith("#"):
            new_dict = {}
            parent[key] = new_dict
            stack.append((indent, new_dict))
        else:
            parent[key] = _coerce(val_str)
    return out


def load(path: str | Path | None = None) -> dict:
    """config.yaml load karo aur dict return karo."""
    path = Path(path) if path else ROOT / "config.yaml"
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # optional — agar installed hai to isse padho

        data = yaml.safe_load(text) or {}
    except ImportError:
        data = _mini_yaml(text)

    # ---- Environment variable override ----
    # Example: AUTOPILOT_MOCK_MODE=false python run.py
    for key in list(data.keys()):
        env_key = "AUTOPILOT_" + key.upper()
        if env_key in os.environ:
            data[key] = _coerce(os.environ[env_key])

    # ---- Safety defaults (agar user ne key delete kar di ho) ----
    data.setdefault("mock_mode", True)
    data.setdefault("db_path", "data/autopilot.db")
    data.setdefault("log_dir", "logs")
    data.setdefault("video_length_sec", 32)
    data.setdefault("autonomy", "review_first")

    # relative paths ko absolute banao (kahin se bhi script chale, kaam kare)
    # Cloud (Render/Railway) pe /tmp use karo — data/ directory har deploy pe wipe ho jaati hai
    if os.environ.get("PORT") or os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("RENDER"):
        # Cloud deployment: /tmp is ephemeral but survives within same dyno session
        cloud_db = os.environ.get("DATABASE_PATH", "/tmp/autopilot.db")
        data["db_path"] = cloud_db
        data["log_dir"] = "/tmp/autopilot_logs"
    else:
        data["db_path"] = str(ROOT / data["db_path"])
        data["log_dir"] = str(ROOT / data["log_dir"])
    data["_root"] = str(ROOT)

    # ---- Placeholder checks (agar mock_mode false hai to warning do) ----
    if not data.get("mock_mode", True):
        if data.get("brand_name") == "AUTOPILOT":
            print("⚠️  WARNING: config.yaml mein brand_name abhi bhi 'AUTOPILOT' hai — apna channel naam daalo")
        if data.get("instagram_handle") in ("@your_handle", ""):
            print("⚠️  WARNING: config.yaml mein instagram_handle abhi bhi placeholder hai — apna IG handle daalo")
        if data.get("youtube_channel") in ("https://youtube.com/@your_channel", ""):
            print("⚠️  WARNING: config.yaml mein youtube_channel abhi bhi placeholder hai — apna channel URL daalo")

    return data


DEFAULT_PROFILES = {
    "shorts": {
        "length_sec": 32,
        "resolution": "720x1280",
        "aspect": "9:16",
        "sec_per_scene": 4.5,
        "subtitles": "kinetic",
    },
    "longform": {
        "length_sec": 600,
        "resolution": "1920x1080",
        "aspect": "16:9",
        "sec_per_scene": 6.0,
        "subtitles": "clean",
        "chapters": True,
        "max_length_sec": 3600,
    },
}


def get_profile(name: str | None = None, cfg: dict | None = None) -> dict:
    """
    Get profile dictionary merged over legacy top-level keys.

    Order:
      1. Explicit `name` argument ('shorts' | 'longform')
      2. Environment variable AUTOPILOT_ACTIVE_PROFILE / AUTOPILOT_PROFILE
      3. Active profile in config (default 'shorts')
    """
    data = cfg if cfg is not None else CONFIG
    prof_name = name or os.environ.get("AUTOPILOT_ACTIVE_PROFILE") or os.environ.get("AUTOPILOT_PROFILE") or data.get("active_profile", "shorts")
    prof_name = str(prof_name).strip().lower()

    # Base profile template
    base = dict(DEFAULT_PROFILES.get(prof_name, DEFAULT_PROFILES["shorts"]))

    # Overlay custom profiles from config.yaml if present
    cfg_profiles = data.get("video_profiles", {})
    if isinstance(cfg_profiles, dict) and prof_name in cfg_profiles:
        custom_prof = cfg_profiles[prof_name]
        if isinstance(custom_prof, dict):
            base.update(custom_prof)

    # Legacy mapping: ensure both new and old keys coexist cleanly
    res = {
        "profile_name": prof_name,
        "length_sec": base.get("length_sec", 32),
        "video_length_sec": base.get("length_sec", 32),
        "resolution": base.get("resolution", data.get("resolution", "720x1280")),
        "aspect": base.get("aspect", "9:16"),
        "aspect_ratio": base.get("aspect", data.get("aspect_ratio", "9:16")),
        "sec_per_scene": float(base.get("sec_per_scene", 4.5)),
        "subtitles": base.get("subtitles", "kinetic"),
        "subtitles_style": base.get("subtitles", "kinetic"),
        "chapters": bool(base.get("chapters", False)),
        "max_length_sec": int(base.get("max_length_sec", 3600)),
    }
    for k, v in base.items():
        if k not in res:
            res[k] = v

    return res


# Poore system ke liye ek hi shared config object
CONFIG = load()

if __name__ == "__main__":
    # `python core/config.py` chalao to config print hogi — debug ke liye
    for k, v in CONFIG.items():
        print(f"{k:22} = {v!r}")
    print("\n--- PROFILES ---")
    print("Shorts profile:", get_profile("shorts"))
    print("Longform profile:", get_profile("longform"))
