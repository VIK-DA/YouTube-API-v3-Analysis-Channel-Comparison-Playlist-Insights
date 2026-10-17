# YouTube API Analysis Project

## Overview

This data science project utilizes the YouTube API v3 to analyze and compare three distinct YouTube channels. The goal is to uncover performance metrics such as views, likes, subscribers, and video counts for each channel and gain valuable insights from their playlists and viewer engagement patterns. The project aims to empower content creators and strategists with data-driven content strategies through interactive visualizations and charts.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Data Retrieval](#data-retrieval)
- [Data Visualization](#data-visualization)
- [Contributing](#contributing)

## Installation

1. Clone the GitHub repository.
2. Ensure you have the required libraries installed:
   - googleapiclient.discovery
   - pandas
   - numpy
   - matplotlib
   - seaborn

## Usage

To run the project, follow these steps:

1. Obtain a YouTube Data API v3 key from the Google Developers Console.
2. Replace `'YOUR_API_KEY'` with your actual API key in the Python code.
3. Open Jupyter Notebook and execute the provided code cells to analyze YouTube channels and retrieve video data.

## Data Retrieval

### Channel Statistics

To compare the performance metrics of three YouTube channels, use the `get_channel_stats` function. Provide the YouTube API client and a list of channel IDs as input. The function will return a DataFrame with channel statistics.

### Playlist Information

To explore the playlists and videos within a specific channel, use the `get_channel_ids` function. Provide the YouTube API client and the playlist ID for the desired channel. The function will return a list of video IDs from the playlist.

### Video Statistics

To analyze video-specific statistics, use the `get_channel_ids` function. Provide the YouTube API client and a list of video IDs as input. The function will return a list of dictionaries containing video details such as title, published date, views, likes, and comment count.

## Data Visualization

### Total Subscribers Bar Plot

To visualize the total number of subscribers for each YouTube channel, use the `plot_subscribers_bar` function. Provide a DataFrame with channel statistics (`df`), and the function will display a bar plot.

### Top 10 Videos Bar Plot

To visualize the top 10 videos based on the number of views, use the `top_10_videos` DataFrame. The function will display a bar plot comparing the views of the top 10 videos.

### Top Years Bar Plot

To visualize the number of views for videos from different years, use the `video_data` DataFrame. The function will display a bar plot showing the popularity of videos over the years.

## Archivarix Tube website (`webapp/`)

A website that analyses a video's comment section. Paste a YouTube link and it shows:

- the video's views, likes and comment count
- the share of positive, neutral and negative comments (VADER sentiment)
- an overview built with Python libraries (no AI service or paid API): a 1-10 reception score
  weighted by comment likes, a summary, how viewers interpreted the video, what they liked and disliked
  (most-repeated phrases found with scikit-learn), main themes, questions, and notable comments
- the most-liked comments for each sentiment

It reuses the notebook's YouTube Data API v3 code to fetch video stats and comments (up to 500, most relevant first).

### Run locally

```bash
cd webapp
pip install -r requirements.txt
export YOUTUBE_API_KEY=your-youtube-key
python app.py   # open http://localhost:5000
```

### Deploy on Render

1. On [render.com](https://render.com), click **New → Blueprint** and pick this repository. Render reads `render.yaml`.
2. When asked, enter your `YOUTUBE_API_KEY`.
3. Click **Apply**. The site URL appears on the service page once the build finishes.

Never put the API key in the code or notebook; keep it in Render's environment variables.

### Languages

Comments in English, Hindi (Devanagari) and Hinglish (Hindi typed in Roman letters, often mixed with
English) are understood. `webapp/hinglish.py` adds:

- Hindi/Hinglish sentiment words in both scripts, e.g. *badhiya*, *mast*, *bakwas*, *ghatiya*, *शानदार*, *बेकार*
- intensifiers such as *bahut*, *ekdum* and *बहुत* ("bahut accha" scores higher than "accha")
- Hindi negation, which comes after the word: *accha nahi*, *अच्छा नहीं* = not good
- Hindi question words (*kaise*, *kab*, *kyun*, *कैसे*, *क्यों*), so questions are found even without a "?"
- Hindi/Hinglish grammar words (*hai*, *bhai*, *के*, *है*) are skipped when finding topics

The page shows what share of comments is in English, Hindi and Hinglish.

### Limitations

- **Word-list based, not AI.** Sentiment comes from VADER plus a list of about 150 Hindi/Hinglish words.
  Unusual slang or creative spellings (*bdhiyaaa*) aren't recognised and count as neutral.
- **No sarcasm.** "wah kya video hai 🙄" or "great, another ad" read as positive.
- **Other languages** (Tamil, Bengali, Spanish, …) mostly count as neutral.
- **Same topic in two scripts counts twice**: "editing" and "एडिटिंग" appear as separate themes.
- **Template summaries.** The summary and "how people interpreted it" text is built from the numbers and
  most-repeated phrases, so it can say *what* people discuss and how they feel, not *why*.
- **Up to 500 comments** (most relevant first) are analysed, and replies to comments are not included.
- **Small comment sections** give rough results: themes need a phrase to appear in at least 2 comments.
- **YouTube API quota**: the free key allows about 10,000 units a day; each analysis uses roughly 6–7.
  Results are cached for an hour per video, but the cache resets when the server restarts.
- **Render free plan** sleeps after about 15 minutes without visitors, so the first load can take up to a minute.

### Changelog

- **Hindi & Hinglish support**: sentiment, negation, questions and topics now work for Hindi and Hinglish
  comments; added a language breakdown to the page.
- **Renamed** the website to Archivarix Tube.
- **Local analysis instead of an AI API**: replaced the Claude API with free Python libraries
  (VADER and scikit-learn), so the site only needs a YouTube API key and costs nothing to run.
- **First version**: Flask website that fetches a video's stats and comments with the YouTube Data API,
  scores sentiment and shows themes, likes, dislikes, questions and notable comments. Deployable on
  Render with `render.yaml`.

## Contributing

Contributions are welcome! If you have any suggestions or find any issues, feel free to create a pull request or open an issue.
