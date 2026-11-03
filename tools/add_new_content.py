"""
Adds content for the two new games (Spell Builder, Echo Memory) and their UI text
to static/content.json WITHOUT touching anything you already edited.

Run once:  python tools/add_new_content.py     then:  python tools/gen_audio.py
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "static" / "content.json"
c = json.load(open(P, encoding="utf-8"))

NEW = {
    "en": {
        "ui": {"spellTitle": "Spell Builder", "spellInstr": "Listen to the word, then tap the letters in the right order.",
               "memTitle": "Echo Memory", "memInstr": "Watch and listen. Then tap the animals in the same order!",
               "watch": "Watch…", "yourTurn": "Your turn!", "mute": "Sound"},
        # each word split into units the child taps; "trap" = one look-alike extra tile
        "spell": [{"word": "cat", "units": ["c", "a", "t"], "trap": "k"},
                  {"word": "fish", "units": ["f", "i", "sh"], "trap": "ch"},
                  {"word": "frog", "units": ["f", "r", "o", "g"], "trap": "q"},
                  {"word": "sun", "units": ["s", "u", "n"], "trap": "m"},
                  {"word": "bed", "units": ["b", "e", "d"], "trap": "p"},
                  {"word": "duck", "units": ["d", "u", "ck"], "trap": "b"}],
    },
    "hi": {
        "ui": {"spellTitle": "शब्द बनाओ", "spellInstr": "शब्द सुनो, फिर अक्षरों को सही क्रम में टैप करो।",
               "memTitle": "याद रखो", "memInstr": "देखो और सुनो। फिर जानवरों को उसी क्रम में टैप करो!",
               "watch": "देखो…", "yourTurn": "अब तुम्हारी बारी!", "mute": "आवाज़"},
        "spell": [{"word": "घर", "units": ["घ", "र"], "trap": "ध"},
                  {"word": "पानी", "units": ["पा", "नी"], "trap": "नि"},
                  {"word": "कलम", "units": ["क", "ल", "म"], "trap": "भ"},
                  {"word": "मछली", "units": ["म", "छ", "ली"], "trap": "लि"},
                  {"word": "किताब", "units": ["कि", "ता", "ब"], "trap": "व"},
                  {"word": "बादल", "units": ["बा", "द", "ल"], "trap": "वा"}],
    },
    "te": {
        "ui": {"spellTitle": "పదం కట్టు", "spellInstr": "పదం విని, అక్షరాలను సరైన క్రమంలో నొక్కు.",
               "memTitle": "గుర్తుంచుకో", "memInstr": "చూడు, విను. తర్వాత జంతువులను అదే క్రమంలో నొక్కు!",
               "watch": "చూడు…", "yourTurn": "ఇప్పుడు నీ వంతు!", "mute": "శబ్దం"},
        "spell": [{"word": "పాలు", "units": ["పా", "లు"], "trap": "వా"},
                  {"word": "కలం", "units": ["క", "లం"], "trap": "కీ"},
                  {"word": "చెట్టు", "units": ["చె", "ట్టు"], "trap": "చే"},
                  {"word": "పువ్వు", "units": ["పు", "వ్వు"], "trap": "వు"},
                  {"word": "ఇల్లు", "units": ["ఇ", "ల్లు"], "trap": "ఈ"},
                  {"word": "అమ్మ", "units": ["అ", "మ్మ"], "trap": "య్య"}],
    },
}

for lang, add in NEW.items():
    if lang not in c:
        continue
    for k, v in add["ui"].items():
        c[lang]["ui"].setdefault(k, v)          # never overwrite your edits
    c[lang].setdefault("spell", add["spell"])

json.dump(c, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("Added Spell Builder + Echo Memory content to static/content.json")
