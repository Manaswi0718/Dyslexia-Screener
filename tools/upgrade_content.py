"""
Adds content for the new games (Letter Sounds, Dot Flash, Bigger Number, Catch the Star),
the owl guide's lines, and praise words to static/content.json.
Never overwrites anything you already edited.

Run once:  python tools/upgrade_content.py     then:  python tools/gen_audio.py
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "static" / "content.json"
c = json.load(open(P, encoding="utf-8"))

UI = {
    "en": {"letterTitle": "Sound Detective", "letterInstr": "Listen to the sound, then tap the letter that makes it.",
           "dotsTitle": "Dot Flash", "dotsInstr": "Dots will flash for a moment. How many were there? Tap the number!",
           "cmpTitle": "Bigger Number", "cmpInstr": "Tap the bigger number, as fast as you can!",
           "gngTitle": "Catch the Star", "gngInstr": "Tap when you see a star. Do not tap the rain cloud!",
           "owlHello": "Hi! I am Ollie the owl. Let's go on an island adventure!",
           "owlNext": "Great job! Let's fly to the next island!",
           "owlDone": "You finished every island! You are a star!",
           "tapStar": "Tap!", "praise": ["Great!", "Nice!", "Super!", "Well done!"]},
    "hi": {"letterTitle": "आवाज़ जासूस", "letterInstr": "आवाज़ सुनो, फिर वह अक्षर टैप करो जिसकी यह आवाज़ है।",
           "dotsTitle": "बिंदु झलक", "dotsInstr": "बिंदु थोड़ी देर के लिए दिखेंगे। कितने थे? सही संख्या पर टैप करो!",
           "cmpTitle": "बड़ी संख्या", "cmpInstr": "दोनों में से बड़ी संख्या पर जल्दी से टैप करो!",
           "gngTitle": "तारा पकड़ो", "gngInstr": "तारा दिखे तो टैप करो। बादल दिखे तो टैप मत करो!",
           "owlHello": "नमस्ते! मैं ओली उल्लू हूँ। चलो द्वीपों के सफ़र पर चलें!",
           "owlNext": "बहुत बढ़िया! चलो अगले द्वीप पर उड़ते हैं!",
           "owlDone": "तुमने सारे द्वीप पूरे कर लिए! तुम एक सितारा हो!",
           "tapStar": "टैप!", "praise": ["बढ़िया!", "शाबाश!", "वाह!", "बहुत अच्छे!"]},
    "te": {"letterTitle": "శబ్ద గూఢచారి", "letterInstr": "శబ్దం విని, ఆ శబ్దం వచ్చే అక్షరాన్ని నొక్కు.",
           "dotsTitle": "చుక్కల మెరుపు", "dotsInstr": "చుక్కలు కొద్దిసేపు కనిపిస్తాయి. ఎన్ని ఉన్నాయి? సంఖ్యను నొక్కు!",
           "cmpTitle": "పెద్ద సంఖ్య", "cmpInstr": "రెండింటిలో పెద్ద సంఖ్యను త్వరగా నొక్కు!",
           "gngTitle": "నక్షత్రం పట్టు", "gngInstr": "నక్షత్రం కనిపిస్తే నొక్కు. మేఘం కనిపిస్తే నొక్కకు!",
           "owlHello": "నమస్తే! నేను ఓలీ గుడ్లగూబను. రా, దీవుల సాహస యాత్రకు వెళ్దాం!",
           "owlNext": "చాలా బాగుంది! తర్వాతి దీవికి ఎగురుదాం!",
           "owlDone": "నువ్వు అన్ని దీవులూ పూర్తి చేశావు! నువ్వు ఒక నక్షత్రం!",
           "tapStar": "నొక్కు!", "praise": ["బాగుంది!", "భలే!", "సూపర్!", "చక్కగా చేశావు!"]},
}

# Letter Sounds: the app SAYS the letter, the child taps it among look-alike / sound-alike options
LETTERS = {
    "en": [{"say": "b", "letter": "b", "distractors": ["d", "p", "q"]},
           {"say": "d", "letter": "d", "distractors": ["b", "q", "p"]},
           {"say": "m", "letter": "m", "distractors": ["n", "w", "u"]},
           {"say": "f", "letter": "f", "distractors": ["t", "v", "l"]},
           {"say": "g", "letter": "g", "distractors": ["j", "q", "p"]},
           {"say": "s", "letter": "s", "distractors": ["z", "c", "x"]},
           {"say": "n", "letter": "n", "distractors": ["m", "u", "h"]},
           {"say": "k", "letter": "k", "distractors": ["c", "x", "h"]}],
    "hi": [{"say": "ब", "letter": "ब", "distractors": ["व", "क", "र"]},
           {"say": "घ", "letter": "घ", "distractors": ["ध", "छ", "थ"]},
           {"say": "म", "letter": "म", "distractors": ["भ", "य", "स"]},
           {"say": "प", "letter": "प", "distractors": ["ष", "फ", "य"]},
           {"say": "द", "letter": "द", "distractors": ["ड", "ढ", "ट"]},
           {"say": "ल", "letter": "ल", "distractors": ["त", "न", "ज"]},
           {"say": "ख", "letter": "ख", "distractors": ["रव", "क", "ग"]},
           {"say": "स", "letter": "स", "distractors": ["श", "ष", "म"]}],
    "te": [{"say": "ప", "letter": "ప", "distractors": ["వ", "ష", "ఫ"]},
           {"say": "మ", "letter": "మ", "distractors": ["య", "వ", "న"]},
           {"say": "ద", "letter": "ద", "distractors": ["డ", "ధ", "చ"]},
           {"say": "ల", "letter": "ల", "distractors": ["ళ", "త", "న"]},
           {"say": "క", "letter": "క", "distractors": ["ఖ", "గ", "ర"]},
           {"say": "బ", "letter": "బ", "distractors": ["భ", "చ", "జ"]},
           {"say": "స", "letter": "స", "distractors": ["శ", "ష", "మ"]},
           {"say": "ట", "letter": "ట", "distractors": ["ఠ", "త", "డ"]}],
}

for lang in ("en", "hi", "te"):
    if lang not in c:
        continue
    for k, v in UI[lang].items():
        c[lang]["ui"].setdefault(k, v)
    c[lang].setdefault("letters", LETTERS[lang])

json.dump(c, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("Upgraded static/content.json (new games, owl guide, praise words)")
