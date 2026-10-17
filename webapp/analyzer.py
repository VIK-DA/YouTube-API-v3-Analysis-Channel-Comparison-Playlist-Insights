import math
import re

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, CountVectorizer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_vader = SentimentIntensityAnalyzer()
# VADER is tuned for general social media; add criticism words that are common under YouTube videos
_vader.lexicon.update({
    "clickbait": -2.0, "cringe": -1.8, "overrated": -1.5, "misleading": -1.8, "slow": -1.0,
    "loud": -0.8, "quiet": -0.5, "repetitive": -1.2, "dragged": -1.2, "unwatchable": -2.5,
    "underrated": 1.5, "goated": 2.0, "masterpiece": 2.5, "fire": 1.2,
})
# "too long", "too loud" etc. are complaints even without a negative word
TOO_PATTERN = re.compile(r"\btoo (long|short|loud|quiet|fast|slow|much|many|little|few|repetitive|basic)\b", re.IGNORECASE)

# Words that show up in almost every comment section and say nothing about the video itself
FILLER_WORDS = {
    "video", "videos", "watch", "watching", "watched", "channel", "youtube", "like", "likes", "just",
    "really", "know", "think", "thing", "things", "make", "made", "got", "get", "going", "want", "way",
    "say", "said", "people", "time", "day", "lol", "lmao", "yes", "yeah", "guys", "guy", "bro", "man",
    "dont", "don", "doesn", "didn", "isn", "im", "ive", "youre", "thats", "cant", "wont", "u", "ur",
    "pls", "please", "omg", "wow", "oh", "ok", "okay", "gonna", "wanna", "actually", "literally",
    "need", "does", "did", "let", "lot", "lots", "use", "used", "new", "good", "great", "best",
    "love", "loved", "nice", "amazing", "awesome", "thanks", "thank", "bad", "worst", "hate",
}
STOP_WORDS = list(ENGLISH_STOP_WORDS | FILLER_WORDS)

VERDICTS = [(8.5, "Loved"), (6.5, "Mostly positive"), (4.5, "Mixed"), (2.5, "Mostly negative"), (0, "Hated")]


def score_sentiment(comments):
    """Label every comment positive/neutral/negative with VADER and return the counts."""
    counts = {"positive": 0, "neutral": 0, "negative": 0}
    for comment in comments:
        compound = _vader.polarity_scores(comment["Text"])["compound"]
        if TOO_PATTERN.search(comment["Text"]):
            compound -= 0.4
        if compound >= 0.05:
            label = "positive"
        elif compound <= -0.05:
            label = "negative"
        else:
            label = "neutral"
        comment["Compound"] = compound
        comment["Sentiment"] = label
        counts[label] += 1

    total = len(comments) or 1
    percents = {k: round(v * 100 / total, 1) for k, v in counts.items()}
    return counts, percents


def _weight(comment):
    # A comment with many likes speaks for more viewers, but don't let one viral comment drown the rest
    return 1 + math.log1p(comment["Likes"])


def _reception_score(comments):
    """Like-weighted balance of positive vs negative comments, mapped to 1-10."""
    pos = sum(_weight(c) for c in comments if c["Sentiment"] == "positive")
    neg = sum(_weight(c) for c in comments if c["Sentiment"] == "negative")
    if pos + neg == 0:
        return 5.5
    return 5.5 + 4.5 * (pos - neg) / (pos + neg)


def _top_terms(texts, limit):
    """Most common 1-2 word phrases across the given texts, as (phrase, number of comments)."""
    if len(texts) < 2:
        return []
    vectorizer = CountVectorizer(
        stop_words=STOP_WORDS, ngram_range=(1, 2), min_df=2, binary=True,
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z']{2,}\b",
    )
    try:
        matrix = vectorizer.fit_transform(texts)
    except ValueError:  # every word was a stop word or appeared only once
        return []

    freq = matrix.sum(axis=0).A1
    ranked = sorted(zip(vectorizer.get_feature_names_out(), freq), key=lambda t: (-t[1], -len(t[0])))

    # Prefer a two-word phrase over its single words when it's nearly as common ("sound quality" over "sound")
    chosen = []
    for term, count in ranked:
        overlaps = [c for c in chosen if term in c[0].split() or c[0] in term.split()]
        if overlaps:
            continue
        chosen.append((term, int(count)))
        if len(chosen) == limit:
            break
    return chosen


def _comments_mentioning(comments, term):
    pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
    return [c for c in comments if pattern.search(c["Text"])]


def _short(text, limit=220):
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def _likes(n):
    return f"{n:,} like" if n == 1 else f"{n:,} likes"


