"""
generate_solo_leveling_ragnarok_ch15.py — Solo Leveling: Ragnarok Chapter 15 Complete Production Master.
Strictly Calibrated for 4.5 to 5 Minutes Runtime (240s–300s).
Features:
- 5 Distinct Humanoid AI Voices (Narrator, Suho, Beru, Lee Minsung, Sung Jinwoo, System)
- Studio Warmth DSP Equalizer
- Procedural Dark Drone, Epic Orchestral Synth, and Cinematic SFX (Braam, Blade Slash, Whoosh)
- 1080p Ken Burns Motion & Blur Backdrop Compositing
- Styled Dual-Color ASS Subtitles
- High-CTR YouTube Thumbnail
- Database Registration in AUTOPILOT Vault
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.ffmpeg import ffmpeg_bin, probe

OUT_DIR = ROOT / "output" / "solo_leveling_ragnarok_ch15"
PANELS_DIR = OUT_DIR / "panels"
CP_DIR = OUT_DIR / "checkpoints"
FINAL_DIR = OUT_DIR / "checkpoints_final"

SCENES = [
    {
        "panel": 1, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Solo Leveling: Ragnarok Chapter 15! Lee Minsung ka khaufnaak Stardust shadyantra samne aa chuka hai!",
        "text_speak": "सोलो लेवलिंग रैनारॉक चैप्टर पंद्रह! ली मिनसुंग का खौफनाक स्टारडस्ट षड्यंत्र सामने आ चुका है, और आज शैडो मोनार्क की ताकत का पहला जलवा दुनिया देखेगी!"
    },
    {
        "panel": 2, "speaker": "suho", "emotion": "serious", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Seoul ke secret underground base ke bahar Suho ne kadam roke: 'Beru, kya tujhe bhi zehreeli mana mehsoos ho rahi hai?'",
        "text_speak": "सियोल के एक गुप्त अंडरग्राउंड बेस के बाहर सू-हो ने अपने कदम रोके: 'बेरू, क्या तुझे भी अंदर से वो अजीब, जहरीली माना महसूस हो रही है?'"
    },
    {
        "panel": 3, "speaker": "beru", "emotion": "epic", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Beru cheekha: 'Haan Young Monarch! Ye koi mamooli jadoo nahi... ye Itarim ke Outer Gods ki gandi urja hai!'",
        "text_speak": "बेरू के पंखों में सिहरन दौड़ गई: 'हाँ यंग मोनार्क! ये कोई मामूली जादू नहीं है... ये इटारिम के भ्रष्ट आउटर गॉड्स की गंदी ऊर्जा है!'"
    },
    {
        "panel": 4, "speaker": "suho", "emotion": "gentle", "camera": "slow_push", "music": "ambient_soft", "sfx": "heartbeat_low",
        "text_sub": "Suho ne Gray ki peeth thapthapayi: 'Gray, kya tum raasta soongh sakte ho?' Gray ne andheri surang ki taraf ishara kiya: 'RUFF!'",
        "text_speak": "सू-हो ने अपने वफादार भेड़िये ग्रे की पीठ थपथपाई: 'ग्रे, क्या तुम रास्ता सूंघ सकते हो?' ग्रे ने अपनी नाक हवा में उठाई और एक अंधेरी सुरंग की तरफ इशारा किया: 'रफ्फ!'"
    },
    {
        "panel": 5, "speaker": "narrator", "emotion": "tense", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Jaise hi Suho ne basement ka steel darwaza toda, samne ek aweedh mutation lab dikhayi di!",
        "text_speak": "जैसे ही सू-हो ने बेसमेंट का भारी स्टील दरवाज़ा तोड़ा, सामने का मंज़र देखकर उसके रोंगटे खड़े हो गए! ये कोई आम गिल्ड ऑफिस नहीं, बल्कि एक अवैध म्यूटेशन लैब थी!"
    },
    {
        "panel": 6, "speaker": "suho", "emotion": "shocked", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Glass cylinders mein darjano hunters kaid the, aur unki nason mein baingani taral Stardust crystal pump ho raha tha!",
        "text_speak": "शीशे के बड़े सिलेंडरों में दर्जनों हंटर्स बंद थे, और उनकी नसों में बैंगनी रंग का तरल पदार्थ पंप किया जा रहा था — वही स्टारडस्ट क्रिस्टल!"
    },
    {
        "panel": 7, "speaker": "minsung", "emotion": "arrogant", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Andhere se taliyon ki goonj aayi! Lee Minsung muskuraaya: 'Toh nakabposh chooha khud mere jaal mein aa hi gaya!'",
        "text_speak": "अचानक अंधेरे से एक तालियों की गूंज सुनाई दी! ग्रिम रीपर गिल्ड का वाइस-सीईओ ली मिनसुंग सामने आया: 'वाह! तो वो नकाबपोश चूहा आखिरकार मेरे जाल में खुद चलकर आ ही गया!'"
    },
    {
        "panel": 8, "speaker": "suho", "emotion": "serious", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Suho ki aankhein aag ki tarah chamki: 'Lee Minsung... begunah hunters ke saath khilwad karke tu kya sabit karna chahta hai?'",
        "text_speak": "सू-हो की आंखें अंगारे जैसी धधक उठीं: 'ली मिनसुंग... बेकसूर हंटर्स की ज़िंदगी के साथ खिलवाड़ करके तू आखिर क्या साबित करना चाहता है?'"
    },
    {
        "panel": 9, "speaker": "minsung", "emotion": "evil", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Lee Minsung ghamand se bola: 'Duniya sirf taqat ki bhasha samajhti hai! Stardust se E-Rank hunter bhi S-Rank ban sakta hai!'",
        "text_speak": "ली मिनसुंग घमंड से हंसा: 'साबित? अरे बेवकूफ, दुनिया सिर्फ ताकत की भाषा समझती है! इस स्टारडस्ट से एक ई-रैंक हंटर भी पलक झपकते ही एस-रैंक जैसी ताकत पा सकता है!'"
    },
    {
        "panel": 10, "speaker": "beru", "emotion": "angry", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Beru gusse mein dahada: 'Keede jaisi aukaat wale insaan! Tu us zeher ko taqat kehta hai jo aatma ko rakshas bana de?!'",
        "text_speak": "बेरू गुस्से से आगबबूला होकर चिल्लाया: 'कीड़े जैसी औकात वाले इंसान! तू उस ज़हर को ताकत कह रहा है जो इंसानी आत्मा को निचोड़कर राक्षस बना देता है?!'"
    },
    {
        "panel": 11, "speaker": "minsung", "emotion": "arrogant", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Lee Minsung ne chutki bajayi: 'Guards! Is ladke ki khaal udhed kar ise agle experiment ka hissa bana do!'",
        "text_speak": "ली मिनसुंग ने चुटकी बजाई: 'बातें बहुत हो गईं! गार्ड्स, इस लड़के की खाल उधेड़कर इसे भी हमारे अगले एक्सपेरिमेंट का हिस्सा बना दो!'"
    },
    {
        "panel": 12, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Darjano mutated hunters laal aankhon aur lohe jaisi takat ke saath Suho par toot pade!",
        "text_speak": "दर्जनों म्यूटेटेड हंटर्स अपनी लाल आंखों और लोहे जैसी मांसपेशियों के साथ सू-हो पर झपटे! हवा में खून की प्यास तैरने लगी!"
    },
    {
        "panel": 13, "speaker": "system", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "System Alert: Emergency Quest! Annihilate Corrupted Mutants! All physical stats boosted by 40%!",
        "text_speak": "Emergency Quest: Annihilate the Corrupted Mutants! All physical stats boosted by forty percent!"
    },
    {
        "panel": 14, "speaker": "suho", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho ne dono khanjaron ko thaama: 'Gray, baayi taraf sambhalo! Beru, kisi ko bhagne mat dena!'",
        "text_speak": "सू-हो ने फुर्ती से अपने दोनों खंजर निकाले: 'ग्रे, बाईं तरफ संभालो! बेरू, किसी को भागने मत देना!'"
    },
    {
        "panel": 15, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "dark_intense", "sfx": "c_rank_blade_slash",
        "text_sub": "Gray ne dahadte hue chhalang lagayi aur pehle mutant ki gardan jabdo mein jakad li! Deewaron par khoon ke chheente gire!",
        "text_speak": "ग्रे ने गगनभेदी दहाड़ लगाई और आगे बढ़कर पहले म्यूटेंट की गर्दन अपने जबड़ों में जकड़ ली! खून के छींटे दीवार पर जा गिरे!"
    },
    {
        "panel": 16, "speaker": "suho", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "c_rank_blade_slash",
        "text_sub": "Suho bijli ki raftaar se dauda! Uske daggers ne hawa ko cheerte hue teen mutators ke seene cheer diye!",
        "text_speak": "सू-हो बिजली की रफ्तार से दुश्मनों के बीच से गुजरा! उसके खंजर ने हवा को चीरते हुए तीन म्यूटेंट्स के सीने को एक झटके में काट दिया!"
    },
    {
        "panel": 17, "speaker": "minsung", "emotion": "shocked", "camera": "sudden_zoom", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Lee Minsung ke paseene chhoote: 'Ye kaun hai? B-Rank mutators ko gajar-mooli ki tarah kaat raha hai?!'",
        "text_speak": "ली मिनसुंग के पसीने छूट गए: 'ये... ये कौन है? बी-रैंक के म्यूटेंट्स को गाजर-मूली की तरह काट रहा है?!'"
    },
    {
        "panel": 18, "speaker": "beru", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Beru ne taaliyaan bajayi: 'Adbhut Young Monarch! Aapka har vaar Shadow Monarch ki yaad dilata hai!'",
        "text_speak": "बेरू हवा में नाचते हुए तालियां पीटने लगा: 'अद्भुत यंग मोनार्क! आपका हर वार शैडो मोनार्क की महान विरासत की याद दिलाता है!'"
    },
    {
        "panel": 19, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Chand lamho mein poori lab laashon ke dher mein badal gayi! Ab bacha tha sirf Lee Minsung!",
        "text_speak": "चंद मिनटों के अंदर पूरी लैब लाशों के ढेर में बदल गई! अब सामने सिर्फ एक शख्स बचा था — ग्रिम रीपर का वाइस-सीईओ ली मिनसुंग!"
    },
    {
        "panel": 20, "speaker": "suho", "emotion": "serious", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Suho aage badha: 'Khel khatam, Lee Minsung! Bata, Itarim ke Apostles kahan chhipe hain?!'",
        "text_speak": "सू-हो अपने खंजर से खून पोंछते हुए आगे बढ़ा: 'तेरा खेल खत्म, ली मिनसुंग! सच बता, इटारिम के वो दूत कहाँ छिपे हैं?!'"
    },
    {
        "panel": 21, "speaker": "minsung", "emotion": "evil", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Lee Minsung pagal ki tarah hasa: 'Hahaha! Tu jeeta nahi hai! Abhi tune asli bhagwan ki taqat kahan dekhi hai!'",
        "text_speak": "ली मिनसुंग पागल की तरह हंसने लगा: 'हाहाहा! तुझे लगता है तूने मुझे हरा दिया? अभी तूने असली भगवान की ताकत देखी ही कहाँ है!'"
    },
    {
        "panel": 22, "speaker": "narrator", "emotion": "tense", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Usne apni jeb se wo chamakta Stardust crystal nikala aur ek hi saans mein poora nigal liya!",
        "text_speak": "उसने अपनी जेब से वो बैंगनी चमकता स्टारडस्ट क्रिस्टल निकाला और एक ही सांस में पूरा निगल लिया!"
    },
    {
        "panel": 23, "speaker": "narrator", "emotion": "fearful", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Agle hi pal ek bhayanak cheekh ke saath Lee Minsung ka shareer fatne laga aur uski peeth se kaale pankh nikal aaye!",
        "text_speak": "अगले ही पल एक भयानक चीख के साथ ली मिनसुंग का शरीर फटने लगा! उसकी हड्डियां मुड़ गईं, और उसकी पीठ से चार जहरीले काले पंख निकल आए!"
    },
    {
        "panel": 24, "speaker": "minsung", "emotion": "evil", "camera": "handheld_shake", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Uski aawaz patal se aati gurrahat jaisi thi: 'Main hoon Itarim ka doot! Tumhari rooh meri khuraak banegi!'",
        "text_speak": "उसकी आवाज़ अब इंसानी नहीं रही, बल्कि पाताल से आती गुर्राहट जैसी थी: 'मैं हूँ इटारिम का सच्चा दूत! अब तुम्हारी रूह मेरी खुराक बनेगी!'"
    },
    {
        "panel": 25, "speaker": "suho", "emotion": "serious", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Suho ne dabav mehsoos kiya: 'Yeh mana... kisi S-Rank monster se bhi kahin zyada bhayanak hai!'",
        "text_speak": "सू-हो ने दबाव महसूस किया: 'ये माना... ये तो किसी एस-रैंक मॉन्स्टर से भी कहीं ज्यादा भयानक है!' जमीन कांपने लगी थी!"
    },
    {
        "panel": 26, "speaker": "minsung", "emotion": "evil", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Danav bane Minsung ne parchaayi se khooni bhala nikala aur seedhe Suho ki taraf phenk diya!",
        "text_speak": "दानव बने ली मिनसुंग ने अपनी परछाईं से एक विशाल खूनी भाला निकाला और सीधे सू-हो के दिल की तरफ फेंक दिया!"
    },
    {
        "panel": 27, "speaker": "beru", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Beru bijli ki gati se beech mein aaya aur dhaal se bhale ko tod diya: 'Young Monarch ko chhoone ki teri himmat kaise hui?!'",
        "text_speak": "बेरू बिजली की गति से बीच में आया और अपनी ढाल से उस भाले को चूर-चूर कर दिया: 'यंग मोनार्क को छूने की तेरी जुर्रत कैसे हुई, नीच कीड़े?!'"
    },
    {
        "panel": 28, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Lekin bhale ke zehreelay asar se Beru ladkhada gaya! Uski mana abhi poori wapas nahi aayi thi!",
        "text_speak": "लेकिन उस भाले के जहरीले असर से बेरू भी लड़खड़ा गया! उसकी माना अभी पूरी तरह वापस नहीं आई थी!"
    },
    {
        "panel": 29, "speaker": "suho", "emotion": "angry", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Beru ko ghayal dekh Suho ka lahu khaul utha! Uski aankhon mein neeli divya roshni chamki!",
        "text_speak": "बेरू को घायल देख सू-हो के अंदर का लहू खौल उठा! उसकी आंखों में नीली दिव्य रोशनी चमकने लगी!"
    },
    {
        "panel": 30, "speaker": "system", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "System Alert: High dimensional resonance! Lineage Authority: Son of the Shadow Monarch active!",
        "text_speak": "Warning: High dimensional resonance detected! Lineage Authority: Son of the Shadow Monarch active!"
    },
    {
        "panel": 31, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Achanak poori lab mein waqt thham gaya, aur Suho ke peeche ek anant bramhandiya saya ubharne laga!",
        "text_speak": "अचानक पूरी लैब का वातावरण शून्य हो गया! वक्त जैसे थम गया हो, और सू-हो के पीछे एक अनंत, ब्रह्मांडीय साया उभरने लगा!"
    },
    {
        "panel": 32, "speaker": "jinwoo", "emotion": "epic", "camera": "slow_push", "music": "dark_drone", "sfx": "braam_impact",
        "text_sub": "Sung Jinwoo ki gaganbhedi aawaz goonji: 'Who gave you permission to touch my son? Kneel before the Shadow Monarch!'",
        "text_speak": "Who gave you permission to touch my son? Kneel before the Monarch of Shadows!"
    },
    {
        "panel": 33, "speaker": "minsung", "emotion": "fearful", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Minsung kanpne laga: 'Sung Jinwoo?! Nahi... ye namumkin hai! Wo toh outer dimension mein phasa hai!'",
        "text_speak": "ली मिनसुंग का दैत्य रूप उस साये को देखते ही थर-थर कांपने लगा: 'सुंग... सुंग जिन-वू?! नहीं... ये नामुमकिन है! वो तो आउटर डायमेंशन में फंसा हुआ है!'"
    },
    {
        "panel": 34, "speaker": "suho", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho ne dono khanjaro mein shadow energy bhari aur chhalang lagayi: 'Ab tera khel khatam, Lee Minsung!'",
        "text_speak": "सू-हो ने अपने दोनों खंजरों में शैडो एनर्जी भरते हुए आखिरी छलांग लगाई: 'अब तुम्हारा खेल सच में खत्म, ली मिनसुंग!'"
    },
    {
        "panel": 35, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "dark_intense", "sfx": "c_rank_blade_slash",
        "text_sub": "Neeli aur kaali roshni ka dhamaka hua! Suho ke khanjar ne Stardust core ko chaknachoor kar diya!",
        "text_speak": "एक नीली और काली रोशनी का ज़ोरदार विस्फोट हुआ! सू-हो के खंजर ने दानव के सीने में बसे उस स्टारडस्ट कोर को चकनाचूर कर दिया!"
    },
    {
        "panel": 36, "speaker": "minsung", "emotion": "shocked", "camera": "sudden_zoom", "music": "dark_drone", "sfx": "braam_impact",
        "text_sub": "Dardnaak cheekh ke saath Lee Minsung ka shareer rakh mein badla aur wo behosh hokar gir pada!",
        "text_speak": "एक दर्दनाक चीख के साथ ली मिनसुंग का दानवी शरीर राख में तब्दील हो गया, और वो बेहोश होकर जमीन पर गिर पड़ा!"
    },
    {
        "panel": 37, "speaker": "system", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Quest Completed! Gained Level 18! Grand Quest: Monarch's Heirs upgraded to (2/8)!",
        "text_speak": "Quest Completed! Gained Level Eighteen! Grand Quest: Monarch's Heirs upgraded to two of eight!"
    },
    {
        "panel": 38, "speaker": "beru", "emotion": "epic", "camera": "slow_push", "music": "ambient_soft", "sfx": "heartbeat_low",
        "text_sub": "Beru ne jhuk kar pranam kiya: 'Young Monarch! Aaj aapne sabit kiya ki Shadow Monarch ka khoon aapme dhadakta hai!'",
        "text_speak": "बेरू ने सिर झुकाकर सम्मान किया: 'यंग मोनार्क! आज आपने साबित कर दिया कि शैडो मोनार्क का खून आपकी रगों में धड़कता है!'"
    },
    {
        "panel": 39, "speaker": "suho", "emotion": "serious", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Suho ne Stardust ki rakh dekhi: 'Yeh toh shuruaat hai Beru... Itarim ke aakaon ko dhoondh kar hume dharti ko bachana hoga!'",
        "text_speak": "सू-हो ने हाथ में बची हुई स्टारडस्ट की राख को देखा: 'ये तो सिर्फ शुरुआत है, बेरू... इटारिम के असली आकाओं को ढूंढकर हमें धरती को बचाना ही होगा!'"
    },
    {
        "panel": 40, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Solo Leveling: Ragnarok Chapter 15 Master! Like, Comment aur Subscribe zaroor karein agle episode ke liye!",
        "text_speak": "और इस तरह चैप्टर पंद्रह का रोमांचक अंत हुआ! क्या सू-हो अपने पिता सुंग जिन-वू से मिल पाएगा? कमेंट्स में अपनी राय ज़रूर बताएं और चैनल को सब्सक्राइब करें!"
    }
]

# ─────────────────────────────────────────────────────────────────────────────
# VOICEOVER GENERATOR (MULTI-SPEAKER HUMANOID NEURAL SYNTHESIS)
# ─────────────────────────────────────────────────────────────────────────────
async def generate_voice(text_speak: str, speaker: str, emotion: str, out_wav: Path):
    import edge_tts

    voice = "hi-IN-MadhurNeural"
    rate_str = "+16%"
    pitch_str = "-2Hz"

    if speaker == "suho":
        voice = "hi-IN-MadhurNeural"
        rate_str = "+18%"
        pitch_str = "+2Hz"
    elif speaker == "beru":
        voice = "hi-IN-SwaraNeural"
        rate_str = "+22%"
        pitch_str = "+6Hz"
    elif speaker == "minsung":
        voice = "hi-IN-MadhurNeural"
        rate_str = "+14%"
        pitch_str = "-4Hz"
    elif speaker == "jinwoo":
        voice = "en-US-ChristopherNeural"
        rate_str = "-2%"
        pitch_str = "-3Hz"
    elif speaker == "system":
        voice = "en-US-JennyNeural"
        rate_str = "+10%"
        pitch_str = "+0Hz"

    raw_mp3 = out_wav.with_suffix(".mp3")
    for attempt in range(1, 6):
        try:
            communicator = edge_tts.Communicate(text_speak, voice, rate=rate_str, pitch=pitch_str)
            await communicator.save(str(raw_mp3))
            if raw_mp3.exists() and raw_mp3.stat().st_size > 500:
                break
        except Exception as e:
            if attempt == 5:
                raise
            print(f"    ⚠️ Edge-TTS attempt {attempt}/5 failed ({e}), retrying in {attempt * 2}s...")
            await asyncio.sleep(attempt * 2)

    # 6-Stage Studio Warmth DSP Equalizer
    ff = ffmpeg_bin()
    dsp_chain = (
        "highpass=f=75,"
        "equalizer=f=125:t=q:w=1.5:g=3.2,"
        "equalizer=f=420:t=q:w=2.0:g=-1.8,"
        "equalizer=f=2800:t=q:w=1.8:g=2.6,"
        "equalizer=f=8000:t=q:w=2.0:g=1.5,"
        "acompressor=threshold=-15dB:ratio=3.5:attack=15:release=120:makeup=2.2dB"
    )

    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(raw_mp3),
        "-af", dsp_chain,
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(out_wav)
    ], check=True)

    if raw_mp3.exists():
        raw_mp3.unlink()

# ─────────────────────────────────────────────────────────────────────────────
# PROCEDURAL SCORE & SFX
# ─────────────────────────────────────────────────────────────────────────────
def generate_music(music_type: str, duration: float, out_wav: Path):
    ff = ffmpeg_bin()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    d = round(duration, 3)

    filters = {
        "dark_drone":     f"aevalsrc='0.22*sin(2*PI*55*t)+0.16*sin(2*PI*82.4*t)+0.10*sin(2*PI*110*t)':d={d}:s=44100,volume=0.26",
        "dark_intense":   f"aevalsrc='0.28*sin(2*PI*45*t)+0.20*sin(2*PI*65*t)+0.12*sin(2*PI*130*t)+0.07*(random(0)-0.5)':d={d}:s=44100,volume=0.32",
        "epic_adventure": f"aevalsrc='0.20*sin(2*PI*130.8*t)+0.16*sin(2*PI*164.8*t)+0.14*sin(2*PI*196*t)+0.12*sin(2*PI*261.6*t)':d={d}:s=44100,volume=0.30",
        "ambient_soft":   f"aevalsrc='0.16*sin(2*PI*174.6*t)+0.14*sin(2*PI*220*t)+0.10*sin(2*PI*261.6*t)':d={d}:s=44100,volume=0.24",
    }
    flt = filters.get(music_type, filters["dark_drone"])
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", flt,
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(out_wav)
    ], check=True)

def generate_sfx(sfx_type: str, duration: float, out_wav: Path):
    ff = ffmpeg_bin()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    d = round(duration, 3)

    filters = {
        "c_rank_blade_slash": f"aevalsrc='0.45*exp(-6*t)*sin(2*PI*(800-450*t)*t)+0.25*exp(-8*t)*(random(0)-0.5)':d={d}:s=44100",
        "braam_impact":       f"aevalsrc='0.42*exp(-1.5*t)*sin(2*PI*40*t)+0.26*exp(-2*t)*sin(2*PI*80*t)':d={d}:s=44100",
        "whoosh_energy":      f"aevalsrc='0.32*exp(-4*t)*sin(2*PI*(320-200*t)*t)':d={d}:s=44100",
        "heartbeat_low":      f"aevalsrc='0.35*sin(2*PI*45*t)*pow(max(0,sin(2*PI*1.3*t)),10)':d={d}:s=44100",
        "ambient_soft":       f"aevalsrc='0.08*sin(2*PI*120*t)':d={d}:s=44100",
    }
    flt = filters.get(sfx_type, filters["ambient_soft"])
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", flt,
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(out_wav)
    ], check=True)

def mix_audio(voice_wav: Path, music_wav: Path, sfx_wav: Path, duration: float, out_aac: Path):
    ff = ffmpeg_bin()
    out_aac.parent.mkdir(parents=True, exist_ok=True)
    d = round(duration, 3)

    filter_complex = (
        "[0:a]volume=1.40,apad[v];"
        "[1:a]volume=0.18[m];"
        "[2:a]volume=0.25[s];"
        "[v][m][s]amix=inputs=3:duration=longest:dropout_transition=2,"
        f"atrim=end={d:.3f},aresample=44100"
    )
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(voice_wav),
        "-i", str(music_wav),
        "-i", str(sfx_wav),
        "-filter_complex", filter_complex,
        "-c:a", "aac", "-b:a", "192k",
        str(out_aac)
    ], check=True)

# ─────────────────────────────────────────────────────────────────────────────
# SINGLE-PASS COMPOSITOR (1080p KEN BURNS & PANEL BORDER)
# ─────────────────────────────────────────────────────────────────────────────
def render_scene_direct(img_path: Path, audio_aac: Path, duration: float, camera: str, out_mp4: Path):
    ff = ffmpeg_bin()
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    dur = max(2.5, round(duration, 3))
    w, h = 1920, 1080

    with Image.open(str(img_path)) as im:
        iw, ih = im.size
    aspect = iw / max(1, ih)

    bg_flt = f"[0:v]scale=320:180:force_original_aspect_ratio=increase,crop=320:180,boxblur=6:2,scale={w}:{h}:flags=bicubic,eq=brightness=-0.22:contrast=0.95[bg]"

    if aspect >= 1.2 or aspect >= 0.7:
        fg_flt = f"[0:v]scale=-2:1040[fg_scaled];[fg_scaled]pad=w=iw+10:h=ih+10:x=5:y=5:color=0x151520@0.8[fg]"
    else:
        fg_w = 1250
        fg_flt = (
            f"[0:v]scale={fg_w}:-2[fg_scaled];"
            f"[fg_scaled]crop=w={fg_w}:h=min(in_h\\,1040):x=0:y='if(gt(in_h\\,1040)\\,(in_h-1040)*t/{dur:.2f}\\,0)'[fg_pan];"
            f"[fg_pan]pad=w={fg_w}+10:h=1050:x=5:y=5:color=0x151520@0.8[fg]"
        )

    comp_flt = f"[bg][fg]overlay=(W-w)/2:(H-h)/2[comp]"

    if camera == "sudden_zoom":
        motion_flt = (
            f"[comp]scale=w='2*floor({w}*(1.01+0.04*pow(t/{dur:.2f},1.5))/2)':h='2*floor({h}*(1.01+0.04*pow(t/{dur:.2f},1.5))/2)':eval=frame,"
            f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2,format=yuv420p[v]"
        )
    elif camera == "handheld_shake":
        motion_flt = (
            f"[comp]scale=w='2*floor({w}*1.03/2)':h='2*floor({h}*1.03/2)',"
            f"crop={w}:{h}:'(in_w-{w})/2+4*sin(12*t)':'(in_h-{h})/2+4*cos(9*t)',format=yuv420p[v]"
        )
    else:
        motion_flt = (
            f"[comp]scale=w='2*floor({w}*(1.01+0.02*t/{dur:.2f})/2)':h='2*floor({h}*(1.01+0.02*t/{dur:.2f})/2)':eval=frame,"
            f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2,format=yuv420p[v]"
        )

    filter_complex = f"{bg_flt};{fg_flt};{comp_flt};{motion_flt}"

    cmd = [
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-t", str(dur), "-i", str(img_path),
        "-i", str(audio_aac),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(out_mp4)
    ]
    subprocess.run(cmd, check=True)

# ─────────────────────────────────────────────────────────────────────────────
# SUBTITLES & THUMBNAIL
# ─────────────────────────────────────────────────────────────────────────────
def generate_ass_subtitles(scenes: list[dict], scene_durs: list[float], out_ass: Path):
    header = """[Script Info]
