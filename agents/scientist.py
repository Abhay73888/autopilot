"""
agents/scientist.py — A/B experiment framework (Phase 8). YE TUMHARA MOAT HAI.

Section 6 ke rules jo yahan enforce hote hain:
  * Ek time pe SIRF EK variable test karo (proper A/B, multivariate nahi)
  * Har experiment: hypothesis -> sample size -> result -> learning DB mein save
  * Sirf tab conclude karo jab statistically meaningful ho (min 5 videos per arm)
  * Winning variants ko DEFAULT banao, losing ko rotation se hatao

Testable variables (Section 6):
  hook_type | length | publish_hour | voice_id | template_id | caption_style

KAISE KAAM KARTA HAI:
  1. design()   — Scientist khud decide karta hai ki ab kya test karna chahiye
                  (jo variable ab tak test nahi hua, ya jiski learning purani ho gayi)
  2. assign()   — har naye video ko A ya B arm mein daalta hai (alternate, taaki
                  dono arms ek hi time window mein publish hon — warna time
                  confound ban jaata hai)
  3. evaluate() — 2h velocity metrics se dono arms compare karta hai (Welch's t-test)
  4. conclude() — learning DB mein save + winner ko default bana deta hai

⚠️ IMANDARI: n=5 per arm pe statistics kamzor hoti hai. Isliye:
   - confidence 'high' tab hi milti hai jab n>=8 AND effect bada ho
   - MDE (minimum detectable effect) bhi report hota hai — beginner ko pata rahe
     ki "n=5 pe sirf 75%+ ka farq dikhega, 10% ka nahi"
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from core.db import DB
from core.logbook import Logbook
from core.stats import min_detectable_lift, summarize

log = Logbook("scientist")

# ---------------------------------------------------------------------
# Kaunse variables test kar sakte hain, aur unke possible values
# ---------------------------------------------------------------------
def _arms():
    """Late import — circular import se bachne ke liye."""
    from agents.artdirector import TEMPLATES
    from agents.voice import profiles
    from agents.writer import HOOK_TYPES
    return {
        "hook_type": list(HOOK_TYPES),
        "voice_id": list(profiles()),
        "template_id": list(TEMPLATES),
        "length_bucket": ["22-30s", "30-45s"],
        "publish_hour": ["14", "17", "20"],   # IST peak windows (UTC mein convert hota hai)
    }


# Har experiment ke liye default sample size
MIN_PER_ARM = 5          # Section 6 ka minimum
TARGET_PER_ARM = 8       # yahan tak pahunche to 'high' confidence possible hai
MAX_PER_ARM = 15         # isse zyada waste hai — conclude kar do

# Primary metric — kis cheez pe judge karna hai
PRIMARY_METRIC = "views"        # 2h velocity views
SECONDARY_METRICS = ["avg_pct", "comments", "shares"]

# Learning kitni purani hone pe dobara test karni chahiye
RETEST_AFTER_DAYS = 90


class Scientist:
    def __init__(self, db: DB | None = None):
        self.db = db or DB()

    # ==================================================================
    # 1. DESIGN — ab kya test karna chahiye?
    # ==================================================================
    def suggest_next(self) -> dict | None:
        """
        Scientist khud decide karta hai ki agla experiment kya ho.

        Priority:
          1. Jo variable kabhi test hi nahi hua
          2. Jiski learning 90+ din purani ho gayi (algorithm badalta rehta hai)
          3. Jiska result 'low' confidence tha (dobara test karo)
        """
        arms = _arms()
        tested = {r["variable"] for r in self.db.q(
            "SELECT DISTINCT variable FROM experiments WHERE status='concluded'")}
        learned = {r["variable"]: r for r in self.db.active_learnings()}

        # ---- priority 1: kabhi test nahi hua ----
        for var in ("hook_type", "voice_id", "template_id", "length_bucket",
                    "publish_hour"):
            if var not in tested and len(arms.get(var, [])) >= 2:
                return self._design_for(var, arms[var], reason="ye variable kabhi test nahi hua")

        # ---- priority 2: purani ya kamzor learning ----
        for var, l in learned.items():
            if var not in arms:
                continue
            age_days = _age_days(l["ts"])
            if age_days > RETEST_AFTER_DAYS:
                return self._design_for(var, arms[var],
                                        reason=f"learning {age_days:.0f} din purani hai — "
                                               f"algorithm badal chuka hoga")
            if l["confidence"] == "low":
                return self._design_for(var, arms[var],
                                        reason="pichhli baar result kamzor tha (low confidence)")

        # ---- priority 3: jo variable learn nahi hua ----
        for var in arms:
            if var not in learned and len(arms[var]) >= 2:
                return self._design_for(var, arms[var], reason="abhi tak koi conclusion nahi")

        return None

    def _design_for(self, variable: str, options: list[str], reason: str) -> dict:
        """Ek variable ke liye A/B arms chuno."""
        # jeeta hua variant hai to usse champion (A) banao, challenger (B) naya
        learned = self.db.active_learnings(variable)
        champion = learned[0]["winner"] if learned and learned[0]["winner"] in options \
            else options[0]
        challengers = [o for o in options if o != champion]

        # jo challenger sabse kam test hua hai usse chuno
        counts = {o: 0 for o in challengers}
        for r in self.db.q(f"SELECT {_col(variable)} v, COUNT(*) n FROM videos "
                           f"WHERE {_col(variable)} IS NOT NULL GROUP BY v"):
            if r["v"] in counts:
                counts[r["v"]] = r["n"]
        challenger = min(counts, key=counts.get) if counts else options[-1]

        return {
            "variable": variable,
            "arm_a": champion,
            "arm_b": challenger,
            "hypothesis": f"'{challenger}' ({variable}) '{champion}' se behtar 2h "
                          f"velocity dega",
            "reason": reason,
            "min_per_arm": MIN_PER_ARM,
            "videos_needed": MIN_PER_ARM * 2,
            "mde_pct": min_detectable_lift(MIN_PER_ARM),
        }

    # ==================================================================
    def start(self, variable: str | None = None, arm_a: str | None = None,
              arm_b: str | None = None, hypothesis: str | None = None) -> dict:
        """Naya experiment shuru karo. Ek time pe sirf ek chal sakta hai."""
        running = self.db.running_experiment()
        if running:
            return {"ok": False,
                    "error": f"Experiment #{running['id']} ({running['variable']}) "
                             f"pehle se chal raha hai. Ek time pe ek hi variable — "
                             f"warna pata nahi chalega ki kis cheez ne farq daala.",
                    "running": dict(running)}

        if variable:
            arms = _arms()
            opts = arms.get(variable)
            if not opts:
                return {"ok": False, "error": f"'{variable}' testable nahi hai. "
                                              f"Allowed: {list(arms)}"}
            design = self._design_for(variable, opts, reason="manually shuru kiya")
            if arm_a:
                design["arm_a"] = arm_a
            if arm_b:
                design["arm_b"] = arm_b
        else:
            design = self.suggest_next()
            if not design:
                return {"ok": False, "error": "Abhi koi experiment suggest nahi hai — "
                                              "sab variables test ho chuke hain"}

        if design["arm_a"] == design["arm_b"]:
            return {"ok": False, "error": "Dono arms same hain — test ka matlab nahi"}

        exp_id = self.db.create_experiment(
            design["variable"], hypothesis or design["hypothesis"],
            design["arm_a"], design["arm_b"], MIN_PER_ARM)

        log.ok(f"🧪 Experiment #{exp_id} shuru: {design['variable']}",
               A=design["arm_a"], B=design["arm_b"])
        print(f"\n  🧪 EXPERIMENT #{exp_id}")
        print(f"     Variable   : {design['variable']}")
        print(f"     Hypothesis : {design.get('hypothesis')}")
        print(f"     Arm A      : {design['arm_a']}   (champion)")
        print(f"     Arm B      : {design['arm_b']}   (challenger)")
        print(f"     Chahiye    : {MIN_PER_ARM} videos per arm ({MIN_PER_ARM*2} total)")
        print(f"     ⚠️ Is sample size pe sirf ~{design.get('mde_pct', 0):.0f}%+ ka")
        print(f"        farq detect ho payega. Chhota farq dikhega hi nahi.\n")
        return {"ok": True, "experiment_id": exp_id, **design}

    # ==================================================================
    # 2. ASSIGN — naye video ko arm do
    # ==================================================================
    def assign(self, video_id: int) -> dict | None:
        """
        Naye video ko A ya B arm mein daalo.

        ⚠️ ALTERNATE assignment (random nahi): A, B, A, B...
        Kyun? Kyunki agar random se saare A pehle publish ho jayein aur B baad mein,
        to time-of-day / algorithm mood confound ban jaata hai. Alternate karne se
        dono arms same conditions dekhte hain.
        """
        exp = self.db.running_experiment()
        if not exp:
            return None

        counts = self._arm_counts(exp["id"])
        if counts["A"] + counts["B"] >= MAX_PER_ARM * 2:
            log.warn(f"Experiment #{exp['id']} mein kaafi videos ho gaye — "
                     f"conclude karo")
            return None

        variant = "A" if counts["A"] <= counts["B"] else "B"
        value = exp["arm_a"] if variant == "A" else exp["arm_b"]
        column = _col(exp["variable"])

        # video pe variable set karo (agar wo column hai to)
        updates = {"experiment_id": exp["id"], "variant": variant}
        if column in ("hook_type", "voice_id", "template_id"):
            updates[column] = value
        self.db.update_video(video_id, **updates)

        log.info(f"Video #{video_id} -> experiment #{exp['id']} arm {variant} "
                 f"({exp['variable']}={value})")
        return {"experiment_id": exp["id"], "variant": variant,
                "variable": exp["variable"], "value": value}

    def forced_value(self, variable: str) -> str | None:
        """
        Agar chal rahe experiment ka variable yahi hai, to agent ko batao ki
        kaunsi value use karni hai (rotation override).
        Writer/Voice/ArtDirector ise call karte hain.
        """
        exp = self.db.running_experiment()
        if not exp or exp["variable"] != variable:
            return None
        counts = self._arm_counts(exp["id"])
        return exp["arm_a"] if counts["A"] <= counts["B"] else exp["arm_b"]

    def _arm_counts(self, exp_id: int) -> dict:
        rows = self.db.q("SELECT variant, COUNT(*) n FROM videos "
                         "WHERE experiment_id=? GROUP BY variant", (exp_id,))
        c = {"A": 0, "B": 0}
        for r in rows:
            if r["variant"] in c:
                c[r["variant"]] = r["n"]
        return c

    # ==================================================================
    # 3. EVALUATE — dono arms compare karo
    # ==================================================================
    def evaluate(self, exp_id: int | None = None, window: str = "2h") -> dict:
        """
        Chal rahe experiment ko dekho. Kaafi data hai to result do.
        Ye khud conclude NAHI karta — wo alag step hai.
        """
        exp = (self.db.one("SELECT * FROM experiments WHERE id=?", (exp_id,))
               if exp_id else self.db.running_experiment())
        if not exp:
            return {"ok": False, "error": "Koi experiment chal nahi raha"}

        data = {}
        for variant in ("A", "B"):
            rows = self.db.q(f"""
                SELECT m.{PRIMARY_METRIC} val, m.avg_pct, m.comments, m.shares
                FROM videos v JOIN metrics m ON m.video_id = v.id
                WHERE v.experiment_id=? AND v.variant=? AND m.window=?
                  AND m.{PRIMARY_METRIC} IS NOT NULL""",
                (exp["id"], variant, window))
            data[variant] = [float(r["val"]) for r in rows]

        n_a, n_b = len(data["A"]), len(data["B"])
        counts = self._arm_counts(exp["id"])

        base = {
            "ok": True, "experiment_id": exp["id"], "variable": exp["variable"],
            "arm_a": exp["arm_a"], "arm_b": exp["arm_b"],
            "hypothesis": exp["hypothesis"],
            "videos_assigned": counts,
            "metrics_ready": {"A": n_a, "B": n_b},
            "min_per_arm": exp["min_per_arm"] or MIN_PER_ARM,
        }

        if n_a < (exp["min_per_arm"] or MIN_PER_ARM) or n_b < (exp["min_per_arm"] or MIN_PER_ARM):
            need = (exp["min_per_arm"] or MIN_PER_ARM)
            base.update({
                "ready": False,
                "status": f"Abhi data kam hai: A={n_a}/{need}, B={n_b}/{need}",
                "message": f"Aur {max(0, need-n_a)} videos arm A mein, "
                           f"{max(0, need-n_b)} arm B mein chahiye. "
                           f"Jaldbazi mein conclude karna = jhoothi learning.",
            })
            return base

        stat = summarize(data["A"], data["B"], exp["arm_a"], exp["arm_b"])
        base.update({"ready": True, **stat})
        base["recommendation"] = _recommend(stat)
        base["explanation"] = _explain_result(exp, stat)
        return base

    # ==================================================================
    # 4. CONCLUDE — learning save karo, winner ko default banao
    # ==================================================================
    def conclude(self, exp_id: int | None = None, force: bool = False) -> dict:
        """
        Experiment khatam karo aur learning DB mein save karo.
        force=True se kam data pe bhi conclude kar sakte ho (par confidence low hogi).
        """
        ev = self.evaluate(exp_id)
        if not ev.get("ok"):
            return ev
        if not ev.get("ready") and not force:
            return {**ev, "concluded": False,
                    "error": "Abhi conclude mat karo — " + ev.get("status", "")}

        exp_id = ev["experiment_id"]

        if not ev.get("ready"):
            # force mode — koi learning save nahi, sirf abandon
            self.db.conclude_experiment(exp_id, {"abandoned": True,
                                                 "reason": "force, data kam tha"})
            log.warn(f"Experiment #{exp_id} abandon kiya (data kam tha) — "
                     f"koi learning save nahi hui")
            return {**ev, "concluded": True, "learning_saved": False,
                    "verdict": "ABANDONED — data kam tha, koi conclusion nahi"}

        significant = ev["significant"]
        conf = ev["confidence"]

        result = {
            "winner": ev["winner"], "loser": ev["loser"],
            "lift_pct": ev["lift_pct"], "p": ev["p"], "t": ev["t"],
            "cohens_d": ev["cohens_d"], "confidence": conf,
            "n_a": ev["n_a"], "n_b": ev["n_b"],
            "significant": significant, "mde_pct": ev["mde_pct"],
        }
        self.db.conclude_experiment(exp_id, result)

        learning_saved = False
        if significant:
            self.db.add_learning(
                ev["variable"], ev["winner"], ev["loser"], ev["lift_pct"],
                min(ev["n_a"], ev["n_b"]), conf, exp_id,
                note=f"p={ev['p']}, d={ev['cohens_d']}, "
                     f"{PRIMARY_METRIC}@2h: {ev['mean_winner']:.0f} vs {ev['mean_loser']:.0f}")
            learning_saved = True
            log.ok(f"✅ Learning save hui: {ev['variable']} — '{ev['winner']}' jeeta "
                   f"({ev['lift_pct']:+.0f}%, p={ev['p']}, {conf} confidence)")
        else:
            log.info(f"Experiment #{exp_id}: koi significant farq nahi mila "
                     f"(p={ev['p']}). Koi learning save nahi — aur yahi imandari hai.")

        verdict = _verdict_text(ev, learning_saved)
        self.db.log_event("experiment_concluded", "scientist", None,
                          exp_id=exp_id, **result)
        return {**ev, "concluded": True, "learning_saved": learning_saved,
                "verdict": verdict}

    # ==================================================================
    # 5. DEFAULTS — jeete hue variants ko default banao
    # ==================================================================
    def champions(self) -> dict:
        """
        Har variable ka current champion (jo learning se jeeta hua hai).
        Writer/Voice/ArtDirector isse padhte hain.
        """
        out = {}
        for r in self.db.active_learnings():
            var = r["variable"]
            if var in out:
                continue    # sabse nayi learning hi count hoti hai
            if r["confidence"] in ("medium", "high"):
                out[var] = {"value": r["winner"], "lift_pct": r["lift_pct"],
                            "confidence": r["confidence"], "n": r["sample_size"],
                            "avoid": r["loser"]}
        return out

    def losers(self) -> dict:
        """
        Jo variants haar chuke hain — inhe rotation se hata dena chahiye.
        Sirf tab jab confidence 'high' ho (warna galti se accha variant hat jayega).
        """
        out = {}
        for r in self.db.active_learnings():
            if r["confidence"] == "high" and r["loser"]:
                out.setdefault(r["variable"], []).append(r["loser"])
        return out

    # ==================================================================
    def report(self) -> str:
        """Plain Hinglish report — Chief ke briefing ke liye."""
        lines = ["🧪 SCIENTIST REPORT", "=" * 62]

        exp = self.db.running_experiment()
        if exp:
            ev = self.evaluate()
            lines.append(f"Chal raha hai: Experiment #{exp['id']} — {exp['variable']}")
            lines.append(f"  A: {exp['arm_a']}   vs   B: {exp['arm_b']}")
            lines.append(f"  Videos: A={ev['videos_assigned']['A']}, "
                         f"B={ev['videos_assigned']['B']} | "
                         f"metrics ready: A={ev['metrics_ready']['A']}, "
                         f"B={ev['metrics_ready']['B']}")
            if ev.get("ready"):
                lines.append(f"  ➜ {ev['explanation']}")
                lines.append(f"  ➜ Recommendation: {ev['recommendation']}")
            else:
                lines.append(f"  ➜ {ev.get('message', '')}")
        else:
            nxt = self.suggest_next()
            lines.append("Koi experiment nahi chal raha.")
            if nxt:
                lines.append(f"  Suggestion: '{nxt['variable']}' test karo "
                             f"({nxt['arm_a']} vs {nxt['arm_b']})")
                lines.append(f"  Kyun: {nxt['reason']}")
                lines.append(f"  Chalane ke liye: python -m agents.scientist --start")

        champs = self.champions()
        if champs:
            lines.append("\nCurrent champions (ye default ban chuke hain):")
            for var, c in champs.items():
                lines.append(f"  {var:14} = {c['value']:18} "
                             f"({c['lift_pct']:+.0f}%, n={c['n']}, {c['confidence']})")
        else:
            lines.append("\nAbhi koi champion nahi — koi experiment poora nahi hua.")

        los = self.losers()
        if los:
            lines.append("\nRotation se hataye gaye (high confidence pe haare):")
            for var, vals in los.items():
                lines.append(f"  {var}: {', '.join(vals)}")

        done = self.db.q("SELECT * FROM experiments WHERE status='concluded' "
                         "ORDER BY id DESC LIMIT 5")
        if done:
            lines.append("\nPichhle experiments:")
            for r in done:
                try:
                    res = json.loads(r["result_json"] or "{}")
                except json.JSONDecodeError:
                    res = {}
                if res.get("abandoned"):
                    lines.append(f"  #{r['id']} {r['variable']}: abandoned")
                else:
                    lines.append(
                        f"  #{r['id']} {r['variable']}: '{res.get('winner')}' jeeta "
                        f"{res.get('lift_pct', 0):+.0f}% (p={res.get('p')}, "
                        f"{res.get('confidence')})")
        return "\n".join(lines)


# =====================================================================
def _col(variable: str) -> str:
    """Variable name -> videos table ka column."""
    return {"length_bucket": "length_sec", "publish_hour": "published_ts"}.get(
        variable, variable)


def _age_days(ts: str) -> float:
    try:
        t = datetime.fromisoformat(ts)
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - t).total_seconds() / 86400
    except (ValueError, TypeError):
        return 0.0


def _recommend(stat: dict) -> str:
    if not stat["significant"]:
        return (f"Koi clear winner nahi (p={stat['p']}). Ya to farq hai hi nahi, "
                f"ya sample chhota hai. Is sample size pe sirf {stat['mde_pct']:.0f}%+ "
                f"ka farq dikhta hai.")
    if stat["confidence"] == "high":
        return (f"'{stat['winner']}' ko DEFAULT bana do aur '{stat['loser']}' ko "
                f"rotation se hata do.")
    if stat["confidence"] == "medium":
        return (f"'{stat['winner']}' ko prefer karo, par '{stat['loser']}' ko "
                f"rotation mein rehne do — sample abhi chhota hai.")
    return "Result kamzor hai. Aur data lo ya dobara test karo."


def _explain_result(exp, stat: dict) -> str:
    """Plain Hinglish mein result."""
    if not stat["significant"]:
        return (f"'{exp['arm_a']}' ({stat['mean_a']:.0f}) vs '{exp['arm_b']}' "
                f"({stat['mean_b']:.0f}) — farq {abs(stat['lift_pct']):.0f}% hai par "
                f"statistically pakka nahi (p={stat['p']}, chahiye p<0.05). "
                f"Ho sakta hai ye sirf luck ho.")
    return (f"'{stat['winner']}' ne '{stat['loser']}' se {stat['lift_pct']:+.0f}% "
            f"behtar kiya ({stat['mean_winner']:.0f} vs {stat['mean_loser']:.0f} views @2h). "
            f"p={stat['p']} matlab {(1-stat['p'])*100:.1f}% chance ye asli farq hai, "
            f"luck nahi. Confidence: {stat['confidence']} "
            f"(n={stat['n_a']}+{stat['n_b']}).")


def _verdict_text(ev: dict, saved: bool) -> str:
    if not ev["significant"]:
        return (f"NO WINNER — koi significant farq nahi (p={ev['p']}). "
                f"Koi learning save nahi hui. Ye theek hai: jhoothi learning "
                f"save karne se accha kuch na save karna.")
    return (f"WINNER: '{ev['winner']}' ({ev['lift_pct']:+.0f}%, p={ev['p']}, "
            f"{ev['confidence']} confidence). "
            + ("Learning DB mein save ho gaya — agli generation isse use karegi."
               if saved else ""))


# =====================================================================
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="A/B experiments")
    ap.add_argument("--suggest", action="store_true", help="agla experiment suggest karo")
    ap.add_argument("--start", action="store_true", help="naya experiment shuru karo")
    ap.add_argument("--variable", help="kaunsa variable (na do to auto)")
    ap.add_argument("--arm-a"); ap.add_argument("--arm-b")
    ap.add_argument("--status", action="store_true", help="chal rahe experiment ka haal")
    ap.add_argument("--conclude", action="store_true", help="conclude karo")
    ap.add_argument("--force", action="store_true", help="kam data pe bhi conclude")
    ap.add_argument("--champions", action="store_true")
    a = ap.parse_args()

    with DB() as db:
        sci = Scientist(db)
        if a.suggest:
            print(json.dumps(sci.suggest_next(), indent=2, ensure_ascii=False))
        elif a.start:
            print(json.dumps(sci.start(a.variable, a.arm_a, a.arm_b),
                             indent=2, ensure_ascii=False))
        elif a.status:
            print(json.dumps(sci.evaluate(), indent=2, ensure_ascii=False))
        elif a.conclude:
            print(json.dumps(sci.conclude(force=a.force), indent=2, ensure_ascii=False))
        elif a.champions:
            print(json.dumps(sci.champions(), indent=2, ensure_ascii=False))
        else:
            print(sci.report())
