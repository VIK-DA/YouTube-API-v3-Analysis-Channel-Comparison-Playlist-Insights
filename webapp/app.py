import logging
import os
import time

from flask import Flask, jsonify, render_template, request
from googleapiclient.errors import HttpError

from analyzer import build_overview, score_sentiment
from youtube_client import (
    YouTubeError,
    extract_video_id,
    get_video_comments,
    get_video_stats,
    get_youtube_client,
)

MAX_COMMENTS = int(os.environ.get("MAX_COMMENTS", "500"))
CACHE_SECONDS = 60 * 60

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Results per video ID, so repeat lookups don't spend YouTube API quota
_cache = {}


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/analyze")
def analyze():
    url = (request.get_json(silent=True) or {}).get("url", "")
    try:
        video_id = extract_video_id(url)
    except YouTubeError as e:
        return jsonify(error=str(e)), 400

    cached = _cache.get(video_id)
    if cached and time.time() - cached[0] < CACHE_SECONDS:
        return jsonify(cached[1])

    try:
        youtube = get_youtube_client()
        video = get_video_stats(youtube, video_id)
        comments = get_video_comments(youtube, video_id, MAX_COMMENTS)
    except YouTubeError as e:
        return jsonify(error=str(e)), 400
    except HttpError:
        app.logger.exception("YouTube API error")
        return jsonify(error="The YouTube API returned an error. Check the API key and try again."), 502

    if not comments:
        return jsonify(error="This video has no comments yet."), 400

    counts, percents = score_sentiment(comments)

    analysis = build_overview(comments, percents)

    # Most-liked comments for each sentiment, so the page can show real examples
    top = sorted(comments, key=lambda c: c["Likes"], reverse=True)
    examples = {label: [c for c in top if c["Sentiment"] == label][:3] for label in counts}

    result = dict(
        video=video,
        comments_analyzed=len(comments),
        sentiment_counts=counts,
        sentiment_percents=percents,
        examples=examples,
        analysis=analysis,
    )
    _cache[video_id] = (time.time(), result)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
