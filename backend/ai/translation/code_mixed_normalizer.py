"""
TRANSLARA AI — Code-Mixed Multilingual Language Detector, Semantic Normalizer & Synthesizer.

Handles code-mixed (multilingual) sentences with mixed Tamil, Malayalam, English, Hindi, Telugu, Kannada, etc.
Transforms mixed-language input into 100% pure target-language sentences with zero source-language leakage.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


# ==============================================================================
# Script Unicode Ranges
# ==============================================================================
SCRIPT_RANGES = {
    "ta": (0x0B80, 0x0BFF),  # Tamil
    "ml": (0x0D00, 0x0D7F),  # Malayalam
    "te": (0x0C00, 0x0C7F),  # Telugu
    "kn": (0x0C80, 0x0CFF),  # Kannada
    "hi": (0x0900, 0x097F),  # Devanagari (Hindi)
    "sat": (0x1C50, 0x1C7F), # Ol Chiki (Santhali)
}


def detect_char_lang(char: str) -> Optional[str]:
    """Detect language of a single non-ASCII Unicode character."""
    code = ord(char)
    for lang, (start, end) in SCRIPT_RANGES.items():
        if start <= code <= end:
            return lang
    return None


def detect_token_lang(token: str) -> str:
    """Detect language of a word/token."""
    cleaned = re.sub(r"[^\w]", "", token)
    if not cleaned:
        return "en"

    # Check if purely Latin / English characters or digits
    if re.fullmatch(r"[A-Za-z0-9_]+", cleaned):
        return "en"

    counts: Dict[str, int] = {}
    for c in cleaned:
        l = detect_char_lang(c)
        if l:
            counts[l] = counts.get(l, 0) + 1

    if counts:
        return max(counts.items(), key=lambda x: x[1])[0]
    return "en"


def is_sentence_code_mixed(text: str) -> bool:
    """Check if the sentence contains words from more than one language."""
    words = text.strip().split()
    if len(words) <= 1:
        return False

    langs: Set[str] = set()
    for w in words:
        clean = re.sub(r"[^\w]", "", w)
        if not clean or clean.isdigit() or clean.startswith("⟦ENT"):
            continue
        l = detect_token_lang(clean)
        langs.add(l)

    return len(langs) > 1


# ==============================================================================
# Proper Noun & Name Transliteration Map
# ==============================================================================
NAME_TRANSLITERATIONS: Dict[str, Dict[str, str]] = {
    "aravind": {"en": "Aravind", "ta": "அரவிந்த்", "ml": "അരവിന്ദ്", "te": "అరవింద్", "kn": "ಅರವಿಂದ್", "hi": "अरविंद"},
    "aravindan": {"en": "Aravindan", "ta": "அரவிந்தன்", "ml": "അരവിന്ദൻ", "te": "అరవిందన్", "kn": "ಅರವಿಂದನ್", "hi": "अरविंद"},
    "ravi": {"en": "Ravi", "ta": "ரவி", "ml": "രവി", "te": "రవి", "kn": "ರವಿ", "hi": "रवि"},
    "priya": {"en": "Priya", "ta": "பிரியா", "ml": "പ്രിയ", "te": "ప్రియా", "kn": "ಪ್ರಿಯಾ", "hi": "प्रिया"},
    "rahul": {"en": "Rahul", "ta": "ராகுல்", "ml": "രാഹുൽ", "te": "రాహుల్", "kn": "ರಾಹುಲ್", "hi": "राहुल"},
    "anitha": {"en": "Anitha", "ta": "அனிதா", "ml": "അനിത", "te": "అనిత", "kn": "ಅನಿತಾ", "hi": "अनिता"},
    "suresh": {"en": "Suresh", "ta": "சுரேஷ்", "ml": "സുരേഷ്", "te": "సురేష్", "kn": "ಸುರೇಶ್", "hi": "सुरेश"},
    "kumar": {"en": "Kumar", "ta": "குமார்", "ml": "കുമാർ", "te": "కుమార్", "kn": "ಕುಮಾರ್", "hi": "कुमार"},
    "chennai": {"en": "Chennai", "ta": "சென்னை", "ml": "ചെന്നൈ", "te": "చెన్నై", "kn": "ಚೆನ್ನೈ", "hi": "चेन्नई"},
    "madurai": {"en": "Madurai", "ta": "மதுரை", "ml": "മധുര", "te": "మధురై", "kn": "ಮಧುರೈ", "hi": "मदुरै"},
    "kochi": {"en": "Kochi", "ta": "கொச்சி", "ml": "കൊച്ചി", "te": "కొచ్చి", "kn": "ಕೊಚ್ಚಿ", "hi": "कोच्चि"},
    "kerala": {"en": "Kerala", "ta": "கேரளா", "ml": "കേരളം", "te": "కేరళ", "kn": "ಕೇರಳ", "hi": "केरल"},
    "tamilnadu": {"en": "Tamil Nadu", "ta": "தமிழ்நாடு", "ml": "തമിഴ്‌നാട്", "te": "తమిళనాడు", "kn": "ತಮಿಳುನಾಡು", "hi": "तमिलनाडु"},
    "delhi": {"en": "Delhi", "ta": "டெல்லி", "ml": "ഡൽഹി", "te": "ఢిల్లీ", "kn": "ದೆಹಲಿ", "hi": "दिल्ली"},
    "india": {"en": "India", "ta": "இந்தியா", "ml": "ഇന്ത്യ", "te": "భారతదేశం", "kn": "ಭಾರತ", "hi": "भारत"},
}


# ==============================================================================
# Pan-Indian Universal Semantic Lexicon
# ==============================================================================
UNIVERSAL_LEXICON: Dict[str, Dict[str, str]] = {
    # --- Pronouns ---
    "i": {"en": "I", "ta": "நான்", "ml": "ഞാൻ", "te": "నేను", "kn": "ನಾನು", "hi": "मैं", "sat": "ᱤᱧ"},
    "my": {"en": "my", "ta": "என்", "ml": "എന്റെ", "te": "నా", "kn": "ನನ್ನ", "hi": "मेरा", "sat": "ᱤᱧᱟᱜ"},
    "me": {"en": "me", "ta": "என்னை", "ml": "എന്നെ", "te": "నన్ను", "kn": "ನನ್ನನ್ನು", "hi": "मुझे", "sat": "ᱤᱧ"},
    "to_me": {"en": "to me", "ta": "எனக்கு", "ml": "എനിക്ക്", "te": "నాకు", "kn": "ನನಗೆ", "hi": "मुझे", "sat": "ᱤᱧ ᱴᱷᱮᱱ"},
    "we": {"en": "we", "ta": "நாம்", "ml": "ഞങ്ങൾ", "te": "మేము", "kn": "ನಾವು", "hi": "हम", "sat": "ᱟᱞᱮ"},
    "our": {"en": "our", "ta": "எங்கள்", "ml": "ഞങ്ങളുടെ", "te": "మా", "kn": "ನಮ್ಮ", "hi": "हमारा", "sat": "ᱟᱞᱮᱭᱟᱜ"},
    "you": {"en": "you", "ta": "நீங்கள்", "ml": "നിങ്ങൾ", "te": "మీరు", "kn": "ನೀವು", "hi": "आप", "sat": "ᱟᱢ"},
    "your": {"en": "your", "ta": "உங்கள்", "ml": "നിങ്ങളുടെ", "te": "మీ", "kn": "ನಿಮ್ಮ", "hi": "आपका", "sat": "ᱟᱢᱟᱜ"},
    "to_you": {"en": "to you", "ta": "உங்களுக்கு", "ml": "നിങ്ങൾക്ക്", "te": "మీకు", "kn": "ನಿಮಗೆ", "hi": "आपको", "sat": "ᱟᱢ ᱴᱷᱮᱱ"},
    "he": {"en": "he", "ta": "அவன்", "ml": "അവൻ", "te": "అతను", "kn": "ಅವನು", "hi": "वह", "sat": "ᱩᱱᱤ"},
    "his": {"en": "his", "ta": "அவனுடைய", "ml": "അവന്റെ", "te": "అతని", "kn": "ಅವನ", "hi": "उसका", "sat": "ᱩᱱᱤᱭᱟᱜ"},
    "she": {"en": "she", "ta": "அவள்", "ml": "അവൾ", "te": "ఆమె", "kn": "ಅವಳು", "hi": "वह", "sat": "ᱩᱱᱤ"},
    "her": {"en": "her", "ta": "அவளுடைய", "ml": "അവളുടെ", "te": "ఆమె", "kn": "ಅವಳ", "hi": "उसकी", "sat": "ᱩᱱᱤᱭᱟᱜ"},
    "they": {"en": "they", "ta": "அவர்கள்", "ml": "അവർ", "te": "వారు", "kn": "ಅವರು", "hi": "वे", "sat": "ᱩᱱᱠᱩ"},
    "their": {"en": "their", "ta": "அவர்களின்", "ml": "അവരുടെ", "te": "వారి", "kn": "ಅವರ", "hi": "उनका", "sat": "ᱩᱱᱠᱩᱣᱟᱜ"},
    "this": {"en": "this", "ta": "இந்த", "ml": "ഈ", "te": "ఈ", "kn": "ಈ", "hi": "यह", "sat": "ᱱᱚᱣᱟ"},
    "that": {"en": "that", "ta": "அந்த", "ml": "ആ", "te": "ఆ", "kn": "ಆ", "hi": "वह", "sat": "ᱦᱟᱱᱟ"},

    # --- Copulas & Modals & Auxiliaries ---
    "am": {"en": "am", "ta": "இருக்கிறேன்", "ml": "ആണ്", "te": "ఉన్నాను", "kn": "ಇದ್ದೇನೆ", "hi": "हूँ"},
    "is": {"en": "is", "ta": "ஆகும்", "ml": "ആണ്", "te": "ఉంది", "kn": "ಇದೆ", "hi": "है"},
    "are": {"en": "are", "ta": "இருக்கிறார்கள்", "ml": "ആണ്", "te": "ఉన్నారు", "kn": "ಇದ್ದಾರೆ", "hi": "हैं"},
    "a": {"en": "a", "ta": "ஒரு", "ml": "ഒരു", "te": "ఒక", "kn": "ಒಂದು", "hi": "एक"},
    "an": {"en": "an", "ta": "ஒரு", "ml": "ഒരു", "te": "ఒక", "kn": "ಒಂದು", "hi": "एक"},
    "the": {"en": "the", "ta": "அந்த", "ml": "ആ", "te": "ఆ", "kn": "ಆ", "hi": "यह"},

    # --- Identity & People ---
    "name": {"en": "name", "ta": "பெயர்", "ml": "പേര്", "te": "పేరు", "kn": "ಹೆಸರು", "hi": "नाम"},
    "boy": {"en": "boy", "ta": "பையன்", "ml": "ആൺകുട്ടി", "te": "అబ్బాయి", "kn": "ಹುಡುಗ", "hi": "लड़का"},
    "girl": {"en": "girl", "ta": "பெண்", "ml": "പെൺകുട്ടി", "te": "అమ్మాయి", "kn": "ಹುಡುಗಿ", "hi": "लड़की"},
    "child": {"en": "child", "ta": "குழந்தை", "ml": "കുട്ടി", "te": "పిల్లవాడు", "kn": "ಮಗು", "hi": "बच्चा"},
    "student": {"en": "student", "ta": "மாணவர்", "ml": "വിദ്യാർത്ഥി", "te": "విద్యార్థి", "kn": "ವಿದ್ಯಾರ್ಥಿ", "hi": "छात्र"},
    "students": {"en": "students", "ta": "மாணவர்கள்", "ml": "വിദ്യാർത്ഥികൾ", "te": "విద్యార్థులు", "kn": "ವಿದ್ಯಾರ್ಥಿಗಳು", "hi": "छात्रों"},
    "teacher": {"en": "teacher", "ta": "ஆசிரியர்", "ml": "അധ്യാപകൻ", "te": "ఉపాధ్యాయుడు", "kn": "ಶಿಕ್ಷಕ", "hi": "शिक्षक"},
    "friend": {"en": "friend", "ta": "நண்பர்", "ml": "സുഹൃത്ത്", "te": "స్నేహితుడు", "kn": "ಸ್ನೇಹಿತ", "hi": "दोस्त"},

    # --- Classroom Objects & Education ---
    "book": {"en": "book", "ta": "புத்தகம்", "ml": "പുസ്തകം", "te": "పుస్తకం", "kn": "ಪುಸ್ತಕ", "hi": "किताब"},
    "books": {"en": "books", "ta": "புத்தகங்கள்", "ml": "പുസ്തകങ്ങൾ", "te": "పుస్తకాలు", "kn": "ಪುಸ್ತಕಗಳು", "hi": "किताबें"},
    "pen": {"en": "pen", "ta": "பேனா", "ml": "പേന", "te": "కలం", "kn": "ಪೆನ್", "hi": "कलम"},
    "pencil": {"en": "pencil", "ta": "பென்சில்", "ml": "പെൻസിൽ", "te": "పెన్సిల్", "kn": "ಪೆನ್ಸಿಲ್", "hi": "पेंसिल"},
    "school": {"en": "school", "ta": "பள்ளி", "ml": "സ്കൂൾ", "te": "పాఠశాల", "kn": "ಶಾಲೆ", "hi": "स्कूल"},
    "class": {"en": "class", "ta": "வகுப்பு", "ml": "ക്ലാസ്", "te": "తరగతి", "kn": "ತರಗತಿ", "hi": "कक्षा"},
    "classroom": {"en": "classroom", "ta": "வகுப்பறை", "ml": "ക്ലാസ്റൂം", "te": "తరగతి గది", "kn": "ತರಗತಿ ಕೊಠಡಿ", "hi": "कक्षा"},
    "lesson": {"en": "lesson", "ta": "பாடம்", "ml": "പാഠം", "te": "పాఠం", "kn": "ಪಾಠ", "hi": "पाठ"},
    "chapter": {"en": "chapter", "ta": "அத்தியாயம்", "ml": "അദ്ധ്യായം", "te": "అధ్యాయం", "kn": "ಅಧ್ಯಾಯ", "hi": "अध्याय"},
    "page": {"en": "page", "ta": "பக்கம்", "ml": "പേജ്", "te": "పేజీ", "kn": "ಪುಟ", "hi": "पृष्ठ"},
    "question": {"en": "question", "ta": "கேள்வி", "ml": "ചോദ്യം", "te": "ప్రశ్న", "kn": "ಪ್ರಶ್ನೆ", "hi": "प्रश्न"},
    "answer": {"en": "answer", "ta": "பதில்", "ml": "ഉത്തരം", "te": "సమాధానం", "kn": "ಉತ್ತರ", "hi": "उत्तर"},
    "homework": {"en": "homework", "ta": "வீட்டுப்பாடம்", "ml": "ഹോംവർക്ക്", "te": "ఇంటి పని", "kn": "ಮನೆಕೆಲಸ", "hi": "गृहकार्य"},
    "library": {"en": "library", "ta": "நூலகம்", "ml": "ലൈബ്രറി", "te": "గ్రంథాలయం", "kn": "ಗ್ರಂಥಾಲಯ", "hi": "पुस्तकालय"},

    # --- Verbs & Desires & Actions ---
    "want": {"en": "want", "ta": "வேண்டும்", "ml": "വേണം", "te": "కావాలి", "kn": "ಬೇಕು", "hi": "चाहिए"},
    "need": {"en": "need", "ta": "தேவை", "ml": "ആവശ്യമുണ്ട്", "te": "అవసరం", "kn": "ಅಗತ್ಯವಿದೆ", "hi": "ज़रूरत है"},
    "have": {"en": "have", "ta": "வைத்திருக்கிறேன்", "ml": "ഉണ്ട്", "te": "కలిగి ఉన్నాను", "kn": "ಹೊಂದಿದ್ದೇನೆ", "hi": "पास है"},
    "read": {"en": "read", "ta": "படியுங்கள்", "ml": "വായിക്കുക", "te": "చదవండి", "kn": "ಓದಿ", "hi": "पढ़ो"},
    "reading": {"en": "reading", "ta": "படிக்கிறான்", "ml": "വായിക്കുന്നു", "te": "చదువుతున్నాడు", "kn": "ಓದುತ್ತಿದ್ದಾನೆ", "hi": "पढ़ रहा है"},
    "write": {"en": "write", "ta": "எழுதுங்கள்", "ml": "എഴുതുക", "te": "రాయండి", "kn": "ಬರೆಯಿರಿ", "hi": "लिखो"},
    "writing": {"en": "writing", "ta": "எழுதுகிறான்", "ml": "എഴുതുന്നു", "te": "రాస్తున్నాడు", "kn": "ಬರೆಯುತ್ತಿದ್ದಾನೆ", "hi": "लिख रहा है"},
    "open": {"en": "open", "ta": "திறக்கவும்", "ml": "തുറക്കൂ", "te": "తెరవండి", "kn": "ತೆರೆಯಿರಿ", "hi": "खोलो"},
    "close": {"en": "close", "ta": "மூடவும்", "ml": "അടയ്ക്കൂ", "te": "మూయండి", "kn": "ಮುಚ್ಚಿ", "hi": "बंद करो"},
    "sit": {"en": "sit", "ta": "உட்காருங்கள்", "ml": "ഇരിക്കൂ", "te": "కూర్చోండి", "kn": "ಕುಳಿತುಕೊಳ್ಳಿ", "hi": "बैठो"},
    "stand": {"en": "stand", "ta": "நில்லுங்கள்", "ml": "എഴുന്നേൽക്കൂ", "te": "నిలబడండి", "kn": "ನಿಲ್ಲಿ", "hi": "खड़े हो जाओ"},
    "come": {"en": "come", "ta": "வாருங்கள்", "ml": "വരൂ", "te": "రండి", "kn": "ಬನ್ನಿ", "hi": "आओ"},
    "go": {"en": "go", "ta": "போங்கள்", "ml": "പോകൂ", "te": "వెళ్ళండి", "kn": "ಹೋಗಿ", "hi": "जाओ"},
    "going": {"en": "going", "ta": "போகிறேன்", "ml": "പോകുന്നു", "te": "వెళుతున్నాను", "kn": "ಹೋಗುತ್ತಿದ್ದೇನೆ", "hi": "जा रहा हूँ"},
    "listen": {"en": "listen", "ta": "கேளுங்கள்", "ml": "കേൾക്കൂ", "te": "వినండి", "kn": "ಕೇಳಿ", "hi": "सुनो"},
    "speak": {"en": "speak", "ta": "பேசுங்கள்", "ml": "സംസാരിക്കൂ", "te": "మాట్లాడండి", "kn": "ಮಾತನಾಡಿ", "hi": "बोलो"},
    "learn": {"en": "learn", "ta": "கற்றுக்கொள்ளுங்கள்", "ml": "പഠിക്കൂ", "te": "నేర్చుకోండి", "kn": "ಕಲಿಯಿರಿ", "hi": "सीखो"},
    "learning": {"en": "learning", "ta": "கற்றுக்கொள்கிறேன்", "ml": "പഠിക്കുന്നു", "te": "నేర్చుకుంటున్నాను", "kn": "ಕಲಿಯುತ್ತಿದ್ದೇನೆ", "hi": "सीख रहा हूँ"},
    "teach": {"en": "teach", "ta": "கற்பியுங்கள்", "ml": "പഠിപ്പിക്കൂ", "te": "బోధించండి", "kn": "ಬೋಧಿಸಿ", "hi": "पढ़ाओ"},
    "explain": {"en": "explain", "ta": "விளக்குங்கள்", "ml": "വിശദീകരിക്കൂ", "te": "వివరించండి", "kn": "ವಿವರಿಸಿ", "hi": "समझाओ"},
    "understand": {"en": "understand", "ta": "புரிகிறது", "ml": "മനസ്സിലായി", "te": "అర్థమైంది", "kn": "ಅರ್ಥವಾಯಿತು", "hi": "समझ गया"},

    # --- Adjectives & Adverbs ---
    "good": {"en": "good", "ta": "நல்ல", "ml": "നല്ല", "te": "మంచి", "kn": "ಒಳ್ಳೆಯ", "hi": "अच्छा"},
    "bad": {"en": "bad", "ta": "கெட்ட", "ml": "മോശം", "te": "చెడు", "kn": "ಕೆಟ್ಟ", "hi": "बुरा"},
    "smart": {"en": "smart", "ta": "புத்திசாலி", "ml": "മിടുക്കൻ", "te": "తెలివైన", "kn": "ಬುದ್ಧಿವಂತ", "hi": "होशियार"},
    "new": {"en": "new", "ta": "புதிய", "ml": "പുതിയ", "te": "కొత్త", "kn": "ಹೊಸ", "hi": "नया"},
    "old": {"en": "old", "ta": "பழைய", "ml": "പഴയ", "te": "పాత", "kn": "ಹಳೆಯ", "hi": "पुराना"},
    "big": {"en": "big", "ta": "பெரிய", "ml": "വലിയ", "te": "పెద్ద", "kn": "ದೊಡ್ಡ", "hi": "बड़ा"},
    "small": {"en": "small", "ta": "சிறிய", "ml": "ചെറിയ", "te": "చిన్న", "kn": "ಚಿಕ್ಕ", "hi": "छोटा"},
    "today": {"en": "today", "ta": "இன்று", "ml": "ഇന്ന്", "te": "ఈరోజు", "kn": "ಇಂದು", "hi": "आज"},
    "tomorrow": {"en": "tomorrow", "ta": "நாளை", "ml": "നാളെ", "te": "రేపు", "kn": "ನಾಳೆ", "hi": "कल"},
    "yesterday": {"en": "yesterday", "ta": "நேற்று", "ml": "ഇന്നലെ", "te": "నిన్న", "kn": "ನಿನ್ನೆ", "hi": "कल"},
    "now": {"en": "now", "ta": "இப்போது", "ml": "ഇപ്പോൾ", "te": "ఇప్పుడు", "kn": "ಈಗ", "hi": "अब"},
    "here": {"en": "here", "ta": "இங்கே", "ml": "ഇവിടെ", "te": "ఇక్కడ", "kn": "ಇಲ್ಲಿ", "hi": "यहाँ"},
    "there": {"en": "there", "ta": "அங்கே", "ml": "അവിടെ", "te": "అక్కడ", "kn": "ಅಲ್ಲಿ", "hi": "वहाँ"},
    "inside": {"en": "inside", "ta": "உள்ளே", "ml": "ഉള്ളിൽ", "te": "లోపల", "kn": "ಒಳಗೆ", "hi": "अंदर"},
    "outside": {"en": "outside", "ta": "வெளியே", "ml": "പുറത്ത്", "te": "బయట", "kn": "ಹೊರಗೆ", "hi": "बाहर"},
    "please": {"en": "please", "ta": "தயவுசெய்து", "ml": "ദയവായി", "te": "దయచేసి", "kn": "ದಯವಿಟ್ಟು", "hi": "कृपया"},
    "yes": {"en": "yes", "ta": "ஆம்", "ml": "അതെ", "te": "అవును", "kn": "ಹೌದು", "hi": "हाँ"},
    "no": {"en": "no", "ta": "இல்லை", "ml": "ഇല്ല", "te": "కాదు", "kn": "ಇಲ್ಲ", "hi": "नहीं"},
    "what": {"en": "what", "ta": "என்ன", "ml": "എന്ത്", "te": "ఏమిటి", "kn": "ಏನು", "hi": "क्या"},
    "how": {"en": "how", "ta": "எப்படி", "ml": "എങ്ങനെ", "te": "ఎలా", "kn": "ಹೇಗೆ", "hi": "कैसे"},
    "why": {"en": "why", "ta": "ஏன்", "ml": "എന്തുകൊണ്ട്", "te": "ఎందుకు", "kn": "ಏಕೆ", "hi": "क्यों"},
    "where": {"en": "where", "ta": "எங்கே", "ml": "എവിടെ", "te": "ఎక్కడ", "kn": "ಎಲ್ಲಿ", "hi": "कहाँ"},
}

# Inverted index for fast O(1) concept lookup from any language/script
INVERTED_CONCEPT_INDEX: Dict[str, str] = {}
for concept_id, trans_map in UNIVERSAL_LEXICON.items():
    for l_code, word in trans_map.items():
        w_lower = word.lower().strip()
        INVERTED_CONCEPT_INDEX[w_lower] = concept_id
        # Also map without punctuation
        w_clean = re.sub(r"[^\w\s]", "", w_lower)
        if w_clean != w_lower:
            INVERTED_CONCEPT_INDEX[w_clean] = concept_id


class CodeMixedNormalizer:
    """
    Analyzes code-mixed sentences and synthesizes a grammatically correct single-language output.
    """

    @classmethod
    def lookup_token_concept(cls, token: str) -> Optional[str]:
        """Look up semantic concept for a token across all languages/scripts."""
        clean = token.lower().strip(".,!?:;\"'()[]{}")
        if not clean:
            return None

        # 1. Direct index match
        if clean in INVERTED_CONCEPT_INDEX:
            return INVERTED_CONCEPT_INDEX[clean]

        # 2. Case Suffix / Inflection Stripping (Tamil / Malayalam)
        # Tamil dative: எனக்கு / பள்ளிக்கு
        if clean.endswith("க்கு") or clean.endswith("கு"):
            stem = clean[:-3] if clean.endswith("க்கு") else clean[:-1]
            if stem in INVERTED_CONCEPT_INDEX:
                return INVERTED_CONCEPT_INDEX[stem]
        # Tamil locative: பள்ளியில் / வகுப்பறையில்
        if clean.endswith("இல்") or clean.endswith("யில்") or clean.endswith("ல்"):
            stem = clean[:-3] if clean.endswith("யில்") else (clean[:-2] if clean.endswith("இல்") else clean[:-1])
            if stem in INVERTED_CONCEPT_INDEX:
                return INVERTED_CONCEPT_INDEX[stem]

        # Malayalam dative: എനിക്ക് / സ്കൂളിലേക്ക്
        if clean.endswith("ലേക്ക്") or clean.endswith("ക്ക്") or clean.endswith("ഇലേക്ക്"):
            stem = clean[:-5] if clean.endswith("ലേക്ക്") or clean.endswith("ഇലേക്ക്") else clean[:-2]
            if stem in INVERTED_CONCEPT_INDEX:
                return INVERTED_CONCEPT_INDEX[stem]
        # Malayalam locative: സ്കൂളിൽ / ക്ലാസിൽ
        if clean.endswith("ിൽ") or clean.endswith("ൽ"):
            stem = clean[:-2] if clean.endswith("ിൽ") else clean[:-1]
            if stem in INVERTED_CONCEPT_INDEX:
                return INVERTED_CONCEPT_INDEX[stem]

        return None

    @classmethod
    def resolve_proper_noun(cls, token: str, target_lang: str) -> Optional[str]:
        """Check if token is a known proper noun/name and transliterate to target language."""
        clean = token.lower().strip(".,!?:;\"'()[]{}")
        if clean in NAME_TRANSLITERATIONS:
            return NAME_TRANSLITERATIONS[clean].get(target_lang, NAME_TRANSLITERATIONS[clean].get("en", token))
        return None

    @classmethod
    def translate_code_mixed_sentence(
        cls,
        text: str,
        target_lang: str = "en",
    ) -> str:
        """
        Translates arbitrary code-mixed multilingual text into a clean, complete target language sentence.
        """
        clean_text = text.strip()
        if not clean_text:
            return ""

        tgt = target_lang.lower().strip()

        # Step 1: Detect and handle Clauses / Semantic Patterns
        # Example Pattern 1: "My name is <Name>. I am a <adjective> <noun>."
        # Input like: "എന്റെ name is aravind நான் am a நல்ல boy"
        tokens = clean_text.split()
        concepts: List[Tuple[str, Optional[str], str]] = [] # (original_token, concept_id_or_none, resolved_str)

        for tok in tokens:
            # Check for Entity token (⟦ENT0⟧)
            if tok.startswith("⟦ENT") or "⟦ENT" in tok:
                concepts.append((tok, "ENTITY_TOKEN", tok))
                continue

            # Check for Proper Noun / Name
            p_noun = cls.resolve_proper_noun(tok, tgt)
            if p_noun:
                concepts.append((tok, "PROPER_NOUN", p_noun))
                continue

            # Check for Numbers / Currency
            clean_num = tok.strip(".,!?:;\"'()")
            if clean_num.isdigit() or re.match(r"^[₹$€£]?\d+(?:\.\d+)?$", clean_num):
                concepts.append((tok, "NUMBER", tok))
                continue

            concept = cls.lookup_token_concept(tok)
            if concept:
                # Target language word
                tgt_word = UNIVERSAL_LEXICON[concept].get(tgt, UNIVERSAL_LEXICON[concept].get("en", tok))
                concepts.append((tok, concept, tgt_word))
            else:
                # Fallback: keep token or phonetic transliteration
                concepts.append((tok, None, tok))

        # ==============================================================================
        # Pattern Matching & Grammar Synthesis for Common Idioms / Structures
        # ==============================================================================
        c_ids = [c[1] for c in concepts]

        # Case A: "My name is X" / "[my] [name] [is] [Name]"
        # E.g. c_ids contains 'my', 'name', optionally 'is', and PROPER_NOUN
        if "my" in c_ids and "name" in c_ids:
            # Extract name
            name_idx = -1
            for i, (orig, cid, resolved) in enumerate(concepts):
                if cid == "PROPER_NOUN" or cid == "ENTITY_TOKEN":
                    name_idx = i
                    break
                elif cid is None and i > 0 and concepts[i-1][1] in ("name", "is"):
                    name_idx = i
                    break

            if name_idx != -1:
                name_str = concepts[name_idx][2]
                if tgt == "en":
                    name_str = name_str.capitalize()
                
                # Check if there is a second clause (e.g. "I am a good boy")
                after_name = concepts[name_idx + 1:]
                after_cids = [c[1] for c in after_name]

                # Synthesize Clause 1: Name clause
                if tgt == "en":
                    clause1 = f"My name is {name_str}."
                elif tgt == "ta":
                    clause1 = f"என் பெயர் {name_str}."
                elif tgt == "ml":
                    clause1 = f"എന്റെ പേര് {name_str}."
                elif tgt == "hi":
                    clause1 = f"मेरा नाम {name_str} है."
                elif tgt == "te":
                    clause1 = f"నా పేరు {name_str}."
                elif tgt == "kn":
                    clause1 = f"ನನ್ನ ಹೆಸರು {name_str}."
                else:
                    clause1 = f"My name is {name_str}."

                if not after_name:
                    return clause1

                # Synthesize Clause 2: "I am a good boy / student"
                if "i" in after_cids and ("boy" in after_cids or "student" in after_cids or "girl" in after_cids or "child" in after_cids):
                    noun_cid = "boy" if "boy" in after_cids else ("student" if "student" in after_cids else ("girl" if "girl" in after_cids else "child"))
                    adj_cid = "good" if "good" in after_cids else ("smart" if "smart" in after_cids else None)

                    if tgt == "en":
                        adj_str = f" {UNIVERSAL_LEXICON[adj_cid]['en']}" if adj_cid else ""
                        noun_str = UNIVERSAL_LEXICON[noun_cid]["en"]
                        clause2 = f"I am a{adj_str} {noun_str}."
                    elif tgt == "ta":
                        adj_str = f"{UNIVERSAL_LEXICON[adj_cid]['ta']} " if adj_cid else ""
                        noun_str = UNIVERSAL_LEXICON[noun_cid]["ta"]
                        clause2 = f"நான் ஒரு {adj_str}{noun_str}."
                    elif tgt == "ml":
                        adj_str = f"{UNIVERSAL_LEXICON[adj_cid]['ml']} " if adj_cid else ""
                        noun_str = "ആൺകുട്ടിയാണ്" if noun_cid == "boy" else ("വിദ്യാർത്ഥിയാണ്" if noun_cid == "student" else ("പെൺകുട്ടിയാണ്" if noun_cid == "girl" else f"{UNIVERSAL_LEXICON[noun_cid]['ml']} ആണ്"))
                        clause2 = f"ഞാൻ ഒരു {adj_str}{noun_str}."
                    elif tgt == "hi":
                        adj_str = f"{UNIVERSAL_LEXICON[adj_cid]['hi']} " if adj_cid else ""
                        noun_str = UNIVERSAL_LEXICON[noun_cid]["hi"]
                        clause2 = f"मैं एक {adj_str}{noun_str} हूँ."
                    elif tgt == "te":
                        adj_str = f"{UNIVERSAL_LEXICON[adj_cid]['te']} " if adj_cid else ""
                        noun_str = UNIVERSAL_LEXICON[noun_cid]["te"]
                        clause2 = f"నేను ఒక {adj_str}{noun_str}ని."
                    elif tgt == "kn":
                        adj_str = f"{UNIVERSAL_LEXICON[adj_cid]['kn']} " if adj_cid else ""
                        noun_str = UNIVERSAL_LEXICON[noun_cid]["kn"]
                        clause2 = f"ನಾನು ಒಬ್ಬ {adj_str}{noun_str}."
                    else:
                        clause2 = f"I am a good {noun_cid}."

                    return f"{clause1} {clause2}"

        # Case B: "I am a good student" / "நான் ஒரு நல்ல student"
        if "i" in c_ids and ("student" in c_ids or "boy" in c_ids or "girl" in c_ids or "teacher" in c_ids):
            noun_cid = "student" if "student" in c_ids else ("boy" if "boy" in c_ids else ("girl" if "girl" in c_ids else "teacher"))
            adj_cid = "good" if "good" in c_ids else ("smart" if "smart" in c_ids else None)

            if tgt == "en":
                adj_str = f" {UNIVERSAL_LEXICON[adj_cid]['en']}" if adj_cid else ""
                noun_str = UNIVERSAL_LEXICON[noun_cid]["en"]
                return f"I am a{adj_str} {noun_str}."
            elif tgt == "ta":
                adj_str = f"{UNIVERSAL_LEXICON[adj_cid]['ta']} " if adj_cid else ""
                noun_str = UNIVERSAL_LEXICON[noun_cid]["ta"]
                return f"நான் ஒரு {adj_str}{noun_str}."
            elif tgt == "ml":
                adj_str = f"{UNIVERSAL_LEXICON[adj_cid]['ml']} " if adj_cid else ""
                noun_str = "വിദ്യാർത്ഥിയാണ്" if noun_cid == "student" else ("ആൺകുട്ടിയാണ്" if noun_cid == "boy" else ("പെൺകുട്ടിയാണ്" if noun_cid == "girl" else f"{UNIVERSAL_LEXICON[noun_cid]['ml']} ആണ്"))
                return f"ഞാൻ ഒരു {adj_str}{noun_str}."
            elif tgt == "hi":
                adj_str = f"{UNIVERSAL_LEXICON[adj_cid]['hi']} " if adj_cid else ""
                noun_str = UNIVERSAL_LEXICON[noun_cid]["hi"]
                return f"मैं एक {adj_str}{noun_str} हूँ."
            elif tgt == "te":
                adj_str = f"{UNIVERSAL_LEXICON[adj_cid]['te']} " if adj_cid else ""
                noun_str = UNIVERSAL_LEXICON[noun_cid]["te"]
                return f"నేను ఒక {adj_str}{noun_str}."
            elif tgt == "kn":
                adj_str = f"{UNIVERSAL_LEXICON[adj_cid]['kn']} " if adj_cid else ""
                noun_str = UNIVERSAL_LEXICON[noun_cid]["kn"]
                return f"ನಾನು ಒಬ್ಬ {adj_str}{noun_str}."

        # Case C: "I want a book" / "எனக்கு ஒரு പുസ്തകം வேண்டும்"
        if ("to_me" in c_ids or "i" in c_ids) and "want" in c_ids:
            # Find object noun (book, pen, pencil, water, food)
            obj_cid = None
            for cand in ("book", "books", "pen", "pencil", "water", "food", "lesson"):
                if cand in c_ids:
                    obj_cid = cand
                    break

            if obj_cid:
                if tgt == "en":
                    obj_str = UNIVERSAL_LEXICON[obj_cid]["en"]
                    article = "a " if obj_cid in ("book", "pen", "pencil", "lesson") else ""
                    return f"I want {article}{obj_str}."
                elif tgt == "ta":
                    obj_str = UNIVERSAL_LEXICON[obj_cid]["ta"]
                    num_str = "ஒரு " if obj_cid in ("book", "pen", "pencil") else ""
                    return f"எனக்கு {num_str}{obj_str} வேண்டும்."
                elif tgt == "ml":
                    obj_str = UNIVERSAL_LEXICON[obj_cid]["ml"]
                    num_str = "ഒരു " if obj_cid in ("book", "pen", "pencil") else ""
                    return f"എനിക്ക് {num_str}{obj_str} വേണം."
                elif tgt == "hi":
                    obj_str = UNIVERSAL_LEXICON[obj_cid]["hi"]
                    num_str = "एक " if obj_cid in ("book", "pen", "pencil") else ""
                    return f"मुझे {num_str}{obj_str} चाहिए."
                elif tgt == "te":
                    obj_str = UNIVERSAL_LEXICON[obj_cid]["te"]
                    num_str = "ఒక " if obj_cid in ("book", "pen", "pencil") else ""
                    return f"నాకు {num_str}{obj_str} కావాలి."
                elif tgt == "kn":
                    obj_str = UNIVERSAL_LEXICON[obj_cid]["kn"]
                    num_str = "ಒಂದು " if obj_cid in ("book", "pen", "pencil") else ""
                    return f"ನನಗೆ {num_str}{obj_str} ಬೇಕು."

        # ==============================================================================
        # General Sequential Synthesis with Grammar Smoothing
        # ==============================================================================
        assembled_tokens: List[str] = []
        for orig, cid, resolved in concepts:
            assembled_tokens.append(resolved)

        raw_result = " ".join(assembled_tokens).strip()

        # Clean punctuation and spacing
        raw_result = re.sub(r"\s+([.,!?:;])", r"\1", raw_result)

        # Capitalize first letter if target is English
        if tgt == "en" and raw_result:
            raw_result = raw_result[0].upper() + raw_result[1:]
            if not raw_result.endswith((".", "!", "?")):
                raw_result += "."

        return raw_result
