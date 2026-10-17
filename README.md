# YouTube API Analysis Project

## Overview

This data science project utilizes the YouTube API v3 to analyze and compare three distinct YouTube channels. The goal is to uncover performance metrics such as views, likes, subscribers, and video counts for each channel and gain valuable insights from their playlists and viewer engagement patterns. The project aims to empower content creators and strategists with data-driven content strategies through interactive visualizations and charts.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Data Retrieval](#data-retrieval)
- [Data Visualization](#data-visualization)
- [Contributing](#contributing)
- [License](#license)

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

## Comment Pulse website (`webapp/`)

A website that analyses a video's comment section. Paste a YouTube link and it shows:

- the video's views, likes and comment count
- the share of positive, neutral and negative comments (VADER sentiment)
- an AI overview from Claude: a 1-10 reception score, summary, how viewers interpreted the video,
  what they liked and disliked, main themes, questions, and notable comments
- the most-liked comments for each sentiment

It reuses the notebook's YouTube Data API v3 code to fetch video stats and comments (up to 500, most relevant first).

### Run locally

```bash
cd webapp
pip install -r requirements.txt
export YOUTUBE_API_KEY=your-youtube-key
export ANTHROPIC_API_KEY=your-anthropic-key   # optional: without it you only get the sentiment numbers
python app.py   # open http://localhost:5000
```

### Deploy on Render

1. On [render.com](https://render.com), click **New → Blueprint** and pick this repository. Render reads `render.yaml`.
2. When asked, enter `YOUTUBE_API_KEY` and `ANTHROPIC_API_KEY`.
3. Click **Apply**. The site URL appears on the service page once the build finishes.

Never put API keys in the code or notebook; keep them in Render's environment variables.

## Contributing

Contributions are welcome! If you have any suggestions or find any issues, feel free to create a pull request or open an issue.

## License

This project is licensed under the [MIT License](LICENSE).
