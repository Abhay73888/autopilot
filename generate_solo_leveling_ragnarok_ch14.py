"""
generate_solo_leveling_ragnarok_ch14.py — Solo Leveling: Ragnarok Chapter 14 Complete Production Master.
Strictly Calibrated for 4 to 5 Minutes Runtime (240s–300s).
Single-pass lightweight FFmpeg rendering with studio warmth DSP humanoid voiceovers.
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.ffmpeg import ffmpeg_bin, probe

OUT_DIR = ROOT / "output" / "solo_leveling_ragnarok_ch14"
PANELS_DIR = OUT_DIR / "panels"
CP_DIR = OUT_DIR / "checkpoints"
FINAL_DIR = OUT_DIR / "checkpoints_final"

SCENES = [
    {
        "panel": 1, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Solo Leveling: Ragnarok Chapter 14! Brocky ki maut ke baad Fang ke vanshaj ko mila naya ghar aur shuru hua ek khaufnaak shadyantra!",
        "text_speak": "सोलो लेवलिंग रैनारॉक चैप्टर चौदह! ब्रॉकी के अंत के बाद फैंग के वारिस को मिला नया घर, और शुरू हुआ एक खौफनाक षड्यंत्र!"
    },
    {
        "panel": 2, "speaker": "beru", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Beru hawa mein mandrate hue bola: 'Young Monarch! Aapne kamaal kar diya!'",
        "text_speak": "बेरू हवा में मंडराते हुए खुशी से गूंजा: 'यंग मोनार्क! आपने वाकई कमाल कर दिया!'"
    },
    {
        "panel": 3, "speaker": "suho", "emotion": "serious", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Suho ne poocha: 'Beru, tune kaha tha ki Brocky ke andar Itarim ki energy mehsoos hui thi? Jin hunters ne Brocky ki aankh mein stone dala tha, kya wo Itarim ke log the?'",
        "text_speak": "सू-हो ने पूछा: 'बेरू, तूने कहा था कि ब्रॉकी में इटारिम की शक्ति थी? जिन शिकारियों ने ब्रॉकी की आंख में वो पत्थर जड़ा था, क्या वो सीधे इटारिम से थे?'"
    },
    {
        "panel": 4, "speaker": "beru", "emotion": "serious", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Beru ne samjhaya: 'Nahi! Outer Gods khud aage nahi aate, wo Apostles ke zariye sansaar ko tabah karte hain! Iska matlab Itarim ke doot Dharti par maujood hain!'",
        "text_speak": "बेरू ने गंभीर होकर समझाया: 'नहीं! आउटर गॉड्स खुद सामने नहीं आते, वो अपने दूतों के ज़रिए इस दुनिया पर हमला कर रहे हैं! यानी इटारिम के एजेंट्स धरती पर ही मौजूद हैं!'"
    },
    {
        "panel": 5, "speaker": "suho", "emotion": "tense", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Suho pareshan hua: 'Agar humne Itarim ka suraag kho diya, toh aage kaise badhenge?' Tabhi Beru muskura utha!",
        "text_speak": "सू-हो परेशान हुआ: 'अगर हमने इटारिम का सुराग खो दिया, तो आगे कैसे बढ़ेंगे?' तभी बेरू के चेहरे पर चमक आ गई!"
    },
    {
        "panel": 6, "speaker": "beru", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Beru ke sar par bulb jala: 'Main Brocky ki laash ko khaakar uski yaadein nikaal sakta hoon! Isse meri mana bhi recover ho jayegi — ek teer se do shikaar!'",
        "text_speak": "बेरू के सिर पर बल्ब जला: 'अगर मैं ब्रॉकी के शरीर को निगल लूँ, तो उसकी सारी यादें जान सकूँगा! और मेरी माना भी लौट आएगी — एक तीर से दो शिकार!'"
    },
    {
        "panel": 7, "speaker": "suho", "emotion": "gentle", "camera": "slow_push", "music": "ambient_soft", "sfx": "heartbeat_low",
        "text_sub": "Suho Fang ke bhediye ke paas baitha aur narm aawaz mein bola: 'Kya tum hamare saath chalna chahte ho? Mere paas ek aisi jagah hai jahan tum surakshit rahoge.'",
        "text_speak": "सू-हो नन्हे भेड़िये के पास बैठा और प्यार से बोला: 'क्या तुम हमारे साथ चलना चाहते हो? मेरे पास एक ऐसी जगह है जहाँ तुम सुरक्षित रहोगे.'"
    },
    {
        "panel": 8, "speaker": "narrator", "emotion": "emotional", "camera": "slow_push", "music": "ambient_soft", "sfx": "heartbeat_low",
        "text_sub": "Bhediye ne aage badhkar Suho ke chehre ko pyaar se chaat liya! Suho khilkhila kar has pada: 'HAHA!'",
        "text_speak": "भेड़िये ने आगे बढ़कर सू-हो के चेहरे को प्यार से चाट लिया! सू-हो खिलखिलाकर हंस पड़ा: 'हाहा!'"
    },
    {
        "panel": 9, "speaker": "suho", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho ne dimensional dagger ghumakar gate khola: 'Toh theek hai, Beru! Baaki kaam main tum par chhodta hoon!'",
        "text_speak": "सू-हो ने खंजर घुमाकर डायमेंशनल गेट खोला: 'तो ठीक है, बेरू! बाकी काम मैं तुझ पर छोड़ता हूँ!'"
    },
    {
        "panel": 10, "speaker": "beru", "emotion": "emotional", "camera": "slow_push", "music": "ambient_soft", "sfx": "heartbeat_low",
        "text_sub": "Beru ki aankhein aansuon se bhar aayi: 'Young Monarch... aapke shabd mere liye anmol hain...' aur Suho bhediye ke saath Shadow Sanctuary mein dakhil hua!",
        "text_speak": "बेरू की आंखें खुशी से छलक उठीं: 'यंग मोनार्क... आपके शब्द मेरे लिए अनमोल हैं...' और सू-हो भेड़िये को लेकर शैडो सैंक्चुअरी में दाखिल हुआ!"
    },
    {
        "panel": 11, "speaker": "narrator", "emotion": "mysterious", "camera": "slow_push", "music": "ambient_soft", "sfx": "whoosh_energy",
        "text_sub": "Dungeon ke ghane andhere jangal mein pahunchte hi Beru ne poocha: 'Young Monarch, aap ghar jaane ke bajay yahan kyun aaye?'",
        "text_speak": "डंजन के घने अंधेरे जंगल में पहुंचते ही बेरू ने पूछा: 'यंग मोनार्क, आप घर जाने के बजाय सीधे यहाँ क्यों आए?'"
    },
    {
        "panel": 12, "speaker": "suho", "emotion": "serious", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Suho bola: 'Fang ke vanshaj ka koi rakhwala nahi bacha, aur uska sanctuary bhi ujad chuka hai... ye bechara bilkul akela hai.'",
        "text_speak": "सू-हो ने कहा: 'फैंग के वारिस का कोई रखवाला नहीं बचा, और उसका घर भी उजड़ चुका है... ये बेचारा बिल्कुल अकेला है.'"
    },
    {
        "panel": 13, "speaker": "system", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Tabhi System Alert baja: 'Teammate: Fang's Heir chahta hai ki aap use ek naam dein!' Bhediye ne utsaah se bhauka: 'RUFF!'",
        "text_speak": "तभी सिस्टम की घंटी बजी: 'साथी फैंग का वारिस चाहता है कि आप उसे एक नाम दें!' भेड़िये ने खुशी से पूंछ हिलाई: 'रफ्फ!'"
    },
    {
        "panel": 14, "speaker": "suho", "emotion": "funny", "camera": "slow_push", "music": "ambient_soft", "sfx": "whoosh_energy",
        "text_sub": "Suho ne socha: 'Tumhara rang gray hai... isliye tumhara naam hoga GRAY!' Beru paseena chhodte hue socha: 'Bilkul pita Sung Jinwoo jaisa naming sense!'",
        "text_speak": "सू-हो ने झट से कहा: 'तुम्हारा रंग ग्रे है... इसलिए तुम्हारा नाम होगा 'ग्रे'!' बेरू को पसीना आ गया: 'बिल्कुल अपने पिता सुंग जिन-वू जैसा नाम रखने का अंदाज़!'"
    },
    {
        "panel": 15, "speaker": "system", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Suho bola: 'Gray, main is jangal ko Fang ki territory ghoshit karta hoon!' System Alert: 'Shadow Dungeon ka hissa Fang's Territory ban gaya!'",
        "text_speak": "सू-हो ने ऐलान किया: 'ग्रे, आज से ये जंगल तुम्हारा इलाका है!' सिस्टम ने मुहर लगाई: 'शैडो डंजन का ये क्षेत्र फैंग की टेरिटरी बन चुका है!'"
    },
    {
        "panel": 16, "speaker": "suho", "emotion": "curious", "camera": "slow_push", "music": "ambient_soft", "sfx": "heartbeat_low",
        "text_sub": "Suho ne poocha: 'Beru, Gray khayega kya?' Beru bola: 'Kyunki ye Fang ka vanshaj hai, ye jangal ke monsters aur jeevo ko kha sakta hai.'",
        "text_speak": "सू-हो ने पूछा: 'बेरू, ग्रे क्या खाएगा?' बेरू ने बताया: 'क्योंकि ये फैंग के खून से है, ये इस जंगल के शैतानी मॉन्स्टर्स को खा सकता है.'"
    },
    {
        "panel": 17, "speaker": "suho", "emotion": "epic", "camera": "slow_push", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Suho muskuraaya: 'Yeh toh badiya hua! Jangal mein abhi bhi kuch monsters bache hain, Gray unki safai kar dega!'",
        "text_speak": "सू-हो मुस्कुरा उठा: 'ये तो बहुत बढ़िया है! इस जंगल में अभी भी कुछ मॉन्स्टर्स छिपे हैं, ग्रे उनकी सफाई कर देगा!'"
    },
    {
        "panel": 18, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "dark_intense", "sfx": "c_rank_blade_slash",
        "text_sub": "Gray ne dahaadte hue chhalang lagayi aur ek goblin monster par toont pada! Uske nukile daanton ne pal bhar mein shikaar ko dher kar diya!",
        "text_speak": "ग्रे ने भयानक दहाड़ के साथ छलांग लगाई और एक गोब्लिन मॉन्स्टर पर टूट पड़ा! उसके पंजों ने पलक झपकते ही शिकार को ढेर कर दिया!"
    },
    {
        "panel": 19, "speaker": "suho", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho ne tareef ki: 'Shabaash Gray! Tumhari movement kaafi tezz hai!' Ab Suho ne pichli ladayi ke inaamo ko check karna shuru kiya.",
        "text_speak": "सू-हो ने तारीफ की: 'शाबाश ग्रे! तुम्हारी रफ्तार काबिले-तारीफ है!' अब सू-हो ने अपनी पिछली जंग के इनामों को देखना शुरू किया."
    },
    {
        "panel": 20, "speaker": "system", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Quest Rewards: 5 Ability Points aur ek naya khitaab mila — 'TITLE: WOLF SLAUGHTERER'! Beast type monsters ke khilaaf sabhi stats 40% badh jayenge!",
        "text_speak": "क्वेस्ट रिवॉर्ड्स: पांच एबिलिटी पॉइंट्स और एक नया खिताब मिला — 'टाइटिल: वुल्फ स्लॉटरर'! बीस्ट टाइप मॉन्स्टर्स के खिलाफ सारे स्टैट्स चालीस प्रतिशत बढ़ जाएंगे!"
    },
    {
        "panel": 21, "speaker": "suho", "emotion": "curious", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Suho bola: 'Wolf Slaughterer? Par Brocky toh ek hyena tha na?' Par aage badhte hue usne Grand Quest dekha: 'Monarch's Heirs (1/8)'!",
        "text_speak": "सू-हो हंसा: 'वुल्फ स्लॉटरर? पर ब्रॉकी तो हायना था ना?' तभी उसकी नज़र ग्रैंड क्वेस्ट पर पड़ी: 'मोनार्क के वारिस (एक बटे आठ)'!"
    },
    {
        "panel": 22, "speaker": "beru", "emotion": "serious", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Beru ne bataya: 'Sung Jinwoo ke zamane mein Architect ka maqsad unke shareer ko Shadow Monarch ka vessel banakar unki aatma ko mitana tha!'",
        "text_speak": "बेरू ने राज़ खोला: 'सुंग जिन-वू के समय आर्किटेक्ट का इरादा उनके शरीर को शैडो मोनार्क का पुतला बनाकर उनकी आत्मा को मिटाना था!'"
    },
    {
        "panel": 23, "speaker": "beru", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Beru bola: 'Lekin aapke pita ne system ke maqsad ko ulat diya aur khud Shadow Monarch ban gaye! Aapka system bina kisi bure iraade ke aapka margdarshan kar raha hai!'",
        "text_speak": "बेरू बोला: 'लेकिन आपके पिता ने सिस्टम के इरादों को मात देकर खुद शैडो मोनार्क का ताज हासिल किया! आपका सिस्टम बिना किसी छल के आपको गाइड कर रहा है!'"
    },
    {
        "panel": 24, "speaker": "suho", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Suho ne Status Window kholi: Level 16, Title Wolf Slaughterer, HP 2550, MP 270, Strength 35, aur 5 points bache hain! Class abhi bhi NONE thi!",
        "text_speak": "सू-हो ने स्टेटस विंडो खोली: लेवल सोलह, टाइटल वुल्फ स्लॉटरर, एचपी पच्चीस सौ पचास, एमपी दो सौ सत्तर, स्ट्रेंथ पैंतीस, और पांच पॉइंट्स बचे थे! क्लास अभी भी नन थी!"
    },
    {
        "panel": 25, "speaker": "suho", "emotion": "serious", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Suho ne sankalp liya: 'Main in sabhi quests ko poora karunga... taaki ek din main apne Mata-Pita se mil sakoon!'",
        "text_speak": "सू-हो ने सीना तानकर संकल्प लिया: 'मैं इन सभी क्वेस्ट्स को पूरा करूँगा... ताकि एक दिन मैं अपने माता-पिता से मिल सकूँ!'"
    },
    {
        "panel": 26, "speaker": "narrator", "emotion": "mysterious", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Tabhi Beru Brocky ki laash ko poori tarah nigal kar wapas lauta! Suho ne poocha: 'Beru, kya Itarim ka koi suraag mila?'",
        "text_speak": "तभी बेरू ब्रॉकी के शरीर को पूरी तरह निगलकर वापस लौटा! सू-हो ने पूछा: 'बेरू, क्या इटारिम का कोई सुराग मिला?'"
    },
    {
        "panel": 27, "speaker": "beru", "emotion": "serious", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Beru ne kaha: 'Apostles ka seedha pata nahi chala... lekin un insaano ki yaadein mil gayi hain jinhone Hyena Guild ko banaya tha!'",
        "text_speak": "बेरू ने खुलासा किया: 'अपॉस्टल्स का सीधा पता नहीं चला... लेकिन उन इंसानों की यादें मिल गई हैं जिन्होंने हायना गिल्ड का निर्माण किया था!'"
    },
    {
        "panel": 28, "speaker": "beru", "emotion": "epic", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Beru ne naam liya: 'Unki asli guild ka naam hai... GRIM REAPER!' Suho chonka: 'Grim Reaper Guild?!'",
        "text_speak": "बेरू की आंखें लाल अंगारे जैसी चमकीं: 'उनकी असली गिल्ड का नाम है... ग्रिम रीपर!' सू-हो चौंक उठा: 'ग्रिम रीपर गिल्ड?!'"
    },
    {
        "panel": 29, "speaker": "narrator", "emotion": "tense", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Kahaani aage badhi: Seoul ke ek aalishan penthouse office mein phone ki ghanti baji. Ek ghamandi shakhs ne call uthayi.",
        "text_speak": "कहानी आगे बढ़ी: सियोल के एक आलीशान पेंटहाउस ऑफिस में फोन की घंटी बजी. एक घमंडी शख्स ने कॉल उठाई."
    },
    {
        "panel": 30, "speaker": "minsung", "emotion": "arrogant", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Uss shakhs ne kahan: 'Kya baat hai, Im Taegyu? Tum toh Southeast Asia raid par gaye the na?' Tabhi doosri taraf se ghusse bhari aawaz aayi!",
        "text_speak": "उसने मुस्कुराकर कहा: 'क्या बात है, इम तायग्यू? तुम तो साउथईस्ट एशिया रेड पर गए थे ना?' तभी दूसरी तरफ से गुस्से भरी आवाज़ आई!"
    },
    {
        "panel": 31, "speaker": "taegyu", "emotion": "angry", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "S-Rank Hunter Im Taegyu dahaada: 'Baat ko ghumao mat, Lee Minsung! Tumhara Hyena Guild ke saath kaala sauda sabke samne aane wala hai!'",
        "text_speak": "एस-रैंक हंटर इम तायग्यू गरजा: 'बात मत घुमाओ, ली मिनसुंग! तुम्हारा हायना गिल्ड के साथ काला सौदा सबके सामने आने वाला है!'"
    },
    {
        "panel": 32, "speaker": "minsung", "emotion": "arrogant", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Lee Minsung ne ghamand se kaha: 'Agar Association ne poocha toh main saaf inkaar kar doonga! Mere vakeel Association ka munh band kar denge!'",
        "text_speak": "ली मिनसुंग ने घमंड से कहा: 'अगर एसोसिएशन ने पूछा तो मैं साफ मुकर जाऊंगा! मेरे वकीलों की फौज एसोसिएशन का मुंह बंद कर देगी!'"
    },
    {
        "panel": 33, "speaker": "taegyu", "emotion": "serious", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Im Taegyu ne chetawani di: 'Zyada udne ki zaroorat nahi hai! Hunter Association ke Chairman Woo Jinchul se nipatna asaan nahi hoga! Mere aane se pehle sab theek kar lo!'",
        "text_speak": "इम तायग्यू ने चेतावनी दी: 'ज्यादा हवा में मत उड़ो! हंटर एसोसिएशन के चेयरमैन वू जिनचुल को हल्के में मत लेना! मेरे लौटने से पहले सब साफ कर लो!'"
    },
    {
        "panel": 34, "speaker": "narrator", "emotion": "tense", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Im Taegyu ne phone kaat diya. Lee Minsung ghusse se kaanpne laga: 'Ek S-Rank kya ban gaya... jo kal tak mera driver tha, aaj mujh par chilla raha hai?!'",
        "text_speak": "इम तायग्यू ने फोन काट दिया. ली मिनसुंग का चेहरा गुस्से से लाल हो गया: 'एक एस-रैंक क्या बन गया... जो कल तक मेरा ड्राइवर था, आज मुझ पर हुक्म चला रहा है?!'"
    },
    {
        "panel": 35, "speaker": "minsung", "emotion": "angry", "camera": "handheld_shake", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Lee Minsung ne desk par jordaar ghunsa mara: 'Wo ladka kaun hai jisne Brocky aur Hyena Guild ko tabah kar diya?!'",
        "text_speak": "ली मिनसुंग ने टेबल पर मुक्का मारा: 'वो शिकारी कौन है जिसने ब्रॉकी और पूरी हायना गिल्ड को मिट्टी में मिला दिया?!'"
    },
    {
        "panel": 36, "speaker": "narrator", "emotion": "serious", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Lee Minsung ne socha: 'Zinda bache logon ne sirf itna bataya ki wo kaala mask pehne ek naujawan shikaari tha... mere paas uspar zaya karne ke liye waqt nahi hai!'",
        "text_speak": "ली मिनसुंग ने सोचा: 'बचे हुए लोगों ने सिर्फ इतना कहा कि वो काला मास्क पहने एक नौजवान था... मेरे पास उसपर बर्बाद करने के लिए वक्त नहीं है!'"
    },
    {
        "panel": 37, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Yeh hai Grim Reaper Guild ka Vice-CEO aur A-Rank Hunter — Lee Minsung!",
        "text_speak": "ये है ग्रिम रीपर गिल्ड का वाइस-सीईओ और ए-रैंक हंटर — ली मिनसुंग!"
    },
    {
        "panel": 38, "speaker": "minsung", "emotion": "evil", "camera": "slow_push", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Lee Minsung ne apne coat ki jeb se ek chamakta hua jaadui crystal nikala — 'Hunter Awakening Stimulant: STARDUST'!",
        "text_speak": "ली मिनसुंग ने अपनी जेब से एक चमकता हुआ रहस्यमयी क्रिस्टल निकाला — 'हंटर अवेकनिंग स्टिमुलैंट: स्टारडस्ट'!"
    },
    {
        "panel": 39, "speaker": "narrator", "emotion": "fearful", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Uss crystal ke andar baingani dhuein mein ek ajeeb parchhayi aur khaufnaak laal aankhein dikh rahi thi!",
        "text_speak": "उस क्रिस्टल के अंदर बैंगनी धुएं में एक भयानक साया और खौफनाक लाल आंखें कैद थीं!"
    },
    {
        "panel": 40, "speaker": "minsung", "emotion": "evil", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Lee Minsung ek darawni muskaan ke saath bola: 'Agar mera yeh kaarobaar safal ho gaya... toh koi bhi mujh par ungli uthane ki himmat nahi karega!'",
        "text_speak": "ली मिनसुंग एक शैतानी मुस्कान के साथ फुसफुसाया: 'अगर मेरा ये धंधा कामयाब रहा... तो कोई भी मुझे नीची नज़र से देखने की हिम्मत नहीं करेगा!'"
    }
]

# ─────────────────────────────────────────────────────────────────────────────
# VOICEOVER GENERATOR (10X BETTER HUMANOID EMOTIVE QUALITY)
# ─────────────────────────────────────────────────────────────────────────────
async def generate_voice(text_speak: str, speaker: str, emotion: str, out_wav: Path):
    import edge_tts

    voice = "hi-IN-MadhurNeural"
    rate_str = "+17%"  # Calibrated for 4.5m
    pitch_str = "+0Hz"

    if speaker == "beru":
        rate_str = "+20%"
        pitch_str = "+5Hz"
    elif speaker == "suho":
        rate_str = "+18%"
        pitch_str = "+1Hz"
    elif speaker == "taegyu":
        rate_str = "+14%"
        pitch_str = "-3Hz"
    elif speaker == "minsung":
        rate_str = "+15%"
        pitch_str = "-2Hz"

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
# SINGLE-PASS COMPOSITOR (ZERO DUPLICATE FILES)
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
Title: Solo Leveling Ragnarok Chapter 14 Subtitles
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
        style = "RagnarokGold" if sc["speaker"] in ["minsung", "beru", "system", "taegyu"] else "RagnarokCyan"
        text = sc["text_sub"].replace("\n", "\\N")
        events.append(f"Dialogue: 0,{fmt_time(start_s)},{fmt_time(end_s)},{style},,0,0,0,,{text}")
        curr = end_s

    out_ass.parent.mkdir(parents=True, exist_ok=True)
    with open(out_ass, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + "\n")
    print(f"  ✓ Dual-Color Subtitles generated: {out_ass.name}")

def create_thumbnail(out_thumb: Path):
    out_thumb.parent.mkdir(parents=True, exist_ok=True)
    p38 = PANELS_DIR / "panel_038.jpg" # Lee Minsung holding Stardust crystal orb
    if not p38.exists():
        p38 = PANELS_DIR / "panel_001.jpg"

    with Image.open(str(p38)) as im:
        thumb = im.convert("RGB").resize((1280, 720), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(thumb)
    try:
        font_big = ImageFont.truetype("arialbd.ttf", 64)
        font_sub = ImageFont.truetype("arialbd.ttf", 42)
    except Exception:
        font_big = ImageFont.load_default()
        font_sub = font_big

    draw.rectangle([(20, 20), (1260, 160)], fill=(10, 12, 24, 220))
    draw.text((40, 30), "GRIM REAPER GUILD CONSPIRACY! 💀✨", fill=(0, 240, 255), font=font_big)
    draw.text((40, 100), "CHAPTER 14 FULL RECAP IN HINDI", fill=(255, 215, 0), font=font_sub)

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
    print("  ⚔️ SOLO LEVELING: RAGNAROK CHAPTER 14 — MASTER PRODUCTION")
    print("  Target: Strictly 4 to 5 Minutes (240s–300s) · 10x Humanoid Voice")
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
    print(f"  ⏱️ EXACT TOTAL DURATION: {total_dur:.1f}s ({total_dur/60:.2f} minutes)")
    print("=" * 75)

    # Concatenate
    concat_list = OUT_DIR / "concat_list_final.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for clip in scene_clips:
            clean_path = str(clip.resolve()).replace("\\", "/")
            f.write(f"file '{clean_path}'\n")

    unsubbed_mp4 = OUT_DIR / "solo_leveling_ragnarok_ch14_unsubbed.mp4"
    print(f"\n📦 Concatenating all {len(scene_clips)} scenes into {unsubbed_mp4.name}...")
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(unsubbed_mp4)
    ], check=True)

    # Calibrate to exactly 270s if needed
    final_mp4 = OUT_DIR / "solo_leveling_ragnarok_ch14_final.mp4"
    if not (240.0 <= total_dur <= 300.0):
        target_total = 270.0
        factor = total_dur / target_total
        print(f"  ⚠️ Recalibrating duration from {total_dur:.1f}s to {target_total:.1f}s (factor: {factor:.4f}x)...")
        scene_durs = [round(d / factor, 3) for d in scene_durs]
        total_dur = sum(scene_durs)

        ass_path = OUT_DIR / "solo_leveling_ragnarok_ch14.ass"
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
        ass_path = OUT_DIR / "solo_leveling_ragnarok_ch14.ass"
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

    # Clean up unsubbed mp4 to save disk space
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

    print("\n" + "🎉" * 38)
    print("  ✅ SOLO LEVELING: RAGNAROK CHAPTER 14 FINAL MASTER IS READY!")
    print(f"  📁 Output: {final_mp4}")
    print(f"  ⏱️ Final Duration: {final_sec:.1f}s ({final_sec/60:.2f} minutes)")
    print(f"  💾 File Size: {final_size_mb:.2f} MB")
    print("🎉" * 38 + "\n")

    if not (240.0 <= final_sec <= 300.0):
        raise ValueError(f"CRITICAL: Final duration {final_sec:.1f}s is not within 240s-300s window!")

    return final_mp4

def main():
    asyncio.run(run_pipeline())

if __name__ == "__main__":
    main()