def _join(items):
    items = [f"“{i}”" for i in items]
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def build_overview(comments, percents):
    """Turn the scored comments into the overview shown on the page."""
    score = _reception_score(comments)
    verdict = next(label for cutoff, label in VERDICTS if score >= cutoff)
    by_likes = sorted(comments, key=lambda c: c["Likes"], reverse=True)

    positive = [c for c in comments if c["Sentiment"] == "positive"]
    negative = [c for c in comments if c["Sentiment"] == "negative"]
    questions = [c for c in by_likes if "?" in c["Text"]]

    # Main themes: most-discussed phrases, with how people felt about each
    themes = []
    for term, count in _top_terms([c["Text"] for c in comments], limit=6):
        mentions = _comments_mentioning(comments, term) or comments
        pos = sum(c["Sentiment"] == "positive" for c in mentions) / len(mentions)
        neg = sum(c["Sentiment"] == "negative" for c in mentions) / len(mentions)
        if pos >= 0.3 and neg >= 0.3:
            tone = "mixed"
        elif pos >= 0.5 and pos >= 2 * neg:
            tone = "positive"
        elif neg >= 0.4 and neg >= pos:
            tone = "negative"
        else:
            tone = "neutral"
        example = max(mentions, key=lambda c: c["Likes"])
        themes.append(dict(
            name=term,
            sentiment=tone,
            description=f"Mentioned in {count} comments: {round(pos * 100)}% positive, {round(neg * 100)}% negative.",
            example_quote=_short(example["Text"]),
        ))

    liked_terms = _top_terms([c["Text"] for c in positive], limit=5)
    disliked_terms = _top_terms([c["Text"] for c in negative], limit=5)
    liked = [f"{t} — in {n} positive comments" for t, n in liked_terms]
    disliked = [f"{t} — in {n} negative comments" for t, n in disliked_terms]
    # With few complaints there's no repeated phrase, so show the most-liked complaints themselves
    if not disliked:
        disliked = [_short(c["Text"], 160) for c in sorted(negative, key=lambda c: c["Likes"], reverse=True)[:3]]

    question_terms = _top_terms([c["Text"] for c in questions], limit=3)
    question_share = round(len(questions) * 100 / len(comments))

    # Plain-language summary and interpretation
    headline = {
        "Loved": "Viewers overwhelmingly loved this video.",
        "Mostly positive": "The reception is mostly positive.",
        "Mixed": "Viewers are split on this video.",
        "Mostly negative": "The reception leans negative.",
        "Hated": "Viewers strongly disliked this video.",
    }[verdict]
    if not positive and not negative:
        headline = "Comments are neutral: nobody expressed a strong opinion either way."

    summary = (
        f"Of {len(comments)} comments analysed, {percents['positive']}% are positive, "
        f"{percents['neutral']}% neutral and {percents['negative']}% negative. "
        "Weighting each comment by its likes gives a reception score of "
        f"{round(score, 1)}/10. "
    )
    if by_likes[0]["Likes"] > 0:
        summary += (
            f"The most-liked comment ({_likes(by_likes[0]['Likes'])}) is "
            f"{by_likes[0]['Sentiment']}: “{_short(by_likes[0]['Text'], 140)}”"
        )

    parts = []
    if themes:
        parts.append(f"The conversation centres on {_join([t['name'] for t in themes[:3]])}.")
    if liked_terms:
        parts.append(f"Viewers who enjoyed it point to {_join([t for t, _ in liked_terms[:3]])}.")
    if disliked_terms:
        parts.append(f"Critics focus on {_join([t for t, _ in disliked_terms[:3]])}.")
    elif negative:
        parts.append("Complaints are scattered rather than about one recurring issue.")
    else:
        parts.append("There are almost no complaints.")
    mixed = [t["name"] for t in themes if t["sentiment"] == "mixed"]
    if mixed:
        parts.append(f"Opinions are divided on {_join(mixed)}, so viewers took those parts differently.")
    if question_share >= 10:
        about = f", mostly about {_join([t for t, _ in question_terms])}" if question_terms else ""
        parts.append(f"{question_share}% of comments ask questions{about}, which shows what viewers want explained or covered next.")
    interpretation = " ".join(parts)

    notable = []
    for comment, why in [
        (by_likes[0] if by_likes else None, "Most-liked comment"),
        (max(positive, key=_weight) if positive else None, "Most-liked positive comment"),
        (max(negative, key=_weight) if negative else None, "Most-liked negative comment"),
        (max(comments, key=lambda c: c["Replies"]) if comments else None, "Started the biggest discussion"),
    ]:
        if comment and all(comment["Text"] != n["text"] for n in notable):
            notable.append(dict(text=_short(comment["Text"], 300),
                                why_it_matters=f"{why} · {_likes(comment['Likes'])} · {comment['Replies']:,} replies"))

    return dict(
        verdict=verdict,
        score=max(1, min(10, round(score))),
        headline=headline,
        summary=summary,
        interpretation=interpretation,
        what_people_liked=liked,
        what_people_disliked=disliked,
        themes=themes,
        questions_and_confusion=[_short(c["Text"], 160) for c in questions[:5]],
        notable_comments=notable,
    )
