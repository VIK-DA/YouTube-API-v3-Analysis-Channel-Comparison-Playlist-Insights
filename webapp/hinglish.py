"""
Hindi and Hinglish support for the comment analyser.

Comments under Indian YouTube videos are written in English, Hindi (Devanagari script) or
Hinglish (Hindi typed in Roman letters, usually mixed with English). VADER only knows English,
so this module adds Hindi/Hinglish sentiment words, Hindi intensifiers and Hindi negation,
plus stop words so topic extraction skips words like "hai" and "है".
"""
import re
import unicodedata

import vaderSentiment.vaderSentiment as vader_module


def _nfc(word):
    # Devanagari letters with a nukta (ड़, ज़) can be typed two ways; NFC makes them match
    return unicodedata.normalize("NFC", word)


# Sentiment strength on VADER's scale (-4 very negative ... +4 very positive).
# Roman spellings vary a lot, so common variants are listed separately.
HINGLISH_LEXICON = {
    # positive
    "accha": 1.8, "acha": 1.8, "achha": 1.8, "achcha": 1.8, "achchha": 1.8, "acchi": 1.8, "achi": 1.8,
    "achhi": 1.8, "acche": 1.8, "ache": 1.8, "achhe": 1.8,
    "badhiya": 2.2, "badiya": 2.2, "badhia": 2.2, "badia": 2.2,
    "mast": 2.0, "zabardast": 2.8, "jabardast": 2.8, "zabardust": 2.8,
    "shandar": 2.5, "shaandar": 2.5, "shandaar": 2.5,
    "kamaal": 2.5, "kamal": 2.5, "gajab": 2.5, "gazab": 2.5, "ghazab": 2.5,
    "behtareen": 2.8, "behtarin": 2.8, "bhetreen": 2.8,
    "sundar": 2.0, "khoobsurat": 2.2, "khubsurat": 2.2, "pyara": 2.0, "pyaara": 2.0, "pyari": 2.0,
    "maza": 1.8, "mazaa": 1.8, "mazza": 1.8, "maja": 1.8, "majaa": 1.8,
    "lajawab": 2.8, "lajawaab": 2.8, "dhamakedar": 2.5, "jhakaas": 2.5, "jhakkas": 2.5,
    "sahi": 1.5, "pasand": 1.5, "khush": 2.0, "khushi": 2.0,
    "shukriya": 2.0, "dhanyavad": 2.0, "dhanyawad": 2.0, "thanku": 2.0, "thnx": 1.8, "thx": 1.8,
    # "samajh aaya" = understood, so "samajh nahi aaya" (didn't understand) becomes a complaint
    "samajh": 0.8, "samjh": 0.8, "samjha": 0.8, "samjhaya": 1.2,
    "op": 1.5, "osm": 2.2, "awsm": 2.2, "superb": 2.5, "jhakas": 2.5,
    # negative
    "bekar": -2.0, "bekaar": -2.0, "bakwas": -2.5, "bakwaas": -2.5, "bakvas": -2.5,
    "ghatiya": -2.8, "ghatia": -2.8, "bura": -2.0, "buri": -2.0, "bure": -2.0,
    "faltu": -2.0, "faaltu": -2.0, "kharab": -2.0, "khraab": -2.0, "khrab": -2.0, "kharaab": -2.0,
    "ganda": -2.0, "gandi": -2.0, "wahiyat": -2.8, "vahiyat": -2.8,
    "galat": -1.5, "glt": -1.5, "jhooth": -1.8, "jhoot": -1.8, "jhuth": -1.8, "dhokha": -2.2,
    "nirash": -1.8, "dukh": -1.8, "dukhi": -1.8, "gussa": -1.8, "bore": -1.5, "bor": -1.5,
    "timepass": -0.8,
}

