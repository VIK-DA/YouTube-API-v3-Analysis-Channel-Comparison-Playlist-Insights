import os
import re

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

VIDEO_ID_PATTERN = re.compile(
    r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|embed/|live/|v/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)


class YouTubeError(Exception):
    """An error we can show to the user as-is."""


def extract_video_id(url):
    """Pull the 11-character video ID out of any common YouTube link (or a bare ID)."""
    url = url.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url
    match = VIDEO_ID_PATTERN.search(url)
    if not match:
        raise YouTubeError("That doesn't look like a YouTube video link.")
    return match.group(1)


def get_youtube_client():
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        raise YouTubeError("YOUTUBE_API_KEY is not set on the server.")
    # Build the YouTube API client
    return build("youtube", "v3", developerKey=api_key, cache_discovery=False)


def get_video_stats(youtube, video_id):
    """Fetch title, channel, published date, views, likes and comment count for one video."""
    response = youtube.videos().list(part="snippet,statistics", id=video_id).execute()
    if not response["items"]:
        raise YouTubeError("Video not found. It may be private or deleted.")

    video = response["items"][0]
    stats = video["statistics"]
    return dict(
        Video_id=video_id,
        Title=video["snippet"]["title"],
        Channel_name=video["snippet"]["channelTitle"],
        Published_date=video["snippet"]["publishedAt"],
        Thumbnail=video["snippet"]["thumbnails"].get("high", {}).get("url"),
        # Likes and comment counts are missing when the creator hides them
        Views=int(stats.get("viewCount", 0)),
        Likes=int(stats["likeCount"]) if "likeCount" in stats else None,
        Comment_count=int(stats["commentCount"]) if "commentCount" in stats else None,
    )


def get_video_comments(youtube, video_id, max_comments=500):
    """
    Retrieve top-level comments for a video, most relevant first.

    Follows nextPageToken the same way the notebook pages through playlist items,
    stopping once max_comments have been collected.
    """
    comments = []
    next_page_token = None

    try:
        while len(comments) < max_comments:
            response = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                order="relevance",
                textFormat="plainText",
                pageToken=next_page_token,
            ).execute()

            for item in response["items"]:
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comments.append(dict(
                    Text=snippet["textOriginal"],
                    Likes=snippet.get("likeCount", 0),
                    Replies=item["snippet"].get("totalReplyCount", 0),
                ))

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
    except HttpError as e:
        if e.resp.status == 403 and "commentsDisabled" in str(e):
            raise YouTubeError("Comments are turned off for this video.")
        if e.resp.status == 403 and "quota" in str(e).lower():
            raise YouTubeError("The YouTube API daily quota is used up. Try again tomorrow.")
        raise

    return comments[:max_comments]
