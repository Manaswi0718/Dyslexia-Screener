// All game content, per language.
// IMPORTANT: have a native Hindi / Telugu speaker check every item before the demo.
// Each mirror round: target + look-alike distractors. Each realword list: real words + made-up words.

const CONTENT = {
  en: {
    name: "English",
    ui: {
      title: "Word Wizards", subtitle: "A few quick games. Just do your best!",
      age: "Child's age", start: "Start", next: "Next", done: "Great job!",
      find: "Tap every", timeLeft: "Time",
      realTitle: "Real or Alien?", realInstr: "Is this a real word, or an alien word?",
      real: "Real", alien: "Alien",
      mirrorTitle: "Mirror Hunt", mirrorInstr: "Tap every one you see, as fast as you can!",
    },
    mirror: [
      { target: "b", distractors: ["d", "p", "q"] },
      { target: "d", distractors: ["b", "q", "p"] },
      { target: "q", distractors: ["p", "b", "d"] },
      { target: "was", distractors: ["saw", "sow", "wos"] },
    ],
    realword: {
      real:  ["cat", "ship", "bread", "green", "train", "plant", "frog", "cloud", "stamp", "brick"],
      alien: ["frop", "slint", "drob", "plim", "grute", "tesk", "zub", "nalp", "crev", "vosk"],
    },
  },

  hi: {
    name: "हिन्दी",
    ui: {
      title: "शब्द जादूगर", subtitle: "कुछ छोटे खेल। बस अपना पूरा प्रयास करो!",
      age: "बच्चे की उम्र", start: "शुरू करें", next: "आगे", done: "शाबाश!",
      find: "हर एक पर टैप करो:", timeLeft: "समय",
      realTitle: "असली या एलियन?", realInstr: "क्या यह असली शब्द है या एलियन शब्द?",
      real: "असली", alien: "एलियन",
      mirrorTitle: "आईना खोज", mirrorInstr: "जितने भी दिखें, सब पर जल्दी से टैप करो!",
    },
    mirror: [
      { target: "ब", distractors: ["व", "क", "र"] },
      { target: "घ", distractors: ["ध", "छ", "प"] },
      { target: "म", distractors: ["भ", "य", "स"] },
      { target: "कि", distractors: ["की", "कु", "के"] },   // vowel-mark (matra) round
    ],
    realword: {
      real:  ["घर", "पानी", "किताब", "कलम", "बादल", "मछली", "सड़क", "फूल", "बिल्ली", "खिड़की"],
      alien: ["पामल", "कितार", "बलाद", "मछड़ी", "फूप", "सड़ाक", "घराम", "तिलप", "नोबा", "लकम"],
    },
  },

  te: {
    name: "తెలుగు",
    ui: {
      title: "పద మాంత్రికులు", subtitle: "కొన్ని చిన్న ఆటలు. నీ వంతు ప్రయత్నం చెయ్యి!",
      age: "పిల్లల వయస్సు", start: "ప్రారంభించండి", next: "తర్వాత", done: "భలే!",
      find: "ప్రతి దాన్నీ నొక్కండి:", timeLeft: "సమయం",
      realTitle: "నిజమా ఏలియనా?", realInstr: "ఇది నిజమైన పదమా లేక ఏలియన్ పదమా?",
      real: "నిజం", alien: "ఏలియన్",
      mirrorTitle: "అద్దం వేట", mirrorInstr: "కనిపించిన ప్రతి దాన్నీ త్వరగా నొక్కండి!",
    },
    mirror: [
      { target: "ప", distractors: ["వ", "ష", "ఫ"] },
      { target: "మ", distractors: ["య", "వ", "ను"] },
      { target: "ద", distractors: ["డ", "ధ", "చ"] },
      { target: "కి", distractors: ["కీ", "కు", "కె"] },   // vowel-mark (gunintham) round
    ],
    realword: {
      real:  ["ఇల్లు", "నీరు", "పుస్తకం", "పువ్వు", "చెట్టు", "ఆవు", "అమ్మ", "బడి", "కలం", "పాలు"],
      alien: ["తవురు", "పిలంగు", "గోమెం", "బెడుపు", "నాసుకం", "రిపాలు", "కుమేటు", "సోవిలు", "దెమ్మం", "లుపాట"],
    },
  },
};