HINDI_LEXICON = {
    # positive
    "अच्छा": 1.8, "अच्छी": 1.8, "अच्छे": 1.8, "बढ़िया": 2.2, "बढिया": 2.2, "मस्त": 2.0,
    "ज़बरदस्त": 2.8, "जबरदस्त": 2.8, "शानदार": 2.5, "कमाल": 2.5, "गज़ब": 2.5, "गजब": 2.5,
    "बेहतरीन": 2.8, "सुंदर": 2.0, "सुन्दर": 2.0, "खूबसूरत": 2.2, "ख़ूबसूरत": 2.2,
    "प्यारा": 2.0, "प्यारी": 2.0, "मज़ा": 1.8, "मजा": 1.8, "लाजवाब": 2.8, "धमाकेदार": 2.5,
    "सही": 1.5, "पसंद": 1.5, "खुश": 2.0, "ख़ुश": 2.0, "खुशी": 2.0, "धन्यवाद": 2.0, "शुक्रिया": 2.0,
    "समझ": 0.8, "समझा": 0.8, "समझाया": 1.2, "प्रेरणादायक": 2.2, "उपयोगी": 1.8, "ज्ञानवर्धक": 2.0,
    # negative
    "बेकार": -2.0, "बकवास": -2.5, "घटिया": -2.8, "बुरा": -2.0, "बुरी": -2.0, "बुरे": -2.0,
    "फालतू": -2.0, "फ़ालतू": -2.0, "खराब": -2.0, "ख़राब": -2.0, "गंदा": -2.0, "गंदी": -2.0,
    "गलत": -1.5, "ग़लत": -1.5, "झूठ": -1.8, "झूठा": -1.8, "धोखा": -2.2, "निराश": -1.8,
    "दुख": -1.8, "दुःख": -1.8, "दुखी": -1.8, "गुस्सा": -1.8, "बोरिंग": -1.5, "वाहियात": -2.8,
}

# "bahut accha" = "very good": these strengthen the next word, like "very" in English
INTENSIFIERS = [
    "bahut", "bohot", "bahot", "bhot", "bht", "boht", "bohat", "ekdum", "bilkul", "sabse",
    "kaafi", "kafi", "itna", "itni", "zyada", "jyada",
    "बहुत", "एकदम", "बिल्कुल", "बिलकुल", "सबसे", "काफी", "काफ़ी", "इतना", "इतनी", "ज़्यादा", "ज्यादा",
]

# Hindi puts "not" after the word: "accha nahi" = "not good"
NEGATIONS = ["nahi", "nahin", "nhi", "nahee", "mat", "नहीं", "नही", "मत"]
_NEGATION_AFTER = re.compile(
    r"(\S+)\s+(?:" + "|".join(map(re.escape, NEGATIONS)) + r")(?=\s|[.!?,।]|$)", re.IGNORECASE
)

# Common Hindi/Hinglish grammar words: they carry no topic, and spotting them tells us a
# Roman-script comment is Hinglish rather than English
HINGLISH_STOP_WORDS = {
    "hai", "hain", "he", "ho", "hoga", "hogi", "hota", "hoti", "hote", "tha", "thi", "the", "raha", "rahi",
    "rahe", "ka", "ki", "ke", "ko", "se", "me", "mein", "mai", "main", "par", "pe", "aur", "ya", "bhi",
    "toh", "to", "ye", "yeh", "yah", "vo", "wo", "woh", "jo", "kya", "kyu", "kyun", "kaise", "kab",
    "kaha", "kahan", "kon", "kaun", "koi", "kuch", "sab", "sabhi", "ek", "isme", "usme", "iska", "uska",
    "apna", "apni", "apne", "aap", "ap", "aapka", "aapki", "aapke", "tum", "tera", "teri", "mera",
    "meri", "mere", "hum", "hamara", "hamari", "humko", "mujhe", "tujhe", "unko", "inko", "ab", "abhi",
    "jab", "tab", "phir", "fir", "bas", "sirf", "bhai", "bro", "sir", "ji", "yaar", "yr", "na", "haan",
    "han", "nahi", "nahin", "nhi", "kar", "karo", "kare", "karna", "karte", "karta", "kiya", "diya",
    "dekh", "dekha", "dekho", "dekhna", "liye", "lie", "wala", "wali", "wale", "bahut", "bohot", "bht",
    "bahot", "ekdum", "bilkul", "aisa", "aise", "jaise", "waise", "agar", "lekin", "par", "kyunki",
    "isliye", "hi", "hu", "hun", "hoon", "rha", "rhi", "rhe", "gya", "gyi", "gaya", "gayi", "lga", "laga",
    "lagi", "lage", "chahiye", "sakta", "sakte", "sakti", "video", "channel", "comment", "please", "plz",
}
HINDI_STOP_WORDS = {_nfc(w) for w in """
है हैं था थी थे हो होगा होगी होता होती होते रहा रही रहे का की के को से में पर और या भी तो ये यह
वो वह जो क्या क्यों कैसे कब कहाँ कहां कौन कोई कुछ सब सभी एक इसमें उसमें इसका उसका अपना अपनी अपने
आप आपका आपकी आपके तुम तेरा मेरा मेरी मेरे हम हमारा हमारी मुझे उन्हें इन्हें अब अभी जब तब फिर बस
सिर्फ भाई सर जी यार ना हाँ हां नहीं नही कर करो करे करना करते करता किया दिया देख देखा देखो लिए
वाला वाली वाले बहुत एकदम बिल्कुल ऐसा ऐसे जैसे वैसे अगर लेकिन क्योंकि इसलिए ही हूँ हूं गया गयी गई
लगा लगी लगे चाहिए सकता सकते सकती वीडियो चैनल
""".split()}

