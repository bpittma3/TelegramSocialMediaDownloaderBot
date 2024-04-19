import json
import os
from pathlib import Path
import time
from urllib.request import urlretrieve
import requests


def handle_url(link):
    headers = {'User-Agent': "Telegram Social Media Downloader Bot"}
    link_parts = link.split('/')
    status_id = link_parts.index('status')
    id = link_parts[status_id + 1]
    try:
        response = requests.get(
            "https://api.fxtwitter.com/tgSocialMediaDownloaderBot/status/" + id, headers=headers)
        result = json.loads(response.text)
        if result['code'] == 200:
            return handle_tweet(result['tweet'])
        else:
            return {}
    except Exception as e:
        # Handle the exception here
        print("An error occurred:", str(e))


def handle_tweet(tweet):
    return_data = {}

    return_data = get_reply_quote_status(return_data, tweet)

    if "media" in tweet:
        if "videos" in tweet["media"]:
            return_data = handle_video_tweet(return_data, tweet)
        elif "mosaic" in tweet["media"]:
            return_data['type'] = "pic"
            return_data['media'] = tweet["media"]["mosaic"]["formats"]["jpeg"]
        elif "photos" in tweet["media"]:
            return_data['type'] = "pic"
            return_data['media'] = tweet["media"]["photos"][0]["url"]
        return_data['spoiler'] = tweet['possibly_sensitive']
    else:
        return_data['type'] = "text"

    return_data['text'] = tweet["text"]
    return_data['author'] = tweet["author"]["name"] + \
        " (@\\" + tweet["author"]["screen_name"] + ")"
    return_data['url'] = tweet['url']

    return return_data


def get_reply_quote_status(return_data, tweet):
    if "quote" in tweet:
        return_data["quote"] = True
        return_data["quote_url"] = tweet["quote"]["url"]
    else:
        return_data["quote"] = False

    if tweet["replying_to"] != None:
        return_data["reply"] = True
        return_data["reply_url"] = "https://twitter.com/" + \
            tweet["replying_to"] + "/status/" + tweet["replying_to_status"]
    else:
        return_data["reply"] = False

    return return_data


def handle_video_tweet(return_data, tweet):
    return_data['type'] = "vid"
    return_data['media'] = []
    for video in tweet["media"]["videos"]:
        return_data['media'].append(video["url"])
    return return_data


def download_video(url, id):
    filename = "temp/twitter/" + id + ".mp4"
    temp_filename = filename + ".temp." + str(time.time())
    try:
        Path("temp/twitter/").mkdir(parents=True, exist_ok=True)
        if (not os.path.isfile(filename)):
            if (not os.path.isfile(temp_filename)):
                urlretrieve(url, temp_filename)
                if not os.path.isfile(filename):
                    os.rename(temp_filename, filename)
                    return filename
                else:
                    final_filename = "temp/9gag/" + \
                        id + str(time.time()) + ".mp4"
                    os.rename(temp_filename, final_filename)
                    return final_filename
        else:
            return filename
    except Exception as e:
        # Handle the exception here
        print("An error occurred:", str(e))
        return ""
