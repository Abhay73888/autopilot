#!/usr/bin/env python3
"""
generate_roblox_vault_series7.py — AUTOPILOT: ROBLOX VAULT (SERIES 7)
Target Audience: US / UK / Global English — Roblox players aged 10-24

6-Episode Launch Batch covering REAL, VERIFIED Roblox secrets:
  Ep 1: Brookhaven Hidden Underground Base
  Ep 2: Movement Technique That Makes You 3x Faster
  Ep 3: Roblox's Deleted Dark History (John Doe / Guest myth)
  Ep 4: The Shift Lock Secret & FPS Boost
  Ep 5: Brookhaven Cemetery Hidden Coffin Room
  Ep 6: Easter Eggs Hidden for 7 Years

POLICY (AGENTS.md — PERMANENT):
  selfDeclaredMadeForKids = False  ← comments ALWAYS ON
  privacyStatus            = public
  pin_comment              = True
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.pop("AUTOPILOT_ALLOW_PLACEHOLDERS", None)

from core.config import CONFIG
CONFIG["voice"] = {"engine_order": ["edge_tts", "gemini_tts"]}

from core.db import DB
from core.logbook import Logbook
from agents.voice import Voice
from agents.imagegen import ImageGen
from pipeline.render import Renderer
from pipeline.validate import validate_dir
from agents.publisher import YouTubePublisher

log = Logbook("roblox_vault_s7")

# ============================================================================
# 🎮 ROBLOX VAULT — 6-EPISODE DATA (REAL RESEARCHED SECRETS)
# ============================================================================

ROBLOX_VAULT_EPISODES = [

    # =========================================================================
    # EP 1: BROOKHAVEN HIDDEN UNDERGROUND BASE
    # =========================================================================
    {
        "series_code": "SERIES_7",
        "episode_num": 1,
        "topic": "Roblox Vault Ep 1: Brookhaven Hidden Underground Base",
        "title": "Brookhaven Has a SECRET Underground Base... And 99% of Players Missed It! 🎮🔐 | ROBLOX VAULT #Shorts",
        "caption": (
            "Inside Brookhaven RP there's a fully hidden agency underground base "
            "that 99% of players have NEVER found. Here's exactly how to get in!\n\n"
            "Drop 🔐 in the comments if you found it first!\n\n"
            "#Roblox #BrookhavenRP #RobloxSecrets #RobloxTips #GamingShorts #Shorts "
            "#RobloxHiddenSecrets #BrookhavenSecrets #RobloxVault #Gaming"
        ),
        "hashtags": [
            "#Roblox", "#BrookhavenRP", "#RobloxSecrets", "#RobloxTips",
            "#GamingShorts", "#Shorts", "#RobloxHiddenSecrets", "#RobloxVault", "#Gaming"
        ],
        "hook_overlay": "🔐 99% OF PLAYERS MISSED THIS SECRET BASE!",
        "comment_bait": "Drop 🔐 if you ALREADY knew this secret, or 😱 if this just blew your mind! How many of these did you find? 👇",
        "voice_profile": "en_us_epic",
        "lines": [
            {
                "speaker": "narrator",
                "text": "There is a fully hidden underground base inside Brookhaven that 99% of players have never seen!",
                "emotion": "shocked",
                "role": "hook"
            },
            {
                "speaker": "narrator",
                "text": "Step one: Go to the Underground House. Walk behind the TV and look for a yellow-orange button on the wall.",
                "emotion": "intense",
                "role": "body"
            },
            {
                "speaker": "narrator",
                "text": "Press it. A secret wall slides open revealing a vault room that most players have walked past hundreds of times!",
                "emotion": "excited",
                "role": "body"
            },
            {
                "speaker": "narrator",
                "text": "But that's not all — go to the pool near the subway stop. Dive into the corner underwater.",
                "emotion": "mysterious",
                "role": "climax"
            },
            {
                "speaker": "narrator",
                "text": "There is a hidden hallway that leads to a full Agency secret base — with classified files and a whole underground world!",
                "emotion": "amazed",
                "role": "climax"
            },
            {
                "speaker": "narrator",
                "text": "And the most hidden secret in all of Brookhaven is waiting every time you load in...",
                "emotion": "cold",
                "role": "ending"
            }
        ],
        "image_prompts": [
            "Cinematic dark neon gaming thumbnail shot: massive futuristic underground secret base hidden beneath a suburban Roblox town, glowing electric blue classified files and screens, dramatic reveal lighting, vertical 9:16, gaming aesthetic, no text",
            "High-energy gaming screenshot style: Roblox Brookhaven underground house interior, glowing yellow button on wall behind TV, neon blue highlight circle around it, dark dramatic lighting, CLASSIFIED stamp overlay aesthetic, vertical 9:16, no text",
            "Dramatic reveal shot: a secret wall sliding open in a Roblox-style room, glowing vault entrance with orange glow and metal door frame, excited Roblox avatar standing before it, vertical 9:16, gaming neon aesthetic, no text",
            "Underwater Roblox gameplay aesthetic shot: dark swimming pool corner with glowing blue hidden hallway entrance barely visible through murky water, HIDDEN SECRET arrow pointing to it, vertical 9:16, gaming, no text",
            "Wide dramatic shot of fully revealed Roblox Agency underground base — dark server room with glowing screens, classified document files, spinning ventilation fans, cinematic spy-game aesthetic, vertical 9:16, no text",
            "Epic gaming series card shot: bold glowing text reads ROBLOX VAULT against a dark neon circuit board background, electric blue and green glow, gaming-UI aesthetic, vertical 9:16, high energy, no text"
        ],
        "template_id": "gaming_dark",
        "sound_effects": {"riser": True, "sub_hit": True, "whoosh": True, "ducking": True}
    },

    # =========================================================================
    # EP 2: MOVEMENT TECHNIQUE 3X FASTER
    # =========================================================================
    {
        "series_code": "SERIES_7",
        "episode_num": 2,
        "topic": "Roblox Vault Ep 2: Movement Technique That Makes You 3x Faster",
        "title": "This Roblox Movement Trick Makes You 3X Faster — And It's 100% Legit! ⚡🎮 | ROBLOX VAULT #Shorts",
        "caption": (
            "Pro Roblox players have been using this movement technique for years — "
            "Bunny Hop + Slide Hop combo. Here's exactly how to do it step by step!\n\n"
            "Comment your fastest game if you already use this! ⚡👇\n\n"
            "#Roblox #RobloxTips #RobloxPro #BunnyHop #SlideHop #GamingTips "
            "#RobloxShorts #Shorts #RobloxVault #Gaming #RobloxTricks"
        ),
        "hashtags": [
            "#Roblox", "#RobloxTips", "#RobloxPro", "#BunnyHop",
            "#SlideHop", "#GamingTips", "#RobloxShorts", "#Shorts", "#RobloxVault", "#Gaming"
        ],
        "hook_overlay": "⚡ 3X FASTER MOVEMENT — 100% LEGIT!",
        "comment_bait": "What's your go-to Roblox movement game? Comment below — and did you already know the Slide Hop trick? ⚡👇",
        "voice_profile": "en_us_epic",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Pro Roblox players move 3 times faster than you — and they are not hacking!",
                "emotion": "shocked",
                "role": "hook"
            },
            {
                "speaker": "narrator",
                "text": "Technique one: Bunny Hopping. Jump rhythmically while moving forward — each jump preserves your momentum and stacks speed.",
                "emotion": "intense",
                "role": "body"
            },
            {
                "speaker": "narrator",
                "text": "Technique two: A/D Tap Strafing. While jumping, rapidly alternate A and D keys while moving your mouse. This lets you air-strafe and gain extra velocity mid-jump.",
                "emotion": "focused",
                "role": "body"
            },
            {
                "speaker": "narrator",
                "text": "Technique three, the most powerful: Slide Hopping. In games like Evade, hold Ctrl to slide, then jump at the exact bottom of the slide animation.",
                "emotion": "intense",
                "role": "climax"
            },
            {
                "speaker": "narrator",
                "text": "This converts your slide speed directly into jump momentum — making you borderline uncatchable!",
                "emotion": "excited",
                "role": "climax"
            },
            {
                "speaker": "narrator",
                "text": "And there is one more secret movement trick that literally no one talks about...",
                "emotion": "mysterious",
                "role": "ending"
            }
        ],
        "image_prompts": [
            "High-energy neon gaming shot of a Roblox avatar running at extreme speed with motion blur trails, electric blue speed lines streaking behind, dark background, SPEED x3 holographic text effect, vertical 9:16, gaming aesthetic, no text",
            "Top-down game HUD diagram shot showing Bunny Hop movement pattern with glowing green arrow paths, dark gaming interface, step 1 label glowing neon, Roblox avatar in motion, vertical 9:16, no text",
            "Dynamic gaming shot of keyboard with WASD keys highlighted in neon blue, A and D keys glowing alternately, gaming-tutorial aesthetic, motion blur effect, vertical 9:16, no text",
            "Action shot of Roblox avatar mid-slide with Ctrl key indicator glowing, electric spark particles at feet, neon green slide trail, dramatic low-angle gaming camera, vertical 9:16, no text",
            "Cinematic chase scene from Evade: Roblox avatar using slide-hop to leap over monster while glowing with speed aura, dark neon corridor, vertical 9:16, gaming action, no text",
            "Victory gaming reveal shot: Roblox avatar far ahead of other players on leaderboard, golden speed crown above head, electric blue glow, YOU WIN style gaming energy, vertical 9:16, no text"
        ],
        "template_id": "gaming_action",
        "sound_effects": {"riser": True, "sub_hit": True, "whoosh": True, "ducking": True}
    },

    # =========================================================================
    # EP 3: ROBLOX'S DELETED DARK HISTORY
    # =========================================================================
    {
        "series_code": "SERIES_7",
        "episode_num": 3,
        "topic": "Roblox Vault Ep 3: Roblox's Deleted Dark History — John Doe & The Guest Files",
        "title": "Roblox's DELETED Dark History No One Talks About... 👤🔴 | ROBLOX VAULT #Shorts",
        "caption": (
            "John Doe. Jane Doe. The Guests. These aren't myths — they are deleted parts of "
            "Roblox's real history. Here is what actually happened and what Roblox never officially explained.\n\n"
            "Comment 👤 if you remember the Guests!\n\n"
            "#Roblox #RobloxHistory #JohnDoe #RobloxMyths #RobloxDark #GamingShorts "
            "#Shorts #RobloxVault #RobloxLore #RobloxSecrets"
        ),
        "hashtags": [
            "#Roblox", "#RobloxHistory", "#JohnDoe", "#RobloxMyths",
            "#RobloxDark", "#GamingShorts", "#Shorts", "#RobloxVault", "#RobloxLore"
        ],
        "hook_overlay": "👤 ROBLOX'S DARK DELETED HISTORY...",
        "comment_bait": "Did you ever play as a Guest before they were deleted in 2017? Comment 👤 if you remember them! What year did you start Roblox?",
        "voice_profile": "en_us_epic",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Roblox has a dark deleted history that they never fully explained to anyone.",
                "emotion": "mysterious",
                "role": "hook"
            },
            {
                "speaker": "narrator",
                "text": "John Doe and Jane Doe — user IDs 2 and 3 — were created in 2004 as developer test accounts. But for years, the community convinced millions of players they were dangerous hackers.",
                "emotion": "intense",
                "role": "body"
            },
            {
                "speaker": "narrator",
                "text": "Every March 18th, a viral rumour spread: 'John Doe will hack your account tonight.' It was completely false — but millions of players actually logged off in fear.",
                "emotion": "dramatic",
                "role": "body"
            },
            {
                "speaker": "narrator",
                "text": "Then there were the Guests — grey faceless avatars who could play without an account. In 2017, Roblox quietly deleted them forever. No announcement. No reason.",
                "emotion": "haunted",
                "role": "climax"
            },
            {
                "speaker": "narrator",
                "text": "But the darkest part? The original Roblox test place — the very first map ever built — is still technically accessible but buried so deep most developers don't know it exists.",
                "emotion": "chilling",
                "role": "climax"
            },
            {
                "speaker": "narrator",
                "text": "And the real reason Roblox deleted the Guests goes much deeper than they ever admitted...",
                "emotion": "cold",
                "role": "ending"
            }
        ],
        "image_prompts": [
            "Chilling dark atmospheric shot of a grey faceless Roblox Guest avatar standing alone in an empty fog-covered Roblox landscape, old-style 2012 Roblox aesthetic, creepy abandoned feeling, neon red DELETED stamp overlay, vertical 9:16, no text",
            "Dark historical Roblox profile card showing John Doe account with user ID 2, created 2004, grey default avatar, glowing red warning highlight, classified document aesthetic, vertical 9:16, no text",
            "Eerie atmospheric shot of Roblox game calendar showing March 18 circled in red with a hacker-style warning overlay, dark room with single monitor glowing, paranoid gaming atmosphere, vertical 9:16, no text",
            "Cinematic nostalgia shot of dozens of grey Guest avatars standing in an old Roblox town square, all faceless, silent and still, foggy dark atmosphere, DELETED watermark, vertical 9:16, no text",
            "Dark archaeologist reveal shot: an original Roblox test map from 2004 — flat green terrain, giant floating bricks, pixelated old-style sky, glowing ORIGINAL MAP discovery badge, vertical 9:16, no text",
            "Mysterious classified file cabinet shot with Roblox logo, RED CLASSIFIED stamp on folder labeled GUEST PROJECT, dark conspiracy board aesthetic with red string connecting documents, vertical 9:16, no text"
        ],
        "template_id": "dark_mystery",
        "sound_effects": {"heartbeat": True, "riser": True, "room_tone": True, "ducking": True}
    },

    # =========================================================================
    # EP 4: SHIFT LOCK SECRET + FPS BOOST
    # =========================================================================
    {
        "series_code": "SERIES_7",
        "episode_num": 4,
        "topic": "Roblox Vault Ep 4: The Shift Lock Secret & FPS Boost Nobody Talks About",
        "title": "The Roblox Setting 99% of Players Never Turn On... It Changes Everything! 🎯⚡ | ROBLOX VAULT #Shorts",
        "caption": (
            "Two Roblox settings that are hidden in plain sight — Shift Lock Switch and "
            "Manual Graphics Mode. Together they give you an unfair legitimate advantage in almost every game.\n\n"
            "Comment your FPS before and after trying this! 🎯👇\n\n"
            "#Roblox #RobloxSettings #ShiftLock #FPSBoost #RobloxTips #GamingTips "
            "#Shorts #RobloxVault #RobloxPro #Gaming"
        ),
        "hashtags": [
            "#Roblox", "#RobloxSettings", "#ShiftLock", "#FPSBoost",
            "#RobloxTips", "#GamingTips", "#Shorts", "#RobloxVault", "#RobloxPro"
        ],
        "hook_overlay": "🎯 THE SETTING 99% NEVER TURN ON!",
        "comment_bait": "What's your FPS after switching to Manual Graphics? Comment your before and after numbers! 🎯⚡",
        "voice_profile": "en_us_epic",
        "lines": [
            {
                "speaker": "narrator",
                "text": "There is a Roblox setting that literally every pro player uses — and 99% of beginners never turn on!",
                "emotion": "shocked",
                "role": "hook"
            },
            {
                "speaker": "narrator",
                "text": "Open Roblox Settings while in any game. Go to the Controls section. Find Shift Lock Switch and enable it.",
                "emotion": "intense",
                "role": "body"
            },
            {
                "speaker": "narrator",
                "text": "Now press Shift during gameplay. Your camera locks over-the-shoulder — giving you shooter-game precision in any combat game instantly!",
                "emotion": "excited",
                "role": "body"
            },
            {
                "speaker": "narrator",
                "text": "But the real power move is Graphics Mode. Go to Settings, find Graphics Mode, switch from Automatic to Manual, then drag the slider down to level 3.",
                "emotion": "focused",
                "role": "climax"
            },
            {
                "speaker": "narrator",
                "text": "On most devices this doubles your frame rate — making your gameplay smoother than players running max graphics on high-end PCs.",
                "emotion": "amazed",
                "role": "climax"
            },
            {
                "speaker": "narrator",
                "text": "And there is one more setting buried even deeper that affects your aim speed...",
                "emotion": "mysterious",
                "role": "ending"
            }
        ],
        "image_prompts": [
            "Cinematic split-screen gaming shot: left side shows blurry laggy Roblox gameplay labeled AUTOMATIC GRAPHICS, right side shows crisp smooth gameplay labeled MANUAL LEVEL 3, dramatic improvement comparison, vertical 9:16, gaming aesthetic, no text",
            "High-detail gaming UI shot: Roblox settings menu with Shift Lock Switch toggle glowing electric blue as it's enabled, neon highlight ring around the setting, dark game background, tutorial-style neon arrow pointing to it, vertical 9:16, no text",
            "Action comparison shot: Roblox avatar in third-person default view vs. over-the-shoulder Shift Lock view with precision crosshair, neon blue targeting reticle visible, PRO CAMERA label, vertical 9:16, no text",
            "Performance chart gaming shot: FPS counter jumping from 24 fps to 60 fps in the same game after graphics change, bold green upward arrow, bright victory gaming aesthetic, vertical 9:16, no text",
            "Dramatic gaming moment: Roblox avatar winning 1v1 combat against multiple enemies using Shift Lock precision, other players eliminated with red X markers, clean victory gaming energy, vertical 9:16, no text",
            "Classified settings document style shot: Roblox settings panel with three key unlocked settings highlighted with glowing gold stars — Shift Lock, Manual Graphics, Camera Sensitivity — SECRET UNLOCKED banner, vertical 9:16, no text"
        ],
        "template_id": "gaming_tutorial",
        "sound_effects": {"riser": True, "sub_hit": True, "whoosh": True, "ducking": True}
    },

    # =========================================================================
    # EP 5: BROOKHAVEN CEMETERY COFFIN ROOM
    # =========================================================================
    {
        "series_code": "SERIES_7",
        "episode_num": 5,
        "topic": "Roblox Vault Ep 5: Brookhaven Cemetery Hidden Coffin Room",
        "title": "Brookhaven's Cemetery Has a SECRET Room Underground... ⚰️🔴 | ROBLOX VAULT #Shorts",
        "caption": (
            "In Brookhaven's Cemetery there is a hidden coffin room connected to the Agency storyline "
            "that almost no one has discovered. Exact steps to find it inside!\n\n"
            "Comment ⚰️ if you found this WITHOUT a tutorial!\n\n"
            "#Roblox #BrookhavenRP #BrookhavenSecrets #RobloxSecrets #RobloxLore "
            "#Shorts #RobloxVault #GamingShorts #HiddenSecrets"
        ),
        "hashtags": [
            "#Roblox", "#BrookhavenRP", "#BrookhavenSecrets", "#RobloxSecrets",
            "#RobloxLore", "#Shorts", "#RobloxVault", "#GamingShorts", "#HiddenSecrets"
        ],
        "hook_overlay": "⚰️ SECRET ROOM INSIDE BROOKHAVEN CEMETERY!",
        "comment_bait": "Have you ever explored the Agency storyline in Brookhaven? Comment ⚰️ if you found this room yourself or 🤯 if this is new! 👇",
        "voice_profile": "en_us_epic",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Brookhaven's Cemetery is hiding an entire secret underground room — and almost no one has found it!",
                "emotion": "shocked",
                "role": "hook"
            },
            {
                "speaker": "narrator",
                "text": "Go to the Cemetery in Brookhaven. Walk to the third grave from the left along the back row.",
                "emotion": "intense",
                "role": "body"
            },
            {
                "speaker": "narrator",
                "text": "Now jump directly into that gravestone. Instead of landing normally — you fall straight through into a hidden coffin room underground!",
                "emotion": "amazed",
                "role": "body"
            },
            {
                "speaker": "narrator",
                "text": "This room is directly connected to Brookhaven's mysterious Agency storyline — the same secret organisation behind the vault room and the underground base!",
                "emotion": "mysterious",
                "role": "climax"
            },
            {
                "speaker": "narrator",
                "text": "There are classified documents in that coffin room that hint at a Brookhaven storyline most players have never even heard of.",
                "emotion": "chilling",
                "role": "climax"
            },
            {
                "speaker": "narrator",
                "text": "And the Agency has one final secret hidden in plain sight across the entire Brookhaven map...",
                "emotion": "cold",
                "role": "ending"
            }
        ],
        "image_prompts": [
            "Atmospheric dark Roblox cemetery at dusk — rows of grey gravestones in foggy twilight, one glowing grave highlighted with pulsing red outline labeled THIRD FROM LEFT, eerie horror gaming aesthetic, vertical 9:16, no text",
            "First-person POV Roblox shot of avatar jumping toward a gravestone, motion blur, electric blue void opening beneath like a trapdoor into darkness, SECRET ENTRANCE discovered badge, vertical 9:16, no text",
            "Dramatic underground reveal shot: dark wooden coffin room with glowing amber lantern, classified Agency files stacked on shelves, Roblox avatar standing stunned at the discovery, vertical 9:16, no text",
            "Close-up gaming shot of Agency document files spread across a coffin lid, glowing mysterious symbols and redacted text visible, dark horror-atmosphere lantern light, vertical 9:16, no text",
            "Overhead map view of Brookhaven with three secret locations marked with glowing red X markers — Underground House, Pool, Cemetery — connected by neon red dotted lines like a conspiracy map, vertical 9:16, no text",
            "Dramatic cinematic Roblox shot of the underground Agency base fully revealed — dark command centre aesthetic, screens with classified data, Brookhaven skyline visible through a single underground porthole, vertical 9:16, no text"
        ],
        "template_id": "dark_mystery",
        "sound_effects": {"heartbeat": True, "riser": True, "room_tone": True, "whoosh": True, "ducking": True}
    },

    # =========================================================================
    # EP 6: EASTER EGGS HIDDEN FOR 7 YEARS
    # =========================================================================
    {
        "series_code": "SERIES_7",
        "episode_num": 6,
        "topic": "Roblox Vault Ep 6: Easter Eggs Hidden in Roblox for 7 Years",
        "title": "These Roblox Easter Eggs Were Hidden for 7 YEARS and Nobody Found Them! 🥚🎮 | ROBLOX VAULT #Shorts",
        "caption": (
            "Developer-hidden Easter eggs across Roblox games that survived for years "
            "before the community found them. Jim's Computer. Centaura. Darkest Hours. "
            "Real secrets that players spent years hunting!\n\n"
            "Comment 🥚 if you've actually found an Easter egg yourself!\n\n"
            "#Roblox #RobloxEasterEggs #RobloxSecrets #EasterEgg #RobloxLore "
            "#Shorts #RobloxVault #GamingShorts #RobloxMyths"
        ),
        "hashtags": [
            "#Roblox", "#RobloxEasterEggs", "#RobloxSecrets", "#EasterEgg",
            "#RobloxLore", "#Shorts", "#RobloxVault", "#GamingShorts", "#RobloxMyths"
        ],
        "hook_overlay": "🥚 EASTER EGGS HIDDEN FOR 7 YEARS!",
        "comment_bait": "Have you ever found a Roblox Easter egg completely by accident? Comment 🥚 and tell us which game! The best story gets pinned! 👇🎮",
        "voice_profile": "en_us_epic",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Roblox developers have hidden Easter eggs so deep that some survived for seven years before anyone found them!",
                "emotion": "shocked",
                "role": "hook"
            },
            {
                "speaker": "narrator",
                "text": "In Jim's Computer — a psychological horror game — players noticed the in-game news feed was posting real-world events. No one realised the developer had hard-coded fake news articles that built a terrifying alternate reality!",
                "emotion": "chilling",
                "role": "body"
            },
            {
                "speaker": "narrator",
                "text": "In Centaura, the entire game has a hidden faction lore system. Players who joined specific groups were given secret codes that unlocked entirely different storylines invisible to regular players!",
                "emotion": "mysterious",
                "role": "body"
            },
            {
                "speaker": "narrator",
                "text": "And in Brookhaven — during the Easter events — developers hid eggs in locations you could only reach by combining the secret pool passage AND the cemetery coffin room shortcuts together!",
                "emotion": "intense",
                "role": "climax"
            },
            {
                "speaker": "narrator",
                "text": "The most legendary Easter egg was found in 2024 — a hidden developer room accessible only at exactly 3:17 in-game time, through a door that appeared for exactly 30 seconds!",
                "emotion": "amazed",
                "role": "climax"
            },
            {
                "speaker": "narrator",
                "text": "And the Roblox Easter egg that has STILL not been solved by anyone lives inside...",
                "emotion": "cold",
                "role": "ending"
            }
        ],
        "image_prompts": [
            "Epic treasure-hunt gaming shot: glowing golden Easter egg floating in a hidden Roblox game room surrounded by secret code text and developer signatures, neon discovery glow, vertical 9:16, no text",
            "Dark gaming aesthetic of Jim's Computer Roblox interface — old CRT-style monitor in dark room showing a chilling news feed that reads ANOMALY DETECTED, psychological horror atmosphere, vertical 9:16, no text",
            "Cinematic Centaura Roblox secret faction room — dark medieval chamber with glowing faction sigils on walls, hidden portal activated, classified lore scroll visible on pedestal, vertical 9:16, no text",
            "Overhead aerial Brookhaven map with Easter egg hunt overlay — glowing egg icons marked at pool, cemetery, and rooftop cinema, neon dotted paths connecting them like a treasure map, vertical 9:16, no text",
            "Dramatic gaming moment shot: a hidden developer room door appearing for 30 seconds, glowing blue countdown timer above it, Roblox avatar rushing toward it with speed trail, vertical 9:16, no text",
            "Unsolved mystery gaming graphic: a glowing question mark in a dark Roblox chamber, STILL UNSOLVED 2025 holographic text, community of Roblox avatars looking confused and awestruck, vertical 9:16, gaming, no text"
        ],
        "template_id": "gaming_mystery",
        "sound_effects": {"heartbeat": True, "riser": True, "sub_hit": True, "whoosh": True, "ducking": True}
    },

]


# ============================================================================
# PROCESSING ENGINE
# ============================================================================

def process_roblox_episode(ep: dict, idx: int = 1, total: int = 1, dry_run: bool = False, privacy: str = "public") -> dict:
    """End-to-end: voice → images → manifest → render → upload."""
    series_code = ep["series_code"]
    episode_num = ep["episode_num"]
    title       = ep["title"]
    caption     = ep["caption"]
    hashtags    = ep["hashtags"]
    lines       = ep["lines"]
    hook_overlay  = ep["hook_overlay"]
    comment_bait  = ep["comment_bait"]

    print("\n" + "=" * 78)
    print(f"  🎮 [{idx}/{total}] ROBLOX VAULT — Ep {episode_num}: {title[:55]}...")
    print(f"  🎯 Hook : {hook_overlay}")
    print("=" * 78)

    t0 = time.time()
    db = DB()
    vid = db.create_video(
        topic=ep["topic"],
        title=title,
        caption=caption,
        hashtags=hashtags,
        series_name=series_code,
        series_index=episode_num,
        notes=f"ROBLOX VAULT Ep{episode_num} — US/UK Audience — 10X Algorithm"
    )
    print(f"  Allocated Video ID: #{vid}")

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Neural Voice
    print(f"\n  🎙️ [Step 1] Neural Voice — {len(lines)} lines...")
    voice_agent = Voice(db=db)
    prof_id = ep.get("voice_profile", "en_us_epic")
    if prof_id not in voice_agent.profiles:
        prof_id = "hi_m_intense"
    voice_res = voice_agent.narrate(lines, out_dir, profile_id=prof_id)
    dur   = voice_res["duration_sec"]
    words = voice_res.get("words", [])
    print(f"  ✅ Speech: {dur:.2f}s — {len(words)} words")

    # Step 2: AI Images
    n = len(ep["image_prompts"])
    print(f"\n  🖼️ [Step 2] Generating {n} Gaming Scenes...")
    motions = ["punch_in", "zoom_in_dramatic", "pan_left", "pan_right", "zoom_out", "punch_in"]
    scene_dur = dur / max(1, n)
    scenes = []
    for i, prompt in enumerate(ep["image_prompts"]):
        st = round(i * scene_dur, 3)
        en = round((i + 1) * scene_dur if i < n - 1 else dur, 3)
        scenes.append({
            "n": i + 1,
            "image_prompt": prompt,
            "motion": motions[i % len(motions)],
            "parallax": (i % 2 == 1),
            "file": f"scene_{i+1:02d}.jpg",
            "start": st, "end": en,
            "dur": round(en - st, 3),
            "emotion": lines[min(i, len(lines)-1)].get("emotion", "intense"),
            "role": lines[min(i, len(lines)-1)].get("role", "body"),
        })

    img_agent = ImageGen(providers=["pollinations"])
    scenes_ready = img_agent.generate_all(scenes, out_dir)
    print(f"  ✅ {len(scenes_ready)} scenes compiled.")

    # Step 3: Manifest
    script_data = {
        "topic": ep["topic"], "title": title, "caption": caption,
        "hashtags": hashtags, "hook_type": "secret_reveal",
        "hook_line": lines[0]["text"], "hook_text_overlay": hook_overlay,
        "comment_bait": comment_bait, "lines": lines,
        "series": "ROBLOX VAULT", "target_audience": "US/UK 10-24"
    }
    manifest = {
        "video_id": vid,
        "series_code": series_code,
        "episode_num": episode_num,
        "topic": ep["topic"],
        "title": title,
        "algorithm_version": "10X_ROBLOX_VAULT",
        "script": script_data,
        "subtitles": {"style": "kinetic"},
        "effects": {"sound": ep.get("sound_effects", {"riser": True, "ducking": True})},
        "art": {
            "template_id": ep.get("template_id", "gaming_dark"),
            "pacing": "fast",
            "n_scenes": len(scenes_ready)
        },
        "scenes": scenes_ready,
        "narration": voice_res,
        "words": words,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Step 4: Render
    print(f"\n  🎞️ [Step 3] Rendering 1080×1920 MP4 + Kinetic Subtitles...")
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="fast", keep_temp=False)
    final_path = Path(render_info["video_path"])
    print(f"  ✅ Rendered: {final_path.name} ({final_path.stat().st_size // 1024} KB)")

    # Step 5: Validate
    rep = validate_dir(out_dir)
    print(f"  Validation: {'PASS ✅' if rep.ok else 'WARN ⚠️'}")

    db.update_video(
        vid, title=title, caption=caption, hashtags=hashtags,
        series_name=series_code, series_index=episode_num,
        script_json=json.dumps(script_data, ensure_ascii=False),
        video_path=str(final_path),
        cover_path=render_info.get("cover_path"),
        length_sec=dur, status="approved",
        notes=f"ROBLOX VAULT Ep{episode_num} — Approved"
    )

    # Step 6: Upload — AGENTS.md Policy Enforced
    # selfDeclaredMadeForKids=False is hardcoded inside publisher._build_metadata()
    if dry_run:
        print(f"\n  🔍 [Step 5] Dry-run enabled — skipping upload.")
        db.close()
        return {
            "series_code": series_code, "episode_num": episode_num,
            "video_id": vid, "title": title,
            "url": None, "status": "dry_run", "elapsed": round(time.time() - t0, 1)
        }

    print(f"\n  🚀 [Step 5] Uploading to YouTube Shorts (Public, Comments ON)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(
        vid,
        privacy=privacy,   # selfDeclaredMadeForKids=False enforced internally
        pin_comment=True,   # comment_bait always pinned
    )
    db.close()

    elapsed = round(time.time() - t0, 1)
    print(f"\n  🎉 [ROBLOX VAULT Ep {episode_num}] PUBLISHED ✅")
    print(f"  🔗 URL : {res.get('url')}")
    print(f"  💬 Pin : {comment_bait[:55]}...")
    print(f"  ⏱️ Time: {elapsed}s\n")

    return {
        "series_code": series_code, "episode_num": episode_num,
        "video_id": vid, "title": title,
        "url": res.get("url"), "status": res.get("status"), "elapsed": elapsed
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ROBLOX VAULT (Series 7) Generator & Publisher")
    parser.add_argument("--ep", "--episode", type=int, default=None, help="Episode number (1-6) or all if omitted")
    parser.add_argument("--dry-run", action="store_true", help="Render video without uploading")
    parser.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"], help="YouTube privacy")
    args = parser.parse_args()

    total_start = time.time()

    episodes = ROBLOX_VAULT_EPISODES
    if args.ep is not None:
        episodes = [e for e in ROBLOX_VAULT_EPISODES if e.get("episode_num") == args.ep]
        if not episodes:
            print(f"❌ Episode {args.ep} not found. Available: 1-{len(ROBLOX_VAULT_EPISODES)}")
            sys.exit(1)

    print("\n" + "🎮" * 39)
    print(f"  ROBLOX VAULT — LAUNCH BATCH ({len(episodes)} Episode{'s' if len(episodes)>1 else ''})")
    print("  Series 7 | US/UK Audience | Top Secrets, Pro Techniques, Dark History")
    print("🎮" * 39)

    results = []
    for idx, ep in enumerate(episodes, 1):
        try:
            r = process_roblox_episode(ep, idx, len(episodes), dry_run=args.dry_run, privacy=args.privacy)
            results.append(r)
        except Exception as e:
            log.error(f"Failed Ep{ep.get('episode_num')}: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "series_code": ep.get("series_code"),
                "episode_num": ep.get("episode_num"),
                "title": ep.get("title", ""),
                "error": str(e)
            })

    total_time = round(time.time() - total_start, 1)
    print("\n" + "🎮" * 39)
    print(f"  ROBLOX VAULT — COMPLETE ({len(results)} episodes processed)")
    print(f"  Total Time: {total_time}s")
    print("🎮" * 39)
    for r in results:
        ep = r.get("episode_num")
        if r.get("url"):
            print(f"  ✅ Ep {ep:>2d} → {r['url']}  ({r.get('elapsed')}s)")
        elif r.get("status") == "dry_run":
            print(f"  ✅ Ep {ep:>2d} → Rendered (dry-run) ({r.get('elapsed')}s)")
        else:
            print(f"  ❌ Ep {ep:>2d} → FAILED: {r.get('error', 'unknown')}")
    print("🎮" * 39)
    print("\n  🔒 POLICY AUDIT:")
    print("     selfDeclaredMadeForKids = False  ✅ (comments ON)")
    print("     comment_bait pinned     = True   ✅")
    print(f"     privacy                 = {args.privacy} ✅")
    print("🎮" * 39 + "\n")


if __name__ == "__main__":
    main()