# Stop words that are also English words can't be used to tell Hinglish from English
HINGLISH_MARKERS = HINGLISH_STOP_WORDS - {
    "he", "to", "me", "main", "the", "par", "pe", "hi", "ab", "na", "ya", "ho", "so", "jo", "bro", "sir",
    "video", "channel", "comment", "please", "plz", "han", "mat", "bas", "fir", "ek", "kar", "rha",
}
QUESTION_WORDS = re.compile(r"(?<![A-Za-z])(?:kaise|kab|kyu|kyun|kyon|kaun|kahan|kitna|kitne|kitni)(?![A-Za-z])"
                            r"|कैसे|क्यों|क्यूं|कब|कौन|कहाँ|कहां|कितना|कितने|कितनी", re.IGNORECASE)

# Opinion words ("badhiya", "बेकार") describe how people feel, not what they talk about
OPINION_WORDS = set(HINGLISH_LEXICON) | {_nfc(w) for w in HINDI_LEXICON} | {_nfc(w) for w in INTENSIFIERS}

DEVANAGARI = re.compile(r"[ऀ-ॿ]")
LATIN = re.compile(r"[A-Za-z]")
# Words in Latin letters, or runs of Devanagari letters and vowel signs
TOKEN_PATTERN = r"(?u)(?:[a-zA-Z][a-zA-Z']{2,}|[ऀ-ॣ०-ॿ]{2,})"
WORD_RE = re.compile(r"[a-zA-Z']+|[ऀ-ॣ०-ॿ]+")


def install(analyzer):
    """Teach a VADER analyzer Hindi and Hinglish words, intensifiers and negations."""
    analyzer.lexicon.update(HINGLISH_LEXICON)
    analyzer.lexicon.update({_nfc(w): v for w, v in HINDI_LEXICON.items()})
    for word in INTENSIFIERS:
        vader_module.BOOSTER_DICT[_nfc(word)] = vader_module.B_INCR
    for word in NEGATIONS:
        if _nfc(word) not in vader_module.NEGATE:
            vader_module.NEGATE.append(_nfc(word))


def normalize(text):
    """Prepare a comment for VADER: unify Devanagari spelling and move Hindi negation before the word."""
    text = _nfc(text).replace("।", ".")
    # "accha nahi hai" -> "nahi accha hai", so VADER sees the negation before the word it negates
    return _NEGATION_AFTER.sub(lambda m: f"nahi {m.group(1)}", text)


def detect_language(text):
    """Classify a comment as 'Hindi', 'Hinglish' or 'English' (None if it has no letters)."""
    devanagari = len(DEVANAGARI.findall(text))
    latin = len(LATIN.findall(text))
    if devanagari + latin == 0:
        return None
    if devanagari and latin and min(devanagari, latin) / (devanagari + latin) >= 0.2:
        return "Hinglish"  # both scripts in one comment
    if devanagari > latin:
        return "Hindi"
    words = [w.lower() for w in WORD_RE.findall(text)]
    hindi_words = sum(w in HINGLISH_MARKERS or w in HINGLISH_LEXICON for w in words)
    # Two Hindi words, or a quarter of a short comment, means Hindi typed in Roman letters
    if hindi_words >= 2 or (words and hindi_words / len(words) >= 0.25):
        return "Hinglish"
    return "English"


def is_question(text):
    return "?" in text or bool(QUESTION_WORDS.search(text))
