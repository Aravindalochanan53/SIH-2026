"""
Gazetteer registries and dictionaries for Entity Locking in TRANSLARA.
Covers classroom student names, primary schools, Indian towns/villages, and math terms.
"""
from __future__ import annotations

# Common Indian student/teacher proper names across South, North, and Eastern India
COMMON_NAMES = {
    # South Indian names
    "arun", "அருண்", "അരുൺ", "అరుణ్", "ಅರುಣ್",
    "priya", "பிரியா", "പ്രിയ", "ప్రియ", "ಪ್ರಿಯಾ",
    "kumar", "குமார்", "കുമാർ", "కుమార్", "ಕುಮಾರ್",
    "ananya", "அனன்யா", "അനന്യ", "అనన్య", "ಅನನ್ಯ",
    "karthik", "கார்த்திக்", "കാർത്തിക്", "కార్తీక్", "ಕಾರ್ತಿಕ್",
    "kavitha", "கவிதா", "കവിത", "కవిత", "ಕವಿತಾ",
    "suresh", "சுரேஷ்", "സുരേഷ്", "సురేష్", "ಸುರೇಶ್",
    "divya", "திவ்யா", "ദിവ്യ", "దివ్య", "ದಿವ್ಯ",
    "meena", "மீனா", "മീന", "మీనా", "ಮೀನಾ",
    "ravi", "ரவி", "രവി", "రవి", "ರವಿ",
    # North / Tribal names (Jharkhand / Santhali / Ho / Mundari)
    "sona murmu", "sona", "murmu", "சோனா முர்மு", "सोना मुर्मू", "ᱥᱳᱱᱟ ᱢᱩᱨᱢᱩ",
    "birsa munda", "birsa", "munda", "பிர்சா முண்டா", "बिरसा मुंडा", "ᱵᱤᱨᱥᱟ ᱢᱩᱱᱰᱟ",
    "jaipal singh", "जयपाल सिंह",
    "rahul", "ராஹுல்", "രാഹുൽ", "రాహుల్", "ರಾಹುಲ್", "राहुल",
    "pooja", "பூஜா", "പൂജ", "పూజ", "ಪೂಜಾ", "पूजा",
    "amit", "அமித்", "അമിത്", "అమిత్", "ಅಮಿತ್", "अमित",
    "shanti", "சாந்தி", "ശാന്തി", "శాంతి", "ಶಾಂತಿ", "शांति",
}

# Educational and geographic place names
COMMON_PLACES = {
    "chennai", "சென்னை", "ചെന്നൈ", "చెన్నై", "ಚೆನ್ನೈ",
    "madurai", "மதுரை", "മധുര", "మదురై", "ಮಧುರೆ",
    "kochi", "കൊച്ചി", "கொச்சி", "కొచ్చి", "ಕೊಚ್ಚಿ",
    "thiruvananthapuram", "திருவனந்தபுரம்", "തിരുവനന്തപുരം",
    "bengaluru", "பெங்களூரு", "ബാംഗ്ലൂർ", "బెంగళూరు", "ಬೆಂಗಳೂರು",
    "hyderabad", "ஹைதராபாத்", "ഹൈദരാബാദ്", "హైదరాబాద్", "ಹೈದರಾಬಾದ್",
    "ranchi", "ராஞ்சி", "റാഞ്ചി", "రాంచీ", "ರಾಂಚಿ", "राँची", "ᱨᱟᱺᱪᱤ",
    "dumka", "दुमका", "ᱫᱩᱢᱠᱟᱹ",
    "jamshedpur", "जमशेदपुर", "ᱡᱟᱢᱥᱮᱫᱽᱯᱩᱨ",
    "delhi", "டெல்லி", "ഡൽഹി", "ఢిల్లీ", "ದೆಹಲಿ", "दिल्ली",
}

# Math and measurement terms
MATH_SYMBOLS = {
    "+", "-", "*", "/", "=", "%", "π", "√", "°", "cm", "kg", "km", "mm", "m", "l", "ml", "₹", "$"
}
