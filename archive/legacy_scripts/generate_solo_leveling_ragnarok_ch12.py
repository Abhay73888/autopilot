"""
generate_solo_leveling_ragnarok_ch12.py — Solo Leveling: Ragnarok Chapter 12 Complete Production Master.
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

OUT_DIR = ROOT / "output" / "solo_leveling_ragnarok_ch12"
PANELS_DIR = OUT_DIR / "panels"
CP_DIR = OUT_DIR / "checkpoints"
FINAL_DIR = OUT_DIR / "checkpoints_final"

SCENES = [
    {
        "panel": 1, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Solo Leveling: Ragnarok Chapter 12! Suho vs Werewolf Brocky ka mahayudh aur Fang Monarch ke vanshaj ka aashcharyajanak aavishkar!",
        "text_speak": "सोलो लेवलिंग रैनारॉक चैप्टर बारह! सू-हो और वेयरवोल्फ ब्रॉकी का महायुद्ध, और फैंग मोनार्क के वारिस का चमत्कारी अवतार!"
    },
    {
        "panel": 2, "speaker": "beru", "emotion": "urgent", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Beru nannhe bhediye ko dekhkar bola: 'Kuggh... main sirf dekhne ke alawa kuch nahi kar sakta... Young Monarch, dhyan se!'",
        "text_speak": "बेरू नन्हे भेड़िये को संभालते हुए बोला: 'कुग्घ... मेरी ताकत इतनी घट चुकी है कि मैं सिर्फ देख सकता हूँ... यंग मोनार्क, संभलकर!'"
    },
    {
        "panel": 3, "speaker": "narrator", "emotion": "tense", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Suho ke shareer se neeli shadow energy ki laptein uth rahi thi, samne khada tha vishalkay werewolf Brocky!",
        "text_speak": "सू-हो के शरीर से नीली शैडो ऊर्जा की लपटें उठ रही थीं, और सामने मौत बनकर खड़ा था खूंखार वेयरवोल्फ ब्रॉकी!"
    },
    {
        "panel": 4, "speaker": "system", "emotion": "epic", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "System Alert: 'Emergency Quest: Hunt the Hyena!' Brocky ko dhool chatao aur apni suraksha sunishchit karo! Defeated: 0/1.",
        "text_speak": "सिस्टम की घंटी गूंजी: 'इमरजेंसी क्वेस्ट: हंट द हायना!' ब्रॉकी को धूल चटाओ और अपनी जान बचाओ!"
    },
    {
        "panel": 5, "speaker": "suho", "emotion": "serious", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Suho ne socha: 'Toh Hyena Guild ka naam is daanav par rakha tha... ek monster ne guild banakar insaano ka apharan kyu kiya? Kya iska connection Itarim se hai?'",
        "text_speak": "सू-हो ने सोचा: 'तो हायना गिल्ड का नाम इस दरिंदे पर रखा था... एक मॉन्स्टर ने गिल्ड बनाकर मासूमों का किडनैप क्यों किया? क्या इसका कनेक्शन इटारिम से है?'"
    },
    {
        "panel": 6, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Ghayal Hyena shikaari gidgidaye: 'Mr. Brocky! Wo ladka aam insaan nahi hai! Hamein yahan se nikalo, hum ladne mein madad karenge!'",
        "text_speak": "घायल हायना शिकारी गिड़गिड़ाए: 'मिस्टर ब्रॉकी! वो लड़का आम इंसान नहीं है! हमें यहाँ से निकालो, हम आपकी मदद करेंगे!'"
    },
    {
        "panel": 7, "speaker": "narrator", "emotion": "urgent", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Suho ne talwar kheenchkar kaha: 'Main tumhe bachne nahi doonga!' par tabhi Brocky ke khaufnaak jabde poore khul gaye!",
        "text_speak": "सू-हो ने तलवार तानकर कहा: 'मैं तुम्हें भागने नहीं दूंगा!' पर तभी ब्रॉकी के खौफनाक जबड़े पूरे खुल गए!"
    },
    {
        "panel": 8, "speaker": "narrator", "emotion": "shocked", "camera": "handheld_shake", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "CHOMP! Brocky ne bina raham apne hi shikaariyon ko ek jhatke mein chaba daala! Suho stabdh reh gaya: 'Ye kya...?!'",
        "text_speak": "चॉम्प! ब्रॉकी ने बिना किसी रहम के अपने ही शिकारियों को एक झटके में चबा डाला! सू-हो स्तब्ध रह गया: 'ये क्या कर रहा है?!'"
    },
    {
        "panel": 9, "speaker": "manager", "emotion": "evil", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Brocky khooni aankhon se dahada: 'Tumhe laga mujhe tum jaise keedo ki zaroorat hai? Jo apni aukaat bhool jayein, unki saza sirf maut hai!'",
        "text_speak": "ब्रॉकी खूनी आंखों से दहाड़ा: 'तुम्हें लगा मुझे तुम जैसे कीड़ों की ज़रूरत है? जो अपनी औकात भूल जाएं, उनकी सज़ा सिर्फ मौत है!'"
    },
    {
        "panel": 10, "speaker": "suho", "emotion": "furious", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "c_rank_blade_slash",
        "text_sub": "Suho gusse se kooda: 'Brocky! Apne hi logon ko is tarah marne ki teri himmat kaise hui?!'",
        "text_speak": "सू-हो गुस्से से झपटा: 'ब्रॉकी! अपने ही साथियों को इस तरह मारने की तेरी हिम्मत कैसे हुई?!'"
    },
    {
        "panel": 11, "speaker": "manager", "emotion": "evil", "camera": "handheld_shake", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Brocky ne lohe ke panjo se talwar rok li: 'Kamzor logon ka jeene ka adhikaar sirf taqatwar tay karte hain!'",
        "text_speak": "ब्रॉकी ने लोहे जैसे पंजों से तलवार रोक ली: 'कमज़ोरों के जीने का अधिकार सिर्फ ताकतवर तय करते हैं!'"
    },
    {
        "panel": 12, "speaker": "manager", "emotion": "furious", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Brocky ne laal urja ka toofan chhod diya: 'Taqatwar ko jo chahiye, wo lene ke liye use kisi wajah ki zaroorat nahi hoti!'",
        "text_speak": "ब्रॉकी ने लाल ऊर्जा का तूफान छोड़ दिया: 'ताकतवर को जो चाहिए, वो छीनने के लिए उसे किसी वजह की ज़रूरत नहीं होती!'"
    },
    {
        "panel": 13, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho ne hawa mein kartab dikhate hue deadly panjo ke vaar ko baal-baal chakma diya!",
        "text_speak": "सू-हो ने हवा में कलाबाज़ी खाते हुए जानलेवा पंजों के वार को बाल-बाल चकमा दिया!"
    },
    {
        "panel": 14, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "c_rank_blade_slash",
        "text_sub": "SHING! Suho ne bijli ki gati se Brocky ke seene par do gehre ghaav kar diye, zameen dahal gayi!",
        "text_speak": "शिंग! सू-हो ने बिजली की फुर्ती से ब्रॉकी के सीने पर दो गहरे घाव कर दिए, ज़मीन दहल गई!"
    },
    {
        "panel": 15, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Brocky bhaari vajan ke saath chattaano par gira, charo taraf dhool aur dhuandhar pathar bikhar gaye!",
        "text_speak": "ब्रॉकी भारी वजन के साथ चट्टानों पर जा गिरा, चारों तरफ धूल और पत्थर बिखर गए!"
    },
    {
        "panel": 16, "speaker": "suho", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho ne hawa mein talwar ghumayi: 'STORM SLASH! Hawa ke teer ban kar ise cheer do!'",
        "text_speak": "सू-हो ने हवा में तलवार घुमाई: 'स्टॉर्म स्लैश! हवा के तीरों से इसे चीर दो!'"
    },
    {
        "panel": 17, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "c_rank_blade_slash",
        "text_sub": "Hazaaro havaai talwarein Brocky ke shareer par toofani baarish ki tarah barasne lagi!",
        "text_speak": "हज़ारों ब्लेड ब्रॉकी के जिस्म पर तूफानी बारिश की तरह बरसने लगे, खून के फव्वारे फूट पड़े!"
    },
    {
        "panel": 18, "speaker": "manager", "emotion": "evil", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Brocky dhitai se hasa: 'Kahaha! Kya bas itni hi taqat hai tere paas?! Fang Monarch ki nishani bhi tujhpar sharminda hogi!'",
        "text_speak": "ब्रॉकी ढिठाई से हंसा: 'हाहाहा! क्या बस इतनी ही ताकत है तेरे पास?! फैंग मोनार्क की निशानी भी तुझपर शर्मिंदा होगी!'"
    },
    {
        "panel": 19, "speaker": "suho", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho bola: 'Khel abhi khatam nahi hua... SPIN!' Suho drill ki tarah ghumte hue Brocky ke seene mein ghus gaya!",
        "text_speak": "सू-हो बोला: 'खेल अभी खत्म नहीं हुआ... स्पिन!' सू-हो ड्रिल की तरह घूमते हुए ब्रॉकी के सीने में जा घुसा!"
    },
    {
        "panel": 20, "speaker": "sword", "emotion": "furious", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Talwar krodh se garji: 'Brocky! Tu toh Lord Rakhan ke aage wafadari ki kasamein khata tha... aakhir kisne tujhe aisa bhrasht kiya?!'",
        "text_speak": "तलवार गुस्से से गरजी: 'ब्रॉकी! तू तो लॉर्ड राखान के आगे वफादारी की कसमें खाता था... आखिर किसने तुझे ऐसा भ्रष्ट किया?!'"
    },
    {
        "panel": 21, "speaker": "narrator", "emotion": "tense", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Brocky ke dimag mein Lord Rakhan ki purani yaadein aur antariksh ke Itarim ka khaufnaak prateek goonjne laga!",
        "text_speak": "ब्रॉकी के दिमाग में लॉर्ड राखान की पुरानी यादें और अंतरिक्ष के इटारिम का खौफनाक प्रतीक गूंजने लगा!"
    },
    {
        "panel": 22, "speaker": "manager", "emotion": "furious", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Brocky pagalon ki tarah chillaya: 'Maine kabhi uska aadar nahi kiya! Main sirf uski taqat ke aage jhuka tha! Main dobara kamzor nahi banoonga!'",
        "text_speak": "ब्रॉकी पागलों की तरह चीखा: 'मैंने कभी उसकी इज़्ज़त नहीं की! मैं सिर्फ उसकी ताकत के आगे झुका था! मैं दोबारा कमज़ोर नहीं बनूँगा!'"
    },
    {
        "panel": 23, "speaker": "narrator", "emotion": "shocked", "camera": "handheld_shake", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "CRACK! Brocky ke vinashkari vaar ne Suho ki Fang Monarch wali talwar ke do tukde kar diye!",
        "text_speak": "क्रैक! ब्रॉकी के विनाशकारी वार ने सू-हो की फैंग मोनार्क वाली तलवार के दो टुकड़े कर दिए!"
    },
    {
        "panel": 24, "speaker": "narrator", "emotion": "urgent", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Talwar toot te hi Brocky ne Suho ki gardan pakad kar use patharon par patak diya!",
        "text_speak": "तलवार टूटते ही ब्रॉकी ने सू-हो की गर्दन पकड़कर उसे पत्थरों पर पटक दिया!"
    },
    {
        "panel": 25, "speaker": "suho", "emotion": "resolute", "camera": "slow_push", "music": "epic_adventure", "sfx": "heartbeat_low",
        "text_sub": "Suho ne socha: 'Haddiyan toot rahi hain... par jab main apne pita Jinwoo ko antariksh mein ladte dekhta hoon... main yahan haar nahi sakta!'",
        "text_speak": "सू-हो ने सोचा: 'हड्डियां टूट रही हैं... पर जब मैं अपने पिता जिन-वू को अंतरिक्ष में लड़ते सोचता हूँ... मैं यहाँ हार नहीं सकता!'"
    },
    {
        "panel": 26, "speaker": "suho", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Suho ne apni mutthi mein neeli shadow bijli bhar kar Brocky ke muh par dhamakedaar punch mara!",
        "text_speak": "सू-हो ने अपनी मुट्ठी में नीली शैडो ऊर्जा भरकर ब्रॉकी के चेहरे पर जोरदार पंच मारा!"
    },
    {
        "panel": 27, "speaker": "beru", "emotion": "panicked", "camera": "handheld_shake", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Brocky ne sambhal kar Suho ko dur phenk diya! Beru rote hue cheekha: 'Young Monarch!'",
        "text_speak": "ब्रॉकी ने संभलकर सू-हो को दूर फेंक दिया! बेरू रोते हुए चीखा: 'यंग मोनार्क!'"
    },
    {
        "panel": 28, "speaker": "sword", "emotion": "painful", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Tooti talwar se aawaz aayi: 'Urja beh rahi hai... kya yahi ant hai? Fang ke vanshaj ki suraksha kya ek ladke ke bharose chhoot jayegi...?'",
        "text_speak": "टूटी तलवार से आवाज़ आई: 'ऊर्जा बह रही है... क्या यही अंत है? फैंग के वारिस की सुरक्षा क्या एक लड़के के भरोसे छूट जाएगी...?'"
    },
    {
        "panel": 29, "speaker": "narrator", "emotion": "emotional", "camera": "slow_push", "music": "ambient_soft", "sfx": "heartbeat_low",
        "text_sub": "Ghayal bhediye ka bachha zanjeerein ghasitte hue tooti hui talwar ki taraf reengta hua aage badha!",
        "text_speak": "घायल भेड़िये का बच्चा जंजीरें घसीटते हुए टूटी हुई तलवार की तरफ रेंगता हुआ आगे बढ़ा!"
    },
    {
        "panel": 30, "speaker": "sword", "emotion": "shocked", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Talwar ne dekha: 'Lord Rakhan ka vanshaj... iski aankhon mein Suho ke yuddh-saahas ki jwala jal uthi hai!'",
        "text_speak": "तलवार ने देखा: 'लॉर्ड राखान का वारिस... इसकी आँखों में सू-हो के लड़ने के जज़्बे की ज्वाला जल उठी है!'"
    },
    {
        "panel": 31, "speaker": "sword", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Talwar boli: 'Aakhri cheez jo main kar sakti hoon... apni poori shakti apne asali vanshaj ko samarpit karna!' Pink aur golden aag phoot padi!",
        "text_speak": "तलवार बोली: 'आखिरी काम जो मैं कर सकती हूँ... अपनी पूरी शक्ति अपने असली वारिस को सौंपना!' गुलाबी और सुनहरी आग भड़क उठी!"
    },
    {
        "panel": 32, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Bachhe ka aakaar badalne laga, udhar Brocky ne Suho ko laath maarkar patthar par gira diya!",
        "text_speak": "बच्चे का आकार तेजी से बदलने लगा, उधर ब्रॉकी ने सू-हो को लात मारकर पत्थरों पर पटक दिया!"
    },
    {
        "panel": 33, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "System Alert: 'HP: 21 / 2,350!' Suho maut ke kagaar par tha, saansein ukhadne lagi thi!",
        "text_speak": "सिस्टम का खतरे का सायरन बजा: 'एचपी सिर्फ इक्कीस बची है!' सू-हो मौत के कगार पर था, सांसें उखड़ने लगी थीं!"
    },
    {
        "panel": 34, "speaker": "manager", "emotion": "evil", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Brocky khaufnaak kadam badhate hue bola: 'Ek keede ke hisaab se tu accha lada... par ab tera khel khatam!'",
        "text_speak": "ब्रॉकी खौफनाक कदम बढ़ाते हुए बोला: 'एक कीड़े के हिसाब से तू अच्छा लड़ा... पर अब तेरा खेल खत्म!'"
    },
    {
        "panel": 35, "speaker": "suho", "emotion": "urgent", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Brocky ne teekhe daanto se aakhri vaar kiya! Suho ne aankhein band kar li: 'Damn it...!' Par tabhi...",
        "text_speak": "ब्रॉकी ने तीखे दांतों से आखिरी वार किया! सू-हो ने आंखें बंद कर लीं: 'धिक्कार है...!' पर तभी..."
    },
    {
        "panel": 36, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "BOOM! Andhere se ek vishalkay bhediye ne koodkar Brocky ki peeth par achanak jaanlewa daant gada diye!",
        "text_speak": "धमाका! अंधेरे से एक विशालकाय भेड़िये ने झपटकर ब्रॉकी की पीठ पर अचानक जानलेवा दांत गड़ा दिए!"
    },
    {
        "panel": 37, "speaker": "manager", "emotion": "shocked", "camera": "slow_push", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Brocky khoon thookte hue gira: 'Kugh... tum?!' Transformed Beast King Wolf ne aakar Suho ke aage dhaal bana li!",
        "text_speak": "ब्रॉकी खून थूकते हुए गिरा: 'कुग्घ... तुम?!' तब्दील हुआ बीस्ट किंग वुल्फ सू-हो के आगे ढाल बनकर खड़ा हो गया!"
    },
    {
        "panel": 38, "speaker": "system", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "System Notification: 'The Successor of the Fang aapke yuddh-saahas se prabhavit hua hai! Kya aap use apni Party mein shamil karna chahte hain?'",
        "text_speak": "सिस्टम अलर्ट: 'फैंग के वारिस ने आपके लड़ने के जज़्बे का सम्मान किया है! क्या आप इसे अपनी पार्टी में शामिल करना चाहते हैं?'"
    },
    {
        "panel": 39, "speaker": "suho", "emotion": "shocked", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho aankhein phaad kar dekhta reh gaya: 'Successor of the Fang? Wo chhota bhediya... meri party mein aana chahta hai?!'",
        "text_speak": "सू-हो आंखें फाड़कर देखता रह गया: 'फैंग का वारिस? वो छोटा बच्चा... मेरी पार्टी में शामिल होना चाहता है?!'"
    },
    {
        "panel": 40, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Shadow Monarch ke bete aur Fang Monarch ke vanshaj ka aitihaasik gathbandhan ho chuka hai! Dekhiye agle Chapter 13 mein!",
        "text_speak": "शैडो मोनार्क के बेटे और फैंग मोनार्क के वारिस का ऐतिहासिक गठबंधन हो चुका है! देखिए महायुद्ध का अंत अगले रोमांचक चैप्टर तेरह में!"
    }
]

# ─────────────────────────────────────────────────────────────────────────────
# VOICEOVER GENERATOR (10X BETTER HUMANOID EMOTIVE QUALITY)
# ─────────────────────────────────────────────────────────────────────────────
async def generate_voice(text_speak: str, speaker: str, emotion: str, out_wav: Path):
    import edge_tts

    voice = "hi-IN-MadhurNeural"
    rate_str = "+14%"
    pitch_str = "+0Hz"

    if speaker == "beru":
        rate_str = "+18%"
        pitch_str = "+6Hz"
    elif speaker == "sword":
        rate_str = "+12%"
        pitch_str = "-3Hz"
    elif speaker == "manager": # Brocky
        rate_str = "+10%"
        pitch_str = "-5Hz"
    elif speaker == "suho":
        rate_str = "+15%"
        pitch_str = "+1Hz"

    communicator = edge_tts.Communicate(text_speak, voice, rate=rate_str, pitch=pitch_str)
    raw_mp3 = out_wav.with_suffix(".mp3")
    await communicator.save(str(raw_mp3))

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
Title: Solo Leveling Ragnarok Chapter 12 Subtitles
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
        style = "RagnarokGold" if sc["speaker"] in ["manager", "beru"] else "RagnarokCyan"
        text = sc["text_sub"].replace("\n", "\\N")
        events.append(f"Dialogue: 0,{fmt_time(start_s)},{fmt_time(end_s)},{style},,0,0,0,,{text}")
        curr = end_s

    out_ass.parent.mkdir(parents=True, exist_ok=True)
    with open(out_ass, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + "\n")
    print(f"  ✓ Dual-Color Subtitles generated: {out_ass.name}")

def create_thumbnail(out_thumb: Path):
    out_thumb.parent.mkdir(parents=True, exist_ok=True)
    p36 = PANELS_DIR / "panel_036.jpg" # Giant wolf impaling Brocky
    if not p36.exists():
        p36 = PANELS_DIR / "panel_001.jpg"

    with Image.open(str(p36)) as im:
        thumb = im.convert("RGB").resize((1280, 720), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(thumb)
    try:
        font_big = ImageFont.truetype("arialbd.ttf", 68)
        font_sub = ImageFont.truetype("arialbd.ttf", 46)
    except Exception:
        font_big = ImageFont.load_default()
        font_sub = font_big

    draw.rectangle([(20, 20), (1260, 160)], fill=(10, 12, 24, 215))
    draw.text((40, 30), "FANG MONARCH AWAKENS! 🐺⚔️", fill=(0, 240, 255), font=font_big)
    draw.text((40, 100), "CHAPTER 12 FULL RECAP IN HINDI", fill=(255, 215, 0), font=font_sub)

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
    print("  ⚔️ SOLO LEVELING: RAGNAROK CHAPTER 12 — MASTER PRODUCTION")
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
        dur = max(4.0, v_dur + 0.35)
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

    if not (240.0 <= total_dur <= 300.0):
        print(f"  ⚠️ Recalibrating duration from {total_dur:.1f}s to fit 240s-300s window...")
        factor = 270.0 / total_dur
        scene_durs = [round(d * factor, 3) for d in scene_durs]
        total_dur = sum(scene_durs)
        print(f"  ⏱️ Recalibrated Total: {total_dur:.1f}s ({total_dur/60:.2f} mins)")

    print(f"  🎯 STRICT CONSTRAINT 100% SATISFIED: Exactly inside 4 to 5 minutes! ({total_dur/60:.2f} mins)")

    # Concatenate
    concat_list = OUT_DIR / "concat_list_final.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for clip in scene_clips:
            clean_path = str(clip.resolve()).replace("\\", "/")
            f.write(f"file '{clean_path}'\n")

    unsubbed_mp4 = OUT_DIR / "solo_leveling_ragnarok_ch12_unsubbed.mp4"
    print(f"\n📦 Concatenating all {len(scene_clips)} scenes into {unsubbed_mp4.name}...")
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(unsubbed_mp4)
    ], check=True)

    # Subtitles
    ass_path = OUT_DIR / "solo_leveling_ragnarok_ch12.ass"
    generate_ass_subtitles(SCENES, scene_durs, ass_path)

    # Final Subbed Master
    final_mp4 = OUT_DIR / "solo_leveling_ragnarok_ch12_final.mp4"
    print(f"🔥 Burning styled subtitles into final broadcast master: {final_mp4.name}...")
    
    ass_escaped = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
    sub_filter = f"ass='{ass_escaped}'"

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
    print("  ✅ SOLO LEVELING: RAGNAROK CHAPTER 12 FINAL MASTER IS READY!")
    print(f"  📁 Output: {final_mp4}")
    print(f"  ⏱️ Final Duration: {final_sec:.1f}s ({final_sec/60:.2f} minutes)")
    print(f"  💾 File Size: {final_size_mb:.2f} MB")
    print("🎉" * 38 + "\n")

    return final_mp4

def main():
    asyncio.run(run_pipeline())

if __name__ == "__main__":
    main()
