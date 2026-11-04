"""
Pre-generate spoken audio for every word AND every instruction the games use.
Uses natural-sounding NEURAL Indian voices (Microsoft Edge TTS):
    English en-IN-NeerjaNeural · Hindi hi-IN-SwaraNeural · Telugu te-IN-ShrutiNeural · Tamil ta-IN-PallaviNeural · Kannada kn-IN-SapnaNeural
Falls back to gTTS if a neural voice fails. Needs internet once; then the app works offline.

Run:            python tools/gen_audio.py
Try a voice:    python tools/gen_audio.py --voice te=te-IN-MohanNeural      (male Telugu voice)
Creates: static/audio/<lang>/<id>.mp3  and  static/audio/manifest.json
"""
import asyncio, hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
content = json.load(open(ROOT / "static" / "content.json", encoding="utf-8"))
out_root = ROOT / "static" / "audio"

VOICES = {"en": "en-IN-NeerjaNeural", "hi": "hi-IN-SwaraNeural", "te": "te-IN-ShrutiNeural",
          "ta": "ta-IN-PallaviNeural", "kn": "kn-IN-SapnaNeural"}
for i, a in enumerate(sys.argv):
    if a == "--voice" and i + 1 < len(sys.argv):
        k, v = sys.argv[i + 1].split("=", 1); VOICES[k] = v

SPOKEN_UI = ("Instr", "owlHello", "owlNext", "owlDone", "owlNextList", "owlSetup")
EMOJI = re.compile(r"[\U0001F000-\U0001FAFF☀-➿️]")


def texts(c):
    t = set()
    t |= {w for r in c.get("rhyme", []) for w in (r["a"], r["b"])}
    t |= {n["word"] for n in c.get("naming", [])}
    t |= {s["word"] for s in c.get("spell", [])}
    t |= {l["say"] for l in c.get("letters", [])}
    for k, v in c.get("ui", {}).items():
        if k.endswith(SPOKEN_UI):
            t |= set(v) if isinstance(v, list) else {v}
    return {x for x in t if isinstance(x, str) and x.strip()}


async def neural(text, voice, path, short):
    import edge_tts
    # words: slower and clearer; sentences: almost natural speed
    rate = "-25%" if short else "-8%"
    await edge_tts.Communicate(text, voice, rate=rate, pitch="+2Hz").save(str(path))


def fallback(text, lang, path, short):
    from gtts import gTTS
    gTTS(text, lang=lang, slow=short).save(str(path))


async def main():
    manifest = {}
    try:
        old = json.load(open(out_root / "manifest.json", encoding="utf-8"))
    except Exception:
        old = {}
    for lang, c in content.items():
        if lang.startswith("_"):
            continue
        voice = VOICES.get(lang)
        (out_root / lang).mkdir(parents=True, exist_ok=True)
        manifest[lang], used, ok, fb = {}, set(), 0, 0
        for w in sorted(texts(c)):
            spoken = EMOJI.sub("", w).strip()
            short = len(spoken) < 15
            fid = hashlib.md5(f"{voice}|{w}".encode("utf-8")).hexdigest()[:12]   # new voice -> new file
            path = out_root / lang / f"{fid}.mp3"
            if not (path.exists() and path.stat().st_size > 0):
                try:
                    await neural(spoken, voice, path, short); ok += 1
                except Exception as e:
                    path.unlink(missing_ok=True)
                    try:
                        fallback(spoken, c.get("tts", lang), path, short); fb += 1
                        print(f"  (gTTS fallback) {spoken[:30]}: {str(e)[:60]}")
                    except Exception as e2:
                        path.unlink(missing_ok=True); print(f"  FAILED: {spoken[:40]} ({e2})")
            if path.exists() and path.stat().st_size > 0:
                manifest[lang][w] = f"/static/audio/{lang}/{fid}.mp3"; used.add(path.name)
            elif w in old.get(lang, {}) and (ROOT / old[lang][w].lstrip("/")).exists():
                manifest[lang][w] = old[lang][w]; used.add(Path(old[lang][w]).name)   # keep the previous clip
        removed = 0
        for f in (out_root / lang).glob("*.mp3"):        # delete clips from the old voice
            if f.name not in used:
                f.unlink(); removed += 1
        print(f"{lang}: {len(manifest[lang])} clips · voice {voice} · new {ok} · fallback {fb} · old removed {removed}")
    json.dump(manifest, open(out_root / "manifest.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Saved static/audio/manifest.json")


asyncio.run(main())
