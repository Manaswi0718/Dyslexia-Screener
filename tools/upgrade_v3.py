"""
v3 content update:
  * the owl is now called Errol (renames Ollie everywhere)
  * Errol says something different after each island (6 variations per language)
Safe to run more than once. Then run:  python tools/gen_audio.py
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "static" / "content.json"
c = json.load(open(P, encoding="utf-8"))

HELLO = {
    "en": "Hi! I am Errol the owl. Let's go on an island adventure!",
    "hi": "नमस्ते! मैं एरल उल्लू हूँ। चलो द्वीपों के सफ़र पर चलें!",
    "te": "నమస్తే! నేను ఎరల్ గుడ్లగూబను. రా, దీవుల సాహస యాత్రకు వెళ్దాం!",
}
NEXT = {
    "en": ["Great job! Let's fly to the next island!",
           "Wow, you are doing so well! Ready for the next one?",
           "Hoot hoot! Another island unlocked!",
           "Brilliant! Let's see what is on the next island.",
           "You are a real word wizard! On we go!",
           "Fantastic! Take a deep breath, then let's play again."],
    "hi": ["बहुत बढ़िया! चलो अगले द्वीप पर उड़ते हैं!",
           "वाह, तुम कमाल कर रहे हो! अगले के लिए तैयार?",
           "हू हू! एक और द्वीप खुल गया!",
           "शानदार! चलो देखें अगले द्वीप पर क्या है।",
           "तुम सच में शब्द जादूगर हो! आगे चलें!",
           "बहुत खूब! एक गहरी साँस लो, फिर खेलते हैं।"],
    "te": ["చాలా బాగుంది! తర్వాతి దీవికి ఎగురుదాం!",
           "వావ్, నువ్వు అద్భుతంగా చేస్తున్నావు! తర్వాతి దానికి సిద్ధమా?",
           "హూ హూ! ఇంకో దీవి తెరుచుకుంది!",
           "అదిరింది! తర్వాతి దీవిలో ఏముందో చూద్దాం.",
           "నువ్వు నిజమైన పద మాంత్రికుడివి! ముందుకు వెళ్దాం!",
           "భలే! ఒక్కసారి గట్టిగా ఊపిరి తీసుకో, మళ్ళీ ఆడదాం."],
}
SETUP = {
    "en": "Hello, grown-ups! I am Errol. Please fill in this page, then give the device to the child, and I will guide them through the islands.",
    "hi": "नमस्ते! मैं एरल हूँ। कृपया यह पेज भरें, फिर डिवाइस बच्चे को दें। मैं उन्हें द्वीपों की सैर कराऊँगा।",
    "te": "నమస్కారం! నేను ఎరల్. దయచేసి ఈ పేజీ నింపి, తర్వాత పరికరాన్ని పిల్లలకు ఇవ్వండి. నేను వారిని దీవుల గుండా తీసుకెళ్తాను.",
}
NEXT_LABEL = {"en": "Next island:", "hi": "अगला द्वीप:", "te": "తర్వాతి దీవి:"}
RENAME = [("Ollie", "Errol"), ("ओली", "एरल"), ("ఓలీ", "ఎరల్")]

for lang in ("en", "hi", "te"):
    if lang not in c:
        continue
    ui = c[lang]["ui"]
    for k, v in list(ui.items()):
        if isinstance(v, str):
            for a, b in RENAME:
                v = v.replace(a, b)
            ui[k] = v
    ui["owlHello"] = HELLO[lang]
    ui.setdefault("owlNextList", NEXT[lang])
    ui.setdefault("nextLabel", NEXT_LABEL[lang])
    ui["owlSetup"] = SETUP[lang]

json.dump(c, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("Content updated: owl renamed to Errol, 6 island messages per language")