Title: Solo Leveling Ragnarok Chapter 15 Subtitles
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: RagnarokCyan,Segoe UI,40,&H00F0FF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0.5,0,1,3.5,2.5,2,50,50,55,1
Style: RagnarokGold,Segoe UI,40,&H00D7FF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0.5,0,1,3.5,2.5,2,50,50,55,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def fmt_time(t: float) -> str:
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        cs = int(round((t - int(t)) * 100))
        if cs >= 100:
            cs = 99
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    events = []
    curr = 0.0
    for sc, dur in zip(scenes, scene_durs):
        start_s = curr
        end_s = curr + dur
        style = "RagnarokGold" if sc["speaker"] in ["minsung", "beru", "system", "jinwoo"] else "RagnarokCyan"
        text = sc["text_sub"].replace("\n", "\\N")
        events.append(f"Dialogue: 0,{fmt_time(start_s)},{fmt_time(end_s)},{style},,0,0,0,,{text}")
        curr = end_s

    out_ass.parent.mkdir(parents=True, exist_ok=True)
    with open(out_ass, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + "\n")
    print(f"  ✓ Dual-Color Subtitles generated: {out_ass.name}")

def create_thumbnail(out_thumb: Path):
    out_thumb.parent.mkdir(parents=True, exist_ok=True)
    p = PANELS_DIR / "panel_032.jpg"
    if not p.exists():
        p = PANELS_DIR / "panel_001.jpg"

    with Image.open(str(p)) as im:
        thumb = im.convert("RGB").resize((1280, 720), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(thumb)
    try:
        font_big = ImageFont.truetype("arialbd.ttf", 62)
        font_sub = ImageFont.truetype("arialbd.ttf", 40)
    except Exception:
        font_big = ImageFont.load_default()
        font_sub = font_big

    draw.rectangle([(20, 20), (1260, 160)], fill=(10, 12, 24, 220))
    draw.text((40, 30), "SHADOW MONARCH AWAKENS! ⚔️🔥", fill=(0, 240, 255), font=font_big)
    draw.text((40, 100), "SOLO LEVELING RAGNAROK CH 15 (HINDI)", fill=(255, 215, 0), font=font_sub)

    thumb.save(str(out_thumb), quality=95)
    print(f"  ✓ High-CTR Thumbnail created: {out_thumb.name}")

# ─────────────────────────────────────────────────────────────────────────────
# MASTER GENERATOR PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
async def run_pipeline():
    ff = ffmpeg_bin()
    CP_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 75)
    print("  ⚔️ SOLO LEVELING: RAGNAROK CHAPTER 15 — MASTER 5-MINUTE PRODUCTION")
    print("  Target: Strictly 4.5 to 5.0 Minutes (240s–300s) · 5 Multi-Voice Humanoid AI")
    print("=" * 75)

    scene_durs = []
    scene_clips = []

    for i, sc in enumerate(SCENES, start=1):
        p_num = sc["panel"]
        img_path = PANELS_DIR / f"panel_{p_num:03d}.jpg"
        if not img_path.exists():
            img_path = PANELS_DIR / "panel_001.jpg"

        print(f"🎬 Scene {i:02d}/{len(SCENES)} (Panel {p_num:03d}): {sc['speaker'].upper()}")

        # 1. Voiceover
        v_wav = CP_DIR / f"sc_{i:02d}_v.wav"
        if not v_wav.exists() or v_wav.stat().st_size < 1000:
            await generate_voice(sc["text_speak"], sc["speaker"], sc["emotion"], v_wav)

        info = probe(v_wav)
        v_dur = float(info["format"]["duration"])
        dur = max(3.5, v_dur + 0.30)
        scene_durs.append(dur)

        sc_mp4 = FINAL_DIR / f"sc_{i:02d}_final.mp4"
        if sc_mp4.exists() and sc_mp4.stat().st_size > 50000:
            scene_clips.append(sc_mp4)
            continue

        # 2. Score & SFX
        m_wav = FINAL_DIR / f"sc_{i:02d}_m.wav"
        generate_music(sc["music"], dur, m_wav)

        s_wav = FINAL_DIR / f"sc_{i:02d}_s.wav"
        generate_sfx(sc["sfx"], dur, s_wav)

        # 3. Audio Mix
        mix_aac = FINAL_DIR / f"sc_{i:02d}_mix.aac"
        mix_audio(v_wav, m_wav, s_wav, dur, mix_aac)

        # 4. Direct Single-Pass Video + Audio Render
        render_scene_direct(img_path, mix_aac, dur, sc["camera"], sc_mp4)
        scene_clips.append(sc_mp4)

        # Clean up temporary scene audio
        for tmp_f in [m_wav, s_wav, mix_aac]:
            if tmp_f.exists():
                try:
                    tmp_f.unlink()
                except Exception:
                    pass

    total_dur = sum(scene_durs)
    print("\n" + "=" * 75)
    print(f"  ⏱️ EXACT SCENE DURATION SUM: {total_dur:.1f}s ({total_dur/60:.2f} minutes)")
    print("=" * 75)

    # Concatenate
    concat_list = OUT_DIR / "concat_list_final.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for clip in scene_clips:
            clean_path = str(clip.resolve()).replace("\\", "/")
            f.write(f"file '{clean_path}'\n")

    unsubbed_mp4 = OUT_DIR / "solo_leveling_ragnarok_ch15_unsubbed.mp4"
    print(f"\n📦 Concatenating all {len(scene_clips)} scenes into {unsubbed_mp4.name}...")
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(unsubbed_mp4)
    ], check=True)

    # Calibrate to 275s if outside 240s–300s window
    final_mp4 = OUT_DIR / "solo_leveling_ragnarok_ch15_final.mp4"
    if not (240.0 <= total_dur <= 300.0):
        target_total = 275.0
        factor = total_dur / target_total
        print(f"  ⚠️ Recalibrating duration from {total_dur:.1f}s to {target_total:.1f}s (factor: {factor:.4f}x)...")
        scene_durs = [round(d / factor, 3) for d in scene_durs]
        total_dur = sum(scene_durs)

        ass_path = OUT_DIR / "solo_leveling_ragnarok_ch15.ass"
        generate_ass_subtitles(SCENES, scene_durs, ass_path)

        ass_escaped = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
        v_flt = f"setpts=PTS/{factor:.4f},ass='{ass_escaped}'"
        a_flt = f"atempo={factor:.4f}"

        print(f"🔥 Burning styled subtitles and applying tempo factor {factor:.4f}x into: {final_mp4.name}...")
        subprocess.run([
            ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-i", str(unsubbed_mp4),
            "-vf", v_flt,
            "-af", a_flt,
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            str(final_mp4)
        ], check=True)
    else:
        ass_path = OUT_DIR / "solo_leveling_ragnarok_ch15.ass"
        generate_ass_subtitles(SCENES, scene_durs, ass_path)

        ass_escaped = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
        sub_filter = f"ass='{ass_escaped}'"

        print(f"🔥 Burning styled subtitles into final broadcast master: {final_mp4.name}...")
        subprocess.run([
            ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-i", str(unsubbed_mp4),
            "-vf", sub_filter,
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "copy",
            str(final_mp4)
        ], check=True)

    if unsubbed_mp4.exists():
        try:
            unsubbed_mp4.unlink()
        except Exception:
            pass

    # Thumbnail
    thumb_path = OUT_DIR / "thumbnail.jpg"
    create_thumbnail(thumb_path)

    final_info = probe(final_mp4)
    final_sec = float(final_info.get("format", {}).get("duration", total_dur))
    final_size_mb = final_mp4.stat().st_size / (1024 * 1024)

    # Register in database for AUTOPILOT platform UI & API
    try:
        from core.db import DB
        db = DB()
        now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        db.conn.execute("""
            INSERT OR REPLACE INTO videos (
                id, topic, title, caption, hashtags, status,
                length_sec, video_path, cover_path, user_id, workspace_id, created_ts, updated_ts
            ) VALUES (
                1000085,
                'Solo Leveling: Ragnarok Chapter 15 — Stardust Secret & Shadow Monarch Awakening',
                'Solo Leveling: Ragnarok Chapter 15 (Hindi) | Stardust Ka Khaufnaak Raaz Aur Shadow Monarch Ka Aavahan!',
                'Solo Leveling: Ragnarok Chapter 15 Full Breakdown in Hindi! Suho vs Grim Reaper Guild and Lee Minsung mutant battle with Sung Jinwoo shadow awakening.',
                '["SoloLeveling", "SoloLevelingRagnarok", "SungJinwoo", "AnimeHindi", "ManhwaHindi"]',
                'rendered',
                ?,
                ?,
                ?,
                'admin_abhay',
                'ws_admin_abhay',
                ?,
                ?
            )
        """, (final_sec, str(final_mp4), str(thumb_path), now_ts, now_ts))
        db.conn.commit()
        print("  ✓ Video successfully registered in AUTOPILOT Master Database (ID #1000085)")
    except Exception as e:
        print(f"  ⚠️ DB registration notice: {e}")

    print("\n" + "🎉" * 38)
    print("  ✅ SOLO LEVELING: RAGNAROK CHAPTER 15 FINAL MASTER IS READY!")
    print(f"  📁 Output: {final_mp4}")
    print(f"  ⏱️ Final Duration: {final_sec:.1f}s ({final_sec/60:.2f} minutes)")
    print(f"  💾 File Size: {final_size_mb:.2f} MB")
    print("🎉" * 38 + "\n")

    return final_mp4

def main():
    asyncio.run(run_pipeline())

if __name__ == "__main__":
    main()
