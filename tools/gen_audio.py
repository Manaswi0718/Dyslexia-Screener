"""
Pre-generate spoken audio for every word AND every instruction the games use (English, Hindi, Telugu).
Instructions are read aloud because many children being screened cannot read them yet.
Needs internet once. After that the app works offline.

Run:  python tools/gen_audio.py
Creates: static/audio/<lang>/<id>.mp3  and  static/audio/manifest.json
"""
import hashlib, json, re, time
from pathlib import Path

from gtts import gTTS

ROOT = Path(__file__).resolve().parent.parent
content = json.load(open(ROOT / "static" / "content.json", encoding="utf-8"))
out_root = ROOT / "static" / "audio"
SPOKEN_UI = ("Instr", "owlHello", "owlNext", "owlDone")
EMOJI = re.compile(r"[\U0001F000-\U0001FAFF☀-➿️]")
manifest = {}


def texts(c):
    words = set()
    words |= {w for r in c.get("rhyme", []) for w in (r["a"], r["b"])}
    words |= {n["word"] for n in c.get("naming", [])}
    words |= {s["word"] for s in c.get("spell", [])}
    words |= {l["say"] for l in c.get("letters", [])}
    words |= {v for k, v in c.get("ui", {}).items() if isinstance(v, str) and k.endswith(SPOKEN_UI)}
    return words


for lang, c in content.items():
    if lang.startswith("_"):
        continue
    items = texts(c)
    (out_root / lang).mkdir(parents=True, exist_ok=True)
    manifest[lang] = {}
    for w in sorted(items):
        fid = hashlib.md5(w.encode("utf-8")).hexdigest()[:10]
        path = out_root / lang / f"{fid}.mp3"
        spoken = EMOJI.sub("", w).strip()
        if not (path.exists() and path.stat().st_size > 0):
            for attempt in range(3):
                try:
                    gTTS(spoken, lang=c.get("tts", lang), slow=len(spoken) < 15).save(str(path))
                    break
                except Exception as e:
                    path.unlink(missing_ok=True)
                    print(f"  retry {spoken[:30]}: {e}"); time.sleep(2)
        if path.exists() and path.stat().st_size > 0:
            manifest[lang][w] = f"/static/audio/{lang}/{fid}.mp3"
        else:
            print(f"  FAILED: {spoken[:40]} (the app will use the browser voice for this one)")
    print(f"{lang}: {len(items)} clips")

json.dump(manifest, open(out_root / "manifest.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("Saved static/audio/manifest.json")
